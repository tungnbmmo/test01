//+------------------------------------------------------------------+
//| TradeLogger.mqh - ghi cac lenh da dong ra CSV de kiem dinh       |
//| Dung: #include "TradeLogger.mqh" roi goi WriteTradeLog() trong   |
//| OnDeinit() cua EA:  WriteTradeLog("trades_cfg1.csv", MagicNumber);|
//| File nam o thu muc Common\Files (Terminal\Common\Files).         |
//| Luu y: profit = profit + swap + commission cua deal dong lenh.   |
//|        Hoa hong tinh o deal mo lenh (neu co) khong duoc cong vao.|
//+------------------------------------------------------------------+
#property strict

void WriteTradeLog(const string fileName, const ulong magic)
{
   if(!HistorySelect(0, TimeCurrent()))
   {
      Print("TradeLogger: HistorySelect that bai");
      return;
   }
   int h = FileOpen(fileName, FILE_WRITE | FILE_CSV | FILE_ANSI | FILE_COMMON, ',');
   if(h == INVALID_HANDLE)
   {
      Print("TradeLogger: khong mo duoc ", fileName, " loi=", GetLastError());
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

      // Deal DONG la SELL -> vi the la BUY (+1); BUY -> vi the la SELL (-1)
      long outType = HistoryDealGetInteger(dealOut, DEAL_TYPE);
      int  dir     = (outType == DEAL_TYPE_SELL) ? 1 : -1;
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
   Print("TradeLogger: da ghi ", fileName);
}
//+------------------------------------------------------------------+
