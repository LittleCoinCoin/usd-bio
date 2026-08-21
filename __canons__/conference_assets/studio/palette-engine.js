/* palette-engine.js — the generator.
   Hue comes from a harmony rule on an OKLCH wheel; lightness and chroma come from a fixed
   role recipe; contrast is then verified and repaired by moving lightness only.
   Exposes window.PE. No dependencies. */
(function(){
const clamp=(v,a,b)=>Math.min(b,Math.max(a,v));
const mod=(v,m)=>((v%m)+m)%m;

/* ---------- sRGB ---------- */
function hex2rgb(h){h=String(h).trim();if(h[0]==='#'){h=h.slice(1);if(h.length===3)h=h.split('').map(c=>c+c).join('');return[parseInt(h.slice(0,2),16),parseInt(h.slice(2,4),16),parseInt(h.slice(4,6),16)]}const m=h.match(/[\d.]+/g);return m?[+m[0],+m[1],+m[2]]:[255,255,255]}
function rgb2hex(a){return'#'+a.map(v=>clamp(Math.round(v),0,255).toString(16).padStart(2,'0')).join('').toUpperCase()}
function s2l(v){v/=255;return v<=0.04045?v/12.92:Math.pow((v+0.055)/1.055,2.4)}
function l2s(v){v=clamp(v,0,1);return 255*(v<=0.0031308?v*12.92:1.055*Math.pow(v,1/2.4)-0.055)}
function lum(c){const[r,g,b]=hex2rgb(c);return 0.2126*s2l(r)+0.7152*s2l(g)+0.0722*s2l(b)}
function ratio(a,b){const x=lum(a),y=lum(b);return(Math.max(x,y)+0.05)/(Math.min(x,y)+0.05)}

/* ---------- OKLab / OKLCH ---------- */
function oklab2lin(L,a,b){
  const l=L+0.3963377774*a+0.2158037573*b,m=L-0.1055613458*a-0.0638541728*b,s=L-0.0894841775*a-1.2914855480*b;
  const l3=l*l*l,m3=m*m*m,s3=s*s*s;
  return[4.0767416621*l3-3.3077115913*m3+0.2309699292*s3,
        -1.2684380046*l3+2.6097574011*m3-0.3413193965*s3,
        -0.0041960863*l3-0.7034186147*m3+1.7076147010*s3];
}
function lin2oklab(r,g,b){
  const l=Math.cbrt(0.4122214708*r+0.5363325363*g+0.0514459929*b);
  const m=Math.cbrt(0.2119034982*r+0.6806995451*g+0.1073969566*b);
  const s=Math.cbrt(0.0883024619*r+0.2817188376*g+0.6299787005*b);
  return[0.2104542553*l+0.7936177850*m-0.0040720468*s,
         1.9779984951*l-2.4285922050*m+0.4505937099*s,
         0.0259040371*l+0.7827717662*m-0.8086757660*s];
}
const ok=(lin)=>lin.every(v=>v>=-0.0015&&v<=1.0015);
function lchLin(L,C,h){const r=h*Math.PI/180;return oklab2lin(L,Math.cos(r)*C,Math.sin(r)*C)}
function maxChroma(L,h){let lo=0,hi=0.42;for(let i=0;i<18;i++){const mid=(lo+hi)/2;if(ok(lchLin(L,mid,h)))lo=mid;else hi=mid}return lo}
function oklch2hex(L,C,h){let lin=lchLin(L,C,h);if(!ok(lin))lin=lchLin(L,maxChroma(L,h),h);return rgb2hex(lin.map(l2s))}
function hex2oklch(hex){const[r,g,b]=hex2rgb(hex).map(s2l);const[L,a,bb]=lin2oklab(r,g,b);return{L:L,C:Math.hypot(a,bb),h:mod(Math.atan2(bb,a)*180/Math.PI,360)}}
function dE(h1,h2){const a=hex2oklch(h1),b=hex2oklch(h2);
  const A=[a.L,Math.cos(a.h*Math.PI/180)*a.C,Math.sin(a.h*Math.PI/180)*a.C];
  const B=[b.L,Math.cos(b.h*Math.PI/180)*b.C,Math.sin(b.h*Math.PI/180)*b.C];
  return 100*Math.hypot(A[0]-B[0],A[1]-B[1],A[2]-B[2]);}

/* ---------- colour-vision deficiency (Machado 2009, severity 1.0; linear RGB) ---------- */
const CVD={
  protan:[[0.152286,1.052583,-0.204868],[0.114503,0.786281,0.099216],[-0.003882,-0.048116,1.051998]],
  deutan:[[0.367322,0.860646,-0.227968],[0.280085,0.672501,0.047413],[-0.011820,0.042940,0.968881]],
  tritan:[[1.255528,-0.076749,-0.178779],[-0.078411,0.930809,0.147602],[0.004733,0.691367,0.303900]]
};
function cvdHex(hex,type){const M=CVD[type];if(!M)return hex;const[r,g,b]=hex2rgb(hex).map(s2l);
  return rgb2hex(M.map(row=>l2s(clamp(row[0]*r+row[1]*g+row[2]*b,0,1))));}

/* ---------- harmony rules ---------- */
const HARMONY={
  mono:{label:'Monochrome',offsets:[0],slots:['base'],
    use:'One hue at several lightnesses. Nothing on the sheet competes with the plate. The default for evidence-dense work.'},
  analogous:{label:'Analogous',offsets:[0,-34,34],slots:['base','cool side','warm side'],
    use:'Neighbours. Reads as one family with a slight temperature shift; the accent is quiet and will not win a crowded hall.'},
  complement:{label:'Complement',offsets:[0,180],slots:['base','opposite'],
    use:'Maximum hue separation with only two slots — one for the neutral family and plate, one for the accent. The strongest five-second layer per unit of ink.'},
  split:{label:'Split complement',offsets:[0,152,208],slots:['base','opposite −28°','opposite +28°'],
    use:'A complement that has been softened, and a spare slot for the plate when it must differ from the ink family.'},
  triad:{label:'Triad',offsets:[0,120,240],slots:['base','+120°','+240°'],
    use:'Three equal hues. Equality is the problem: the poster has no third job, so one slot must be discarded on purpose.'},
  square:{label:'Square',offsets:[0,90,180,270],slots:['base','+90°','+180°','+270°'],
    use:'Four hues for three jobs at most. Included for completeness and to be argued out of.'},
  compound:{label:'Compound',offsets:[0,32,180,212],slots:['base','base +32°','opposite','opposite +32°'],
    use:'Our reading of Adobe’s compound: a complement pair plus each one’s neighbour. Useful when the plate and the accent should be related but not identical.'}
};
const RULES=Object.keys(HARMONY);

/* ---------- role recipe: the part authors do not get to set ---------- */
const ROLE_SPEC=[
  ['paper','n',s=>0.995-0.020*s.tint, s=>0.007*s.tint*s.sat],
  ['field','n',s=>0.958-0.022*s.tint, s=>0.018*s.sat],
  ['ink','n',s=>0.215, s=>0.022*s.sat],
  ['ink-soft','n',s=>0.455, s=>0.018*s.sat],
  ['panel','p',s=>0.225, s=>0.085*s.sat],
  ['panel-ink','n',s=>0.986-0.010*s.tint, s=>0.006*s.tint*s.sat],
  ['accent','a',s=>0.485, s=>0.150*s.sat],
  ['accent-on-panel','a',s=>0.750, s=>0.155*s.sat],
  ['rule','r',s=>0.615, s=>0.014*s.sat]
];
const ROLES=ROLE_SPEC.map(r=>r[0]);

/* ---------- contrast contract ---------- */
const CHECKS=[
  ['ink','paper',4.5,'prose on paper','fg'],
  ['ink-soft','paper',4.5,'soft prose on paper','fg'],
  ['ink','field',4.5,'prose on evidence field','bg'],
  ['panel-ink','panel',4.5,'takeaway on plate','bg'],
  ['accent','paper',4.5,'accent text on paper','fg'],
  ['accent-on-panel','panel',4.5,'accent on plate','fg'],
  ['rule','paper',3,'hairlines & graphics','fg'],
  /* ADDED 2026-08-21: figure frames sit on --field, not on --paper, so checking only
     against paper let a rule pass at 3.2:1 on white and sit at 2.8:1 where it is actually
     drawn. Neither the hand-written tokens nor the six attested themes caught this. */
  ['rule','field',3,'hairlines on the evidence field','fg']
];

/* ---------- reference ink schedule ----------
   Net, non-overlapping shares of an A0 landscape sheet in the contained-plate layout.
   Approximates the measured specimen; used where measuring the DOM is not worth it. */
const SCHEDULE=[['paper',0.705],['field',0.145],['panel',0.131],['ink',0.012],['ink-soft',0.006],['accent',0.001]];
const COV_MAX=0.30, PLATE_MAX=0.22, PLATE_SHARE=0.131;

/* CANON NOTE (added on import to the repo): this is the ORIGINAL Okabe-Ito order.
   library/tokens.css reorders the same eight values by contrast-on-paper, so --cat-1 there is
   #0072B2 while OKABE[0] here is #000000. Charts drawn by chart-kit.js cycle THIS order.
   The two must be reconciled — see studio/PENDING-reconcile.md. Do not silently "fix" either
   side: the CSS order encodes a safety ranking, this order encodes the published palette. */
const OKABE=['#000000','#E69F00','#56B4E9','#009E73','#F0E442','#0072B2','#D55E00','#CC79A7'];

function slotHues(st){const H=HARMONY[st.rule]||HARMONY.split;return H.offsets.map(o=>mod(st.hue+o,360))}

/* Sensible non-colliding defaults for a rule's slot count: neutral is always fixed to
   slot 0, so plate/accent should not default onto it once a spare slot exists. */
function assignDefaults(ruleKey){
  const n=(HARMONY[ruleKey]||HARMONY.split).offsets.length;
  if(n<=1)return{plateSlot:0,accentSlot:0};
  if(n===2)return{plateSlot:0,accentSlot:1};
  return{plateSlot:1,accentSlot:2};
}

function build(st,light){
  st=Object.assign({rule:'split',hue:262,sat:0.62,tint:0.12,plateSlot:1,accentSlot:2,ruleSlot:null,overrides:{}},st);
  const hues=slotHues(st), n=hues.length;
  const ov=st.overrides||{};
  const hueFor={n:hues[0],p:hues[clamp(st.plateSlot,0,n-1)],a:hues[clamp(st.accentSlot,0,n-1)],
    r:st.ruleSlot!=null?hues[clamp(st.ruleSlot,0,n-1)]:hues[0]};
  const roles={};
  ROLE_SPEC.forEach(([role,slot,fL,fC])=>{
    const locked=ov[role]!=null,L=locked?clamp(ov[role],0.04,0.995):fL(st),C=fC(st),h=hueFor[slot];
    roles[role]={L:L,C:C,h:h,hex:oklch2hex(L,C,h),slot:slot,locked:locked};
  });
  const repairs=[];
  CHECKS.forEach(([a,b,min,label,lever])=>{
    const tgt=lever==='fg'?a:b, other=lever==='fg'?b:a;
    if(ratio(roles[a].hex,roles[b].hex)>=min)return;
    let mv=tgt,anchor=other;
    if(roles[mv].locked){if(roles[anchor].locked){repairs.push({role:tgt,label:label,from:roles[tgt].L,to:roles[tgt].L,dir:'locked',ok:false,locked:true});return}mv=other;anchor=tgt;}
    const t=roles[mv],from=t.L,dir=t.L>roles[anchor].L?1:-1;
    for(let i=0;i<95;i++){
      const L=clamp(t.L+dir*0.01,0.04,0.995);
      if(L===t.L)break;
      t.L=L;t.hex=oklch2hex(t.L,t.C,t.h);
      if(ratio(roles[a].hex,roles[b].hex)>=min)break;
    }
    repairs.push({role:mv,label:label,from:from,to:t.L,dir:dir>0?'lighter':'darker',
      ok:ratio(roles[a].hex,roles[b].hex)>=min});
  });
  const checks=CHECKS.map(([a,b,min,label])=>{
    const v=ratio(roles[a].hex,roles[b].hex);return{label:label,a:a,b:b,min:min,val:v,pass:v>=min};
  });
  if(light)return{state:st,roles:roles,order:ROLES,hues:hues,hueFor:hueFor,checks:checks,repairs:repairs};
  const mono=ratio(roles.accent.hex,roles.ink.hex);
  const ink=estimateInk(roles);
  const cvd=['protan','deutan','tritan'].map(type=>{
    const pairs=[['accent','ink','accent among prose'],['accent','field','accent on the field'],
                 ['accent-on-panel','panel-ink','accent inside the plate'],['panel','field','plate against the field']]
      .map(([x,y,label])=>{const d=dE(cvdHex(roles[x].hex,type),cvdHex(roles[y].hex,type));return{label:label,d:d,pass:d>=10}});
    return{type:type,pairs:pairs,worst:Math.min.apply(null,pairs.map(p=>p.d))};
  });
  let catMin=999,catAt='';
  OKABE.forEach((c,i)=>{const d=dE(roles.accent.hex,c);if(d<catMin){catMin=d;catAt='--cat-'+(i+1)}});
  const jobs=new Set([0,clamp(st.plateSlot,0,n-1),clamp(st.accentSlot,0,n-1)]);
  if(st.ruleSlot!=null)jobs.add(clamp(st.ruleSlot,0,n-1));
  const unused=n-jobs.size;
  const warn=[];
  if(unused>0)warn.push(HARMONY[st.rule].label+' emits '+n+' hues; '+jobs.size+' have a job. '+unused+' slot'+(unused>1?'s':'')+' unused — assign one to --rule for a fourth voice, or leave idle. Discard on purpose, never spend.');
  if(ink.c>COV_MAX)warn.push('Coverage C '+(ink.c*100).toFixed(1)+'% is over the '+(COV_MAX*100)+'% ceiling. Lever: '+(ink.ground>0.06?'drop the ground tint':'lighten the plate or cut its share')+'.');
  if(catMin<14)warn.push('The accent sits '+catMin.toFixed(0)+' ΔE from '+catAt+' in the categorical scale. On a sheet where both appear, the accent stops being a signal.');
  if(mono<1.6)warn.push('Accent and ink separate by only '+mono.toFixed(2)+':1 in greyscale — the accent must be carried by underline or weight, not colour.');
  if(!repairs.every(r=>r.ok))warn.push('A contrast check could not be repaired inside the lightness bounds — reduce the chroma temperament, or free up a manually fixed role.');
  const lockedRoles=Object.keys(ov).filter(k=>ov[k]!=null);
  if(lockedRoles.length)warn.push(lockedRoles.length+' role'+(lockedRoles.length>1?'s':'')+' lightness-locked by hand ('+lockedRoles.map(r=>'--'+r).join(', ')+') — the recipe no longer guarantees these; the checks above are still live, so watch for fails.');
  return{state:st,roles:roles,order:ROLES,hues:hues,hueFor:hueFor,checks:checks,repairs:repairs,
    mono:mono,ink:ink,cvd:cvd,cat:{d:catMin,at:catAt},warnings:warn,
    pass:checks.every(c=>c.pass)&&ink.c<=COV_MAX};
}

function estimateInk(roles){
  let marks=0,ground=0;
  SCHEDULE.forEach(([role,share])=>{
    const cost=share*(1-lum(roles[role].hex));
    if(role==='paper')ground+=cost;else marks+=cost;
  });
  return{c:marks+ground,marks:marks,ground:ground,plate:PLATE_SHARE};
}

function css(res,name){
  const n=(name||'untitled').toLowerCase().replace(/[^a-z0-9]+/g,'-').replace(/^-|-$/g,'');
  const st=res.state;
  const head='/* '+HARMONY[st.rule].label+' · base hue '+st.hue.toFixed(0)+'° · chroma '+st.sat.toFixed(2)+
    ' · ground tint '+st.tint.toFixed(2)+' · C '+(res.ink.c*100).toFixed(1)+'% */';
  const body=ROLES.map(r=>'--'+r+':'+res.roles[r].hex).join(';');
  return head+'\n[data-theme="'+n+'"]{'+body+'}';
}

window.PE={hex2rgb:hex2rgb,rgb2hex:rgb2hex,lum:lum,ratio:ratio,oklch2hex:oklch2hex,hex2oklch:hex2oklch,
  maxChroma:maxChroma,lchLin:lchLin,l2s:l2s,dE:dE,cvdHex:cvdHex,HARMONY:HARMONY,RULES:RULES,ROLES:ROLES,
  ROLE_SPEC:ROLE_SPEC,CHECKS:CHECKS,SCHEDULE:SCHEDULE,OKABE:OKABE,COV_MAX:COV_MAX,PLATE_MAX:PLATE_MAX,
  build:build,estimateInk:estimateInk,css:css,slotHues:slotHues,mod:mod,clamp:clamp,assignDefaults:assignDefaults};
})();
