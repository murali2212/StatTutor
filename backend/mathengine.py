"""Verified statistics calculations with beginner-friendly working.
Every function returns numbers plus `steps`: a list of
{"title", "lines": [...], "table": {"head", "rows"}} explaining each stage."""
import math, re
from scipy import stats

def _g(x, dp=4):
    s = f"{x:.{dp}f}"
    if "." in s:
        s = s.rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s

def S(title, *lines, table=None):
    d = {"title": title, "lines": list(lines)}
    if table:
        d["table"] = {"head": [str(c) for c in table[0]], "rows": [[str(c) for c in r] for r in table[1:]]}
    return d

def _floats(v, name="values", minlen=1):
    if not isinstance(v, (list, tuple)):
        raise ValueError(f"{name}: enter a list of numbers.")
    try:
        out = [float(a) for a in v]
    except (TypeError, ValueError):
        raise ValueError(f"{name}: every entry must be a number.")
    if any(math.isnan(a) or math.isinf(a) for a in out):
        raise ValueError(f"{name}: every entry must be a finite number.")
    if len(out) < minlen:
        raise ValueError(f"{name}: enter at least {minlen} value(s).")
    if len(out) > 500:
        raise ValueError(f"{name}: at most 500 values.")
    return out

def _median(s):
    n = len(s)
    return s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2

def _alpha(alpha, tails=2):
    if not 0 < alpha < 1:
        raise ValueError("Level of significance must be between 0 and 1 (for example 0.05).")
    if tails not in (1, 2):
        raise ValueError("Tails must be 1 or 2.")

def _crit(computed, table_value):
    if table_value is None:
        return float(computed), "Table value (from the statistical table)"
    if table_value <= 0:
        raise ValueError("Table value must be positive.")
    return float(table_value), "Table value (the one given in your question)"

def _decision(stat, crit, label, null_text, alt_text):
    rej = stat > crit
    lines = [f"Calculated {label} = {_g(stat)}; table value = {_g(crit)}.",
             (f"{_g(stat)} is greater than {_g(crit)}, so we REJECT the null hypothesis H0." if rej else
              f"{_g(stat)} is not greater than {_g(crit)}, so we ACCEPT the null hypothesis H0."),
             ("Conclusion: " + alt_text) if rej else ("Conclusion: " + null_text)]
    return rej, S("Final step: Decision and conclusion", *lines)

# ---------------------------------------------------------------- lists of numbers
def descriptive(data, sample=True):
    xs = _floats(data, "Numbers")
    n = len(xs)
    if sample and n < 2:
        raise ValueError("Sample variance needs at least 2 values.")
    s = sorted(xs)
    total = sum(s); mean = total / n
    steps = [S("Step 1: Arrange the data from smallest to largest",
               ", ".join(_g(x) for x in s), f"Count the values: n = {n}"),
             S("Step 2: Mean (the average)", "Formula: mean = (sum of all values) ÷ (number of values)",
               f"Sum = {_g(total)}", f"Mean = {_g(total)} ÷ {n} = {_g(mean)}")]
    med = _median(s)
    if n % 2:
        steps.append(S("Step 3: Median (the middle value)", f"n = {n} is odd, so the median is the value in position (n+1)/2 = {(n + 1) // 2}.", f"Median = {_g(med)}"))
    else:
        steps.append(S("Step 3: Median (the middle value)", f"n = {n} is even, so take the average of the two middle values, {_g(s[n // 2 - 1])} and {_g(s[n // 2])}.", f"Median = ({_g(s[n // 2 - 1])} + {_g(s[n // 2])}) ÷ 2 = {_g(med)}"))
    counts = {}
    for x in s: counts[x] = counts.get(x, 0) + 1
    top = max(counts.values())
    modes = [] if top == 1 else sorted(k for k, v in counts.items() if v == top)
    steps.append(S("Step 4: Mode (the value that repeats most)", ("Mode = " + ", ".join(_g(m) for m in modes) + f" (appears {top} times)") if modes else "No value repeats, so there is no mode."))
    ss = sum((x - mean) ** 2 for x in s)
    if n <= 15:
        steps.append(S("Step 5: How far is each value from the mean?", "Square each difference so negatives do not cancel positives.",
                       table=[["x", "x − mean", "(x − mean)²"]] + [[_g(x), _g(x - mean), _g((x - mean) ** 2)] for x in s] + [["Total", "", _g(ss)]]))
    denom = n - 1 if sample else n
    var = ss / denom; sd = math.sqrt(var)
    steps.append(S("Step 6: Variance and standard deviation",
                   f"Formula: variance = (sum of squared differences) ÷ {'(n − 1)' if sample else 'n'}",
                   ("We divide by n − 1 because this is a sample, not the whole population." if sample else "We divide by n because this is the whole population."),
                   f"Variance = {_g(ss)} ÷ {denom} = {_g(var)}",
                   f"Standard deviation = √variance = √{_g(var)} = {_g(sd)}"))
    half = n // 2
    lower, upper = s[:half], s[half + (n % 2):]
    q1 = _median(lower) if lower else s[0]; q3 = _median(upper) if upper else s[-1]
    steps.append(S("Step 7: Quartiles", f"Q1 = median of the lower half = {_g(q1)}", f"Q3 = median of the upper half = {_g(q3)}", f"Range = largest − smallest = {_g(s[-1])} − {_g(s[0])} = {_g(s[-1] - s[0])}"))
    return {"n": n, "mean": mean, "median": med, "mode": modes, "variance": var, "sd": sd,
            "range": s[-1] - s[0], "q1": q1, "q3": q3, "iqr": q3 - q1,
            "cv_percent": (sd / mean * 100) if mean else None, "steps": steps}

