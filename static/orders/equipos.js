// static/orders/equipos.js
(function() {
  function addRow(prefix) {
    const body = document.getElementById(prefix + '-body');
    const total = document.getElementById('id_' + prefix + '-TOTAL_FORMS');
    const emptyProto = document.getElementById(prefix + '-empty');
    
    if (!body || !total || !emptyProto) return;

    const idx = parseInt(total.value, 10);
    const tmp = document.createElement('tbody');
    tmp.innerHTML = emptyProto.innerHTML.trim();
    const tr = tmp.firstElementChild;

    // Definimos qué campos hay en cada tabla
    const fieldsByPrefix = {
      equipos: ['marca','modelo','serie','descripcion'],
      materiales: ['descripcion','cantidad','comentarios'],
    };
    const fields = fieldsByPrefix[prefix] || [];

    // Reemplazamos los marcadores __FIELD__
    tr.querySelectorAll('td').forEach(function(td){
      const text = td.textContent || '';
      fields.forEach(function(name){
        const marker = '__FIELD__:' + name;
        if (text.indexOf(marker) !== -1) {
          // Determinamos si debe ser input o textarea
          // 'descripcion' (en equipos) y 'comentarios' (en materiales) deben ser Textarea
          const isTextarea = (prefix === 'equipos' && name === 'descripcion') || 
                             (prefix === 'materiales' && name === 'comentarios');
                             
          const inputType = (name === 'cantidad') ? 'number' : 'text';

          td.innerHTML = getEmptyFieldHTML(prefix, name, idx, inputType, isTextarea);
        }
      });
    });

    body.appendChild(tr);
    total.value = idx + 1;
  }

  function getEmptyFieldHTML(prefix, name, idx, type, isTextarea){
    const id = `id_${prefix}-__prefix__-${name}`.replace('__prefix__', idx);
    const inputName = `${prefix}-__prefix__-${name}`.replace('__prefix__', idx);
    
    const el = document.createElement(isTextarea ? 'textarea' : 'input');
    el.className = 'form-control';
    el.name = inputName;
    el.id = id;
    
    if (isTextarea) {
      el.rows = 2; // Misma altura que en CSS
      el.style.resize = 'none'; // Evitar que rompa la tabla
    } else {
      el.type = type || 'text';
    }
    
    return el.outerHTML;
  }

  function removeRow(btn){
    const row = btn.closest('.formset-row');
    if (!row) return;
    
    // Buscar el checkbox de eliminación de Django (si es una fila existente)
    const del = row.querySelector('input[type="checkbox"][name$="-DELETE"]');
    
    if (del) {
      del.checked = true;
      row.style.display = 'none'; // Ocultar visualmente
    } else {
      // Si es una fila nueva dinámica que aún no se guardó en BD
      row.remove();
    }
  }

  document.addEventListener('click', function(e){
    if (e.target.matches('[data-add-equipo]')) { e.preventDefault(); addRow('equipos'); }
    if (e.target.matches('[data-add-material]')) { e.preventDefault(); addRow('materiales'); }
    if (e.target.matches('[data-remove-row]')) { e.preventDefault(); removeRow(e.target); }
  });
})();