import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
const catalog = JSON.parse(fs.readFileSync(path.join(here, "brand-catalog.json"), "utf8"));

export function normalizeBrandText(value = "") {
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

export function matchBrand(title, brands = catalog.brands) {
  const normalizedTitle = normalizeBrandText(title);
  if (!normalizedTitle) return { status: "no_match", brand: null, matches: [] };

  const found = [];
  for (const brand of brands) {
    for (const alias of brand.aliases ?? []) {
      const normalizedAlias = normalizeBrandText(alias);
      if (normalizedAlias && normalizedTitle.includes(normalizedAlias)) {
        found.push({ brand, alias, normalizedAlias, length: normalizedAlias.length });
      }
    }
  }
  if (!found.length) return { status: "no_match", brand: null, matches: [] };

  const longest = Math.max(...found.map(item => item.length));
  const best = found.filter(item => item.length === longest);
  const byId = new Map();
  for (const item of best) if (!byId.has(item.brand.id)) byId.set(item.brand.id, item);

  const matches = [...byId.values()].map(({ brand, alias }) => ({
    id: brand.id, name_fa: brand.name_fa, asset_status: brand.asset_status,
    logo_path: brand.logo_path, matched_alias: alias
  }));
  if (matches.length > 1) return { status: "ambiguity", brand: null, matches };
  return { status: "match", brand: matches[0], matches };
}
