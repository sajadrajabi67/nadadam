from pathlib import Path

logic = Path("src/logic.ts")
s = logic.read_text(encoding="utf-8")
old = """export function createInstallments(debt: Debt): Installment[] {
  return Array.from({ length: debt.totalInstallments }, (_, index) => ({ id: crypto.randomUUID(), debtId: debt.id, installmentNumber: index + 1, amount: debt.installmentAmount, dueDate: addMonthsClamped(debt.firstDueDate, index), isPaid: false, paidAt: null, notes: '' }));
}"""
new = """export function createId(): string {
  const cryptoApi = globalThis.crypto;
  if (cryptoApi && typeof cryptoApi.randomUUID === 'function') return cryptoApi.randomUUID();
  const bytes = new Uint8Array(16);
  if (cryptoApi && typeof cryptoApi.getRandomValues === 'function') cryptoApi.getRandomValues(bytes);
  else for (let i = 0; i < bytes.length; i++) bytes[i] = Math.floor(Math.random() * 256);
  bytes[6] = (bytes[6] & 0x0f) | 0x40;
  bytes[8] = (bytes[8] & 0x3f) | 0x80;
  const hex = Array.from(bytes, b => b.toString(16).padStart(2, '0')).join('');
  return hex.slice(0, 8) + '-' + hex.slice(8, 12) + '-' + hex.slice(12, 16) + '-' + hex.slice(16, 20) + '-' + hex.slice(20);
}
export function createInstallments(debt: Debt): Installment[] {
  if (!Number.isInteger(debt.totalInstallments) || debt.totalInstallments < 1 || debt.totalInstallments > 600) throw new Error('تعداد اقساط نامعتبر است');
  toGregorian(debt.firstDueDate);
  return Array.from({ length: debt.totalInstallments }, (_, index) => ({
    id: createId(), debtId: debt.id, installmentNumber: index + 1,
    amount: debt.installmentAmount, dueDate: addMonthsClamped(debt.firstDueDate, index),
    isPaid: false, paidAt: null, notes: ''
  }));
}"""
if old not in s: raise SystemExit("createInstallments block not found")
logic.write_text(s.replace(old,new,1),encoding="utf-8")

app = Path("src/App.tsx")
s = app.read_text(encoding="utf-8")
s = s.replace("compare, createInstallments, dateLabel", "compare, createId, createInstallments, dateLabel", 1)
old = """      const debt:Debt={id:crypto.randomUUID(),title:title.trim(),installmentAmount:value,totalInstallments:duration,firstDueDate:due,createdAt:Date.now(),notes:notes.trim(),active:true};
      if (commit({ ...store, debts:[...store.debts,debt], installments:[...store.installments,...createInstallments(debt).map(i=>({...i,notes:notes.trim()}))] })) { setMonth({ ...due,d:1 }); notice('قسطت با موفقیت ثبت شد.'); navigate('home'); }"""
new = """      try {
        const debt:Debt={id:createId(),title:title.trim(),installmentAmount:value,totalInstallments:duration,firstDueDate:due,createdAt:Date.now(),notes:notes.trim(),active:true};
        const newInstallments=createInstallments(debt).map(i=>({...i,notes:notes.trim()}));
        if (newInstallments.length !== duration) throw new Error('تعداد اقساط ساخته‌شده کامل نیست');
        const next:Store={...store,debts:[...store.debts,debt],installments:[...store.installments,...newInstallments]};
        if (commit(next)) { setMonth({ ...due,d:1 }); notice('قسطت با موفقیت ثبت شد.'); navigate('home'); }
      } catch (error) {
        console.error('Debt save failed before commit:', error);
        notice('ثبت قسط انجام نشد؛ اطلاعات قبلی محفوظ ماند. دوباره تلاش کن.');
      }"""
if old not in s: raise SystemExit("new debt save block not found")
app.write_text(s.replace(old,new,1),encoding="utf-8")
print("Safe debt creation patch applied.")
