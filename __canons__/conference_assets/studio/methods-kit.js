/* methods-kit.js — v3 (Goldilocks ink). Drop-in replacement for studio/methods-kit.js.
   A protocol drawn as an attrition-flow diagram: ribbon width IS enrollment n at each stage.
   Closed set of five marks + node/connector. Depends on PE. Same poster-distance floors.

   WHAT CHANGED IN v3. Warrant [house].
   1. THE INTERMEDIATE n IS NOW READABLE.  v2 printed an nBadge only at each arm's terminus, so
      every stage in between was encoded SOLELY as sqrt-scaled ribbon width — an unfamiliar
      magnitude channel with no redundant label. Under Lai & Morrison's argument this is exactly
      the wrong economy: the label is "unnecessary ink" that makes the encoding legible.
      Ribbon width is still the shape of the story; the numbers are now recoverable from it.
   2. INK IS A DIAL: ink:'lean'|'mid'|'rich', or dwell:'5s'|'1min'|'5min'.
      A methods figure lives in the 5-minute layer, so `lean` here means lean-in-decoration but
      fully labelled — accuracy over engagement. Defaults to 'mid'.
   3. STAGE NAMES ARE DRAWN, not implied.  v2 only labelled a stage where an arm deviated.
   4. THE ATTRITION IS STATED.  At rich, each arm's total loss is printed once, which is the
      number a reviewer at the 5-minute layer is actually looking for. */
