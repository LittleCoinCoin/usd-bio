/* chart-kit.js — v3 (Goldilocks ink). Supersedes v2 in place.
   Same closed set of forms, same mm user units, same poster-distance floors, same PE dependency.
   Exposes window.CK. No hand-drawn illustration — bars, lines, arcs, circles, squares only.

   WHAT CHANGED IN v3, and why. Warrant for all six is [house]: Lai & Morrison 2025 is a
   literature commentary in the authors' own outlet (see evidence_base_v0.md §1).
   It licenses a PROCEDURE and a DIAGNOSTIC. It cannot warrant a numeric default, so every
   number below is a house choice, argued in the plate, not an evidence claim.

   1. INK IS A DIAL, NOT A CONSTANT.  Every form takes ink:'lean'|'mid'|'rich'. v2 hardcoded
      one dose (gridOp 0.55, 3 ticks, all values labelled) and exposed a single `scale` boolean,
      so the kit could render exactly one of the three charts the Goldilocks method requires.
   2. THE DOSE CAN COME FROM THE DWELL LAYER.  dwell:'5s'|'1min'|'5min' maps to rich|mid|lean.
      The 5s claim optimises memorability and can afford decoration; the 5min methods figure
      optimises accurate value reading and wants lean-but-fully-labelled. Deriving the dose from
      the layer beats any global constant.
   3. EXTRA INK CONCENTRATES ON THE CLAIM.  v2 only did this in rankedBar. series /
      dotComparison / distribution never printed the emphasised series' actual number, so the
      one datum doing the poster's work was encoded by colour and weight alone.
   4. distribution() DEFAULTS TO THE FAMILIAR BOXED FORM.  v2's strip-with-mean-bar is Tufte
      boxplot territory — the unfamiliar-form failure the commentary is specifically about.
      form:'box' (default) | 'strip' (v2 behaviour, opt-in) | 'both'.
   5. greyDiagnostic() REPORTS WHETHER COLOUR IS LOAD-BEARING OR DECORATIVE. The greyscale proof
      already existed as a CVD/mono-laser sufficiency test; this reads the same conversion as a
      data-ink diagnostic, which is the commentary's other usable contribution.
   6. goldilocks() RENDERS ONE DATASET AT ALL THREE DOSES so the test is runnable, not advisory.

   BACK-COMPAT: the v2 `scale:false` / `scale:true` boolean still works — it now resolves to the
   lean and mid doses, so 03-chart-kit.html's before/after comparison keeps working and
   becomes, correctly, a two-dose comparison. */
