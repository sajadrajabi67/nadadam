import { cancelReminder, scheduleReminder, requestReminderPermission, remindersAreNative } from './lib/reminders';
import { toGregorian, type Store } from './logic';

export type ReminderOptions = { enabled: boolean; days: number };
const OPTIONS_KEY = 'nadadam-reminder-options-v1';
const SCHEDULE_KEY = 'nadadam-scheduled-reminders-v1';
const choices = [0, 1, 2, 3, 5, 7, 10];
type Scheduled = Record<string, { id: number; at: number; title: string }>;
let queue: Promise<void> = Promise.resolve();

export function loadReminderOptions(): ReminderOptions {
  try {
    const saved = JSON.parse(localStorage.getItem(OPTIONS_KEY) || 'null');
    if (saved && typeof saved.enabled === 'boolean' && choices.includes(saved.days)) return saved;
  } catch { /* invalid settings: keep reminders off */ }
  return { enabled: false, days: 3 };
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
    const desired: Record<string, { at: number; title: string }> = {};
    const now = Date.now();
    if (options.enabled) for (const item of store.installments) {
      if (item.isPaid) continue;
      const date = toGregorian(item.dueDate);
      const at = new Date(date.getUTCFullYear(), date.getUTCMonth(), date.getUTCDate() - options.days, 9).getTime();
      if (at <= now) continue;
      desired[item.id] = { at, title: item.titleOverride || store.debts.find(d => d.id === item.debtId)?.title || 'قسط' };
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
      const body = options.days === 0
        ? `قسط ${entry.title} امروز سررسید می‌شه. اگه دادی، برو توی برنامه و بزن «دادم».`
        : `قسط ${entry.title} تا ${options.days.toLocaleString('fa-IR')} روز دیگه سررسید می‌شه. هنوز ندادیش!`;
      await scheduleReminder({ id, title: options.days === 0 ? 'امروز روز قسطته!' : 'حواست به قسطت باشه!', body, at: new Date(entry.at) });
      saved[key] = { id, ...entry };
      localStorage.setItem(SCHEDULE_KEY, JSON.stringify(saved));
    }
  })();
}
export function syncReminders(store: Store, options: ReminderOptions): Promise<void> {
  queue = queue.catch(() => {}).then(() => sync(store, options));
  return queue;
}
