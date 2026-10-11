//+------------------------------------------------------------------+
//| UJ_EBTA.mq5 - Donchian trend rule (H4) thiet ke theo EBTA        |
//|                                                                  |
//| Nguyen tac (D. Aronson, Evidence-Based Technical Analysis):      |
//|  * Quy tac KHACH QUAN, lap trinh duoc, dau ra Long/Short/Neutral |
//|  * DOI XUNG hoan toan: dieu kien Long va Short gương nhau, de    |
//|    tranh position bias (Chuong 1)                                |
//|  * IT THAM SO (chi EntryN la tham so khao sat) de han che        |
//|    data-mining bias (Chuong 6)                                   |
//|  * Giao dich H4: lenh thua nen spread gan nhu khong dang ke      |
//|  * Ghi file lenh CSV de dua vao ebta_validator.py kiem dinh      |
//| Volume khong duoc dung (tick volume cua forex khong dang tin).   |
//+------------------------------------------------------------------+
#property copyright "Demo"
#property version   "1.00"
#property strict

#include <Trade/Trade.mqh>
CTrade trade;

//--- Quy tac (vu tru quy tac dang ky truoc: EntryN thuoc {20,40,60,80,120})
input ENUM_TIMEFRAMES Tf          = PERIOD_H4;
input int    EntryN               = 40;     // so nen kenh Donchian de VAO lenh
//     ExitN = EntryN/2 (kenh doi nghich ngan hon) -> khong phai tham so rieng
input int    AtrPeriod            = 14;
input double AtrStopMult          = 3.0;    // SL ban dau = AtrStopMult x ATR (co dinh, khong toi uu)

//--- Von va an toan
input double RiskPercent          = 0.5;    // % von rui ro moi lenh (tinh theo khoang SL)
input int    MaxSpreadPts         = 60;     // khong vao lenh neu spread lon hon
input double MaxDDPct             = 25.0;   // cau dao: dung giao dich neu equity giam % tu dinh
input ulong  MagicNumber          = 20260513;

//--- Ghi nhat ky de kiem dinh thong ke
input bool   WriteLog             = true;
input string RunTag               = "train"; // nhan doan du lieu: train / test / val

int      hAtr       = INVALID_HANDLE;
datetime lastBar    = 0;
double   peakEquity = 0.0;
bool     halted     = false;

//+------------------------------------------------------------------+
int OnInit()
{
   if(EntryN < 4) return INIT_PARAMETERS_INCORRECT;
   hAtr = iATR(_Symbol, Tf, AtrPeriod);
   if(hAtr == INVALID_HANDLE) return INIT_FAILED;
   trade.SetExpertMagicNumber(MagicNumber);
   trade.SetDeviationInPoints(30);
   peakEquity = AccountInfoDouble(ACCOUNT_EQUITY);
   return INIT_SUCCEEDED;
}

//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
   if(hAtr != INVALID_HANDLE) IndicatorRelease(hAtr);
}

//+------------------------------------------------------------------+
bool GetPosition(ulong &ticket)
{
   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      ulong t = PositionGetTicket(i);   // chon vi the de doc thuoc tinh
      if(t == 0) continue;
      if(PositionGetString(POSITION_SYMBOL) == _Symbol &&
         PositionGetInteger(POSITION_MAGIC) == (long)MagicNumber)
      {
         ticket = t;
         return true;
      }
   }
   return false;
}

//+------------------------------------------------------------------+
double CalcLot(double slDistance)
{
   double riskMoney = AccountInfoDouble(ACCOUNT_BALANCE) * RiskPercent / 100.0;
   double tickValue = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_VALUE);
   double tickSize  = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_SIZE);
   double minLot    = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
   double maxLot    = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MAX);
   double step      = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);
   if(tickValue <= 0 || tickSize <= 0 || slDistance <= 0) return minLot;

   double lossPerLot = slDistance / tickSize * tickValue;
   double lot = riskMoney / lossPerLot;
   lot = MathFloor(lot / step) * step;
   return MathMax(minLot, MathMin(maxLot, lot));
}

