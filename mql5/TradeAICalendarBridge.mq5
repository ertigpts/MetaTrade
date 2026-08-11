#property strict
#property version   "1.00"
#property description "Exports the native MT5 USD economic calendar for TradeAI."

input int RefreshSeconds = 60;
input int HorizonDays = 2;

string JsonEscape(string value)
  {
   StringReplace(value,"\\","\\\\");
   StringReplace(value,"\"","\\\"");
   StringReplace(value,"\r"," ");
   StringReplace(value,"\n"," ");
   return value;
  }

string CalendarNumber(long value)
  {
   if(value==LONG_MIN)
      return "null";
   return DoubleToString((double)value/1000000.0,6);
  }

void ExportCalendar()
  {
   datetime now=TimeTradeServer();
   if(now<=0)
      now=TimeCurrent();
   datetime until=now+(datetime)(MathMax(1,HorizonDays)*86400);
   MqlCalendarValue values[];
   ResetLastError();
   // The broad currency query can time out while MT5 is warming its calendar
   // cache.  Gold's relevant USD releases are US events, so the narrower
   // country query is both faster and more precise.
   int count=CalendarValueHistory(values,now,until,"US",NULL);
   if(count<0)
     {
      PrintFormat("TradeAI calendar export failed: %d",GetLastError());
      return;
     }

   FolderCreate("TradeAI",FILE_COMMON);
   int handle=FileOpen("TradeAI\\economic_calendar.json",FILE_WRITE|FILE_TXT|FILE_ANSI|FILE_COMMON);
   if(handle==INVALID_HANDLE)
     {
      PrintFormat("TradeAI calendar file open failed: %d",GetLastError());
      return;
     }

   string output="{\"source\":\"MT5 Economic Calendar\",\"generated_server_epoch\":"+
                 IntegerToString((long)now)+",\"currency\":\"USD\",\"events\":[";
   int written=0;
   for(int i=0;i<count && written<100;i++)
     {
      MqlCalendarEvent event;
      if(!CalendarEventById(values[i].event_id,event))
         continue;
      if(written>0)
         output+=",";
      output+="{\"value_id\":"+IntegerToString((long)values[i].id)+
              ",\"event_id\":"+IntegerToString((long)values[i].event_id)+
              ",\"name\":\""+JsonEscape(event.name)+"\""+
              ",\"event_code\":\""+JsonEscape(event.event_code)+"\""+
              ",\"time_server_epoch\":"+IntegerToString((long)values[i].time)+
              ",\"importance\":"+IntegerToString((int)event.importance)+
              ",\"time_mode\":"+IntegerToString((int)event.time_mode)+
              ",\"actual\":"+CalendarNumber(values[i].actual_value)+
              ",\"forecast\":"+CalendarNumber(values[i].forecast_value)+
              ",\"previous\":"+CalendarNumber(values[i].prev_value)+"}";
      written++;
     }
   output+="]}";
   FileWriteString(handle,output);
   FileClose(handle);
   PrintFormat("TradeAI calendar exported: %d USD events",written);
  }

int OnInit()
  {
   EventSetTimer(MathMax(60,RefreshSeconds));
   ExportCalendar();
   return INIT_SUCCEEDED;
  }

void OnTimer()
  {
   ExportCalendar();
  }

void OnDeinit(const int reason)
  {
   EventKillTimer();
  }
