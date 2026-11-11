import unittest,tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch,MagicMock
import paramiko
from gpt_pi.dashboard.ssh.service import ComputerState,PinnedHost,SourceError,fingerprint

class SSHTrustTests(unittest.TestCase):
 def test_unknown_and_changed_host_keys_fail_closed(self):
  key=paramiko.RSAKey.generate(1024)
  for expected,code in [('', 'verification_required'),('SHA256:'+'a'*43,'host_key_changed')]:
   with self.assertRaises(SourceError) as raised:PinnedHost(expected).missing_host_key(None,'synthetic.invalid',key)
   self.assertEqual(raised.exception.code,code)
  PinnedHost(fingerprint(key)).missing_host_key(None,'synthetic.invalid',key)
 def test_photo_contract_uses_separate_identity_and_explicit_session_grant(self):
  with tempfile.TemporaryDirectory() as temp:
   state=ComputerState(Path(temp));key=paramiko.RSAKey.generate(1024)
   state.configure({'host':'synthetic.invalid','port':22,'user':'metrics','photoUser':'photos','platform':'linux','fingerprint':fingerprint(key),'verified':True})
   session=SimpleNamespace(alive=True,resources=set(),dashboard={})
   grant={'generation':state.generation,'root':'/'}
   with self.assertRaises(SourceError):
    with state.sftp(session,grant):pass
   session.dashboard['photoGrant']=grant
   client=MagicMock();sftp=client.open_sftp.return_value
   with patch('gpt_pi.dashboard.ssh.service.paramiko.SSHClient',return_value=client):
    with state.sftp(session,grant) as actual:self.assertIs(actual,sftp)
   self.assertEqual(client.connect.call_args.kwargs['username'],'photos')
   self.assertFalse(client.connect.call_args.kwargs['allow_agent']);client.exec_command.assert_not_called();sftp.close.assert_called_once()
   state.reset()
   with self.assertRaises(SourceError):
    with state.sftp(session,grant):pass
