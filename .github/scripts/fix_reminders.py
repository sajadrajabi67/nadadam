from pathlib import Path
import re

lib = Path("src/lib/reminders.ts")
s = lib.read_text(encoding="utf-8")
anchor = "export function remindersAreNative(): boolean {\n  return nativePlugin() !== null;\n}\n"
if "getReminderPermissionState" not in s:
    s = s.replace(anchor, anchor + """
export async function getReminderPermissionState(): Promise<{ display: string; exact: string }> {
  const native = nativePlugin();
  if (!native) return { display: typeof Notification === 'undefined' ? 'unsupported' : Notification.permission, exact: 'not-applicable' };
  const display = (await native.checkPermissions()).display;
  let exact = 'unknown';
  try { exact = (await native.checkExactNotificationSetting()).exact_alarm; } catch {}
  return { display, exact };
}
""", 1)
start = s.index("export async function scheduleReminder(")
end = s.index("\nexport async function cancelReminder", start)
s = s[:start] + """export async function scheduleReminders(items: ReminderOptions[]): Promise<void> {
  if (!items.length) return;
  const native = nativePlugin();
  if (native) {
    await native.schedule({ notifications: items.map(item => {
      const at = new Date(item.at.getTime()); at.setSeconds(0, 0);
      return { id: item.id, title: item.title, body: item.body ?? '', schedule: { at, allowWhileIdle: true } };
    }) });
    return;
  }
  const all = readStore();
  writeStore([...all.filter(old => !items.some(item => item.id === old.id)),
    ...items.map(item => ({ id: item.id, title: item.title, body: item.body, at: item.at.getTime(), repeats: null as null }))]);
  for (const item of items) armWebTimer({ id: item.id, title: item.title, body: item.body, at: item.at.getTime(), repeats: null });
}
export async function scheduleReminder(opts: ReminderOptions): Promise<{ native: boolean }> {
  await scheduleReminders([opts]); return { native: remindersAreNative() };
}
""" + s[end:]
lib.write_text(s, encoding="utf-8")

p = Path("src/reminderSync.ts")
s = p.read_text(encoding="utf-8")
s = s.replace("cancelReminder, scheduleReminder, requestReminderPermission, remindersAreNative, listReminderIds",
              "cancelReminder, scheduleReminder, scheduleReminders, requestReminderPermission, remindersAreNative, listReminderIds, getReminderPermissionState")
needle = "    const pendingIds = remindersAreNative() ? new Set(await listReminderIds()) : null;\n"
if "getReminderPermissionState()" not in s:
    s = s.replace(needle, needle + """    if (options.enabled && remindersAreNative()) {
      const permission = await getReminderPermissionState();
      if (permission.display !== 'granted' || permission.exact !== 'granted') {
        try { localStorage.setItem('nadadam-reminder-last-error-v1', 'مجوز ناکافی: اعلان=' + permission.display + '، هشدار دقیق=' + permission.exact); } catch {}
        return;
      }
    }
""", 1)
pattern = r"    let nextId = Math\.max\(0, \.\.\.Object\.values\(saved\)\.map\(v => v\.id\)\);.*?(?=\n  \}\)\(\);)"
replacement = """    let nextId = Math.max(1000, ...Object.values(saved).map(v => v.id)) + 1;
    const additions: Array<{ key: string; id: number; at: number; title: string; daysBefore: number }> = [];
    for (const [key, entry] of Object.entries(desired)) if (!saved[key]) additions.push({ key, id: nextId++, ...entry });
    const makeNotice = (entry: typeof additions[number]) => ({
      id: entry.id,
      title: entry.daysBefore === 0 ? 'امروز روز قسطته!' : 'حواست به قسطت باشه!',
      body: entry.daysBefore === 0
        ? 'قسط ' + entry.title + ' امروز سررسید می‌شه. اگه دادی، برو توی برنامه و بزن «دادم».'
        : 'قسط ' + entry.title + ' تا ' + entry.daysBefore.toLocaleString('fa-IR') + ' روز دیگه سررسید می‌شه. هنوز ندادیش!',
      at: new Date(entry.at)
    });
    if (additions.length) {
      try {
        await scheduleReminders(additions.map(makeNotice));
        for (const entry of additions) saved[entry.key] = { id: entry.id, at: entry.at, title: entry.title };
        localStorage.setItem(SCHEDULE_KEY, JSON.stringify(saved));
        try { localStorage.setItem('nadadam-reminder-last-error-v1', ''); } catch {}
      } catch {
        for (const entry of additions) {
          try {
            await scheduleReminder(makeNotice(entry));
            saved[entry.key] = { id: entry.id, at: entry.at, title: entry.title };
            localStorage.setItem(SCHEDULE_KEY, JSON.stringify(saved));
          } catch (error) {
            try { localStorage.setItem('nadadam-reminder-last-error-v1', error instanceof Error ? error.message : String(error)); } catch {}
          }
        }
      }
    }"""
