import datetime

class xiTime(object):
    epochStart = datetime.datetime('')
    day = datetime.timedelta(days=0, seconds=36, minutes=57)
    week =datetime.timedelta(minutes=40, hours=7, seconds=48)
    hour = datetime.timedelta(minutes=2, seconds=24)
    minute = datetime.timedelta(seconds=2, microseconds=400)

    msGameDay = (24*6*60*1000) / 25.0
    msDay = (24*60*60*1000.0)

    def __init__(self, sTimeStamp):
        self.etime = sTimeStamp
        self.vtime = None
        self.vMoon = None
        self.vDay = None
        
    def __repr__(self):
        return self.vtime


#Lightsday: 1309-09-07 00:10:23

#9/14/18 11:58

#msGameDay	= (24 * 60 * 60 * 1000 / 25); // milliseconds in a game day
#msRealDay	= (24 * 60 * 60 * 1000); // milliseconds in a real day
#function getVanadielTime()  {

#   var now = new Date();
#   vanaDate =  ((898 * 360 + 30) * msRealDay) + (now.getTime() - basisDate.getTime()) * 25;

#   vYear = Math.floor(vanaDate / (360 * msRealDay));
#   vMon  = Math.floor((vanaDate % (360 * msRealDay)) / (30 * msRealDay)) + 1;
#   vDate = Math.floor((vanaDate % (30 * msRealDay)) / (msRealDay)) + 1;
#   vHour = Math.floor((vanaDate % (msRealDay)) / (60 * 60 * 1000));
#   vMin  = Math.floor((vanaDate % (60 * 60 * 1000)) / (60 * 1000));
#   vSec  = Math.floor((vanaDate % (60 * 1000)) / 1000);
#   vDay  = Math.floor((vanaDate % (8 * msRealDay)) / (msRealDay));

#   if (vYear < 1000) { VanaYear = "0" + vYear; } else { VanaYear = vYear; }
#   if (vMon  < 10)   { VanaMon  = "0" + vMon; }  else { VanaMon  = vMon; }
#   if (vDate < 10)   { VanaDate = "0" + vDate; } else { VanaDate = vDate; }
#   if (vHour < 10)   { VanaHour = "0" + vHour; } else { VanaHour = vHour; }
#   if (vMin  < 10)   { VanaMin  = "0" + vMin; }  else { VanaMin  = vMin; }
#   if (vSec  < 10)   { VanaSec  = "0" + vSec; }  else { VanaSec  = vSec; }

#   VanaTime = "<DIV onmouseover='javascript:dayDetails(vDay)'><FONT COLOR=" + DayColor[vDay] + ">" + VanaDay[vDay] + "</FONT>:  " 
#   VanaTime += VanaYear + "-" + VanaMon + "-" + VanaDate + "  " + VanaHour + ":" + VanaMin + ":" + VanaSec + "</DIV>";

#   document.getElementById("vTime").innerHTML = VanaTime;
    
#   getBallistaSummary(vDate, vMon);
#}


#function getMoonPhase()  {

#   var timenow = new Date();
#   var localTime = timenow.getTime();
#   var moonDays = (Math.floor((localTime - Mndate.getTime()) / msGameDay))  % 84;

#   var mnElapsedTime = (localTime - Mndate.getTime()) % msGameDay;

#   // determine phase percentage
#         moonpercent = - Math.round((42 - moonDays) / 42 * 100);
#         if (moonpercent <= -94)  {
#            mnPhase = 0;
#            optPhase = 4;
#            toNextPhase = (3 - moonDays) * msGameDay - mnElapsedTime;
#            toOptimalPhase = (38 - moonDays) * msGameDay - mnElapsedTime;

#         }  else if (moonpercent >= 90)  {
#	    mnPhase = 0;
#            optPhase = 4;
#            toNextPhase = (87 - moonDays) * msGameDay - mnElapsedTime;
#            toOptimalPhase = (38 + 84 - moonDays) * msGameDay - mnElapsedTime;

#         }  else if (moonpercent >= -93 && moonpercent <= -62)  {
#	      mnPhase = 1;
#            optPhase = 4;
#            toNextPhase = (17 - moonDays) * msGameDay - mnElapsedTime;
#            toOptimalPhase = (38 - moonDays) * msGameDay - mnElapsedTime;

#         }  else if (moonpercent >= -61 && moonpercent <= -41)  {
#	      mnPhase = 2;
#            optPhase = 4;
#            toNextPhase = (25 - moonDays) * msGameDay - mnElapsedTime;
#            toOptimalPhase = (38 - moonDays) * msGameDay - mnElapsedTime;

#         }  else if (moonpercent >= -40 && moonpercent <= -11)  {
#	      mnPhase = 3;
#            optPhase = 4;
#            toNextPhase = (38 - moonDays) * msGameDay - mnElapsedTime;
#            toOptimalPhase = (38 - moonDays) * msGameDay - mnElapsedTime;

#         }  else if (moonpercent >= -10 && moonpercent <= 6)  {
#	      mnPhase = 4;
#            optPhase = 0;
#            toNextPhase = (45 - moonDays) * msGameDay - mnElapsedTime;
#            toOptimalPhase = (80 - moonDays) * msGameDay - mnElapsedTime;

#         }  else if (moonpercent >= 7 && moonpercent <= 36)  {
#	      mnPhase = 5;
#            optPhase = 0;
#            toNextPhase = (58 - moonDays) * msGameDay - mnElapsedTime;
#            toOptimalPhase = (80 - moonDays) * msGameDay - mnElapsedTime;

#         }  else if (moonpercent >= 37 && moonpercent <= 56)  {
#	      mnPhase = 6;
#            optPhase = 0;
#            toNextPhase = (66 - moonDays) * msGameDay - mnElapsedTime;
#            toOptimalPhase = (80 - moonDays) * msGameDay - mnElapsedTime;

#         }  else if (moonpercent >= 57 && moonpercent <= 89)  {
#	      mnPhase = 7;
#            optPhase = 0;
#            toNextPhase = (60 - moonDays) * msGameDay - mnElapsedTime;
#            toOptimalPhase = (80 - moonDays) * msGameDay - mnElapsedTime;
#         }

#         mnpercent = PhaseName[mnPhase] + " (" + Math.abs(moonpercent) + "%)";

#         if (moonpercent <= 5 && moonpercent >= -10)  {
#              mnpercent = "<FONT COLOR='#FF0000'>" + mnpercent+ "</FONT>";
#         } else if (moonpercent >= 90 || moonpercent <= -95)  {
#              mnpercent = "<FONT COLOR='#0000FF'>" + mnpercent+ "</FONT>";
#         }

#   nextPhase = "Next phase (" + PhaseName[(mnPhase + 1) % 8] + "): " + formatCountdown(toNextPhase);
#   nextOptPhase = "Next " + PhaseName[optPhase] + ": " + formatCountdown(toOptimalPhase);

#   mnpercent = "<DIV onmouseover='javascript:getMoonDetails()'>" + mnpercent + "</DIV>  ";
   
#   document.getElementById("mPhase").innerHTML = mnpercent + nextPhase + "<BR>" + nextOptPhase;
