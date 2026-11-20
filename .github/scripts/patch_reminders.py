from pathlib import Path
import re

app = Path("src/App.tsx")
source = app.read_text(encoding="utf-8")
source = source.replace("type ReminderOptions } from './reminderSync';", "type ReminderOptions, reminderDayChoices } from './reminderSync';", 1)
pattern = r'\{reminderOptions\.enabled&&<label className="mt-3 block text-sm font-bold">چند روز قبل از سررسید بهت خبر بدم؟.*?</select></label>\}'
replacement = r'''{reminderOptions.enabled&&<div className="mt-4 space-y-4"><div><p className="mb-3 text-sm font-bold">یادآوری سررسید قسط‌ها چند روز قبل از سررسید بهت خبر بدم؟</p><div data-testid="reminder-days" role="group" aria-label="روزهای یادآوری" className="grid grid-cols-7 gap-1.5">{reminderDayChoices.map(day=><button key={day} type="button" data-testid={'reminder-day-' + day} role="checkbox" aria-checked={reminderOptions.days.includes(day)} onClick={()=>{const days=reminderOptions.days.includes(day)?reminderOptions.days.filter(d=>d!==day):[...reminderOptions.days,day].sort((a,b)=>a-b);if(!days.length)return;const next={...reminderOptions,days};try{saveReminderOptions(next);setReminderOptions(next);setReminderError('');}catch{setReminderError('تنظیمات ذخیره نشد.');}}} className={'min-h-11 rounded-xl border text-sm font-bold transition ' + (reminderOptions.days.includes(day)?'border-[#0F9D8A] bg-[#0F9D8A] text-white shadow-sm':'border-slate-200 bg-slate-50 text-slate-600')}>{day===0?'امروز':fa(day)}</button>)}</div><p className="mt-2 text-xs text-slate-500">می‌تونی چند روز رو هم‌زمان انتخاب کنی.</p></div><label className="block text-sm font-bold">ساعت ارسال یادآوری<input data-testid="reminder-time" type="time" dir="ltr" required className={field + ' mt-2'} value={reminderOptions.time} onChange={e=>{if(!/^([01]\d|2[0-3]):[0-5]\d$/.test(e.target.value))return;const next={...reminderOptions,time:e.target.value};try{saveReminderOptions(next);setReminderOptions(next);setReminderError('');}catch{setReminderError('تنظیمات ذخیره نشد.');}}}/></label></div>}'''
source, count = re.subn(pattern, lambda _: replacement, source, count=1, flags=re.S)
if count != 1:
    raise SystemExit("Could not locate the original reminder-day dropdown.")
app.write_text(source, encoding="utf-8")

Path("src/reminderSync.ts").write_text("""import { cancelReminder, scheduleReminder, requestReminderPermission, remindersAreNative } from './lib/reminders';
import { toGregorian, type Store } from './logic';

export const reminderDayChoices = [0, 1, 2, 3, 5, 7, 10] as const;
export type ReminderOptions = { enabled: boolean; days: number[]; time: string };
const OPTIONS_KEY = 'nadadam-reminder-options-v1';
const SCHEDULE_KEY = 'nadadam-scheduled-reminders-v1';
type Scheduled = Record<string, { id: number; at: number; title: string }>;
let queue: Promise<void> = Promise.resolve();

function validTime(value: unknown): value is string {
  return typeof value === 'string' && /^(?:[01]\\d|2[0-3]):[0-5]\\d$/.test(value);
}
export function loadReminderOptions(): ReminderOptions {
  try {
    const saved = JSON.parse(localStorage.getItem(OPTIONS_KEY) || 'null');
    if (saved && typeof saved.enabled === 'boolean') {
      const legacyDays = Number.isInteger(saved.days) ? [saved.days] : [];
      const days = Array.isArray(saved.days) ? saved.days : legacyDays;
      const validDays = [...new Set(days.filter((day: unknown) => typeof day === 'number' && reminderDayChoices.includes(day as any)))];
      return { enabled: saved.enabled, days: validDays.length ? validDays : [3], time: validTime(saved.time) ? saved.time : '09:00' };
    }
  } catch { /* invalid settings: keep reminders off */ }
  return { enabled: false, days: [3], time: '09:00' };
}
export function saveReminderOptions(options: ReminderOptions) {
  localStorage.setItem(OPTIONS_KEY, JSON.stringify(options));
}
export async function enableReminderPermission(): Promise<boolean> {
  const result = await requestReminderPermission();
  return result !== false;
}
export { remindersAreNative };

function sync(store: Store, options: ReminderOptions): Promise<void> {
  return (async () => {
    let saved: Scheduled = {};
    try { saved = JSON.parse(localStorage.getItem(SCHEDULE_KEY) || '{}') || {}; } catch { saved = {}; }
    const desired: Record<string, { at: number; title: string; daysBefore: number }> = {};
    const now = Date.now();
    const [hour, minute] = options.time.split(':').map(Number);
    if (options.enabled && validTime(options.time)) for (const item of store.installments) {
      if (item.isPaid) continue;
      const date = toGregorian(item.dueDate);
      const title = item.titleOverride || store.debts.find(d => d.id === item.debtId)?.title || 'قسط';
      for (const daysBefore of options.days) {
        const at = new Date(date.getUTCFullYear(), date.getUTCMonth(), date.getUTCDate() - daysBefore, hour, minute).getTime();
        if (at <= now) continue;
        desired[item.id + ':' + daysBefore] = { at, title, daysBefore };
      }
    }
    for (const [key, entry] of Object.entries(saved)) {
      if (!desired[key] || desired[key].at !== entry.at || desired[key].title !== entry.title) {
        await cancelReminder(entry.id);
        delete saved[key];
        localStorage.setItem(SCHEDULE_KEY, JSON.stringify(saved));
      }
    }
    let nextId = Math.max(0, ...Object.values(saved).map(v => v.id));
    for (const [key, entry] of Object.entries(desired)) {
      if (saved[key]) continue;
      const id = ++nextId;
      const body = entry.daysBefore === 0
        ? 'قسط ' + entry.title + ' امروز سررسید می‌شه. اگه دادی، برو توی برنامه و بزن «دادم».'
        : 'قسط ' + entry.title + ' تا ' + entry.daysBefore.toLocaleString('fa-IR') + ' روز دیگه سررسید می‌شه. هنوز ندادیش!';
      await scheduleReminder({ id, title: entry.daysBefore === 0 ? 'امروز روز قسطته!' : 'حواست به قسطت باشه!', body, at: new Date(entry.at) });
      saved[key] = { id, at: entry.at, title: entry.title };
      localStorage.setItem(SCHEDULE_KEY, JSON.stringify(saved));
    }
  })();
}
export function syncReminders(store: Store, options: ReminderOptions): Promise<void> {
  queue = queue.catch(() => {}).then(() => sync(store, options));
  return queue;
}
""", encoding="utf-8")
print("Reminder settings and scheduling patch applied.")