# ---------------------------------------------------------------- frequency tables
def _pairs(x, f):
    xs, fs = _floats(x, "x values"), _floats(f, "Frequencies")
    if len(xs) != len(fs):
        raise ValueError("x values and frequencies must have the same count.")
    if any(v < 0 for v in fs) or sum(fs) <= 0:
        raise ValueError("Frequencies must be zero or more, and not all zero.")
    return sorted(zip(xs, fs))

def _item(pairs, pos):
    cum = 0
    for x, f in pairs:
        cum += f
        if cum >= pos:
            return x

def freq_discrete(x, f, focus="sd_cv", about="mean"):
    p = _pairs(x, f)
    N = sum(f for _, f in p)
    fx = sum(x * f for x, f in p); mean = fx / N
    used = [x for x, f in p if f > 0]
    if focus == "sd_cv":
        fx2 = sum(x * x * f for x, f in p)
        var = max(fx2 / N - mean ** 2, 0.0); sd = math.sqrt(var)
        cv = sd / mean * 100 if mean else None
        if cv is None:
            raise ValueError("Mean is 0, so the coefficient of variation is undefined.")
        steps = [S("Step 1: Make the working table", "Multiply each x by its frequency f to get fx, and each x² by f to get fx².",
                   table=[["x", "f", "fx", "fx²"]] + [[_g(a), _g(b), _g(a * b), _g(a * a * b)] for a, b in p] + [["Total", _g(N), _g(fx), _g(fx2)]]),
                 S("Step 2: Mean", "Formula: mean = Σfx ÷ N  (N is the total frequency)", f"Mean = {_g(fx)} ÷ {_g(N)} = {_g(mean)}"),
                 S("Step 3: Standard deviation", "Formula: σ = √[ Σfx² ÷ N − (mean)² ]",
                   f"Σfx² ÷ N = {_g(fx2)} ÷ {_g(N)} = {_g(fx2 / N)}", f"(mean)² = {_g(mean)}² = {_g(mean ** 2)}",
                   f"Variance = {_g(fx2 / N)} − {_g(mean ** 2)} = {_g(var)}", f"σ = √{_g(var)} = {_g(sd)}"),
                 S("Step 4: Coefficient of variation (CV)", "Formula: CV = (σ ÷ mean) × 100. It shows spread as a percentage of the mean, so a smaller CV means more consistent data.",
                   f"CV = ({_g(sd)} ÷ {_g(mean)}) × 100 = {_g(cv)}%")]
        return {"n": N, "mean": mean, "variance": var, "sd": sd, "cv_percent": cv, "steps": steps}
    if focus == "range":
        L, Sm = max(used), min(used)
        steps = [S("Step 1: Find the largest and smallest values", f"Largest value L = {_g(L)}", f"Smallest value S = {_g(Sm)}",
                   "Frequencies do not change the range; only the extreme values matter."),
                 S("Step 2: Range", "Formula: Range = L − S", f"Range = {_g(L)} − {_g(Sm)} = {_g(L - Sm)}"),
                 S("Step 3: Coefficient of range (the relative measure)", "Formula: (L − S) ÷ (L + S)", f"= {_g(L - Sm)} ÷ {_g(L + Sm)} = {_g((L - Sm) / (L + Sm))}")]
        return {"range": L - Sm, "coeff_range": (L - Sm) / (L + Sm), "steps": steps}
    if focus == "qd":
        cum, rows = 0, [["x", "f", "cumulative f"]]
        for a, b in p:
            cum += b; rows.append([_g(a), _g(b), _g(cum)])
        p1, p3 = (N + 1) / 4, 3 * (N + 1) / 4
        q1, q3 = _item(p, p1), _item(p, p3)
        qd = (q3 - q1) / 2
        steps = [S("Step 1: Arrange x in order and add a cumulative frequency column", "Cumulative frequency = running total of f.", table=rows),
                 S("Step 2: Find Q1", "Formula: Q1 = value of the (N + 1) ÷ 4 th item", f"(N + 1) ÷ 4 = ({_g(N)} + 1) ÷ 4 = {_g(p1)}",
                   f"The first cumulative frequency that is at least {_g(p1)} gives x = {_g(q1)}, so Q1 = {_g(q1)}"),
                 S("Step 3: Find Q3", "Formula: Q3 = value of the 3(N + 1) ÷ 4 th item", f"3(N + 1) ÷ 4 = {_g(p3)}",
                   f"The first cumulative frequency that is at least {_g(p3)} gives x = {_g(q3)}, so Q3 = {_g(q3)}"),
                 S("Step 4: Quartile deviation (QD)", "Formula: QD = (Q3 − Q1) ÷ 2", f"QD = ({_g(q3)} − {_g(q1)}) ÷ 2 = {_g(qd)}"),
                 S("Step 5: Coefficient of quartile deviation (the relative measure)", "Formula: (Q3 − Q1) ÷ (Q3 + Q1)",
                   f"= {_g(q3 - q1)} ÷ {_g(q3 + q1)} = {_g((q3 - q1) / (q3 + q1)) if q3 + q1 else 'undefined'}")]
        return {"n": N, "q1": q1, "q3": q3, "qd": qd, "coeff_qd": (q3 - q1) / (q3 + q1) if q3 + q1 else None, "steps": steps}
    if focus == "md":
        if about == "median":
            A = _item(p, (N + 1) / 2); name = "median"
        else:
            A, name = mean, "mean"
        tot = sum(f * abs(x - A) for x, f in p); md = tot / N
        steps = [S(f"Step 1: Find the {name}", f"{name.capitalize()} = {_g(A)}" + (" (the value of the (N + 1) ÷ 2 th item)" if about == "median" else f"  (Σfx ÷ N = {_g(fx)} ÷ {_g(N)})")),
                 S("Step 2: Distance of each x from the " + name, "|x − " + name + "| means the difference with the sign ignored.",
                   table=[["x", "f", f"|x − {name}|", f"f × |x − {name}|"]] + [[_g(a), _g(b), _g(abs(a - A)), _g(b * abs(a - A))] for a, b in p] + [["Total", _g(N), "", _g(tot)]]),
                 S(f"Step 3: Mean deviation about the {name}", "Formula: MD = Σf|x − A| ÷ N", f"MD = {_g(tot)} ÷ {_g(N)} = {_g(md)}"),
                 S("Step 4: Coefficient of mean deviation (the relative measure)", f"Formula: MD ÷ {name}", f"= {_g(md)} ÷ {_g(A)} = {_g(md / A) if A else 'undefined'}")]
        return {"n": N, "about": A, "md": md, "coeff_md": md / A if A else None, "steps": steps}
    raise ValueError("Unknown focus. Use sd_cv, range, qd or md.")

