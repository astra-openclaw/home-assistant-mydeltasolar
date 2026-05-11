#!/usr/bin/env python3
"""Safely probe MyDeltaSolar endpoints and print redacted schemas.

This script is for manual mapping only. It must not write raw payloads, cookies,
passwords, or private identifiers to the repo.
"""

from __future__ import annotations

import argparse
import getpass
import json
import sys
import time
from collections.abc import Mapping
from typing import Any

import requests

BASE_URL = "https://mydeltasolar.deltaww.com/"

SENSITIVE_KEY_HINTS = (
    "email",
    "mail",
    "password",
    "pwd",
    "token",
    "cookie",
    "session",
    "serial",
    "sn",
    "plant_id",
    "pid",
    "id",
    "img",
    "image",
    "url",
    "location",
    "address",
    "lat",
    "lng",
    "lon",
    "name",
)


def redact_scalar(key: str, value: Any) -> Any:
    """Redact likely identifying scalar values while preserving type/unit clues."""
    lower = key.lower()
    if any(hint in lower for hint in SENSITIVE_KEY_HINTS):
        if value is None:
            return None
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return "<redacted-number>"
        return "<redacted>"
    return value


def summarize(value: Any, key: str = "", depth: int = 0) -> Any:
    """Return a redacted shape summary."""
    if depth > 4:
        return type(value).__name__
    if isinstance(value, Mapping):
        return {
            "type": "dict",
            "keys": sorted(str(k) for k in value),
            "sample": {
                str(k): summarize(v, str(k), depth + 1)
                for k, v in list(value.items())[:12]
            },
        }
    if isinstance(value, list):
        return {
            "type": "list",
            "len": len(value),
            "head": [summarize(v, key, depth + 1) for v in value[:3]],
            "tail": [summarize(v, key, depth + 1) for v in value[-3:]],
        }
    if isinstance(value, tuple):
        return summarize(list(value), key, depth)
    return redact_scalar(key, value)


def request_json(session: requests.Session, method: str, path: str, **kwargs: Any) -> tuple[int, str, Any]:
    url = BASE_URL + path.lstrip("/")
    response = session.request(method, url, timeout=30, **kwargs)
    text = response.text
    if not text.strip():
        return response.status_code, response.headers.get("content-type", ""), None
    try:
        return response.status_code, response.headers.get("content-type", ""), response.json()
    except Exception:
        return response.status_code, response.headers.get("content-type", ""), {"non_json_prefix": text[:120]}


def print_probe(label: str, status: int, content_type: str, payload: Any) -> None:
    print(f"\n## {label}")
    print(f"status: {status}")
    print(f"content_type: {content_type}")
    if isinstance(payload, Mapping) and payload.get("non_json_prefix") is not None:
        print("non_json_prefix:", repr(payload["non_json_prefix"]))
        return
    print(json.dumps(summarize(payload), indent=2, ensure_ascii=False))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--username", required=True)
    parser.add_argument("--sleep", type=float, default=0.5, help="Delay between probes")
    args = parser.parse_args()

    password = getpass.getpass("MyDeltaSolar password: ")
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": "Mozilla/5.0 HomeAssistant-MyDeltaSolar-Mapper/0.1",
            "Accept-Language": "en-US,en;q=0.9",
        }
    )

    session.get(BASE_URL + "index.php?p=login", timeout=30)
    login_status, _login_ct, login_payload = request_json(
        session,
        "POST",
        "web/process_login.php",
        data={"email": args.username, "password": password},
        headers={
            "Origin": BASE_URL.rstrip("/"),
            "Referer": BASE_URL + "index.php?p=login",
            "X-Requested-With": "XMLHttpRequest",
            "Accept": "application/json, text/javascript, */*; q=0.01",
        },
    )
    print("login_status:", login_status)
    print("login_ok:", isinstance(login_payload, Mapping) and not bool(login_payload.get("errmsg")))
    if not isinstance(login_payload, Mapping) or login_payload.get("errmsg"):
        return 1

    headers = {
        "X-Requested-With": "XMLHttpRequest",
        "Referer": BASE_URL + "index.php?p=m_gtop",
        "Accept": "application/json, text/javascript, */*; q=0.01",
    }

    probes: list[tuple[str, str, str, dict[str, str] | None]] = [
        ("init plant", "GET", "web/process_init_plant.php", None),
        ("init energy all plants", "POST", "web/process_init_energy.php", {"is_all_plants": "1"}),
        ("plant graph day all", "POST", "web/process_gtop_plot.php", {"unit": "day", "is_all_plants": "1"}),
        ("plant graph month all", "POST", "web/process_gtop_plot.php", {"unit": "month", "is_all_plants": "1"}),
        ("plant graph year all", "POST", "web/process_gtop_plot.php", {"unit": "year", "is_all_plants": "1"}),
    ]

    for label, method, path, data in probes:
        time.sleep(args.sleep)
        kwargs: dict[str, Any] = {"headers": headers}
        if data is not None:
            kwargs["data"] = data
        status, ct, payload = request_json(session, method, path, **kwargs)
        print_probe(label, status, ct, payload)

    return 0


if __name__ == "__main__":
    sys.exit(main())
