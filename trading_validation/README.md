# Cong cu kiem dinh thong ke cho EA (dua tren EBTA - D. Aronson)

Muc tieu: tra loi cau hoi **"ket qua backtest tot nhat cua toi co phai chi la may man vi
da thu qua nhieu cau hinh khong?"** thay vi chi nhin Profit Factor.

> Day la cong cu thong ke. Ket qua "khong co y nghia thong ke" khong chung minh quy tac vo
> dung; ket qua "co y nghia" khong dam bao loi nhuan trong tuong lai. Khong dung de tu tin
> giao dich tien that.

## Cai dat

```bash
pip install -r requirements.txt
python -m pytest -q            # 19 test
python ebta_validator.py demo  # xem data-mining bias bang mo phong
```

## Ba y tuong cot loi (Aronson)

1. **Benchmark dung** (Chuong 1). Quy tac ngau nhien thien Long tren thi truong di len van
   co loi nhuan ky vong duong: `ER = [p(Long) - p(Short)] x bien dong trung binh`.
   Lenh `benchmark` tach phan nay ra (khu xu huong).
2. **Data-mining bias** (Chuong 6). Thu nhieu cau hinh roi chon cai tot nhat thi ket qua do
   bi thoi phong co he thong. p-value thong thuong khi do **sai**. Dung `mcperm` hoac `wrc`.
3. **Dem moi cau hinh da thu** (`trial`). Khong dem du N thi p-value hieu chinh bi lac quan.

## Quy trinh de xuat

### Buoc 0: Ghi nhat ky moi lan thu cau hinh
Moi lan ban doi input roi chay lai backtest la 1 "quy tac" trong vu tru quy tac:

```bash
python ebta_validator.py trial cfg07 --params "AsiaEnd=8,RR=1.5" --notes "thu loc xu huong"
python ebta_validator.py count
```

### Buoc 1: Xuat danh sach lenh tu EA
Copy `mql5/TradeLogger.mqh` vao `MQL5/Include/` (hoac canh EA), roi trong EA:

```cpp
#include <TradeLogger.mqh>      // hoac "TradeLogger.mqh"
void OnDeinit(const int reason) { WriteTradeLog("trades_cfg07.csv", MagicNumber); }
```

File ra o `Terminal\Common\Files\` (MT5: File > Open Data Folder > len 1 cap > Common\Files).
Dinh dang: `open_time,close_time,direction,volume,open_price,close_price,profit`.

### Buoc 2a: Kiem dinh best-of-N tren P&L theo ngay (bootstrap, kieu White's Reality Check)
Dua **tat ca** cau hinh da thu vao:

```bash
python ebta_validator.py dailypnl trades_cfg*.csv --out daily_pnl.csv
python ebta_validator.py wrc daily_pnl.csv --iter 5000 --block 5 --trials trials.csv
```

### Buoc 2b: Monte Carlo permutation (can vi the theo bar)
1. Chay script `mql5/ExportBars.mq5` tren chart (H1 hoac M15) de co `bars_*.csv`.
2. Doi tung file lenh thanh vi the theo bar roi gop thanh mot bang (moi cot = 1 quy tac):

```python
import pandas as pd, ebta_validator as ev
bars = pd.read_csv("bars_USDJPY_H1.csv")
cols = {}
for name in ["cfg01", "cfg02", "cfg03"]:
    p = ev.trades_to_positions(ev.load_trades(f"trades_{name}.csv"), bars)
    cols[name] = p["position"].to_numpy()
df = pd.DataFrame(cols); df.insert(0, "market_return", p["market_return"].to_numpy())
df.to_csv("positions.csv", index=False)
```

```bash
python ebta_validator.py mcperm positions.csv --iter 5000 --trials trials.csv
python ebta_validator.py benchmark one_rule.csv   # position bias cho 1 quy tac
```

### Buoc 3: Drawdown co the xay ra
```bash
python ebta_validator.py mcdd trades_cfg07.csv --equity 10000 --iter 5000
```
Cho biet phan phoi max drawdown khi thu tu lenh bi xao tron (khong tinh lai kep).

## Cach doc ket qua
- `p DA hieu chinh < 0.05`: du bang chung bac bo H0 "khong quy tac nao co suc du bao".
  Van phai xac nhan tren du lieu **out-of-sample chua tung nhin**.
- `p DA hieu chinh >= 0.05`: khong du bang chung. Trong case study 6.402 quy tac cua sach,
  quy tac tot nhat co p thong thuong = 0.0005 nhung p hieu chinh = 0.82.

## Gioi han (hay nho)
- `trades_to_positions` xap xi vi the theo bar (sai so <= 1 bar moi dau lenh).
- Thong ke dung la trung binh loi nhuan; chua cai Hansen/Romano-Wolf hay thong ke
  studentized. Bootstrap iid bo qua tu tuong quan; dung `--block` de dung stationary bootstrap.
- Hoan vi cua MC pha vo tu tuong quan chuoi cua thi truong (dung nhu mo ta trong sach).
- Du lieu OOS "trinh nguyen" chi dung duoc **mot lan**: nhin kqua roi chinh la hong no.
- Cac file `.mq5/.mqh` chua duoc bien dich tren may tac gia; neu MetaEditor bao loi, hay gui lai.
