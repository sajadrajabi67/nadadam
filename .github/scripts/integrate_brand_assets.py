from pathlib import Path
import json
import shutil

ROOT = Path(__file__).resolve().parents[2]
PROJECT = Path.cwd()
APP = PROJECT / "src" / "App.tsx"
CATALOG = ROOT / "brand-assets" / "catalog" / "brand-catalog.json"
LOGO_SOURCE = ROOT / "brand-assets" / "logos"
PUBLIC_LOGOS = PROJECT / "public" / "brand-logos"

if not APP.is_file() or not CATALOG.is_file():
    raise SystemExit("App.tsx or brand catalog was not found; refusing to continue.")

catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
brands = catalog.get("brands", [])
available = [b for b in brands if b.get("asset_status") == "available" and b.get("logo_path")]

PUBLIC_LOGOS.mkdir(parents=True, exist_ok=True)
copied = []
for brand in available:
    filename = Path(brand["logo_path"]).name
    source = LOGO_SOURCE / filename
    if not source.is_file() or source.suffix.lower() != ".svg":
        raise SystemExit(f"Missing or invalid SVG for {brand.get('id')}: {source}")
    shutil.copy2(source, PUBLIC_LOGOS / filename)
    copied.append(filename)

if len(copied) != len(available) or not copied:
    raise SystemExit("Logo copy verification failed.")

# Package the cheque reference image when its external source is reachable.
# It is optional so a temporary third-party redirect failure cannot block APK builds.
CHEQUE_SOURCE = ROOT / "brand-assets" / "references" / "bank-cheque.gif"
if CHEQUE_SOURCE.is_file() and CHEQUE_SOURCE.stat().st_size >= 5000:
    PUBLIC_REFERENCES = PROJECT / "public" / "reference-images"
    PUBLIC_REFERENCES.mkdir(parents=True, exist_ok=True)
    shutil.copy2(CHEQUE_SOURCE, PUBLIC_REFERENCES / "bank-cheque.gif")
else:
    print("Optional cheque reference image unavailable; continuing without it.")

