//+------------------------------------------------------------------+
//| UJ_SwingEMA.mq5 - Swing H4, pullback ve SMA50 theo xu huong EMA200|
//|                                                                  |
//| Chi giao dich THEO XU HUONG, doi xung Long/Short:                |
//|  Xu huong len : close > EMA200 va SMA50 > EMA200                 |
//|  Long : nen vua dong cham/xuyen SMA50 roi dong cua lai tren SMA50|
//|         bang nen tang (pullback + tu choi).                      |
//|  SL = AtrStopMult x ATR ; TP = RewardRisk x khoang SL (1:5).     |
//|  Thoat som neu nen dong cua cat nguoc qua EMA200 (het xu huong). |
//| Khong dung khoi luong (tick volume forex khong dang tin) va      |
//| khong dung pivot/cung-cau de giu quy tac khach quan, it tham so. |
//+------------------------------------------------------------------+
#property copyright "Demo"
#property version   "1.00"
#property strict

#include <Trade/Trade.mqh>
CTrade trade;

//--- Quy tac
input ENUM_TIMEFRAMES Tf          = PERIOD_H4;
input int    TrendEmaP            = 200;    // EMA loc xu huong
input int    PullbackSmaP         = 50;     // SMA dong vai tro ho tro/khang cu dong
input int    AtrPeriod            = 14;
input double AtrStopMult          = 2.0;    // SL = AtrStopMult x ATR
input double RewardRisk           = 5.0;    // TP = RewardRisk x khoang SL (R:R 1:5)
input bool   UseTrendExit         = true;   // dong lenh khi gia cat nguoc qua EMA200

//--- Von va chi phi
input double RiskPercent          = 0.5;    // % von rui ro moi lenh (theo khoang SL)
input double MaxSpreadFrac        = 0.05;   // spread toi da = x% khoang SL
input int    MaxSpreadPts         = 80;
input double MaxDDPct             = 25.0;   // cau dao: dung neu equity giam % tu dinh
input ulong  MagicNumber          = 20260515;

//--- Nhat ky kiem dinh
input bool   WriteLog             = true;
input string RunTag               = "train";

int      hEma = INVALID_HANDLE, hSma = INVALID_HANDLE, hAtr = INVALID_HANDLE;
datetime lastBar    = 0;
double   peakEquity = 0.0;
bool     halted     = false;

//+------------------------------------------------------------------+
int OnInit()
{
   hEma = iMA(_Symbol, Tf, TrendEmaP,    0, MODE_EMA, PRICE_CLOSE);
   hSma = iMA(_Symbol, Tf, PullbackSmaP, 0, MODE_SMA, PRICE_CLOSE);
   hAtr = iATR(_Symbol, Tf, AtrPeriod);
   if(hEma == INVALID_HANDLE || hSma == INVALID_HANDLE || hAtr == INVALID_HANDLE)
      return INIT_FAILED;
   trade.SetExpertMagicNumber(MagicNumber);
   trade.SetDeviationInPoints(30);
   peakEquity = AccountInfoDouble(ACCOUNT_EQUITY);
   return INIT_SUCCEEDED;
}

//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
   if(hEma != INVALID_HANDLE) IndicatorRelease(hEma);
   if(hSma != INVALID_HANDLE) IndicatorRelease(hSma);
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
bool ReadOne(const int handle, double &value)
{
   double buf[];
   ArraySetAsSeries(buf, true);
   if(CopyBuffer(handle, 0, 1, 1, buf) < 1) return false;   // gia tri tai nen vua dong
   value = buf[0];
   return true;
}

//+------------------------------------------------------------------+
void OnTick()
{
   // Chi quyet dinh 1 lan khi nen moi mo; tin hieu lay tren nen vua dong (shift 1)
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

   double ema = 0, sma = 0, atr = 0;
   if(!ReadOne(hEma, ema) || !ReadOne(hSma, sma) || !ReadOne(hAtr, atr)) return;
   if(atr <= 0) return;

   MqlRates r[];
   ArraySetAsSeries(r, true);
   if(CopyRates(_Symbol, Tf, 0, 3, r) < 3) return;
   double o1 = r[1].open, h1 = r[1].high, l1 = r[1].low, c1 = r[1].close;

   // --- Thoat som khi het xu huong (doi xung Long/Short) ---
   if(have && UseTrendExit)
   {
      ENUM_POSITION_TYPE type = (ENUM_POSITION_TYPE)PositionGetInteger(POSITION_TYPE);
      bool exitLong  = (type == POSITION_TYPE_BUY  && c1 < ema);
      bool exitShort = (type == POSITION_TYPE_SELL && c1 > ema);
      if(exitLong || exitShort)
      {
         if(trade.PositionClose(ticket)) have = false;
      }
   }
   if(have) return;

   if(SymbolInfoInteger(_Symbol, SYMBOL_SPREAD) > MaxSpreadPts) return;

   // --- Tin hieu (doi xung): xu huong + pullback ve SMA50 + nen tu choi ---
   bool trendUp   = (c1 > ema && sma > ema);
   bool trendDown = (c1 < ema && sma < ema);
   bool longSig   = trendUp   && l1 <= sma && c1 > sma && c1 > o1;
   bool shortSig  = trendDown && h1 >= sma && c1 < sma && c1 < o1;
   if(!longSig && !shortSig) return;

   double ask    = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
   double bid    = SymbolInfoDouble(_Symbol, SYMBOL_BID);
   int    digits = (int)SymbolInfoInteger(_Symbol, SYMBOL_DIGITS);
   double slDist = AtrStopMult * atr;
   double tpDist = RewardRisk * slDist;
   if((ask - bid) > MaxSpreadFrac * slDist) return;

   if(longSig)
   {
      double sl = NormalizeDouble(ask - slDist, digits);
      double tp = NormalizeDouble(ask + tpDist, digits);
      trade.Buy(CalcLot(slDist), _Symbol, ask, sl, tp, "Swing Long");
   }
   else
   {
      double sl = NormalizeDouble(bid + slDist, digits);
      double tp = NormalizeDouble(bid - tpDist, digits);
      trade.Sell(CalcLot(slDist), _Symbol, bid, sl, tp, "Swing Short");
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
double OnTester()
{
   if(WriteLog) WriteTradeLog("trades_UJSWING_" + RunTag + ".csv", MagicNumber);
   return TesterStatistics(STAT_PROFIT);
}
//+------------------------------------------------------------------+
