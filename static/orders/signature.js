// static/orders/signature.js
document.addEventListener("DOMContentLoaded", function () {
  const wrapper = document.getElementById("signature-wrapper");
  const canvas = document.getElementById("signature-canvas");
  const clearBtn = document.getElementById("sig-clear");
  const undoBtn = document.getElementById("sig-undo");
  const dataInput = document.getElementById("signature-data");
  const form = document.getElementById("order-form");
  if (!wrapper || !canvas) return;

  const ctx = canvas.getContext("2d");
  let drawing = false;
  let last = null;
  let stack = [];

  function safeRect() {
    const r = wrapper.getBoundingClientRect();
    if (r.width < 2 || r.height < 2) {
      return { width: wrapper.clientWidth || 320, height: wrapper.clientHeight || 220 };
    }
    return { width: r.width, height: r.height };
  }

  function resizeCanvas(preserve = true) {
    const ratio = Math.max(window.devicePixelRatio || 1, 1);
    const { width, height } = safeRect();
    const prev = preserve ? ctx.getImageData(0, 0, canvas.width || 1, canvas.height || 1) : null;

    canvas.style.width = width + "px";
    canvas.style.height = height + "px";
    canvas.width = Math.max(1, Math.round(width * ratio));
    canvas.height = Math.max(1, Math.round(height * ratio));

    ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
    ctx.lineWidth = 2;
    ctx.lineJoin = "round";
    ctx.lineCap = "round";
    ctx.strokeStyle = "#000";

    if (preserve && prev && prev.width && prev.height) {
      ctx.setTransform(1, 0, 0, 1, 0, 0);
      ctx.putImageData(prev, 0, 0);
      ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
    } else {
      ctx.clearRect(0, 0, width, height);
    }
  }

  requestAnimationFrame(() => resizeCanvas(false));
  window.addEventListener("resize", () => resizeCanvas(true));
  if ("ResizeObserver" in window) {
    new ResizeObserver(() => resizeCanvas(true)).observe(wrapper);
  }

  function pointFromEvent(e) {
    const rect = canvas.getBoundingClientRect();
    const clientX = (e.clientX !== undefined ? e.clientX : (e.touches && e.touches[0].clientX));
    const clientY = (e.clientY !== undefined ? e.clientY : (e.touches && e.touches[0].clientY));
    return { x: clientX - rect.left, y: clientY - rect.top };
  }

  function startStroke(e) {
    e.preventDefault();
    if (canvas.width < 2 || canvas.height < 2) resizeCanvas(false);
    drawing = true;
    last = pointFromEvent(e);
    try { stack.push(ctx.getImageData(0, 0, canvas.width, canvas.height)); } catch (_) {}
    document.body.classList.add("signing");
  }

  function moveStroke(e) {
    if (!drawing) return;
    e.preventDefault();
    const p = pointFromEvent(e);
    ctx.beginPath();
    ctx.moveTo(last.x, last.y);
    ctx.lineTo(p.x, p.y);
    ctx.stroke();
    last = p;
  }

  function endStroke() {
    if (!drawing) return;
    drawing = false;
    last = null;
    document.body.classList.remove("signing");
  }

  const opts = { passive: false };
  canvas.addEventListener("pointerdown", startStroke, opts);
  canvas.addEventListener("pointermove", moveStroke, opts);
  window.addEventListener("pointerup", endStroke, opts);
  window.addEventListener("pointercancel", endStroke, opts);
  canvas.addEventListener("touchstart", startStroke, opts);
  canvas.addEventListener("touchmove", moveStroke, opts);
  window.addEventListener("touchend", endStroke, opts);
  window.addEventListener("touchcancel", endStroke, opts);

  clearBtn && clearBtn.addEventListener("click", () => {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    stack = [];
    if (dataInput) dataInput.value = "";
  });

  undoBtn && undoBtn.addEventListener("click", () => {
    if (!stack.length) return;
    const imgData = stack.pop();
    ctx.putImageData(imgData, 0, 0);
  });

  form && form.addEventListener("submit", () => {
    if (dataInput) dataInput.value = canvas.toDataURL("image/png");
  });
});
