// static/orders/equipos.js
document.addEventListener('DOMContentLoaded', () => {
  const tableBody = document.querySelector('#equipos-table tbody');
  const addBtn    = document.getElementById('add-equipo');
  const total     = document.getElementById('id_equipos-TOTAL_FORMS'); // lo genera Django
  const tpl       = document.getElementById('equip-row-template');

  if (!tableBody || !addBtn || !total || !tpl) return;

  function wireDelete(row) {
    const btn = row.querySelector('.btn-del-equipo');
    if (!btn) return;
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      const delInput = row.querySelector('input[name$="-DELETE"]');
      // Si la fila es nueva (sin PK), la removemos y decrementamos el contador.
      if (row.dataset.new === '1') {
        row.remove();
        total.value = String(Math.max(0, parseInt(total.value || '0', 10) - 1));
      } else {
        // Si es existente, marcamos DELETE y ocultamos la fila.
        if (delInput) delInput.checked = true;
        row.style.display = 'none';
      }
    });
  }

  function addRow() {
    const idx = parseInt(total.value || '0', 10);
    // Clonar la plantilla y reemplazar __prefix__ por el índice
    const html = tpl.innerHTML.replace(/__prefix__/g, idx);
    const tmp = document.createElement('tbody');
    tmp.innerHTML = html.trim();
    const row = tmp.firstElementChild;

    row.dataset.new = '1';
    tableBody.appendChild(row);

    total.value = String(idx + 1);
    wireDelete(row);
  }

  // Enlazar existentes
  tableBody.querySelectorAll('tr.equipo-row').forEach(wireDelete);

  // Click para agregar
  addBtn.addEventListener('click', addRow);
});
