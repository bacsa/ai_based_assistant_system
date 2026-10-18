const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1360, height: 900 } });
  const errs = []; p.on('pageerror', e => errs.push('pageerror: ' + e.message)); p.on('console', m => { if (m.type() === 'error') errs.push('console: ' + m.text()); });
  const html = '<!doctype html><html><head><meta charset="utf-8"></head><body>' + require('fs').readFileSync(require('path').join(__dirname, '..', 'index.html'), 'utf8') + '</body></html>';
  await p.setContent(html, { waitUntil: 'load' });
  const nav = async v => { await p.click(`[data-action=nav][data-view=${v}]`); await p.waitForTimeout(60); if (v === 'flows') { await p.click('[data-action=flow-tab][data-tab=monitor]'); await p.waitForTimeout(60); } };
  const log = (k, v) => console.log(k.padEnd(26), String(v).slice(0, 170).replace(/\n/g, ' | '));
  await nav('flows'); log('monitor cards', await p.locator('.fcard').count());
  await p.click('[data-action=flow-tab][data-tab=canvas]'); log('canvas nodes', await p.locator('#canvas .node').count()); log('canvas edges', await p.locator('#canvas .edge').count());
  await p.locator('#canvas [data-node=triage]').dispatchEvent('pointerdown', { clientX: 10, clientY: 10 }); await p.locator('body').dispatchEvent('pointerup'); await p.waitForTimeout(60);
  log('inspector', await p.locator('.panel h3').first().innerText());
  await p.selectOption('#add-type', 'notify'); await p.click('[data-action=add-node]'); await p.waitForTimeout(60); log('nodes after add', await p.locator('#canvas .node').count());
  await p.click('[data-action=flow-test]'); await p.waitForTimeout(100); log('test run', await p.locator('#toast').innerText());
  log('run steps', await p.locator('table.tbl tbody tr').last().locator('xpath=ancestor::table').locator('tbody tr').count());
  // drive the push path through events and watch the flow
  await nav('events'); await p.click('[data-action=ev-tab][data-tab=publish]'); await p.click('form[data-form=publish] button[type=submit]'); await p.waitForTimeout(120);
  log('chain', (await p.locator('.trace .call').allInnerTexts()).map(x => x.split(' ')[0]).join(' > '));
  await nav('flows'); log('parked runs', await p.locator('.panel:has-text("Parked runs") tbody tr').count());
  log('waiting text', await p.locator('.panel:has-text("Parked runs") tbody tr').first().innerText().catch(() => 'none'));
  await nav('approvals'); log('pending', await p.locator('.appr .pill.warn').count()); await p.click('[data-action=approve]'); await p.waitForTimeout(80);
  await nav('flows'); log('after approve first run', await p.locator('.panel:has-text("Latest runs") tbody tr').first().innerText());
  // invoice ladder: publish invoice -> timer -> fire
  await nav('events'); await p.click('[data-action=ev-tab][data-tab=publish]'); await p.selectOption('#pub-type', 'erp.invoice.posted'); await p.waitForTimeout(50); await p.click('form[data-form=publish] button[type=submit]'); await p.waitForTimeout(100);
  await nav('flows'); const row = p.locator('.panel:has-text("Parked runs") tbody tr:has-text("Invoice")').first(); log('invoice parked', await row.innerText().catch(() => 'none'));
  await row.locator('[data-action=fire-timer]').click(); await p.waitForTimeout(100); log('after timer', await p.locator('.panel:has-text("Parked runs") tbody tr:has-text("Invoice")').first().innerText().catch(() => 'none'));
  // uptime incident flow: 3 failures
  for (let i = 0; i < 3; i++) { await nav('events'); await p.click('[data-action=ev-tab][data-tab=publish]'); await p.selectOption('#pub-type', 'uptime.check.failed'); await p.waitForTimeout(40); await p.fill('#pub-idem', 'up' + i + Date.now()); await p.click('form[data-form=publish] button[type=submit]'); await p.waitForTimeout(80); }
  await nav('flows'); log('incident parked', await p.locator('.panel:has-text("Parked runs") tbody tr:has-text("incident")').first().innerText().catch(() => 'none'));
  await nav('events'); await p.click('[data-action=ev-tab][data-tab=publish]'); await p.selectOption('#pub-type', 'uptime.check.recovered'); await p.waitForTimeout(40); await p.click('form[data-form=publish] button[type=submit]'); await p.waitForTimeout(80);
  log('recovered chain', (await p.locator('.trace .res').allInnerTexts()).filter(x => x.includes('flow-runner')).join(' / '));
  await nav('flows'); await p.click('[data-action=flow-tab][data-tab=runs]'); await p.click('[data-action=open-flow][data-id=website-incident]'); await p.click('[data-action=flow-tab][data-tab=runs]'); await p.waitForTimeout(60); log('incident runs', await p.locator('tbody tr').count()); await p.locator('tbody tr').first().click(); await p.waitForTimeout(60); log('run detail steps', await p.locator('.panel:has-text("Run run-") tbody tr').count());
  await p.click('[data-action=flow-tab][data-tab=canvas]'); await p.click('[data-action=flow-export]'); await p.waitForTimeout(60); log('export', (await p.locator('pre.yaml').first().innerText()).slice(0, 60));
  await p.click('[data-action=new-flow]'); await p.waitForTimeout(60); log('new flow nodes', await p.locator('#canvas .node').count());
  await p.click('[data-action=toggle-live]'); await p.waitForTimeout(9000); await p.click('[data-action=toggle-live]'); await p.click('[data-action=flow-tab][data-tab=monitor]'); await p.waitForTimeout(60);
  log('runs after live', await p.locator('.panel:has-text("Latest runs") tbody tr').count());
  await p.setViewportSize({ width: 400, height: 800 }); await p.waitForTimeout(100); log('h-overflow@400', await p.evaluate(() => document.documentElement.scrollWidth > document.documentElement.clientWidth));
  await p.setViewportSize({ width: 1360, height: 900 }); await p.click('[data-action=open-flow][data-id=key-page-regression-response]'); await p.waitForTimeout(80);
  await p.screenshot({ path: 'tests/out/flows.png', fullPage: false });
  await p.click('[data-action=flow-tab][data-tab=monitor]'); await p.waitForTimeout(60); await p.screenshot({ path: 'tests/out/monitor.png', fullPage: false });
  console.log('ERRORS', errs.length ? errs : 'none');
  await b.close();
})().catch(e => { console.log('FATAL', e.message); process.exit(1); });
