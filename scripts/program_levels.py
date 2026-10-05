"""Medium, Advanced and Pro levels of the home-practice program.

Each skill ("kind") is a small generator that returns problems as plain dicts:
  {"t": "q", "q": "34 + 25 = □", "ans": "59"}            drill (□ marks the answer box)
  {"t": "story", "text": "...", "ans": "12", "illus": False} word problem
Answers are computed exactly (fractions with Fraction, money in cents, decimals
rounded explicitly) so every answer key is correct by construction.

build_program.py imports LEVELS_MORE, KINDS and level_intro() from here.
"""
import math
import random
from fractions import Fraction

NAMES = ["Sam", "Mia", "Aria", "Leo", "Noah", "Zoe", "Ravi", "Ana", "Kai", "Lily",
         "Omar", "Ella", "Tara", "Finn", "Maya", "Jack"]
BOX = "□"  # □


def q(text, ans):
    return {"t": "q", "q": text, "ans": str(ans)}


def story(text, ans):
    return {"t": "story", "text": text, "ans": str(ans), "illus": False}


def names(rnd):
    return rnd.sample(NAMES, 2)


def money(cents):
    return f"${cents // 100}.{cents % 100:02d}"


def dec(x, places):
    """Format a float-free decimal from an integer count of 10^-places units."""
    s = f"{x / 10 ** places:.{places}f}"
    return s.rstrip("0").rstrip(".") if "." in s else s


def frac(f: Fraction):
    if f.denominator == 1:
        return str(f.numerator)
    whole, rem = divmod(f.numerator, f.denominator)
    if whole and rem:
        return f"{whole} {rem}/{f.denominator}"
    return f"{f.numerator}/{f.denominator}"


# ------------------------------------------------------------------ MEDIUM skills

