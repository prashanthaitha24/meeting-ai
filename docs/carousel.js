/* Sideways card rows (.carousel > .car-prev, .car-track, .car-next).
   Arrow buttons scroll one view of cards at a time and hide at the ends; optional
   .stage-chip buttons beside a row jump to [data-stage] cards and highlight the one in view. */
(function () {
  var carousels = Array.prototype.slice.call(document.querySelectorAll('.carousel'));
  if (!carousels.length) return;

  function chipsFor(car) { return car.parentNode.querySelectorAll('.stage-chip'); }

  function update(car) {
    var t = car.querySelector('.car-track');
    var max = t.scrollWidth - t.clientWidth;
    car.querySelector('.car-prev').hidden = t.scrollLeft <= 4;
    car.querySelector('.car-next').hidden = max <= 4 || t.scrollLeft >= max - 4;
    var chips = chipsFor(car);
    if (!chips.length) return;
    var first = null, cards = t.children;
    for (var i = 0; i < cards.length; i++) {
      if (cards[i].offsetLeft + cards[i].offsetWidth / 2 >= t.scrollLeft) { first = cards[i]; break; }
    }
    for (var j = 0; j < chips.length; j++) {
      chips[j].classList.toggle('on', !!first && chips[j].dataset.jump === first.dataset.stage);
    }
  }

  carousels.forEach(function (car) {
    var t = car.querySelector('.car-track');
    function step(dir) {
      var card = t.firstElementChild;
      var gap = parseFloat(getComputedStyle(t).columnGap) || 14;
      var w = card ? card.getBoundingClientRect().width + gap : 280;
      t.scrollBy({ left: dir * Math.max(w, Math.floor((t.clientWidth + gap) / w) * w), behavior: 'smooth' });
    }
    car.querySelector('.car-prev').addEventListener('click', function () { step(-1); });
    car.querySelector('.car-next').addEventListener('click', function () { step(1); });
    t.addEventListener('keydown', function (e) {
      if (e.target !== t) return;
      if (e.key === 'ArrowRight') { e.preventDefault(); step(1); }
      else if (e.key === 'ArrowLeft') { e.preventDefault(); step(-1); }
    });
    t.addEventListener('scroll', function () { update(car); }, { passive: true });
    Array.prototype.forEach.call(chipsFor(car), function (chip) {
      chip.addEventListener('click', function () {
        var target = t.querySelector('[data-stage="' + chip.dataset.jump + '"]');
        if (target) t.scrollTo({ left: target.offsetLeft - t.firstElementChild.offsetLeft, behavior: 'smooth' });
      });
    });
  });

  window.carUpdateAll = function () { carousels.forEach(update); };
  window.addEventListener('resize', window.carUpdateAll);
  window.addEventListener('load', window.carUpdateAll);
  window.carUpdateAll();
})();
