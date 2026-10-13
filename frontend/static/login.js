const $=s=>document.querySelector(s);
const SL=[["Fastest routes","Dijkstra, Bellman-Ford and Floyd-Warshall find the quickest path between any two campus stops."],
["Smarter schedules","Greedy trip scheduling and knapsack DP fill every shuttle without breaking seat limits or shift windows."],
["Lean networks","Kruskal and Prim build the cheapest backbone, and a policy report recommends how many shuttles to run."]];
let sl=0,mode='reg',timer;
function showSlide(i){sl=i;$('#ttl').textContent=SL[i][0];$('#dsc').textContent=SL[i][1];
 $('#dots').innerHTML=SL.map((_,j)=>`<button class="${j==i?'on':''}" data-i="${j}" aria-label="Slide ${j+1}"></button>`).join('')}
$('#dots').addEventListener('click',e=>{const b=e.target.closest('button');if(b){showSlide(+b.dataset.i);clearInterval(timer)}});
showSlide(0);timer=setInterval(()=>showSlide((sl+1)%SL.length),6000);
function setMode(m){mode=m;$('#t-reg').classList.toggle('on',m=='reg');$('#t-log').classList.toggle('on',m=='log');
 $('#name').style.display=m=='reg'?'':'none';$('#pw').autocomplete=m=='reg'?'new-password':'current-password';$('#err').textContent=''}
$('#t-reg').onclick=()=>setMode('reg');$('#t-log').onclick=()=>setMode('log');setMode('reg');
$('#eye').onclick=()=>{const p=$('#pw'),s=p.type=='password';p.type=s?'text':'password';$('#eye').textContent=s?'hide':'show'};
async function post(url,data){const r=await fetch(url,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data||{})});const j=await r.json().catch(()=>({}));if(!r.ok)throw new Error(j.error||'Something went wrong.');return j}
async function submit(){const b=$('#go');$('#err').textContent='';b.disabled=true;
 try{await post(mode=='reg'?'/api/register':'/api/login',{name:$('#name').value,email:$('#email').value,password:$('#pw').value});location='/app'}
 catch(e){$('#err').textContent=e.message;b.disabled=false}}
$('#go').onclick=submit;
['#name','#email','#pw'].forEach(s=>$(s).addEventListener('keydown',e=>{if(e.key=='Enter')submit()}));
$('#guest').onclick=async()=>{try{await post('/api/guest');location='/app'}catch(e){$('#err').textContent=e.message}};
