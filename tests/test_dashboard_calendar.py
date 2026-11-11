import unittest
from gpt_pi.dashboard.calendar.model import validate_event, days_until
class CalendarTests(unittest.TestCase):
 def test_calendar_days_ignore_dst_and_leap_boundaries(self):
  self.assertEqual(days_until('2026-11-10','2027-01-01'),52)
  self.assertEqual(days_until('2024-02-28','2024-03-01'),2)
  self.assertEqual(days_until('2026-03-28','2026-03-30'),2)
  self.assertEqual(days_until('2026-11-11','2026-11-10'),0)
 def test_validation_preserves_all_day_dates_and_rejects_invalid_time(self):
  self.assertEqual(validate_event({'title':'  Event  ','date':'2026-11-10','time':''})['date'],'2026-11-10')
  for data in [{'title':'','date':'2026-11-10'}, {'title':'x','date':'2026-02-30'}, {'title':'x','date':'2026-11-10','time':'25:00'}, {'title':'x','date':'2026-11-10','owner':'another'}]:
   with self.assertRaises(ValueError):validate_event(data)
