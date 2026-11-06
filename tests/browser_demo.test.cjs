const test = require('node:test');
const assert = require('node:assert/strict');
const { normalizePhone, operatorFor, processContacts, parseCsvContacts, buildOutputCsv, sample } = require('../docs/app.js');

test('browser normalizer supports project formats and rejects unsafe ambiguity', () => {
  assert.equal(normalizePhone('۰۹۱۲ ۰۰۰ ۰۰۰۱'), '09120000001');
  assert.equal(normalizePhone('+98-930-000-0002'), '09300000002');
  assert.equal(normalizePhone('0098 912 000 0001'), '09120000001');
  assert.equal(normalizePhone('0912abc000001'), null);
  assert.equal(normalizePhone('02100000000'), null);
  assert.equal(normalizePhone('09120000001\t'), null);
});

test('operator groups follow the configured conservative prefixes', () => {
  assert.equal(operatorFor('09120000001'), 'MCI');
  assert.equal(operatorFor('09300000002'), 'Irancell');
  assert.equal(operatorFor('09200000003'), 'Rightel');
  assert.equal(operatorFor('09320000004'), 'Other/Unknown');
});

test('sample processing is deterministic and reports aggregate quality', () => {
  const { selected, stats } = processContacts(sample);
  assert.deepEqual(selected.map(x => [x.first, x.phone, x.operator]), [
    ['کاربر', '09120000001', 'MCI'], ['Synthetic', '09120000003', 'MCI'],
    ['', '09880000004', 'Other/Unknown'], ['Synthetic', '09120000001', 'MCI']
  ]);
  assert.deepEqual([stats.inputRows, stats.outputRows, stats.rejectedRows, stats.duplicateNumbersWithinRows, stats.repeatedSelectedNumbers], [5, 4, 1, 1, 1]);
});

test('browser CSV parser supports quoted local records and enforces schema limits', () => {
  const csv = '\uFEFFFirst Name,Last Name,Phone 1 - Value,Phone 2 - Value\r\n"Ari, Jr",Example,+989121234567,09121234567\r\nNima,Sample,not-a-number,09301234567\r\n';
  const records = parseCsvContacts(csv);
  const result = processContacts(records);
  assert.deepEqual(records[0], { first: 'Ari, Jr', last: 'Example', phones: ['+989121234567', '09121234567'] });
  assert.equal(result.selected[0].phone, '09121234567');
  assert.equal(result.stats.duplicateNumbersWithinRows, 1);
  assert.equal(result.stats.invalidPhoneValues, 1);
  assert.throws(() => parseCsvContacts('First Name,Last Name\nAli,Sample\n'), /Phone 1 - Value/);
  assert.throws(() => parseCsvContacts('First Name,Last Name,Phone 1 - Value\n"Ali,Sample,09121234567\n'), /unclosed quoted/);
});

test('normalized CSV export keeps formula-like names inert', () => {
  const csv = buildOutputCsv([{ first: '=1+1', last: 'Sample', phone: '09121234567', operator: 'MCI' }]);
  assert.match(csv, /'=1\+1/);
  assert.match(csv, /selected_phone,mobile_operator/);
});

test('browser demonstration accepts only local CSV files and makes no outbound requests', () => {
  const fs = require('node:fs');
  const path = require('node:path');
  const page = fs.readFileSync(path.join(__dirname, '../docs/index.html'), 'utf8');
  const app = fs.readFileSync(path.join(__dirname, '../docs/app.js'), 'utf8');
  assert.match(page, /type="file"[^>]+accept="\.csv,text\/csv"/);
  assert.doesNotMatch(page, /type=["'](?:text|tel|number)["']/i);
  assert.match(page, /connect-src 'none'/);
  assert.doesNotMatch(app, /fetch\s*\(|XMLHttpRequest|WebSocket|sendBeacon|localStorage/);
});

test('strict phone boundaries reject trailing line controls and count Unicode characters', () => {
  for (const suffix of ['\n','\r','\t','\u0000','\u2028','\u200f','\u00a0']) assert.equal(normalizePhone('09120000001'+suffix), null);
  assert.equal(normalizePhone(' ۰۹۱۲ (۰۰۰) ۰۰۰۱ '), '09120000001');
  assert.equal(normalizePhone('٩١٢٠٠٠٠٠٠١'), '09120000001');
});

test('CSV parser rejects inconsistent widths, duplicate columns and UTF-8 byte overflow', () => {
  const head = 'First Name,Last Name,Phone 1 - Value\n';
  for (const row of ['A,B','A,B,09120000001,','A,B,09120000001,X']) assert.throws(()=>parseCsvContacts(head+row), /column count/);
  assert.equal(parseCsvContacts(head+',,\n').length, 1);
  assert.equal(parseCsvContacts(head+'"",,\n').length, 1);
  assert.throws(()=>parseCsvContacts('First Name,First Name,Last Name,Phone 1 - Value\nA,B,C,D'), /Duplicate/);
  assert.throws(()=>parseCsvContacts(head+'ک'.repeat(524288)+',B,09120000001'), /1 MiB/);
  assert.throws(()=>parseCsvContacts(head+'A,B,09120000001\n'.repeat(1001)), /1,000/);
  assert.equal(parseCsvContacts(head+'A,B,09120000001\n'.repeat(1000)).length, 1000);
});

test('quoted multiline names survive; phone controls are rejected with valid fallback', () => {
  const records = parseCsvContacts('First Name,Last Name,Phone 1 - Value,Phone 2 - Value\r\n"A\nB","C""D","09120000001\n",09300000002\r\n');
  const result = processContacts(records);
  assert.equal(result.selected[0].first, 'A\nB');
  assert.equal(result.selected[0].last, 'C"D');
  assert.equal(result.selected[0].phone, '09300000002');
  assert.equal(result.stats.invalidPhoneValues, 1);
});

test('review filters include accepted warnings and rejected rows, without cross-row merging', () => {
  const result=processContacts(sample);
  assert.equal(result.stats.reviewRows, 4);
  assert.ok(result.outcomes[1].reasons.includes('multiple'));
  assert.ok(result.outcomes[2].reasons.includes('unknown'));
  assert.ok(result.outcomes[3].reasons.includes('no-mobile'));
  assert.ok(result.outcomes[4].reasons.includes('shared'));
  assert.equal(result.selected.length,4);
});

test('exports are BOM CSV, quote names and protect leading-whitespace formulas', () => {
  for (const value of ['=1+1','+1','-1','@SUM(A1)','  =1','\u0001=1','\t=1','\rtest','\ntest']) {
    const output=buildOutputCsv([{first:value,last:'A,"B"',phone:'09120000001',operator:'MCI'}]);
    assert.ok(output.startsWith('\uFEFFfirst_name,'));
    assert.ok(output.includes("'"+value.replace(/"/g,'""')));
    assert.ok(output.includes('"A,""B"""'));
  }
  assert.equal(buildOutputCsv([]), '\uFEFFfirst_name,last_name,selected_phone,mobile_operator\r\n');
});