# ---------------------------------------------------------------- class intervals
def _classes(classes, f):
    fs = _floats(f, "Frequencies")
    if not isinstance(classes, (list, tuple)) or len(classes) != len(fs):
        raise ValueError("Give one frequency for each class interval.")
    out = []
    for c in classes:
        m = re.fullmatch(r"\s*(\d+(?:\.\d+)?)\s*(?:-|–|to)\s*(\d+(?:\.\d+)?)\s*", str(c))
        if not m:
            raise ValueError(f'Could not read the class "{c}". Write it like 0-5. An open class such as "Above 30" needs a closed limit, for example 30-35.')
        lo, hi = float(m[1]), float(m[2])
        if hi <= lo:
            raise ValueError(f'Class "{c}" must have a higher upper limit.')
        out.append((lo, hi))
    h = out[0][1] - out[0][0]
    for (lo, hi), (lo2, _) in zip(out, out[1:] + [(out[-1][1], 0)]):
        if abs((hi - lo) - h) > 1e-9 or abs(lo2 - hi) > 1e-9:
            raise ValueError("Classes must be continuous with equal width (0-5, 5-10, 10-15 ...).")
    if sum(fs) <= 0 or any(v < 0 for v in fs):
        raise ValueError("Frequencies must be zero or more, and not all zero.")
    return out, fs, h

def grouped(classes, f, focus="skew"):
    cl, fs, h = _classes(classes, f)
    N = sum(fs); mids = [(lo + hi) / 2 for lo, hi in cl]
    fm = sum(m * a for m, a in zip(mids, fs)); mean = fm / N
    fm2 = sum(m * m * a for m, a in zip(mids, fs))
    var = max(fm2 / N - mean ** 2, 0.0); sd = math.sqrt(var)
    rows = [["Class", "f", "mid-value m", "fm", "fm²"]] + [[f"{_g(lo)}-{_g(hi)}", _g(a), _g(m), _g(a * m), _g(a * m * m)] for (lo, hi), a, m in zip(cl, fs, mids)] + [["Total", _g(N), "", _g(fm), _g(fm2)]]
    steps = [S("Step 1: Working table", "Mid-value m = (lower limit + upper limit) ÷ 2. Then work out fm and fm².", table=rows),
             S("Step 2: Mean", "Formula: mean = Σfm ÷ N", f"Mean = {_g(fm)} ÷ {_g(N)} = {_g(mean)}"),
             S("Step 3: Standard deviation", "Formula: σ = √[ Σfm² ÷ N − (mean)² ]", f"Σfm² ÷ N = {_g(fm2 / N)}", f"(mean)² = {_g(mean ** 2)}",
               f"Variance = {_g(fm2 / N)} − {_g(mean ** 2)} = {_g(var)}", f"σ = √{_g(var)} = {_g(sd)}")]
    if focus == "sd_cv":
        if not mean:
            raise ValueError("Mean is 0, so the coefficient of variation is undefined.")
        steps.append(S("Step 4: Coefficient of variation", "Formula: CV = (σ ÷ mean) × 100", f"CV = ({_g(sd)} ÷ {_g(mean)}) × 100 = {_g(sd / mean * 100)}%"))
        return {"n": N, "mean": mean, "sd": sd, "cv_percent": sd / mean * 100, "steps": steps}
    if focus == "skew":
        i = max(range(len(fs)), key=lambda k: fs[k])
        f1, f0, f2 = fs[i], fs[i - 1] if i > 0 else 0, fs[i + 1] if i < len(fs) - 1 else 0
        den = 2 * f1 - f0 - f2
        if den == 0 or sd == 0:
            raise ValueError("The mode cannot be found by the formula for this data. Use Sk = 3(mean − median) ÷ σ instead.")
        L = cl[i][0]; mode = L + (f1 - f0) / den * h
        sk = (mean - mode) / sd
        steps.append(S("Step 4: Mode", f"The modal class is the class with the highest frequency: {_g(cl[i][0])}-{_g(cl[i][1])} (f = {_g(f1)}).",
                       "Formula: Mode = L + [(f1 − f0) ÷ (2f1 − f0 − f2)] × h",
                       f"L = {_g(L)}, f1 = {_g(f1)}, f0 (class before) = {_g(f0)}, f2 (class after) = {_g(f2)}, h (class width) = {_g(h)}",
                       f"Mode = {_g(L)} + [({_g(f1)} − {_g(f0)}) ÷ (2×{_g(f1)} − {_g(f0)} − {_g(f2)})] × {_g(h)} = {_g(mode)}"))
        kind = "positively skewed (long tail to the right)" if sk > 0 else "negatively skewed (long tail to the left)" if sk < 0 else "symmetrical"
        steps.append(S("Step 5: Karl Pearson's coefficient of skewness", "Formula: Sk = (mean − mode) ÷ σ", f"Sk = ({_g(mean)} − {_g(mode)}) ÷ {_g(sd)} = {_g(sk)}",
                       f"Meaning: the sign shows the direction. Sk is {_g(sk)}, so the distribution is {kind}."))
        return {"n": N, "mean": mean, "mode": mode, "sd": sd, "skewness": sk, "steps": steps}
    raise ValueError("Unknown focus. Use sd_cv or skew.")

