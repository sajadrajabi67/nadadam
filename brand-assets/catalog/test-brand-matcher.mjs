import assert from "node:assert/strict";
import { matchBrand } from "./brand-matcher.js";

const cases = [
  ["وام مسکن سجاد", "maskan"],
  ["قسط بلو بانک", "blu-bank"],
  ["پرداخت اسنپ پی", "snapp-pay"],
  ["دیجی پی ماهانه", "digipay"],
  ["کارت بانک ملی", "melli"]
];
for (const [input, expected] of cases) {
  const result = matchBrand(input);
  assert.equal(result.status, "match", input);
  assert.equal(result.brand.id, expected, input);
}
assert.equal(matchBrand("عنوان کاملاً نامرتبط").status, "no_match");

// "بانک سپه" deliberately exists as the generic Sepah alias and as the
// parent-bank alias for the legacy merged Ansar entry: never guess between them.
assert.equal(matchBrand("بانک سپه").status, "ambiguity");
assert.equal(matchBrand("بانک سپه انصار").brand.id, "sepah-merged-ansar");
console.log("brand matcher: 8 assertions passed");
