import unittest
from gpt_pi.domain import ConversationStore, LocalSession, Principal


class OwnershipTests(unittest.TestCase):
    def setUp(self):
        self.store = ConversationStore()
        self.a = LocalSession(Principal("synthetic-a"))
        self.b = LocalSession(Principal("synthetic-b"))
        self.chat = self.store.create(self.a, "Synthetic conversation")

    def test_other_profile_cannot_read_guessed_id(self):
        with self.assertRaises(LookupError):
            self.store.get(self.b, self.chat.id)

    def test_other_profile_cannot_delete(self):
        with self.assertRaises(LookupError):
            self.store.delete(self.b, self.chat.id)
        self.assertEqual(self.chat, self.store.get(self.a, self.chat.id))

    def test_lists_are_owner_scoped(self):
        self.assertEqual((), self.store.list_for(self.b))
        self.assertEqual((self.chat,), self.store.list_for(self.a))

    def test_unknown_and_foreign_ids_have_same_error(self):
        errors = []
        for chat_id in (self.chat.id, "missing"):
            with self.assertRaises(LookupError) as error:
                self.store.get(self.b, chat_id)
            errors.append(str(error.exception))
        self.assertEqual(*errors)

    def test_lock_revokes_old_session_operations(self):
        self.a.lock()
        operations = [lambda: self.store.get(self.a, self.chat.id),
                      lambda: self.store.list_for(self.a),
                      lambda: self.store.create(self.a, "Late request"),
                      lambda: self.store.delete(self.a, self.chat.id)]
        for operation in operations:
            with self.assertRaises(PermissionError):
                operation()

    def test_owner_can_delete(self):
        self.store.delete(self.a, self.chat.id)
        self.assertEqual((), self.store.list_for(self.a))
