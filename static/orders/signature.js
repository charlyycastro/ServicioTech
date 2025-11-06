// static/orders/signature.js
(function(){
  const canvas = document.getElementById('signature');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  let drawing = false; let last = null;

  function posFromEvent(ev){
    const rect = canvas.getBoundingClientRect();
    const pt = ev.touches ? ev.touches[0] : ev;
    return {
      x: (pt.clientX - rect.left) * (canvas.width / rect.width),
      y: (pt.clientY - rect.top) * (canvas.height / rect.height)
    };
  }

  function start(ev){ drawing = true; last = posFromEvent(ev); ev.preventDefault(); }
  function move(ev){
    if (!drawing) return;
    const p = posFromEvent(ev);
    ctx.beginPath();
    ctx.moveTo(last.x, last.y);
    ctx.lineTo(p.x, p.y);
    ctx.lineWidth = 2; ctx.lineCap = 'round';
    ctx.stroke();
    last = p; ev.preventDefault();
  }
  function end(){ drawing = false; save(); }

  function save(){
    const input = document.getElementById('firma-base64');
    if (input) input.value = canvas.toDataURL('image/png');
  }

  canvas.addEventListener('mousedown', start);
  canvas.addEventListener('mousemove', move);
  document.addEventListener('mouseup', end);

  canvas.addEventListener('touchstart', start, {passive:false});
  canvas.addEventListener('touchmove', move, {passive:false});
  canvas.addEventListener('touchend', end);

  document.getElementById('clear-signature')?.addEventListener('click', function(){
    ctx.clearRect(0,0,canvas.width,canvas.height);
    save();
  });
})();
