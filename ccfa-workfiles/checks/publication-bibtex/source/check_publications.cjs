const fs = require('fs');
const path = require('path');
const {pathToFileURL} = require('url');
const assert = require('assert');

async function main() {
  const root = path.resolve(__dirname, '../../../..');
  const packages = process.argv[2];
  const chrome = process.argv[3];
  const {marked} = await import(pathToFileURL(require.resolve('marked', {paths:[packages]})).href);
  const {chromium} = require(require.resolve('playwright', {paths:[packages]}));
  const output = path.join(root, 'ccfa-workfiles/checks/publication-bibtex/build');
  fs.mkdirSync(output, {recursive:true});
  const citations = JSON.parse(fs.readFileSync(path.join(root,'docs/_data/publications.json'),'utf8'));
  assert.strictEqual(Object.keys(citations).length,42);
  const usedKeys=[];
  const css = fs.readFileSync(path.join(root,'docs/_sass/jekyll-theme-minimal.scss'),'utf8').replace(/^@import[^\n]*\n/gm,'').replace(/\/\/[^\n]*/g,'');
  const javascript = fs.readFileSync(path.join(root,'docs/assets/js/bibtex.js'),'utf8');
  const pages={};
  for (const kind of ['journal','conference']) {
    const source=fs.readFileSync(path.join(root,'docs/'+kind+'.md'),'utf8');
    const markdown=source.replace(/\{% include bibtex-button\.html key="([^"]+)" %\}/g,(_,key)=>{
      assert(citations[key], 'Missing citation '+key);usedKeys.push(key);
      return '<button type="button" class="bibtex-toggle" data-bibtex-key="'+key+'" aria-expanded="false" aria-label="Show BibTeX citation" hidden>BibTeX</button>';
    });
    const content=marked.parse(markdown);
    let layout=fs.readFileSync(path.join(root,'docs/_layouts/default.html'),'utf8');
    layout=layout.replace(/\{% seo %\}/g,'<title>'+kind+' | Haojie Zhang</title>')
      .replace(/<link rel="stylesheet"[^>]+>/,'<style>'+css+'</style>')
      .replace(/<script src="https:[^>]+><\/script>/g,'')
      .replace(/\{\{ content \}\}/g,content)
      .replace(/\{% include external_links.html %\}/g,fs.readFileSync(path.join(root,'docs/_includes/external_links.html'),'utf8'))
      .replace(/\{\{ site.data.publications \| jsonify \}\}/g,JSON.stringify(citations).replace(/</g,'\\u003c'))
      .replace(/<script src="\{\{[^\n]+bibtex\.js[^\n]+><\/script>/,'<script>'+javascript+'</script>')
      .replace(/<script src="\{\{[^\n]+scale.fix[^\n]+><\/script>/,'')
      .replace(/\{% if page.name[^\n]+%\}/,'').replace(/\{% endif %\}/,'')
      .replace(/\{\{ site.lang \| default: 'en-US' \}\}/g,'en-US')
      .replace(/\{\{ site.github.build_revision \}\}/g,'preview');
    assert(!/\{%|\{\{\s*(site\.|page\.|content\b|'\/assets\/)/.test(layout), 'Unrendered template');
    const filename=path.join(output,kind+'.html');fs.writeFileSync(filename,layout,'utf8');pages[kind]=filename;
  }
  assert.strictEqual(new Set(usedKeys).size,42);
  for (const [key,entry] of Object.entries(citations)) {
    assert(entry.bibtex.startsWith('@')&&entry.bibtex.includes('{'+key+','));
    assert.strictEqual(entry.bibtex.split('{').length,entry.bibtex.split('}').length,'Unbalanced citation '+key);
    assert(!/[†‡#*]/.test(entry.metadata.author),'Role markers in authors '+key);
    if (entry.id.startsWith('c')) assert(entry.metadata.location,'Missing location '+key);
  }
  assert.strictEqual(citations.wang2025can.metadata.year,'2026');
  assert.strictEqual(citations.yang2025lightweight.metadata.pages,'1252--1256');
  assert.strictEqual(citations.wu2024inspiration.metadata.pages,'1--4');
  assert.strictEqual(citations.meng2026similarity.metadata.pages,'2790--2798');
  assert(!citations.yang2026object.metadata.pages&&!citations.gurlev2025heart.metadata.pages&&!citations.shen2024self.metadata.pages);
  assert(citations.cao2025somatisation.metadata.author.includes('Nakamura, Toru'));
  const browser=await chromium.launch({executablePath:chrome,headless:true});
  try {
    const context=await browser.newContext({permissions:['clipboard-read','clipboard-write']});
    const page=await context.newPage();const errors=[];page.on('pageerror',e=>errors.push(e.message));
    for (const kind of ['journal','conference']) {
      for (const width of [1440,736,390,320]) {
        await page.setViewportSize({width,height:1000});
        await page.goto(pathToFileURL(pages[kind]).href);
        const buttons=page.locator('.bibtex-toggle');
        assert.strictEqual(await buttons.count(),kind==='journal'?19:23);
        assert.strictEqual(await page.locator('.bibtex-toggle[hidden]').count(),0);
        assert.strictEqual(await page.locator('.bibtex-panel:not([hidden])').count(),0);
        const placement=await buttons.evaluateAll(items=>items.map(button=>({inList:!!button.closest('li'),inParagraph:button.parentElement.tagName==='P'})));
        assert(placement.every(item=>item.inList),'Button outside paper list');
        assert(placement.every(item=>item.inParagraph),'Button outside citation paragraph');
        await buttons.first().click();
        assert.strictEqual(await page.locator('.bibtex-panel:not([hidden])').count(),1);
        await buttons.nth(1).click();
        assert.strictEqual(await page.locator('.bibtex-panel:not([hidden])').count(),1);
        assert.strictEqual(await buttons.first().getAttribute('aria-expanded'),'false');
        const key=await buttons.nth(1).getAttribute('data-bibtex-key');
        const code=page.locator('#bibtex-'+key+' code');
        assert.strictEqual(await code.textContent(),citations[key].bibtex,'Highlighting changed raw citation');
        const overflow=await page.evaluate(()=>({body:document.documentElement.scrollWidth>window.innerWidth,panels:[...document.querySelectorAll('.bibtex-panel:not([hidden])')].some(p=>p.scrollWidth>p.clientWidth)}));
        assert(!overflow.body&&!overflow.panels,'Horizontal overflow '+kind+' '+width);
        if (width===1440 || width===390) await page.screenshot({path:path.join(output,kind+'-'+width+'.png'),fullPage:false});
        await buttons.nth(1).click();
        assert.strictEqual(await page.locator('.bibtex-panel:not([hidden])').count(),0);
        console.log(kind,width,'buttons, accordion and responsive layout passed');
      }
    }
    await page.setViewportSize({width:1440,height:1000});
    await page.goto(pathToFileURL(pages.journal).href);
    await page.locator('[data-bibtex-key="wang2025can"]').click();
    await page.locator('#bibtex-wang2025can .bibtex-copy').click();
    await page.waitForFunction(()=>document.querySelector('#bibtex-wang2025can .bibtex-status').textContent==='Copied!',null,{timeout:5000});
    assert.strictEqual(await page.locator('#bibtex-wang2025can .bibtex-status').textContent(),'Copied!');
    assert.strictEqual((await page.evaluate(()=>navigator.clipboard.readText())).replace(/\r\n/g,'\n'),citations.wang2025can.bibtex);
    await page.evaluate(()=>Object.defineProperty(navigator,'clipboard',{configurable:true,value:{writeText:async()=>{throw new Error('Blocked')}}}));
    await page.locator('#bibtex-wang2025can .bibtex-copy').click();
    assert.strictEqual(await page.evaluate(()=>window.getSelection().toString()),citations.wang2025can.bibtex);
    await page.locator('[data-bibtex-key="wang2025can"]').focus();await page.keyboard.press('Enter');
    assert.strictEqual(await page.locator('#bibtex-wang2025can').isVisible(),false);
    assert.deepStrictEqual(errors,[]);
    console.log('All 42 references, real clipboard copy, fallback selection and keyboard activation passed.');
  } finally {await browser.close();}
}
main().catch(error=>{console.error(error);process.exitCode=1});
