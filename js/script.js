const K = 0.0864, $ = s => document.querySelector(s);
const css = (v, elx) => getComputedStyle(elx || document.documentElement).getPropertyValue(v).trim();
function rng(seed){let a=seed>>>0;return()=>{a|=0;a=a+0x6D2B79F5|0;let t=Math.imul(a^a>>>15,1|a);t=t+Math.imul(t^t>>>7,61|t)^t;return((t^t>>>14)>>>0)/4294967296;};}
function gauss(r){return Math.sqrt(-2*Math.log(r()+1e-12))*Math.cos(2*Math.PI*r());}
function fill(arr){const o=arr.slice();let l=null;for(let i=0;i<o.length;i++){if(o[i]==null)o[i]=l;else l=o[i];}l=null;for(let i=o.length-1;i>=0;i--){if(o[i]==null)o[i]=l;else l=o[i];}return o;}
function simulate(name,a,b,o){
  const g=DATA[name],i0=g.d.indexOf(a),i1=g.d.indexOf(b);
  const d=g.d.slice(i0,i1+1),qin=g.qi.slice(i0,i1+1),act=g.v.slice(i0,i1+1),qo=g.qo.slice(i0,i1+1);
  const hi=fill(g.hi).slice(i0,i1+1),lo=fill(g.lo).slice(i0,i1+1).map(x=>x==null?0:x);
  const r=rng(7),n=d.length,V=[act[0]],Q=[],qEnv=2,margin=5,loss=0.1;
  for(let t=0;t<n;t++){let s=V[t],need=-Infinity;
    for(let k=0;k<=o.lead&&t+k<n;k++){s+=(qin[t+k]*(1+o.err+0.05*gauss(r))-qEnv)*K-loss;need=Math.max(need,(s-(hi[t]-margin))/(K*(k+1)));}
    let q=Math.min(qEnv+Math.max(0,need),o.qs);
    if(need<=0){const fq=(V[t]+qin[t]*K-loss-lo[t])/K;q=Math.min(q,Math.max(qEnv,fq));}
    q=Math.max(q,0);Q.push(q);V.push(V[t]+(qin[t]-q)*K-loss);}
  return{d,qin,act,qo,hi,lo,smart:V.slice(1),out:Q,total:g.total,hasLo:g.lo.some(x=>x!=null),lim:g.lim};
}
function quota(s,q){const m={};s.d.forEach((d,i)=>{const k=String(+d.split('-')[0]);m[k]=(m[k]||0)+q[i]*K;});let best=null;for(const k in m){if(s.lim&&s.lim[k]){const p=100*m[k]/s.lim[k];if(best==null||p>best)best=p;}}return best==null?null:Math.round(best);}
function kpi(s){const above=v=>v.filter((x,i)=>x>s.hi[i]).length,below=v=>s.hasLo?v.filter((x,i)=>x<s.lo[i]).length:null,mx=v=>Math.max(...v);
  return[['Peak volume, million m³',mx(s.act),mx(s.smart),'low'],['Days above upper schedule',above(s.act),above(s.smart),'low'],['Days below lower schedule',below(s.act),below(s.smart),'low'],['Peak release, m³/s',mx(s.qo),mx(s.out),'low'],['Fullest month vs quota, %',quota(s,s.qo),quota(s,s.out),'info'],['Volume at period end, million m³',s.act.at(-1),s.smart.at(-1),'info']];}
