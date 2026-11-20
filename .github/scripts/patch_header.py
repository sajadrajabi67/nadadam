from pathlib import Path

p = Path("src/App.tsx")
s = p.read_text(encoding="utf-8")

old_header = '''return <div dir="rtl" className="min-h-screen bg-[#F3F6F5] pb-28 text-[#0B1F2A] sm:pb-8"><div className="mx-auto w-full max-w-3xl px-4 sm:px-6"><header className="flex items-center gap-3 py-5">'''
new_header = '''return <div dir="rtl" className="min-h-screen bg-[#F3F6F5] pb-28 text-[#0B1F2A] sm:pb-8"><div className="fixed inset-x-0 top-0 z-40 bg-[linear-gradient(to_bottom,#F3F6F5_0%,rgba(243,246,245,0.98)_68%,rgba(243,246,245,0)_100%)]"><div className="mx-auto w-full max-w-3xl px-4 sm:px-6"><header className="flex items-center gap-3 pt-7 pb-8">'''
if old_header not in s:
    raise SystemExit("Expected original header opening was not found; refusing to patch.")
s = s.replace(old_header, new_header, 1)

old_main = '''</header>
  <main className="py-6">'''
new_main = '''</header></div></div><div className="mx-auto w-full max-w-3xl px-4 sm:px-6">
  <main className="pt-32 pb-6">'''
if old_main not in s:
    raise SystemExit("Expected main opening was not found; refusing to patch.")
s = s.replace(old_main, new_main, 1)

if 'className="fixed inset-x-0 top-0 z-40 bg-[linear-gradient(to_bottom' not in s or 'className="pt-32 pb-6"' not in s:
    raise SystemExit("Header patch verification failed.")
p.write_text(s, encoding="utf-8")
print("Header fixed-position and fading-bottom treatment applied.")