(function(){
const clamp=PE.clamp;
/* ---------- poster-distance floors, mm user units == mm on the sheet ---------- */
const LABEL_MM=7.06;    // = 20pt, the canon's --type-detail: the smallest sanctioned size anywhere on the sheet
const VALUE_MM=9.87;    // = 28pt, --type-caption: the one number doing the finding's work sits one step up
const STROKE={hair:0.35,data:1.4,strong:2.4};       // NOTE: 0.35 is a chart-internal hairline, NOT --rule-weight (0.6mm). See NOTES.
const GAP_MM=2.6;

/* ---------- the ink dial ----------
   Each dose is a coherent position on the minimal→embellished continuum, not a slider.
   `values`: 'emph' prints only the emphasised datum's number (ink spent on the claim);
   'all' prints every datum's number. `callout` allows one short annotation sentence inside
   the plot — the "unnecessary" ink the commentary argues buys attention and memorability. */
const DOSE={
  lean:{grid:false,gridOp:0,   ticks:2,tickScale:0.72,values:'emph',endDots:false,baseline:'hair',callout:false,points:false,leader:false},
  mid: {grid:true, gridOp:0.55,ticks:3,tickScale:0.80,values:'all', endDots:true, baseline:'hair',callout:false,points:false,leader:false},
  rich:{grid:true, gridOp:0.75,ticks:5,tickScale:0.94,values:'all', endDots:true, baseline:'data',callout:true, points:true, leader:true}
};
const DWELL={'5s':'rich','1min':'mid','5min':'lean'};
const DOSE_KEYS=['lean','mid','rich'];
function dose(o){
  let k=o.ink||DWELL[o.dwell]||null;
  if(!k){ k = o.scale===false ? 'lean' : 'mid'; }        // v2 boolean, resolved
  else if(o.scale===false) k='lean';                      // explicit no-scale still wins
  return Object.assign({key:k},DOSE[k]||DOSE.mid);
}

/* DECISION 2026-08-21 — figure typeface is not hardcoded.
   Default 'inherit' means an SVG picks up whatever the container sets: --font-prose on a
   poster sheet, Archivo inside a studio plate. Figures therefore match the surface they sit
   on with no coordination. Two escape hatches for the exceptions:
     CK.setFont('Fira Sans, sans-serif')   — project-wide override
     CK.series({..., font:'IBM Plex Mono'}) — per-call override
   Previously every SVG hardcoded Archivo, so every figure on a Lato sheet was off-family. */
let FONT='inherit';
function setFont(f){FONT=f||'inherit';return FONT}
function esc(s){return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;')}
function svg(w,h,body,font){return '<svg viewBox="0 0 '+w+' '+h+'" width="100%" height="100%" preserveAspectRatio="xMidYMid meet" font-family="'+(font||FONT)+'">'+body+'</svg>'}
function text(x,y,s,o){o=o||{};return '<text x="'+x+'" y="'+y+'" font-size="'+(o.size||LABEL_MM)+'" font-weight="'+(o.weight||500)+'" fill="'+(o.fill||'#17171B')+'" text-anchor="'+(o.anchor||'start')+'">'+esc(s)+'</text>'}
const fmtv=(v,o)=>(o&&o.fmt?o.fmt(v):v)+((o&&o.unit)||'');

/* ---------- categorical safety: computed against THIS theme's paper, never hardcoded ---------- */
function catSafety(paperHex){
  return PE.OKABE.map((hex,i)=>({hex:hex,i:i,safe:PE.ratio(hex,paperHex)>=3}));
}
function catPick(safety,n){
  // DECISION 2026-08-21: assign in SAFETY order, not array order.
  // PE.OKABE stays the published Okabe-Ito sequence (recognisable, and what --cat-N in
  // tokens.css names), but assignment prefers entries that clear the 3:1 floor against
  // THIS theme's paper. Walking the raw array handed out #F0E442 (1.32:1 on white,
  // invisible as a line) as the fifth series. Stable sort: safe first, original index
  // order within each group, so the choice is deterministic and re-runnable.
  // An unsafe entry is still used once the safe ones run out — callers dash it rather
  // than inventing a ninth colour.
  const ranked=safety.slice().sort((a,b)=>(b.safe-a.safe)||(a.i-b.i));
  const out=[];for(let i=0;i<n;i++)out.push(ranked[i%ranked.length]);return out;
}

/* ---------- greyscale as a DATA-INK diagnostic, not only a CVD sufficiency test ----------
   Desaturate every mark colour in the figure and re-measure separation.
   survives  → hue was redundant with position/shape/label. The colour is decorative ink:
               legitimate under Goldilocks, and free to spend.
   load-bearing → a distinction dies in grey. Hue is carrying data alone, which violates §6
               of the guidelines regardless of how much ink you decided to spend. */
function greyHex(hex){const g=PE.l2s(PE.lum(hex));return PE.rgb2hex([g,g,g])}
function greyDiagnostic(hexes,paperHex){
  const list=hexes.filter(Boolean),pairs=[];
  for(let i=0;i<list.length;i++)for(let j=i+1;j<list.length;j++){
    pairs.push({a:list[i],b:list[j],grey:PE.ratio(greyHex(list[i]),greyHex(list[j])),colour:PE.ratio(list[i],list[j])});
  }
  list.forEach(h=>pairs.push({a:h,b:paperHex,grey:PE.ratio(greyHex(h),greyHex(paperHex)),colour:PE.ratio(h,paperHex),ground:true}));
  const marks=pairs.filter(p=>!p.ground),ground=pairs.filter(p=>p.ground);
  const worst=marks.length?marks.reduce((m,p)=>p.grey<m.grey?p:m):null;
  const worstGround=ground.length?ground.reduce((m,p)=>p.grey<m.grey?p:m):null;
  const separates=!worst||worst.grey>=1.6;                 // house floor, same 1.6:1 PE.build warns at
  const visible=!worstGround||worstGround.grey>=3;         // graphics floor
  return{mode:separates?'decorative':'load-bearing',separates:separates,visible:visible,
    worst:worst,worstGround:worstGround,
    note:separates?'Hue is redundant here — every distinction survives desaturation, so the colour is decorative ink you are free to spend or cut.'
                   :'Hue is load-bearing: a distinction collapses in greyscale. Add position, shape, or a direct label before spending ink anywhere else.'};
}

/* ---------- scale reference: gridlines + tick values, per Lai & Morrison 2025 ---------- */
function niceStep(range,count){
  if(range<=0)return 1;
  const raw=range/count,mag=Math.pow(10,Math.floor(Math.log10(raw))),norm=raw/mag;
  return (norm<1.5?1:norm<3?2:norm<7?5:10)*mag;
}
function ticksFor(min,max,count){
  const step=niceStep(max-min,count||3),start=Math.ceil(min/step)*step,out=[];
  for(let v=start;v<=max+1e-6;v+=step)out.push(Math.round(v*1000)/1000);
  return out.length?out:[min,max];
}
function gridlinesY(sy,x0,x1,ticks,roles,fmt,d){
  d=d||DOSE.mid;const ts=LABEL_MM*d.tickScale;let body='';
  ticks.forEach(t=>{
    const y=sy(t);
    if(d.grid)body+='<line x1="'+x0+'" y1="'+y+'" x2="'+x1+'" y2="'+y+'" stroke="'+roles.rule.hex+'" stroke-width="'+STROKE.hair+'" stroke-opacity="'+d.gridOp+'"/>';
    body+=text(x0-1.6,y+ts*0.32,(fmt?fmt(t):t),{size:ts,weight:500,fill:roles['ink-soft'].hex,anchor:'end'});
  });
  return body;
}
function gridlinesX(sx,y0,y1,ticks,roles,fmt,d){
  d=d||DOSE.mid;const ts=LABEL_MM*d.tickScale;let body='';
  ticks.forEach(t=>{
    const x=sx(t);
    if(d.grid)body+='<line x1="'+x+'" y1="'+y0+'" x2="'+x+'" y2="'+y1+'" stroke="'+roles.rule.hex+'" stroke-width="'+STROKE.hair+'" stroke-opacity="'+d.gridOp+'"/>';
    body+=text(x,y1+ts+1.2,(fmt?fmt(t):t),{size:ts,weight:500,fill:roles['ink-soft'].hex,anchor:'middle'});
  });
  return body;
}
function deconflict(items){ // items: [{y,...}] sorted ascending, push apart to keep a minimum gap
  items.sort((a,b)=>a.y-b.y);
  for(let pass=0;pass<items.length;pass++)for(let i=1;i<items.length;i++){
    const gap=items[i].y-items[i-1].y;
    if(gap<GAP_MM){const d=(GAP_MM-gap)/2;items[i-1].y-=d;items[i].y+=d}
  }
  return items;
}
/* one short annotation sentence, rich dose only — the ink that buys attention */
function callout(x,y,s,roles,d,anchor){
  if(!d.callout||!s)return '';
  return text(x,y,s,{size:LABEL_MM*0.78,weight:700,fill:roles.accent.hex,anchor:anchor||'start'});
}

/* ---------- 1. ranked bar — one variable across categories, one accent event ----------
   v3: gains the value scale the kit's own header comment promised but never drew for bars,
   and at lean prints only the highlighted bar's number. */
function rankedBar(o){
  const d=dose(o),w=o.w||300,h=o.h||150,roles=o.roles,data=o.data.slice().sort((a,b)=>b.value-a.value);
  const padL=4,padR=30,padB=d.grid?12:2,axR=w-padR,max=Math.max.apply(null,data.map(x=>x.value))*1.08;
  const sx=v=>padL+(v/max)*(axR-padL);
  const rowH=(h-padB-4)/data.length,barH=Math.min(rowH*0.52,14);
  let body=d.grid?gridlinesX(sx,2,h-padB,ticksFor(0,max,d.ticks),roles,o.fmt,d):'';
  if(d.baseline==='data')body+='<line x1="'+padL+'" y1="'+(h-padB)+'" x2="'+(axR)+'" y2="'+(h-padB)+'" stroke="'+roles.rule.hex+'" stroke-width="'+STROKE.data+'"/>';
  data.forEach((x,i)=>{
    const y=2+rowH*i+rowH/2,bw=sx(x.value)-padL,hit=x.label===o.highlight;
    body+='<rect x="'+padL+'" y="'+(y-barH/2)+'" width="'+bw+'" height="'+barH+'" rx="0.6" fill="'+(hit?roles.accent.hex:roles['ink-soft'].hex)+'" fill-opacity="'+(hit?1:0.55)+'"/>';
    body+=text(padL,y-barH/2-1.3,x.label,{size:LABEL_MM,weight:600,fill:roles.ink.hex});
    if(hit||d.values==='all')
      body+=text(padL+bw+2.6,y+VALUE_MM*0.32,fmtv(x.value,o),{size:hit?VALUE_MM:LABEL_MM,weight:hit?800:500,fill:hit?roles.accent.hex:roles.ink.hex});
  });
  body+=callout(padL,h-padB-1.5,o.annotation,roles,d);
  return svg(w,h,body,o.font);
}

/* ---------- 2. series / trend — multi-series, Okabe-Ito, direct end labels, no legend ----------
   v3: the emphasised series gets its terminal VALUE printed under its name, and at rich a
   dashed leader to the axis. That number was previously unrecoverable from the figure. */
function series(o){
  const d=dose(o),w=o.w||300,h=o.h||150,roles=o.roles,xs=o.x,rows=o.data;
  const padL=d.grid?10:4,padT=d.callout&&o.annotation?11:6,padB=14,padR=54,plotW=w-padL-padR,plotH=h-padT-padB;
  const allV=rows.flatMap(r=>r.values),max=Math.max.apply(null,allV)*1.06,min=Math.min(0,Math.min.apply(null,allV));
  const sx=i=>padL+(i/(xs.length-1))*plotW, sy=v=>padT+plotH-((v-min)/(max-min))*plotH;
  const safety=catSafety(roles.paper.hex),cols=catPick(safety,rows.length);
  let body=gridlinesY(sy,padL,padL+plotW,ticksFor(min,max,d.ticks),roles,o.fmt,d);
  body+='<line x1="'+padL+'" y1="'+(padT+plotH)+'" x2="'+(padL+plotW)+'" y2="'+(padT+plotH)+'" stroke="'+roles.rule.hex+'" stroke-width="'+STROKE[d.baseline]+'"/>';
  xs.forEach((lb,i)=>body+=text(sx(i),h-2,lb,{size:LABEL_MM*(d.tickScale*1.03),weight:500,fill:roles['ink-soft'].hex,anchor:'middle'}));
  const labels=[];
  rows.forEach((r,ri)=>{
    const emph=r.name===o.emphasize, col=emph?roles.accent.hex:cols[ri].hex, unsafe=!emph&&!cols[ri].safe;
    const pts=r.values.map((v,i)=>sx(i)+','+sy(v)).join(' ');
    body+='<polyline points="'+pts+'" fill="none" stroke="'+col+'" stroke-width="'+(emph?STROKE.strong:STROKE.data)+'" stroke-linejoin="round" stroke-linecap="round"'+(unsafe?' stroke-dasharray="'+STROKE.data*2+' '+STROKE.data*1.4+'"':'')+'/>';
    const lastI=r.values.length-1;
    if(d.points)r.values.forEach((v,i)=>{if(i<lastI)body+='<circle cx="'+sx(i)+'" cy="'+sy(v)+'" r="'+(emph?1.5:1.15)+'" fill="'+col+'"/>'});
    if(d.endDots||emph)body+='<circle cx="'+sx(lastI)+'" cy="'+sy(r.values[lastI])+'" r="'+(emph?2.1:1.5)+'" fill="'+col+'"/>';
    if(emph&&d.leader)body+='<line x1="'+padL+'" y1="'+sy(r.values[lastI])+'" x2="'+sx(lastI)+'" y2="'+sy(r.values[lastI])+'" stroke="'+roles.accent.hex+'" stroke-width="'+STROKE.hair+'" stroke-dasharray="2.2 1.8"/>';
    labels.push({y:sy(r.values[lastI]),name:r.name,col:col,emph:emph,x:sx(lastI)+3.2,
      val:(emph||d.values==='all')?fmtv(r.values[lastI],o):null});
  });
  deconflict(labels).forEach(l=>{
    body+=text(l.x,l.y+1.4,l.name,{size:LABEL_MM*0.86,weight:l.emph?800:600,fill:l.emph?roles.accent.hex:roles.ink.hex});
    if(l.val!=null)body+=text(l.x,l.y+1.4+(l.emph?VALUE_MM*0.78:LABEL_MM*0.86),l.val,
      {size:l.emph?VALUE_MM*0.82:LABEL_MM*0.7,weight:l.emph?900:500,fill:l.emph?roles.accent.hex:roles['ink-soft'].hex});
  });
  body+=callout(padL,padT-3.5,o.annotation,roles,d);
  return svg(w,h,body,o.font);
}

/* ---------- 3. dot comparison / slope — before→after per category ----------
   v3: the highlighted row prints its own delta. */
function dotComparison(o){
  const d=dose(o),w=o.w||300,h=o.h||150,roles=o.roles,data=o.data;
  const padL=26,padR=d.values==='all'?34:26,padT=d.callout&&o.annotation?11:6,padB=d.grid?16:8;
  const plotW=w-padL-padR,rowH=(h-padT-padB)/data.length;
  const all=data.flatMap(x=>[x.before,x.after]),max=Math.max.apply(null,all)*1.08,min=Math.min(0,Math.min.apply(null,all));
  const sx=v=>padL+((v-min)/(max-min))*plotW;
  let body=d.grid?gridlinesX(sx,2,h-padB+3,ticksFor(min,max,d.ticks),roles,o.fmt,d):'';
  body+=text(padL,padT-1.5,o.fromLabel||'before',{size:LABEL_MM*0.8,weight:500,fill:roles['ink-soft'].hex})+
    text(padL+plotW,padT-1.5,o.toLabel||'after',{size:LABEL_MM*0.8,weight:500,fill:roles['ink-soft'].hex,anchor:'end'});
  data.forEach((x,i)=>{
    const y=padT+8+rowH*i,hit=x.label===o.highlight,col=hit?roles.accent.hex:roles['ink-soft'].hex;
    body+='<line x1="'+sx(x.before)+'" y1="'+y+'" x2="'+sx(x.after)+'" y2="'+y+'" stroke="'+col+'" stroke-width="'+(hit?STROKE.strong:STROKE.data)+'" stroke-linecap="round"'+(hit?'':' stroke-opacity="0.55"')+'/>';
    body+='<circle cx="'+sx(x.before)+'" cy="'+y+'" r="1.6" fill="'+roles.paper.hex+'" stroke="'+col+'" stroke-width="1.1"/>';
    body+='<circle cx="'+sx(x.after)+'" cy="'+y+'" r="'+(hit?2.3:1.8)+'" fill="'+col+'"/>';
    body+=text(padL-3,y+1.4,x.label,{size:LABEL_MM*0.86,weight:hit?800:600,fill:hit?roles.accent.hex:roles.ink.hex,anchor:'end'});
    if(hit||d.values==='all'){
      const dv=x.after-x.before,s=(dv>0?'+':'')+(o.fmt?o.fmt(dv):Math.round(dv*100)/100)+(o.unit||'');
      body+=text(Math.max(sx(x.before),sx(x.after))+3.2,y+(hit?VALUE_MM*0.3:LABEL_MM*0.3),s,
        {size:hit?VALUE_MM*0.8:LABEL_MM*0.7,weight:hit?900:500,fill:hit?roles.accent.hex:roles['ink-soft'].hex});
    }
  });
  body+=callout(padL,padT-6.5,o.annotation,roles,d);
  return svg(w,h,body,o.font);
}

/* ---------- 4. distribution — honest about spread ----------
   v3: form:'box' is the DEFAULT. The v2 strip (points + a mean bar, no box) is the
   Tufte-minimal boxplot the commentary warns about: less ink, less familiar, slower to read.
   'strip' keeps v2 behaviour for anyone who wants it; 'both' boxes the familiar frame and
   overlays the real points, which is the highest-ink and most honest of the three. */
function quantile(s,p){const i=(s.length-1)*p,lo=Math.floor(i),hi=Math.ceil(i);return lo===hi?s[lo]:s[lo]+(s[hi]-s[lo])*(i-lo)}
function boxStats(pts){
  const s=pts.slice().sort((a,b)=>a-b),q1=quantile(s,0.25),q2=quantile(s,0.5),q3=quantile(s,0.75),iqr=q3-q1;
  const inl=s.filter(v=>v>=q1-1.5*iqr&&v<=q3+1.5*iqr);
  return{q1:q1,q2:q2,q3:q3,lo:inl.length?inl[0]:s[0],hi:inl.length?inl[inl.length-1]:s[s.length-1],
    out:s.filter(v=>v<q1-1.5*iqr||v>q3+1.5*iqr),mean:s.reduce((a,b)=>a+b,0)/s.length,n:s.length};
}
function distribution(o){
  const d=dose(o),w=o.w||300,h=o.h||150,roles=o.roles,data=o.data;
  const form=o.form||'box',showPts=form==='strip'||form==='both'||(form==='box'&&d.points);
  const padL=d.grid?10:4,padT=d.callout&&o.annotation?11:6,padB=14,padR=4,plotW=w-padL-padR,plotH=h-padT-padB;
  const all=data.flatMap(x=>x.points),max=Math.max.apply(null,all)*1.08,min=Math.min.apply(null,all)*0.9;
  const gW=plotW/data.length,sy=v=>padT+plotH-((v-min)/(max-min))*plotH;
  let body=gridlinesY(sy,padL,padL+plotW,ticksFor(min,max,d.ticks),roles,o.fmt,d);
  data.forEach((x,gi)=>{
    const cx=padL+gW*gi+gW/2,hit=x.label===o.highlight,col=hit?roles.accent.hex:roles['ink-soft'].hex;
    const st=boxStats(x.points),bw=Math.min(gW*0.44,15);
    if(form!=='strip'){
      body+='<line x1="'+cx+'" y1="'+sy(st.hi)+'" x2="'+cx+'" y2="'+sy(st.q3)+'" stroke="'+col+'" stroke-width="'+STROKE.data+'"/>';
      body+='<line x1="'+cx+'" y1="'+sy(st.lo)+'" x2="'+cx+'" y2="'+sy(st.q1)+'" stroke="'+col+'" stroke-width="'+STROKE.data+'"/>';
      body+='<line x1="'+(cx-bw*0.32)+'" y1="'+sy(st.hi)+'" x2="'+(cx+bw*0.32)+'" y2="'+sy(st.hi)+'" stroke="'+col+'" stroke-width="'+STROKE.data+'"/>';
      body+='<line x1="'+(cx-bw*0.32)+'" y1="'+sy(st.lo)+'" x2="'+(cx+bw*0.32)+'" y2="'+sy(st.lo)+'" stroke="'+col+'" stroke-width="'+STROKE.data+'"/>';
      body+='<rect x="'+(cx-bw/2)+'" y="'+sy(st.q3)+'" width="'+bw+'" height="'+Math.max(sy(st.q1)-sy(st.q3),0.8)+'" fill="'+(hit?roles.accent.hex:roles.paper.hex)+'" fill-opacity="'+(hit?0.14:1)+'" stroke="'+col+'" stroke-width="'+STROKE.data+'"/>';
      body+='<line x1="'+(cx-bw/2)+'" y1="'+sy(st.q2)+'" x2="'+(cx+bw/2)+'" y2="'+sy(st.q2)+'" stroke="'+(hit?roles.accent.hex:roles.ink.hex)+'" stroke-width="'+STROKE.strong+'"/>';
      st.out.forEach(v=>body+='<circle cx="'+cx+'" cy="'+sy(v)+'" r="1.15" fill="none" stroke="'+col+'" stroke-width="0.7"/>');
    }
    if(showPts)x.points.forEach((v,i)=>{
      const jx=cx+((i%7)-3)*gW*(form==='strip'?0.055:0.038)+(form==='strip'?0:bw*0.72);
      body+='<circle cx="'+jx+'" cy="'+sy(v)+'" r="1.15" fill="'+col+'" fill-opacity="'+(hit?0.85:0.45)+'"/>';
    });
    if(form==='strip')body+='<line x1="'+(cx-gW*0.3)+'" y1="'+sy(st.mean)+'" x2="'+(cx+gW*0.3)+'" y2="'+sy(st.mean)+'" stroke="'+(hit?roles.accent.hex:roles.ink.hex)+'" stroke-width="'+STROKE.strong+'"/>';
    body+=text(cx,h-2,x.label,{size:LABEL_MM*0.86,weight:hit?800:600,fill:hit?roles.accent.hex:roles.ink.hex,anchor:'middle'});
    if(hit||d.values==='all')
      body+=text(cx,sy(st.hi)-2.4,fmtv(Math.round(st.q2*100)/100,o),
        {size:hit?VALUE_MM*0.78:LABEL_MM*0.68,weight:hit?900:500,fill:hit?roles.accent.hex:roles['ink-soft'].hex,anchor:'middle'});
  });
  body+=callout(padL,padT-3.5,o.annotation,roles,d);
  return svg(w,h,body,o.font);
}

/* ---------- claim graphics: the non-text 5-second encoding ---------- */
function claimProportion(o){
  const w=o.w||140,h=o.h||140,roles=o.roles,v=clamp(o.value,0,1),r=Math.min(w,h)/2-STROKE.strong*2.4,cx=w/2,cy=h/2,C=2*Math.PI*r;
  const big=Math.min(w,h)*0.30;
  let body='<circle cx="'+cx+'" cy="'+cy+'" r="'+r+'" fill="none" stroke="'+roles.rule.hex+'" stroke-width="'+STROKE.strong+'" stroke-opacity="0.5"/>';
  body+='<circle cx="'+cx+'" cy="'+cy+'" r="'+r+'" fill="none" stroke="'+roles.accent.hex+'" stroke-width="'+STROKE.strong+'" stroke-linecap="round" stroke-dasharray="'+(v*C)+' '+C+'" transform="rotate(-90 '+cx+' '+cy+')"/>';
  body+='<text x="'+cx+'" y="'+(cy+big*0.34)+'" font-size="'+big+'" font-weight="900" fill="'+roles.ink.hex+'" text-anchor="middle">'+esc(o.label||Math.round(v*100)+'%')+'</text>';
  return svg(w,h,body,o.font);
}
/* v3: an ISOTYPE alternative to the ring. A ring gauge is familiar but a poor proportion
   encoder — arc length read against a circle is the classic pie problem. A counted grid is
   equally familiar, countable, higher-ink, and (the commentary's actual argument) more
   memorable, because the reader does the counting. Squares only — still no illustration. */
function claimWaffle(o){
  const w=o.w||140,h=o.h||140,roles=o.roles,cols=o.cols||10,rows=o.rows||10;
  const total=o.total||cols*rows,filled=o.count!=null?o.count:Math.round(clamp(o.value,0,1)*total);
  const lab=String(o.label||(filled+' of '+total));
  const capH=Math.min(w,h)*0.325;
  const cell=Math.min((w-2)/cols,(h-2-capH)/rows),gap=cell*0.18,s=cell-gap;
  const x0=(w-(cols*cell-gap))/2,y0=capH;
  /* the numeral is the loudest mark in the graphic, so it is sized to FIT the space left of the
     right edge — a clipped 5-second number is worse than a smaller one */
  const big=Math.min(Math.min(w,h)*0.26,(w-x0-2)/(lab.length*0.64));
  let body='';
  for(let i=0;i<total;i++){
    const r=Math.floor(i/cols),c=i%cols,on=i<filled;
    body+='<rect x="'+(x0+c*cell)+'" y="'+(y0+r*cell)+'" width="'+s+'" height="'+s+'" rx="'+(s*0.14)+'" fill="'+(on?roles.accent.hex:roles.rule.hex)+'" fill-opacity="'+(on?1:0.3)+'"/>';
  }
  body+='<text x="'+x0+'" y="'+(capH-big*0.34)+'" font-size="'+big+'" font-weight="900" fill="'+roles.ink.hex+'">'+esc(lab)+'</text>';
  return svg(w,h,body,o.font);
}
function claimDelta(o){
  const d=dose(o),w=o.w||220,h=o.h||140,roles=o.roles,from=o.from,to=o.to,max=Math.max(from,to)*1.15;
  const bw=w*0.16,gap=w*0.30,x0=w*0.14,x1=x0+bw+gap,base=h-14,plotH=h-30;
  const h0=(from/max)*plotH,h1=(to/max)*plotH,big=h*0.24;
  let body='<rect x="'+x0+'" y="'+(base-h0)+'" width="'+bw+'" height="'+h0+'" fill="'+roles['ink-soft'].hex+'" fill-opacity="0.55"/>';
  body+='<rect x="'+x1+'" y="'+(base-h1)+'" width="'+bw+'" height="'+h1+'" fill="'+roles.accent.hex+'"/>';
  body+='<line x1="'+(x0+bw+4)+'" y1="'+(base-h0-3)+'" x2="'+(x1-6)+'" y2="'+(base-h1-3)+'" stroke="'+roles.ink.hex+'" stroke-width="'+STROKE.data+'"/>';
  const ang=Math.atan2((base-h1-3)-(base-h0-3),(x1-6)-(x0+bw+4));
  body+='<polygon points="0,-2.6 6.5,0 0,2.6" fill="'+roles.ink.hex+'" transform="translate('+(x1-6)+','+(base-h1-3)+') rotate('+(ang*180/Math.PI)+')"/>';
  body+=text(x0+bw/2,base+8,o.fromLabel||'before',{size:LABEL_MM*0.82,weight:500,fill:roles['ink-soft'].hex,anchor:'middle'});
  body+=text(x1+bw/2,base+8,o.toLabel||'after',{size:LABEL_MM*0.82,weight:500,fill:roles.ink.hex,anchor:'middle'});
  if(d.values==='all'){
    body+=text(x0+bw/2,base-h0-3.4,fmtv(from,o),{size:LABEL_MM*0.8,weight:600,fill:roles['ink-soft'].hex,anchor:'middle'});
  }
  /* clamp the multiplier off the top edge: at a tall `to` bar the label ran out of the viewBox */
  const ly=Math.max(base-h1-14,big*0.94);
  body+='<text x="'+(x1+bw/2)+'" y="'+ly+'" font-size="'+big+'" font-weight="900" fill="'+roles.accent.hex+'" text-anchor="middle">'+esc(o.label||(to/from).toFixed(1)+'×')+'</text>';
  return svg(w,h,body,o.font);
}

/* ---------- the Goldilocks test, runnable ----------
   Render one dataset at all three doses. The method the commentary proposes is comparison —
   so make comparison a function call rather than an instruction in a guidelines document. */
function goldilocks(form,o){
  const fn=typeof form==='function'?form:FORMS[form];
  return DOSE_KEYS.map(k=>({ink:k,dose:DOSE[k],svg:fn(Object.assign({},o,{ink:k,scale:undefined}))}));
}
/* dose implied by a dwell layer, for callers that only know which layer they are drawing into */
function doseForDwell(layer){return DWELL[layer]||'mid'}

/* ---------- raster minimum-ppi check ---------- */
function ppiCheck(pxW,pxH,mmW,mmH,floor){
  const ppiW=pxW/(mmW/25.4),ppiH=pxH/(mmH/25.4),eff=Math.min(ppiW,ppiH);
  return{ppi:eff,pass:eff>=floor,needPxW:Math.ceil((mmW/25.4)*floor),needPxH:Math.ceil((mmH/25.4)*floor)};
}

const FORMS={rankedBar:rankedBar,series:series,dotComparison:dotComparison,distribution:distribution};
window.CK={setFont:setFont,LABEL_MM:LABEL_MM,VALUE_MM:VALUE_MM,STROKE:STROKE,DOSE:DOSE,DOSE_KEYS:DOSE_KEYS,DWELL:DWELL,FORMS:FORMS,
  catSafety:catSafety,catPick:catPick,greyHex:greyHex,greyDiagnostic:greyDiagnostic,boxStats:boxStats,
  rankedBar:rankedBar,series:series,dotComparison:dotComparison,distribution:distribution,
  claimProportion:claimProportion,claimWaffle:claimWaffle,claimDelta:claimDelta,
  goldilocks:goldilocks,doseForDwell:doseForDwell,ppiCheck:ppiCheck};
})();
