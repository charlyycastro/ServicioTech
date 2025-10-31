(function(){
const canvas = document.getElementById('sig');
if(!canvas) return;
const ctx = canvas.getContext('2d');
let drawing = false, prev = null;


function pos(e){
const r = canvas.getBoundingClientRect();
const x = (e.touches? e.touches[0].clientX : e.clientX) - r.left;
const y = (e.touches? e.touches[0].clientY : e.clientY) - r.top;
return {x,y};
}
function start(e){ drawing = true; prev = pos(e); }
function end(){ drawing = false; prev = null; document.getElementById('signature_data').value = canvas.toDataURL('image/png'); }
function move(e){ if(!drawing) return; const p = pos(e); ctx.beginPath(); ctx.moveTo(prev.x, prev.y); ctx.lineTo(p.x, p.y); ctx.stroke(); prev = p; }


canvas.addEventListener('mousedown', start);
canvas.addEventListener('mousemove', move);
window.addEventListener('mouseup', end);
canvas.addEventListener('touchstart', start, {passive:true});
canvas.addEventListener('touchmove', move, {passive:true});
window.addEventListener('touchend', end);


document.getElementById('sig-clear').addEventListener('click', ()=>{ ctx.clearRect(0,0,canvas.width,canvas.height); document.getElementById('signature_data').value=''; });
})();