# ---------------------------------------------------------------- correlation and regression
def correlation_regression(x, y, estimate_x=None):
    xs, ys = _floats(x, "x values", 2), _floats(y, "y values", 2)
    if len(xs) != len(ys):
        raise ValueError("x and y need the same count.")
    n = len(xs); mx, my = sum(xs) / n, sum(ys) / n
    sxx = sum((a - mx) ** 2 for a in xs); syy = sum((b - my) ** 2 for b in ys)
    sxy = sum((a - mx) * (b - my) for a, b in zip(xs, ys))
    if sxx == 0 or syy == 0:
        raise ValueError("Values of x or y are all equal; correlation is undefined.")
    r = sxy / math.sqrt(sxx * syy)
    byx, bxy = sxy / sxx, sxy / syy
    ay, ax = my - byx * mx, mx - bxy * my
    steps = [S("Step 1: Means", f"x̄ = Σx ÷ n = {_g(sum(xs))} ÷ {n} = {_g(mx)}", f"ȳ = Σy ÷ n = {_g(sum(ys))} ÷ {n} = {_g(my)}")]
    if n <= 12:
        steps.append(S("Step 2: Working table", "Take each value's distance from its mean, then multiply and square.",
                       table=[["x", "y", "x − x̄", "y − ȳ", "(x − x̄)²", "(y − ȳ)²", "(x − x̄)(y − ȳ)"]] +
                             [[_g(a), _g(b), _g(a - mx), _g(b - my), _g((a - mx) ** 2), _g((b - my) ** 2), _g((a - mx) * (b - my))] for a, b in zip(xs, ys)] +
                             [["Total", "", "", "", _g(sxx), _g(syy), _g(sxy)]]))
    else:
        steps.append(S("Step 2: Sums needed", f"Σ(x − x̄)² = {_g(sxx)}", f"Σ(y − ȳ)² = {_g(syy)}", f"Σ(x − x̄)(y − ȳ) = {_g(sxy)}"))
    steps += [S("Step 3: Karl Pearson's correlation coefficient r", "Formula: r = Σ(x − x̄)(y − ȳ) ÷ √[Σ(x − x̄)² × Σ(y − ȳ)²]",
                f"r = {_g(sxy)} ÷ √({_g(sxx)} × {_g(syy)}) = {_g(r)}",
                "Meaning: r is always between −1 and +1. Near +1 means they rise together, near −1 means one rises as the other falls, near 0 means little linear relationship."),
              S("Step 4: Regression coefficients", "b(yx) = Σ(x − x̄)(y − ȳ) ÷ Σ(x − x̄)²  (how much y changes when x increases by 1)", f"b(yx) = {_g(sxy)} ÷ {_g(sxx)} = {_g(byx)}",
                "b(xy) = Σ(x − x̄)(y − ȳ) ÷ Σ(y − ȳ)²  (how much x changes when y increases by 1)", f"b(xy) = {_g(sxy)} ÷ {_g(syy)} = {_g(bxy)}"),
              S("Step 5: Regression line of Y on X", "Formula: Y − ȳ = b(yx) (X − x̄)", f"Y − {_g(my)} = {_g(byx)} (X − {_g(mx)})",
                f"Simplified: Y = {_g(ay)} + {_g(byx)}X"),
              S("Step 6: Regression line of X on Y", "Formula: X − x̄ = b(xy) (Y − ȳ)", f"X − {_g(mx)} = {_g(bxy)} (Y − {_g(my)})", f"Simplified: X = {_g(ax)} + {_g(bxy)}Y")]
    est = None
    if estimate_x is not None:
        est = ay + byx * float(estimate_x)
        steps.append(S(f"Step 7: Estimate Y when X = {_g(float(estimate_x))}", "Put the X value into the line of Y on X.", f"Y = {_g(ay)} + {_g(byx)} × {_g(float(estimate_x))} = {_g(est)}"))
    return {"r": r, "r_squared": r * r, "y_on_x": {"a": ay, "b": byx}, "x_on_y": {"a": ax, "b": bxy}, "estimate": est, "steps": steps}

