export type JDate = { y: number; m: number; d: number };
export type Debt = { id: string; title: string; installmentAmount: number; totalInstallments: number; firstDueDate: JDate; createdAt: number; notes: string; active: boolean };
export type Installment = { id: string; debtId: string; installmentNumber: number; amount: number; dueDate: JDate; isPaid: boolean; paidAt: number | null; notes: string; titleOverride?: string };
export type Store = { debts: Debt[]; installments: Installment[]; currency: 'toman' | 'rial' };
export const emptyStore: Store = { debts: [], installments: [], currency: 'toman' };
export const months = ['فروردین','اردیبهشت','خرداد','تیر','مرداد','شهریور','مهر','آبان','آذر','دی','بهمن','اسفند'];
const calendar = new Intl.DateTimeFormat('en-US-u-ca-persian', { timeZone: 'UTC', year: 'numeric', month: 'numeric', day: 'numeric' });
export function fromGregorian(date: Date): JDate {
  const parts = calendar.formatToParts(date);
  const get = (key: string) => Number(parts.find(p => p.type === key)?.value);
  return { y: get('year'), m: get('month'), d: get('day') };
}
export function today(): JDate { const n = new Date(); return fromGregorian(new Date(Date.UTC(n.getFullYear(), n.getMonth(), n.getDate()))); }
export function compare(a: JDate, b: JDate) { return a.y - b.y || a.m - b.m || a.d - b.d; }
export function toGregorian(j: JDate): Date {
  let lo = Date.UTC(j.y + 620, 0, 1), hi = Date.UTC(j.y + 623, 0, 1);
  while (lo <= hi) {
    const mid = Math.floor((lo + hi) / 2 / 86400000) * 86400000;
    const cmp = compare(fromGregorian(new Date(mid)), j);
    if (cmp === 0) return new Date(mid);
    if (cmp < 0) lo = mid + 86400000; else hi = mid - 86400000;
  }
  throw new Error('تاریخ نامعتبر است');
}
export function shiftMonth(j: JDate, delta: number): JDate {
  const index = j.y * 12 + j.m - 1 + delta;
  return { y: Math.floor(index / 12), m: ((index % 12) + 12) % 12 + 1, d: 1 };
}
export function daysInMonth(y: number, m: number): number {
  const start = toGregorian({ y, m, d: 1 }).getTime();
  const next = shiftMonth({ y, m, d: 1 }, 1);
  return Math.round((toGregorian(next).getTime() - start) / 86400000);
}
export function addMonthsClamped(j: JDate, delta: number): JDate {
  const next = shiftMonth(j, delta);
  return { ...next, d: Math.min(j.d, daysInMonth(next.y, next.m)) };
}
export function createInstallments(debt: Debt): Installment[] {
  return Array.from({ length: debt.totalInstallments }, (_, index) => ({ id: crypto.randomUUID(), debtId: debt.id, installmentNumber: index + 1, amount: debt.installmentAmount, dueDate: addMonthsClamped(debt.firstDueDate, index), isPaid: false, paidAt: null, notes: '' }));
}
export function monthly(items: Installment[], month: JDate) {
  const list = items.filter(i => i.dueDate.y === month.y && i.dueDate.m === month.m).sort((a,b) => compare(a.dueDate,b.dueDate));
  const total = list.reduce((sum,i) => sum + i.amount, 0);
  const paid = list.reduce((sum,i) => sum + (i.isPaid ? i.amount : 0), 0);
  return { list, total, paid, remaining: total-paid, percent: total ? Math.round(paid/total*100) : 0 };
}
export function debtStats(items: Installment[]) {
  const total = items.reduce((sum,i) => sum+i.amount,0);
  const paid = items.reduce((sum,i) => sum+(i.isPaid ? i.amount : 0),0);
  return { total, paid, remaining: total-paid, paidCount: items.filter(i=>i.isPaid).length, remainingCount: items.filter(i=>!i.isPaid).length };
}
export const fa = (value: number | string) => String(value).replace(/[0-9]/g, d => '۰۱۲۳۴۵۶۷۸۹'[Number(d)]);
export const digits = (value: string) => value.replace(/[۰-۹]/g, d => String('۰۱۲۳۴۵۶۷۸۹'.indexOf(d))).replace(/[٠-٩]/g, d => String('٠١٢٣٤٥٦٧٨٩'.indexOf(d)));
export const number = (value: number) => fa(new Intl.NumberFormat('en-US').format(value));
export const dateLabel = (j: JDate) => `${fa(j.d)} ${months[j.m-1]} ${fa(j.y)}`;
export const monthLabel = (j: JDate) => `${months[j.m-1]} ${fa(j.y)}`;
export function money(value: number, currency: Store['currency']) { return `${number(currency === 'rial' ? value*10 : value)} ${currency === 'rial' ? 'ریال' : 'تومان'}`; }
export function loadStore(): Store {
  try {
    const raw = localStorage.getItem('debt-manager-v1');
    if (!raw) return emptyStore;
    const parsed = JSON.parse(raw);
    if (!isStore(parsed)) return emptyStore;
    return parsed;
  } catch { return emptyStore; }
}
export function isStore(value: unknown): value is Store {
  if (!value || typeof value !== 'object') return false;
  const v = value as Partial<Store>;
  return Array.isArray(v.debts) && Array.isArray(v.installments) && (v.currency === 'toman' || v.currency === 'rial') &&
    v.debts.every(d => typeof d?.id === 'string' && typeof d.title === 'string' && Number.isFinite(d.installmentAmount) && Number.isInteger(d.totalInstallments) && d.firstDueDate && Number.isInteger(d.firstDueDate.y)) &&
    v.installments.every(i => typeof i?.id === 'string' && typeof i.debtId === 'string' && Number.isFinite(i.amount) && i.dueDate && Number.isInteger(i.dueDate.y) && i.dueDate.m >= 1 && i.dueDate.m <= 12 && i.dueDate.d >= 1 && i.dueDate.d <= 31 && typeof i.isPaid === 'boolean');
}
