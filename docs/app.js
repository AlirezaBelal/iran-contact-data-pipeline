const sample = [
  { first: "کاربر", last: "نمونه", phones: ["۰۹۱۲۰۰۰۰۰۰۱", "+989120000001"] },
  { first: "Synthetic", last: "International", phones: ["+989300000002", "09120000003"] },
  { first: "", last: "", phones: ["09880000004", ""] },
  { first: "Synthetic", last: "Rejected", phones: ["invalid", "02100000000"] },
  { first: "Synthetic", last: "Shared number", phones: ["09120000001", ""] }
];
const digitMap = new Map([..."۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩"].map((digit, index) => [digit, String(index % 10)]));
const operatorPriority = ["MCI", "Irancell", "Rightel"];
const MAX_CSV_CHARS = 1_048_576;
const MAX_CSV_ROWS = 1_000;

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

function parseCsvRows(text) {
  if (typeof text !== "string" || text.length > MAX_CSV_CHARS) throw new Error("The CSV must be smaller than 1 MiB.");
  const input = text.replace(/^\uFEFF/, "");
  if (!input.trim()) throw new Error("The CSV file is empty.");
  const rows = [];
  let row = [], cell = "", quoted = false, afterQuote = false, atCellStart = true;
  const pushRow = () => {
    row.push(cell);
    if (row.some(value => value !== "")) rows.push(row);
    row = []; cell = ""; afterQuote = false; atCellStart = true;
    if (rows.length > MAX_CSV_ROWS + 1) throw new Error("The CSV can contain at most 1,000 contact rows.");
  };
  for (let i = 0; i < input.length; i++) {
    const char = input[i];
    if (quoted) {
      if (char === '"' && input[i + 1] === '"') { cell += '"'; i++; }
      else if (char === '"') { quoted = false; afterQuote = true; }
      else cell += char;
      continue;
    }
    if (afterQuote && char !== "," && char !== "\n" && char !== "\r") throw new Error("The CSV has characters after a closing quote.");
    if (char === '"') {
      if (!atCellStart) throw new Error("The CSV contains a quote outside a quoted field.");
      quoted = true; atCellStart = false;
    } else if (char === ",") {
      row.push(cell); cell = ""; afterQuote = false; atCellStart = true;
    } else if (char === "\n" || char === "\r") {
      if (char === "\r" && input[i + 1] === "\n") i++;
      pushRow();
    } else { cell += char; atCellStart = false; }
  }
  if (quoted) throw new Error("The CSV contains an unclosed quoted field.");
  if (cell !== "" || row.length) pushRow();
  if (rows.length < 2) throw new Error("The CSV needs a header row and at least one contact row.");
  return rows;
}

function parseCsvContacts(text) {
  const rows = parseCsvRows(text);
  const headers = rows.shift();
  if (new Set(headers).size !== headers.length) throw new Error("Duplicate CSV column names are not supported.");
  const required = ["First Name", "Last Name", "Phone 1 - Value"];
  if (required.some(name => !headers.includes(name))) throw new Error("Include First Name, Last Name, and Phone 1 - Value columns from the project CSV format.");
  const phoneColumns = [1, 2, 3, 4].map(index => headers.indexOf(`Phone ${index} - Value`));
  return rows.map((values, rowIndex) => {
    if (values.length > headers.length && values.slice(headers.length).some(value => value !== "")) throw new Error(`Row ${rowIndex + 2} has more values than the header.`);
    const valueFor = name => { const index = headers.indexOf(name); return index < 0 ? "" : (values[index] ?? ""); };
    return {
      first: valueFor("First Name"),
      last: valueFor("Last Name"),
      phones: phoneColumns.filter(index => index >= 0).map(index => values[index] ?? "")
    };
  });
}

function processContacts(records) {
  const selected = [], stats = { inputRows: records.length, outputRows: 0, invalidPhoneValues: 0, duplicateNumbersWithinRows: 0, rowsWithMultipleCandidates: 0, repeatedSelectedNumbers: 0, rowsWithoutNames: 0, selectedOperators: {} }, seenSelected = new Set();
  records.forEach((record, sourceIndex) => {
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
    if (!chosen) return;
    if (seenSelected.has(chosen.number)) stats.repeatedSelectedNumbers++;
    seenSelected.add(chosen.number); stats.outputRows++;
    stats.selectedOperators[chosen.operator] = (stats.selectedOperators[chosen.operator] || 0) + 1;
    if (![record.first, record.last].some(name => String(name || "").trim())) stats.rowsWithoutNames++;
    selected.push({ first: String(record.first || "").trim(), last: String(record.last || "").trim(), phone: chosen.number, operator: chosen.operator, review: (record.phones || []).some(p => p && !normalizePhone(p)), sourceIndex });
  });
  stats.rejectedRows = stats.inputRows - stats.outputRows;
  return { selected, stats };
}

