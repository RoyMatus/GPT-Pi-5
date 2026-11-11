"""Local calendar: dates and floating wall times, session-only storage."""
from datetime import date, time
import re

def validate_event(data):
 if not isinstance(data,dict) or set(data)-{'id','title','date','time'}:raise ValueError('invalid_event')
 title=data.get('title')
 if not isinstance(title,str) or not 1<=len(title.strip())<=120:raise ValueError('invalid_event')
 day=data.get('date','')
 if not isinstance(day,str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}',day):raise ValueError('invalid_event')
 parsed=date.fromisoformat(day)
 if not 1900<=parsed.year<=2200:raise ValueError('invalid_event')
 clock=data.get('time','')
 if clock is None:clock=''
 if not isinstance(clock,str) or (clock and not re.fullmatch(r'([01]\d|2[0-3]):[0-5]\d',clock)):raise ValueError('invalid_event')
 return {'title':title.strip(),'date':day,'time':clock}

def days_until(today,target):return max(0,(date.fromisoformat(target)-date.fromisoformat(today)).days)