def spearman(x, y):
    xs, ys = _floats(x, "x values", 2), _floats(y, "y values", 2)
    if len(xs) != len(ys):
        raise ValueError("x and y need the same count.")
    if len(set(xs)) != len(xs) or len(set(ys)) != len(ys):
        raise ValueError("This calculator handles non-repeated values only, as in your syllabus. Your data has repeats.")
    rank = lambda v: [sorted(v).index(a) + 1 for a in v]
    rx, ry = rank(xs), rank(ys); n = len(xs)
    d2 = [(a - b) ** 2 for a, b in zip(rx, ry)]
    rho = 1 - 6 * sum(d2) / (n * (n * n - 1))
    steps = [S("Step 1: Give ranks (1 = smallest)", table=[["x", "y", "R1 (rank of x)", "R2 (rank of y)", "d = R1 − R2", "d²"]] +
                [[_g(a), _g(b), c, d, c - d, e] for a, b, c, d, e in zip(xs, ys, rx, ry, d2)] + [["Total", "", "", "", "", sum(d2)]]),
             S("Step 2: Spearman's rank correlation", "Formula: ρ = 1 − [6 Σd²] ÷ [n (n² − 1)]", f"ρ = 1 − (6 × {sum(d2)}) ÷ ({n} × {n * n - 1}) = {_g(rho)}",
               "It is read like r: +1 means identical ranking, −1 means exactly opposite ranking.")]
    return {"rho": rho, "steps": steps}

# ---------------------------------------------------------------- tests of significance
def t_single(data, mu0, alpha=0.05, tails=2, table_value=None):
    xs = _floats(data, "Sample values", 2); _alpha(alpha, tails)
    n = len(xs); mean = sum(xs) / n; ss = sum((a - mean) ** 2 for a in xs)
    s = math.sqrt(ss / (n - 1))
    if s == 0:
        raise ValueError("All values are equal, so the test cannot be done.")
    se = s / math.sqrt(n); t = (mean - mu0) / se; df = n - 1
    crit, lab = _crit(stats.t.ppf(1 - alpha / tails, df), table_value)
    p = float(stats.t.sf(abs(t), df) * tails)
    steps = [S("Step 1: Hypotheses", f"H0: the true mean is {_g(mu0)} (no difference).", f"H1: the true mean is different from {_g(mu0)}" + (" (two-tailed test)." if tails == 2 else " (one-tailed test: check the direction in your question).")),
             S("Step 2: Sample mean and standard deviation", f"Mean x̄ = Σx ÷ n = {_g(sum(xs))} ÷ {n} = {_g(mean)}",
               table=[["x", "x − x̄", "(x − x̄)²"]] + [[_g(a), _g(a - mean), _g((a - mean) ** 2)] for a in xs] + [["Total", "", _g(ss)]] if n <= 15 else None),
             S("Step 3: Standard deviation s", "Formula: s = √[ Σ(x − x̄)² ÷ (n − 1) ]", f"s = √({_g(ss)} ÷ {n - 1}) = {_g(s)}"),
             S("Step 4: Test statistic t", "Formula: t = (x̄ − μ) ÷ (s ÷ √n)", f"Standard error = s ÷ √n = {_g(s)} ÷ √{n} = {_g(se)}", f"t = ({_g(mean)} − {_g(mu0)}) ÷ {_g(se)} = {_g(t)}"),
             S("Step 5: Degrees of freedom and table value", f"Degrees of freedom = n − 1 = {df}", f"{lab} at {_g(alpha * 100)}% level, {df} df = {_g(crit)}. We compare |t| = {_g(abs(t))} with it.")]
    rej, last = _decision(abs(t), crit, "|t|", "there is no significant difference between the sample mean and " + _g(mu0) + ".", "there is a significant difference between the sample mean and " + _g(mu0) + ".")
    steps.append(last)
    return {"mean": mean, "sd": s, "t": t, "df": df, "table_value": crit, "p_value": p, "reject_h0": rej, "steps": steps}

