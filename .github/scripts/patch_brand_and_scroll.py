from pathlib import Path
import re

p = Path("src/App.tsx")
s = p.read_text(encoding="utf-8")

# Remove only the explanatory sentence; keep the reminder label and controls intact.
s, removed = re.subn(
    r'<small className="block pt-1 font-normal text-amber-700">اعلان‌ها در ساعت انتخابی، حتی با بسته‌بودن برنامه زمان‌بندی می‌شوند\.</small>',
    '',
    s,
    count=1
)
if removed != 1:
    raise SystemExit(f"Expected the exact reminder sentence once; found {removed}.")

# Every page entry (including browser back/forward) starts at the top.
anchor = "  const navigate = (next:Page) => { setMenu(null); setPage(next); window.history.pushState({ page: next }, ''); };"
if anchor not in s:
    raise SystemExit("Navigation anchor not found.")
effect = """
  useEffect(() => {
    window.scrollTo(0, 0);
    document.documentElement.scrollTop = 0;
    document.body.scrollTop = 0;
  }, [page]);
"""
if "document.documentElement.scrollTop = 0;" not in s:
    s = s.replace(anchor, anchor + effect, 1)

p.write_text(s, encoding="utf-8")
print("Brand and page-entry scroll behavior applied.")
