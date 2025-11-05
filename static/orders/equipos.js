// Dinámica del formset de equipos
(function () {
  const addBtn = document.getElementById("add-equipo");
  const tbody = document.querySelector("#equipos-table tbody");
  const tmpl = document.getElementById("equip-row-template");
  const total = document.querySelector('input[name="equipos-TOTAL_FORMS"]');

  if (!addBtn || !tbody || !tmpl || !total) return;

  function bindRemove(btn) {
    btn.addEventListener("click", function () {
      const row = this.closest("tr");
      const del = row.querySelector('input[type="checkbox"][name$="-DELETE"]');
      if (del) {
        del.checked = true;      // marca para borrar en el formset
        row.style.display = "none";
      } else {
        row.remove();            // fila recién añadida
        total.value = parseInt(total.value, 10) - 1;
      }
    });
  }

  // Enlaza botones existentes
  document.querySelectorAll("#equipos-table .btn-del-equipo").forEach(bindRemove);

  // Agregar nueva fila
  addBtn.addEventListener("click", () => {
    const idx = parseInt(total.value, 10);
    const html = tmpl.innerHTML.replace(/__prefix__/g, idx);
    const tmp = document.createElement("tbody");
    tmp.innerHTML = html.trim();
    const row = tmp.firstElementChild;
    tbody.appendChild(row);
    total.value = idx + 1;

    const delBtn = row.querySelector(".btn-del-equipo");
    if (delBtn) bindRemove(delBtn);
  });
})();
