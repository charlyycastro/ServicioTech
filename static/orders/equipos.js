// Manejo de inline formset de equipos (agregar/eliminar filas)
document.addEventListener("DOMContentLoaded", function () {
  const container = document.getElementById("equipos-formset");
  if (!container) return;

  const tbody = document.getElementById("equipos-tbody");
  const addBtn = document.getElementById("equipos-add");
  const template = document.getElementById("equipos-empty-form");

  // Busca el TOTAL_FORMS dentro del management_form del formset
  const totalInput = container.querySelector('input[name$="-TOTAL_FORMS"]');

  function addRow() {
    const index = parseInt(totalInput.value, 10);
    const clone = document.importNode(template.content, true);

    // Reemplaza __prefix__ por el índice real
    clone.querySelectorAll("[name]").forEach((el) => {
      el.name = el.name.replace(/__prefix__/g, index);
      if (el.id) el.id = el.id.replace(/__prefix__/g, index);
      if (el.type !== "hidden" && el.type !== "checkbox") el.value = "";
      if (el.type === "checkbox") el.checked = false;
    });

    tbody.appendChild(clone);
    totalInput.value = index + 1;
  }

  function removeRow(btn) {
    const row = btn.closest("tr");
    if (!row) return;
    const del = row.querySelector('input[type="checkbox"][name$="-DELETE"]');

    if (del) {
      // fila existente: marcar DELETE y ocultar
      del.checked = true;
      row.style.display = "none";
    } else {
      // fila nueva (aún sin guardar): quitar del DOM
      row.remove();
    }
  }

  addBtn && addBtn.addEventListener("click", addRow);
  tbody && tbody.addEventListener("click", (e) => {
    if (e.target.closest(".equip-remove")) removeRow(e.target);
  });

  (function () {
  const addBtn = document.getElementById("add-equipo");
  const tbody = document.getElementById("equipos-body");
  const tmpl = document.getElementById("equipos-empty-template");
  const totalInput = document.getElementById("id_equipos-TOTAL_FORMS"); // ← ojo al id

  if (!addBtn || !tbody || !tmpl || !totalInput) return;

  function wireDelete(btn) {
    btn.addEventListener("click", () => {
      // Marca DELETE si existe el checkbox; si no, simplemente quita la fila
      const row = btn.closest("tr");
      const del = row.querySelector('input[type="checkbox"][name$="-DELETE"]');
      if (del) {
        del.checked = true;
        row.style.display = "none";
      } else {
        row.remove();
        // no tocamos TOTAL_FORMS porque solo cuenta formularios “creados”
      }
    });
  }

  // Botón agregar
  addBtn.addEventListener("click", (e) => {
    e.preventDefault();
    const index = parseInt(totalInput.value, 10);
    let html = tmpl.innerHTML.replace(/__prefix__/g, index);

    // Creamos la fila
    const temp = document.createElement("tbody");
    temp.innerHTML = html.trim();
    const newRow = temp.firstElementChild;
    tbody.appendChild(newRow);

    // Incrementa TOTAL_FORMS
    totalInput.value = index + 1;

    // Cablea el botón de borrar de la nueva fila
    const delBtn = newRow.querySelector(".btn-del-equipo");
    if (delBtn) wireDelete(delBtn);
  });

  // Cablear los existentes (si los hay)
  tbody.querySelectorAll(".btn-del-equipo").forEach(wireDelete);
})();

});
