#!/usr/bin/env python3
"""
Download Echo360 lecture transcripts (.vtt) for one or more course sections.

Usage:
  python3 echo360_download.py --cookies cookies.txt COURSE=SECTION [COURSE=SECTION ...]
  python3 echo360_download.py --cookies cookies.txt --list CSSE3030=https://echo360.net.au/section/<id>/home

SECTION is either the section ID or the full section URL from your browser.
Transcripts land in <out>/<COURSE>/<date>_<lesson name>.vtt. Re-running skips files already downloaded.
Standard library only, no installs needed.
"""

import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

UUID = r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"


def load_cookie_header(path: Path) -> str:
    """Turn a Netscape cookies.txt export into a Cookie header value."""
    pairs = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if line.startswith("#HttpOnly_"):
            line = line[len("#HttpOnly_"):]
        if not line or line.startswith("#"):
            continue
        parts = line.split("\t")
        if len(parts) >= 7:
            pairs.append(f"{parts[5]}={parts[6]}")
    if not pairs:
        sys.exit(f"No cookies found in {path}. Export them in Netscape (cookies.txt) format.")
    return "; ".join(pairs)


def parse_section(arg: str, default_host: str) -> tuple[str, str, str]:
    """'COURSE=ID_or_URL' -> (course, host, section_id)."""
    course, sep, target = arg.partition("=")
    match = re.search(UUID, target, re.I)
    if not sep or not course or not match:
        sys.exit(f"Bad course argument {arg!r}. Expected COURSE=SECTION_ID or COURSE=SECTION_URL.")
    host = re.match(r"https?://[^/]+", target)
    return course, host.group(0) if host else default_host, match.group(0)


def get(url: str, cookie: str) -> tuple[int, bytes]:
    req = urllib.request.Request(url, headers={
        "Cookie": cookie, "User-Agent": "Mozilla/5.0", "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, b""


def lessons(items: list[dict]):
    """Yield (filename_stem, media_id) for every available recording in a syllabus."""
    for i, item in enumerate(items):
        lesson = item.get("lesson", {})
        info = lesson.get("lesson", {})
        name = info.get("displayName") or info.get("name") or f"lesson_{i:03d}"
        date = (lesson.get("startTimeUTC") or "")[:10]
        stem = re.sub(r'[<>:"/\\|?*]', "_", f"{date}_{name}" if date else name).strip()
        ids = [m["id"] for m in lesson.get("medias", []) if m.get("id") and m.get("isAvailable")]
        for j, media_id in enumerate(ids):
            yield (f"{stem}_{j}" if len(ids) > 1 else stem), media_id


def main() -> None:
    p = argparse.ArgumentParser(description="Download Echo360 transcripts.")
    p.add_argument("courses", nargs="+", metavar="COURSE=SECTION")
    p.add_argument("--cookies", required=True, type=Path, help="Netscape-format cookies.txt for your Echo360 host")
    p.add_argument("--out", default="transcripts", type=Path, help="output folder (default: transcripts)")
    p.add_argument("--host", default="https://echo360.net.au",
                   help="Echo360 host when SECTION is a bare ID (e.g. https://echo360.org, https://echo360.org.uk)")
    p.add_argument("--list", action="store_true", help="list lessons without downloading")
    args = p.parse_args()

    cookie = load_cookie_header(args.cookies)
    for arg in args.courses:
        course, host, section = parse_section(arg, args.host.rstrip("/"))
        print(f"\n=== {course} ({host}/section/{section}) ===")
        status, body = get(f"{host}/section/{section}/syllabus", cookie)
        if status != 200:
            print(f"  [ERROR] HTTP {status}. If 401/403, your cookies have expired: log in and export them again.")
            continue
        try:
            items = json.loads(body)["data"]
        except (ValueError, KeyError):
            print("  [ERROR] Unexpected response. Your cookies may have expired (got a login page?).")
            continue
        print(f"  {len(items)} lessons found")

        for stem, media_id in lessons(items):
            out = args.out / course / f"{stem}.vtt"
            if args.list:
                print(f"  {stem}  ->  {media_id}")
            elif out.exists():
                print(f"  [EXISTS] {out.name}")
            else:
                status, vtt = get(f"{host}/media/{media_id}/transcription/latest"
                                  "?transcriptionType=vtt&download=true", cookie)
                if status != 200 or not vtt:
                    print(f"  [SKIP]   {stem} (no transcript, HTTP {status})")
                    continue
                out.parent.mkdir(parents=True, exist_ok=True)
                out.write_bytes(vtt)
                print(f"  [OK]     {out}")
                time.sleep(0.25)  # be polite to the server
    print("\nDone.")


if __name__ == "__main__":
    main()
