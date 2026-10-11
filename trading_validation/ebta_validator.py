"""Cong cu kiem dinh thong ke cho EA/quy tac giao dich, dua tren
David Aronson - "Evidence-Based Technical Analysis" (2007).

Cac y tuong duoc cai dat:
  * Chuong 1 : benchmark = quy tac khong co suc du bao; khu xu huong de loai bo
               anh huong cua position bias x xu huong thi truong.
  * Chuong 6 : data-mining bias. Kiem dinh best-of-N bang
               - Monte Carlo permutation (Masters): ghep ngau nhien dau ra quy tac
                 voi bien dong thi truong, CUNG mot hoan vi cho moi quy tac.
               - Bootstrap kieu White's Reality Check: tru trung binh tung quy tac
                 ve 0 (H0) roi lay mau lai, cung chi so thoi gian cho moi quy tac.
  * Dem so quy tac da thu (trials.csv): khong dem du N thi p-value bi danh gia thap.
  * Monte Carlo drawdown tu danh sach lenh.

Luu y: day la cong cu thong ke, khong du doan loi nhuan. Ket qua "khong co y nghia
thong ke" khong chung minh quy tac vo dung, chi la khong du bang chung.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import os
import sys
from typing import Dict, List, Optional, Sequence

import numpy as np
import pandas as pd

# --------------------------------------------------------------------------
# Tien ich
# --------------------------------------------------------------------------

def _rng(seed: Optional[int]) -> np.random.Generator:
    return np.random.default_rng(seed)


def _norm_sf(z: float) -> float:
    """P(Z > z) cho phan phoi chuan."""
    return 0.5 * math.erfc(z / math.sqrt(2.0))


def _parse_time(series: pd.Series) -> pd.Series:
    """Doc thoi gian MT5 ('2026.10.10 21:23:02') hoac ISO."""
    out = pd.to_datetime(series, format="%Y.%m.%d %H:%M:%S", errors="coerce")
    if out.isna().any():
        alt = pd.to_datetime(series, errors="coerce")
        out = out.fillna(alt)
    return out


def _as_2d(x: np.ndarray) -> np.ndarray:
    x = np.asarray(x, dtype=float)
    return x[:, None] if x.ndim == 1 else x


# --------------------------------------------------------------------------
# 1. Benchmark va khu xu huong (Chuong 1)
# --------------------------------------------------------------------------

def benchmark_stats(positions: np.ndarray, market: np.ndarray) -> Dict[str, float]:
    """Phan tich 1 quy tac: position bias, loi nhuan ky vong cua tin hieu ngau nhien.

    positions: mang {-1, 0, +1} moi bar (vi the nam giu trong bar do)
    market   : loi nhuan thi truong moi bar (cung do dai)

    ER (ngau nhien)  = [p(L) - p(S)] * ADC          (cong thuc trong sach)
    Detrended mean   = mean(pos * (market - ADC))   = observed - ER
    """
    pos = np.asarray(positions, dtype=float)
    mkt = np.asarray(market, dtype=float)
    if pos.shape != mkt.shape:
        raise ValueError("positions va market phai cung do dai")
    t = len(pos)
    p_long = float(np.mean(pos > 0))
    p_short = float(np.mean(pos < 0))
    adc = float(np.mean(mkt))
    observed = float(np.mean(pos * mkt))
    expected_random = (p_long - p_short) * adc
    det = pos * (mkt - adc)
    det_mean = float(np.mean(det))
    det_std = float(np.std(det, ddof=1)) if t > 1 else float("nan")
    t_stat = det_mean / (det_std / math.sqrt(t)) if det_std and det_std > 0 else float("nan")
    return {
        "bars": t,
        "p_long": p_long,
        "p_short": p_short,
        "p_flat": 1.0 - p_long - p_short,
        "market_avg_change": adc,
        "observed_mean": observed,
        "expected_random_mean": expected_random,
        "detrended_mean": det_mean,
        "naive_t_stat": t_stat,
        "naive_p_value": _norm_sf(t_stat) if not math.isnan(t_stat) else float("nan"),
    }


# --------------------------------------------------------------------------
# 2. Monte Carlo permutation best-of-N (Chuong 6, phuong phap Masters)
# --------------------------------------------------------------------------

def mc_permutation_test(
    positions: np.ndarray,
    market: np.ndarray,
    n_iter: int = 2000,
    seed: Optional[int] = None,
) -> Dict[str, object]:
    """Kiem dinh best-of-N bang hoan vi ngau nhien.

    H0: dau ra cua tat ca N quy tac khong lien quan den bien dong thi truong.
    Moi vong lap: hoan vi loi nhuan thi truong (cung hoan vi cho moi quy tac de giu
    cau truc tuong quan), tinh trung binh loi nhuan cua moi quy tac, lay MAX.
    p-value hieu chinh cua quy tac j = ty le vong lap co MAX >= trung binh quan sat cua j.
    """
    pos = _as_2d(positions)
    mkt = np.asarray(market, dtype=float)
    t, n = pos.shape
    if len(mkt) != t:
        raise ValueError("positions va market phai cung so bar")
    if n_iter < 1:
        raise ValueError("n_iter phai >= 1")

    observed = pos.T @ mkt / t                      # (N,)
    rng = _rng(seed)
    null_max = np.empty(n_iter)
    null_each = np.empty((n_iter, n))
    for b in range(n_iter):
        perm = rng.permutation(t)
        means = pos.T @ mkt[perm] / t
        null_each[b] = means
        null_max[b] = means.max()

    adj_p = (1.0 + (null_max[:, None] >= observed[None, :]).sum(axis=0)) / (n_iter + 1.0)
    single_p = (1.0 + (null_each >= observed[None, :]).sum(axis=0)) / (n_iter + 1.0)
    best = int(np.argmax(observed))
    return {
        "method": "mc_permutation",
        "n_rules": n,
        "n_obs": t,
        "n_iter": n_iter,
        "observed_mean": observed,
        "best_index": best,
        "best_mean": float(observed[best]),
        "adjusted_p": adj_p,             # da hieu chinh data-mining bias
        "uncorrected_p": single_p,       # kiem dinh tung quy tac rieng le (SAI neu da chon best-of-N)
        "best_adjusted_p": float(adj_p[best]),
        "best_uncorrected_p": float(single_p[best]),
        "null_max": null_max,
    }


# --------------------------------------------------------------------------
# 3. Bootstrap kieu White's Reality Check (Chuong 6)
# --------------------------------------------------------------------------

def _bootstrap_indices(t: int, n_boot: int, rng: np.random.Generator,
                       mean_block: Optional[float]) -> np.ndarray:
    """Chi so lay mau lai (n_boot, t). iid neu mean_block <= 1, nguoc lai stationary bootstrap."""
    if not mean_block or mean_block <= 1:
        return rng.integers(0, t, size=(n_boot, t))
    p = 1.0 / mean_block
    starts = rng.integers(0, t, size=(n_boot, t))
    new = rng.random((n_boot, t)) < p
    new[:, 0] = True
    idx = np.empty((n_boot, t), dtype=np.int64)
    idx[:, 0] = starts[:, 0]
    for k in range(1, t):
        idx[:, k] = np.where(new[:, k], starts[:, k], (idx[:, k - 1] + 1) % t)
    return idx


def reality_check(
    returns: np.ndarray,
    n_boot: int = 2000,
    mean_block: Optional[float] = None,
    seed: Optional[int] = None,
) -> Dict[str, object]:
    """Bootstrap best-of-N (tinh than White's Reality Check, thong ke = trung binh).

    returns: (T, N) loi nhuan theo ky cua N quy tac tren CUNG luoi thoi gian.
    H0: ky vong loi nhuan cua moi quy tac <= 0 (dung chan 0 = kho nhat de bac bo).
    """
    r = _as_2d(returns)
    t, n = r.shape
    if t < 2:
        raise ValueError("can it nhat 2 ky")
    means = r.mean(axis=0)
    centered = r - means
    rng = _rng(seed)
    idx = _bootstrap_indices(t, n_boot, rng, mean_block)
    null_each = np.empty((n_boot, n))
    for b in range(n_boot):
        null_each[b] = centered[idx[b]].mean(axis=0)
    null_max = null_each.max(axis=1)
    adj_p = (1.0 + (null_max[:, None] >= means[None, :]).sum(axis=0)) / (n_boot + 1.0)
    single_p = (1.0 + (null_each >= means[None, :]).sum(axis=0)) / (n_boot + 1.0)
    best = int(np.argmax(means))
    return {
        "method": "reality_check_bootstrap",
        "n_rules": n,
        "n_obs": t,
        "n_iter": n_boot,
        "observed_mean": means,
        "best_index": best,
        "best_mean": float(means[best]),
        "adjusted_p": adj_p,
        "uncorrected_p": single_p,
        "best_adjusted_p": float(adj_p[best]),
        "best_uncorrected_p": float(single_p[best]),
        "null_max": null_max,
    }


# --------------------------------------------------------------------------
# 4. Monte Carlo drawdown tu danh sach lenh
# --------------------------------------------------------------------------

def monte_carlo_drawdown(
    pnl: Sequence[float],
    initial_equity: float = 10000.0,
    n_iter: int = 5000,
    mode: str = "shuffle",
    seed: Optional[int] = None,
    dd_thresholds: Sequence[float] = (0.10, 0.20, 0.30),
) -> Dict[str, object]:
    """Phan phoi max drawdown / von cuoi khi thu tu lenh bi xao tron.

    mode='shuffle'   : hoan vi thu tu lenh (tong loi nhuan khong doi).
    mode='bootstrap' : lay mau lai co hoan lai (tong loi nhuan thay doi).
    Cong don loi nhuan tuyet doi (khoi luong co dinh). Khong tinh lai kep.
    """
    x = np.asarray(pnl, dtype=float)
    n = len(x)
    if n == 0:
        raise ValueError("danh sach lenh rong")
    if mode not in ("shuffle", "bootstrap"):
        raise ValueError("mode phai la 'shuffle' hoac 'bootstrap'")
    rng = _rng(seed)
    max_dd = np.empty(n_iter)
    final = np.empty(n_iter)
    chunk = max(1, int(2_000_000 // max(n, 1)))
    done = 0
    while done < n_iter:
        b = min(chunk, n_iter - done)
        if mode == "shuffle":
            paths = np.stack([rng.permutation(x) for _ in range(b)])
        else:
            paths = x[rng.integers(0, n, size=(b, n))]
        eq = initial_equity + np.cumsum(paths, axis=1)
        eq = np.concatenate([np.full((b, 1), initial_equity), eq], axis=1)
        peak = np.maximum.accumulate(eq, axis=1)
        dd = (peak - eq) / np.where(peak > 0, peak, np.nan)
        dd = np.nan_to_num(dd, nan=1.0)
        max_dd[done:done + b] = dd.max(axis=1)
        final[done:done + b] = eq[:, -1]
        done += b

    pct = (50, 75, 90, 95, 99)
    return {
        "n_trades": n,
        "n_iter": n_iter,
        "mode": mode,
        "initial_equity": initial_equity,
        "max_dd_percentiles": {f"p{q}": float(np.percentile(max_dd, q)) for q in pct},
        "final_equity_percentiles": {f"p{q}": float(np.percentile(final, q)) for q in (5, 25, 50, 75, 95)},
        "prob_loss": float(np.mean(final < initial_equity)),
        "prob_dd_exceeds": {f"{int(th * 100)}%": float(np.mean(max_dd > th)) for th in dd_thresholds},
        "actual_max_dd": _actual_max_dd(x, initial_equity),
    }


def _actual_max_dd(x: np.ndarray, initial_equity: float) -> float:
    eq = initial_equity + np.concatenate([[0.0], np.cumsum(x)])
    peak = np.maximum.accumulate(eq)
    return float(np.max((peak - eq) / np.where(peak > 0, peak, np.nan)))


# --------------------------------------------------------------------------
# 5. Chuyen doi du lieu: danh sach lenh -> vi the theo bar / P&L theo ngay
# --------------------------------------------------------------------------

def load_trades(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    df.columns = [c.strip().lower() for c in df.columns]
    for col in ("open_time", "close_time"):
        if col in df.columns:
            df[col] = _parse_time(df[col])
    if "direction" in df.columns:
        df["direction"] = df["direction"].map(_direction_to_int)
    return df


def _direction_to_int(v) -> int:
    if isinstance(v, str):
        s = v.strip().lower()
        if s in ("buy", "long", "1", "+1"):
            return 1
        if s in ("sell", "short", "-1"):
            return -1
        raise ValueError(f"direction khong hop le: {v!r}")
    return 1 if float(v) > 0 else -1


def trades_to_positions(trades: pd.DataFrame, bars: pd.DataFrame) -> pd.DataFrame:
    """Vi the {-1,0,1} cho tung bar tu danh sach lenh.

    bars: cot 'time' (gio MO bar) va 'close'. Bar i giu vi the neu gio mo bar nam trong
    [open_time, close_time). Sai so toi da ~1 bar moi dau lenh; dung bar H1/M15 la du.
    market_return = close_i / close_{i-1} - 1 (bar dau bi bo).
    """
    b = bars.copy()
    b.columns = [c.strip().lower() for c in b.columns]
    b["time"] = _parse_time(b["time"])
    b = b.sort_values("time").reset_index(drop=True)
    times = b["time"].to_numpy()
    pos = np.zeros(len(b))
    for row in trades.itertuples(index=False):
        s = np.searchsorted(times, np.datetime64(row.open_time), side="left")
        e = np.searchsorted(times, np.datetime64(row.close_time), side="left")
        if e > s:
            pos[s:e] += row.direction
    pos = np.sign(pos)
    ret = b["close"].pct_change()
    out = pd.DataFrame({"time": b["time"], "market_return": ret, "position": pos})
    return out.iloc[1:].reset_index(drop=True)


def trades_to_daily_pnl(trade_files: Dict[str, str]) -> pd.DataFrame:
    """Bang P&L theo ngay (hang = ngay, cot = cau hinh) tu nhieu file lenh.

    P&L duoc gan vao ngay dong lenh; ngay khong co lenh = 0 (cung luoi ngay cho moi quy tac).
    """
    series = {}
    for name, path in trade_files.items():
        df = load_trades(path)
        if "close_time" not in df.columns or "profit" not in df.columns:
            raise ValueError(f"{path}: can cot close_time va profit")
        d = df.dropna(subset=["close_time"]).copy()
        d["day"] = d["close_time"].dt.normalize()
        series[name] = d.groupby("day")["profit"].sum()
    if not series:
        raise ValueError("khong co file lenh nao")
    start = min(s.index.min() for s in series.values())
    end = max(s.index.max() for s in series.values())
    days = pd.bdate_range(start, end)
    out = pd.DataFrame({k: v.reindex(days, fill_value=0.0) for k, v in series.items()})
    out.index.name = "date"
    return out


# --------------------------------------------------------------------------
# 6. So quy tac da thu (trials.csv)
# --------------------------------------------------------------------------

TRIALS_COLUMNS = ["timestamp", "name", "params", "notes"]


def log_trial(path: str, name: str, params: str = "", notes: str = "") -> int:
    new = not os.path.exists(path)
    row = pd.DataFrame([[dt.datetime.now().isoformat(timespec="seconds"), name, params, notes]],
                       columns=TRIALS_COLUMNS)
    row.to_csv(path, mode="a", header=new, index=False)
    return count_trials(path)


def count_trials(path: str) -> int:
    if not os.path.exists(path):
        return 0
    return len(pd.read_csv(path))


# --------------------------------------------------------------------------
# 7. Bao cao
# --------------------------------------------------------------------------

def verdict(adjusted_p: float, alpha: float = 0.05) -> str:
    if adjusted_p < alpha:
        return (f"p hieu chinh = {adjusted_p:.4f} < {alpha}: du bang chung bac bo H0 "
                "(khong phai tat ca quy tac deu vo dung). Van can xac nhan tren du lieu out-of-sample.")
    return (f"p hieu chinh = {adjusted_p:.4f} >= {alpha}: KHONG du bang chung. "
            "Ket qua tot nhat co the chi la may man do da thu nhieu quy tac.")


def format_test(res: Dict[str, object], names: Optional[List[str]] = None, alpha: float = 0.05) -> str:
    n = res["n_rules"]
    names = names or [f"rule_{i}" for i in range(n)]
    best = res["best_index"]
    lines = [
        f"Phuong phap          : {res['method']}",
        f"So quy tac (N)       : {n}",
        f"So quan sat          : {res['n_obs']}",
        f"So vong lap          : {res['n_iter']}",
        f"Quy tac tot nhat     : {names[best]}  (trung binh/ky = {res['best_mean']:.6g})",
        f"p-value KHONG hieu chinh (sai khi chon best-of-N): {res['best_uncorrected_p']:.4f}",
        f"p-value DA hieu chinh data-mining bias          : {res['best_adjusted_p']:.4f}",
        "",
        verdict(res["best_adjusted_p"], alpha),
    ]
    if n > 1:
        order = np.argsort(res["adjusted_p"])[:10]
        lines += ["", "Top quy tac theo p hieu chinh:"]
        for i in order:
            lines.append(f"  {names[i]:<24} mean={res['observed_mean'][i]: .6g}  "
                         f"p_adj={res['adjusted_p'][i]:.4f}  p_raw={res['uncorrected_p'][i]:.4f}")
    return "\n".join(lines)


def _trials_warning(n_rules: int, trials_path: Optional[str]) -> Optional[str]:
    if not trials_path:
        return None
    n_logged = count_trials(trials_path)
    if n_logged > n_rules:
        return (f"CANH BAO: da ghi {n_logged} lan thu trong {trials_path} nhung chi dua vao {n_rules} quy tac. "
                "Thieu quy tac => p-value hieu chinh bi DANH GIA THAP (qua lac quan). "
                "Hay dua tat ca cau hinh da thu vao ma tran.")
    return None


# --------------------------------------------------------------------------
# 8. Demo mo phong: thay tan mat data-mining bias
# --------------------------------------------------------------------------

def run_demo(n_rules: int = 200, n_bars: int = 2000, seed: int = 1, n_iter: int = 1000,
             with_edge: bool = False, edge_accuracy: float = 0.60) -> Dict[str, object]:
    """Thi truong ngau nhien co xu huong tang; N quy tac ngau nhien thien Long."""
    rng = _rng(seed)
    market = rng.normal(0.0002, 0.005, n_bars)              # drift duong
    pos = np.where(rng.random((n_bars, n_rules)) < 0.65, 1.0, -1.0)   # thien Long
    if with_edge:
        informed = np.where(rng.random(n_bars) < edge_accuracy, np.sign(market), -np.sign(market))
        pos[:, 0] = informed
    res = mc_permutation_test(pos, market, n_iter=n_iter, seed=seed + 1)
    # p-value "thong thuong" cho quy tac tot nhat (t-test don le tren loi nhuan detrended)
    best = res["best_index"]
    bs = benchmark_stats(pos[:, best], market)
    res["naive_best_p"] = bs["naive_p_value"]
    res["benchmark_best"] = bs
    return res


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------

def _load_matrix(path: str, drop: Sequence[str]) -> pd.DataFrame:
    df = pd.read_csv(path)
    df.columns = [c.strip() for c in df.columns]
    drop_l = {d.lower() for d in drop}
    keep = [c for c in df.columns if c.lower() not in drop_l]
    return df[keep]


def _cmd_benchmark(a: argparse.Namespace) -> int:
    df = pd.read_csv(a.positions)
    df.columns = [c.strip().lower() for c in df.columns]
    pos_col = a.position_col
    s = benchmark_stats(df[pos_col].to_numpy(), df["market_return"].to_numpy())
    print(json.dumps(s, indent=2) if a.json else "\n".join(f"{k:<24}{v}" for k, v in s.items()))
    return 0


def _cmd_mcperm(a: argparse.Namespace) -> int:
    df = pd.read_csv(a.positions)
    df.columns = [c.strip() for c in df.columns]
    mcol = next((c for c in df.columns if c.lower() == "market_return"), None)
    if mcol is None:
        print("Can cot market_return", file=sys.stderr)
        return 2
    rule_cols = [c for c in df.columns if c.lower() not in ("time", "date", "market_return")]
    res = mc_permutation_test(df[rule_cols].to_numpy(), df[mcol].to_numpy(), a.iter, a.seed)
    warn = _trials_warning(len(rule_cols), a.trials)
    if a.json:
        print(json.dumps({k: (v.tolist() if isinstance(v, np.ndarray) else v) for k, v in res.items()
                          if k != "null_max"}, indent=2))
    else:
        print(format_test(res, rule_cols, a.alpha))
    if warn:
        print("\n" + warn)
    return 0


def _cmd_wrc(a: argparse.Namespace) -> int:
    df = _load_matrix(a.returns, ("time", "date"))
    res = reality_check(df.to_numpy(), a.iter, a.block, a.seed)
    warn = _trials_warning(df.shape[1], a.trials)
    if a.json:
        print(json.dumps({k: (v.tolist() if isinstance(v, np.ndarray) else v) for k, v in res.items()
                          if k != "null_max"}, indent=2))
    else:
        print(format_test(res, list(df.columns), a.alpha))
    if warn:
        print("\n" + warn)
    return 0


def _cmd_mcdd(a: argparse.Namespace) -> int:
    df = load_trades(a.trades)
    col = a.col
    r = monte_carlo_drawdown(df[col].to_numpy(), a.equity, a.iter, a.mode, a.seed)
    if a.json:
        print(json.dumps(r, indent=2))
        return 0
    print(f"So lenh: {r['n_trades']}  | che do: {r['mode']}  | von dau: {r['initial_equity']:.2f}")
    print(f"Max drawdown thuc te : {r['actual_max_dd'] * 100:.1f}%")
    print("Phan phoi max drawdown mo phong:")
    for k, v in r["max_dd_percentiles"].items():
        print(f"  {k:>4}: {v * 100:6.1f}%")
    print("Von cuoi mo phong:")
    for k, v in r["final_equity_percentiles"].items():
        print(f"  {k:>4}: {v:12.2f}")
    print(f"Xac suat von cuoi < von dau: {r['prob_loss'] * 100:.1f}%")
    for k, v in r["prob_dd_exceeds"].items():
        print(f"Xac suat max drawdown > {k}: {v * 100:.1f}%")
    return 0


def _cmd_positions(a: argparse.Namespace) -> int:
    out = trades_to_positions(load_trades(a.trades), pd.read_csv(a.bars))
    out.to_csv(a.out, index=False)
    print(f"Da ghi {len(out)} bar -> {a.out}")
    return 0


def _cmd_dailypnl(a: argparse.Namespace) -> int:
    files = {os.path.splitext(os.path.basename(p))[0]: p for p in a.trades}
    out = trades_to_daily_pnl(files)
    out.to_csv(a.out)
    print(f"Da ghi {out.shape[0]} ngay x {out.shape[1]} quy tac -> {a.out}")
    return 0


def _cmd_trial(a: argparse.Namespace) -> int:
    n = log_trial(a.file, a.name, a.params, a.notes)
    print(f"Da ghi. Tong so lan thu (N): {n}")
    return 0


def _cmd_count(a: argparse.Namespace) -> int:
    print(count_trials(a.file))
    return 0


def _cmd_demo(a: argparse.Namespace) -> int:
    for edge in (False, True):
        res = run_demo(a.rules, a.bars, a.seed, a.iter, with_edge=edge)
        tag = "CO 1 quy tac that su co loi the" if edge else "TAT CA quy tac deu vo dung"
        print(f"=== {tag} ===")
        print(f"N = {a.rules} quy tac thien Long tren thi truong co drift duong, {a.bars} bar")
        print(f"p-value thong thuong cho quy tac tot nhat : {res['naive_best_p']:.4f}")
        print(f"p-value hieu chinh best-of-N (MC permutation): {res['best_adjusted_p']:.4f}")
        print()
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0],
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("benchmark", help="position bias va benchmark cho 1 quy tac")
    s.add_argument("positions", help="CSV co cot market_return va cot vi the")
    s.add_argument("--position-col", default="position")
    s.add_argument("--json", action="store_true")
    s.set_defaults(func=_cmd_benchmark)

    s = sub.add_parser("mcperm", help="Monte Carlo permutation best-of-N")
    s.add_argument("positions", help="CSV: market_return + moi cot la vi the {-1,0,1} cua 1 quy tac")
    s.add_argument("--iter", type=int, default=2000)
    s.add_argument("--seed", type=int, default=None)
    s.add_argument("--alpha", type=float, default=0.05)
    s.add_argument("--trials", default=None, help="duong dan trials.csv de doi chieu so quy tac")
    s.add_argument("--json", action="store_true")
    s.set_defaults(func=_cmd_mcperm)

    s = sub.add_parser("wrc", help="Bootstrap best-of-N (Reality Check)")
    s.add_argument("returns", help="CSV: moi cot la loi nhuan theo ky cua 1 quy tac")
    s.add_argument("--iter", type=int, default=2000)
    s.add_argument("--block", type=float, default=None, help="do dai khoi trung binh (stationary bootstrap)")
    s.add_argument("--seed", type=int, default=None)
    s.add_argument("--alpha", type=float, default=0.05)
    s.add_argument("--trials", default=None)
    s.add_argument("--json", action="store_true")
    s.set_defaults(func=_cmd_wrc)

    s = sub.add_parser("mcdd", help="Monte Carlo drawdown tu danh sach lenh")
    s.add_argument("trades", help="CSV lenh (cot profit)")
    s.add_argument("--col", default="profit")
    s.add_argument("--equity", type=float, default=10000.0)
    s.add_argument("--iter", type=int, default=5000)
    s.add_argument("--mode", choices=("shuffle", "bootstrap"), default="shuffle")
    s.add_argument("--seed", type=int, default=None)
    s.add_argument("--json", action="store_true")
    s.set_defaults(func=_cmd_mcdd)

    s = sub.add_parser("positions", help="danh sach lenh + bar gia -> vi the theo bar")
    s.add_argument("trades")
    s.add_argument("bars", help="CSV bar: time, close")
    s.add_argument("--out", default="positions.csv")
    s.set_defaults(func=_cmd_positions)

    s = sub.add_parser("dailypnl", help="nhieu file lenh -> ma tran P&L theo ngay")
    s.add_argument("trades", nargs="+")
    s.add_argument("--out", default="daily_pnl.csv")
    s.set_defaults(func=_cmd_dailypnl)

    s = sub.add_parser("trial", help="ghi 1 lan thu cau hinh vao trials.csv")
    s.add_argument("name")
    s.add_argument("--params", default="")
    s.add_argument("--notes", default="")
    s.add_argument("--file", default="trials.csv")
    s.set_defaults(func=_cmd_trial)

    s = sub.add_parser("count", help="dem so lan thu da ghi")
    s.add_argument("--file", default="trials.csv")
    s.set_defaults(func=_cmd_count)

    s = sub.add_parser("demo", help="mo phong data-mining bias")
    s.add_argument("--rules", type=int, default=200)
    s.add_argument("--bars", type=int, default=2000)
    s.add_argument("--iter", type=int, default=1000)
    s.add_argument("--seed", type=int, default=1)
    s.set_defaults(func=_cmd_demo)
    return p


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    sys.exit(main())
