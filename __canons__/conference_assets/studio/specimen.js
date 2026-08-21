/* specimen.js — the two A0 proof surfaces and the coverage instrument, shared by studio plates.
   Depends on PE (palette-engine.js). Exposes window.SP. */
(function(){
const L=`<div class="sp-sheet" data-cover>
  <div class="sp-bar" data-cover><div class="h"></div><div class="ln"><i style="width:100%"></i><i style="width:96%"></i><i style="width:88%"></i></div><div class="ln"><i style="width:100%"></i><i style="width:92%"></i><i style="width:70%"></i></div></div>
  <div class="sp-main" data-cover>
    <div class="sp-plate" data-cover="plate"><span>X halves Y under Z — and the <em>mechanism</em> is not the obvious one.</span></div>
    <div class="sp-ev" data-cover><div class="cap"></div><div class="sp-chart"><i style="height:34%"></i><i style="height:52%"></i><i style="height:41%"></i><i class="hit" style="height:88%"></i><i style="height:47%"></i><i style="height:29%"></i><i style="height:38%"></i></div></div>
    <div class="sp-foot"><div class="lm"></div><div class="qr"></div></div>
  </div>
</div>`;
const P=`<div class="sp-sheet" data-orient="portrait" data-cover>
  <div class="sp-page">
  <div class="sp-head"><div class="h"></div><div class="ln"><i style="width:100%"></i><i style="width:72%"></i></div></div>
  <div class="sp-main" data-cover>
    <div class="sp-plate" data-cover="plate"><span>X halves Y under Z — and the <em>mechanism</em> is not the obvious one.</span></div>
    <div class="sp-ev" data-cover><div class="cap"></div><div class="sp-chart"><i style="height:34%"></i><i style="height:52%"></i><i style="height:41%"></i><i class="hit" style="height:88%"></i><i style="height:47%"></i><i style="height:29%"></i></div></div>
    <div class="sp-meth"><i data-cover></i><i data-cover></i><i data-cover></i></div>
    <div class="sp-foot"><div class="lm"></div><div class="qr"></div></div>
  </div>
  </div>
</div>`;
function build(root){
  (root||document).querySelectorAll('.specimen').forEach(s=>{
    if(s.firstElementChild)return;
    s.innerHTML=s.dataset.orient==='portrait'?P:L;
    if(s.dataset.plate)s.firstElementChild.setAttribute('data-plate',s.dataset.plate);
  });
}
function same(a,b){const x=PE.hex2rgb(a),y=PE.hex2rgb(b);return Math.abs(x[0]-y[0])<3&&Math.abs(x[1]-y[1])<3&&Math.abs(x[2]-y[2])<3}
function coverage(sheet,paper){
  const R=sheet.getBoundingClientRect(),A=R.width*R.height;if(!A)return null;
  if(!paper){const sc=sheet.closest('[data-theme],[data-scope]');paper=sc?getComputedStyle(sc).getPropertyValue('--paper').trim():'#FFFFFF'}
  const els=[sheet].concat([].slice.call(sheet.querySelectorAll('[data-cover]')));
  const box=el=>{const r=el.getBoundingClientRect();return r.width*r.height};
  const nearest=o=>o.parentElement?o.parentElement.closest('[data-cover]'):null;
  let marks=0,ground=0,plate=0;
  els.forEach(el=>{
    const bg=getComputedStyle(el).backgroundColor;
    if(!bg||bg==='rgba(0, 0, 0, 0)')return;
    let net=box(el);
    els.forEach(o=>{if(o!==el&&el.contains(o)&&nearest(o)===el)net-=box(o)});
    if(net<=0)return;
    const cost=(net/A)*(1-PE.lum(bg));
    if(same(bg,paper))ground+=cost;else marks+=cost;
  });
  [].slice.call(sheet.querySelectorAll('[data-cover="plate"]')).forEach(el=>{plate+=box(el)/A});
  return{c:Math.min(marks+ground,1),marks:marks,ground:ground,plate:plate};
}
function meter(host,m,label){
  if(!m){host.innerHTML='';return}
  const w=Math.min(m.c/PE.COV_MAX,1)*100,gw=Math.min(m.ground/PE.COV_MAX,1)*100;
  host.innerHTML='<div class="who">'+(label||'')+'</div><div class="bar"><i style="width:'+w+'%"></i><s style="width:'+gw+'%"></s><u style="left:calc(100% - 1px)"></u></div>'+
  '<div class="cap"><span>C <b>'+(m.c*100).toFixed(1)+'%</b> — marks '+(m.marks*100).toFixed(1)+'% \u00B7 ground '+(m.ground*100).toFixed(1)+'%</span>'+
  '<span>plate <b>'+(m.plate*100).toFixed(1)+'%</b> / '+(PE.PLATE_MAX*100).toFixed(0)+'%</span></div>';
}
function apply(el,roles){PE.ROLES.forEach(r=>el.style.setProperty('--'+r,roles[r].hex))}
window.SP={LANDSCAPE:L,PORTRAIT:P,build:build,coverage:coverage,meter:meter,apply:apply};
})();
