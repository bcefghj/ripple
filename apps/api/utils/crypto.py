"""加密工具:用户 BYOK API Key 本地加密存储

使用 AES-256-GCM + Argon2id 派生密钥
- 用户主密码 → Argon2id → 加密密钥
- 加密密钥 → AES-256-GCM → 加密 API Key
- 存储格式: salt(16) + nonce(12) + ciphertext + tag

参考:OWASP Cryptographic Storage Cheat Sheet
"""

from __future__ import annotations

import os
import secrets
from typing import Tuple

try:
    from argon2 import low_level
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
except ImportError:
    raise ImportError(
        "请安装加密库: pip install cryptography argon2-cffi"
    )


SALT_SIZE = 16
NONCE_SIZE = 12
KEY_SIZE = 32  # AES-256

# Argon2id 参数(2025 OWASP 推荐)
ARGON2_TIME_COST = 3
ARGON2_MEMORY_COST = 65536  # 64 MB
ARGON2_PARALLELISM = 4


def derive_key(passphrase: str, salt: bytes) -> bytes:
    """从用户密码派生加密密钥"""
    return low_level.hash_secret_raw(
        secret=passphrase.encode("utf-8"),
        salt=salt,
        time_cost=ARGON2_TIME_COST,
        memory_cost=ARGON2_MEMORY_COST,
        parallelism=ARGON2_PARALLELISM,
        hash_len=KEY_SIZE,
        type=low_level.Type.ID,
    )


def encrypt(plaintext: str, passphrase: str) -> bytes:
    """
    加密字符串(如 API Key)
    
    返回: salt(16) + nonce(12) + ciphertext+tag
    """
    salt = secrets.token_bytes(SALT_SIZE)
    key = derive_key(passphrase, salt)

    aesgcm = AESGCM(key)
    nonce = secrets.token_bytes(NONCE_SIZE)
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), associated_data=None)

    return salt + nonce + ciphertext


def decrypt(blob: bytes, passphrase: str) -> str:
    """解密"""
    if len(blob) < SALT_SIZE + NONCE_SIZE:
        raise ValueError("Invalid encrypted blob: too short")

    salt = blob[:SALT_SIZE]
    nonce = blob[SALT_SIZE:SALT_SIZE + NONCE_SIZE]
    ciphertext = blob[SALT_SIZE + NONCE_SIZE:]

    key = derive_key(passphrase, salt)
    aesgcm = AESGCM(key)
    plaintext = aesgcm.decrypt(nonce, ciphertext, associated_data=None)

    return plaintext.decode("utf-8")


def encrypt_with_master_key(plaintext: str, master_key: bytes) -> Tuple[bytes, bytes]:
    """
    用预派生的主密钥加密(适合服务端临时操作)
    
    返回: (nonce, ciphertext)
    """
    if len(master_key) != KEY_SIZE:
        raise ValueError(f"Master key must be {KEY_SIZE} bytes")

    aesgcm = AESGCM(master_key)
    nonce = secrets.token_bytes(NONCE_SIZE)
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), associated_data=None)

    return nonce, ciphertext


def decrypt_with_master_key(nonce: bytes, ciphertext: bytes, master_key: bytes) -> str:
    """用预派生的主密钥解密"""
    aesgcm = AESGCM(master_key)
    plaintext = aesgcm.decrypt(nonce, ciphertext, associated_data=None)
    return plaintext.decode("utf-8")


def generate_master_key() -> bytes:
    """生成新的主密钥(应妥善保管)"""
    return secrets.token_bytes(KEY_SIZE)


# ============================================================
# 简单测试
# ============================================================

if __name__ == "__main__":
    # 自测
    test_key = "sk-test-1234567890abcdef"
    test_password = "user-master-password-2026"

    print("=" * 50)
    print("Ripple 加密工具自测")
    print("=" * 50)

    print(f"\n原始 API Key: {test_key}")

    encrypted = encrypt(test_key, test_password)
    print(f"加密后 ({len(encrypted)} 字节,16 进制): {encrypted.hex()[:80]}...")

    decrypted = decrypt(encrypted, test_password)
    print(f"解密后: {decrypted}")

    assert decrypted == test_key, "解密失败!"
    print("\n✓ 测试通过")

    # 测试错误密码
    try:
        decrypt(encrypted, "wrong-password")
        print("✗ 错误密码应该解密失败但没有")
    except Exception as e:
        print(f"✓ 错误密码正确拦截: {type(e).__name__}")
