// static/orders/equipos.js
(function() {
  function addRow(prefix) {
    const body = document.getElementById(prefix + '-body');
    const total = document.getElementById('id_' + prefix + '-TOTAL_FORMS');
    const emptyProto = document.getElementById(prefix + '-empty');
    const idx = parseInt(total.value, 10);

    const tmp = document.createElement('tbody');
    tmp.innerHTML = emptyProto.innerHTML.trim();
    const tr = tmp.firstElementChild;

    // Campos por prefix
    const fieldsByPrefix = {
      equipos: ['marca','modelo','serie','descripcion'],
      materiales: ['descripcion','cantidad','comentarios'],
    };
    const fields = fieldsByPrefix[prefix] || [];

    tr.querySelectorAll('td').forEach(function(td){
      const text = td.textContent || '';
      fields.forEach(function(name){
        const marker = '__FIELD__:' + name;
        if (text.indexOf(marker) !== -1) {
          td.innerHTML = getEmptyFieldHTML(prefix, name, idx, name === 'cantidad' ? 'number' : 'text');
        }
      });
    });

    body.appendChild(tr);
    total.value = idx + 1;
  }

  function getEmptyFieldHTML(prefix, name, idx, type){
    const id = `id_${prefix}-__prefix__-${name}`;
    const baseName = `${prefix}-__prefix__-${name}`;
    const input = document.createElement(name === 'descripcion' || name === 'comentarios' ? 'input' : 'input');
    input.className = 'form-control';
    input.name = baseName.replace('__prefix__', idx);
    input.id = id.replace('__prefix__', idx);
    input.type = type || 'text';
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
