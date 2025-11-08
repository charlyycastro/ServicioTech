// Firma con mouse/táctil + guardado en hidden input
(function () {
  const canvas = document.getElementById('signature-canvas');
  const wrapper = document.getElementById('signature-wrapper');
  const clearBtn = document.getElementById('clear-signature');
  const hiddenInput = document.getElementById('firma-base64');
  const form = document.getElementById('order-form');

  if (!canvas || !wrapper) return;

  const ctx = canvas.getContext('2d');
  let drawing = false;
  let hasStroke = false;

  // Estilo de trazo
  function setStrokeStyle() {
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';
    ctx.lineWidth = 2;
    ctx.strokeStyle = '#111';
  }

  // Ajuste retina y tamaño del lienzo al contenedor
  function resizeCanvas() {
    const rect = wrapper.getBoundingClientRect();
    const width = Math.max(300, Math.floor(rect.width));
    const height = Math.max(160, Math.floor(rect.height)); // wrapper controla altura por CSS

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
    if (e.touches && e.touches.length) {
      return {
        x: e.touches[0].clientX - rect.left,
        y: e.touches[0].clientY - rect.top
      };
    } else {
      return {
        x: e.clientX - rect.left,
        y: e.clientY - rect.top
      };
    }
  }

  function start(e) {
    e.preventDefault();
    const { x, y } = getPos(e);
    drawing = true;
    hasStroke = true;
    ctx.beginPath();
    ctx.moveTo(x, y);
  }

  function move(e) {
    if (!drawing) return;
    e.preventDefault();
    const { x, y } = getPos(e);
    ctx.lineTo(x, y);
    ctx.stroke();
  }

  function end(e) {
    if (!drawing) return;
    e.preventDefault();
    drawing = false;
  }

  // Eventos mouse
  canvas.addEventListener('mousedown', start);
  canvas.addEventListener('mousemove', move);
  window.addEventListener('mouseup', end);

  // Eventos touch (mobile)
  canvas.addEventListener('touchstart', start, { passive: false });
  canvas.addEventListener('touchmove', move,   { passive: false });
  canvas.addEventListener('touchend', end,     { passive: false });
  canvas.addEventListener('touchcancel', end,  { passive: false });

  // Limpiar
  if (clearBtn) {
    clearBtn.addEventListener('click', function () {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      hasStroke = false;
      if (hiddenInput) hiddenInput.value = '';
    });
  }

  // Guardar al enviar
  if (form && hiddenInput) {
    form.addEventListener('submit', function () {
      if (hasStroke) {
        // Exporta PNG Base64
        hiddenInput.value = canvas.toDataURL('image/png');
      } else {
        hiddenInput.value = '';
      }
    });
  }

  // Redimensionar al mostrar el acordeón (Bootstrap)
  document.addEventListener('shown.bs.collapse', function (ev) {
    const target = ev.target;
    if (target && target.id === 'collapseFirma') {
      // Espera un tick para que el layout esté listo
      setTimeout(resizeCanvas, 50);
    }
  });

  // Resize on window
  window.addEventListener('resize', function () {
    const prevImage = hasStroke ? canvas.toDataURL() : null;
    resizeCanvas();
    // Nota: reponer la imagen tras resize es complejo; optamos por redibujar nuevo trazo.
    // Si necesitas conservar el trazo al redimensionar, implementamos un buffer de puntos.
  });

  // Init
  resizeCanvas();
  setStrokeStyle();
})();