s, n = re.subn(pattern, replacement, s, count=1, flags=re.S)
if n != 1: raise SystemExit("Could not replace reminder scheduling loop")
s = s.replace("new Date(Date.now() + 60_000)", "new Date(Date.now() + 2 * 60_000)")
s = s.replace("تا یک دقیقه دیگر منتظر بمان و برنامه را ببند.", "حدود دو دقیقه دیگر منتظر بمان و برنامه را ببند.")
if "export async function reminderDiagnostics" not in s:
    s += """
export async function reminderDiagnostics(): Promise<string> {
  const permission = await getReminderPermissionState();
  const pending = await listReminderIds();
  let error = '';
  try { error = localStorage.getItem('nadadam-reminder-last-error-v1') || ''; } catch {}
  return 'مجوز اعلان: ' + permission.display + '\\\\nهشدار دقیق: ' + permission.exact + '\\\\nاعلان‌های زمان‌بندی‌شده: ' + pending.length + (error ? '\\\\nآخرین خطا: ' + error : '');
}
"""
p.write_text(s, encoding="utf-8")

app = Path("src/App.tsx")
s = app.read_text(encoding="utf-8")
s = s.replace("type ReminderOptions, reminderDayChoices, runReminderTest } from './reminderSync';",
              "type ReminderOptions, reminderDayChoices, runReminderTest, reminderDiagnostics } from './reminderSync';")
s = s.replace("ارسال اعلان آزمایشی (یک دقیقه بعد)", "آزمایش اعلان (حدود دو دقیقه بعد)")
if "data-testid=\"reminder-diagnostics\"" not in s:
    marker = "{reminderError&&<p role=\"alert\""
    pos = s.find(marker)
    if pos < 0: raise SystemExit("App reminder error display not found")
    diag = """{remindersAreNative()&&<button data-testid="reminder-diagnostics" type="button" onClick={async()=>{try{setReminderError(await reminderDiagnostics());}catch(error){setReminderError("خواندن وضعیت اعلان‌ها ناموفق بود: "+(error instanceof Error?error.message:String(error)));}}} className="mt-2 min-h-12 w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 font-bold text-slate-700">بررسی وضعیت و مجوز اعلان‌ها</button>}"""
    s = s[:pos] + diag + s[pos:]
app.write_text(s, encoding="utf-8")
print("Reminder hardening patch applied.")


# Emergency safety switch: reminders stay disabled until native scheduling is repaired.
# Clear the persisted enabled flag without touching debt/installment data.
from pathlib import Path
import re

p = Path("src/reminderSync.ts")
s = p.read_text(encoding="utf-8")
s = s.replace(
    "      return { enabled: saved.enabled, days: validDays.length ? validDays : [3], time: validTime(saved.time) ? saved.time : '09:00' };",
    """      if (saved.enabled) {
        try { localStorage.setItem(OPTIONS_KEY, JSON.stringify({ ...saved, enabled: false })); } catch {}
      }
      return { enabled: false, days: validDays.length ? validDays : [3], time: validTime(saved.time) ? saved.time : '09:00' };"""
)
s = s.replace(
    "function sync(store: Store, options: ReminderOptions): Promise<void> {\n  return (async () => {",
    "function sync(store: Store, options: ReminderOptions): Promise<void> {\n  if (!options.enabled) return Promise.resolve();\n  return (async () => {"
)
p.write_text(s, encoding="utf-8")

app = Path("src/App.tsx")
s = app.read_text(encoding="utf-8")
s, n = re.subn(
    r'<input data-testid="reminder-toggle" type="checkbox".*?/>',
    '<input data-testid="reminder-toggle" type="checkbox" className="h-6 w-6 accent-[#0F9D8A]" checked={false} disabled aria-label="یادآوری موقتاً غیرفعال است"/>',
    s, count=1, flags=re.S
)
if n != 1:
    raise SystemExit("Could not safely disable reminder toggle")
s = s.replace(
    '<span>یادآوری سررسید قسط‌ها</span>',
    '<span>یادآوری سررسید قسط‌ها <small className="block pt-1 font-normal text-amber-700">به‌دلیل رفع اشکال فنی، موقتاً غیرفعال شده است.</small></span>',
    1
)
app.write_text(s, encoding="utf-8")
print("Emergency reminder shutdown applied; debt data is untouched.")
