import fs from "node:fs";
import http from "node:http";
import os from "node:os";
import path from "node:path";
import {spawn} from "node:child_process";
import {setTimeout as sleep} from "node:timers/promises";
const root=process.cwd();
const chrome=["/usr/bin/google-chrome","/usr/bin/google-chrome-stable","/usr/bin/chromium"].find(fs.existsSync);
if(!chrome)throw Error("Chrome is required for browser QA.");
const types={".html":"text/html;charset=utf-8",".js":"text/javascript;charset=utf-8",".css":"text/css;charset=utf-8",".json":"application/json;charset=utf-8"};
const server=http.createServer((req,res)=>{
 try{
  const urlPath=decodeURIComponent(new URL(req.url,"http://localhost").pathname);
  const file=path.resolve(root,"."+urlPath+(urlPath.endsWith("/")?"index.html":""));
  if(!file.startsWith(root+path.sep)){res.writeHead(400);res.end();return;}
  res.writeHead(200,{"Content-Type":types[path.extname(file)]||"application/octet-stream"});res.end(fs.readFileSync(file));
 }catch{res.writeHead(404);res.end("Not found");}
});
await new Promise(resolve=>server.listen(0,"127.0.0.1",resolve));
const url="http://127.0.0.1:"+server.address().port;
const profile=fs.mkdtempSync(path.join(os.tmpdir(),"tdn-country-"));
const chromeProcess=spawn(chrome,["--headless=new","--no-sandbox","--disable-gpu","--disable-dev-shm-usage","--remote-allow-origins=*","--remote-debugging-port=0","--user-data-dir="+profile,"about:blank"],{stdio:"ignore"});
let ws,number=0,error=null;const pending=new Map();
function cmd(method,params={}){
 const id=++number;
 return new Promise((resolve,reject)=>{
  pending.set(id,{resolve,reject});ws.send(JSON.stringify({id,method,params}));
  setTimeout(()=>{if(pending.has(id)){pending.delete(id);reject(Error("Chrome timed out: "+method));}},12000);
 });
}
async function js(expression){
 const r=await cmd("Runtime.evaluate",{expression,returnByValue:true,awaitPromise:true});
 if(r.exceptionDetails)throw Error("Browser JS: "+r.exceptionDetails.text);
 return r.result?.value;
}
async function eventually(fn,max=14000){
 const start=Date.now();
 while(Date.now()-start<max){const v=await fn();if(v)return v;await sleep(100);}
 throw Error("Page did not reach expected browser state.");
}
async function page(route){
 await cmd("Page.navigate",{url:url+route});
 await eventually(()=>js('document.readyState==="complete"&&!!document.querySelector("#country-edition-select")'));
}
try{
 await eventually(()=>fs.existsSync(path.join(profile,"DevToolsActivePort")));
 const debuggerPort=fs.readFileSync(path.join(profile,"DevToolsActivePort"),"utf8").split("\n")[0];
 const tabs=await (await fetch("http://127.0.0.1:"+debuggerPort+"/json/list")).json();
 const tab=tabs.find(x=>x.type==="page");if(!tab)throw Error("No browser page target.");
 ws=new WebSocket(tab.webSocketDebuggerUrl);
 await new Promise((resolve,reject)=>{ws.onopen=resolve;ws.onerror=reject;});
 ws.onmessage=event=>{const m=JSON.parse(event.data);if(m.id&&pending.has(m.id)){const p=pending.get(m.id);pending.delete(m.id);m.error?p.reject(Error(m.error.message)):p.resolve(m.result);}};
 await cmd("Page.enable");await cmd("Runtime.enable");
 await page("/");
 await eventually(()=>js('document.querySelector("#status-label")?.textContent==="AUTOMATED NEWS LIVE"'));
 if((await js('document.querySelectorAll("#country-edition-select option").length'))!==11)throw Error("Expected Worldwide plus ten countries.");
 await js('(()=>{const s=document.querySelector("#country-edition-select");s.value="BD";s.dispatchEvent(new Event("change",{bubbles:true}));})()');
 const bd=await js('(async()=>{const f=await(await fetch("/data/news.json")).json();const titles=new Set(f.articles.filter(a=>(a.countries||[]).includes("BD")).map(a=>a.title));const shown=[...document.querySelectorAll("#news-grid .story-title a")].map(a=>a.textContent.trim());return {found:shown.length,valid:shown.every(a=>titles.has(a)),lead:titles.has(document.querySelector("#lead-title")?.textContent)};})()');
 if(!bd.found||!bd.valid||!bd.lead)throw Error("Bangladesh homepage leaked unrelated headlines: "+JSON.stringify(bd));
 console.log("PASS: Bangladesh shows "+bd.found+" country-matched technology headlines.");
 await page("/category/ai/");
 if(await js('document.querySelector("#country-edition-select").value')!=="BD")throw Error("Country preference was lost.");
 if(!(await js('[...document.querySelectorAll("[data-edition-story]")].filter(x=>!x.hidden).every(x=>x.dataset.editionStory.split(",").includes("BD"))')))throw Error("Category includes another country's news.");
 console.log("PASS: Country choice is preserved on category pages.");
 await page("/");
 await js('(()=>{const s=document.querySelector("#country-edition-select");s.value="JP";s.dispatchEvent(new Event("change",{bubbles:true}));})()');
 const japan=await js('(async()=>{const f=await(await fetch("/data/news.json")).json();const titles=new Set(f.articles.filter(a=>(a.countries||[]).includes("JP")).map(a=>a.title));return [...document.querySelectorAll("#news-grid .story-title a")].every(a=>titles.has(a.textContent.trim()));})()');
 if(!japan)throw Error("Japan selection leaked other-country stories.");
 console.log("PASS: Country changes do not display unrelated headlines.");
}catch(e){error=e;console.error("TechDaily country browser QA failed:",e.message);}
finally{try{ws?.close();}catch{}chromeProcess.kill("SIGTERM");await new Promise(resolve=>server.close(resolve));try{fs.rmSync(profile,{recursive:true,force:true});}catch{}}
if(error)process.exitCode=1;
