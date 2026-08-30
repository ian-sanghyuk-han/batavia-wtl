/* Shared sub-page chrome: settings (theme + language) reachable from every page.
   Injected after inline EN swaps run (defer), so the header it decorates is final. */
(function(){
const T=localStorage.getItem('bp-theme')||'dark';
const L=localStorage.getItem('bp-lang')||'en';
const EN=L==='en';
const h=document.querySelector('header');if(!h)return;
/* unified tabs (canvas design): a sticky bar at the very top of every page, so
   navigation never scrolls away; hides the old one-way back link */
const back=h.querySelector('a[href="./"]');if(back)back.style.display='none';
const path=location.pathname.split('/').pop()||'index.html';
const TABS=[['TODAY','index.html'],['OBSERVATORY','observatory.html'],['NEXT','next.html'],
 ['LEDGER','ledger.html'],['CALENDAR','calendar.html'],['REPLAY','replay.html']];
const bar=document.createElement('div');
bar.style.cssText='position:sticky;top:0;z-index:80;display:flex;align-items:center;gap:4px;flex-wrap:wrap;'+
 'padding:9px 16px;background:var(--glass);border-bottom:1px solid var(--edge);backdrop-filter:blur(9px)';
const brand=document.createElement('a');
brand.textContent='BATAVIA';brand.href='./';
brand.style.cssText='font:600 11px Consolas,monospace;letter-spacing:3px;color:var(--ink);text-decoration:none;margin-right:8px';
bar.appendChild(brand);
TABS.forEach(([lb,href])=>{const a=document.createElement('a');
  a.textContent=lb;a.href=href==='index.html'?'./':href;
  const on=(path===href)||(href==='index.html'&&(path===''||path==='index.html'));
  a.style.cssText='font:600 10px Consolas,monospace;letter-spacing:2px;padding:6px 12px;border-radius:8px;text-decoration:none;'+
    (on?'color:#06121c;background:var(--acc)':'color:var(--dim)');
  bar.appendChild(a);});
const btn=document.createElement('span');
btn.id='pcset';btn.textContent='⚙';btn.title=EN?'Settings':'설정';
btn.style.cssText='margin-left:auto;cursor:pointer;color:var(--acc);font-size:13px;user-select:none;padding:0 2px';
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
bar.appendChild(btn);document.body.prepend(bar);document.body.appendChild(menu);
})();