runtime_catalog = {
    "brands": [
        {
            "id": b["id"],
            "name_fa": b["name_fa"],
            "aliases": b.get("aliases", []),
            "logo_path": b.get("logo_path"),
            "asset_status": b.get("asset_status", "pending"),
        }
        for b in brands
    ],
    "excluded_brand_names": catalog.get("excluded_brand_names", []),
    "document_types": [
        {
            "id": item["id"],
            "name_fa": item["name_fa"],
            "aliases": item.get("aliases", []),
            "asset_status": item.get("asset_status", "pending"),
            "reference_image_path": "/reference-images/bank-cheque.gif" if item.get("id") == "bank-cheque" else item.get("reference_image_path"),
        }
        for item in catalog.get("document_types", catalog.get("documentTypes", []))
    ],
}
catalog_json = json.dumps(runtime_catalog, ensure_ascii=False, separators=(",", ":"))
matcher = r'''
export const brandCatalog = __CATALOG__ as const;

export function normalizeBrandText(value = ""): string {
  return String(value)
    .normalize("NFKC")
    .replace(/[\u064B-\u065F\u0670\u0640]/g, "")
    .replace(/[يى]/g, "ی")
    .replace(/ك/g, "ک")
    .replace(/[\u200c\u200d]/g, " ")
    .toLowerCase()
    .replace(/[^\p{L}\p{N}]+/gu, " ")
    .trim()
    .replace(/\s+/g, " ");
}

export function matchBrand(title: string) {
  const normalizedTitle = normalizeBrandText(title);
  if (!normalizedTitle) return { status: "no_match" as const, brand: null, matches: [] as const };
  const excluded = brandCatalog.excluded_brand_names ?? [];
  if (excluded.some(name => {
    const normalized = normalizeBrandText(name);
    return normalized && (normalizedTitle === normalized || normalizedTitle.includes(" " + normalized + " ") || normalizedTitle.startsWith(normalized + " ") || normalizedTitle.endsWith(" " + normalized));
  })) return { status: "no_match" as const, brand: null, matches: [] as const };

  const found: Array<{ brand: typeof brandCatalog.brands[number]; alias: string; normalizedAlias: string; length: number }> = [];
  for (const brand of brandCatalog.brands) {
    for (const alias of brand.aliases) {
      const normalizedAlias = normalizeBrandText(alias);
      if (normalizedAlias && normalizedTitle.includes(normalizedAlias)) {
        found.push({ brand, alias, normalizedAlias, length: normalizedAlias.length });
      }
    }
  }
  if (!found.length) return { status: "no_match" as const, brand: null, matches: [] as const };

  const longest = Math.max(...found.map(item => item.length));
  const best = found.filter(item => item.length === longest);
  const byId = new Map<string, typeof best[number]>();
  for (const item of best) if (!byId.has(item.brand.id)) byId.set(item.brand.id, item);

  const matches = [...byId.values()].map(({ brand, alias }) => ({
    id: brand.id,
    name_fa: brand.name_fa,
    asset_status: brand.asset_status,
    logo_path: brand.logo_path,
    matched_alias: alias
  }));
  if (matches.length > 1) return { status: "ambiguity" as const, brand: null, matches };
  return { status: "match" as const, brand: matches[0], matches };
}

export function matchDocumentType(title: string) {
  const normalizedTitle = normalizeBrandText(title);
  if (!normalizedTitle) return { status: "no_match" as const, document_type: null, matches: [] as const };
  const found: Array<{ item: typeof brandCatalog.document_types[number]; alias: string; normalizedAlias: string; length: number }> = [];
  for (const item of brandCatalog.document_types) {
    for (const alias of item.aliases) {
      const normalizedAlias = normalizeBrandText(alias);
      if (normalizedAlias && normalizedTitle.includes(normalizedAlias)) {
        found.push({ item, alias, normalizedAlias, length: normalizedAlias.length });
      }
    }
  }
  if (!found.length) return { status: "no_match" as const, document_type: null, matches: [] as const };
  const longest = Math.max(...found.map(item => item.length));
  const best = found.filter(item => item.length === longest);
  const byId = new Map<string, typeof best[number]>();
  for (const item of best) if (!byId.has(item.item.id)) byId.set(item.item.id, item);
  const matches = [...byId.values()].map(({ item, alias }) => ({
    id: item.id,
    name_fa: item.name_fa,
    asset_status: item.asset_status,
    reference_image_path: item.reference_image_path,
    matched_alias: alias
  }));
  if (matches.length > 1) return { status: "ambiguity" as const, document_type: null, matches };
  return { status: "match" as const, document_type: matches[0], matches };
}
'''.replace("__CATALOG__", catalog_json)

(PROJECT / "src" / "brandCatalog.ts").write_text(matcher, encoding="utf-8")

s = APP.read_text(encoding="utf-8")
import_line = "import { matchBrand } from './brandCatalog';"
if import_line not in s:
    anchor = "import packageInfo from '../package.json';"
    if anchor not in s:
        raise SystemExit("Could not locate package import in App.tsx.")
    s = s.replace(anchor, anchor + "\n" + import_line, 1)

