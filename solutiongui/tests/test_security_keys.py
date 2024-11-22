import sys
import os
import unittest
from security_keys import SecurityKeys

# Add the project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'FutureUpdate')))

class TestSecurityKeys(unittest.TestCase):
    def setUp(self):
        self.security_keys = SecurityKeys()

    def test_add_key(self):
        self.security_keys.add_key("key1")
        self.assertIn("key1", self.security_keys.get_keys())

    def test_remove_key(self):
        self.security_keys.add_key("key2")
        self.security_keys.remove_key("key2")
        self.assertNotIn("key2", self.security_keys.get_keys())

if __name__ == '__main__':
    unittest.main() 