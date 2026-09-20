(function () {
  // copy buttons
  document.querySelectorAll('[data-copy]').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var code = btn.closest('.code').querySelector('code').textContent;
      function done() { btn.textContent = 'Copied'; setTimeout(function () { btn.textContent = 'Copy'; }, 1400); }
      if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(code).then(done, done);
      else { var ta = document.createElement('textarea'); ta.value = code; document.body.appendChild(ta); ta.select(); try { document.execCommand('copy'); } catch (e) {} ta.remove(); done(); }
    });
  });

  // step ticks, stored per project in this browser only
  var KEY = 'thavionai-edu-projects';
  var pid = document.body.dataset.project;
  var all = {};
  try { all = JSON.parse(localStorage.getItem(KEY)) || {}; } catch (e) { all = {}; }
  var done = all[pid] || {};
  var boxes = document.querySelectorAll('input[data-step]');
  var chip = document.getElementById('progressChip');
  function save() { all[pid] = done; try { localStorage.setItem(KEY, JSON.stringify(all)); } catch (e) {} }
  function paint() {
    var n = 0;
    boxes.forEach(function (b) { var on = !!done[b.dataset.step]; b.checked = on; b.closest('.pj-step').classList.toggle('done', on); if (on) n++; });
    if (chip) chip.textContent = n + ' / ' + boxes.length + ' done';
  }
  boxes.forEach(function (b) {
    b.addEventListener('change', function () { if (b.checked) done[b.dataset.step] = 1; else delete done[b.dataset.step]; save(); paint(); });
  });
  paint();

  // mobile nav + scroll spy (same behaviour as lesson pages)
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
