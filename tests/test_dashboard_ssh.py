import unittest
from gpt_pi.dashboard.ssh.service import validate_profile, validate_sample, network_rates
class SSHDataTests(unittest.TestCase):
 def test_typed_profile_and_trust_are_required(self):
  with self.assertRaises(ValueError):validate_profile({'host':'pc','port':22,'user':'user','platform':'linux','fingerprint':''})
  with self.assertRaises(ValueError):validate_profile({'host':'pc','port':True,'user':'user','platform':'linux','fingerprint':'SHA256:'+'a'*43})
 def test_metrics_reject_impossible_values_and_network_reset(self):
  with self.assertRaises(ValueError):validate_sample({'schema':1,'cpuPct':101})
  self.assertEqual(network_rates(None,{'netRxBytes':200,'netTxBytes':10,'uptime':10}),(None,None))
  self.assertEqual(network_rates({'netRxBytes':100,'netTxBytes':10,'uptime':10},{'netRxBytes':200,'netTxBytes':30,'uptime':12}),(400,80))
  self.assertEqual(network_rates({'netRxBytes':200,'netTxBytes':10,'uptime':10},{'netRxBytes':1,'netTxBytes':30,'uptime':12}),(None,None))
