(function () {
  // copy buttons (code appears in some model answers, e.g. SQL)
  document.querySelectorAll('[data-copy]').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var code = btn.closest('.code').querySelector('code').textContent;
      function done() { btn.textContent = 'Copied'; setTimeout(function () { btn.textContent = 'Copy'; }, 1400); }
      if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(code).then(done, done);
      else { var ta = document.createElement('textarea'); ta.value = code; document.body.appendChild(ta); ta.select(); try { document.execCommand('copy'); } catch (e) {} ta.remove(); done(); }
    });
  });

  // "I can answer this" ticks, stored per kit in this browser only
  var KEY = 'thavionai-edu-interview';
  var kid = document.body.dataset.kit;
  var all = {};
  try { all = JSON.parse(localStorage.getItem(KEY)) || {}; } catch (e) { all = {}; }
  var done = all[kid] || {};
  var boxes = document.querySelectorAll('input[data-q]');
  var chip = document.getElementById('progressChip');
  function save() { all[kid] = done; try { localStorage.setItem(KEY, JSON.stringify(all)); } catch (e) {} }
  function paint() {
    var n = 0;
    boxes.forEach(function (b) { var on = !!done[b.dataset.q]; b.checked = on; b.closest('.iv-q').classList.toggle('known', on); if (on) n++; });
    if (chip) chip.textContent = n + ' / ' + boxes.length + ' marked known';
  }
  boxes.forEach(function (b) {
    b.addEventListener('change', function () { if (b.checked) done[b.dataset.q] = 1; else delete done[b.dataset.q]; save(); paint(); });
  });
  paint();

  // mobile nav + scroll spy (same behaviour as lesson and project pages)
  var hb = document.getElementById('hamburger'), nl = document.getElementById('navLinks');
  if (hb && nl) hb.addEventListener('click', function () { nl.classList.toggle('open'); });
  var links = Array.prototype.slice.call(document.querySelectorAll('.subnav a'));
  var targets = links.map(function (a) { return document.querySelector(a.getAttribute('href')); }).filter(Boolean);
  function spy() {
    var y = window.scrollY + 140, cur = targets[0];
    targets.forEach(function (t) { if (t.offsetTop <= y) cur = t; });
    links.forEach(function (a) { a.classList.toggle('on', cur && a.getAttribute('href') === '#' + cur.id); });
  }
  window.addEventListener('scroll', spy, { passive: true }); spy();
})();
