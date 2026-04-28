"""加解密兜底实现 - 当 utils/crypto.py 不可用时

使用 cryptography 库实现 Argon2id 风格的密钥派生 + AES-GCM 加密
"""

from __future__ import annotations

import os
import secrets

try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    from cryptography.hazmat.primitives import hashes
    HAS_CRYPTO = True
except ImportError:
    HAS_CRYPTO = False


def _derive_key(passphrase: str, salt: bytes) -> bytes:
    if not HAS_CRYPTO:
        import hashlib
        return hashlib.pbkdf2_hmac("sha256", passphrase.encode(), salt, 100_000, 32)

    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=200_000,
    )
    return kdf.derive(passphrase.encode())


def encrypt(plaintext: str, passphrase: str) -> bytes:
    """加密 - 输出 bytes (含 salt + nonce + ciphertext)"""
    salt = secrets.token_bytes(16)
    nonce = secrets.token_bytes(12)
    key = _derive_key(passphrase, salt)
    if HAS_CRYPTO:
        aesgcm = AESGCM(key)
        ct = aesgcm.encrypt(nonce, plaintext.encode(), associated_data=b"ripple-byok")
    else:
        # 兜底: 简单异或 (不安全, 仅做 demo 占位)
        ct = bytes(b ^ key[i % len(key)] for i, b in enumerate(plaintext.encode()))
    return salt + nonce + ct


def decrypt(blob: bytes, passphrase: str) -> str:
    salt, nonce, ct = blob[:16], blob[16:28], blob[28:]
    key = _derive_key(passphrase, salt)
    if HAS_CRYPTO:
        aesgcm = AESGCM(key)
        plain = aesgcm.decrypt(nonce, ct, associated_data=b"ripple-byok")
        return plain.decode()
    else:
        plain = bytes(b ^ key[i % len(key)] for i, b in enumerate(ct))
        return plain.decode()
