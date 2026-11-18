#!/usr/bin/env python3
"""Cổng kiểm ảnh — không có ảnh thì KHÔNG cho chạy bước sinh video.

Kiểm trên bảng vẽ của dự án (máy chủ 8001, cổng MCP):
  * thẻ tài sản (nhân vật / bối cảnh / đạo cụ / sinh vật / phong cách / sản phẩm)
    phải có ảnh;
  * thẻ cảnh phải có ảnh storyboard;
  * nhân vật ghi trong brief phải có thẻ tài sản mang ảnh;
  * bảng vẽ trống (0 tài sản, 0 cảnh) cũng là chặn — không có gì để kiểm thì
    không được coi là «đủ ảnh».

Thoát mã 1 khi còn thiếu ảnh (chặn bước sau), 0 khi đủ.

Dùng:
  python3 kiem-anh.py --canvas-id <mã bảng vẽ> [--brief <tệp brief.json>]
  python3 kiem-anh.py --canvas-id <mã> --json      # máy đọc
  python3 kiem-anh.py --selftest                   # tự kiểm logic, không cần máy chủ
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request

MCP_DEFAULT = "http://127.0.0.1:8001/mcp"
BASE_DEFAULT = "http://127.0.0.1:8001"

#: Loại tài sản theo đúng danh mục của dự án, kèm nhãn tiếng Việt để báo lỗi.
ASSET_LABELS = {
    "character": "nhân vật",
    "environment": "bối cảnh",
    "object": "đạo cụ",
    "style": "phong cách",
    "product": "sản phẩm",
    "custom": "tài sản khác",
}


def _rpc(url: str, name: str, args: dict, req_id: int = 1) -> dict:
    body = json.dumps(
        {"jsonrpc": "2.0", "id": req_id, "method": "tools/call",
         "params": {"name": name, "arguments": args}}
    ).encode("utf-8")
    req = urllib.request.Request(
        url, data=body, headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=90) as resp:
        payload = json.load(resp)
    if "error" in payload:
        raise RuntimeError(payload["error"].get("message") or "lỗi MCP")
    content = (payload.get("result") or {}).get("content") or []
    if not content:
        raise RuntimeError("máy chủ trả về rỗng")
    return json.loads(content[0]["text"])


def _has_image(node: dict) -> bool:
    """Thẻ có ảnh thật hay không: media_ref/media_refs mang ảnh."""
    refs = []
    if node.get("media_ref"):
        refs.append(node["media_ref"])
    refs.extend(node.get("media_refs") or [])
    for ref in refs:
        if isinstance(ref, dict) and str(ref.get("media_type") or "") == "image":
            if ref.get("object_key") or ref.get("files") or ref.get("primary"):
                return True
    return False


def _label(node: dict) -> str:
    kind = str(node.get("asset_kind") or node.get("kind") or "")
    name = str(node.get("title") or node.get("node_id") or "?")
    return f"{ASSET_LABELS.get(kind, 'tài sản')} «{name}»"


def _head_of(name: str) -> str:
    """Lấy phần tên riêng của một mục nhân vật trong brief: «Milo — cậu bé…» -> «milo»."""
    return name.split("—")[0].split("-")[0].strip().lower()


def danh_gia(nodes: list, brief: dict | None = None) -> dict:
    """Tính kết quả cổng từ danh sách node và brief. Hàm thuần, không gọi mạng."""
    assets = [n for n in nodes if n.get("type") == "asset"]
    scenes = [n for n in nodes if n.get("type") == "scene"]

    missing_assets = [n for n in assets if not _has_image(n)]
    missing_scenes = [n for n in scenes if not _has_image(n)]

    brief_missing = []
    if brief:
        titles = [str(n.get("title") or "").lower() for n in assets]
        for item in brief.get("characters") or []:
            name = str(item if isinstance(item, str) else item.get("name") or "").strip()
            if not name:
                continue
            head = _head_of(name)
            if head and not any(head in t for t in titles):
                brief_missing.append(name)

    empty = not assets and not scenes
    no_scene = bool(assets) and not scenes

    report = {
        "asset_total": len(assets),
        "scene_total": len(scenes),
        "missing_assets": [
            {"kind": n.get("asset_kind"), "title": n.get("title"), "node_id": n.get("node_id")}
            for n in missing_assets
        ],
        "missing_scenes": [
            {"title": n.get("title"), "node_id": n.get("node_id")} for n in missing_scenes
        ],
        "brief_missing_characters": brief_missing,
        "empty_canvas": empty,
        "no_scene": no_scene,
    }
    report["blocked"] = bool(
        missing_assets or missing_scenes or brief_missing or empty or no_scene
    )
    return report


def _print_report(report: dict, canvas_id: str) -> int:
    if report.get("empty_canvas"):
        print(f"Bảng vẽ {canvas_id}: trống (0 tài sản, 0 cảnh)")
        print("\nCHẶN: bảng vẽ chưa có gì để kiểm — chưa được sinh video.")
        return 1

    print(
        f"Bảng vẽ {canvas_id}: {report['asset_total']} tài sản, "
        f"{report['scene_total']} cảnh"
    )
    if not report["blocked"]:
        print("ĐỦ ẢNH — được sang bước sinh video.")
        return 0

    print("\nCHẶN: chưa đủ ảnh, không được sinh video.")
    if report["missing_assets"]:
        print(f"\nTài sản chưa có ảnh ({len(report['missing_assets'])}):")
        for item in report["missing_assets"]:
            print(f"  - {_label(item)} [{item['node_id']}]")
    if report["missing_scenes"]:
        print(f"\nCảnh chưa có ảnh storyboard ({len(report['missing_scenes'])}):")
        for item in report["missing_scenes"]:
            print(f"  - cảnh «{item['title'] or item['node_id']}» [{item['node_id']}]")
    if report.get("no_scene"):
        print("\nChưa có cảnh nào — kịch bản chưa dựng xong, chưa được sinh video.")
    if report["brief_missing_characters"]:
        print(
            f"\nNhân vật có trong brief nhưng chưa có thẻ tài sản "
            f"({len(report['brief_missing_characters'])}):"
        )
        for name in report["brief_missing_characters"]:
            print(f"  - {name}")
    print("\nSửa: chạy bước 3 (sinh ảnh) rồi kiểm lại.")
    return 1


def _selftest() -> int:
    """Tự kiểm bốn tình huống, không cần máy chủ."""
    anh = {"media_type": "image", "object_key": "sinh-anh/a.png"}
    cases = [
        (
            "phim chỉ 1 nhân vật + 1 cảnh, có 2 ảnh thì qua được",
            [
                {"node_id": "a1", "type": "asset", "asset_kind": "character",
                 "title": "Lena", "media_ref": anh},
                {"node_id": "s1", "type": "scene", "title": "cảnh 1", "media_ref": anh},
            ],
            {"characters": ["Lena — nữ bác sĩ"]},
            False,
        ),
        (
            "thẻ đạo cụ đã lập mà không có ảnh thì chặn",
            [
                {"node_id": "a1", "type": "asset", "asset_kind": "character",
                 "title": "Lena", "media_ref": anh},
                {"node_id": "a2", "type": "asset", "asset_kind": "object",
                 "title": "Lọ thuốc giải"},
                {"node_id": "s1", "type": "scene", "title": "cảnh 1", "media_ref": anh},
            ],
            {"characters": ["Lena — nữ bác sĩ"]},
            True,
        ),
        (
            "tài sản không ảnh thì chặn",
            [
                {"node_id": "a1", "type": "asset", "asset_kind": "character", "title": "Lena"},
                {"node_id": "s1", "type": "scene", "title": "cảnh 1", "media_ref": anh},
            ],
            None,
            True,
        ),
        (
            "cảnh không ảnh storyboard thì chặn",
            [
                {"node_id": "a1", "type": "asset", "asset_kind": "character",
                 "title": "Lena", "media_ref": anh},
                {"node_id": "s1", "type": "scene", "title": "cảnh 1"},
            ],
            None,
            True,
        ),
        (
            "nhân vật trong brief thiếu thẻ tài sản thì chặn",
            [
                {"node_id": "a1", "type": "asset", "asset_kind": "character",
                 "title": "Lena", "media_ref": anh},
                {"node_id": "s1", "type": "scene", "title": "cảnh 1", "media_ref": anh},
            ],
            {"characters": ["Lena — nữ bác sĩ", "Milo — cậu bé"]},
            True,
        ),
        ("bảng vẽ trống thì chặn", [], None, True),
        (
            "có tài sản nhưng chưa có cảnh thì chặn",
            [{"node_id": "a1", "type": "asset", "asset_kind": "character",
              "title": "Lena", "media_ref": anh}],
            None,
            True,
        ),
    ]
    failures = 0
    for name, nodes, brief, want_blocked in cases:
        got = danh_gia(nodes, brief)
        ok = got["blocked"] is want_blocked
        print(f"{'ĐẠT ' if ok else 'HỎNG'} {name}: blocked={got['blocked']}")
        failures += 0 if ok else 1
    print(f"\n{len(cases) - failures}/{len(cases)} tình huống đúng")
    return 1 if failures else 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Cổng kiểm ảnh trước khi sinh video")
    ap.add_argument("--canvas-id", help="mã bảng vẽ cần kiểm")
    ap.add_argument("--brief", help="tệp brief JSON, để kiểm cả nhân vật trong brief")
    ap.add_argument("--mcp", default=MCP_DEFAULT, help="địa chỉ cổng MCP (mặc định 8001)")
    ap.add_argument("--base", default=BASE_DEFAULT, help="địa chỉ máy chủ dữ liệu")
    ap.add_argument("--json", action="store_true", help="in JSON thay cho chữ")
    ap.add_argument("--selftest", action="store_true", help="tự kiểm logic, không cần máy chủ")
    args = ap.parse_args()

    if args.selftest:
        return _selftest()
    if not args.canvas_id:
        ap.error("thiếu --canvas-id")

    state = _rpc(
        args.mcp,
        "canvas_state_get",
        {
            "canvas_id": args.canvas_id,
            "fields": ["nodes.identity", "nodes.generation", "nodes.hierarchy"],
        },
    )
    brief = None
    if args.brief:
        with open(args.brief, "r", encoding="utf-8") as fh:
            brief = json.load(fh)

    report = danh_gia(state.get("nodes") or [], brief)
    report["canvas_id"] = args.canvas_id

    if args.json:
        print(json.dumps(report, ensure_ascii=False))
        return 1 if report["blocked"] else 0
    return _print_report(report, args.canvas_id)


if __name__ == "__main__":
    sys.exit(main())
