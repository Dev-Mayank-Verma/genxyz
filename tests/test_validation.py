from app.main import DOMAIN_RE

def test_valid_xyz():
    assert DOMAIN_RE.fullmatch('example.xyz')
    assert DOMAIN_RE.fullmatch('my-domain.xyz')

def test_invalid_domains():
    assert not DOMAIN_RE.fullmatch('example.com')
    assert not DOMAIN_RE.fullmatch('example')
    assert not DOMAIN_RE.fullmatch('-bad.xyz')
