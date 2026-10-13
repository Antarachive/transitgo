// TransitGo dashboard: all optimisation runs on the Flask backend; this file only draws.
const $=s=>document.querySelector(s);
let ST=[],ED=[],G=[],ME='';
const S={m:0,algo:'dijkstra',src:0,dst:3,lane:false,ma:'kruskal',k:2,cap:20,dense:false,bench:null};
let seq=0;
async function api(path,data){
 const r=await fetch('/api/'+path,{method:data?'POST':'GET',headers:{'Content-Type':'application/json'},body:data?JSON.stringify(data):undefined});
 if(r.status==401){location='/';throw new Error('auth')}
 const j=await r.json().catch(()=>({}));if(!r.ok)throw new Error(j.error||'Request failed');return j}
const key=(a,b)=>a<b?a+'-'+b:b+'-'+a;
const nm=i=>ST[i].name,f1=x=>Math.round(x*10)/10;
const clk=m=>Math.floor(m/60+7)+':'+String(m%60).padStart(2,'0');
const IC={route:'<circle cx="6" cy="18" r="2.5"/><circle cx="18" cy="6" r="2.5"/><path d="M8.5 18h6a3 3 0 0 0 0-6h-5a3 3 0 0 1 0-6h6"/>',
mst:'<circle cx="12" cy="5" r="2"/><circle cx="5" cy="19" r="2"/><circle cx="19" cy="19" r="2"/><path d="M12 7v5m0 0-6 5m6-5 6 5"/>',
sch:'<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',ben:'<path d="M5 20V10M12 20V4M19 20v-8"/>',
pol:'<rect x="6" y="4" width="12" height="17" rx="2"/><path d="M9 4h6v3H9zM9 12h6M9 16h4"/>',
theme:'<circle cx="12" cy="12" r="8"/><path d="M12 4a8 8 0 0 1 0 16z" fill="currentColor"/>',
reset:'<path d="M4 12a8 8 0 1 0 3-6.2M4 4v4h4"/>',out:'<path d="M9 4H5v16h4M16 8l4 4-4 4M20 12H9"/>'};
const M=[
{k:'route',l:'Routes',t:'Fastest route finder',d:'Pick two stops and an algorithm. Dijkstra, Bellman-Ford and Floyd-Warshall each find the quickest shuttle path across the campus graph.'},
{k:'mst',l:'Backbone',t:'Minimum backbone network',d:'Kruskal and Prim connect every stop using the least total travel time, a cost-minimal skeleton for permanent shuttle lanes.'},
{k:'sch',l:'Schedule',t:'Greedy trips + knapsack loads',d:'Greedy earliest-finish scheduling packs trips into shuttle shifts, then 0-1 knapsack DP picks which waiting groups board within seat capacity.'},
{k:'ben',l:'Benchmark',t:'Runtime experiments',d:'Random graphs of growing size and density show how each algorithm scales, so trade-offs are measured rather than assumed.'},
{k:'pol',l:'Policy',t:'Policy recommendation',d:'Compares fleet sizes by trips served, waiting time and cost, then recommends a fleet size and a loop route.'}];
function nav(){
 $('#nav').innerHTML='<svg class="logo" width="26" height="26" viewBox="0 0 24 24" aria-label="TransitGo"><path d="M12 2c3 4 6.5 6.5 6.5 11.2a6.5 6.5 0 0 1-13 0C5.5 11 6.8 9.6 8 8.6c0 2 .9 3.2 2 3.4-.4-4 0-7 2-10z" fill="var(--accent)"/></svg>'+
 M.map((x,i)=>`<button class="nb ${i==S.m?'on':''}" data-m="${i}" aria-label="${x.l}"><svg viewBox="0 0 24 24">${IC[x.k]}</svg>${x.l}</button>`).join('')+
 '<div class="sp"></div>'+[['theme','Theme'],['reset','Reset'],['out','Logout']].map(([a,l])=>`<button class="nb" data-a="${a}" aria-label="${l}"><svg viewBox="0 0 24 24">${IC[a]}</svg>${l}</button>`).join('');
 $('#dots').innerHTML=M.map((x,i)=>`<button class="${i==S.m?'on':''}" data-m="${i}" aria-label="${x.l}"></button>`).join('');
}
const opts=(a,list,v)=>`<div class="row">${list.map(([x,l])=>`<button class="opt ${x==v?'on':''}" data-a="${a}" data-v="${x}">${l||x}</button>`).join('')}</div>`;
const sel=(id,v)=>`<select class="fld" id="${id}" aria-label="${id}">${ST.map((s,i)=>`<option value="${i}" ${i==v?'selected':''}>${s.name}</option>`).join('')}</select>`;
const capCtl=()=>`<div class="lbl">Seat capacity: <span id="cv">${S.cap}</span></div><input type="range" id="cap" min="10" max="60" value="${S.cap}" aria-label="Seat capacity">`;
function form(){
 const m=S.m;let h=`<div class="brand">TransitGo · ${M[m].l}</div>`;
 if(m==0)h+=`<h1>Plan a route</h1><p class="sub">One graph, three shortest-path algorithms</p>${opts('algo',[['dijkstra','Dijkstra'],['bellman-ford','Bellman-Ford'],['floyd-warshall','Floyd-Warshall']],S.algo)}
 <div class="lbl">From</div>${sel('src',S.src)}<div class="lbl">To</div>${sel('dst',S.dst)}
 <label class="tg"><input type="checkbox" id="lane" ${S.lane?'checked':''}> Priority lane: Academic → Library costs −2 min</label>`;
 if(m==1)h+=`<h1>Build the backbone</h1><p class="sub">Connect every stop at minimum total travel time</p>${opts('ma',[['kruskal','Kruskal'],['prim','Prim']],S.ma)}`;
 if(m==2)h+=`<h1>Schedule the fleet</h1><p class="sub">Shift 07:00–11:00 · 14 trip requests · 8 waiting groups</p><div class="lbl">Shuttles</div>${opts('k',[1,2,3,4].map(x=>[x,x]),S.k)}${capCtl()}`;
 if(m==3)h+=`<h1>Run experiments</h1><p class="sub">Random graphs, 20 to 120 stops</p>${opts('dense',[['0','Sparse'],['1','Dense']],S.dense?'1':'0')}<button class="go" id="runb" data-a="run">Run benchmark</button>`;
 if(m==4)h+=`<h1>Recommend a policy</h1><p class="sub">Fleet size, loading rule and loop route</p>${capCtl()}`;
 $('#right').innerHTML=h+'<div class="sep">result</div><div class="res" id="out" aria-live="polite"></div><div class="who">Signed in as '+ME+'</div>';
}
function art(hl=[],nd=[]){
 const H=new Set(hl.map(e=>key(e[0],e[1]))),Nd=new Set(nd);
 let s='<svg viewBox="0 0 400 340" role="img" aria-label="Campus graph"><circle cx="352" cy="30" r="22" fill="var(--accent)"/><path d="M336 24c10-8 22-6 30 4M334 36c12 4 24 0 32-8M341 16c8 14 4 24-2 32" stroke="#fff" fill="none" stroke-width="1.4" opacity=".75"/><path d="M20 36q8-12 20-6 6-8 18 0 10 0 10 8H20z" fill="none" stroke="var(--ink)" stroke-width="1.3"/>';
 ED.forEach(([u,v])=>{const on=H.has(key(u,v));s+=`<line x1="${ST[u].x}" y1="${ST[u].y}" x2="${ST[v].x}" y2="${ST[v].y}" stroke="${on?'var(--accent)':'var(--ink)'}" stroke-width="${on?5:1.4}" stroke-linecap="round" ${on?'':'opacity=".7"'}/>`});
 const halo='style="paint-order:stroke;stroke:var(--paper);stroke-width:3px"';
 ED.forEach(([u,v,w])=>{s+=`<text x="${(ST[u].x+ST[v].x)/2}" y="${(ST[u].y+ST[v].y)/2+3}" font-size="9" text-anchor="middle" fill="var(--ink)" ${halo}>${w}</text>`});
 ST.forEach((p,i)=>{const on=Nd.has(i);s+=`<circle cx="${p.x}" cy="${p.y}" r="${on?10:8}" fill="${i==0?'var(--yel)':on?'var(--accent)':'var(--paper)'}" stroke="var(--ink)" stroke-width="2"/><text x="${p.x}" y="${p.y+22}" font-size="10" text-anchor="middle" fill="var(--ink)" ${halo}>${p.name}</text>`});
 s+='<g transform="translate(12,300)" stroke="var(--ink)" stroke-width="1.5"><rect width="46" height="22" rx="4" fill="var(--green)"/><rect x="5" y="4" width="10" height="8" fill="var(--paper)"/><rect x="19" y="4" width="10" height="8" fill="var(--paper)"/><rect x="33" y="4" width="8" height="8" fill="var(--paper)"/><circle cx="11" cy="23" r="4.5" fill="var(--ink)"/><circle cx="35" cy="23" r="4.5" fill="var(--ink)"/></g></svg>';
 $('#art').innerHTML=s;
}
function chart(rows){
 const al=[['dijkstra','Dijkstra','var(--accent)'],['bellman_ford','Bellman-Ford','var(--green)'],['floyd_warshall','Floyd-Warshall','var(--red)'],['kruskal','Kruskal','var(--ink)']];
 const mx=Math.max(...rows.flatMap(r=>al.map(a=>r[a[0]]))),L=v=>Math.log10(1+v*1000)/Math.log10(1+mx*1000);
 let s='<svg viewBox="0 0 400 340" role="img" aria-label="Runtime chart"><text x="200" y="22" font-size="11" text-anchor="middle" fill="var(--ink)">runtime (log scale)</text>';
 rows.forEach((r,i)=>{const gx=34+i*92;al.forEach((a,j)=>{const h=Math.max(2,L(r[a[0]])*220);s+=`<rect x="${gx+j*17}" y="${280-h}" width="14" height="${h}" fill="${a[2]}" stroke="var(--ink)"/>`});s+=`<text x="${gx+34}" y="298" font-size="10" text-anchor="middle" fill="var(--ink)">n=${r.n}</text>`});
 s+='<line x1="24" y1="280" x2="392" y2="280" stroke="var(--ink)"/>';
 al.forEach((a,j)=>{s+=`<rect x="${14+j*96}" y="314" width="9" height="9" fill="${a[2]}" stroke="var(--ink)"/><text x="${27+j*96}" y="322" font-size="8.5" fill="var(--ink)">${a[1]}</text>`});
 $('#art').innerHTML=s+'</svg>';
}
const kn=(c,cap)=>`<b>0-1 knapsack</b> (${cap} seats): board ${c.picked.map(i=>nm(G[i][0])+' ×'+G[i][1]).join(', ')||'nobody'}
Seats used ${c.seats_used}/${cap} · waiting relieved ${c.value} pax-min
Ratio-greedy gets ${c.ratio_greedy_value}${c.ratio_greedy_value<c.value?` <span class="warn">(${c.value-c.ratio_greedy_value} short)</span>`:' (ties here)'} · fractional upper bound ${c.fractional_bound}`;
async function run(){
 const my=++seq,m=S.m,o=$('#out');
 try{
  if(m==0){const r=await api('route',{algo:S.algo,src:S.src,dst:S.dst,lane:S.lane});if(my!=seq)return;
   o.innerHTML=r.path.length?`Route: <b>${r.path.map(nm).join(' → ')}</b>\nTravel time: ${r.cost} min · ${r.path.length-1} hops\nComplexity: ${r.complexity} · server time ${r.ms} ms`+(r.warning?`\n<span class="warn">${r.warning}</span>`:'')+(r.avg_trip!=null?`\nAll-pairs average trip: ${r.avg_trip} min`:''):'No route found.';
   art(r.edges,r.path)}
  if(m==1){const r=await api('mst',{algo:S.ma});if(my!=seq)return;
   o.innerHTML=`${r.algo} MST · ${r.edges.length} edges · total <b>${r.total} min</b>\n`+r.edges.map(e=>`${nm(e[0])} – ${nm(e[1])}  (${e[2]})`).join('\n')+`\nFull network costs ${r.full} min, so the backbone saves ${r.saved} min (${Math.round(r.saved/r.full*100)}%).\nComplexity: ${r.complexity}`;
   art(r.edges,[...new Set(r.edges.flatMap(e=>[e[0],e[1]]))])}
  if(m==2){const r=await api('schedule',{k:S.k,cap:S.cap});if(my!=seq)return;
   o.innerHTML=`<b>Greedy trips</b> (earliest finish): ${r.served.length}/${r.total} served · avg wait ${r.avg_wait} min\n`+r.served.map(t=>`S${t.j+1} ${clk(t.s)}-${clk(t.s+t.dur)} ${nm(t.o)} → ${nm(t.d)}`).join('\n')+`\n\n`+kn(r.knapsack,S.cap)+`\nComplexity: greedy O(n log n + nk) · DP O(n·cap)`;
   art(r.edges,r.nodes)}
  if(m==3){o.textContent='Press "Run benchmark" to time the algorithms on the server.';if(S.bench){drawBench();}else art()}
  if(m==4){const r=await api('policy',{cap:S.cap});if(my!=seq)return;
   o.innerHTML=`<table><tr><th>Shuttles</th><th>Served</th><th>Avg wait</th><th>Served/cost</th></tr>${r.rows.map(x=>`<tr><td>${x.k}${x.k==r.best_k?' ★':''}</td><td>${x.served}/${x.total}</td><td>${x.avg_wait}</td><td>${x.per_shuttle}</td></tr>`).join('')}</table>\nRecommended fleet: <b>${r.best_k} shuttle${r.best_k>1?'s':''}</b> (next vehicle adds ≤1 trip)\n`+kn(r.knapsack,S.cap)+`\nLoop route (nearest neighbour on all-pairs times): ${r.tour.map(nm).join(' → ')}, ${r.tour_time} min per loop`;
   art(r.edges,r.nodes)}
 }catch(e){if(e.message!='auth'&&my==seq)o.innerHTML=`<span class="warn">${e.message}</span>`}
}
function drawBench(){const R=S.bench;chart(R);$('#out').innerHTML=`<table><tr><th>n</th><th>Dijk</th><th>BF</th><th>FW</th><th>Krus</th></tr>${R.map(r=>`<tr><td>${r.n}</td><td>${r.dijkstra.toFixed(2)}</td><td>${r.bellman_ford.toFixed(2)}</td><td>${r.floyd_warshall.toFixed(2)}</td><td>${r.kruskal.toFixed(2)}</td></tr>`).join('')}</table>\n${S.dense?'Dense':'Sparse'} graphs, ms per run (Python). Floyd-Warshall grows cubically; Dijkstra and Kruskal stay near-linear.`}
async function bench(){const b=$('#runb');b.disabled=true;b.textContent='Running…';
 try{S.bench=(await api('benchmark',{dense:S.dense})).rows;drawBench()}catch(e){if(e.message!='auth')$('#out').innerHTML=`<span class="warn">${e.message}</span>`}
 b.disabled=false;b.textContent='Run benchmark'}
