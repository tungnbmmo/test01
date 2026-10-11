import os
import sys

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import ebta_validator as ev  # noqa: E402


# ---------- Chuong 1: benchmark / position bias ----------

def test_benchmark_identity_observed_minus_expected_equals_detrended():
    rng = np.random.default_rng(0)
    market = rng.normal(0.0005, 0.01, 5000)
    pos = np.where(rng.random(5000) < 0.9, 1.0, -1.0)
    s = ev.benchmark_stats(pos, market)
    assert s["observed_mean"] - s["expected_random_mean"] == pytest.approx(s["detrended_mean"], abs=1e-12)
    assert s["expected_random_mean"] == pytest.approx((s["p_long"] - s["p_short"]) * s["market_avg_change"])


def test_random_long_biased_rule_looks_profitable_but_detrended_is_not():
    rng = np.random.default_rng(1)
    market = rng.normal(0.001, 0.005, 20000)          # xu huong tang ro ret
    pos = np.where(rng.random(20000) < 0.9, 1.0, -1.0)
    s = ev.benchmark_stats(pos, market)
    assert s["observed_mean"] > 0.0006                 # nhin co ve co loi nhuan
    assert abs(s["detrended_mean"]) < 0.0001           # sau khi khu xu huong ~ 0
    assert s["naive_p_value"] > 0.01


def test_benchmark_length_mismatch():
    with pytest.raises(ValueError):
        ev.benchmark_stats(np.ones(3), np.ones(4))


# ---------- Chuong 6: best-of-N ----------

def _type1_rate(test_fn, n_experiments=150, t=300, n_rules=20, seed=0):
    rng = np.random.default_rng(seed)
    rejects = 0
    for k in range(n_experiments):
        market = rng.normal(0.0, 0.01, t)
        pos = np.where(rng.random((t, n_rules)) < 0.5, 1.0, -1.0)
        p = test_fn(pos, market, k)
        rejects += p < 0.05
    return rejects / n_experiments


def test_mc_permutation_controls_type_I_error_for_best_of_N():
    rate = _type1_rate(lambda pos, m, k: ev.mc_permutation_test(pos, m, 199, seed=k)["best_adjusted_p"])
    assert rate <= 0.12


def test_uncorrected_best_of_N_is_wildly_anticonservative():
    rate = _type1_rate(lambda pos, m, k: ev.mc_permutation_test(pos, m, 199, seed=k)["best_uncorrected_p"])
    assert rate > 0.4      # 20 quy tac => chon cai tot nhat gan nhu luon "co y nghia" neu khong hieu chinh


def test_mc_permutation_detects_real_edge():
    rng = np.random.default_rng(5)
    t = 2000
    market = rng.normal(0, 0.01, t)
    pos = np.where(rng.random((t, 30)) < 0.5, 1.0, -1.0)
    pos[:, 7] = np.where(rng.random(t) < 0.6, np.sign(market), -np.sign(market))
    res = ev.mc_permutation_test(pos, market, 499, seed=2)
    assert res["best_index"] == 7
    assert res["best_adjusted_p"] < 0.01


def test_mc_permutation_same_permutation_preserves_correlation():
    # hai quy tac giong het nhau: max khong "tang them" so voi 1 quy tac
    rng = np.random.default_rng(3)
    t = 400
    market = rng.normal(0, 0.01, t)
    one = np.where(rng.random(t) < 0.5, 1.0, -1.0)
    r1 = ev.mc_permutation_test(one, market, 499, seed=4)
    r2 = ev.mc_permutation_test(np.column_stack([one, one]), market, 499, seed=4)
    assert r2["best_adjusted_p"] == pytest.approx(r1["best_adjusted_p"], abs=1e-9)


def test_reality_check_controls_type_I_error():
    def fn(pos, m, k):
        returns = pos * m[:, None]                      # loi nhuan = vi the x thi truong, ky vong 0
        return ev.reality_check(returns, 199, seed=k)["best_adjusted_p"]
    assert _type1_rate(fn) <= 0.12


def test_reality_check_detects_real_edge_and_block_mode_runs():
    rng = np.random.default_rng(8)
    t = 1000
    r = rng.normal(0, 1, (t, 15))
    r[:, 3] += 0.25
    res = ev.reality_check(r, 499, seed=1)
    assert res["best_index"] == 3 and res["best_adjusted_p"] < 0.02
    res_b = ev.reality_check(r, 199, mean_block=10, seed=1)
    assert res_b["best_index"] == 3


def test_reality_check_single_rule_matches_N_equals_1():
    rng = np.random.default_rng(9)
    r = rng.normal(0.1, 1, 500)
    res = ev.reality_check(r, 499, seed=1)
    assert res["n_rules"] == 1
    assert res["best_adjusted_p"] == pytest.approx(res["best_uncorrected_p"])


def test_demo_shows_data_mining_bias():
    null = ev.run_demo(n_rules=200, n_bars=2000, seed=1, n_iter=300)
    assert null["naive_best_p"] < 0.05 < null["best_adjusted_p"]
    edge = ev.run_demo(n_rules=200, n_bars=2000, seed=1, n_iter=300, with_edge=True)
    assert edge["best_adjusted_p"] < 0.05


# ---------- Monte Carlo drawdown ----------