(function(){
/* STROKE.hair (0.35mm) is a CHART-INTERNAL hairline and is deliberately finer than the
   sheet's --rule-weight (0.6mm). DECISION 2026-08-21: keep both. A gridline inside a figure
   and a rule dividing the sheet are different jobs; earlier comments wrongly claimed they
   were the same value. data = 4x hair so a line survives a 3m glance. */
const LABEL_MM=7.06,STROKE={hair:0.35,data:1.4,strong:2.4};
const MAXHW=9,MINHW=1.6;
const DOSE={
  lean:{stageN:'emph',stageNames:false,attrition:false,timelineTicks:false,params:false},
  mid: {stageN:'all', stageNames:true, attrition:false,timelineTicks:true, params:true},
  rich:{stageN:'all', stageNames:true, attrition:true, timelineTicks:true, params:true}
};
const DWELL={'5s':'lean','1min':'mid','5min':'rich'};   // inverted vs charts: the methods figure
// rewards MORE labelling the longer someone reads it, and less when it is only glanced at.
function dose(o){const k=(o&&(o.ink||DWELL[o.dwell]))||'mid';return Object.assign({key:k},DOSE[k]||DOSE.mid)}

function esc(s){return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;')}
let FONT='inherit';
function setFont(f){FONT=f||'inherit';return FONT}
function svg(w,h,body,font){return '<svg viewBox="0 0 '+w+' '+h+'" width="100%" height="100%" preserveAspectRatio="xMidYMid meet" font-family="'+(font||FONT)+'">'+body+'</svg>'}
function text(x,y,s,o){o=o||{};return '<text x="'+x+'" y="'+y+'" font-size="'+(o.size||LABEL_MM)+'" font-weight="'+(o.weight||500)+'" fill="'+(o.fill||'#17171B')+'" text-anchor="'+(o.anchor||'start')+'">'+esc(s)+'</text>'}
function hw(n,nMax){return MINHW+(MAXHW-MINHW)*Math.sqrt(Math.max(n,0)/nMax)}

/* 1. ribbon — a flowing path whose width at each point is a real headcount, not styling */
function ribbonPath(pts){
  let top='M '+pts[0].x+' '+(pts[0].y-pts[0].hw);
  for(let i=1;i<pts.length;i++){const a=pts[i-1],b=pts[i],mx=(a.x+b.x)/2;
    top+=' C '+mx+' '+(a.y-a.hw)+' '+mx+' '+(b.y-b.hw)+' '+b.x+' '+(b.y-b.hw)}
  let bot='L '+pts[pts.length-1].x+' '+(pts[pts.length-1].y+pts[pts.length-1].hw);
  for(let i=pts.length-1;i>0;i--){const a=pts[i],b=pts[i-1],mx=(a.x+b.x)/2;
    bot+=' C '+mx+' '+(a.y+a.hw)+' '+mx+' '+(b.y+b.hw)+' '+b.x+' '+(b.y+b.hw)}
  return top+' '+bot+' Z';
}
function ribbon(pts,roles,o){
  o=o||{};const col=o.emphasis?roles.accent.hex:roles['ink-soft'].hex;
  return '<path d="'+ribbonPath(pts)+'" fill="'+col+'" fill-opacity="'+(o.emphasis?0.94:0.42)+'"/>';
}
/* 2. stage tick — marks one named step by crossing the ribbon */
function stageTick(x,y,halfWidth,label,roles,o){
  o=o||{};const col=o.emphasis?roles.accent.hex:roles.ink.hex;
  let g='<line x1="'+x+'" y1="'+(y-halfWidth-2.4)+'" x2="'+x+'" y2="'+(y+halfWidth+2.4)+'" stroke="'+col+'" stroke-width="'+(o.emphasis?STROKE.strong*0.7:STROKE.hair)+'"/>';
  g+=text(x,y-halfWidth-4.4,label,{size:LABEL_MM*0.8,weight:o.emphasis?800:600,fill:col,anchor:'middle'});
  return g;
}
/* 3. direction chevron */
function chevron(x,y,roles,o){
  o=o||{};const col=o.emphasis?roles.accent.hex:roles.ink.hex,s=3.2;
  return '<polygon points="'+(-s*0.5)+',-'+s+' '+s*0.6+',0 '+(-s*0.5)+','+s+'" fill="'+col+'" transform="translate('+x+','+y+')"/>';
}
/* 4. n-badge — the magnitude a ribbon terminates in */
function nBadge(x,y,label,roles,o){
  o=o||{};const w=String(label).length*3.5+7,h=8.6,col=o.emphasis?roles.accent.hex:roles.ink.hex;
  let g='<rect x="'+x+'" y="'+(y-h/2)+'" width="'+w+'" height="'+h+'" rx="'+h/2+'" fill="'+col+'"/>';
  g+=text(x+w/2,y+LABEL_MM*0.27,label,{size:LABEL_MM*0.78,weight:700,fill:roles.paper.hex,anchor:'middle'});
  return{svg:g,w:w};
}
/* 4b. v3 — the intermediate stage count, set INSIDE the ribbon where it is wide enough to hold
   the glyph and immediately under it where it is not. This is the label that makes a
   sqrt-width encoding readable instead of merely suggestive. */
function stageN(x,y,halfWidth,label,roles,o){
  o=o||{};const size=LABEL_MM*0.72,inside=halfWidth>=size*0.62;
  const col=inside?(o.emphasis?roles.paper.hex:roles.paper.hex):(o.emphasis?roles.accent.hex:roles['ink-soft'].hex);
  const y2=inside?y+size*0.34:y+halfWidth+size*0.98;
  return text(x,y2,label,{size:size,weight:700,fill:col,anchor:'middle'});
}
/* 5. timeline */
function timeline(x,y,w,ticks,roles){
  let g='<line x1="'+x+'" y1="'+y+'" x2="'+(x+w)+'" y2="'+y+'" stroke="'+roles.rule.hex+'" stroke-width="'+STROKE.hair+'"/>';
  ticks.forEach(t=>{const tx=x+t.at*w;
    g+='<line x1="'+tx+'" y1="'+(y-2)+'" x2="'+tx+'" y2="'+(y+2)+'" stroke="'+roles.rule.hex+'" stroke-width="'+STROKE.hair+'"/>';
    g+=text(tx,y+7,t.label,{size:LABEL_MM*0.72,weight:500,fill:roles['ink-soft'].hex,anchor:'middle'})});
  return g;
}

/* composition: one shared trunk fans into named arms; ribbon width is n at every stage */
function funnel(o){
  const d=dose(o),w=o.w||620,h=o.h||150,roles=o.roles,arms=o.arms,trunk=o.trunk;
  const padL=8,padR=42,usableW=w-padL-padR,armsN=arms.length;
  const splitX=padL+usableW*0.2,divX=splitX+usableW*0.09;
  const stageCount=arms[0].stages.length,stageXs=arms[0].stages.map((s,i)=>divX+(w-padR-divX)*(stageCount===1?0:i/(stageCount-1)));
  const nMax=Math.max(trunk.n,...arms.flatMap(a=>a.n));
  const topPad=d.stageNames?9:0;
  const trunkY=Math.max(h/2,h*0.42)+topPad*0.4,rowGap=Math.min(30,(h-70-topPad)/Math.max(armsN-1,1));
  const branchY=arms.map((a,i)=>trunkY+(i-(armsN-1)/2)*rowGap);

  let body='';
  if(o.ticks&&d.timelineTicks)body+=timeline(divX,h-16,w-padR-divX,o.ticks,roles);
  /* v3: the stage vocabulary, once, along the top — not repeated per arm and not left implicit */
  if(d.stageNames)arms[0].stages.forEach((s,i)=>{
    body+=text(stageXs[i],7.4,s,{size:LABEL_MM*0.68,weight:600,fill:roles['ink-soft'].hex,anchor:i===0?'start':(i===stageCount-1?'end':'middle')});
  });
  body+=ribbon([{x:padL,y:trunkY,hw:hw(trunk.n,nMax)},{x:splitX,y:trunkY,hw:hw(trunk.n,nMax)}],roles,{});
  body+=text(padL,trunkY-hw(trunk.n,nMax)-4,trunk.label,{size:LABEL_MM*0.86,weight:700,fill:roles.ink.hex});
  body+=stageN(padL+(splitX-padL)/2,trunkY,hw(trunk.n,nMax),(trunk.unit?trunk.n+' '+trunk.unit:'n='+trunk.n),roles,{});

  arms.forEach((a,i)=>{
    const pts=[{x:splitX,y:trunkY,hw:hw(a.n[0],nMax)},{x:divX,y:branchY[i],hw:hw(a.n[0],nMax)}]
      .concat(stageXs.slice(1).map((x,k)=>({x:x,y:branchY[i],hw:hw(a.n[k+1],nMax)})));
    body+=ribbon(pts,roles,{emphasis:a.emphasis});
    body+=text(divX,branchY[i]-hw(a.n[0],nMax)-4,a.label,{size:LABEL_MM*0.86,weight:a.emphasis?800:700,fill:a.emphasis?roles.accent.hex:roles.ink.hex});
    /* v3: every intermediate stage count, not just the terminus */
    const last=stageXs.length-1;
    stageXs.forEach((x,k)=>{
      if(k===last)return;                                        // terminus keeps its badge
      const show=d.stageN==='all'||(d.stageN==='emph'&&(a.emphasis||k===a.deviateAt));
      if(!show)return;
      const nk=a.n[k];if(nk==null)return;
      /* keep the count clear of the deviation tick, which crosses the ribbon at the same x */
      const xo=k===0?(stageXs[1]-x)*0.34:(k===a.deviateAt?-5.4:0);
      body+=stageN(x+xo,branchY[i],hw(nk,nMax),String(nk),roles,{emphasis:a.emphasis});
    });
    if(typeof a.deviateAt==='number'){
      const x=stageXs[a.deviateAt];
      body+=stageTick(x,branchY[i],hw(a.n[a.deviateAt],nMax),a.deviateLabel||a.stages[a.deviateAt],roles,{emphasis:true});
    }
    const tipX=stageXs[last],tipN=a.n[a.n.length-1];
    body+=chevron(tipX+4.5,branchY[i],roles,{emphasis:a.emphasis});
    const b=nBadge(tipX+9,branchY[i],(a.unit?tipN+' '+a.unit:'n='+tipN),roles,{emphasis:a.emphasis});
    body+=b.svg;
    /* v3: state the attrition rather than leaving it to be inferred from taper */
    if(d.attrition&&a.n.length>1&&a.n[0]>0){
      const lost=a.n[0]-tipN,pct=Math.round((lost/a.n[0])*100);
      body+=text(tipX+9,branchY[i]+8.2,'−'+lost+' ('+pct+'%)',
        {size:LABEL_MM*0.64,weight:600,fill:a.emphasis?roles.accent.hex:roles['ink-soft'].hex});
    }
  });
  return svg(w,h,body,o.font);
}

/* 6. node + connector — plain process step for apparatus/pipeline/block diagrams.
   shape carries meaning: rect=process, diamond=decision, circle=state/actor/terminus,
   cylinder=data store. */
function node(x,y,w,h,label,roles,o){
  o=o||{};const hit=!!o.emphasis,stroke=hit?roles.accent.hex:roles.rule.hex,sw=hit?STROKE.strong:0.6,fill=roles.paper.hex,shape=o.shape||'rect';
  let g='';
  if(shape==='diamond'){const cx=x+w/2,cy=y+h/2;g='<polygon points="'+cx+','+y+' '+(x+w)+','+cy+' '+cx+','+(y+h)+' '+x+','+cy+'" fill="'+fill+'" stroke="'+stroke+'" stroke-width="'+sw+'"/>'}
  else if(shape==='circle'){const cx=x+w/2,cy=y+h/2,rad=Math.min(w,h)/2;g='<circle cx="'+cx+'" cy="'+cy+'" r="'+rad+'" fill="'+fill+'" stroke="'+stroke+'" stroke-width="'+sw+'"/>'}
  else if(shape==='cylinder'){const eh=h*0.16;
    g='<path d="M '+x+' '+(y+eh)+' L '+x+' '+(y+h-eh)+' A '+(w/2)+' '+eh+' 0 0 0 '+(x+w)+' '+(y+h-eh)+' L '+(x+w)+' '+(y+eh)+' A '+(w/2)+' '+eh+' 0 0 0 '+x+' '+(y+eh)+' Z" fill="'+fill+'" stroke="'+stroke+'" stroke-width="'+sw+'"/>'+
      '<path d="M '+x+' '+(y+eh)+' A '+(w/2)+' '+eh+' 0 0 0 '+(x+w)+' '+(y+eh)+'" fill="none" stroke="'+stroke+'" stroke-width="'+sw+'"/>'}
  else{g='<rect x="'+x+'" y="'+y+'" width="'+w+'" height="'+h+'" rx="1.4" fill="'+fill+'" stroke="'+stroke+'" stroke-width="'+sw+'"/>'}
  const labelY=y+h/2+(o.param?-1.6:0)+LABEL_MM*0.3;
  g+=text(x+w/2,labelY,label,{size:LABEL_MM*0.82,weight:hit?800:600,fill:hit?roles.accent.hex:roles.ink.hex,anchor:'middle'});
  if(o.param)g+=text(x+w/2,y+h/2+LABEL_MM*0.95,o.param,{size:LABEL_MM*0.64,weight:500,fill:roles['ink-soft'].hex,anchor:'middle'});
  return g;
}
function connector(x1,y1,x2,y2,roles,o){
  o=o||{};const col=o.emphasis?roles.accent.hex:roles['ink-soft'].hex;
  const dash=o.style==='dashed'?' stroke-dasharray="3.2 2.2"':o.style==='dotted'?' stroke-dasharray="0.5 2.1" stroke-linecap="round"':'';
  let g='<line x1="'+x1+'" y1="'+y1+'" x2="'+(x2-3.4)+'" y2="'+y2+'" stroke="'+col+'" stroke-width="1.3"'+dash+'/>';
  if(o.arrow!=='none')g+=chevron(x2-1.4,y2,roles,o);
  if(o.label)g+=text((x1+x2)/2,y1-3.4,o.label,{size:LABEL_MM*0.66,weight:500,fill:roles['ink-soft'].hex,anchor:'middle'});
  return g;
}
/* composition: a linear (optionally one-branch) sequence of nodes — no width-as-data */
function sequence(o){
  const d=dose(o),w=o.w||560,h=o.h||100,roles=o.roles,steps=o.steps,n=steps.length;
  const padL=6,padR=6,gap=w*0.045,boxW=(w-padL-padR-gap*(n-1))/n,boxH=Math.min(h*0.46,30),y=h/2-boxH/2;
  let body='',cx=padL;
  steps.forEach((s,i)=>{
    if(i>0)body+=connector(cx-gap,h/2,cx,h/2,roles,{emphasis:s.emphasis||steps[i-1].emphasis,style:s.link,label:d.params?s.edge:null});
    body+=node(cx,y,boxW,boxH,s.label,roles,{emphasis:s.emphasis,param:d.params?s.param:null,shape:s.shape});
    cx+=boxW+gap;
  });
  return svg(w,h,body,o.font);
}

window.MK={setFont:setFont,DOSE:DOSE,DWELL:DWELL,hw:hw,ribbon:ribbon,ribbonPath:ribbonPath,stageTick:stageTick,stageN:stageN,
  chevron:chevron,nBadge:nBadge,timeline:timeline,funnel:funnel,node:node,connector:connector,sequence:sequence};
})();