def t_two_means(n1, mean1, sd1, n2, mean2, sd2, alpha=0.05, tails=2, sd_type="n", table_value=None):
    _alpha(alpha, tails)
    if n1 < 2 or n2 < 2 or sd1 <= 0 or sd2 <= 0:
        raise ValueError("Each sample needs n of at least 2 and a positive standard deviation.")
    df = int(n1 + n2 - 2)
    if sd_type == "n":
        pooled = (n1 * sd1 ** 2 + n2 * sd2 ** 2) / df
        f_txt = "S² = (n1·s1² + n2·s2²) ÷ (n1 + n2 − 2)"; calc = f"S² = ({_g(n1)}×{_g(sd1 ** 2)} + {_g(n2)}×{_g(sd2 ** 2)}) ÷ {df} = {_g(pooled)}"
        note = "Use this form when the given standard deviations were worked out by dividing by n (the usual textbook case)."
    elif sd_type == "n-1":
        pooled = ((n1 - 1) * sd1 ** 2 + (n2 - 1) * sd2 ** 2) / df
        f_txt = "S² = [(n1 − 1)s1² + (n2 − 1)s2²] ÷ (n1 + n2 − 2)"; calc = f"S² = ({_g(n1 - 1)}×{_g(sd1 ** 2)} + {_g(n2 - 1)}×{_g(sd2 ** 2)}) ÷ {df} = {_g(pooled)}"
        note = "Use this form when the given standard deviations are sample standard deviations (divided by n − 1)."
    else:
        raise ValueError('sd_type must be "n" or "n-1".')
    Sp = math.sqrt(pooled); se = Sp * math.sqrt(1 / n1 + 1 / n2); t = (mean1 - mean2) / se
    crit, lab = _crit(stats.t.ppf(1 - alpha / tails, df), table_value)
    steps = [S("Step 1: Hypotheses", "H0: the two population means are equal (no real difference).", "H1: the means are different."),
             S("Step 2: Combine the two spreads (pooled variance)", note, "Formula: " + f_txt, calc, f"S = √{_g(pooled)} = {_g(Sp)}"),
             S("Step 3: Standard error of the difference", "Formula: S × √(1/n1 + 1/n2)", f"= {_g(Sp)} × √(1/{_g(n1)} + 1/{_g(n2)}) = {_g(se)}"),
             S("Step 4: Test statistic t", "Formula: t = (x̄1 − x̄2) ÷ standard error", f"t = ({_g(mean1)} − {_g(mean2)}) ÷ {_g(se)} = {_g(t)}"),
             S("Step 5: Degrees of freedom and table value", f"Degrees of freedom = n1 + n2 − 2 = {df}", f"{lab} at {_g(alpha * 100)}% level, {df} df = {_g(crit)}. We compare |t| = {_g(abs(t))} with it.")]
    rej, last = _decision(abs(t), crit, "|t|", "there is no significant difference between the two means.", "there is a significant difference between the two means.")
    steps.append(last)
    return {"pooled_variance": pooled, "se": se, "t": t, "df": df, "table_value": crit, "reject_h0": rej, "steps": steps}

def f_test(data1, data2, alpha=0.05, table_value=None):
    a, b = _floats(data1, "Sample I", 2), _floats(data2, "Sample II", 2); _alpha(alpha)
    def stat(v):
        m = sum(v) / len(v); ss = sum((x - m) ** 2 for x in v); return m, ss, ss / (len(v) - 1)
    m1, ss1, v1 = stat(a); m2, ss2, v2 = stat(b)
    if v1 == 0 or v2 == 0:
        raise ValueError("One sample has no variation, so the F-test cannot be done.")
    big_first = v1 >= v2
    F = max(v1, v2) / min(v1, v2)
    d1, d2 = (len(a) - 1, len(b) - 1) if big_first else (len(b) - 1, len(a) - 1)
    crit, lab = _crit(stats.f.ppf(1 - alpha, d1, d2), table_value)
    steps = [S("Step 1: Hypotheses", "H0: the two population variances are equal.", "H1: the variances are different."),
             S("Step 2: Variance of Sample I", f"n1 = {len(a)}, mean = {_g(m1)}", f"Σ(x − x̄)² = {_g(ss1)}", f"s1² = {_g(ss1)} ÷ {len(a) - 1} = {_g(v1)}"),
             S("Step 3: Variance of Sample II", f"n2 = {len(b)}, mean = {_g(m2)}", f"Σ(x − x̄)² = {_g(ss2)}", f"s2² = {_g(ss2)} ÷ {len(b) - 1} = {_g(v2)}"),
             S("Step 4: F ratio", "Formula: F = larger variance ÷ smaller variance (so F is always 1 or more)", f"F = {_g(max(v1, v2))} ÷ {_g(min(v1, v2))} = {_g(F)}"),
             S("Step 5: Degrees of freedom and table value", f"Degrees of freedom = (n − 1) of the larger-variance sample, then of the smaller = ({d1}, {d2})", f"{lab} for ({d1}, {d2}) at {_g(alpha * 100)}% = {_g(crit)}")]
    rej, last = _decision(F, crit, "F", "there is no significant difference between the two variances.", "there is a significant difference between the two variances.")
    steps.append(last)
    return {"var1": v1, "var2": v2, "F": F, "df": [d1, d2], "table_value": crit, "reject_h0": rej, "steps": steps}

