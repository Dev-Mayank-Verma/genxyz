import re

DOMAIN_RE = re.compile(r"^(?=.{1,253}$)([a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)xyz$", re.I)


def test_valid_xyz_domain():
    assert DOMAIN_RE.fullmatch("example.xyz")
    assert DOMAIN_RE.fullmatch("my-domain.xyz")


def test_invalid_domain():
    assert not DOMAIN_RE.fullmatch("example.com")
    assert not DOMAIN_RE.fullmatch("-bad.xyz")
    assert not DOMAIN_RE.fullmatch("bad-.xyz")