def test_drawdown_zero_for_all_wins():
    r = ev.monte_carlo_drawdown([10, 20, 5, 7], initial_equity=1000, n_iter=200, seed=1)
    assert r["max_dd_percentiles"]["p99"] == 0.0
    assert r["prob_loss"] == 0.0


def test_drawdown_shuffle_keeps_final_equity_and_orders_percentiles():
    pnl = [100, -50, 30, -80, 60, -20, 40, -10]
    r = ev.monte_carlo_drawdown(pnl, initial_equity=1000, n_iter=500, mode="shuffle", seed=2)
    assert r["final_equity_percentiles"]["p50"] == pytest.approx(1000 + sum(pnl))
    p = r["max_dd_percentiles"]
    assert p["p50"] <= p["p75"] <= p["p90"] <= p["p95"] <= p["p99"]
    assert 0 <= p["p99"] <= 1
    assert r["actual_max_dd"] > 0


def test_drawdown_bootstrap_mode_and_bad_input():
    r = ev.monte_carlo_drawdown([10, -5, 3], 100, 200, mode="bootstrap", seed=1)
    assert r["mode"] == "bootstrap"
    with pytest.raises(ValueError):
        ev.monte_carlo_drawdown([], 100)
    with pytest.raises(ValueError):
        ev.monte_carlo_drawdown([1], 100, mode="x")


# ---------- Chuyen doi du lieu ----------

def _bars():
    times = pd.date_range("2024-01-01 00:00", periods=10, freq="h")
    return pd.DataFrame({"time": times.strftime("%Y.%m.%d %H:%M:%S"),
                         "close": [100, 101, 102, 101, 100, 99, 100, 101, 102, 103.0]})


def test_trades_to_positions_basic():
    trades = pd.DataFrame({
        "open_time": pd.to_datetime(["2024-01-01 01:00", "2024-01-01 06:00"]),
        "close_time": pd.to_datetime(["2024-01-01 03:00", "2024-01-01 08:00"]),
        "direction": [1, -1],
    })
    out = ev.trades_to_positions(trades, _bars())
    pos = dict(zip(out["time"].dt.hour, out["position"]))
    assert pos[1] == 1 and pos[2] == 1 and pos[3] == 0
    assert pos[6] == -1 and pos[7] == -1 and pos[8] == 0
    assert out["market_return"].iloc[0] == pytest.approx(101 / 100 - 1)


def test_load_trades_parses_mt5_time_and_direction(tmp_path):
    f = tmp_path / "t.csv"
    f.write_text("open_time,close_time,direction,volume,open_price,close_price,profit\n"
                 "2024.01.02 09:00:00,2024.01.02 15:30:00,1,0.1,150.1,150.5,40\n"
                 "2024.01.03 09:00:00,2024.01.03 12:00:00,-1,0.1,150.5,150.8,-30\n")
    df = ev.load_trades(str(f))
    assert df["close_time"].iloc[0] == pd.Timestamp("2024-01-02 15:30:00")
    assert list(df["direction"]) == [1, -1]


def test_daily_pnl_aligns_rules_on_common_calendar(tmp_path):
    a = tmp_path / "A.csv"
    b = tmp_path / "B.csv"
    a.write_text("close_time,profit\n2024.01.02 10:00:00,10\n2024.01.04 10:00:00,-5\n")
    b.write_text("close_time,profit\n2024.01.03 10:00:00,7\n2024.01.05 10:00:00,2\n2024.01.05 12:00:00,1\n")
    out = ev.trades_to_daily_pnl({"A": str(a), "B": str(b)})
    assert out.shape == (4, 2)
    assert out.loc["2024-01-05", "B"] == 3
    assert out.loc["2024-01-03", "A"] == 0


# ---------- So quy tac da thu ----------

def test_trials_log_and_warning(tmp_path):
    f = str(tmp_path / "trials.csv")
    assert ev.count_trials(f) == 0
    assert ev.log_trial(f, "cfg1", "ema=50") == 1
    assert ev.log_trial(f, "cfg2", "ema=100") == 2
    assert ev._trials_warning(1, f) is not None
    assert ev._trials_warning(2, f) is None
    assert ev._trials_warning(1, None) is None


# ---------- CLI ----------

def test_cli_end_to_end(tmp_path, capsys):
    rng = np.random.default_rng(0)
    t = 500
    market = rng.normal(0, 0.01, t)
    pos = pd.DataFrame(np.where(rng.random((t, 5)) < 0.5, 1, -1), columns=list("abcde"))
    pos.insert(0, "market_return", market)
    pf = tmp_path / "pos.csv"
    pos.to_csv(pf, index=False)
    assert ev.main(["mcperm", str(pf), "--iter", "99", "--seed", "1"]) == 0
    assert "p-value DA hieu chinh" in capsys.readouterr().out

    ret = pd.DataFrame(rng.normal(0, 1, (300, 4)), columns=list("wxyz"))
    rf = tmp_path / "ret.csv"
    ret.to_csv(rf, index=False)
    assert ev.main(["wrc", str(rf), "--iter", "99", "--seed", "1", "--json"]) == 0
    assert "best_adjusted_p" in capsys.readouterr().out

    tr = tmp_path / "tr.csv"
    pd.DataFrame({"profit": [10, -4, 6, -2, 8, -9]}).to_csv(tr, index=False)
    assert ev.main(["mcdd", str(tr), "--iter", "100", "--seed", "1"]) == 0
    assert "Max drawdown thuc te" in capsys.readouterr().out