def chi_gof(observed, expected=None, alpha=0.05, table_value=None):
    o = _floats(observed, "Observed frequencies", 2); _alpha(alpha)
    k, tot = len(o), sum(o)
    e = [tot / k] * k if not expected else _floats(expected, "Expected frequencies", 2)
    if len(e) != k:
        raise ValueError("Give one expected frequency for each observed frequency.")
    if abs(sum(e) - tot) > 1e-6 * max(tot, 1):
        raise ValueError("Expected frequencies must add up to the same total as the observed ones.")
    if any(v <= 0 for v in e):
        raise ValueError("Expected frequencies must be positive.")
    terms = [(a - b) ** 2 / b for a, b in zip(o, e)]; chi = sum(terms); df = k - 1
    crit, lab = _crit(stats.chi2.ppf(1 - alpha, df), table_value)
    steps = [S("Step 1: Hypotheses", "H0: the data fits the expected pattern (for a die: it is fair).", "H1: the data does not fit."),
             S("Step 2: Expected frequencies", ("No expected values were given, so we assume all categories are equally likely: E = total ÷ number of categories = " + f"{_g(tot)} ÷ {k} = {_g(tot / k)}.") if not expected else "Expected frequencies were given."),
             S("Step 3: Working table", "Formula: χ² = Σ (O − E)² ÷ E", table=[["O", "E", "O − E", "(O − E)²", "(O − E)² ÷ E"]] + [[_g(a), _g(b), _g(a - b), _g((a - b) ** 2), _g(t)] for a, b, t in zip(o, e, terms)] + [["Total", _g(sum(e)), "", "", _g(chi)]]),
             S("Step 4: Degrees of freedom and table value", f"Degrees of freedom = number of categories − 1 = {df}", f"{lab} at {_g(alpha * 100)}% level, {df} df = {_g(crit)}")]
    if any(v < 5 for v in e):
        steps[-1]["lines"].append("Warning: some expected frequencies are below 5, so the chi-square result may be unreliable.")
    rej, last = _decision(chi, crit, "χ²", "the data fits the expected pattern.", "the data does not fit the expected pattern.")
    steps.append(last)
    return {"chi_square": chi, "df": df, "table_value": crit, "reject_h0": rej, "steps": steps}

def chi_independence(table, alpha=0.05, table_value=None):
    if not isinstance(table, list) or len(table) < 2 or any(not isinstance(r, list) or len(r) != len(table[0]) for r in table) or len(table[0]) < 2:
        raise ValueError("Enter a table with at least 2 rows and 2 columns, all rows the same length.")
    t = [_floats(r, "Table row") for r in table]; _alpha(alpha)
    if any(v < 0 for r in t for v in r):
        raise ValueError("Counts cannot be negative.")
    rt = [sum(r) for r in t]; ct = [sum(c) for c in zip(*t)]; N = sum(rt)
    if N <= 0 or 0 in rt or 0 in ct:
        raise ValueError("Every row and column needs at least one count.")
    E = [[rt[i] * ct[j] / N for j in range(len(ct))] for i in range(len(rt))]
    chi = sum((t[i][j] - E[i][j]) ** 2 / E[i][j] for i in range(len(rt)) for j in range(len(ct)))
    df = (len(rt) - 1) * (len(ct) - 1)
    crit, lab = _crit(stats.chi2.ppf(1 - alpha, df), table_value)
    steps = [S("Step 1: Hypotheses", "H0: the two attributes are independent (not related).", "H1: they are dependent (related)."),
             S("Step 2: Expected frequencies", "Formula: E = (row total × column total) ÷ grand total", f"Grand total = {_g(N)}",
               table=[[""] + [f"Col {j + 1}" for j in range(len(ct))]] + [[f"Row {i + 1} (E)"] + [_g(v) for v in E[i]] for i in range(len(rt))]),
             S("Step 3: Chi-square", "Formula: χ² = Σ (O − E)² ÷ E, added over every cell", f"χ² = {_g(chi)}"),
             S("Step 4: Degrees of freedom and table value", f"Degrees of freedom = (rows − 1)(columns − 1) = {df}", f"{lab} at {_g(alpha * 100)}% level, {df} df = {_g(crit)}")]
    rej, last = _decision(chi, crit, "χ²", "the attributes are independent.", "the attributes are dependent (related).")
    steps.append(last)
    return {"chi_square": chi, "df": df, "table_value": crit, "reject_h0": rej, "steps": steps}

def anova_oneway(groups, alpha=0.05, table_value=None):
    if not isinstance(groups, list) or len(groups) < 2:
        raise ValueError("Enter at least 2 groups.")
    g = [_floats(x, "Group", 1) for x in groups]; _alpha(alpha)
    k, N = len(g), sum(len(x) for x in g)
    if N <= k:
        raise ValueError("Need more values than groups.")
    grand = sum(sum(x) for x in g) / N
    ssb = sum(len(x) * (sum(x) / len(x) - grand) ** 2 for x in g)
    ssw = sum(sum((v - sum(x) / len(x)) ** 2 for v in x) for x in g)
    dfb, dfw = k - 1, N - k
    if ssw == 0:
        raise ValueError("No variation inside the groups, so F is undefined.")
    msb, msw = ssb / dfb, ssw / dfw; F = msb / msw
    crit, lab = _crit(stats.f.ppf(1 - alpha, dfb, dfw), table_value)
    steps = [S("Step 1: Hypotheses", "H0: all group means are equal.", "H1: at least one group mean is different."),
             S("Step 2: Group means and grand mean", *[f"Group {i + 1}: n = {len(x)}, mean = {_g(sum(x) / len(x))}" for i, x in enumerate(g)], f"Grand mean = {_g(grand)}"),
             S("Step 3: Sums of squares", "Between groups: SSB = Σ n × (group mean − grand mean)²  (how far the groups are from each other)", f"SSB = {_g(ssb)}",
               "Within groups: SSW = Σ (value − its group mean)²  (the spread inside each group)", f"SSW = {_g(ssw)}"),
             S("Step 4: ANOVA table", "Mean square = sum of squares ÷ degrees of freedom. F = MSB ÷ MSW.",
               table=[["Source", "SS", "df", "MS", "F"], ["Between groups", _g(ssb), dfb, _g(msb), _g(F)], ["Within groups", _g(ssw), dfw, _g(msw), ""], ["Total", _g(ssb + ssw), N - 1, "", ""]]),
             S("Step 5: Table value", f"{lab} for ({dfb}, {dfw}) at {_g(alpha * 100)}% = {_g(crit)}")]
    rej, last = _decision(F, crit, "F", "the group means do not differ significantly.", "at least one group mean differs significantly.")
    steps.append(last)
    return {"F": F, "df": [dfb, dfw], "table_value": crit, "reject_h0": rej, "ssb": ssb, "ssw": ssw, "steps": steps}

