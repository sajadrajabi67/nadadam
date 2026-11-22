from pathlib import Path

app = Path("src/App.tsx")
s = app.read_text(encoding="utf-8")

s = s.replace(
    "import { Capacitor } from '@capacitor/core';",
    "import { Capacitor, registerPlugin } from '@capacitor/core';",
    1
)
anchor = "const button = 'min-h-11 rounded-2xl px-4 font-bold transition active:scale-[.98] focus-visible:outline-2 focus-visible:outline-[#0F9D8A]';"
plugin_types = """
type BackupStoragePlugin = {
  saveBackup(options: { fileName: string; content: string }): Promise<{ uri: string }>;
};
const BackupStorage = registerPlugin<BackupStoragePlugin>('BackupStorage');
"""
if anchor not in s: raise SystemExit("UI constants anchor not found")
s = s.replace(anchor, anchor + plugin_types, 1)

state_anchor = "  const [confirm, setConfirm] = useState<{ kind:'installment'|'debt'|'all'; id?:string; scope?:'single'|'all' }|null>(null);"
if state_anchor not in s: raise SystemExit("confirmation state anchor not found")
s = s.replace(state_anchor, state_anchor + """
  const [actionConfirm, setActionConfirm] = useState<{ kind:'duplicate'|'import' }|null>(null);
  const [pendingImport, setPendingImport] = useState<Store|null>(null);
""", 1)
ref_anchor = "  const fileRef = useRef<HTMLInputElement>(null);"
if ref_anchor not in s: raise SystemExit("file input ref anchor not found")
s = s.replace(ref_anchor, ref_anchor + "\n  const allowDuplicateRef = useRef(false);", 1)

old_duplicate = "if (duplicate && !window.confirm('به نظر می‌رسد بدهی مشابهی قبلاً ثبت شده است. آیا می‌خواهید ادامه دهید؟')) return;"
new_duplicate = "if (duplicate && !allowDuplicateRef.current) { setActionConfirm({kind:'duplicate'}); return; } allowDuplicateRef.current = false;"
if old_duplicate not in s: raise SystemExit("duplicate native confirm not found")
s = s.replace(old_duplicate, new_duplicate, 1)

old_export = "const exportData = () => { const blob=new Blob([JSON.stringify({format:'debt-manager-v1',data:store},null,2)],{type:'application/json'}); const url=URL.createObjectURL(blob); const a=document.createElement('a'); a.href=url; a.download='nadadam-backup.json'; document.body.appendChild(a); a.click(); a.remove(); setTimeout(()=>URL.revokeObjectURL(url),1000); notice('فایل در پوشهٔ دانلود ذخیره شد.'); };"
new_export = """const exportData = async () => {
    const data = JSON.stringify({format:'debt-manager-v1',data:store}, null, 2);
    const current = today();
    const pad = (value:number) => fa(String(value).padStart(2, '0'));
    const fileName = 'ندادم_' + fa(current.y) + '-' + pad(current.m) + '-' + pad(current.d) + '.json';
    try {
      if (Capacitor.isNativePlatform()) {
        await BackupStorage.saveBackup({fileName, content:data});
        notice('پشتیبان در پوشه دانلودها/ندادم ذخیره شد.');
      } else {
        const blob = new Blob([data], {type:'application/json'});
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url; a.download = fileName;
        document.body.appendChild(a); a.click(); a.remove();
        setTimeout(() => URL.revokeObjectURL(url), 1000);
        notice('فایل پشتیبان دانلود شد.');
      }
    } catch (error) {
      console.error('Backup export failed:', error);
      notice('ذخیره فایل پشتیبان انجام نشد؛ دوباره تلاش کن.');
    }
  };"""
if old_export not in s: raise SystemExit("exportData block not found")
s = s.replace(old_export, new_export, 1)

old_import = "const importData = async (file?:File) => { if (!file) return; try { const parsed=JSON.parse(await file.text()); if (parsed.format!=='debt-manager-v1' || !isStore(parsed.data)) throw new Error('invalid'); if (!window.confirm('اطلاعات فعلی با اطلاعات فایل جایگزین شوند؟')) return; if(commit(parsed.data)) { notice('اطلاعات بازیابی شد.'); navigate('home'); } } catch { notice('فایل پشتیبان معتبر نیست.'); } finally { if(fileRef.current) fileRef.current.value=''; } };"
new_import = """const importData = async (file?:File) => {
    if (!file) return;
    try {
      const parsed = JSON.parse(await file.text());
      if (parsed.format !== 'debt-manager-v1' || !isStore(parsed.data)) throw new Error('invalid');
      setPendingImport(parsed.data);
      setActionConfirm({kind:'import'});
    } catch {
      notice('فایل پشتیبان معتبر نیست.');
    } finally {
      if (fileRef.current) fileRef.current.value = '';
    }
  };
  const confirmPendingAction = () => {
    const action = actionConfirm;
    setActionConfirm(null);
    if (!action) return;
    if (action.kind === 'duplicate') {
      allowDuplicateRef.current = true;
      save();
      return;
    }
    if (pendingImport && commit(pendingImport)) {
      notice('اطلاعات بازیابی شد.');
      navigate('home');
    }
    setPendingImport(null);
  };"""
if old_import not in s: raise SystemExit("importData block not found")
s = s.replace(old_import, new_import, 1)

modal_anchor = "  {payAsk&&<div role=\\"dialog\\""
modal = """  {actionConfirm&&<div role="dialog" aria-modal="true" aria-labelledby="action-confirm-title" className="fixed inset-0 z-[55] flex items-center justify-center bg-slate-900/50 p-4"><div className="w-full max-w-sm rounded-[28px] bg-white p-6 text-[#0B1F2A] shadow-2xl"><div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-[#E3F5F2] text-[#0F9D8A]"><CircleHelp size={28}/></div><h3 id="action-confirm-title" className="text-center text-lg font-black">{actionConfirm.kind==='duplicate'?'ثبت بدهی مشابه':'بازیابی اطلاعات'}</h3><p className="mt-3 text-center text-sm leading-7 text-slate-600">{actionConfirm.kind==='duplicate'?'به نظر می‌رسد بدهی مشابهی قبلاً ثبت شده است. با این حال می‌خواهی بدهی جدید ثبت شود؟':'اطلاعات فعلی با اطلاعات فایل پشتیبان جایگزین می‌شوند. ادامه می‌دهی؟'}</p><div className="mt-6 grid gap-3"><button data-testid="action-confirm-yes" onClick={confirmPendingAction} className={button + ' w-full bg-[linear-gradient(135deg,#14B8A6,#0B6E63)] text-white shadow-lg shadow-teal-300/30'}>بله، ادامه بده</button><button data-testid="action-confirm-no" onClick={()=>{setActionConfirm(null);setPendingImport(null);allowDuplicateRef.current=false;}} className={button + ' w-full bg-slate-100 text-slate-700'}>انصراف</button></div></div></div>}
"""
if modal_anchor not in s: raise SystemExit("pay confirmation modal anchor not found")
s = s.replace(modal_anchor, modal + modal_anchor, 1)

if "window.confirm(" in s:
    raise SystemExit("A native browser confirm() remains in App.tsx")
app.write_text(s, encoding="utf-8")
print("Replaced browser-native confirmation dialogs and updated dated backup export.")
