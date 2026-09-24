def test_browser_module_imports():
    from app.browser.genxyz import GenXYZBrowser, CheckoutResult
    assert GenXYZBrowser is not None
    assert CheckoutResult is not None
