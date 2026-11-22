from pathlib import Path

app = Path("src/App.tsx")
source = app.read_text(encoding="utf-8")
anchor = "  {page==='home'&&<>"
card = """  {page==='home'&&<><section data-testid="creator-credit" aria-label="سازنده برنامه" className="mb-4 rounded-2xl border border-[#D7E5E1] bg-white px-4 py-3 text-center shadow-sm"><p dir="ltr" className="text-base font-black tracking-wide text-[#0B1F2A]">Sajad Rajabi</p><p dir="ltr" className="mt-1 text-xs font-semibold text-slate-500">@Sajadrajabi67 Instagram &amp; Telegram</p></section>"""
if source.count(anchor) != 1:
    raise SystemExit(f"Expected exactly one home-page anchor, found {source.count(anchor)}")
source = source.replace(anchor, card, 1)
app.write_text(source, encoding="utf-8")
print("Added the creator credit card to the home page only.")
