(function () {
  var box = document.getElementById('results'), input = document.getElementById('q');
  if (!box || !input) return;
  var root = box.dataset.root, data = null;
  function norm(s) { return (s || '').normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase(); }
  function el(tag, cls, text) { var e = document.createElement(tag); if (cls) e.className = cls; if (text) e.textContent = text; return e; }
  function section(title, items, render) {
    if (!items.length) return;
    box.appendChild(el('p', 'cta-kicker', title));
    var ul = el('ul', 'sresults');
    items.forEach(function (x) { ul.appendChild(render(x)); });
    box.appendChild(ul);
  }
  function link(href, text, meta) {
    var li = el('li'), a = el('a', null, text); a.href = root + href; li.appendChild(a);
    if (meta) li.appendChild(el('span', 'smeta', meta));
    return li;
  }
  function run() {
    var q = norm(input.value.trim());
    box.innerHTML = '';
    if (history.replaceState) history.replaceState(null, '', q ? '?q=' + encodeURIComponent(input.value.trim()) : location.pathname);
    if (!q || !data) return;
    var words = q.split(/\s+/);
    function hit(s) { s = norm(s); return words.every(function (w) { return s.indexOf(w) !== -1; }); }
    var ms = data.managers.filter(function (m) { return hit(m.n + ' ' + m.f + ' ' + m.s); });
    var cs = data.companies.filter(function (c) { return hit(c.n); });
    section('Companies', cs.slice(0, 30), function (c) { return link(c.u, c.n, c.l + (c.l === 1 ? ' letter' : ' letters')); });
    section('Managers', ms, function (m) { return link(m.u, m.n + ', ' + m.f, m.s); });
    if (!ms.length && !cs.length) box.appendChild(el('p', 'small', 'Nothing found. The company index only covers letters I’ve been able to read so far.'));
  }
  fetch(box.dataset.index).then(function (r) { return r.json(); }).then(function (d) {
    data = d;
    var p = new URLSearchParams(location.search).get('q');
    if (p) input.value = p;
    run();
  });
  input.addEventListener('input', run);
})();
