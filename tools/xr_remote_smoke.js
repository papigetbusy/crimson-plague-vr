// Loads a PUBLISHED link (raw.githack) in headless Chrome with the fake Quest, clicks through githack's 'One more step' notice, enters VR (sandbox + full game), reports build + errors.
// Usage: SHOTS=dir NODE_PATH=... node tools/xr_remote_smoke.js <url without query>
const puppeteer=require('puppeteer-core'),fs=require('fs');
const FAKE=fs.readFileSync(__dirname+'/xr_fake_quest.js','utf8');
(async()=>{const b=await puppeteer.launch({executablePath:'/usr/bin/google-chrome',headless:'new',args:['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist']});
for (const q of ['?sandbox','']){const p=await b.newPage();const logs=[];p.on('pageerror',e=>logs.push(e.message));p.on('response',r=>{if(r.status()>=400)logs.push('HTTP '+r.status()+' '+r.url().slice(0,120))});p.on('console',m=>{if(m.type()==='error')logs.push(m.text())});
await p.evaluateOnNewDocument(FAKE);
await p.goto(process.argv[2]+q,{waitUntil:'load',timeout:120000});
if(await p.evaluate(()=>/External Content Notice/.test(document.title))){console.log('githack notice shown: clicking Open the page');await Promise.all([p.waitForNavigation({waitUntil:'load',timeout:120000}),p.click('form button')]);}
await p.waitForFunction(()=>window.__game&&!document.getElementById('vrBtn').hidden,{timeout:120000});
await p.click('#vrBtn');await p.waitForFunction(()=>window.__game.xr.presenting(),{timeout:30000});await new Promise(r=>setTimeout(r,4000));
const st=await p.evaluate(()=>({build:(document.querySelector('.buildTag')||{}).textContent,presenting:window.__game.xr.presenting(),frames:window.__fx.frames}));
await p.screenshot({path:(process.env.SHOTS||'/tmp')+'/remote_'+(q?'sandbox':'full')+'.png'});
console.log(q||'(full)',JSON.stringify(st),'errors:',logs.length,logs.slice(0,3).join(' | '));await p.close();}
await b.close();})();
