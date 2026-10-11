//+------------------------------------------------------------------+
//| ExportBars.mq5 - xuat bar gia ra CSV (Common\Files)              |
//| Chay tren chart cua symbol can phan tich (Navigator > Scripts).  |
//+------------------------------------------------------------------+
#property strict
#property script_show_inputs

input ENUM_TIMEFRAMES Tf       = PERIOD_H1;
input datetime        FromDate = D'2023.01.01';
input datetime        ToDate   = D'2026.10.01';
input string          FileName = "bars_USDJPY_H1.csv";

void OnStart()
{
   MqlRates r[];
   int n = CopyRates(_Symbol, Tf, FromDate, ToDate, r);
   if(n <= 0)
   {
      Print("ExportBars: CopyRates that bai, loi=", GetLastError());
      return;
   }
   int h = FileOpen(FileName, FILE_WRITE | FILE_CSV | FILE_ANSI | FILE_COMMON, ',');
   if(h == INVALID_HANDLE)
   {
      Print("ExportBars: khong mo duoc file, loi=", GetLastError());
      return;
   }
   FileWrite(h, "time", "open", "high", "low", "close", "tick_volume");
   for(int i = 0; i < n; i++)
      FileWrite(h,
                TimeToString(r[i].time, TIME_DATE | TIME_SECONDS),
                DoubleToString(r[i].open,  _Digits),
                DoubleToString(r[i].high,  _Digits),
                DoubleToString(r[i].low,   _Digits),
                DoubleToString(r[i].close, _Digits),
                (string)r[i].tick_volume);
   FileClose(h);
   Print("ExportBars: da ghi ", n, " bar vao ", FileName);
}
//+------------------------------------------------------------------+
