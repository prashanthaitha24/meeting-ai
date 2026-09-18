// Behaviour for thavionai.com/education/<module>.html. Everything is stored in this browser only.
(function () {
  var moduleId = document.body.dataset.module;
  var PROGRESS_KEY = 'thavionai-edu-progress'; // shared with education.html
  var QUIZ_KEY = 'thavionai-edu-quiz';
  var PASS = 4;

  function load(key) {
    try { return JSON.parse(localStorage.getItem(key)) || {}; } catch (e) { return {}; }
  }
  function store(key, value) {
    try { localStorage.setItem(key, JSON.stringify(value)); } catch (e) { /* private mode etc. */ }
  }

  // Mobile nav
  var navLinks = document.getElementById('navLinks');
  document.getElementById('hamburger').addEventListener('click', function () { navLinks.classList.toggle('open'); });

  // Copy buttons
  document.querySelectorAll('[data-copy]').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var code = btn.closest('.code').querySelector('pre code').textContent;
      var done = function () { btn.textContent = 'Copied'; setTimeout(function () { btn.textContent = 'Copy'; }, 1500); };
      if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(code).then(done, function () {});
    });
  });

  // Print only the cheat sheet
  var printBtn = document.querySelector('[data-print]');
  if (printBtn) {
    printBtn.addEventListener('click', function () {
      document.body.classList.add('print-cheats');
      window.print();
    });
    window.addEventListener('afterprint', function () { document.body.classList.remove('print-cheats'); });
  }

  // Sub-nav highlight
  var subLinks = Array.prototype.slice.call(document.querySelectorAll('#subnav a'));
  var targets = subLinks.map(function (a) { return document.querySelector(a.getAttribute('href')); });
  function spy() {
    var current = 0;
    targets.forEach(function (t, i) { if (t && t.getBoundingClientRect().top < 160) current = i; });
    subLinks.forEach(function (a, i) { a.classList.toggle('on', i === current); });
  }
  window.addEventListener('scroll', spy, { passive: true });
  spy();

  // "Mark complete"
  var doneBox = document.getElementById('doneBox');
  function setDone(on) {
    var p = load(PROGRESS_KEY);
    if (on) p[moduleId] = 1; else delete p[moduleId];
    store(PROGRESS_KEY, p);
    doneBox.checked = on;
  }
  doneBox.checked = !!load(PROGRESS_KEY)[moduleId];
  doneBox.addEventListener('change', function () { setDone(doneBox.checked); });

  // Quiz
  var badge = document.querySelector('[data-quiz-badge]');
  function showBadge() {
    var best = load(QUIZ_KEY)[moduleId];
    if (typeof best !== 'number') return;
    badge.textContent = 'Best quiz score ' + best + '/5';
    badge.hidden = false;
  }
  showBadge();

  var root = document.getElementById('quizRoot');
  var questions = JSON.parse(document.getElementById('quizData').textContent);

  function shuffled(n) {
    var a = []; for (var i = 0; i < n; i++) a.push(i);
    for (var j = n - 1; j > 0; j--) { var k = Math.floor(Math.random() * (j + 1)); var t = a[j]; a[j] = a[k]; a[k] = t; }
    return a;
  }
  function el(tag, cls, text) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text != null) e.textContent = text;
    return e;
  }

  function renderQuiz() {
    root.innerHTML = '';
    var answered = 0, score = 0;
    var result = el('div', 'result'); result.hidden = true; result.setAttribute('aria-live', 'polite');

    questions.forEach(function (q, qi) {
      var box = el('div', 'q');
      box.appendChild(el('div', 'q-num', 'Question ' + (qi + 1) + ' of ' + questions.length));
      box.appendChild(el('div', 'q-text', q.q));
      var opts = el('div', 'opts'); opts.setAttribute('role', 'group'); opts.setAttribute('aria-label', 'Question ' + (qi + 1));
      var explain = el('div', 'explain'); explain.hidden = true; explain.setAttribute('aria-live', 'polite');
      var buttons = [];

      shuffled(q.options.length).forEach(function (oi, pos) {
        var b = el('button', 'opt'); b.type = 'button';
        b.appendChild(el('span', 'opt-key', 'ABCD'.charAt(pos)));
        b.appendChild(el('span', null, q.options[oi]));
        b.addEventListener('click', function () {
          var correct = oi === q.answer;
          buttons.forEach(function (x) { x.btn.disabled = true; if (x.oi === q.answer) x.btn.classList.add('right'); });
          if (!correct) b.classList.add('wrong');
          explain.innerHTML = '';
          explain.appendChild(el('b', null, correct ? 'Correct. ' : 'Not quite. '));
          explain.appendChild(document.createTextNode(q.explain));
          explain.hidden = false;
          answered++; if (correct) score++;
          if (answered === questions.length) finish();
        });
        buttons.push({ btn: b, oi: oi });
        opts.appendChild(b);
      });
      box.appendChild(opts); box.appendChild(explain);
      root.appendChild(box);
    });
    root.appendChild(result);

    function finish() {
      var all = load(QUIZ_KEY);
      if (typeof all[moduleId] !== 'number' || score > all[moduleId]) { all[moduleId] = score; store(QUIZ_KEY, all); }
      showBadge();
      var passed = score >= PASS;
      if (passed) setDone(true);
      result.className = 'result' + (passed ? ' pass' : '');
      result.innerHTML = '';
      result.appendChild(el('div', 'result-score', score + ' / ' + questions.length));
      result.appendChild(el('p', null, passed
        ? 'Passed — this module is now marked complete.'
        : 'You need ' + PASS + ' to pass. Skim the cheat sheet and the explanations above, then try again.'));
      var again = el('button', 'btn', passed ? 'Retake quiz' : 'Try again'); again.type = 'button';
      again.addEventListener('click', function () { renderQuiz(); document.getElementById('quiz').scrollIntoView(); });
      result.appendChild(again);
      result.hidden = false;
    }
  }
  renderQuiz();
})();
