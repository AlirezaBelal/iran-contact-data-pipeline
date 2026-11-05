const test = require('node:test');
const assert = require('node:assert/strict');
const { normalizePhone, operatorFor, processContacts, sample } = require('../docs/app.js');

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

test('browser demonstration has no arbitrary contact input or outbound APIs', () => {
  const fs = require('node:fs');
  const page = fs.readFileSync('docs/index.html', 'utf8');
  const app = fs.readFileSync('docs/app.js', 'utf8');
  assert.doesNotMatch(page, /type=["']file|<form\b|<input\b/i);
  assert.match(page, /connect-src 'none'/);
  assert.doesNotMatch(app, /fetch\s*\(|XMLHttpRequest|WebSocket|sendBeacon|localStorage/);
});

