import unittest
import test_webapp as harness
class PhotoHTTPTests(unittest.TestCase):
 setUp=harness.WebTests.setUp
 tearDown=harness.WebTests.tearDown
 post=harness.WebTests.post
 login=harness.WebTests.login
 def test_photo_authorization_is_separate_and_no_path_endpoint_exists(self):
  self.assertEqual(self.client.get('/api/dashboard/photos').status_code,401)
  self.login()
  self.assertEqual(self.client.get('/api/dashboard/photos').json()['files'],[])
  self.assertEqual(self.post('/api/dashboard/photos',{'root':'/photos','confirmed':True,'serverRestricted':False}).status_code,400)
  self.assertEqual(self.client.get('/api/dashboard/photos/unknown-id').status_code,404)
  self.assertEqual(self.post('/api/dashboard/photos',{'action':'revoke'}).json()['state'],'not_configured')
  self.assertEqual(self.client.post('/api/dashboard/photos',json={'action':'revoke'}).status_code,403)
