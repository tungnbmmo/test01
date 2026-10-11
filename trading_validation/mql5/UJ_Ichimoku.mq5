//+------------------------------------------------------------------+
//| UJ_Ichimoku.mq5 - Trend following theo Ichimoku, khung M15       |
//|                                                                  |
//| Chi giao dich THEO XU HUONG, doi xung Long/Short:                |
//|  Long : gia dong cua tren may (Kumo) + may tang (SpanA > SpanB)  |
//|         + Tenkan cat len Kijun + Chikou tren gia 26 nen truoc.   |
//|  Short: guong lai hoan toan.                                     |
//|  Thoat: nen dong cua cat nguoc qua Kijun, hoac cham SL (ATR).    |
//| Cac duong Ichimoku duoc tinh truc tiep tu cong thuc chuan        |
//| (9/26/52) de tranh nham lan do Senkou Span bi dich 26 nen.       |
//| Tham so Ichimoku giu NGUYEN gia tri chuan, khong toi uu.         |
//+------------------------------------------------------------------+
#property copyright "Demo"
#property version   "1.00"
#property strict

#include <Trade/Trade.mqh>
CTrade trade;

//--- Ichimoku chuan (khong toi uu)
input ENUM_TIMEFRAMES Tf          = PERIOD_M15;
input int    TenkanP              = 9;
input int    KijunP               = 26;
input int    SenkouBP             = 52;

//--- Quan ly lenh
input int    AtrPeriod            = 14;
input double AtrStopMult          = 2.5;    // SL = AtrStopMult x ATR (co dinh)
input double RiskPercent          = 0.5;    // % von rui ro moi lenh (theo khoang SL)

//--- Bo loc chi phi / thoi gian (gio SERVER, gia dinh GMT+0)
input int    SessStart            = 7;      // chi VAO lenh tu gio nay
input int    SessEnd              = 17;     // ... den truoc gio nay
input double MaxSpreadFrac        = 0.15;   // spread toi da = x% khoang SL
input int    MaxSpreadPts         = 60;
input int    MaxTradesPerDay      = 3;

//--- An toan va nhat ky
input double MaxDDPct             = 25.0;   // cau dao: dung neu equity giam % tu dinh
input ulong  MagicNumber          = 20260514;
input bool   WriteLog             = true;
input string RunTag               = "train";

int      hAtr       = INVALID_HANDLE;
datetime lastBar    = 0;
datetime curDay     = 0;
int      tradesToday = 0;
double   peakEquity = 0.0;
bool     halted     = false;

//+------------------------------------------------------------------+
int OnInit()
{
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
// (Cao nhat + Thap nhat)/2 cua 'period' nen, bat dau tu nen 'startShift' (r la series)
double MidHL(const MqlRates &r[], int startShift, int period)
{
   double hi = r[startShift].high, lo = r[startShift].low;
   for(int k = 1; k < period; k++)
   {
      if(r[startShift + k].high > hi) hi = r[startShift + k].high;
      if(r[startShift + k].low  < lo) lo = r[startShift + k].low;
   }
   return (hi + lo) / 2.0;
}

//+------------------------------------------------------------------+
void OnTick()
{
   // Chi quyet dinh 1 lan khi nen moi mo; tin hieu lay tren nen vua dong (shift 1)
   datetime barTime = iTime(_Symbol, Tf, 0);
   if(barTime == lastBar) return;
   lastBar = barTime;

   datetime now = TimeCurrent();
   MqlDateTime t; TimeToStruct(now, t);
   datetime dayStart = now - (now % 86400);
   if(dayStart != curDay) { curDay = dayStart; tradesToday = 0; }

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

   // --- Du lieu (r[1] = nen vua dong). Can: SpanB tai nen 1 dung nen (1+Kijun) + SenkouBP, + Chikou ---
   int need = 1 + KijunP + SenkouBP + 5;
   MqlRates r[];
   ArraySetAsSeries(r, true);
   if(CopyRates(_Symbol, Tf, 0, need, r) < need) return;

   double atrBuf[];
   ArraySetAsSeries(atrBuf, true);
   if(CopyBuffer(hAtr, 0, 1, 1, atrBuf) < 1) return;
   double atr = atrBuf[0];
   if(atr <= 0) return;

   // --- Ichimoku tinh tu cong thuc chuan ---
   double tenkan1 = MidHL(r, 1, TenkanP);
   double kijun1  = MidHL(r, 1, KijunP);
   double tenkan2 = MidHL(r, 2, TenkanP);
   double kijun2  = MidHL(r, 2, KijunP);
   // May (Kumo) hien thi tai nen 1 = gia tri tinh tu nen (1+Kijun)
   int    cs      = 1 + KijunP;
   double spanA   = (MidHL(r, cs, TenkanP) + MidHL(r, cs, KijunP)) / 2.0;
   double spanB   = MidHL(r, cs, SenkouBP);
   double cloudTop = MathMax(spanA, spanB);
   double cloudBot = MathMin(spanA, spanB);
   double c1       = r[1].close;
   double chikouRef = r[1 + KijunP].close;     // gia 26 nen truoc, de so voi Chikou (= c1)

   // --- Thoat lenh: dong cua cat nguoc qua Kijun (doi xung Long/Short) ---
   if(have)
   {
      ENUM_POSITION_TYPE type = (ENUM_POSITION_TYPE)PositionGetInteger(POSITION_TYPE);
      bool exitLong  = (type == POSITION_TYPE_BUY  && c1 < kijun1);
      bool exitShort = (type == POSITION_TYPE_SELL && c1 > kijun1);
      if(exitLong || exitShort)
      {
         if(trade.PositionClose(ticket)) have = false;
      }
   }
   if(have) return;

   // --- Bo loc vao lenh ---
   if(tradesToday >= MaxTradesPerDay) return;
   if(t.hour < SessStart || t.hour >= SessEnd) return;
   if(SymbolInfoInteger(_Symbol, SYMBOL_SPREAD) > MaxSpreadPts) return;

   // --- Tin hieu (doi xung) ---
   bool crossUp   = (tenkan2 <= kijun2 && tenkan1 > kijun1);
   bool crossDown = (tenkan2 >= kijun2 && tenkan1 < kijun1);
   bool longSig   = crossUp   && c1 > cloudTop && spanA > spanB && c1 > chikouRef;
   bool shortSig  = crossDown && c1 < cloudBot && spanA < spanB && c1 < chikouRef;
   if(!longSig && !shortSig) return;

   double ask    = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
   double bid    = SymbolInfoDouble(_Symbol, SYMBOL_BID);
   int    digits = (int)SymbolInfoInteger(_Symbol, SYMBOL_DIGITS);
   double slDist = AtrStopMult * atr;
   if((ask - bid) > MaxSpreadFrac * slDist) return;    // spread an qua nhieu vao rui ro

   if(longSig)
   {
      double sl = NormalizeDouble(ask - slDist, digits);
      if(trade.Buy(CalcLot(slDist), _Symbol, ask, sl, 0.0, "Ichimoku Long")) tradesToday++;
   }
   else
   {
      double sl = NormalizeDouble(bid + slDist, digits);
      if(trade.Sell(CalcLot(slDist), _Symbol, bid, sl, 0.0, "Ichimoku Short")) tradesToday++;
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
   if(WriteLog) WriteTradeLog("trades_UJICHI_" + RunTag + ".csv", MagicNumber);
   return TesterStatistics(STAT_PROFIT);
}
//+------------------------------------------------------------------+
