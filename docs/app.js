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
  if ([...raw].length > 64) return null;
  raw = [...raw].map(char => digitMap.get(char) ?? char).join("").replace(/^ +| +$/g, "");
  if (!raw.trim() || /[^0-9+ ().-]/.test(raw) || (raw.match(/\+/g) || []).length > 1 || (raw.includes("+") && !raw.startsWith("+"))) return null;
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
  if (typeof text !== "string" || new TextEncoder().encode(text).length > MAX_CSV_CHARS) throw new Error("The CSV must be smaller than 1 MiB.");
  const input = text.replace(/^\uFEFF/, "");
  if (!input.trim()) throw new Error("The CSV file is empty.");
  const rows = [];
  let row = [], cell = "", quoted = false, afterQuote = false, atCellStart = true;
  const pushRow = () => {
    row.push(cell);
    if (row.length > 1 || cell !== "" || !atCellStart) rows.push(row);
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
    if (values.length !== headers.length) throw new Error(`Record ${rowIndex + 1} has an inconsistent column count; match the header.`);
    const valueFor = name => { const index = headers.indexOf(name); return index < 0 ? "" : (values[index] ?? ""); };
    return {
      first: valueFor("First Name"),
      last: valueFor("Last Name"),
      phones: phoneColumns.filter(index => index >= 0).map(index => values[index] ?? "")
    };
  });
}

// Match Python str.strip whitespace for core parity (JS trim treats BOM differently).
const pythonStrip = value => String(value ?? "").replace(/^[\u0009-\u000d\u001c-\u0020\u0085\u00a0\u1680\u2000-\u200a\u2028\u2029\u202f\u205f\u3000]+|[\u0009-\u000d\u001c-\u0020\u0085\u00a0\u1680\u2000-\u200a\u2028\u2029\u202f\u205f\u3000]+$/gu, "");

function processContacts(records) {
  const selected = [], stats = { inputRows: records.length, outputRows: 0, invalidPhoneValues: 0, duplicateNumbersWithinRows: 0, rowsWithMultipleCandidates: 0, repeatedSelectedNumbers: 0, rowsWithoutNames: 0, selectedOperators: {} }, seenSelected = new Set();
  const outcomes = [];
  records.forEach((record, sourceIndex) => {
    const candidates = [], seenInRow = new Set();
    let invalid = 0, duplicates = 0;
    for (const raw of (record.phones || []).slice(0, 4)) {
      if (raw == null || !pythonStrip(raw)) continue;
      const normalized = normalizePhone(raw);
      if (!normalized) { stats.invalidPhoneValues++; invalid++; continue; }
      if (seenInRow.has(normalized)) { stats.duplicateNumbersWithinRows++; duplicates++; continue; }
      seenInRow.add(normalized); candidates.push({ number: normalized, operator: operatorFor(normalized) });
    }
    if (candidates.length > 1) stats.rowsWithMultipleCandidates++;
    candidates.sort((a, b) => { const ai = operatorPriority.indexOf(a.operator), bi = operatorPriority.indexOf(b.operator); return (ai < 0 ? 3 : ai) - (bi < 0 ? 3 : bi); });
    const chosen = candidates[0];
    const unnamed = ![record.first, record.last].some(name => pythonStrip(name));
    const shared = chosen ? seenSelected.has(chosen.number) : false;
    const reasons = [];
    if (!chosen) reasons.push("no-mobile");
    if (invalid) reasons.push("invalid");
    if (candidates.length > 1) reasons.push("multiple");
    if (shared) reasons.push("shared");
    if (chosen && unnamed) reasons.push("unnamed");
    if (chosen?.operator === "Other/Unknown") reasons.push("unknown");
    outcomes.push({ sourceIndex, reasons, invalid, duplicates, review: reasons.length > 0 });
    if (!chosen) return;
    if (shared) stats.repeatedSelectedNumbers++;
    seenSelected.add(chosen.number); stats.outputRows++;
    stats.selectedOperators[chosen.operator] = (stats.selectedOperators[chosen.operator] || 0) + 1;
    if (unnamed) stats.rowsWithoutNames++;
    selected.push({ first: pythonStrip(record.first), last: pythonStrip(record.last), phone: chosen.number, operator: chosen.operator, review: reasons.length > 0, sourceIndex });
  });
  stats.reviewRows = outcomes.filter(row => row.review).length;
  stats.rejectedRows = stats.inputRows - stats.outputRows;
  return { selected, stats, outcomes };
}