# ---------------------------------------------------------------- probability
def binomial(n, p, k):
    if n < 0 or int(n) != n or not 0 <= p <= 1 or int(k) != k or not 0 <= k <= n:
        raise ValueError("Need whole n >= 0, 0 <= p <= 1 and 0 <= k <= n.")
    n, k = int(n), int(k)
    pmf = lambda i: math.comb(n, i) * p ** i * (1 - p) ** (n - i)
    cdf = sum(pmf(i) for i in range(k + 1))
    steps = [S("Step 1: Formula", "P(X = k) = C(n, k) × p^k × q^(n − k), where q = 1 − p", "n = number of trials, p = chance of success each time, k = number of successes wanted."),
             S(f"Step 2: Put in the numbers for exactly {k} successes", f"C({n}, {k}) = {math.comb(n, k)}", f"P(X = {k}) = {math.comb(n, k)} × {_g(p)}^{k} × {_g(1 - p)}^{n - k} = {_g(pmf(k), 6)}"),
             S(f"Step 3: At most {k} successes", f"Add P(X = 0) up to P(X = {k}): P(X ≤ {k}) = {_g(cdf, 6)}"),
             S("Step 4: Mean and variance", f"Mean = np = {_g(n * p)}", f"Variance = npq = {_g(n * p * (1 - p))}")]
    return {"pmf": pmf(k), "cdf": cdf, "mean": n * p, "variance": n * p * (1 - p), "steps": steps}

def poisson(lam, k):
    if lam <= 0 or int(k) != k or k < 0:
        raise ValueError("Need lambda > 0 and a whole k >= 0.")
    k = int(k)
    pmf = lambda i: math.exp(-lam) * lam ** i / math.factorial(i)
    cdf = sum(pmf(i) for i in range(k + 1))
    steps = [S("Step 1: Formula", "P(X = k) = e^(−λ) × λ^k ÷ k!", "λ is the average number of events."),
             S("Step 2: Put in the numbers", f"P(X = {k}) = e^(−{_g(lam)}) × {_g(lam)}^{k} ÷ {k}! = {_g(pmf(k), 6)}", f"P(X ≤ {k}) = {_g(cdf, 6)}"),
             S("Step 3: Mean and variance", f"For a Poisson distribution mean = variance = λ = {_g(lam)}")]
    return {"pmf": pmf(k), "cdf": cdf, "mean": lam, "variance": lam, "steps": steps}

def _phi(z):
    return 0.5 * (1 + math.erf(z / math.sqrt(2)))

def normal(mean, sd, x, x2=None):
    if sd <= 0:
        raise ValueError("Standard deviation must be positive.")
    z = (x - mean) / sd
    steps = [S("Step 1: Convert to a z-score", "Formula: z = (x − mean) ÷ standard deviation. It says how many standard deviations x is from the mean.", f"z = ({_g(x)} − {_g(mean)}) ÷ {_g(sd)} = {_g(z)}"),
             S("Step 2: Look up the area", f"P(X ≤ {_g(x)}) = Φ({_g(z)}) = {_g(_phi(z), 6)}", f"P(X > {_g(x)}) = 1 − {_g(_phi(z), 6)} = {_g(1 - _phi(z), 6)}")]
    out = {"z": z, "p_less": _phi(z), "p_greater": 1 - _phi(z)}
    if x2 is not None:
        z2 = (x2 - mean) / sd; lo, hi = sorted((z, z2))
        out["p_between"] = _phi(hi) - _phi(lo)
        steps.append(S("Step 3: Probability between the two values", f"P({_g(min(x, x2))} < X < {_g(max(x, x2))}) = Φ({_g(hi)}) − Φ({_g(lo)}) = {_g(out['p_between'], 6)}"))
    out["steps"] = steps
    return out

REGISTRY = {"descriptive": descriptive, "freq": freq_discrete, "grouped": grouped, "correlation": correlation_regression,
            "spearman": spearman, "t_single": t_single, "t_two": t_two_means, "f_test": f_test, "chi_gof": chi_gof,
            "chi_ind": chi_independence, "anova": anova_oneway, "binomial": binomial, "poisson": poisson, "normal": normal}
