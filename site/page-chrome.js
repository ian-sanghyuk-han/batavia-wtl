/* Shared sub-page chrome: settings (theme + language) reachable from every page.
   Injected after inline EN swaps run (defer), so the header it decorates is final. */
(function(){
const T=localStorage.getItem('bp-theme')||'dark';
const L=localStorage.getItem('bp-lang')||'en';
const EN=L==='en';
const h=document.querySelector('header');if(!h)return;
const btn=document.createElement('span');
btn.id='pcset';btn.textContent='⚙';btn.title=EN?'Settings':'설정';
btn.style.cssText='float:right;margin:2px 0 0 14px;cursor:pointer;color:var(--acc);font-size:13px;user-select:none';
const menu=document.createElement('div');
menu.style.cssText='display:none;position:fixed;top:46px;right:16px;z-index:99;min-width:168px;padding:9px 12px 11px;'+
 'background:var(--glass);border:1px solid var(--edge);border-radius:11px;backdrop-filter:blur(9px)';
const head=t=>{const d=document.createElement('div');d.textContent=t;
  d.style.cssText='font:600 9px Consolas,monospace;letter-spacing:1px;color:var(--mut);margin:7px 0 2px';
  menu.appendChild(d);};
const row=(txt,on,fn)=>{const d=document.createElement('div');
  d.textContent=txt+(on?'  ✓':'');
  d.style.cssText='padding:5px 4px;font:11px "Segoe UI";color:var(--ink);cursor:pointer;border-radius:6px';
  d.onmouseenter=()=>d.style.background='rgba(127,216,255,.10)';
  d.onmouseleave=()=>d.style.background='none';
  d.onclick=fn;menu.appendChild(d);};
head(EN?'THEME':'테마');
row(EN?'● Dark':'● 다크',T==='dark',()=>{localStorage.setItem('bp-theme','dark');location.reload();});
row(EN?'○ Light':'○ 라이트',T==='gundam'||T==='light',()=>{localStorage.setItem('bp-theme','gundam');location.reload();});
head(EN?'LANGUAGE':'언어');
row('English',EN,()=>{localStorage.setItem('bp-lang','en');location.reload();});
row('한국어',!EN,()=>{localStorage.setItem('bp-lang','ko');location.reload();});
btn.addEventListener('click',e=>{
  menu.style.display=menu.style.display==='none'?'block':'none';e.stopPropagation();});
document.addEventListener('click',e=>{
  if(e.target!==btn&&!menu.contains(e.target))menu.style.display='none';});
h.appendChild(btn);document.body.appendChild(menu);
})();
