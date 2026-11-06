import {chromium} from 'playwright';
import AxeBuilder from '@axe-core/playwright';
import {mkdir,writeFile,readFile} from 'node:fs/promises';
import assert from 'node:assert/strict';
const out=process.env.QA_OUTPUT||'qa-artifacts';await mkdir(out,{recursive:true});
const url=process.env.PRODUCT_URL||'http://127.0.0.1:8765/';
const browser=await chromium.launch();const results=[];
const header='First Name,Last Name,Phone 1 - Value,Phone 2 - Value\r\n';
const csv=header+'"نمونه, ساختگی",Example,۰۹۱۲۰۰۰۰۰۰۱,+989120000001\r\nSynthetic,Rejected,bad,02100000000\r\nShared,Number,09120000001,\r\n';
try{for(const width of [320,375,390,768,1024,1440,1920]){
 const context=await browser.newContext({viewport:{width,height:900},reducedMotion:'reduce',acceptDownloads:true});const page=await context.newPage();
 const errors=[],requests=[],bad=[];page.on('pageerror',e=>errors.push(e.message));page.on('console',m=>{if(m.type()==='error')errors.push(m.text());});page.on('request',r=>requests.push(r.url()));page.on('response',r=>{if(r.status()>=400)bad.push([r.status(),r.url()]);});
 await page.goto(url,{waitUntil:'networkidle'});
 assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),'page overflow '+width);
 assert(await page.locator('img').evaluateAll(xs=>xs.every(x=>x.complete&&x.naturalWidth)),'assets');
 assert.equal(await page.locator('h1').count(),1);assert(await page.locator('h1').evaluate(e=>parseFloat(getComputedStyle(e).fontSize)<=60));
 assert.equal(await page.locator('#workspace').getAttribute('dir'),'rtl');
 for(const a of await page.locator('a[href^="#"]').all()){const href=await a.getAttribute('href');assert(await page.locator(href).count(),'anchor '+href);}
 await page.keyboard.press('Tab');assert(await page.evaluate(()=>{const e=document.activeElement;return e!==document.body&&getComputedStyle(e).outlineStyle!=='none';}),'focus visibility');
 await page.locator('.cta-row a[href="#workspace"]').click();assert.equal(new URL(page.url()).hash,'#workspace');
 await page.locator('#run').click();assert.equal(await page.locator('#result-rows tr').count(),5);
 await page.locator('#view').selectOption('accepted');assert.equal(await page.locator('#result-rows tr').count(),4);
 await page.locator('#view').selectOption('review');assert.equal(await page.locator('#result-rows tr').count(),4);
 await page.locator('#reset').click();assert.equal(await page.locator('#result-rows tr').count(),0);assert(await page.locator('#export').isDisabled());
 await page.locator('#contact-file').setInputFiles({name:'fictional.csv',mimeType:'text/csv',buffer:Buffer.from('\uFEFF'+csv)});
 await page.locator('#run-file').waitFor({state:'visible'});await page.waitForFunction(()=>!document.querySelector('#run-file').disabled);
 await page.locator('#run-file').click();assert.equal(await page.locator('#result-rows tr').count(),3);assert.match(await page.locator('#contact-file').inputValue(),/fictional\.csv$/,'selected file remains visible');
 assert.equal(await page.locator('#metric-output').textContent(),'۲');assert.equal(await page.locator('#metric-rejected').textContent(),'۱');
 const downloadPromise=page.waitForEvent('download');await page.locator('#export').click();const download=await downloadPromise;
 const bytes=await readFile(await download.path());assert.deepEqual([...bytes.subarray(0,3)],[239,187,191]);const output=bytes.toString('utf8');assert.match(output,/selected_phone,mobile_operator/);assert.match(output,/"نمونه, ساختگی",Example,09120000001,MCI/);assert.doesNotMatch(output,/Synthetic,Rejected/);
 await page.locator('#view').selectOption('rejected');assert.equal(await page.locator('#result-rows tr').count(),1);
 await page.locator('#view').selectOption('all');await page.locator('.source-details summary').click();
 await page.screenshot({path:out+'/product-'+width+'.png',fullPage:true});
 const table=page.locator('.scroll').first();if(await table.evaluate(e=>e.scrollWidth>e.clientWidth)){await table.focus();const before=await table.evaluate(e=>e.scrollLeft);await page.keyboard.down('ArrowLeft');await page.waitForTimeout(350);await page.keyboard.up('ArrowLeft');await page.waitForTimeout(150);assert(await table.evaluate((e,b)=>e.scrollLeft!==b,before),'RTL keyboard table scroll');}
 const a11y=await new AxeBuilder({page}).withTags(['wcag2a','wcag2aa','wcag21aa']).analyze();await writeFile(out+'/product-'+width+'-accessibility.json',JSON.stringify(a11y,null,2));assert.deepEqual(a11y.violations.map(v=>({id:v.id,nodes:v.nodes.map(n=>n.target)})),[],'axe violations');
 // Errors never include file content. Test encoding, malformed CSV, limits, and recovery.
 for(const buffer of [Buffer.from(header+'A,B'),Buffer.from(header+'"broken'),Buffer.from([255,254,0,0]),Buffer.alloc(1048577,65)]){
  await page.locator('#contact-file').setInputFiles({name:'fictional-invalid.csv',mimeType:'text/csv',buffer});await page.locator('#file-error').waitFor({state:'visible'});assert(await page.locator('#run-file').isDisabled());assert(await page.locator('#export').isDisabled());
 }
 await page.locator('#run').click();assert(await page.locator('#file-error').isHidden());assert.equal(await page.locator('#contact-file').inputValue(),'');
 // All-rejected input can still export the documented header-only schema.
 await page.locator('#contact-file').setInputFiles({name:'fictional-rejected.csv',mimeType:'text/csv',buffer:Buffer.from(header+'Synthetic,Rejected,bad,\r\n')});await page.waitForFunction(()=>!document.querySelector('#run-file').disabled);await page.locator('#run-file').click();
 const d2=page.waitForEvent('download');await page.locator('#export').click();assert.equal((await readFile(await(await d2).path())).toString('utf8'),'\uFEFFfirst_name,last_name,selected_phone,mobile_operator\r\n');
 // Race: reset after a read starts; stale promises cannot restore private data.
 await page.evaluate(()=>{const original=File.prototype.arrayBuffer;File.prototype.arrayBuffer=function(){return new Promise(resolve=>setTimeout(()=>original.call(this).then(resolve),150));};});
 await page.locator('#contact-file').setInputFiles({name:'fictional-race.csv',mimeType:'text/csv',buffer:Buffer.from(csv)});await page.locator('#reset').click();await page.waitForTimeout(250);assert(await page.locator('#run-file').isDisabled());assert.equal(await page.locator('#result-rows tr').count(),0);assert.equal(await page.locator('#contact-file').inputValue(),'');
 if(width===375||width===1440){
  await page.locator('#run').click();await page.locator('.scroll').evaluateAll(xs=>xs.forEach(x=>x.scrollLeft=0));await page.locator('#workspace').screenshot({path:out+'/workbench-'+width+'.png'});
  // 1,000-row input is paginated, not rendered as an unbounded DOM.
  await page.locator('#contact-file').setInputFiles({name:'fictional-boundary.csv',mimeType:'text/csv',buffer:Buffer.from(header+'Synthetic,Boundary,09120000001,\r\n'.repeat(1000))});await page.waitForFunction(()=>!document.querySelector('#run-file').disabled);await page.locator('#run-file').click();assert.equal(await page.locator('#result-rows tr').count(),25);await page.locator('#next').click();assert.match(await page.locator('#row-count').textContent(),/۲/);
 }
 assert.deepEqual(await page.evaluate(()=>({local:localStorage.length,session:sessionStorage.length,cookies:document.cookie})),{local:0,session:0,cookies:''});
 const external=requests.filter(u=>/^https?:/.test(u)&&new URL(u).origin!==new URL(url).origin);assert.deepEqual(external,[]);assert.deepEqual(errors,[]);assert.deepEqual(bad,[]);
 results.push({width,url,overflow:'passed',importExport:'passed',resetRace:'passed',accessibilityViolations:a11y.violations.length,unexpectedRequests:external,browserErrors:errors,hero:await page.locator('h1').evaluate(e=>getComputedStyle(e).fontSize)});await context.close();
}}finally{await writeFile(out+'/results.json',JSON.stringify(results,null,2));await browser.close();}
