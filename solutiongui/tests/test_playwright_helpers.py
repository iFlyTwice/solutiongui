import sys
import os
import unittest
from core.playwright_helpers import open_page, close_resources

# Add the project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'FutureUpdate')))

class TestPlaywrightHelpers(unittest.IsolatedAsyncioTestCase):
    async def test_open_and_close_page(self):
        url = "https://example.com"
        page, context, browser, playwright = await open_page(url)
        self.assertIsNotNone(page)
        await close_resources(page, context, browser, playwright)

if __name__ == '__main__':
    unittest.main() 