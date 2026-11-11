import asyncio,tempfile,threading,unittest
from pathlib import Path
from types import SimpleNamespace
from gpt_pi.dashboard.ssh.service import ComputerState
class SourceLifecycleTests(unittest.IsolatedAsyncioTestCase):
 async def test_disable_rejects_late_collector_sample(self):
  with tempfile.TemporaryDirectory() as directory:
   state=ComputerState(Path(directory));state.configure({'host':'synthetic.invalid','port':22,'user':'metrics','platform':'linux','fingerprint':'SHA256:'+'a'*43,'verified':True})
   started=threading.Event();finish=threading.Event()
   def late(session):started.set();finish.wait(2);return {'schema':1,'cpuPct':50,'netRxBytes':1,'netTxBytes':1,'uptime':10,'netRxBitsPerSecond':None,'netTxBitsPerSecond':None}
   state.collect_sync=late
   session=SimpleNamespace(alive=True,resources=set(),dashboard_tasks=set())
   task=asyncio.create_task(state.collect(session))
   for _ in range(100):
    if started.is_set():break
    await asyncio.sleep(.005)
   self.assertTrue(started.is_set());state.disable();finish.set();result=await task
   self.assertEqual(result['state'],'disabled');self.assertIsNone(result['sample']);self.assertEqual(result['history'],[])
