import asyncio
import unittest
from unittest.mock import patch, AsyncMock
from playwright.async_api import Page, Browser, BrowserContext
from core.playwright_helpers import open_page, close_resources

class TestPlaywrightHelpers(unittest.IsolatedAsyncioTestCase):
    async def test_open_page_success(self):
        """
        Test if `open_page` successfully opens a valid URL.
        """
        url = "https://example.com"
        with patch('playwright.async_api.async_playwright') as mock_playwright:
            mock_browser = AsyncMock(spec=Browser)
            mock_context = AsyncMock(spec=BrowserContext)
            mock_page = AsyncMock(spec=Page)
            mock_playwright.start.return_value = AsyncMock(
                chromium=AsyncMock(
                    launch=AsyncMock(return_value=mock_browser),
                )
            )
            mock_browser.new_context.return_value = mock_context
            mock_context.new_page.return_value = mock_page

            page, context, browser, playwright = await open_page(url)

            mock_page.goto.assert_called_with(url, timeout=60000)
            self.assertEqual(page, mock_page)
            self.assertEqual(context, mock_context)
            self.assertEqual(browser, mock_browser)

    async def test_close_resources_success(self):
        """
        Test if `close_resources` cleans up resources without errors.
        """
        mock_page = AsyncMock(spec=Page)
        mock_context = AsyncMock(spec=BrowserContext)
        mock_browser = AsyncMock(spec=Browser)
        mock_playwright = AsyncMock()

        await close_resources(mock_page, mock_context, mock_browser, mock_playwright)

        mock_page.close.assert_awaited_once()
        mock_context.close.assert_awaited_once()
        mock_browser.close.assert_awaited_once()
        mock_playwright.stop.assert_awaited_once()

    async def test_open_page_failure(self):
        """
        Test if `open_page` raises an exception for invalid URLs.
        """
        url = "https://invalid-url.example.com"
        with patch('playwright.async_api.async_playwright') as mock_playwright:
            mock_browser = AsyncMock(spec=Browser)
            mock_playwright.start.return_value = AsyncMock(
                chromium=AsyncMock(
                    launch=AsyncMock(return_value=mock_browser),
                )
            )
            mock_browser.new_context.side_effect = Exception("Invalid URL")

            with self.assertRaises(Exception) as context:
                await open_page(url)
            self.assertIn("Invalid URL", str(context.exception))

if __name__ == '__main__':
    unittest.main() 