brand_helper = r'''
const brandMark = (value: string, size = "h-10 w-10") => {
  const result = matchBrand(value);
  if (result.status !== "match") return null;
  if (result.brand.asset_status !== "available" || !result.brand.logo_path) {
    return <span title={result.brand.name_fa + " (لوگو هنوز در آرشیو نیست)"} data-testid="brand-pending-mark" className={"flex " + size + " shrink-0 items-center justify-center rounded-xl bg-[#E3F5F2] px-1 text-[10px] font-black text-[#0B6E63] ring-1 ring-[#CDEBE6]"}>{result.brand.name_fa}</span>;
  }
  const filename = result.brand.logo_path.split("/").pop() || "";
  return <span title={result.brand.name_fa} className={"flex " + size + " shrink-0 items-center justify-center overflow-hidden rounded-xl bg-white p-1 ring-1 ring-slate-100"}><img src={"/brand-logos/" + encodeURIComponent(filename)} alt={"لوگوی " + result.brand.name_fa} className="h-full w-full object-contain" loading="lazy" decoding="async"/></span>;
};
'''
if "const brandMark = (" not in s:
    anchor = "const button = 'min-h-11 rounded-2xl px-4 font-bold transition active:scale-[.98] focus-visible:outline-2 focus-visible:outline-[#0F9D8A]';"
    if anchor not in s:
        raise SystemExit("Could not locate App style constants.")
    s = s.replace(anchor, anchor + "\n" + brand_helper, 1)

tick = chr(96)
old_installment = "<strong className={" + tick + "block break-words text-[15px] " + chr(36) + "{item.isPaid?'text-slate-400 line-through':'text-[#0B1F2A]'}" + tick + "}>{displayTitle(item)}</strong>"
new_installment = '<div className="flex min-w-0 items-center gap-2">{brandMark(displayTitle(item),\'h-9 w-9\')}<strong className={"block min-w-0 break-words text-[15px] " + (item.isPaid?\'text-slate-400 line-through\':\'text-[#0B1F2A]\')}>{displayTitle(item)}</strong></div>'
if 'brandMark(displayTitle(item)' not in s:
    if old_installment not in s:
        raise SystemExit("Could not locate installment title display.")
    s = s.replace(old_installment, new_installment, 1)

old_debt = '<strong className="block truncate text-lg">{d.title}</strong>'
new_debt = '<div className="flex min-w-0 items-center gap-2">{brandMark(d.title,\'h-10 w-10\')}<strong className="block min-w-0 truncate text-lg">{d.title}</strong></div>'
if 'brandMark(d.title' not in s:
    if old_debt not in s:
        raise SystemExit("Could not locate debt-list title display.")
    s = s.replace(old_debt, new_debt, 1)

old_detail = '<h2 className="mb-2 text-2xl font-extrabold">{selected.title}</h2>'
new_detail = '<div className="mb-2 flex items-center gap-3">{brandMark(selected.title,\'h-12 w-12\')}<h2 className="text-2xl font-extrabold">{selected.title}</h2></div>'
if 'brandMark(selected.title' not in s:
    if old_detail not in s:
        raise SystemExit("Could not locate debt detail heading.")
    s = s.replace(old_detail, new_detail, 1)

old_form = 'onChange={e=>setTitle(e.target.value)}/>{errors.title&&'
new_form = '''onChange={e=>setTitle(e.target.value)}/>{title.trim()&&(()=>{const found=matchBrand(title);if(found.status==='match'){return found.brand.asset_status==='available'?<div data-testid="brand-match" className="mt-3 flex items-center gap-3 rounded-2xl bg-[#F3F6F5] p-3">{brandMark(title,'h-11 w-11')}<span className="text-sm text-slate-600">برند شناسایی‌شده: <strong className="text-[#0B1F2A]">{found.brand.name_fa}</strong></span></div>:<p data-testid="brand-pending" className="mt-2 text-xs text-slate-500">نام {found.brand.name_fa} شناسایی شد؛ لوگوی آن در آرشیو فعلی موجود نیست.</p>;}if(found.status==='ambiguity')return <p data-testid="brand-ambiguous" className="mt-2 text-xs text-amber-700">چند برند مشابه پیدا شد؛ لطفاً نام دقیق‌تر بانک یا سرویس را وارد کن.</p>;return null;})()}{errors.title&&'''
if 'data-testid="brand-match"' not in s:
    if old_form not in s:
        raise SystemExit("Could not locate installment title input.")
    s = s.replace(old_form, new_form, 1)

APP.write_text(s, encoding="utf-8")
print(f"Integrated {len(copied)} verified SVG logos and brand recognition into App.tsx.")
