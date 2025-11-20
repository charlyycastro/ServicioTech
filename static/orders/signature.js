// static/orders/signature.js - VERSIÓN FINAL LIMPIA
(function () {
  // CONFIGURACIÓN
  const CANVAS_ID = 'signature-canvas';
  const WRAPPER_ID = 'signature-wrapper';
  const INPUT_ID = 'firma_b64';
  const CLEAR_BTN_ID = 'clear-signature';
  const FORM_ID = 'order-form';

  const canvas = document.getElementById(CANVAS_ID);
  const wrapper = document.getElementById(WRAPPER_ID);
  const hiddenInput = document.getElementById(INPUT_ID);
  const form = document.getElementById(FORM_ID);

  // Si no existe el canvas (ej. estamos en "Ver Detalle"), salimos silenciosamente.
  if (!canvas || !wrapper || !hiddenInput) return;

  // Si llegamos aquí, es porque ESTAMOS en la pantalla de crear/editar
  console.log("✅ Sistema de firma activado.");

  const ctx = canvas.getContext('2d');
  const clearBtn = document.getElementById(CLEAR_BTN_ID);
  let drawing = false;
  let hasStroke = false;

  function setStrokeStyle() {
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';
    ctx.lineWidth = 2;
    ctx.strokeStyle = '#111';
  }

  function resizeCanvas() {
    const rect = wrapper.getBoundingClientRect();
    const width = Math.max(300, Math.floor(rect.width));
    const height = Math.max(160, Math.floor(rect.height)); 
    const dpr = window.devicePixelRatio || 1;

    canvas.width = Math.floor(width * dpr);
    canvas.height = Math.floor(height * dpr);
    canvas.style.width = width + 'px';
    canvas.style.height = height + 'px';
    ctx.scale(dpr, dpr);
    setStrokeStyle();
  }

  function getPos(e) {
    const rect = canvas.getBoundingClientRect();
    const clientX = e.touches ? e.touches[0].clientX : e.clientX;
    const clientY = e.touches ? e.touches[0].clientY : e.clientY;
    return { x: clientX - rect.left, y: clientY - rect.top };
  }

  function start(e) {
    e.preventDefault();
    drawing = true;
    hasStroke = true;
    const pos = getPos(e);
    ctx.beginPath();
    ctx.moveTo(pos.x, pos.y);
  }

  function move(e) {
    if (!drawing) return;
    e.preventDefault();
    const pos = getPos(e);
    ctx.lineTo(pos.x, pos.y);
    ctx.stroke();
  }

  function end(e) {
    if (!drawing) return;
    e.preventDefault();
    drawing = false;
  }

  ['mousedown', 'touchstart'].forEach(evt => canvas.addEventListener(evt, start, { passive: false }));
  ['mousemove', 'touchmove'].forEach(evt => canvas.addEventListener(evt, move, { passive: false }));
  ['mouseup', 'touchend', 'touchcancel', 'mouseleave'].forEach(evt => canvas.addEventListener(evt, end));

  if (clearBtn) {
    clearBtn.addEventListener('click', function () {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      hasStroke = false;
      hiddenInput.value = '';
    });
  }

  if (form) {
    form.addEventListener('submit', function () {
      if (hasStroke) {
        hiddenInput.value = canvas.toDataURL('image/png');
      } else {
        hiddenInput.value = '';
      }
    });
  }

  // Inicializar al abrir acordeón y resize
  document.addEventListener('shown.bs.collapse', function (ev) {
    if (ev.target.id === 'collapseFirma') resizeCanvas();
  });
  resizeCanvas();
  window.addEventListener('resize', resizeCanvas);
})();