import asyncio
import os
from browser_use import Agent
from langchain_openai import ChatOpenAI

async def run():
    # Use a dummy LLM or real if OPENAI_API_KEY is set.
    # Actually, we can just use playwright directly to take a screenshot to avoid LLM dependency if we just want to see the page.
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto("https://yoro.etzhayyim.com/")
        await page.wait_for_timeout(3000)
        await page.screenshot(path="screenshot.png")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
