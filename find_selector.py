import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto("https://github.com/topics/workflow-automation")
        await page.wait_for_selector("article.border")

        # Try to find elements that look like star counts
        # They usually have a number followed by 'k' or just a number
        # and are near a star icon.
        items = await page.evaluate("""() => {
            const articles = Array.from(document.querySelectorAll('article.border'));
            return articles.map(article => {
                const text = article.innerText;
                const starMatch = text.match(/Star\s+([\d.k,]+)/i);
                return {
                    repo: article.querySelector('h3.f3 a.text-bold')?.innerText.trim(),
                    starMatch: starMatch ? starMatch[0] : 'not found'
                };
            });
        }""")
        print(items[:3])

        # Let's also look for the specific element
        selector_check = await page.evaluate("""() => {
            const el = document.querySelector('article.border .Counter.js-social-count');
            if (el) return '.Counter.js-social-count';

            // On topics page, stars are often inside a link with 'stargazers'
            const starLink = document.querySelector('a[href$="/stargazers"]');
            if (starLink) return 'a[href$="/stargazers"]';

            return 'not found';
        }""")
        print(f"Detected selector: {selector_check}")

        await browser.close()

asyncio.run(main())
