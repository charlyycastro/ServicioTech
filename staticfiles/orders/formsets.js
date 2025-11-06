// static/orders/formsets.js
(function () {
  const addBtn = document.getElementById('add-equipo');
  const tableBody = document.querySelector('#equipos-table tbody');
  const template = document.getElementById('empty-equipo-form');
  const totalInput = document.getElementById('id_equipos-TOTAL_FORMS');

  if (!addBtn || !tableBody || !template || !totalInput) return;

  function addRow() {
    const index = parseInt(totalInput.value, 10);
    // Clonamos el template y reemplazamos __prefix__ por el índice
    const html = template.innerHTML.replace(/__prefix__/g, index);
    tableBody.insertAdjacentHTML('beforeend', html);
    totalInput.value = index + 1;
  }

  function removeRow(btn) {
    const tr = btn.closest('tr');
    if (!tr) return;
    // Si existe un checkbox DELETE en la fila (objs existentes), se marca y se oculta
    const del = tr.querySelector('input[type="checkbox"][name$="-DELETE"]');
    if (del) {
      del.checked = true;
      tr.style.display = 'none';
    } else {
      // Fila nueva: limpiamos inputs y ocultamos (Django la ignorará por estar vacía)
      tr.querySelectorAll('input, textarea').forEach(i => i.value = '');
      tr.style.display = 'none';
    }
  }

  addBtn.addEventListener('click', addRow);
  document.addEventListener('click', (e) => {
    if (e.target.classList.contains('remove-row')) {
      e.preventDefault();
      removeRow(e.target);
    }
  });
})();
