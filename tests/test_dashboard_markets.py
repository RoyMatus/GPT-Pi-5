import unittest
from gpt_pi.dashboard.markets.service import change_percent, parse_cbr, parse_kraken
class MarketTests(unittest.TestCase):
 def test_missing_and_zero_baselines_are_not_changes(self):
  self.assertIsNone(change_percent(10,0));self.assertIsNone(change_percent(None,10));self.assertEqual(change_percent(110,100),10)
 def test_fx_nominal_and_decimal_comma(self):
  self.assertEqual(parse_cbr(b'<ValCurs Date="10.11.2026"><Valute><CharCode>JPY</CharCode><Nominal>100</Nominal><Value>51,23</Value></Valute></ValCurs>','JPY')[0],.5123)
  with self.assertRaises(ValueError):parse_cbr(b'<!DOCTYPE bad><ValCurs/>','USD')
 def test_kraken_schema_rejects_nonfinite_and_error_payload(self):
  with self.assertRaises(ValueError):parse_kraken({'error':['limit'],'result':{}})
  with self.assertRaises(ValueError):parse_kraken({'error':[],'result':{'PAIR':[[1,'1','2','0','NaN','0','1',1]]}})

 def test_provider_can_include_current_candle_after_720_closed_candles(self):
  rows=[[1794300000+i*60,'1','2','0','1','1','1',1] for i in range(721)]
  self.assertEqual(len(parse_kraken({'error':[],'result':{'PAIR':rows,'last':1794300000}})),721)
