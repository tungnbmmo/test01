# Quy trinh kiem chung cho UJ_EBTA (dang ky truoc, theo EBTA)

Muc dich: **quyet dinh truoc khi nhin ket qua**, de khong tu lua minh bang data-mining bias.
Khong thay doi quy trinh nay sau khi da xem ket qua.

## 1. Vu tru quy tac (dang ky truoc)
Quy tac: Donchian breakout H4, doi xung Long/Short, thoat bang kenh doi nghich = EntryN/2,
SL co dinh = 3 x ATR(14), rui ro 0.5%/lenh.

Tham so duy nhat duoc khao sat: `EntryN` thuoc {20, 40, 60, 80, 120} -> **N = 5 quy tac**.
Moi lan chay phai ghi `python ebta_validator.py trial <ten> --params "EntryN=..,RunTag=.."`.
Neu sau nay ban them quy tac/tham so moi, N tang len va p-value phai tinh lai voi N moi.

## 2. Phan chia du lieu
Du lieu "trinh nguyen" chi dung duoc MOT lan (EBTA, Chuong 6).
- **Train**: dung de so sanh 5 quy tac. Cang dai cang tot (nen >= 8-10 nam neu Exness cho lich su
  M1; tren tai khoan cua ban hay thu keo Date lui ve 2015-2019).
- **Test**: chon DUNG 1 quy tac tot nhat o Train, chay 1 lan tren Test. Khong chinh lai.
- **Validation / Incubation**: cua so cuoi cung chi mo 1 lan. Vi giai doan 2023-2026 ban da nhin
  ket qua cua nhieu EA truoc do nen khong con "trinh nguyen" -> dung **forward test tren Demo**
  (du lieu thuc su moi) it nhat 8-12 tuan lam buoc xac nhan cuoi.

Goi y neu chi co 2023-2026: Train 2023.01-2024.12 | Test 2025.01-2025.06 | Demo forward tu nay.
(Mau nho -> cong cu se cho p lon; do la ket qua trung thuc, khong phai loi.)

## 3. Cach chay
Tester: `UJ_EBTA`, USDJPYm, `Tf=H4`, Every tick based on real ticks, Optimization **Disabled**.
Voi moi EntryN trong {20,40,60,80,120}: chay doan Train voi `RunTag=train`.
EA tu ghi `trades_UJEBTA_N<EntryN>_train.csv` vao Common\Files.

```bash
python ebta_validator.py dailypnl trades_UJEBTA_N*_train.csv --out train_pnl.csv
python ebta_validator.py wrc train_pnl.csv --iter 5000 --block 5 --trials trials.csv
```

## 4. Quy tac quyet dinh (dat truoc)
1. `wrc` best-of-5 tren Train: **p hieu chinh < 0.05** moi duoc coi la co bang chung.
   Neu khong: DUNG. Khong thu them bien the de "cuu" no (se tang N, lam tang bias).
2. Neu dat: chay quy tac tot nhat tren Test voi `RunTag=test`; yeu cau loi nhuan duong,
   PF > 1.2 va drawdown trong gioi han tu `mcdd` (p95 max DD <= 25%).
3. Neu dat: forward Demo >= 8-12 tuan, so sanh voi phan phoi cua `mcdd`.
4. Chi sau do moi xet tien that, von nho, rui ro 0.25%.

## 5. Kiem tra benchmark (position bias)
Chay `positions` + `benchmark` cho quy tac duoc chon. Neu loi nhuan quan sat chu yeu den tu
`expected_random_mean` (thien Long x xu huong tang cua USDJPY) thi do khong phai loi the cua quy tac.

## 6. Ky vong trung thuc
Trong case study cua sach, 0/6.402 quy tac co y nghia thong ke tren S&P 500 sau khi hieu chinh.
Ket qua "khong co bang chung" la mot ket qua hop le va huu ich.