def k_skip(rnd, hi):
    step = rnd.choice([2, 5, 10]) if hi < 100 else 10
    start = step * rnd.randint(0, max(1, hi // step - 6))
    terms = [start + step * i for i in range(6)]
    b = rnd.randint(2, 5)
    shown = [BOX if i == b else str(t) for i, t in enumerate(terms)]
    return q(", ".join(shown), terms[b])


def s_skip(rnd, hi):
    n1, _ = names(rnd)
    k, step = rnd.randint(3, 9), rnd.choice([2, 5, 10])
    return story(f"{n1} puts {step} stickers on each page. How many stickers are on {k} pages?", k * step)


def k_pv2(rnd, hi):
    n = rnd.randint(11, 99)
    ones = f"{n % 10} one" + ("" if n % 10 == 1 else "s")
    if rnd.random() < 0.5:
        return q(f"{n} = {BOX} tens and {ones}", n // 10)
    tens = f"{n // 10} ten" + ("" if n // 10 == 1 else "s")
    return q(f"{tens} and {ones} = {BOX}", n)


def s_pv2(rnd, hi):
    n1, _ = names(rnd)
    t, o = rnd.randint(2, 9), rnd.randint(0, 9)
    return story(f"{n1} has {t} bags of 10 marbles and {o} loose marbles. How many marbles in all?", 10 * t + o)


def k_pv3(rnd, hi):
    n = rnd.randint(101, 999)
    h, t, o = n // 100, n // 10 % 10, n % 10
    form = rnd.randint(0, 2)
    if form == 0:
        hs = f"{h} hundred" + ("" if h == 1 else "s")
        return q(f"{n} = {hs}, {BOX} tens and {o} one" + ("" if o == 1 else "s"), t)
    if form == 1:
        return q(f"{h * 100} + {t * 10} + {o} = {BOX}", n)
    d = rnd.choice([0, 1, 2])
    digit, value = [(h, h * 100), (t, t * 10), (o, o)][d]
    return q(f"In {n}, the digit {digit} is worth {BOX}", value)


def s_pv3(rnd, hi):
    n1, _ = names(rnd)
    h, t, o = rnd.randint(1, 9), rnd.randint(0, 9), rnd.randint(0, 9)
    return story(f"A shop has {h} boxes of 100 pencils, {t} packs of 10 and {o} single pencils. "
                 f"How many pencils does the shop have?", 100 * h + 10 * t + o)


def k_cmp(rnd, hi):
    a, b = rnd.randint(10, hi), rnd.randint(10, hi)
    if rnd.random() < 0.15:
        b = a
    sign = ">" if a > b else ("<" if a < b else "=")
    return q(f"{a} {BOX} {b}   (write >, < or =)", sign)


def s_cmp(rnd, hi):
    n1, n2 = names(rnd)
    a, b = rnd.sample(range(10, hi), 2)
    who = n1 if a > b else n2
    return story(f"{n1} scored {a} points and {n2} scored {b} points. Who scored more?", who)


def k_addtens(rnd, hi):
    a, b = rnd.randint(1, 8) * 10, 0
    b = rnd.randint(1, 9 - a // 10) * 10
    if rnd.random() < 0.5:
        return q(f"{a} + {b} = {BOX}", a + b)
    return q(f"{a + b} - {b} = {BOX}", a)


def add2(rnd, hi, carry):
    while True:
        a, b = rnd.randint(10, hi - 10), rnd.randint(10, hi - 10)
        if a + b > hi:
            continue
        has_carry = (a % 10 + b % 10) >= 10
        if has_carry == carry:
            return a, b


def sub2(rnd, hi, borrow):
    while True:
        a, b = rnd.randint(20, hi), rnd.randint(10, hi - 10)
        if b >= a:
            continue
        needs = (a % 10) < (b % 10)
        if needs == borrow:
            return a, b


def k_add_nc(rnd, hi):
    a, b = add2(rnd, hi, False)
    return q(f"{a} + {b} = {BOX}", a + b)


def k_add_c(rnd, hi):
    a, b = add2(rnd, hi, True)
    return q(f"{a} + {b} = {BOX}", a + b)


def k_sub_nb(rnd, hi):
    a, b = sub2(rnd, hi, False)
    return q(f"{a} - {b} = {BOX}", a - b)


def k_sub_b(rnd, hi):
    a, b = sub2(rnd, hi, True)
    return q(f"{a} - {b} = {BOX}", a - b)


ADD_STORIES = [
    "{n1} read {a} pages last week and {b} pages this week. How many pages in all?",
    "A farm has {a} sheep and {b} goats. How many animals is that altogether?",
    "{n1} walked {a} metres to the shop and {b} metres to the park. How far did {n1} walk?",
    "The school collected {a} cans on Monday and {b} on Tuesday. How many cans were collected?",
    "A train has {a} people in the front carriages and {b} in the back. How many people are on the train?",
]
SUB_STORIES = [
    "A library had {a} books and lent out {b}. How many books are left?",
    "{n1} had {a} stickers and gave {b} to {n2}. How many stickers does {n1} have now?",
    "There were {a} seats in the hall and {b} are taken. How many seats are free?",
    "A baker made {a} rolls and sold {b}. How many rolls are left?",
    "{n1} needs {a} points to win and has {b}. How many more points does {n1} need?",
]


def s_add(rnd, hi):
    n1, n2 = names(rnd)
    a, b = add2(rnd, hi, rnd.random() < 0.5)
    return story(rnd.choice(ADD_STORIES).format(n1=n1, n2=n2, a=a, b=b), a + b)


def s_sub(rnd, hi):
    n1, n2 = names(rnd)
    a, b = sub2(rnd, hi, rnd.random() < 0.5)
    return story(rnd.choice(SUB_STORIES).format(n1=n1, n2=n2, a=a, b=b), a - b)


def k_mix2(rnd, hi):
    return (k_add_c if rnd.random() < 0.5 else k_sub_b)(rnd, hi)


def s_mix2(rnd, hi):
    return (s_add if rnd.random() < 0.5 else s_sub)(rnd, hi)


def k_add3(rnd, hi):
    a = rnd.randint(100, 899)
    b = rnd.randint(100, 999 - a) if a < 899 else 100
    return q(f"{a} + {b} = {BOX}", a + b)


def k_sub3(rnd, hi):
    a = rnd.randint(200, 999)
    b = rnd.randint(100, a - 1)
    return q(f"{a} - {b} = {BOX}", a - b)


def s_add3(rnd, hi):
    n1, n2 = names(rnd)
    a = rnd.randint(100, 499)
    b = rnd.randint(100, 499)
    return story(rnd.choice(ADD_STORIES).format(n1=n1, n2=n2, a=a, b=b), a + b)


def s_sub3(rnd, hi):
    n1, n2 = names(rnd)
    a = rnd.randint(300, 999)
    b = rnd.randint(100, a - 50)
    return story(rnd.choice(SUB_STORIES).format(n1=n1, n2=n2, a=a, b=b), a - b)


def k_dbl(rnd, hi):
    n = rnd.randint(2, 50)
    if rnd.random() < 0.5:
        return q(f"Double {n} = {BOX}", 2 * n)
    return q(f"Half of {2 * n} = {BOX}", n)


def s_dbl(rnd, hi):
    n1, n2 = names(rnd)
    n = rnd.randint(3, 40)
    if rnd.random() < 0.5:
        return story(f"{n1} has {n} cards. {n2} has double that. How many cards does {n2} have?", 2 * n)
    return story(f"{n1} and {n2} share {2 * n} grapes equally. How many grapes does each get?", n)


def tables(ts):
    def k(rnd, hi):
        a, b = rnd.choice(ts), rnd.randint(1, 10 if max(ts) <= 10 else 12)
        if rnd.random() < 0.5:
            a, b = b, a
        if rnd.random() < 0.2:
            return q(f"{a} x {BOX} = {a * b}", b)
        return q(f"{a} x {b} = {BOX}", a * b)
    return k


def stables(ts):
    def s(rnd, hi):
        n1, _ = names(rnd)
        a, b = rnd.choice(ts), rnd.randint(2, 10)
        tpl = rnd.choice([
            "There are {b} bags with {a} oranges in each. How many oranges are there?",
            "{n1} buys {b} packs of {a} pens. How many pens is that?",
            "A table seats {a} people. How many people can sit at {b} tables?",
            "Each bike has {a} lights. How many lights are on {b} bikes?",
        ])
        return story(tpl.format(n1=n1, a=a, b=b), a * b)
    return s


COINS = [1, 5, 10, 25, 100, 500]  # cents: penny, nickel, dime, quarter, $1, $5


def k_money_count(rnd, hi):
    picks = sorted(rnd.choices(COINS[:5], k=rnd.randint(2, 4)), reverse=True)
    label = {1: "1c", 5: "5c", 10: "10c", 25: "25c", 100: "$1"}
    return q(" + ".join(label[c] for c in picks) + f" = {BOX}", money(sum(picks)))


def k_money(rnd, hi):
    a, b = rnd.randint(1, 40) * 25, rnd.randint(1, 40) * 25
    if rnd.random() < 0.5:
        return q(f"{money(a)} + {money(b)} = {BOX}", money(a + b))
    big, small = max(a, b) + 100, min(a, b)
    return q(f"{money(big)} - {money(small)} = {BOX}", money(big - small))


def s_money(rnd, hi):
    n1, _ = names(rnd)
    price = rnd.randint(2, 30) * 25
    paid = (price // 500 + 1) * 500
    if rnd.random() < 0.5:
        return story(f"{n1} buys a book for {money(price)} and pays with {money(paid)}. How much change?",
                     money(paid - price))
    p2 = rnd.randint(2, 20) * 25
    return story(f"A sandwich costs {money(price)} and a juice costs {money(p2)}. How much for both?",
                 money(price + p2))


def k_time(rnd, hi):
    h, m = rnd.randint(1, 11), rnd.choice(range(0, 60, 5))
    add = rnd.choice([5, 10, 15, 20, 25, 30, 45])
    t = h * 60 + m + add
    nh, nm = (t // 60 - 1) % 12 + 1, t % 60
    return q(f"{add} minutes after {h}:{m:02d} is {BOX}", f"{nh}:{nm:02d}")


def s_time(rnd, hi):
    n1, _ = names(rnd)
    h, m = rnd.randint(1, 10), rnd.choice([0, 15, 30, 45])
    d = rnd.choice([15, 20, 30, 40, 45])
    t = h * 60 + m + d
    return story(f"{n1} starts football practice at {h}:{m:02d}. It lasts {d} minutes. What time does it end?",
                 f"{(t // 60 - 1) % 12 + 1}:{t % 60:02d}")


def k_measure(rnd, hi):
    a, b = rnd.randint(10, 90), rnd.randint(5, 60)
    unit = rnd.choice(["cm", "m", "kg", "L"])
    if rnd.random() < 0.5 or b >= a:
        return q(f"{a} {unit} + {b} {unit} = {BOX} {unit}", a + b)
    return q(f"{a} {unit} - {b} {unit} = {BOX} {unit}", a - b)


def s_measure(rnd, hi):
    n1, _ = names(rnd)
    a, b = rnd.randint(40, 95), rnd.randint(5, 35)
    tpl = rnd.choice([
        ("A ribbon is {a} cm long. {n1} cuts off {b} cm. How long is the ribbon now (cm)?", a - b),
        ("{n1} is {a} cm tall and grows {b} cm. How tall is {n1} now (cm)?", a + b),
        ("A jug holds {a} L of water. {b} L is poured out. How many litres are left?", a - b),
    ])
    return story(tpl[0].format(n1=n1, a=a, b=b), tpl[1])


# ------------------------------------------------------------------ ADVANCED skills

def k_mul21(rnd, hi):
    a, b = rnd.randint(12, 99), rnd.randint(2, 9)
    return q(f"{a} x {b} = {BOX}", a * b)


def k_mul31(rnd, hi):
    a, b = rnd.randint(102, 999), rnd.randint(2, 9)
    return q(f"{a} x {b} = {BOX}", a * b)


def k_mul22(rnd, hi):
    a, b = rnd.randint(11, 99), rnd.randint(11, 49)
    return q(f"{a} x {b} = {BOX}", a * b)


def s_mul(rnd, hi):
    n1, _ = names(rnd)
    a, b = rnd.randint(12, 60), rnd.randint(3, 9)
    tpl = rnd.choice([
        "A cinema has {b} rows with {a} seats in each. How many seats are there?",
        "{n1} saves {a} dollars every week for {b} weeks. How much does {n1} save?",
        "A crate holds {a} bottles. How many bottles are in {b} crates?",
    ])
    return story(tpl.format(n1=n1, a=a, b=b), a * b)


def k_div(rnd, hi):
    b, c = rnd.randint(2, 12), rnd.randint(2, 12)
    return q(f"{b * c} ÷ {b} = {BOX}", c)


def k_divr(rnd, hi):
    b = rnd.randint(2, 9)
    c, r = rnd.randint(3, 12), rnd.randint(1, b - 1)
    return q(f"{b * c + r} ÷ {b} = {BOX} r {BOX}", f"{c} r {r}")


def k_longdiv(rnd, hi):
    b = rnd.randint(2, 9)
    c = rnd.randint(21, 199)
    return q(f"{b * c} ÷ {b} = {BOX}", c)


def s_div(rnd, hi):
    n1, _ = names(rnd)
    b, c = rnd.randint(3, 9), rnd.randint(4, 15)
    if rnd.random() < 0.5:
        return story(f"{b * c} children are split into {b} equal teams. How many children are in each team?", c)
    r = rnd.randint(1, b - 1)
    return story(f"{n1} packs {b * c + r} eggs into boxes of {b}. How many full boxes, and how many eggs are left over?",
                 f"{c} boxes, {r} left")


def k_fracname(rnd, hi):
    d = rnd.choice([2, 3, 4, 5, 6, 8, 10])
    n = rnd.randint(1, d - 1)
    return q(f"{n} of {d} equal parts are shaded: fraction = {BOX}", f"{n}/{d}")


def k_fracof(rnd, hi):
    d = rnd.choice([2, 3, 4, 5, 6, 8, 10])
    n = rnd.randint(1, d - 1)
    m = d * rnd.randint(2, 10)
    return q(f"{n}/{d} of {m} = {BOX}", m * n // d)


def s_fracof(rnd, hi):
    n1, _ = names(rnd)
    d = rnd.choice([2, 3, 4, 5])
    n = rnd.randint(1, d - 1)
    m = d * rnd.randint(3, 10)
    return story(f"{n1} has {m} marbles and gives away {n}/{d} of them. How many marbles does {n1} give away?",
                 m * n // d)


def k_fracequiv(rnd, hi):
    d = rnd.choice([2, 3, 4, 5])
    n = rnd.randint(1, d - 1)
    k = rnd.randint(2, 5)
    return q(f"{n}/{d} = {BOX}/{d * k}", n * k)


def k_fraccmp(rnd, hi):
    if rnd.random() < 0.5:
        d = rnd.choice([5, 6, 8, 10, 12])
        a, b = rnd.sample(range(1, d), 2)
        fa, fb = Fraction(a, d), Fraction(b, d)
        text = f"{a}/{d} {BOX} {b}/{d}"
    else:
        n = rnd.randint(1, 3)
        da, db = rnd.sample([2, 3, 4, 5, 6, 8], 2)
        if n >= min(da, db):
            n = 1
        fa, fb = Fraction(n, da), Fraction(n, db)
        text = f"{n}/{da} {BOX} {n}/{db}"
    return q(text + "   (>, < or =)", ">" if fa > fb else ("<" if fa < fb else "="))


def k_fracadd(rnd, hi):
    d = rnd.choice([4, 5, 6, 8, 10, 12])
    a, b = rnd.randint(1, d - 1), rnd.randint(1, d - 1)
    return q(f"{a}/{d} + {b}/{d} = {BOX}", frac(Fraction(a + b, d)))


def k_fracsub(rnd, hi):
    d = rnd.choice([4, 5, 6, 8, 10, 12])
    a, b = sorted(rnd.sample(range(1, d + 4), 2), reverse=True)
    return q(f"{a}/{d} - {b}/{d} = {BOX}", frac(Fraction(a - b, d)))


def s_fracadd(rnd, hi):
    n1, n2 = names(rnd)
    d = rnd.choice([4, 6, 8])
    a, b = rnd.randint(1, d // 2), rnd.randint(1, d // 2)
    return story(f"{n1} eats {a}/{d} of a pizza and {n2} eats {b}/{d}. What fraction of the pizza did they eat?",
                 frac(Fraction(a + b, d)))


def k_mixed(rnd, hi):
    d = rnd.choice([2, 3, 4, 5, 6, 8])
    w, n = rnd.randint(1, 5), rnd.randint(1, d - 1)
    if rnd.random() < 0.5:
        return q(f"{w} {n}/{d} = {BOX}/{d}", w * d + n)
    return q(f"{w * d + n}/{d} = {BOX} (as a mixed number)", f"{w} {n}/{d}")


def k_multistep_as(rnd, hi):
    a, b, c = rnd.randint(100, 500), rnd.randint(20, 200), rnd.randint(10, 90)
    return q(f"{a} + {b} - {c} = {BOX}", a + b - c)


def s_multistep_as(rnd, hi):
    n1, _ = names(rnd)
    a, b, c = rnd.randint(150, 600), rnd.randint(20, 120), rnd.randint(10, 100)
    return story(f"A school has {a} pupils. {b} new pupils join and {c} leave. How many pupils now?", a + b - c)


def k_multistep_md(rnd, hi):
    a, b, c = rnd.randint(3, 9), rnd.randint(4, 12), rnd.choice([2, 3, 4, 6])
    tot = a * b * c
    return q(f"{tot} ÷ {c} ÷ {a} = {BOX}", b)


def s_multistep_md(rnd, hi):
    n1, _ = names(rnd)
    packs, per, share = rnd.randint(3, 8), rnd.choice([6, 8, 10, 12]), rnd.choice([2, 3, 4])
    while (packs * per) % share:
        packs += 1
    return story(f"{n1} buys {packs} packs of {per} cookies and shares them equally among {share} friends. "
                 f"How many cookies does each friend get?", packs * per // share)


def k_areaper(rnd, hi):
    w, h = rnd.randint(2, 15), rnd.randint(2, 15)
    if rnd.random() < 0.5:
        return q(f"Area of a {w} cm by {h} cm rectangle = {BOX} sq cm", w * h)
    return q(f"Perimeter of a {w} cm by {h} cm rectangle = {BOX} cm", 2 * (w + h))


def s_areaper(rnd, hi):
    w, h = rnd.randint(3, 12), rnd.randint(3, 12)
    if rnd.random() < 0.5:
        return story(f"A garden is {w} m long and {h} m wide. How many metres of fence go all the way around?",
                     2 * (w + h))
    return story(f"A floor is {w} m by {h} m. How many square metres of carpet are needed?", w * h)


def k_factors(rnd, hi):
    if rnd.random() < 0.5:
        n = rnd.choice([12, 16, 18, 20, 24, 28, 30, 32, 36, 40, 42, 48])
        fs = [d for d in range(1, n + 1) if n % d == 0]
        return q(f"How many factors does {n} have? {BOX}", len(fs))
    a = rnd.randint(3, 12)
    k = rnd.randint(3, 9)
    return q(f"The {k}th multiple of {a} is {BOX}", a * k)


def k_round(rnd, hi):
    n = rnd.randint(101, 9999)
    to = rnd.choice([10, 100, 1000])
    r = int(math.floor(n / to + 0.5)) * to
    return q(f"Round {n} to the nearest {to}: {BOX}", r)


def k_pattern(rnd, hi):
    start, step = rnd.randint(1, 30), rnd.choice([3, 4, 6, 7, 9, 11, 15, 25])
    if rnd.random() < 0.3:
        start += 60
        step = -step
    terms = [start + step * i for i in range(5)]
    return q(", ".join(map(str, terms[:4])) + f", {BOX}", terms[4])


def k_elapsed(rnd, hi):
    h1, m1 = rnd.randint(7, 11), rnd.choice(range(0, 60, 5))
    dur = rnd.choice([25, 35, 40, 50, 65, 75, 90, 105])
    t2 = h1 * 60 + m1 + dur
    return q(f"From {h1}:{m1:02d} to {(t2 // 60 - 1) % 12 + 1}:{t2 % 60:02d} is {BOX} minutes", dur)


# ------------------------------------------------------------------ PRO skills

def k_decpv(rnd, hi):
    n = rnd.randint(1001, 99999)  # hundredths
    s = f"{n // 100}.{n % 100:02d}"
    which = rnd.choice(["tenths", "hundredths"])
    digit = (n // 10) % 10 if which == "tenths" else n % 10
    return q(f"In {s}, the {which} digit is {BOX}", digit)


def k_decadd(rnd, hi):
    a, b = rnd.randint(11, 999), rnd.randint(11, 999)  # hundredths
    return q(f"{a // 100}.{a % 100:02d} + {b // 100}.{b % 100:02d} = {BOX}", f"{(a + b) // 100}.{(a + b) % 100:02d}")


def k_decsub(rnd, hi):
    a, b = sorted(rnd.sample(range(11, 999), 2), reverse=True)
    return q(f"{a // 100}.{a % 100:02d} - {b // 100}.{b % 100:02d} = {BOX}", f"{(a - b) // 100}.{(a - b) % 100:02d}")


def s_dec(rnd, hi):
    n1, _ = names(rnd)
    a, b = rnd.randint(105, 950), rnd.randint(105, 950)
    if rnd.random() < 0.5:
        return story(f"{n1} runs {a // 100}.{a % 100:02d} km on Monday and {b // 100}.{b % 100:02d} km on Tuesday. "
                     f"How far in total (km)?", f"{(a + b) // 100}.{(a + b) % 100:02d}")
    big, small = max(a, b), min(a, b)
    return story(f"A bottle holds {big // 100}.{big % 100:02d} L. {n1} pours out {small // 100}.{small % 100:02d} L. "
                 f"How much is left (L)?", f"{(big - small) // 100}.{(big - small) % 100:02d}")


def k_decmul(rnd, hi):
    a, b = rnd.randint(11, 99), rnd.randint(2, 9)  # a in tenths
    p = a * b
    return q(f"{a // 10}.{a % 10} x {b} = {BOX}", f"{p // 10}.{p % 10}")


def k_pow10(rnd, hi):
    n = rnd.randint(11, 9999)  # hundredths
    s = f"{n // 100}.{n % 100:02d}"
    f = rnd.choice([10, 100, 1000])
    if rnd.random() < 0.5:
        return q(f"{s} x {f} = {BOX}", decimal_str(Fraction(n, 100) * f))
    return q(f"{s} ÷ {f} = {BOX}", decimal_str(Fraction(n, 100) / f))


def decimal_str(f: Fraction) -> str:
    """Exact decimal string for a fraction with a power-of-ten-friendly denominator."""
    places = 0
    while (f * 10 ** places).denominator != 1:
        places += 1
        if places > 8:
            break
    scaled = int(f * 10 ** places)
    if places == 0:
        return str(scaled)
    sign = "-" if scaled < 0 else ""
    scaled = abs(scaled)
    s = f"{scaled // 10 ** places}.{scaled % 10 ** places:0{places}d}".rstrip("0").rstrip(".")
    return sign + s


def k_fracdec(rnd, hi):
    f = rnd.choice([Fraction(1, 2), Fraction(1, 4), Fraction(3, 4), Fraction(1, 5), Fraction(2, 5),
                    Fraction(3, 5), Fraction(4, 5), Fraction(1, 10), Fraction(7, 10), Fraction(3, 20),
                    Fraction(1, 8), Fraction(3, 8)])
    if rnd.random() < 0.5:
        return q(f"{f.numerator}/{f.denominator} as a decimal = {BOX}", decimal_str(f))
    return q(f"{decimal_str(f)} as a fraction in lowest terms = {BOX}", f"{f.numerator}/{f.denominator}")


def k_fracunlike(rnd, hi):
    da, db = rnd.sample([2, 3, 4, 5, 6, 8, 10, 12], 2)
    a, b = rnd.randint(1, da - 1), rnd.randint(1, db - 1)
    r = Fraction(a, da) + Fraction(b, db)
    return q(f"{a}/{da} + {b}/{db} = {BOX}", frac(r))


def k_fracmul(rnd, hi):
    a, b = Fraction(rnd.randint(1, 5), rnd.randint(2, 9)), Fraction(rnd.randint(1, 5), rnd.randint(2, 9))
    a, b = Fraction(a.numerator % a.denominator or 1, a.denominator), Fraction(b.numerator % b.denominator or 1, b.denominator)
    return q(f"{a.numerator}/{a.denominator} x {b.numerator}/{b.denominator} = {BOX}", frac(a * b))


def k_fracdiv(rnd, hi):
    a = Fraction(rnd.randint(1, 7), rnd.choice([2, 3, 4, 5, 6, 8]))
    if a >= 1:
        a = Fraction(1, a.denominator)
    if rnd.random() < 0.5:
        w = rnd.randint(2, 6)
        return q(f"{a.numerator}/{a.denominator} ÷ {w} = {BOX}", frac(a / w))
    b = Fraction(1, rnd.choice([2, 3, 4, 5]))
    return q(f"{a.numerator}/{a.denominator} ÷ {b.numerator}/{b.denominator} = {BOX}", frac(a / b))


def s_frac(rnd, hi):
    n1, _ = names(rnd)
    d = rnd.choice([3, 4, 5, 8])
    n = rnd.randint(1, d - 1)
    m = d * rnd.randint(4, 15)
    return story(f"A {m}-page book: {n1} has read {n}/{d} of it. How many pages are left to read?", m - m * n // d)


def k_pct(rnd, hi):
    p = rnd.choice([10, 20, 25, 50, 75, 5, 15, 30, 40])
    n = rnd.choice([20, 40, 60, 80, 120, 200, 240, 300, 360, 400, 500, 800])
    return q(f"{p}% of {n} = {BOX}", decimal_str(Fraction(p * n, 100)))


def k_pctconv(rnd, hi):
    p = rnd.choice([5, 10, 20, 25, 40, 50, 60, 75, 80])
    f = Fraction(p, 100)
    form = rnd.randint(0, 2)
    if form == 0:
        return q(f"{p}% as a decimal = {BOX}", decimal_str(f))
    if form == 1:
        return q(f"{p}% as a fraction in lowest terms = {BOX}", f"{f.numerator}/{f.denominator}")
    return q(f"{decimal_str(f)} as a percent = {BOX}%", p)


def s_pct(rnd, hi):
    n1, _ = names(rnd)
    price = rnd.choice([20, 40, 60, 80, 120, 150, 200])
    off = rnd.choice([10, 20, 25, 50])
    sale = Fraction(price * (100 - off), 100)
    return story(f"A jacket costs ${price}. It is {off}% off in the sale. What is the sale price in dollars?",
                 decimal_str(sale))


def k_ratiosimp(rnd, hi):
    a, b = rnd.randint(1, 9), rnd.randint(1, 9)
    g = math.gcd(a, b)
    a, b = a // g, b // g
    k = rnd.randint(2, 9)
    return q(f"Simplify {a * k}:{b * k} = {BOX}", f"{a}:{b}")


def k_ratioshare(rnd, hi):
    a, b = rnd.randint(1, 5), rnd.randint(1, 5)
    tot = (a + b) * rnd.randint(2, 12)
    return q(f"Share {tot} in the ratio {a}:{b} -> first share = {BOX}", tot * a // (a + b))


def s_ratio(rnd, hi):
    n1, n2 = names(rnd)
    a, b = rnd.randint(1, 4), rnd.randint(1, 4)
    tot = (a + b) * rnd.randint(3, 10)
    return story(f"{n1} and {n2} share ${tot} in the ratio {a}:{b}. How many dollars does {n2} get?",
                 tot * b // (a + b))


def k_rate(rnd, hi):
    n, unit = rnd.randint(2, 12), rnd.choice([3, 4, 5, 6, 8])
    total = n * unit * 25  # cents
    return q(f"{n} pens cost {money(total)}. One pen costs {BOX}", money(total // n))


def s_rate(rnd, hi):
    n1, _ = names(rnd)
    speed, hrs = rnd.choice([40, 45, 50, 60, 80]), rnd.randint(2, 6)
    return story(f"{n1}'s train travels at {speed} km per hour for {hrs} hours. How far does it go (km)?",
                 speed * hrs)


def k_bodmas(rnd, hi):
    a, b, c, d = rnd.randint(2, 12), rnd.randint(2, 9), rnd.randint(2, 9), rnd.randint(1, 20)
    form = rnd.randint(0, 2)
    if form == 0:
        return q(f"{d} + {b} x {c} = {BOX}", d + b * c)
    if form == 1:
        return q(f"({d} + {b}) x {c} = {BOX}", (d + b) * c)
    return q(f"{a * b} ÷ {b} + {c} x {c} = {BOX}", a + c * c)


def k_neg(rnd, hi):
    a, b = rnd.randint(-20, 20), rnd.randint(-20, 20)
    op = rnd.choice(["+", "-"])
    r = a + b if op == "+" else a - b
    bs = f"({b})" if b < 0 else str(b)
    return q(f"{a} {op} {bs} = {BOX}", r)


def s_neg(rnd, hi):
    t, drop = rnd.randint(-5, 8), rnd.randint(3, 15)
    return story(f"At noon it is {t} degrees. By midnight the temperature falls {drop} degrees. "
                 f"What is the temperature at midnight?", t - drop)


def k_eval(rnd, hi):
    x, a, b = rnd.randint(1, 12), rnd.randint(2, 9), rnd.randint(1, 20)
    if rnd.random() < 0.5:
        return q(f"If x = {x}, then {a}x + {b} = {BOX}", a * x + b)
    return q(f"If x = {x}, then {a}(x - 1) = {BOX}", a * (x - 1))


def k_eq1(rnd, hi):
    x, a = rnd.randint(2, 30), rnd.randint(2, 12)
    form = rnd.randint(0, 2)
    if form == 0:
        return q(f"x + {a} = {x + a}, x = {BOX}", x)
    if form == 1:
        return q(f"x - {a} = {x - a}, x = {BOX}", x)
    return q(f"{a}x = {a * x}, x = {BOX}", x)


def k_eq2(rnd, hi):
    x, a, b = rnd.randint(1, 15), rnd.randint(2, 9), rnd.randint(1, 30)
    if rnd.random() < 0.5:
        return q(f"{a}x + {b} = {a * x + b}, x = {BOX}", x)
    return q(f"{a}x - {b} = {a * x - b}, x = {BOX}", x)


def s_eq(rnd, hi):
    n1, _ = names(rnd)
    x, a, b = rnd.randint(2, 15), rnd.randint(2, 6), rnd.randint(1, 20)
    return story(f"{n1} thinks of a number, multiplies it by {a} and adds {b}. The answer is {a * x + b}. "
                 f"What was the number?", x)


def k_pow(rnd, hi):
    if rnd.random() < 0.5:
        b, e = rnd.randint(2, 10), rnd.choice([2, 2, 3])
        return q(f"{b}^{e} = {BOX}", b ** e)
    n = rnd.randint(2, 15)
    return q(f"The square root of {n * n} = {BOX}", n)


def k_hcflcm(rnd, hi):
    a, b = rnd.sample([4, 6, 8, 9, 10, 12, 14, 15, 16, 18, 20, 24], 2)
    if rnd.random() < 0.5:
        return q(f"Highest common factor of {a} and {b} = {BOX}", math.gcd(a, b))
    return q(f"Lowest common multiple of {a} and {b} = {BOX}", a * b // math.gcd(a, b))


def k_area2(rnd, hi):
    b, h = rnd.randint(2, 20), rnd.randint(2, 20)
    if rnd.random() < 0.5:
        return q(f"Triangle: base {b} cm, height {h} cm. Area = {BOX} sq cm", decimal_str(Fraction(b * h, 2)))
    return q(f"Parallelogram: base {b} cm, height {h} cm. Area = {BOX} sq cm", b * h)


def k_volume(rnd, hi):
    l, w, h = rnd.randint(2, 12), rnd.randint(2, 10), rnd.randint(2, 10)
    return q(f"Cuboid {l} cm x {w} cm x {h} cm: volume = {BOX} cubic cm", l * w * h)


def s_volume(rnd, hi):
    l, w, h = rnd.randint(3, 10), rnd.randint(2, 8), rnd.randint(2, 6)
    return story(f"A box is {l} cm long, {w} cm wide and {h} cm high. How many 1 cm cubes fill it?", l * w * h)


def k_stats(rnd, hi):
    data = [rnd.randint(1, 20) for _ in range(rnd.choice([5, 5, 7]))]
    while sum(data) % len(data):
        data[0] += 1
    which = rnd.choice(["mean", "median", "range"])
    s = ", ".join(map(str, data))
    if which == "mean":
        return q(f"Mean of {s} = {BOX}", sum(data) // len(data))
    if which == "median":
        return q(f"Median of {s} = {BOX}", sorted(data)[len(data) // 2])
    return q(f"Range of {s} = {BOX}", max(data) - min(data))


def s_stats(rnd, hi):
    n1, _ = names(rnd)
    scores = [rnd.randint(5, 20) for _ in range(4)]
    while sum(scores) % 4:
        scores[0] += 1
    return story(f"{n1} scored {', '.join(map(str, scores))} in four games. What is the mean score?",
                 sum(scores) // 4)


# ------------------------------------------------------------------ registry and plans

# kind: (section heading, grid class, drill generator, story generator)
KINDS = {
    "skip": ("Fill in the missing number", "wide", k_skip, s_skip),
    "pv2": ("Tens and ones", "wide", k_pv2, s_pv2),
    "pv3": ("Hundreds, tens and ones", "wide", k_pv3, s_pv3),
    "cmp100": ("Compare: write >, < or =", "wide", k_cmp, s_cmp),
    "cmp1000": ("Compare: write >, < or =", "wide", k_cmp, s_cmp),
    "addtens": ("Add and subtract tens", "num", k_addtens, s_add),
    "add_nc": ("Add", "num", k_add_nc, s_add),
    "add_c": ("Add (you may need to regroup)", "num", k_add_c, s_add),
    "sub_nb": ("Subtract", "num", k_sub_nb, s_sub),
    "sub_b": ("Subtract (you may need to regroup)", "num", k_sub_b, s_sub),
    "mix2": ("Add and subtract", "num", k_mix2, s_mix2),
    "add3": ("Add 3-digit numbers", "num", k_add3, s_add3),
    "sub3": ("Subtract 3-digit numbers", "num", k_sub3, s_sub3),
    "dbl": ("Doubles and halves", "wide", k_dbl, s_dbl),
    "t2510": ("Times tables: 2, 5 and 10", "num", tables([2, 5, 10]), stables([2, 5, 10])),
    "t34": ("Times tables: 3 and 4", "num", tables([3, 4]), stables([3, 4])),
    "tmix": ("Times tables", "num", tables([2, 3, 4, 5, 10]), stables([2, 3, 4, 5, 10])),
    "coins": ("Count the money", "wide", k_money_count, s_money),
    "money": ("Add and subtract money", "wide", k_money, s_money),
    "time": ("Time: what time will it be?", "wide", k_time, s_time),
    "measure": ("Measures: add and subtract", "wide", k_measure, s_measure),
    "t67": ("Times tables: 6 and 7", "num", tables([6, 7]), stables([6, 7])),
    "t89": ("Times tables: 8 and 9", "num", tables([8, 9]), stables([8, 9])),
    "t12": ("Times tables to 12", "num", tables([6, 7, 8, 9, 11, 12]), stables([6, 7, 8, 9, 11, 12])),
    "mul21": ("Multiply", "num", k_mul21, s_mul),
    "mul31": ("Multiply", "num", k_mul31, s_mul),
    "mul22": ("Multiply 2-digit by 2-digit", "num", k_mul22, s_mul),
    "div": ("Divide", "num", k_div, s_div),
    "divr": ("Divide: answer and remainder", "wide", k_divr, s_div),
    "longdiv": ("Divide", "num", k_longdiv, s_div),
    "fracname": ("Name the fraction", "wide", k_fracname, s_fracof),
    "fracof": ("Fraction of an amount", "num", k_fracof, s_fracof),
    "fracequiv": ("Equivalent fractions", "num", k_fracequiv, s_fracof),
    "fraccmp": ("Compare fractions", "wide", k_fraccmp, s_fracadd),
    "fracadd": ("Add fractions", "num", k_fracadd, s_fracadd),
    "fracsub": ("Subtract fractions", "num", k_fracsub, s_fracadd),
    "mixednum": ("Mixed numbers and improper fractions", "wide", k_mixed, s_fracadd),
    "ms_as": ("Two steps: add and subtract", "num", k_multistep_as, s_multistep_as),
    "ms_md": ("Two steps: multiply and divide", "num", k_multistep_md, s_multistep_md),
    "areaper": ("Area and perimeter", "wide", k_areaper, s_areaper),
    "factors": ("Factors and multiples", "wide", k_factors, s_mul),
    "round": ("Rounding", "wide", k_round, s_add3),
    "pattern": ("Continue the pattern", "wide", k_pattern, s_skip),
    "elapsed": ("How long?", "wide", k_elapsed, s_time),
    "decpv": ("Decimal place value", "wide", k_decpv, s_dec),
    "decadd": ("Add decimals", "num", k_decadd, s_dec),
    "decsub": ("Subtract decimals", "num", k_decsub, s_dec),
    "decmul": ("Multiply decimals by whole numbers", "num", k_decmul, s_dec),
    "pow10": ("Multiply and divide by 10, 100, 1000", "num", k_pow10, s_dec),
    "fracdec": ("Fractions and decimals", "wide", k_fracdec, s_frac),
    "fracunlike": ("Add fractions with different denominators", "num", k_fracunlike, s_frac),
    "fracmul": ("Multiply fractions", "num", k_fracmul, s_frac),
    "fracdiv": ("Divide fractions", "num", k_fracdiv, s_frac),
    "pct": ("Percent of an amount", "num", k_pct, s_pct),
    "pctconv": ("Percents, decimals and fractions", "wide", k_pctconv, s_pct),
    "ratiosimp": ("Simplify ratios", "num", k_ratiosimp, s_ratio),
    "ratioshare": ("Share in a ratio", "wide", k_ratioshare, s_ratio),
    "rate": ("Unit price and rates", "wide", k_rate, s_rate),
    "bodmas": ("Order of operations", "num", k_bodmas, s_multistep_as),
    "neg": ("Negative numbers", "num", k_neg, s_neg),
    "evalx": ("Evaluate the expression", "wide", k_eval, s_eq),
    "eq1": ("Solve for x", "wide", k_eq1, s_eq),
    "eq2": ("Solve for x (two steps)", "wide", k_eq2, s_eq),
    "pow": ("Powers and square roots", "num", k_pow, s_volume),
    "hcflcm": ("HCF and LCM", "wide", k_hcflcm, s_ratio),
    "area2": ("Area of triangles and parallelograms", "wide", k_area2, s_areaper),
    "volume": ("Volume of cuboids", "wide", k_volume, s_volume),
    "stats": ("Mean, median and range", "wide", k_stats, s_stats),
}

MEDIUM = [
    ("Counting in 10s to 100", "skip", 100), ("Skip counting in 2s, 5s and 10s", "skip", 60),
    ("Tens and ones", "pv2", 99), ("Comparing numbers to 100", "cmp100", 100),
    ("Adding and subtracting tens", "addtens", 100), ("Adding within 50", "add_nc", 50),
    ("Adding within 100", "add_nc", 100), ("Adding with regrouping", "add_c", 100),
    ("Subtracting within 50", "sub_nb", 50), ("Subtracting within 100", "sub_nb", 100),
    ("Subtracting with regrouping", "sub_b", 100), ("Add and subtract to 100", "mix2", 100),
    ("Hundreds, tens and ones", "pv3", 999), ("Comparing numbers to 1000", "cmp1000", 1000),
    ("Adding 3-digit numbers", "add3", 999), ("Subtracting 3-digit numbers", "sub3", 999),
    ("Doubles and halves", "dbl", 100), ("Times tables: 2, 5 and 10", "t2510", 10),
    ("Times tables: 3 and 4", "t34", 10), ("Multiplication stories", "tmix", 10),
    ("Counting money", "coins", 0), ("Shopping: adding prices and change", "money", 0),
    ("Telling time", "time", 0), ("Length, mass and capacity", "measure", 0),
    ("Mixed revision", "@mix", 0), ("Big Medium revision", "@mix", 0),
]
ADVANCED = [
    ("Times tables: 6 and 7", "t67", 10), ("Times tables: 8 and 9", "t89", 10),
    ("All times tables to 12", "t12", 12), ("Multiplying 2-digit by 1-digit", "mul21", 0),
    ("Multiplying 3-digit by 1-digit", "mul31", 0), ("Division facts", "div", 0),
    ("Division with remainders", "divr", 0), ("Dividing larger numbers", "longdiv", 0),
    ("Multiply and divide stories", "ms_md", 0), ("Naming fractions", "fracname", 0),
    ("Fractions of an amount", "fracof", 0), ("Equivalent fractions", "fracequiv", 0),
    ("Comparing fractions", "fraccmp", 0), ("Adding fractions", "fracadd", 0),
    ("Subtracting fractions", "fracsub", 0), ("Mixed numbers", "mixednum", 0),
    ("Two-step problems: + and -", "ms_as", 0), ("Area and perimeter", "areaper", 0),
    ("Multiplying 2-digit by 2-digit", "mul22", 0), ("Factors and multiples", "factors", 0),
    ("Rounding", "round", 0), ("Number patterns", "pattern", 0),
    ("Time intervals", "elapsed", 0), ("Fractions review", "@frac", 0),
    ("Mixed revision", "@mix", 0), ("Big Advanced revision", "@mix", 0),
]
PRO = [
    ("Decimal place value", "decpv", 0), ("Adding decimals", "decadd", 0),
    ("Subtracting decimals", "decsub", 0), ("Multiplying decimals", "decmul", 0),
    ("x and ÷ by 10, 100 and 1000", "pow10", 0), ("Fractions and decimals", "fracdec", 0),
    ("Adding unlike fractions", "fracunlike", 0), ("Multiplying fractions", "fracmul", 0),
    ("Dividing fractions", "fracdiv", 0), ("Percent of an amount", "pct", 0),
    ("Percents, fractions and decimals", "pctconv", 0), ("Simplifying ratios", "ratiosimp", 0),
    ("Sharing in a ratio", "ratioshare", 0), ("Rates and unit prices", "rate", 0),
    ("Order of operations", "bodmas", 0), ("Negative numbers", "neg", 0),
    ("Evaluating expressions", "evalx", 0), ("One-step equations", "eq1", 0),
    ("Two-step equations", "eq2", 0), ("Powers and square roots", "pow", 0),
    ("HCF and LCM", "hcflcm", 0), ("Area of triangles and parallelograms", "area2", 0),
    ("Volume of cuboids", "volume", 0), ("Mean, median and range", "stats", 0),
    ("Mixed revision", "@mix", 0), ("Big Pro revision", "@mix", 0),
]

LEVELS_MORE = [
    ("medium", "Medium", "Numbers to 1000, regrouping, times tables, money, time and measures.", MEDIUM),
    ("advanced", "Advanced", "All times tables, multiplication and division, fractions and multi-step problems.", ADVANCED),
    ("pro", "Pro", "Decimals, fraction operations, percentages, ratios, negative numbers and first equations.", PRO),
]

INTROS = {
    "medium": [
        "{n1} and {n2} run a lemonade stand today. Prices, change and counting cups all need maths. Let's help them!",
        "It's sports day! {n1} and {n2} add up points, time races and measure jumps. Grab a pencil and join in.",
        "{n1} is saving up for a new bike. Coins, notes and adding it all up: today's sheets are about big numbers.",
        "A trip to the library with {n1}: hundreds of books, shelves in tens, and pages to count. Ready?",
    ],
    "advanced": [
        "{n1} and {n2} are planning a class party: tables of guests, packs of food shared equally and fractions of pizza.",
        "Building day! {n1} measures a garden, works out fences and floors, and splits the jobs fairly.",
        "{n1} is in charge of the school fair: rows of stalls, crates of drinks and money shared between teams.",
        "A recipe for {n1} and {n2}: double it, halve it, share it. Fractions and times tables are everywhere.",
    ],
    "pro": [
        "{n1} is planning a trip: distances in decimals, ticket discounts in percent and budgets to balance.",
        "Science club with {n1} and {n2}: temperatures below zero, measurements in decimals and a mystery number to find.",
        "{n1} runs a small online shop: unit prices, sale percentages and profits shared in a ratio.",
        "Puzzle day! {n1} sets {n2} riddles that are really equations. Solve them all.",
    ],
}


def level_intro(lid, rnd):
    n1, n2 = rnd.sample(NAMES, 2)
    return rnd.choice(INTROS[lid]).format(n1=n1, n2=n2)


def resolve(kind, hi, weeks, wk_ix, rnd):
    """Turn '@mix' / '@frac' into a concrete (kind, hi) for one problem."""
    if kind == "@mix":
        return rnd.choice([(k, h) for _t, k, h in weeks[:wk_ix] if not k.startswith("@")])
    if kind == "@frac":
        return rnd.choice(["fracof", "fracequiv", "fraccmp", "fracadd", "fracsub", "mixednum"]), 0
    return kind, hi