function go(i){S.m=i;nav();$('#ttl').textContent=M[i].t;$('#dsc').textContent=M[i].d;form();run()}
document.addEventListener('click',async e=>{const t=e.target.closest('[data-m],[data-a]');if(!t)return;
 if(t.dataset.m!==undefined)return go(+t.dataset.m);
 const a=t.dataset.a,v=t.dataset.v;
 if(a=='theme'){const r=document.documentElement,dark=getComputedStyle(r).getPropertyValue('--paper').trim()=='#241E17';r.dataset.theme=dark?'light':'dark';return}
 if(a=='out'){await fetch('/api/logout',{method:'POST'});location='/';return}
 if(a=='reset'){Object.assign(S,{algo:'dijkstra',src:0,dst:3,lane:false,ma:'kruskal',k:2,cap:20,dense:false,bench:null});return go(S.m)}
 if(a=='run')return bench();
 if(a=='k')S.k=+v;else if(a=='dense'){S.dense=v=='1';S.bench=null}else S[a]=v;
 form();run()});
document.addEventListener('change',e=>{const t=e.target;if(t.id=='src')S.src=+t.value;else if(t.id=='dst')S.dst=+t.value;else if(t.id=='lane')S.lane=t.checked;else return;run()});
document.addEventListener('input',e=>{if(e.target.id=='cap'){S.cap=+e.target.value;$('#cv').textContent=S.cap;run()}});
(async()=>{try{const [me,g]=await Promise.all([api('me'),api('graph')]);ME=me.name;ST=g.stops;ED=g.edges;G=g.groups;go(0)}catch(e){}})();