//+------------------------------------------------------------------+
void OnTick()
{
   // Chi quyet dinh 1 lan khi nen moi mo (tin hieu tren nen vua dong -> khong nhin truoc tuong lai)
   datetime barTime = iTime(_Symbol, Tf, 0);
   if(barTime == lastBar) return;
   lastBar = barTime;

   // --- Cau dao bao ve von ---
   double eq = AccountInfoDouble(ACCOUNT_EQUITY);
   if(eq > peakEquity) peakEquity = eq;
   if(!halted && peakEquity > 0 && eq < peakEquity * (1.0 - MaxDDPct / 100.0))
   {
      halted = true;
      PrintFormat("CAU DAO: equity %.2f < %.1f%% duoi dinh %.2f -> dung giao dich", eq, MaxDDPct, peakEquity);
   }

   ulong ticket = 0;
   bool  have   = GetPosition(ticket);
   if(halted)
   {
      if(have) trade.PositionClose(ticket);
      return;
   }

   // --- Du lieu: r[1] = nen vua dong; kenh tinh tren cac nen TRUOC nen tin hieu (shift 2..) ---
   int exitN = MathMax(2, EntryN / 2);
   int need  = EntryN + 5;
   MqlRates r[];
   ArraySetAsSeries(r, true);
   if(CopyRates(_Symbol, Tf, 0, need, r) < need) return;

   double atrBuf[];
   ArraySetAsSeries(atrBuf, true);
   if(CopyBuffer(hAtr, 0, 1, 1, atrBuf) < 1) return;
   double atr = atrBuf[0];
   if(atr <= 0) return;

   double entryHigh = r[2].high, entryLow = r[2].low;
   for(int i = 3; i <= EntryN + 1; i++)
   {
      if(r[i].high > entryHigh) entryHigh = r[i].high;
      if(r[i].low  < entryLow)  entryLow  = r[i].low;
   }
   double exitHigh = r[2].high, exitLow = r[2].low;
   for(int i = 3; i <= exitN + 1; i++)
   {
      if(r[i].high > exitHigh) exitHigh = r[i].high;
      if(r[i].low  < exitLow)  exitLow  = r[i].low;
   }
   double c1 = r[1].close;

   // --- Thoat lenh: dong cua pha kenh doi nghich ngan (doi xung Long/Short) ---
   if(have)
   {
      ENUM_POSITION_TYPE type = (ENUM_POSITION_TYPE)PositionGetInteger(POSITION_TYPE);
      bool exitLong  = (type == POSITION_TYPE_BUY  && c1 < exitLow);
      bool exitShort = (type == POSITION_TYPE_SELL && c1 > exitHigh);
      if(exitLong || exitShort)
      {
         if(trade.PositionClose(ticket)) have = false;
      }
   }
   if(have) return;

   // --- Vao lenh: dong cua pha kenh vao (doi xung Long/Short) ---
   if(SymbolInfoInteger(_Symbol, SYMBOL_SPREAD) > MaxSpreadPts) return;

   double ask    = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
   double bid    = SymbolInfoDouble(_Symbol, SYMBOL_BID);
   int    digits = (int)SymbolInfoInteger(_Symbol, SYMBOL_DIGITS);
   double slDist = AtrStopMult * atr;

   if(c1 > entryHigh)
   {
      double sl = NormalizeDouble(ask - slDist, digits);
      trade.Buy(CalcLot(slDist), _Symbol, ask, sl, 0.0, "EBTA Long");
   }
   else if(c1 < entryLow)
   {
      double sl = NormalizeDouble(bid + slDist, digits);
      trade.Sell(CalcLot(slDist), _Symbol, bid, sl, 0.0, "EBTA Short");
   }
}

//+------------------------------------------------------------------+
// Ghi cac lenh da dong ra CSV (Common\Files) cho ebta_validator.py
void WriteTradeLog(const string fileName, const ulong magic)
{
   if(!HistorySelect(0, TimeCurrent()))
   {
      Print("TradeLog: HistorySelect that bai");
      return;
   }
   int h = FileOpen(fileName, FILE_WRITE | FILE_CSV | FILE_ANSI | FILE_COMMON, ',');
   if(h == INVALID_HANDLE)
   {
      Print("TradeLog: khong mo duoc ", fileName, " loi=", GetLastError());
      return;
   }
   FileWrite(h, "open_time", "close_time", "direction", "volume",
             "open_price", "close_price", "profit");

   int total = HistoryDealsTotal();
   for(int i = 0; i < total; i++)
   {
      ulong dealOut = HistoryDealGetTicket(i);
      if(dealOut == 0) continue;
      if((ulong)HistoryDealGetInteger(dealOut, DEAL_MAGIC) != magic) continue;
      if(HistoryDealGetInteger(dealOut, DEAL_ENTRY) != DEAL_ENTRY_OUT) continue;

      ulong    posId     = (ulong)HistoryDealGetInteger(dealOut, DEAL_POSITION_ID);
      datetime openTime  = 0;
      double   openPrice = 0.0;
      for(int j = 0; j < i; j++)
      {
         ulong d = HistoryDealGetTicket(j);
         if(d == 0) continue;
         if((ulong)HistoryDealGetInteger(d, DEAL_POSITION_ID) == posId &&
            HistoryDealGetInteger(d, DEAL_ENTRY) == DEAL_ENTRY_IN)
         {
            openTime  = (datetime)HistoryDealGetInteger(d, DEAL_TIME);
            openPrice = HistoryDealGetDouble(d, DEAL_PRICE);
            break;
         }
      }
      long outType = HistoryDealGetInteger(dealOut, DEAL_TYPE);
      int  dir     = (outType == DEAL_TYPE_SELL) ? 1 : -1;   // deal dong SELL => vi the la BUY
      double profit = HistoryDealGetDouble(dealOut, DEAL_PROFIT)
                    + HistoryDealGetDouble(dealOut, DEAL_SWAP)
                    + HistoryDealGetDouble(dealOut, DEAL_COMMISSION);

      FileWrite(h,
                TimeToString(openTime, TIME_DATE | TIME_SECONDS),
                TimeToString((datetime)HistoryDealGetInteger(dealOut, DEAL_TIME), TIME_DATE | TIME_SECONDS),
                dir,
                DoubleToString(HistoryDealGetDouble(dealOut, DEAL_VOLUME), 2),
                DoubleToString(openPrice, _Digits),
                DoubleToString(HistoryDealGetDouble(dealOut, DEAL_PRICE), _Digits),
                DoubleToString(profit, 2));
   }
   FileClose(h);
   Print("TradeLog: da ghi ", fileName);
}

//+------------------------------------------------------------------+
// Goi sau khi backtest ket thuc: ghi danh sach lenh
double OnTester()
{
   if(WriteLog)
      WriteTradeLog("trades_UJEBTA_N" + IntegerToString(EntryN) + "_" + RunTag + ".csv", MagicNumber);
   return TesterStatistics(STAT_PROFIT);
}
//+------------------------------------------------------------------+
