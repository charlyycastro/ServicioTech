// static/orders/equipos.js
(function() {
  function addRow(prefix) {
    const body = document.getElementById(prefix + '-body');
    const total = document.getElementById('id_' + prefix + '-TOTAL_FORMS');
    const emptyProto = document.getElementById(prefix + '-empty');
    const idx = parseInt(total.value, 10);

    let rowHtml = emptyProto.innerHTML;
    const tmp = document.createElement('tbody');
    tmp.innerHTML = rowHtml.trim();
    const tr = tmp.firstElementChild;

    const fields = ['tipo','marca','modelo','serie','falla','descripcion','cantidad','unidad'];
    fields.forEach(function(name){
      tr.querySelectorAll('td').forEach(function(td){
        const marker = '__FIELD__:' + name;
        if (td.textContent && td.textContent.indexOf(marker) !== -1) {
          const html = getEmptyFieldHTML(prefix, name, idx);
          if (html) td.innerHTML = html;
        }
      });
    });

    body.appendChild(tr);
    total.value = idx + 1;
  }

  function getEmptyFieldHTML(prefix, name, idx){
    const id = `id_${prefix}-__prefix__-${name}`;
    const baseName = `${prefix}-__prefix__-${name}`;
    const input = document.createElement('input');
    input.className = 'form-control';
    input.name = baseName.replace('__prefix__', idx);
    input.id = id.replace('__prefix__', idx);
    input.type = (name === 'cantidad') ? 'number' : 'text';
    return input.outerHTML;
  }

  function removeRow(btn){
    const row = btn.closest('.formset-row');
    if (!row) return;
    const del = row.querySelector('input[type="checkbox"][name$="-DELETE"]');
    if (del) {
      del.checked = true;
      row.style.display = 'none';
    } else {
      row.remove();
    }
  }

  document.addEventListener('click', function(e){
    if (e.target.matches('[data-add-equipo]')) { e.preventDefault(); addRow('equipos'); }
    if (e.target.matches('[data-add-material]')) { e.preventDefault(); addRow('materiales'); }
    if (e.target.matches('[data-remove-row]')) { e.preventDefault(); removeRow(e.target); }
  });
})();
