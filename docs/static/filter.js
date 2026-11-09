(function () {
  var input = document.getElementById('filter');
  var items = document.querySelectorAll('#directory > li');
  var empty = document.getElementById('empty');
  if (!input) return;
  input.addEventListener('input', function () {
    var q = input.value.trim().toLowerCase();
    var shown = 0;
    items.forEach(function (li) {
      var hit = !q || li.getAttribute('data-search').indexOf(q) !== -1;
      li.hidden = !hit;
      if (hit) shown++;
    });
    empty.hidden = shown !== 0;
  });
})();
