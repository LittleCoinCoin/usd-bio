/* pictogram-kit.js — construction rules for a small, coherent pictogram system.
   Closed on HOW an icon is built (grid, stroke, corner, colour); open on WHICH
   concepts get drawn — that vocabulary is inherently domain-specific.
   All icons share one 24-unit grid so stroke and corner radius scale together. */
(function(){
const GRID=24,STROKE_RATIO=0.1,CORNER_RATIO=1/12,STROKE_U=GRID*STROKE_RATIO,CORNER_U=GRID*CORNER_RATIO;
const INLINE_MM=7.06,STANDALONE_MM=INLINE_MM*2;

function guide(roles){
  let g='';
  for(let i=0;i<=24;i+=4){
    g+='<line x1="'+i+'" y1="0" x2="'+i+'" y2="24" stroke="'+roles.rule.hex+'" stroke-width="0.18" stroke-opacity="0.55"/>';
    g+='<line x1="0" y1="'+i+'" x2="24" y2="'+i+'" stroke="'+roles.rule.hex+'" stroke-width="0.18" stroke-opacity="0.55"/>';
  }
  g+='<circle cx="12" cy="12" r="10" fill="none" stroke="'+roles.rule.hex+'" stroke-width="0.32" stroke-dasharray="0.6 0.6"/>';
  g+='<rect x="3" y="3" width="18" height="18" fill="none" stroke="'+roles.rule.hex+'" stroke-width="0.32" stroke-dasharray="0.6 0.6"/>';
  return g;
}
function icon(key,roles,o){
  o=o||{};const col=o.emphasis?roles.accent.hex:roles.ink.hex;
  const body=ICONS[key]||'';
  const g=(o.guide?guide(roles):'')+'<g fill="none" stroke="'+col+'" stroke-width="'+STROKE_U+'" stroke-linecap="round" stroke-linejoin="round">'+body+'</g>';
  return '<svg viewBox="0 0 24 24" width="100%" height="100%">'+g+'</svg>';
}
const ICONS={
  subject:'<circle cx="12" cy="7.5" r="3.4"/><path d="M5.2,20.5 C5.2,14.8 8.2,12.2 12,12.2 C15.8,12.2 18.8,14.8 18.8,20.5"/>',
  sample:'<rect x="9" y="3.5" width="6" height="15" rx="2.6"/><line x1="8" y1="3.5" x2="16" y2="3.5"/><line x1="9.6" y1="13.5" x2="14.4" y2="13.5"/>',
  time:'<circle cx="12" cy="12" r="9"/><line x1="12" y1="12" x2="12" y2="6.8"/><line x1="12" y1="12" x2="16" y2="13.6"/>',
  location:'<path d="M12,3.4 C8.2,3.4 5.2,6.4 5.2,10.1 C5.2,15.6 12,21 12,21 C12,21 18.8,15.6 18.8,10.1 C18.8,6.4 15.8,3.4 12,3.4 Z"/><circle cx="12" cy="10.1" r="2.6"/>',
  instrument:'<circle cx="10" cy="10" r="6"/><line x1="14.6" y1="14.6" x2="20.4" y2="20.4"/>',
  computation:'<rect x="6.5" y="6.5" width="11" height="11" rx="1.6"/><line x1="9" y1="3.4" x2="9" y2="6.5"/><line x1="15" y1="3.4" x2="15" y2="6.5"/><line x1="9" y1="17.5" x2="9" y2="20.6"/><line x1="15" y1="17.5" x2="15" y2="20.6"/><line x1="3.4" y1="9" x2="6.5" y2="9"/><line x1="3.4" y1="15" x2="6.5" y2="15"/><line x1="17.5" y1="9" x2="20.6" y2="9"/><line x1="17.5" y1="15" x2="20.6" y2="15"/>',
  citation:'<path d="M4,6.4 C4,6.4 8,4.6 12,6.4 L12,18 C8,16.2 4,18 4,18 Z"/><path d="M20,6.4 C20,6.4 16,4.6 12,6.4 L12,18 C16,16.2 20,18 20,18 Z"/>',
  flag:'<line x1="6" y1="3.2" x2="6" y2="20.8"/><path d="M6,4.2 L18,7.4 L6,10.6 Z"/>'
};
window.PG={GRID:GRID,STROKE_RATIO:STROKE_RATIO,CORNER_RATIO:CORNER_RATIO,STROKE_U:STROKE_U,CORNER_U:CORNER_U,
  INLINE_MM:INLINE_MM,STANDALONE_MM:STANDALONE_MM,KEYS:Object.keys(ICONS),icon:icon,guide:guide};
})();
