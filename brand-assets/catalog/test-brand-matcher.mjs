import assert from "node:assert/strict";
import { matchBrand, matchDocumentType } from "./brand-matcher.js";

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


const approvedBrandCases = [
  ["پیگیری ازکی وام", "azkivam"],
  ["خرید اقساطی لندو", "lendo"],
  ["پرداخت تکنوپی", "technopay"],
  ["اعتبار ونسی", "vency"],
  ["پرداخت جی اس ام پی", "gsmpay"],
  ["وی پاد", "vepod"],
  ["دیما بانک ملت", "dima"],
  ["خرید اعتباری سلام پی", "salam-pay"],
  ["تارا ۳۶۰", "tara"],
  ["بانکینو", "bankino"]
];
for (const [input, expected] of approvedBrandCases) {
  const result = matchBrand(input);
  assert.equal(result.status, "match", input);
  assert.equal(result.brand.id, expected, input);
}
assert.equal(matchBrand("دیما").brand.logo_brand_fa, "بانک ملت");
assert.equal(matchBrand("سلام پی").brand.logo_brand_fa, "باسلام");

const cheque = matchDocumentType("تصویر برگه چک صیادی");
assert.equal(cheque.status, "match");
assert.equal(cheque.document_type.id, "bank-cheque");
assert.equal(matchDocumentType("یک رسید عادی خرید").status, "no_match");
console.log("approved brands and cheque: 25 additional assertions passed");

// Services not selected for this release must not be recognized.
for (const [input] of [["دیجی‌شهر","dgshahr"],["بالون","baloon"],["ایزی‌پی","easy-pay"],["وای‌چک","vaycheck"],["وامینه","vamineh"],["باجت","bajet"],["نوپی","noopi"],["کالاکارت مهر ایران","kalakart-mehr-iran"],["اعتباری‌نو","etebari-no"],["قسطا","ghesta"],["ترب‌پی","torobpay"],["کیپا","keepa"],["مانیسا","manisa"]]) {
  assert.equal(matchBrand(input).status, "no_match", input);
}
console.log("excluded/unselected services: 13 negative assertions passed");
