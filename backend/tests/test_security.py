"""密碼雜湊（scrypt）與 session token。"""

from app.core import security


def test_hash_and_verify_roundtrip():
    encoded = security.hash_password("correct-horse-42")

    assert encoded.startswith("scrypt$")
    assert "correct-horse-42" not in encoded
    assert security.verify_password("correct-horse-42", encoded)
    assert not security.verify_password("wrong-password", encoded)


def test_each_hash_uses_a_random_salt():
    assert security.hash_password("same-password") != security.hash_password("same-password")


def test_tampered_or_unknown_hash_is_rejected():
    algorithm, n, r, p, salt, key = security.hash_password("pw-123456").split("$")
    tampered = "$".join([algorithm, n, r, p, salt, ("A" if key[0] != "A" else "B") + key[1:]])

    assert not security.verify_password("pw-123456", tampered)
    assert not security.verify_password("pw-123456", "plain-text")
    assert not security.verify_password("pw-123456", "bcrypt$1$2$3$4$5")


def test_parameters_are_stored_with_the_hash(monkeypatch):
    encoded = security.hash_password("pw-123456")
    monkeypatch.setattr(security, "SCRYPT_N", 2**11)

    assert security.verify_password("pw-123456", encoded)  # 調整預設參數不影響舊帳號


def test_session_token_is_stored_as_sha256():
    token = security.new_session_token()

    assert len(token) >= 40
    assert security.hash_token(token) == security.hash_token(token)
    assert security.hash_token(token) != token
    assert len(security.hash_token(token)) == 64
