from app.registrar import RegistrarClient
from app.main import DOMAIN_RE

def test_xyz_regex_examples():
    assert DOMAIN_RE.fullmatch('hello.xyz')
    assert DOMAIN_RE.fullmatch('hello-world.xyz')
    assert not DOMAIN_RE.fullmatch('hello.com')
    assert not DOMAIN_RE.fullmatch('hello.xyz.com')