function csvEscape(value) {
  let text = String(value ?? "");
  if (/^[=+\-@\t\r]/.test(text)) text = `'${text}`;
  return /[",\r\n]/.test(text) ? `"${text.replace(/"/g, '""')}"` : text;
}

function buildOutputCsv(selected) {
  const lines = [["first_name", "last_name", "selected_phone", "mobile_operator"].join(",")];
  for (const row of selected) lines.push([row.first, row.last, row.phone, row.operator].map(csvEscape).join(","));
  return `\uFEFF${lines.join("\r\n")}\r\n`;
}

if (typeof module !== "undefined") module.exports = { normalizePhone, operatorFor, processContacts, parseCsvRows, parseCsvContacts, buildOutputCsv, sample };

if (typeof document !== "undefined") {
  const sourceBody = document.querySelector("#source-rows"), resultBody = document.querySelector("#result-rows"), view = document.querySelector("#view"), run = document.querySelector("#run"), reset = document.querySelector("#reset");
  const fileInput = document.querySelector("#contact-file"), runFile = document.querySelector("#run-file"), exportButton = document.querySelector("#export"), fileError = document.querySelector("#file-error");
  const names = record => [record.first, record.last].filter(Boolean).join(" ") || "Unnamed record";
  let fileRecords = null, lastSelected = [];
  function sourceRow(record) {
    const tr = document.createElement("tr"), name = document.createElement("td"), values = document.createElement("td");
    name.textContent = names(record); values.className = "phone-values"; values.textContent = (record.phones || []).filter(Boolean).join(" · ") || "No phone values"; tr.append(name, values); return tr;
  }
  function render(records, sourceLabel) {
    const { selected, stats } = processContacts(records); lastSelected = selected;
    for (const [id, value] of [["input", stats.inputRows], ["output", stats.outputRows], ["rejected", stats.rejectedRows], ["duplicates", stats.duplicateNumbersWithinRows], ["shared", stats.repeatedSelectedNumbers]]) document.querySelector(`#metric-${id}`).textContent = value;
    const acceptedIndexes = new Set(selected.map(row => row.sourceIndex));
    const byIndex = new Map(selected.map(row => [row.sourceIndex, row]));
    const shown = records.map((record, i) => ({ record, result: byIndex.get(i), accepted: acceptedIndexes.has(i) })).filter(item => view.value === "all" || (view.value === "accepted" ? item.accepted : !item.accepted));
    sourceBody.replaceChildren(...records.map(sourceRow));
    resultBody.replaceChildren(...shown.map(({ record, result }) => {
      const tr = document.createElement("tr"), name = document.createElement("td"), phone = document.createElement("td"), op = document.createElement("td"), status = document.createElement("td");
      name.textContent = names(record); phone.textContent = result?.phone || "—"; phone.className = result ? "phone-values" : "muted"; op.textContent = result?.operator || "—"; op.className = "muted";
      const pill = document.createElement("span"); pill.className = `pill${result ? "" : " review"}`; pill.textContent = result ? (result.review ? "Accepted · review extra value" : "Accepted") : "Needs review"; status.append(pill); tr.append(name, phone, op, status); return tr;
    }));
    document.querySelector("#empty").hidden = shown.length > 0;
    document.querySelector("#row-count").textContent = `${shown.length} ${shown.length === 1 ? "record" : "records"} shown`;
    document.querySelector("#status").textContent = sourceLabel;
    exportButton.disabled = selected.length === 0;
  }
  function showError(message) { fileError.textContent = message; fileError.hidden = false; }
  fileInput.addEventListener("change", async () => {
    fileError.hidden = true; fileError.textContent = ""; fileRecords = null; runFile.disabled = true;
    lastSelected = []; exportButton.disabled = true; view.value = "all"; resultBody.replaceChildren(); sourceBody.replaceChildren(); document.querySelector("#empty").hidden = true;
    for (const id of ["input", "output", "rejected", "duplicates", "shared"]) document.querySelector(`#metric-${id}`).textContent = "—";
    const file = fileInput.files?.[0];
    if (!file) return;
    if (file.size > MAX_CSV_CHARS) { showError("Choose a CSV file smaller than 1 MiB."); document.querySelector("#status").textContent = "File rejected · size limit"; return; }
    document.querySelector("#status").textContent = "Reading the selected file in this tab…";
    try {
      fileRecords = parseCsvContacts(await file.text());
      if (fileRecords.length > MAX_CSV_ROWS) throw new Error("The CSV can contain at most 1,000 contact rows.");
      runFile.disabled = false; sourceBody.replaceChildren(...fileRecords.map(sourceRow));
      document.querySelector("#status").textContent = `Loaded ${fileRecords.length} rows in this tab · ready to process`;
      document.querySelector("#row-count").textContent = "File parsed; choose Process file locally";
    } catch (error) { fileRecords = null; showError(error instanceof Error ? error.message : "The file could not be read."); document.querySelector("#status").textContent = "File not processed"; }
  });
  run.addEventListener("click", () => { fileInput.value = ""; fileRecords = null; runFile.disabled = true; render(sample, "Processed 5 synthetic sample records locally"); });
  runFile.addEventListener("click", () => { if (!fileRecords) return; view.value = "all"; render(fileRecords, `Processed ${fileRecords.length} rows locally in this tab · no upload or storage`); });
  view.addEventListener("change", () => {
    const current = fileRecords || sample;
    if (lastSelected.length || document.querySelector("#metric-input").textContent !== "—") render(current, document.querySelector("#status").textContent);
  });
  exportButton.addEventListener("click", () => {
    if (!lastSelected.length) return;
    const blob = new Blob([buildOutputCsv(lastSelected)], { type: "text/csv;charset=utf-8" });
    const link = document.createElement("a"); link.href = URL.createObjectURL(blob); link.download = "normalized-contacts.csv"; link.click();
    setTimeout(() => URL.revokeObjectURL(link.href), 0);
  });
  reset.addEventListener("click", () => {
    fileInput.value = ""; fileRecords = null; lastSelected = []; runFile.disabled = true; exportButton.disabled = true; view.value = "all"; fileError.hidden = true; fileError.textContent = "";
    for (const id of ["input", "output", "rejected", "duplicates", "shared"]) document.querySelector(`#metric-${id}`).textContent = "—";
    sourceBody.replaceChildren(); resultBody.replaceChildren(); document.querySelector("#empty").hidden = true; document.querySelector("#status").textContent = "Ready · no file has been uploaded or stored"; document.querySelector("#row-count").textContent = "Choose a file or run the synthetic sample"; reset.focus();
  });
}
