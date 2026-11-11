import unittest
from gpt_pi.dashboard.overview.weather import parse_weather,validate_location
class WeatherTests(unittest.TestCase):
 def test_invalid_location_and_units_fail_closed(self):
  with self.assertRaises(ValueError):validate_location({'name':'x','latitude':100,'longitude':0})
  with self.assertRaises(ValueError):parse_weather({'current':{'temperature_2m':float('nan'),'weather_code':0,'time':'2026-11-11T10:00'},'current_units':{'temperature_2m':'°C'},'hourly':{'time':[],'temperature_2m':[]}})
 def test_zero_temperature_is_a_reading_and_forecast_is_future_only(self):
  result=parse_weather({'current':{'temperature_2m':0,'weather_code':3,'time':'2026-11-11T10:00'},'current_units':{'temperature_2m':'°C'},'hourly':{'time':['2026-11-11T09:00','2026-11-11T11:00'],'temperature_2m':[5,1]}})
  self.assertEqual(result['temperature'],0);self.assertEqual(len(result['forecast']),1);self.assertEqual(result['forecast'][0]['temperature'],1)