function csvEscape(value) {
  let text = String(value ?? "");
  if (/^[\s\u0000-\u001f]*[=+\-@]/u.test(text) || /^[\t\r\n]/.test(text)) text = `'${text}`;
  return /[",\r\n]/.test(text) ? `"${text.replace(/"/g, '""')}"` : text;
}

function buildOutputCsv(selected) {
  const lines = [["first_name", "last_name", "selected_phone", "mobile_operator"].join(",")];
  for (const row of selected) lines.push([row.first, row.last, row.phone, row.operator].map(csvEscape).join(","));
  return `\uFEFF${lines.join("\r\n")}\r\n`;
}

if (typeof module !== "undefined") module.exports = { normalizePhone, operatorFor, processContacts, parseCsvRows, parseCsvContacts, buildOutputCsv, sample };

if (typeof document !== "undefined") {
  const $ = id => document.getElementById(id);
  const fileInput = $("contact-file"), runFile = $("run-file"), exportButton = $("export"), view = $("view");
  const metricKeys = { input: "inputRows", output: "outputRows", rejected: "rejectedRows", invalid: "invalidPhoneValues", duplicates: "duplicateNumbersWithinRows", shared: "repeatedSelectedNumbers", review: "reviewRows" };
  const reasons = { "no-mobile": "بدون شماره معتبر", invalid: "مقدار نامعتبر", multiple: "چند گزینه معتبر", shared: "شماره تکراری بین ردیف‌ها", unnamed: "بدون نام", unknown: "گروه پیش‌شماره نامشخص" };
  const count = new Intl.NumberFormat("fa-IR");
  const PAGE_SIZE = 25;
  let records = null, result = null, page = 0, generation = 0;
  const status = text => { $("status").textContent = text; };
  const cell = (tr, text, cls, dir) => { const td = document.createElement("td"); td.textContent = text; if (cls) td.className = cls; td.dir = dir || "auto"; tr.append(td); };
  const name = record => [record.first, record.last].filter(Boolean).join(" ") || "بدون نام";
  function clear() {
    generation++; records = null; result = null; page = 0; fileInput.value = "";
    runFile.disabled = true; exportButton.disabled = true; view.disabled = true; view.value = "all";
    $("file-error").hidden = true; $("file-error").textContent = ""; fileInput.removeAttribute("aria-invalid");
    $("source-rows").replaceChildren(); $("result-rows").replaceChildren();
    for (const id of Object.keys(metricKeys)) $("metric-" + id).textContent = "—";
    $("empty").hidden = false; $("empty").textContent = "فایل مجاز خود را انتخاب کنید یا نمونه ساختگی را امتحان کنید.";
    $("row-count").textContent = "هنوز داده‌ای پردازش نشده است.";
    $("previous").disabled = true; $("next").disabled = true;
    $("workspace").setAttribute("aria-busy", "false");
  }
  function render() {
    if (!result || !records) return;
    const selectedByIndex = new Map(result.selected.map(row => [row.sourceIndex, row]));
    const shown = result.outcomes.filter(row => view.value === "all" || (view.value === "accepted" ? selectedByIndex.has(row.sourceIndex) : view.value === "rejected" ? !selectedByIndex.has(row.sourceIndex) : row.review));
    page = Math.max(0, Math.min(page, Math.ceil(shown.length / PAGE_SIZE) - 1));
    const visible = shown.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE);
    $("source-rows").replaceChildren(); $("result-rows").replaceChildren();
    for (const outcome of visible) {
      const record = records[outcome.sourceIndex], selected = selectedByIndex.get(outcome.sourceIndex);
      const source = document.createElement("tr"), after = document.createElement("tr");
      cell(source, count.format(outcome.sourceIndex + 1)); cell(source, name(record)); cell(source, record.phones.filter(Boolean).join(" · ") || "—", "phone-values", "ltr");
      cell(after, count.format(outcome.sourceIndex + 1)); cell(after, name(record)); cell(after, selected?.phone || "—", "phone-values", "ltr"); cell(after, selected?.operator || "—", "operator", "ltr");
      cell(after, selected ? "پذیرفته" : "رد شده", selected ? "accepted" : "rejected");
      cell(after, outcome.reasons.map(reason => reasons[reason]).join("؛ ") || "بدون هشدار");
      $("source-rows").append(source); $("result-rows").append(after);
    }
    $("empty").hidden = shown.length > 0; $("empty").textContent = "در این فیلتر ردیفی وجود ندارد. فیلتر دیگری انتخاب کنید.";
    $("row-count").textContent = `${count.format(shown.length)} ردیف در این فیلتر · صفحه ${count.format(page + 1)} از ${count.format(Math.max(1, Math.ceil(shown.length / PAGE_SIZE)))}`;
    $("previous").disabled = page === 0; $("next").disabled = (page + 1) * PAGE_SIZE >= shown.length;
  }
  function process(label) {
    result = processContacts(records); page = 0; view.value = "all"; view.disabled = false;
    for (const [id, key] of Object.entries(metricKeys)) $("metric-" + id).textContent = count.format(result.stats[key]);
    exportButton.disabled = false; render(); status(label);
  }
  fileInput.addEventListener("change", async () => {
    const file = fileInput.files?.[0]; clear();
    if (!file) { status("فایلی انتخاب نشده است."); return; }
    const ticket = generation;
    status("در حال خواندن فایل در همین تب…"); $("workspace").setAttribute("aria-busy", "true");
    try {
      if (file.size > MAX_CSV_CHARS) throw new Error("Choose a CSV file no larger than 1 MiB.");
      let buffer;
      try { buffer = await file.arrayBuffer(); } catch { throw new Error("Unable to read this file. Choose the CSV again or use another local copy."); }
      if (ticket !== generation) return;
      let text;
      try { text = new TextDecoder("utf-8", { fatal: true }).decode(buffer); }
      catch { throw new Error("Save the CSV using UTF-8 encoding and try again."); }
      records = parseCsvContacts(text); runFile.disabled = false;
      $("empty").textContent = "فایل معتبر است. برای نمایش نتیجه، پردازش محلی را شروع کنید.";
      status(`${count.format(records.length)} ردیف آماده پردازش محلی است. هیچ فایلی آپلود نشده است.`);
    } catch (error) {
      if (ticket !== generation) return;
      records = null; fileInput.setAttribute("aria-invalid", "true");
      $("file-error").textContent = error instanceof Error && !(error instanceof TypeError) ? error.message : "Unable to read this file. Choose a UTF-8 CSV and try again.";
      $("file-error").hidden = false; status("فایل پذیرفته نشد. راهنمای خطا را بررسی کنید.");
    } finally { if (ticket === generation) $("workspace").setAttribute("aria-busy", "false"); }
  });
  $("run").addEventListener("click", () => { clear(); records = sample; process("نمونه ساختگی پردازش شد. این ردیف‌ها متعلق به افراد واقعی نیستند."); });
  runFile.addEventListener("click", () => { if (records) process("پردازش محلی کامل شد. خروجی و هشدارها را پیش از دانلود بررسی کنید."); });
  view.addEventListener("change", () => { page = 0; render(); });
  $("previous").addEventListener("click", () => { page--; render(); });
  $("next").addEventListener("click", () => { page++; render(); });
  exportButton.addEventListener("click", () => {
    if (!result) return;
    const url = URL.createObjectURL(new Blob([buildOutputCsv(result.selected)], { type: "text/csv;charset=utf-8" }));
    const link = document.createElement("a"); link.href = url; link.download = "normalized-contacts.csv"; document.body.append(link); link.click(); link.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
    status("دانلود آماده شد. خروجی یک نسخه محلی از داده است؛ آن را در محل امن نگه دارید.");
  });
  $("reset").addEventListener("click", () => { clear(); status("فضای کار پاک شد. برای شروع فایل جدیدی انتخاب کنید."); $("reset").focus(); });
  clear();
}
