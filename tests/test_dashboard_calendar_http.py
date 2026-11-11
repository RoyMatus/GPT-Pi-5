import unittest
import test_webapp as harness
from starlette.testclient import TestClient
class CalendarHTTPTests(unittest.TestCase):
 setUp=harness.WebTests.setUp
 tearDown=harness.WebTests.tearDown
 post=harness.WebTests.post
 login=harness.WebTests.login
 def test_events_are_session_owned_and_logout_clears(self):
  self.assertEqual(self.client.get('/api/dashboard/calendar').status_code,401)
  self.login()
  result=self.post('/api/dashboard/calendar',{'title':'Synthetic event','date':'2026-11-10','time':'09:30'})
  self.assertEqual(result.status_code,200)
  event=result.json()['events'][0]
  other=TestClient(self.app,base_url=self.settings.origin)
  self.login('synthetic-B',client=other)
  self.assertEqual(other.get('/api/dashboard/calendar').json()['events'],[])
  self.assertEqual(self.post('/api/dashboard/calendar',{'action':'delete','id':event['id']},other).status_code,404)
  other.close()
  self.assertEqual(self.client.post('/api/dashboard/calendar',json=event).status_code,403)
  self.assertEqual(self.post('/api/dashboard/calendar',{'id':{},'action':'delete'}).status_code,400)
  self.post('/api/logout');self.login()
  self.assertEqual(self.client.get('/api/dashboard/calendar').json()['events'],[])
