const sample = [
  { first: "کاربر", last: "نمونه", phones: ["۰۹۱۲۰۰۰۰۰۰۱", "+989120000001"] },
  { first: "Synthetic", last: "International", phones: ["+989300000002", "09120000003"] },
  { first: "", last: "", phones: ["09880000004", ""] },
  { first: "Synthetic", last: "Rejected", phones: ["invalid", "02100000000"] },
  { first: "Synthetic", last: "Shared number", phones: ["09120000001", ""] }
];
const digitMap = new Map([..."۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩"].map((digit, index) => [digit, String(index % 10)]));
const operatorPriority = ["MCI", "Irancell", "Rightel"];
function normalizePhone(value) {
  let raw = String(value ?? "");
  if (raw.length > 64) return null;
  raw = [...raw].map(char => digitMap.get(char) ?? char).join("").replace(/^ +| +$/g, "");
  if (!raw.trim() || !/^[0-9+ ().-]+$/.test(raw) || (raw.match(/\+/g) || []).length > 1 || (raw.includes("+") && !raw.startsWith("+"))) return null;
  let digits = raw.replace(/\D/g, "");
  if (raw.startsWith("+") && !digits.startsWith("98")) return null;
  if (digits.startsWith("0098")) digits = `0${digits.slice(4)}`;
  else if (digits.startsWith("98")) digits = `0${digits.slice(2)}`;
  else if (digits.length === 10 && digits.startsWith("9")) digits = `0${digits}`;
  return /^09\d{9}$/.test(digits) ? digits : null;
}
function operatorFor(phone) {
  if (/^(?:091\d{8}|099[012]\d{7})$/.test(phone)) return "MCI";
  if (/^(?:093[035-9]\d{7}|090[0-5]\d{7})$/.test(phone)) return "Irancell";
  if (/^092[0-3]\d{7}$/.test(phone)) return "Rightel";
  return "Other/Unknown";
}
function processContacts(records) {
  const selected = [], stats = { inputRows: records.length, outputRows: 0, invalidPhoneValues: 0, duplicateNumbersWithinRows: 0, rowsWithMultipleCandidates: 0, repeatedSelectedNumbers: 0, rowsWithoutNames: 0, selectedOperators: {} }, seenSelected = new Set();
  for (const record of records) {
    const candidates = [], seenInRow = new Set();
    for (const raw of (record.phones || []).slice(0, 4)) {
      if (raw == null || !String(raw).trim()) continue;
      const normalized = normalizePhone(raw);
      if (!normalized) { stats.invalidPhoneValues++; continue; }
      if (seenInRow.has(normalized)) { stats.duplicateNumbersWithinRows++; continue; }
      seenInRow.add(normalized); candidates.push({ number: normalized, operator: operatorFor(normalized) });
    }
    if (candidates.length > 1) stats.rowsWithMultipleCandidates++;
    candidates.sort((a, b) => { const ai = operatorPriority.indexOf(a.operator), bi = operatorPriority.indexOf(b.operator); return (ai < 0 ? 3 : ai) - (bi < 0 ? 3 : bi); });
    const chosen = candidates[0];
    if (!chosen) continue;
    if (seenSelected.has(chosen.number)) stats.repeatedSelectedNumbers++;
    seenSelected.add(chosen.number); stats.outputRows++;
    stats.selectedOperators[chosen.operator] = (stats.selectedOperators[chosen.operator] || 0) + 1;
    if (![record.first, record.last].some(name => String(name || "").trim())) stats.rowsWithoutNames++;
    selected.push({ first: String(record.first || "").trim(), last: String(record.last || "").trim(), phone: chosen.number, operator: chosen.operator, review: record.phones.some(p => p && !normalizePhone(p)) });
  }
  stats.rejectedRows = stats.inputRows - stats.outputRows;
  return { selected, stats };
}
if (typeof module !== "undefined") module.exports = { normalizePhone, operatorFor, processContacts, sample };
if (typeof document !== "undefined") {
  const sourceBody = document.querySelector("#source-rows"), resultBody = document.querySelector("#result-rows"), view = document.querySelector("#view"), run = document.querySelector("#run"), reset = document.querySelector("#reset");
  const names = record => [record.first, record.last].filter(Boolean).join(" ") || "Unnamed synthetic record";
  function sourceRow(record) {
    const tr = document.createElement("tr"), name = document.createElement("td"), values = document.createElement("td"); name.textContent = names(record); values.className = "phone-values"; values.textContent = record.phones.filter(Boolean).join(" · ") || "No phone values"; tr.append(name, values); return tr;
  }
  sourceBody.replaceChildren(...sample.map(sourceRow));
  function render() {
    const { selected, stats } = processContacts(sample);
    for (const [id, value] of [["input", stats.inputRows], ["output", stats.outputRows], ["rejected", stats.rejectedRows], ["duplicates", stats.duplicateNumbersWithinRows], ["shared", stats.repeatedSelectedNumbers]]) document.querySelector(`#metric-${id}`).textContent = value;
    const acceptedIndexes = new Set(selected.map(row => sample.findIndex(s => names(s) === `${row.first} ${row.last}`)));
    const shown = sample.map((record, i) => ({ record, result: selected.find(s => names(s) === names(record)), accepted: acceptedIndexes.has(i) })).filter(item => view.value === "all" || (view.value === "accepted" ? item.accepted : !item.accepted));
    resultBody.replaceChildren(...shown.map(({ record, result }) => {
      const tr = document.createElement("tr"), name = document.createElement("td"), phone = document.createElement("td"), op = document.createElement("td"), status = document.createElement("td");
      name.textContent = names(record); phone.textContent = result?.phone || "—"; phone.className = result ? "phone-values" : "muted"; op.textContent = result?.operator || "—"; op.className = "muted";
      const pill = document.createElement("span"); pill.className = `pill${result ? "" : " review"}`; pill.textContent = result ? "Accepted" : "Needs review"; status.append(pill); tr.append(name, phone, op, status); return tr;
    }));
    document.querySelector("#empty").hidden = shown.length > 0;
    document.querySelector("#row-count").textContent = `${shown.length} ${shown.length === 1 ? "record" : "records"} shown`;
    document.querySelector("#status").textContent = `Processed ${stats.inputRows} fictional records locally`;
  }
  run.addEventListener("click", render); view.addEventListener("change", render);
  reset.addEventListener("click", () => { view.value = "all"; for (const id of ["input", "output", "rejected", "duplicates", "shared"]) document.querySelector(`#metric-${id}`).textContent = "—"; resultBody.replaceChildren(); document.querySelector("#empty").hidden = true; document.querySelector("#status").textContent = "Ready"; document.querySelector("#row-count").textContent = "Run the sample to see results"; run.focus(); });
}

