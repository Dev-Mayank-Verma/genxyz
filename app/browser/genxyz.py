import asyncio
import os
from dataclasses import dataclass
from typing import Optional
from playwright.async_api import async_playwright, Page, BrowserContext


class GenXYZBrowserError(RuntimeError):
    pass


@dataclass
class CheckoutResult:
    available: bool
    checkout_url: Optional[str] = None
    price_text: Optional[str] = None
    message: Optional[str] = None


class GenXYZBrowser:
    """Customer-like Playwright flow for the public Gen.xyz checkout.

    This intentionally does not bypass Cloudflare/CAPTCHA/anti-bot controls and
    does not submit a final order or payment automatically. It prepares the
    normal checkout and lets the user complete the final action in the browser.
    """

    def __init__(self, headless: bool = True):
        self.headless = headless
        self.base_url = os.getenv("GENXYZ_URL", "https://gen.xyz")
        self.coupon = os.getenv("GENXYZ_COUPON_CODE", "HFY26")
        self.timeout_ms = int(os.getenv("BROWSER_TIMEOUT_MS", "30000"))

    async def _dismiss_optional(self, page: Page, texts: list[str]):
        for text in texts:
            try:
                loc = page.get_by_text(text, exact=True).first
                if await loc.count():
                    await loc.click(timeout=2500)
                    await page.wait_for_timeout(500)
                    return
            except Exception:
                pass

    async def prepare_checkout(
        self,
        domain: str,
        first_name: str,
        last_name: str,
        email: str,
        address: str,
        city: str,
        region: str,
        postal_code: str,
        country: str = "India",
    ) -> CheckoutResult:
        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=self.headless)
            context: BrowserContext = await browser.new_context(viewport={"width": 390, "height": 844})
            page = await context.new_page()
            page.set_default_timeout(self.timeout_ms)
            try:
                await page.goto(self.base_url, wait_until="domcontentloaded")
                await page.wait_for_timeout(1200)

                # If an anti-bot challenge appears, stop instead of trying to bypass it.
                body = (await page.locator("body").inner_text()).lower()
                blocked_markers = ["verify you are human", "checking your browser", "captcha", "cloudflare"]
                if any(m in body for m in blocked_markers):
                    raise GenXYZBrowserError("Gen.xyz anti-bot/challenge page detected; manual browser completion is required.")

                # Register page / search field.
                candidates = [
                    page.get_by_role("link", name="Register"),
                    page.get_by_role("button", name="Register"),
                    page.get_by_text("Register", exact=True),
                ]
                clicked = False
                for loc in candidates:
                    try:
                        if await loc.count():
                            await loc.first.click()
                            clicked = True
                            break
                    except Exception:
                        pass
                if not clicked:
                    await page.goto(f"{self.base_url}/register", wait_until="domcontentloaded")
                await page.wait_for_timeout(1000)

                inputs = page.locator("input")
                # Find a likely domain search field by placeholder/name first.
                domain_input = None
                for selector in [
                    'input[placeholder*="domain" i]',
                    'input[name*="domain" i]',
                    'input[type="text"]',
                ]:
                    loc = page.locator(selector).first
                    if await loc.count():
                        domain_input = loc
                        break
                if domain_input is None:
                    raise GenXYZBrowserError("Could not find the domain search field; Gen.xyz UI may have changed.")
                await domain_input.fill(domain)

                # Search/availability action.
                for name in ["Search", "Check", "Find", "Search Domain"]:
                    loc = page.get_by_role("button", name=name, exact=True).first
                    try:
                        if await loc.count():
                            await loc.click()
                            break
                    except Exception:
                        continue
                else:
                    await domain_input.press("Enter")

                await page.wait_for_timeout(1500)
                body = (await page.locator("body").inner_text()).lower()
                if "not available" in body or "unavailable" in body:
                    return CheckoutResult(False, message="Domain is not available.")
                if "it's available" not in body and "available" not in body:
                    # Do not guess. Return a useful diagnostic.
                    return CheckoutResult(False, message="Availability result was not recognized; inspect the Gen.xyz page manually.")

                # Add/register the domain.
                for name in ["Register", "Add to Cart", "Buy"]:
                    loc = page.get_by_role("button", name=name, exact=True).first
                    try:
                        if await loc.count():
                            await loc.click()
                            break
                    except Exception:
                        continue
                await page.wait_for_timeout(1200)

                # Continue to recommended add-ons, then opt out of optional paid add-ons.
                for name in ["Next: Recommended Add-Ons", "Recommended Add-Ons", "Continue"]:
                    loc = page.get_by_role("button", name=name, exact=True).first
                    try:
                        if await loc.count():
                            await loc.click()
                            break
                    except Exception:
                        continue
                await page.wait_for_timeout(800)

                # The recording chooses no paid add-ons. Use explicit labels when present.
                for _ in range(6):
                    await self._dismiss_optional(page, ["No Thanks", "No thanks", "Opt out of Weebly Website Builder"])
                    for name in ["Next: Info & Checkout", "Info & Checkout", "Continue to Checkout", "Continue"]:
                        loc = page.get_by_role("button", name=name, exact=True).first
                        try:
                            if await loc.count():
                                await loc.click()
                                break
                        except Exception:
                            continue
                    await page.wait_for_timeout(600)

                # Apply the legitimate promo code shown in the supplied recording.
                promo = page.locator('input').filter(has=page.locator('')) if False else None
                for selector in [
                    'input[placeholder*="promo" i]',
                    'input[name*="promo" i]',
                    'input[name*="coupon" i]',
                    'input[type="text"]',
                ]:
                    locs = page.locator(selector)
                    if await locs.count():
                        for i in range(await locs.count()):
                            candidate = locs.nth(i)
                            try:
                                if await candidate.is_visible():
                                    await candidate.fill(self.coupon)
                                    applied = page.get_by_role("button", name="Apply Code", exact=True).first
                                    if await applied.count():
                                        await applied.click()
                                    await page.wait_for_timeout(700)
                                    break
                            except Exception:
                                continue
                        else:
                            continue
                        break

                # Fill customer details where labels are exposed. We deliberately avoid card fields.
                async def fill_label(label: str, value: str):
                    if not value:
                        return
                    try:
                        loc = page.get_by_label(label, exact=False).first
                        if await loc.count():
                            await loc.fill(value)
                            return
                    except Exception:
                        pass

                await fill_label("First Name", first_name)
                await fill_label("Last Name", last_name)
                await fill_label("Email Address", email)
                await fill_label("Street Address", address)
                await fill_label("City", city)
                await fill_label("State", region)
                await fill_label("Postal", postal_code)
                await fill_label("ZIP", postal_code)
                await fill_label("Country", country)

                return CheckoutResult(True, await page.url, message="Checkout prepared. Complete any remaining required fields and final submission manually.")
            finally:
                await context.close()
                await browser.close()
