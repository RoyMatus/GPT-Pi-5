import unittest
import test_webapp as harness
class ComputerHTTPTests(unittest.TestCase):
 setUp=harness.WebTests.setUp
 tearDown=harness.WebTests.tearDown
 post=harness.WebTests.post
 login=harness.WebTests.login
 def test_profile_is_owner_bound_and_never_exposes_private_key(self):
  self.assertEqual(self.client.get('/api/dashboard/computer').status_code,401)
  self.login()
  config={'action':'configure','host':'synthetic.invalid','port':22,'user':'metrics','photoUser':'photos','platform':'linux','fingerprint':'SHA256:'+'a'*43,'label':'Synthetic PC','verified':True}
  response=self.post('/api/dashboard/computer',config);self.assertEqual(response.status_code,200)
  self.assertIn('ssh-ed25519 ',response.json()['publicKey']);self.assertNotIn('PRIVATE KEY',response.text)
  other=harness.TestClient(self.app,base_url=self.settings.origin);self.login('synthetic-B',client=other)
  self.assertIsNone(other.get('/api/dashboard/computer').json()['profile']);other.close()
  self.assertEqual(self.post('/api/dashboard/computer',{'action':'shell','command':'whoami'}).status_code,400)
  result=self.post('/api/dashboard/computer',{'action':'disable'}).json();self.assertEqual(result['state'],'disabled')
  self.assertEqual(self.post('/api/dashboard/computer',{'action':'remove'}).json()['state'],'not_configured')
