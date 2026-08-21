/* diagram-grammars.js — LOW-FIDELITY sketches of six diagram structures that are not
   directed process flow. Each function is intentionally simpler than chart-kit/methods-kit:
   this file exists to let the user pick a direction, not to ship as a closed kit yet.
   Depends on PE for roles. SVG in mm-ish user units. */
(function(){
/* HAIR (0.35mm) is the chart-internal hairline, deliberately finer than the sheet's
   --rule-weight (0.6mm). See methods-kit.js for the rationale. */
const LABEL_MM=7.06,HAIR=0.35,DATA=1.4,STRONG=2.4;
function esc(s){return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;')}
let FONT='inherit';
function setFont(f){FONT=f||'inherit';return FONT}
function svg(w,h,body,font){return '<svg viewBox="0 0 '+w+' '+h+'" width="100%" height="100%" preserveAspectRatio="xMidYMid meet" font-family="'+(font||FONT)+'">'+body+'</svg>'}
function text(x,y,s,o){o=o||{};return '<text x="'+x+'" y="'+y+'" font-size="'+(o.size||LABEL_MM*0.8)+'" font-weight="'+(o.weight||500)+'" fill="'+(o.fill||'#17171B')+'" text-anchor="'+(o.anchor||'start')+'">'+esc(s)+'</text>'}
function chevron(x,y,ang,roles,emph){const s=2.6,col=emph?roles.accent.hex:roles.ink.hex;
  return '<polygon points="'+(-s*0.5)+',-'+s+' '+(s*0.6)+',0 '+(-s*0.5)+','+s+'" fill="'+col+'" transform="translate('+x+','+y+') rotate('+ang+')"/>'}
const R=(a,b)=>Math.round(a+Math.random()*(b-a));
const PICK=arr=>arr[R(0,arr.length-1)];

/* 1. actor / lifeline sequence diagram — who messages whom, over time */
function sequenceDiagram(roles,o){
  const w=o.w||420,h=o.h||220,actors=o.actors,msgs=o.messages;
  const padT=16,padB=8,ax=actors.map((a,i)=>16+(w-32)*(actors.length===1?0:i/(actors.length-1)));
  let body='';
  actors.forEach((a,i)=>{
    body+='<rect x="'+(ax[i]-22)+'" y="2" width="44" height="13" rx="1.4" fill="'+roles.paper.hex+'" stroke="'+roles.rule.hex+'" stroke-width="0.7"/>';
    body+=text(ax[i],10.5,a,{size:LABEL_MM*0.72,weight:700,fill:roles.ink.hex,anchor:'middle'});
    body+='<line x1="'+ax[i]+'" y1="16" x2="'+ax[i]+'" y2="'+(h-padB)+'" stroke="'+roles.rule.hex+'" stroke-width="0.6" stroke-dasharray="0.4 2.2"/>';
  });
  const rowH=(h-padT-padB-4)/msgs.length;
  msgs.forEach((m,i)=>{
    const y=padT+8+rowH*i,x1=ax[m.from],x2=ax[m.to],col=m.emphasis?roles.accent.hex:roles['ink-soft'].hex;
    body+='<line x1="'+x1+'" y1="'+y+'" x2="'+(x2+(x2>x1?-3:3))+'" y2="'+y+'" stroke="'+col+'" stroke-width="'+(m.emphasis?STRONG*0.6:DATA)+'"/>';
    body+=chevron(x2,y,x2>x1?90:-90,roles,m.emphasis);
    body+=text((x1+x2)/2,y-2.2,m.label,{size:LABEL_MM*0.62,weight:m.emphasis?800:500,fill:m.emphasis?roles.accent.hex:roles['ink-soft'].hex,anchor:'middle'});
  });
  return svg(w,h,body);
}
function genSequence(){
  const actors=['Subject','Instrument','Analyst'];
  const verbs=['request','calibrate','sample','record','flag anomaly','report'];
  const n=R(4,5),msgs=[];let cur=0;
  for(let i=0;i<n;i++){let to;do{to=R(0,2)}while(to===cur);msgs.push({from:cur,to:to,label:PICK(verbs),emphasis:i===n-2});cur=to}
  return{actors:actors,messages:msgs};
}

/* 2. Gantt / project timeline — phase durations and overlap */
function gantt(roles,o){
  const w=o.w||420,h=o.h||180,tasks=o.tasks,padL=6,padR=10,padT=8,padB=16,rowH=(h-padT-padB)/tasks.length;
  const max=Math.max.apply(null,tasks.map(t=>t.end)),plotW=w-padL-padR;
  const sx=v=>padL+(v/max)*plotW;
  let body='<line x1="'+padL+'" y1="'+(h-padB)+'" x2="'+(padL+plotW)+'" y2="'+(h-padB)+'" stroke="'+roles.rule.hex+'" stroke-width="'+HAIR+'"/>';
  for(let m=0;m<=max;m+=Math.ceil(max/6)){const x=sx(m);body+='<line x1="'+x+'" y1="'+(h-padB)+'" x2="'+x+'" y2="'+(h-padB+2)+'" stroke="'+roles.rule.hex+'" stroke-width="'+HAIR+'"/>'+text(x,h-padB+8,'wk '+m,{size:LABEL_MM*0.58,weight:500,fill:roles['ink-soft'].hex,anchor:'middle'})}
  tasks.forEach((t,i)=>{
    const y=padT+rowH*i+rowH*0.22,bh=rowH*0.5,col=t.emphasis?roles.accent.hex:roles['ink-soft'].hex;
    body+=text(padL,y-1.6,t.label,{size:LABEL_MM*0.66,weight:t.emphasis?800:600,fill:t.emphasis?roles.accent.hex:roles.ink.hex});
    body+='<rect x="'+sx(t.start)+'" y="'+y+'" width="'+(sx(t.end)-sx(t.start))+'" height="'+bh+'" rx="1" fill="'+col+'" fill-opacity="'+(t.emphasis?0.95:0.5)+'"/>';
  });
  return svg(w,h,body);
}
function genGantt(){
  const names=['Recruitment','Baseline visits','Intervention','Follow-up','Analysis'];
  let t=0;const tasks=names.map((n,i)=>{const start=Math.max(0,t-R(0,2)),dur=R(3,7);t=start+dur;return{label:n,start:start,end:start+dur,emphasis:i===2}});
  return tasks;
}

/* 3. nested component / architecture diagram — containment, not flow */
function component(roles,o){
  const w=o.w||420,h=o.h||220,root=o.root;
  let body='<rect x="4" y="4" width="'+(w-8)+'" height="'+(h-8)+'" rx="2" fill="none" stroke="'+roles.rule.hex+'" stroke-width="'+DATA+'"/>';
  body+=text(10,15,root.label,{size:LABEL_MM*0.78,weight:700,fill:roles.ink.hex});
  const inner=root.children,gap=8,padT=22,innerW=(w-16-gap*(inner.length-1))/inner.length,innerH=h-padT-14;
  inner.forEach((c,i)=>{
    const x=8+i*(innerW+gap),y=padT,col=c.emphasis?roles.accent.hex:roles.rule.hex;
    body+='<rect x="'+x+'" y="'+y+'" width="'+innerW+'" height="'+innerH+'" rx="1.6" fill="'+roles.paper.hex+'" stroke="'+col+'" stroke-width="'+(c.emphasis?STRONG*0.6:0.7)+'"/>';
    body+=text(x+innerW/2,y+14,c.label,{size:LABEL_MM*0.72,weight:c.emphasis?800:600,fill:c.emphasis?roles.accent.hex:roles.ink.hex,anchor:'middle'});
    if(c.children)c.children.forEach((g,j)=>{
      const gw=innerW-12,gx=x+6,gy=y+22+j*20;
      body+='<rect x="'+gx+'" y="'+gy+'" width="'+gw+'" height="14" rx="1.2" fill="'+roles.field.hex+'" stroke="'+roles.rule.hex+'" stroke-width="0.5"/>';
      body+=text(gx+gw/2,gy+9.5,g,{size:LABEL_MM*0.6,weight:500,fill:roles['ink-soft'].hex,anchor:'middle'});
    });
  });
  if(inner.length>1){const y=padT+innerH*0.5,x1=8+innerW,x2=8+innerW+gap;
    body+='<line x1="'+x1+'" y1="'+y+'" x2="'+x2+'" y2="'+y+'" stroke="'+roles.ink.hex+'" stroke-width="0.9"/>'+
      '<circle cx="'+x1+'" cy="'+y+'" r="1.4" fill="'+roles.paper.hex+'" stroke="'+roles.ink.hex+'" stroke-width="0.9"/>';
  }
  return svg(w,h,body);
}
function genComponent(){
  const layouts=[
    {label:'Instrument control system',children:[{label:'Acquisition module',emphasis:true,children:['Trigger','ADC driver']},{label:'Storage module',children:['Buffer','Writer']}]},
    {label:'Software architecture',children:[{label:'Frontend',children:['UI','State store']},{label:'Backend',emphasis:true,children:['API','Scheduler']}]}
  ];
  return PICK(layouts);
}

/* 4. state machine — states, transitions, conditions */
function stateMachine(roles,o){
  const w=o.w||420,h=o.h||200,states=o.states,rad=16;
  let body='';
  states.forEach(s=>{
    if(s.start)body+='<line x1="'+(s.x-rad-12)+'" y1="'+s.y+'" x2="'+(s.x-rad-2)+'" y2="'+s.y+'" stroke="'+roles.ink.hex+'" stroke-width="1.2"/>'+chevron(s.x-rad,s.y,90,roles,false);
    const col=s.emphasis?roles.accent.hex:roles.rule.hex;
    body+='<circle cx="'+s.x+'" cy="'+s.y+'" r="'+rad+'" fill="'+roles.paper.hex+'" stroke="'+col+'" stroke-width="'+(s.emphasis?STRONG*0.6:1)+'"/>';
    if(s.terminal)body+='<circle cx="'+s.x+'" cy="'+s.y+'" r="'+(rad-3)+'" fill="none" stroke="'+col+'" stroke-width="0.8"/>';
    body+=text(s.x,s.y+LABEL_MM*0.26,s.label,{size:LABEL_MM*0.66,weight:s.emphasis?800:600,fill:s.emphasis?roles.accent.hex:roles.ink.hex,anchor:'middle'});
  });
  (o.edges||[]).forEach(e=>{
    const a=states[e.from],b=states[e.to];
    if(a===b){const cx=a.x,cy=a.y-rad-14;
      body+='<path d="M '+(a.x-8)+' '+(a.y-rad+2)+' Q '+cx+' '+cy+' '+(a.x+8)+' '+(a.y-rad+2)+'" fill="none" stroke="'+roles['ink-soft'].hex+'" stroke-width="'+DATA+'"/>'+chevron(a.x+8,a.y-rad+2,150,roles,false);
      body+=text(cx,cy+3,e.label,{size:LABEL_MM*0.56,weight:500,fill:roles['ink-soft'].hex,anchor:'middle'});
    } else {
      const dx=b.x-a.x,dy=b.y-a.y,dist=Math.hypot(dx,dy),ux=dx/dist,uy=dy/dist;
      const x1=a.x+ux*rad,y1=a.y+uy*rad,x2=b.x-ux*(rad+2.4),y2=b.y-uy*(rad+2.4);
      const col=e.emphasis?roles.accent.hex:roles['ink-soft'].hex;
      body+='<line x1="'+x1+'" y1="'+y1+'" x2="'+x2+'" y2="'+y2+'" stroke="'+col+'" stroke-width="'+(e.emphasis?STRONG*0.6:DATA)+'"/>';
      body+=chevron(x2,y2,Math.atan2(dy,dx)*180/Math.PI,roles,e.emphasis);
      body+=text((x1+x2)/2,(y1+y2)/2-3,e.label,{size:LABEL_MM*0.58,weight:e.emphasis?700:500,fill:e.emphasis?roles.accent.hex:roles['ink-soft'].hex,anchor:'middle'});
    }
  });
  return svg(w,h,body);
}
function genStateMachine(){
  const states=[{label:'Idle',x:40,y:100,start:true},{label:'Armed',x:150,y:50},{label:'Sampling',x:260,y:100,emphasis:true},{label:'Fault',x:150,y:160},{label:'Done',x:370,y:100,terminal:true}];
  const edges=[{from:0,to:1,label:'trigger'},{from:1,to:2,label:'threshold met',emphasis:true},{from:2,to:2,label:'retry'},{from:2,to:4,label:'complete'},{from:2,to:3,label:'timeout'},{from:3,to:0,label:'reset'}];
  return{states:states,edges:edges};
}

/* 5. factorial / matrix experimental design — condition × outcome */
function matrix(roles,o){
  const w=o.w||360,h=o.h||220,rows=o.rows,cols=o.cols,cells=o.cells;
  const padL=64,padT=26,cw=(w-padL-6)/cols.length,ch=(h-padT-6)/rows.length;
  let body=text(padL+((w-padL)/2),13,o.title||'',{size:LABEL_MM*0.72,weight:700,fill:roles.ink.hex,anchor:'middle'});
  cols.forEach((c,j)=>body+=text(padL+cw*j+cw/2,padT-4,c,{size:LABEL_MM*0.6,weight:600,fill:roles['ink-soft'].hex,anchor:'middle'}));
  rows.forEach((r,i)=>body+=text(padL-6,padT+ch*i+ch/2+3,r,{size:LABEL_MM*0.6,weight:600,fill:roles['ink-soft'].hex,anchor:'end'}));
  rows.forEach((r,i)=>cols.forEach((c,j)=>{
    const cell=cells[i][j],x=padL+cw*j,y=padT+ch*i,hit=cell.emphasis;
    body+='<rect x="'+x+'" y="'+y+'" width="'+cw+'" height="'+ch+'" fill="'+(hit?roles.accent.hex:roles.paper.hex)+'" fill-opacity="'+(hit?0.16:1)+'" stroke="'+(hit?roles.accent.hex:roles.rule.hex)+'" stroke-width="'+(hit?STRONG*0.5:0.6)+'"/>';
    body+=text(x+cw/2,y+ch/2+LABEL_MM*0.24,cell.label,{size:LABEL_MM*0.7,weight:hit?800:600,fill:hit?roles.accent.hex:roles.ink.hex,anchor:'middle'});
  }));
  return svg(w,h,body);
}
function genMatrix(){
  const rows=['Low dose','High dose'],cols=['Placebo','Active'];
  const cells=rows.map((r,i)=>cols.map((c,j)=>({label:'n='+R(18,34),emphasis:i===1&&j===1})));
  return{title:'2×2 design',rows:rows,cols:cols,cells:cells};
}

/* 6. undirected network / relationship graph */
function network(roles,o){
  const w=o.w||360,h=o.h||220,nodes=o.nodes,edges=o.edges;
  let body='';
  edges.forEach(e=>{const a=nodes[e.a],b=nodes[e.b];
    body+='<line x1="'+a.x+'" y1="'+a.y+'" x2="'+b.x+'" y2="'+b.y+'" stroke="'+roles['ink-soft'].hex+'" stroke-width="'+(e.w||DATA*0.7)+'" stroke-opacity="0.55"/>';
  });
  nodes.forEach(n=>{
    const r=6+((n.size||1)*3),col=n.hub?roles.accent.hex:roles.ink.hex;
    body+='<circle cx="'+n.x+'" cy="'+n.y+'" r="'+r+'" fill="'+(n.hub?roles.accent.hex:roles.paper.hex)+'" stroke="'+col+'" stroke-width="'+(n.hub?0:1.1)+'"/>';
    body+=text(n.x,n.y+r+9,n.label,{size:LABEL_MM*0.6,weight:n.hub?800:500,fill:n.hub?roles.accent.hex:roles['ink-soft'].hex,anchor:'middle'});
  });
  return svg(w,h,body);
}
function genNetwork(){
  const labels=['Site A','Site B','Site C','Site D','Site E','Site F'];
  const hub=R(0,5);
  const nodes=labels.map((l,i)=>{const ang=(i/labels.length)*Math.PI*2;return{label:l,x:180+Math.cos(ang)*(i===hub?0:110),y:110+Math.sin(ang)*(i===hub?0:80),hub:i===hub,size:i===hub?2:1}});
  const edges=[];labels.forEach((l,i)=>{if(i!==hub)edges.push({a:hub,b:i,w:1.6})});
  for(let k=0;k<3;k++){let a=R(0,5),b=R(0,5);if(a!==b&&a!==hub&&b!==hub)edges.push({a:a,b:b})}
  return{nodes:nodes,edges:edges};
}

window.DG={setFont:setFont,sequenceDiagram:sequenceDiagram,genSequence:genSequence,gantt:gantt,genGantt:genGantt,
  component:component,genComponent:genComponent,stateMachine:stateMachine,genStateMachine:genStateMachine,
  matrix:matrix,genMatrix:genMatrix,network:network,genNetwork:genNetwork};
})();
