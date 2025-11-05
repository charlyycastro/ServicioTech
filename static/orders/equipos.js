// static/orders/equipos.js
(function () {
  const addBtn   = document.getElementById('add-equipo');
  const table    = document.getElementById('equipos-table');
  const template = document.getElementById('equip-row-template');
  const totalInp = document.getElementById('id_equipos-TOTAL_FORMS');

  if (!addBtn || !table || !template || !totalInp) return;

  const tbody = table.querySelector('tbody');

  function bindDelete(btn, row) {
    btn.addEventListener('click', () => {
      const del = row.querySelector('input[name$="-DELETE"]');
      const pk  = row.querySelector('input[name$="-id"]');
      if (del && pk && pk.value) {
        // fila ya guardada: marcar delete y ocultar
        del.checked = true;
        row.style.display = 'none';
      } else {
        // fila nueva: quitar del DOM y decrementar TOTAL_FORMS
        row.remove();
        totalInp.value = String(Math.max(0, parseInt(totalInp.value, 10) - 1));
      }
    });
  }

  function addRow() {
    const idx = parseInt(totalInp.value, 10);
    const html = template.innerHTML.replace(/__prefix__/g, idx);
    const frag = document.createElement('tbody');
    frag.innerHTML = html.trim();
    const row = frag.firstElementChild;
    tbody.appendChild(row);
    totalInp.value = String(idx + 1);

    const delBtn = row.querySelector('.btn-del-equipo');
    if (delBtn) bindDelete(delBtn, row);
  }

  // enlazar ya existentes
  tbody.querySelectorAll('.btn-del-equipo').forEach(btn => {
    bindDelete(btn, btn.closest('tr'));
  });

  addBtn.addEventListener('click', addRow);
})();
