# Gen.xyz Telegram Bot — Playwright / Render build

This build follows the flow visible in the supplied screen recording:

1. Telegram `/start` — no login at the beginning.
2. Search for a `.xyz` domain.
3. Check availability.
4. Use a 1-year registration.
5. Decline optional paid add-ons (WHOIS privacy, paid Workspace, paid website-builder plans).
6. Apply the legitimate promotional code configured in `GENXYZ_COUPON_CODE` (the supplied recording shows `HFY26`).
7. Collect the customer's real contact details.
8. Prepare the normal Gen.xyz checkout.
9. Registration/email verification is tracked after the user completes the registrar's final checkout/verification steps.

## Why Playwright is included

You asked for browser-style automation rather than a made-up Gen.xyz API. `app/browser/genxyz.py` uses Playwright/Chromium to interact with the public customer-facing site like a normal browser.

The automation **does not bypass Cloudflare, CAPTCHA, anti-bot checks, rate limits, or other access controls**. If Gen.xyz presents an anti-bot challenge, the worker stops and reports it.

It also does not collect or automate credit-card entry. The bot is designed to stop at checkout rather than silently submit a financial transaction.

## Render

Use the included `Dockerfile` because it contains the Playwright/Chromium runtime.

Create a Render Web Service from this repository/ZIP after uploading it to GitHub. Add:

```text
TELEGRAM_BOT_TOKEN=...
TELEGRAM_WEBHOOK_SECRET=...
PUBLIC_BASE_URL=https://YOUR-SERVICE.onrender.com
DATABASE_URL=...
GENXYZ_URL=https://gen.xyz
GENXYZ_COUPON_CODE=HFY26
BROWSER_TIMEOUT_MS=30000
```

Do not commit `.env` or secrets.

## Verification performed locally

- Python syntax compilation for all application modules.
- Unit tests for domain validation and Playwright module import.
- ZIP integrity check before delivery.

A live domain registration was **not** performed during testing, so no claim is made that Gen.xyz's current production selectors or promotion will remain unchanged. The site can change its UI at any time.
