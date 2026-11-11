import unittest
from gpt_pi.dashboard.shared.contracts import SSHProfile, SourceIdentity, Sample

class FoundationContracts(unittest.TestCase):
    def test_separate_telemetry_and_photo_identities(self):
        profile=SSHProfile('synthetic','host.invalid',22,'readonly','exec-key','sftp-key','SHA256:test')
        self.assertNotEqual(profile.telemetry_key_ref,profile.photo_key_ref)
        self.assertNotIn('password',profile.__dataclass_fields__)
    def test_unavailable_is_not_zero_and_source_generation_is_explicit(self):
        sample=Sample(SourceIdentity('pc',3),'unavailable',None,'percent',None,None,False)
        self.assertIsNone(sample.value)
        self.assertEqual(sample.source.generation,3)
