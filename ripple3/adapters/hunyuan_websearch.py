"""Tencent Cloud Web Search API (联网搜索) adapter.

Uses the SearchPro action on wsa.tencentcloudapi.com with TC3-HMAC-SHA256
signing.  Env: TENCENT_SECRET_ID, TENCENT_SECRET_KEY.
"""

from __future__ import annotations

import datetime
import hashlib
import hmac
import json
import logging
import os
from typing import Any

import httpx

log = logging.getLogger(__name__)

_HOST = "wsa.tencentcloudapi.com"
_ENDPOINT = f"https://{_HOST}"
_SERVICE = "wsa"
_ACTION = "SearchPro"
_VERSION = "2025-05-08"
_REGION = ""
_TIMEOUT = httpx.Timeout(connect=5, read=30, write=5, pool=5)


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _hmac_sha256(key: bytes, msg: bytes) -> bytes:
    return hmac.new(key, msg, hashlib.sha256).digest()


def _build_auth_header(
    secret_id: str,
    secret_key: str,
    payload: str,
    timestamp: int,
) -> dict[str, str]:
    """Build Tencent Cloud API v3 (TC3-HMAC-SHA256) Authorization header."""
    date = datetime.datetime.fromtimestamp(timestamp, tz=datetime.timezone.utc).strftime("%Y-%m-%d")
    credential_scope = f"{date}/{_SERVICE}/tc3_request"

    # ---- Step 1: Canonical request ----
    http_method = "POST"
    canonical_uri = "/"
    canonical_querystring = ""
    ct = "application/json; charset=utf-8"
    canonical_headers = (
        f"content-type:{ct}\n"
        f"host:{_HOST}\n"
        f"x-tc-action:{_ACTION.lower()}\n"
    )
    signed_headers = "content-type;host;x-tc-action"
    hashed_payload = _sha256(payload.encode("utf-8"))

    canonical_request = "\n".join([
        http_method,
        canonical_uri,
        canonical_querystring,
        canonical_headers,
        signed_headers,
        hashed_payload,
    ])

    # ---- Step 2: String to sign ----
    algorithm = "TC3-HMAC-SHA256"
    string_to_sign = "\n".join([
        algorithm,
        str(timestamp),
        credential_scope,
        _sha256(canonical_request.encode("utf-8")),
    ])

    # ---- Step 3: Signing key ----
    secret_date = _hmac_sha256(f"TC3{secret_key}".encode("utf-8"), date.encode("utf-8"))
    secret_service = _hmac_sha256(secret_date, _SERVICE.encode("utf-8"))
    secret_signing = _hmac_sha256(secret_service, b"tc3_request")

    # ---- Step 4: Signature ----
    signature = hmac.new(secret_signing, string_to_sign.encode("utf-8"), hashlib.sha256).hexdigest()

    authorization = (
        f"{algorithm} "
        f"Credential={secret_id}/{credential_scope}, "
        f"SignedHeaders={signed_headers}, "
        f"Signature={signature}"
    )

    return {
        "Authorization": authorization,
        "Content-Type": ct,
        "Host": _HOST,
        "X-TC-Action": _ACTION,
        "X-TC-Version": _VERSION,
        "X-TC-Timestamp": str(timestamp),
        **({"X-TC-Region": _REGION} if _REGION else {}),
    }


async def search_hunyuan_web(
    query: str,
    count: int = 10,
    *,
    mode: int = 2,
    site: str = "",
    from_time: str = "",
    to_time: str = "",
) -> list[dict[str, str]]:
    """Search the web via Tencent's SearchPro (联网搜索) API.

    Args:
        query: Search query string.
        count: Maximum number of results (1-20, default 10).
        mode:  Search mode — 0=natural language, 1=vertical results,
               2=mixed (default).
        site:  Optional domain filter (e.g. ``"zhihu.com"``).
        from_time: Optional start time filter (``"YYYY-MM-DD"``).
        to_time:   Optional end time filter (``"YYYY-MM-DD"``).

    Returns:
        A list of dicts, each with keys ``title``, ``url``, ``snippet``,
        ``source``.  Returns an empty list on any failure.
    """
    secret_id = os.getenv("TENCENT_SECRET_ID", "")
    secret_key = os.getenv("TENCENT_SECRET_KEY", "")
    if not secret_id or not secret_key:
        log.debug("TENCENT_SECRET_ID / TENCENT_SECRET_KEY not set — skipping web search")
        return []

    body: dict[str, Any] = {
        "Query": query,
        "Cnt": min(max(count, 1), 20),
        "Mode": mode,
    }
    if site:
        body["Site"] = site
    if from_time:
        body["FromTime"] = from_time
    if to_time:
        body["ToTime"] = to_time

    payload = json.dumps(body, ensure_ascii=False)
    timestamp = int(datetime.datetime.now(tz=datetime.timezone.utc).timestamp())
    headers = _build_auth_header(secret_id, secret_key, payload, timestamp)

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.post(_ENDPOINT, content=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
    except httpx.HTTPStatusError as exc:
        _log_api_error(exc.response, query)
        return []
    except Exception as exc:
        log.warning("Tencent web search request failed for '%s': %s", query[:80], exc)
        return []

    return _parse_response(data, query)


def _log_api_error(resp: httpx.Response, query: str) -> None:
    try:
        err = resp.json().get("Response", {}).get("Error", {})
        code = err.get("Code", resp.status_code)
        msg = err.get("Message", resp.text[:200])
    except Exception:
        code, msg = resp.status_code, resp.text[:200]
    log.warning("Tencent web search API error for '%s': [%s] %s", query[:80], code, msg)


def _parse_response(data: dict, query: str) -> list[dict[str, str]]:
    """Parse SearchPro response into a flat list of result dicts."""
    response = data.get("Response", {})

    if "Error" in response:
        err = response["Error"]
        log.warning(
            "Tencent web search returned error for '%s': [%s] %s",
            query[:80],
            err.get("Code", "?"),
            err.get("Message", "?"),
        )
        return []

    results: list[dict[str, str]] = []
    for page in response.get("Pages", []):
        title = (page.get("Title") or "").strip()
        url = (page.get("Url") or "").strip()
        snippet = (page.get("Summary") or page.get("Content") or "").strip()
        if not url:
            continue
        source = _extract_source(url)
        results.append({
            "title": title,
            "url": url,
            "snippet": snippet,
            "source": source,
        })
    return results


def _extract_source(url: str) -> str:
    """Derive a short source label from a URL's domain."""
    try:
        from urllib.parse import urlparse
        host = urlparse(url).hostname or ""
        parts = host.split(".")
        if len(parts) >= 2:
            return parts[-2]
        return host
    except Exception:
        return ""
