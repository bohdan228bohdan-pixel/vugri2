// JS to toggle admin form fields visibility for SeafoodProduct in Django admin.
// Save as: static/admin/js/seafood_product_toggle.js
//
// Behavior:
// - When the "sold_in_units" checkbox is checked, show fields for price_per_unit and unit_label,
//   and hide gram-related fields such as package_size_grams and price_per_100g.
// - When unchecked, do the inverse.
// - Works on initial load and when inlines are dynamically added (best-effort).
//
// Notes:
// - Django admin wraps each field in a div with class "form-row field_<fieldname>".
//   This script relies on that structure. If your admin templates are heavily customized,
//   you may need to adjust selectors.

(function() {
  // Helper: find the admin form-row element for a model field name
  function formRowFor(fieldName) {
    return document.querySelector('.form-row.field-' + fieldName);
  }

  // Toggle visibility for lists of fields
  function setVisible(fieldNames, visible) {
    fieldNames.forEach(function(name) {
      var el = formRowFor(name);
      if (!el) return;
      el.style.display = visible ? '' : 'none';
    });
  }

  function toggleFields() {
    var soldCheckbox = document.querySelector('#id_sold_in_units');
    if (!soldCheckbox) return;
    var sold = !!soldCheckbox.checked;

    // Fields to show when selling in units
    var showUnitFields = ['price_per_unit', 'unit_label'];
    // Fields to hide when selling in units (gram-based)
    var hideGramFields = ['package_size_grams', 'price_per_100g'];

    // Apply
    setVisible(showUnitFields, sold);
    setVisible(hideGramFields, !sold);
  }

  // Initialize on DOM ready
  document.addEventListener('DOMContentLoaded', function(){
    var soldCheckbox = document.querySelector('#id_sold_in_units');
    if (!soldCheckbox) return;

    // Initial toggle
    toggleFields();

    // Toggle on change
    soldCheckbox.addEventListener('change', toggleFields);

    // Observe DOM changes (inline forms, dynamic admin behaviors)
    var observer = new MutationObserver(function() {
      // re-run toggle in case admin inserted fields dynamically
      toggleFields();
    });
    observer.observe(document.body, { childList: true, subtree: true });
  });
})();
