(() => {
"use strict";
const countries=[["BD","Bangladesh"],["IN","India"],["US","United States"],["GB","United Kingdom"],["CA","Canada"],["AU","Australia"],["DE","Germany"],["AE","United Arab Emirates"],["SG","Singapore"],["JP","Japan"]];
const KEY="tdn-country-edition-v1",query=new URLSearchParams(location.search).get("country");
const valid=c=>c==="WORLD"||countries.some(([code])=>code===c);
let stored;try{stored=localStorage.getItem(KEY);}catch{}
let selected=valid(query)?query:valid(stored)?stored:"WORLD";
const label=c=>countries.find(x=>x[0]===c)?.[1]||"Worldwide";
function filterStatic(){
 const stories=[...document.querySelectorAll("[data-edition-story]")];
 if(!stories.length)return;
 let count=0;
 for(const card of stories){const codes=(card.dataset.editionStory||"WORLD").split(",");const visible=selected==="WORLD"||codes.includes(selected);card.hidden=!visible;if(visible)count++;}
 let empty=document.querySelector("[data-edition-empty]");
 if(!empty){empty=document.createElement("p");empty.dataset.editionEmpty="";empty.className="country-empty";document.querySelector(".seo-headlines")?.after(empty);}
 empty.hidden=count>0;empty.textContent=selected==="WORLD"?"No recent verified headlines available.":"No verified "+label(selected)+" headlines in this category. Select Worldwide to see global reporting.";
}
function refresh(){
 const labelNode=document.querySelector("[data-edition-name]");
 if(labelNode)labelNode.textContent=label(selected);
 const context=document.querySelector("[data-edition-context]");
 if(context){context.hidden=selected==="WORLD";context.textContent=selected==="WORLD"?"":"Showing verified "+label(selected)+" technology news. Headlines are tagged by geographic relevance; general international news is not relabeled as local.";}
 filterStatic();
 document.dispatchEvent(new CustomEvent("countryeditionchange",{detail:{country:selected}}));
}
function choose(value){
 selected=valid(value)?value:"WORLD";
 document.documentElement.dataset.countryEdition=selected;
 try{localStorage.setItem(KEY,selected);}catch{}
 const u=new URL(location.href);if(selected==="WORLD")u.searchParams.delete("country");else u.searchParams.set("country",selected);
 try{history.replaceState(history.state,"",u.pathname+u.search+u.hash);}catch{}
 refresh();
}
function init(){
 const header=document.querySelector(".header");if(!header)return;
 const top=document.createElement("div");top.className="country-edition";
 const wrap=document.createElement("div");wrap.className="wrap country-edition-inner";
 const heading=document.createElement("span");heading.textContent="COUNTRY EDITION";heading.className="country-edition-caption";
 const lab=document.createElement("label");lab.htmlFor="country-edition-select";lab.textContent="Select country";
 const select=document.createElement("select");select.id="country-edition-select";select.setAttribute("aria-label","Choose country edition");
 for(const [code,name] of [["WORLD","🌐 Worldwide"],...countries]){const option=document.createElement("option");option.value=code;option.textContent=name;select.appendChild(option);}
 select.value=selected;select.addEventListener("change",()=>choose(select.value));
 const name=document.createElement("small");name.dataset.editionName="";name.textContent=label(selected);
 wrap.append(heading,lab,select,name);top.appendChild(wrap);header.before(top);
 const context=document.createElement("div");context.className="country-context";context.dataset.editionContext="";context.hidden=true;header.after(context);
 choose(selected);
}
window.TechDailyEdition={get:()=>selected};
if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",init,{once:true});else init();
})();