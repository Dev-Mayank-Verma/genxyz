# Playwright Gen.xyz flow

`genxyz.py` models the customer-facing flow visible in the supplied recording:

- open Gen.xyz
- go to Register
- search a `.xyz` domain
- select the 1-year registration
- decline optional paid add-ons
- enter the legitimate promotional code configured by `GENXYZ_COUPON_CODE`
- fill customer details
- stop at checkout

It deliberately does **not** defeat Cloudflare, CAPTCHA, rate limits, bot detection, or other anti-automation controls. If an anti-bot challenge appears, the flow raises `GenXYZBrowserError` and stops.

It also does not type or store credit-card data.
