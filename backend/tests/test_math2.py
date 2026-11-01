import math, statistics as st
import pytest
from scipy import stats
from backend import mathengine as m

def close(a, b, t=1e-6): return abs(a - b) < t

BP_X, BP_F = [112, 113, 118, 120, 125, 130], [12, 14, 10, 16, 4, 14]
def expand(x, f): return [a for a, b in zip(x, f) for _ in range(int(b))]

def test_freq_sd_cv_matches_expanded_data():
    d = expand(BP_X, BP_F); r = m.freq_discrete(BP_X, BP_F, "sd_cv")
    assert close(r["mean"], st.fmean(d)) and close(r["sd"], st.pstdev(d)) and close(r["cv_percent"], st.pstdev(d) / st.fmean(d) * 100)
    assert r["steps"][0]["table"]["rows"][-1][0] == "Total"

def test_range_qd_md():
    r = m.freq_discrete([35, 45, 18, 25, 48], [3, 4, 5, 4, 3], "range")
    assert r["range"] == 30 and close(r["coeff_range"], 30 / 66)
    W, F = [28, 30, 40, 45, 22, 20, 35, 48, 50], [10, 5, 8, 7, 6, 3, 4, 7, 5]
    q = m.freq_discrete(W, F, "qd")
    assert (q["q1"], q["q3"], q["qd"]) == (28, 45, 8.5) and close(q["coeff_qd"], 17 / 73)
    d = expand(W, F); mean = st.fmean(d)
    md = m.freq_discrete(W, F, "md")
    assert close(md["md"], sum(abs(v - mean) for v in d) / len(d))
    med = m.freq_discrete(W, F, "md", about="median")
    assert close(med["md"], sum(abs(v - med["about"]) for v in d) / len(d))

def test_grouped_skewness_and_mode():
    cl = ["0-5", "5-10", "10-15", "15-20", "20-25", "25-30", "30-35"]; f = [6, 5, 8, 10, 7, 13, 9]
    r = m.grouped(cl, f, "skew")
    mids = [2.5, 7.5, 12.5, 17.5, 22.5, 27.5, 32.5]; d = expand(mids, f)
    assert close(r["mode"], 28) and close(r["mean"], st.fmean(d)) and close(r["sd"], st.pstdev(d))
    assert close(r["skewness"], (st.fmean(d) - 28) / st.pstdev(d))
    with pytest.raises(ValueError): m.grouped(["0-5", "5-10", "10-15", "15-20", "20-25", "25-30", "Above 30"], f, "skew")
    with pytest.raises(ValueError): m.grouped(["0-5", "5-12"], [1, 2], "skew")

def test_regression_with_estimate():
    x, y = [2, 3, 4, 5, 6, 7, 8], [40, 45, 55, 64, 75, 80, 87]
    r = m.correlation_regression(x, y, 5.5); lr = st.linear_regression(x, y)
    assert close(r["y_on_x"]["b"], lr.slope) and close(r["y_on_x"]["a"], lr.intercept)
    assert close(r["estimate"], lr.intercept + lr.slope * 5.5) and close(r["r"], st.correlation(x, y))

def test_spearman():
    x, y = [86, 97, 99, 100, 101, 103, 106, 110, 112, 113], [0, 20, 28, 27, 50, 29, 7, 17, 6, 12]
    assert close(m.spearman(x, y)["rho"], stats.spearmanr(x, y).statistic)
    with pytest.raises(ValueError): m.spearman([1, 1, 2], [1, 2, 3])

def test_t_single_filling_machine():
    d = [4.7, 4.9, 5.0, 5.1, 5.4, 5.2, 4.6, 5.1, 4.6, 4.7]
    r = m.t_single(d, 5, 0.05, 2, table_value=2.262); ref = stats.ttest_1samp(d, 5)
    assert close(r["t"], ref.statistic) and close(r["p_value"], ref.pvalue) and r["df"] == 9 and r["reject_h0"] is False
    assert abs(m.t_single(d, 5)["table_value"] - 2.262) < 0.001

def test_t_two_means_both_sd_conventions():
    a = m.t_two_means(20, 170, 20, 18, 205, 25, 0.01, 2, "n", 2.58)
    S2 = (20 * 400 + 18 * 625) / 36
    assert close(a["t"], (170 - 205) / (math.sqrt(S2) * math.sqrt(1 / 20 + 1 / 18))) and a["reject_h0"] and a["df"] == 36
    b = m.t_two_means(20, 170, 20, 18, 205, 25, 0.01, 2, "n-1")
    ref = stats.ttest_ind_from_stats(170, 20, 20, 205, 25, 18, equal_var=True)
    assert close(b["t"], ref.statistic) and abs(b["table_value"] - 2.719) < 0.001

def test_f_test_two_variances():
    s1, s2 = [5, 6, 8, 1, 12, 4, 3, 9, 6, 10], [2, 3, 6, 8, 1, 10, 2, 8]
    r = m.f_test(s1, s2, 0.05)
    assert close(r["F"], st.variance(s2) / st.variance(s1)) and r["df"] == [7, 9]
    assert abs(r["table_value"] - 3.29) < 0.01 and r["reject_h0"] is False

def test_chi_gof_die():
    r = m.chi_gof([15, 18, 22, 20, 25, 20], None, 0.05)
    assert close(r["chi_square"], 2.9) and r["df"] == 5 and abs(r["table_value"] - 11.07) < 0.01 and not r["reject_h0"]
    with pytest.raises(ValueError): m.chi_gof([10, 10], [5, 5])

def test_chi_independence_and_anova():
    t = [[20, 15, 30], [10, 25, 20]]
    assert close(m.chi_independence(t)["chi_square"], stats.chi2_contingency(t, correction=False)[0])
    g = [[6, 8, 4, 5], [8, 12, 9, 11], [13, 9, 11, 8]]
    assert close(m.anova_oneway(g)["F"], stats.f_oneway(*g).statistic)

def test_input_errors():
    for fn, a in [(m.t_single, ([1], 0)), (m.f_test, ([1, 2], [3])), (m.freq_discrete, ([1, 2], [1])), (m.chi_independence, ([[1, 2]],)), (m.anova_oneway, ([[1, 2]],))]:
        with pytest.raises(ValueError): fn(*a)
    with pytest.raises(ValueError): m.t_single([1, 2, 3], 0, alpha=2)
    with pytest.raises(ValueError): m.descriptive(["a", "b"])
