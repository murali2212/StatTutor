import pytest
from backend import mathengine as m

def approx(a, b, t=1e-4): return abs(a - b) < t

def test_descriptive_population():
    r = m.descriptive([2, 4, 4, 4, 5, 5, 7, 9], sample=False)
    assert r["mean"] == 5 and r["median"] == 4.5 and r["mode"] == [4]
    assert r["variance"] == 4 and r["sd"] == 2 and r["q1"] == 4 and r["q3"] == 6

def test_descriptive_sample():
    r = m.descriptive([2, 4, 4, 4, 5, 5, 7, 9])
    assert approx(r["variance"], 32 / 7)

def test_no_mode_and_odd_median():
    r = m.descriptive([1, 2, 3, 4, 5])
    assert r["mode"] == [] and r["median"] == 3 and r["q1"] == 1.5 and r["q3"] == 4.5

def test_correlation_regression():
    r = m.correlation_regression([1, 2, 3, 4, 5], [2, 4, 5, 4, 5])
    assert approx(r["r"], 0.7746) and approx(r["y_on_x"]["b"], 0.6) and approx(r["y_on_x"]["a"], 2.2)

def test_binomial():
    r = m.binomial(10, 0.5, 3)
    assert approx(r["pmf"], 120 / 1024) and approx(r["cdf"], 176 / 1024)

def test_poisson():
    assert approx(m.poisson(2, 0)["pmf"], 0.135335, 1e-6)

def test_normal():
    assert approx(m.normal(0, 1, 1.96)["p_less"], 0.9750, 1e-4)
    assert approx(m.normal(50, 10, 40, 60)["p_between"], 0.6827, 1e-4)

def test_bad_input():
    with pytest.raises(ValueError): m.descriptive([])
    with pytest.raises(ValueError): m.descriptive([3], sample=True)
    with pytest.raises(ValueError): m.correlation_regression([1, 1, 1], [1, 2, 3])
    with pytest.raises(ValueError): m.binomial(5, 1.5, 2)
    with pytest.raises(ValueError): m.normal(0, 0, 1)