const NS='http://www.w3.org/2000/svg';
function el(tag,at,p){const e=document.createElementNS(NS,tag);for(const k in at)e.setAttribute(k,at[k]);if(p)p.appendChild(e);return e;}
function ticks(min,max,n){const st=Math.pow(10,Math.floor(Math.log10((max-min)/n)));const m=[1,2,5,10].find(m=>(max-min)/(st*m)<=n)*st;const o=[];for(let v=Math.ceil(min/m)*m;v<=max;v+=m)o.push(+v.toFixed(6));return o;}
const MONTHS=['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
const fmtDay=md=>{const[m,dd]=md.split('-');return`${+dd} ${MONTHS[+m-1]}`;};
function drawVolume(svg,s,W,H,c){
  svg.innerHTML='';const P={l:48,r:44,t:12,b:28},barH=H*0.22,plotB=H-P.b-barH-10;
  const vals=[...s.act,...s.smart,...s.hi,...(s.hasLo?s.lo:[])].filter(x=>x!=null);
  let y0=Math.min(...vals),y1=Math.max(...vals);const pad=(y1-y0)*0.08;y0-=pad;y1+=pad;
  const n=s.d.length,x=i=>P.l+(W-P.l-P.r)*i/(n-1||1),y=v=>P.t+(plotB-P.t)*(1-(v-y0)/(y1-y0));
  const txt=(X,Y,t,anchor)=>{const e=el('text',{x:X,y:Y,'text-anchor':anchor||'start','font-size':12,fill:c.soft,'font-family':'Archivo, Arial, sans-serif'},svg);e.textContent=t;};
  ticks(y0,y1,5).forEach(t=>{el('line',{x1:P.l,x2:W-P.r,y1:y(t),y2:y(t),stroke:c.rule,'stroke-width':1},svg);txt(P.l-8,y(t)+4,t,'end');});
  const area=(arr,top)=>{let p=`M${x(0)},${top?P.t:plotB}`;arr.forEach((v,i)=>p+=`L${x(i)},${y(Math.max(y0,Math.min(y1,v)))}`);return p+`L${x(n-1)},${top?P.t:plotB}Z`;};
  el('path',{d:area(s.hi,true),fill:c.flood,'fill-opacity':.12},svg);
  if(s.hasLo)el('path',{d:area(s.lo,false),fill:c.dry,'fill-opacity':.14},svg);
  const line=(arr,col,w,dash)=>el('path',{d:arr.map((v,i)=>`${i?'L':'M'}${x(i)},${y(v)}`).join(''),fill:'none',stroke:col,'stroke-width':w,'stroke-dasharray':dash||'','stroke-linejoin':'round','stroke-linecap':'round'},svg);
  line(s.hi,c.flood,1.8,'7 5');if(s.hasLo)line(s.lo,c.dry,1.8,'7 5');
  line(s.act,c.grey,3.2);line(s.smart,c.water,3.6);
  const qmax=Math.max(...s.qin,1),bw=Math.max(1,(W-P.l-P.r)/n-1.5),by=H-P.b;
  s.qin.forEach((q,i)=>el('rect',{x:x(i)-bw/2,y:by-barH*q/qmax,width:bw,height:barH*q/qmax,rx:1.5,fill:c.bar},svg));
  txt(W-P.r-4,by-barH-4,'max '+Math.round(qmax)+' m³/s','end');
  const step=Math.ceil(n/7);for(let i=0;i<n;i+=step)txt(x(i),H-6,fmtDay(s.d[i]),'middle');
}
const heroColors=()=>{const h=$('.hero');return{soft:css('--lake-soft',h),rule:css('--lake-line',h),flood:css('--lake-flood',h),dry:css('--lake-dry',h),grey:css('--lake-grey',h),water:css('--lake-water',h),bar:'rgba(108,210,227,.45)'};};
const pageColors=()=>({soft:css('--soft'),rule:css('--rule'),flood:css('--flood'),dry:css('--dry'),grey:css('--grey'),water:css('--water'),bar:css('--water-2')});
function hero(){const lead=+$('#hero-lead').value;$('#hero-lead-out').value=`${lead} day${lead===1?'':'s'}`;$('#h-lead').textContent=lead;
  const s=simulate('Studen Kladenets','11-15','12-31',{lead,qs:DATA['Studen Kladenets'].qmax,err:0});drawVolume($('#hero-chart'),s,1100,380,heroColors());
  const k=kpi(s);$('#h-act').textContent=k[1][1];$('#h-smart').textContent=k[1][2];}
let period=['11-15','12-31'];const f1=v=>v==null?'n/a':(Number.isInteger(v)?v:v.toFixed(1));
function sim(){const dam=$('#dam').value,lead=+$('#lead').value,qs=+$('#qs').value,err=+$('#err').value/100;
  $('#lead-out').value=`${lead} day${lead===1?'':'s'}`;$('#qs-out').value=`${qs} m³/s${Math.abs(qs-DATA[dam].qmax)<0.05?' (2017 maximum)':''}`;$('#err-out').value=`${err>0?'+':''}${Math.round(err*100)}%`;
  const s=simulate(dam,period[0],period[1],{lead,qs,err});drawVolume($('#sim-chart'),s,760,400,pageColors());
  const tb=$('#kpi tbody');tb.innerHTML='';
  kpi(s).forEach(([lab,a,b,mode])=>{const tr=document.createElement('tr');let cls='';if(mode==='low'&&a!=null&&b!=null&&Math.abs(a-b)>0.05)cls=b<a?'better':'worse';
    tr.innerHTML=`<td>${lab}</td><td>${f1(a)}</td><td class="${cls}">${f1(b)}</td>`;tb.appendChild(tr);});
  $('#sim-note').textContent=s.hasLo?`Forecast = observed inflow with 5% noise${err?`, biased ${Math.round(err*100)}%`:''}. Quota = released water as a share of the ministry’s monthly permit. Blue marks a number that improved; red marks one that got worse.`
    :'The 2017 reports give Ivaylovgrad no dry-season reserve, so here the plan guards the upper schedule and nothing else.';}
document.querySelectorAll('.per').forEach(b=>b.addEventListener('click',()=>{document.querySelectorAll('.per').forEach(x=>x.setAttribute('aria-pressed','false'));b.setAttribute('aria-pressed','true');period=[b.dataset.a,b.dataset.b];sim();}));
['#lead','#qs','#err'].forEach(id=>$(id).addEventListener('input',sim));$('#dam').addEventListener('change',()=>{$('#qs').value=DATA[$('#dam').value].qmax;sim();});$('#hero-lead').addEventListener('input',hero);
function cascade(){const i=+$('#day').value,svg=$('#cascade');svg.innerHTML='';const soft=css('--soft');
  const names=['Kardzhali','Studen Kladenets','Ivaylovgrad'],xs=[150,450,750];$('#day-out').value=fmtDay(DATA.Kardzhali.d[i])+' 2017';
  el('path',{d:'M10,170 C80,160 100,180 150,172 S300,160 450,172 S620,185 750,172 S860,165 890,170',fill:'none',stroke:css('--water-2'),'stroke-width':7,'stroke-linecap':'round'},svg);
  const T=(X,Y,t,o)=>{const e=el('text',Object.assign({x:X,y:Y,'font-size':12,fill:soft,'font-family':'Archivo, Arial, sans-serif'},o||{}),svg);e.textContent=t;};
  T(12,200,'Arda river, upstream');T(888,200,'towards Greece and Turkey',{'text-anchor':'end'});
  names.forEach((nm,j)=>{const g=DATA[nm],v=g.v[i],hi=fill(g.hi)[i],lo=fill(g.lo)[i],pct=v/g.total;
    const st=v>hi?'flood':(lo!=null&&v<lo?'dry':'ok'),col=st==='flood'?css('--flood'):st==='dry'?css('--dry'):css('--rule');
    const X=xs[j]-60,Y=60,Wd=120,Hd=100;
    el('rect',{x:X,y:Y,width:Wd,height:Hd,rx:10,fill:css('--page'),stroke:col,'stroke-width':st==='ok'?2:4},svg);
    el('rect',{x:X+3,y:Y+Hd-3-(Hd-6)*pct,width:Wd-6,height:(Hd-6)*pct,rx:7,fill:css('--water'),'fill-opacity':.6},svg);
    el('line',{x1:X,x2:X+Wd,y1:Y+Hd-Hd*hi/g.total,y2:Y+Hd-Hd*hi/g.total,stroke:css('--flood'),'stroke-dasharray':'4 3','stroke-width':1.6},svg);
    if(lo!=null)el('line',{x1:X,x2:X+Wd,y1:Y+Hd-Hd*lo/g.total,y2:Y+Hd-Hd*lo/g.total,stroke:css('--dry'),'stroke-dasharray':'4 3','stroke-width':1.6},svg);
    T(xs[j],42,nm,{'text-anchor':'middle','font-size':16,'font-weight':700,fill:css('--ink')});
    T(xs[j],225,`${Math.round(pct*100)}% full, in ${Math.round(g.qi[i])} / out ${Math.round(g.qo[i])} m³/s`,{'text-anchor':'middle'});});}
$('#day').addEventListener('input',cascade);
function soil(){const svg=$('#sm-chart');svg.innerHTML='';const W=520,H=300,P={l:40,r:10,t:10,b:28},soft=css('--soft');
  const A=DATA._sm.arda_basin,S=DATA._sm.sofia_iskar,max=0.4,bw=(W-P.l-P.r)/12,y=v=>P.t+(H-P.t-P.b)*(1-v/max);
  [0,.1,.2,.3,.4].forEach(t=>{el('line',{x1:P.l,x2:W-P.r,y1:y(t),y2:y(t),stroke:css('--rule')},svg);const e=el('text',{x:P.l-6,y:y(t)+4,'text-anchor':'end','font-size':11,fill:soft,'font-family':'Archivo, Arial, sans-serif'},svg);e.textContent=t.toFixed(1);});
  A.forEach((v,i)=>{const x0=P.l+i*bw+bw*.12;el('rect',{x:x0,y:y(v),width:bw*.36,height:y(0)-y(v),rx:2,fill:css('--dry')},svg);el('rect',{x:x0+bw*.38,y:y(S[i]),width:bw*.36,height:y(0)-y(S[i]),rx:2,fill:css('--water-2')},svg);
    const e=el('text',{x:P.l+i*bw+bw/2,y:H-8,'text-anchor':'middle','font-size':11,fill:soft,'font-family':'Archivo, Arial, sans-serif'},svg);e.textContent=MONTHS[i][0];});}
function drawAll(){hero();sim();cascade();soil();}
$('#theme').addEventListener('click',()=>{const r=document.documentElement;const dark=r.dataset.theme?r.dataset.theme==='dark':matchMedia('(prefers-color-scheme: dark)').matches;r.dataset.theme=dark?'light':'dark';drawAll();});
matchMedia('(prefers-color-scheme: dark)').addEventListener('change',drawAll);
drawAll();
