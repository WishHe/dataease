#!/usr/bin/env python3
"""Fetch official template market listing (optional). Downloads are skipped if offline."""

from __future__ import annotations

import argparse
import json
import ssl
import sys
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from common import RAW_DIR, ensure_dirs  # noqa: E402

DEFAULT_BASES = [
    "https://dataease.io/templates",
    "https://templates.dataease.cn",
]
LIST_API = (
    "/apis/api.store.halo.run/v1alpha1/applications"
    "?keyword=&priceMode=&sort=latestReleaseTimestamp%2Cdesc"
    "&type=THEME&deVersion=V2&templateType=&label=&page=1&size=2000"
)


def fetch(url: str, timeout: int = 12) -> bytes:
    ctx = ssl.create_default_context()
    req = urllib.request.Request(url, headers={"User-Agent": "dv-board-compose/0.1"})
    with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
        return resp.read()


def encode_url(base: str, link: str) -> str:
    if link.startswith("http://") or link.startswith("https://"):
        parsed = urllib.parse.urlsplit(link)
        path = urllib.parse.quote(urllib.parse.unquote(parsed.path), safe="/-%._")
        return urllib.parse.urlunsplit((parsed.scheme, parsed.netloc, path, parsed.query, parsed.fragment))
    path = urllib.parse.quote(urllib.parse.unquote(link), safe="/-%._")
    return base.rstrip("/") + path


def safe_filename(link: str, title: str, template_type: str) -> str:
    raw = urllib.parse.unquote(link.split("/")[-1]).replace(" ", "-")
    if not raw.lower().endswith(".det2"):
        raw = (title or "template") + "-TEMPLATE.DET2"
    prefix = "SCREEN" if template_type == "SCREEN" else ("PANEL" if template_type == "PANEL" else "OTHER")
    return f"{prefix}-{raw}"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="", help="template.url, e.g. https://dataease.io/templates")
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--download", action="store_true", help="download STYLE .DET2 files")
    args = parser.parse_args()
    ensure_dirs()
    bases = [args.base] if args.base else DEFAULT_BASES
    last_error = None
    for base in bases:
        base = base.rstrip("/")
        url = base + LIST_API
        try:
            raw = fetch(url)
            data = json.loads(raw.decode("utf-8"))
        except Exception as exc:  # noqa: BLE001
            last_error = f"{url}: {exc}"
            continue
        out = RAW_DIR / "market-list.json"
        out.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        items = data.get("items") or []
        index = []
        for item in items:
            spec = (item.get("application") or {}).get("spec") or {}
            meta = (item.get("application") or {}).get("metadata") or {}
            link = ((spec.get("links") or [{}])[0] or {}).get("url") or ""
            index.append(
                {
                    "name": meta.get("name"),
                    "title": spec.get("displayName"),
                    "templateType": spec.get("templateType"),
                    "label": spec.get("label"),
                    "suggest": spec.get("suggest"),
                    "classify": spec.get("templateClassification"),
                    "screenshot": ((spec.get("screenshots") or [{}])[0] or {}).get("url"),
                    "link": link,
                }
            )
        (RAW_DIR / "market-index.json").write_text(
            json.dumps({"base": base, "count": len(index), "items": index}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        style_det2 = [
            it
            for it in index
            if (it.get("classify") or "").upper() in {"STYLE", "TEMPLATE", ""}
            and str(it.get("link") or "").upper().endswith(".DET2")
            and not str(it.get("link") or "").upper().endswith(".DET2APP")
        ]
        # keep SCREEN/PANEL mix: take panels first then screens
        panels = [it for it in style_det2 if it.get("templateType") == "PANEL"]
        screens = [it for it in style_det2 if it.get("templateType") == "SCREEN"]
        others = [it for it in style_det2 if it not in panels and it not in screens]
        queued = panels[: max(8, args.limit // 3)] + screens + others
        print(f"ok base={base} listed={len(index)} style_det2={len(style_det2)} panel={len(panels)} screen={len(screens)}")
        if not args.download:
            print("pass --download to fetch STYLE .DET2 into workspace/raw/")
            return
        downloaded = 0
        skipped = 0
        for item in queued:
            if downloaded >= args.limit:
                break
            link = item.get("link") or ""
            dest = RAW_DIR / safe_filename(link, item.get("title") or "template", item.get("templateType") or "")
            if dest.exists() and dest.stat().st_size > 1000:
                skipped += 1
                print(f"exists {dest.name}")
                downloaded += 1
                continue
            file_url = encode_url(base, link)
            try:
                body = fetch(file_url, timeout=90)
            except Exception as exc:  # noqa: BLE001
                print(f"skip {item.get('title')}: {exc}")
                continue
            if not body.lstrip().startswith(b"{") and not body.lstrip().startswith(b"["):
                print(f"skip {item.get('title')}: not json ({len(body)} bytes)")
                continue
            dest.write_bytes(body)
            downloaded += 1
            print(f"downloaded {dest.name} ({len(body)} bytes) [{item.get('templateType')}] {item.get('title')}")
        print(f"downloaded {downloaded} DET2 (skipped existing {skipped}) into {RAW_DIR}")
        return
    print("market unreachable (expected in some networks)")
    if last_error:
        print(last_error)
    raise SystemExit(2)


if __name__ == "__main__":
    main()
