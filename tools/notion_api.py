from __future__ import annotations

import mimetypes
import pathlib
from dataclasses import dataclass
from typing import Any

import requests


NOTION_VERSION = "2022-06-28"


@dataclass
class NotionClient:
    token: str

    def headers(self, json: bool = True) -> dict[str, str]:
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Notion-Version": NOTION_VERSION,
        }
        if json:
            headers["Content-Type"] = "application/json"
        return headers

    def request(self, method: str, url: str, **kwargs: Any) -> dict[str, Any]:
        response = requests.request(method, url, headers=self.headers(kwargs.pop("json_headers", True)), timeout=90, **kwargs)
        response.raise_for_status()
        return response.json() if response.content else {}

    def get_children(self, block_id: str) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        cursor = None
        while True:
            params = {"page_size": 100}
            if cursor:
                params["start_cursor"] = cursor
            data = self.request("GET", f"https://api.notion.com/v1/blocks/{block_id}/children", params=params)
            results.extend(data.get("results", []))
            if not data.get("has_more"):
                return results
            cursor = data.get("next_cursor")

    def find_child_page(self, parent_id: str, title: str) -> str | None:
        for child in self.get_children(parent_id):
            if child.get("type") != "child_page":
                continue
            if child.get("child_page", {}).get("title", "").strip() == title:
                return child["id"]
        return None

    def create_child_page(self, parent_id: str, title: str, children: list[dict[str, Any]] | None = None) -> str:
        payload: dict[str, Any] = {
            "parent": {"type": "page_id", "page_id": parent_id},
            "properties": {"title": {"title": [{"text": {"content": title}}]}},
        }
        if children:
            payload["children"] = children[:100]
        data = self.request("POST", "https://api.notion.com/v1/pages", json=payload)
        return data["id"]

    def ensure_path(self, root_id: str, titles: list[str]) -> str:
        parent = root_id
        for title in titles:
            existing = self.find_child_page(parent, title)
            parent = existing or self.create_child_page(parent, title)
        return parent

    def append_blocks(self, page_id: str, blocks: list[dict[str, Any]]) -> None:
        for start in range(0, len(blocks), 100):
            chunk = blocks[start : start + 100]
            self.request(
                "PATCH",
                f"https://api.notion.com/v1/blocks/{page_id}/children",
                json={"children": chunk},
            )

    def archive_page(self, page_id: str) -> None:
        self.request("PATCH", f"https://api.notion.com/v1/pages/{page_id}", json={"archived": True})

    def upload_image_block(self, page_id: str, image_path: str, caption: str | None = None) -> None:
        path = pathlib.Path(image_path).resolve()
        content_type = mimetypes.guess_type(path.name)[0] or "image/png"
        upload = self.request(
            "POST",
            "https://api.notion.com/v1/file_uploads",
            json={"filename": path.name, "content_type": content_type},
        )
        upload_id = upload["id"]
        with path.open("rb") as image_file:
            response = requests.post(
                f"https://api.notion.com/v1/file_uploads/{upload_id}/send",
                headers=self.headers(json=False),
                files={"file": (path.name, image_file, content_type)},
                timeout=120,
            )
        response.raise_for_status()
        image: dict[str, Any] = {"type": "file_upload", "file_upload": {"id": upload_id}}
        if caption:
            image["caption"] = [{"type": "text", "text": {"content": caption[:2000]}}]
        self.append_blocks(page_id, [{"object": "block", "type": "image", "image": image}])


def rich_text(text: str, bold: bool = False, italic: bool = False) -> list[dict[str, Any]]:
    return [{"type": "text", "text": {"content": text[:2000]}, "annotations": {"bold": bold, "italic": italic}}]


def paragraph(text: str) -> dict[str, Any]:
    return {"object": "block", "type": "paragraph", "paragraph": {"rich_text": rich_text(text)}}


def heading(level: int, text: str) -> dict[str, Any]:
    notion_level = min(max(level, 1), 3)
    key = f"heading_{notion_level}"
    return {"object": "block", "type": key, key: {"rich_text": rich_text(text, bold=True)}}


def quote(text: str) -> dict[str, Any]:
    return {"object": "block", "type": "quote", "quote": {"rich_text": rich_text(text)}}


def divider() -> dict[str, Any]:
    return {"object": "block", "type": "divider", "divider": {}}


def code_block(text: str, language: str = "plain text") -> dict[str, Any]:
    return {"object": "block", "type": "code", "code": {"language": language, "rich_text": rich_text(text[:2000])}}


def bulleted(text: str) -> dict[str, Any]:
    return {"object": "block", "type": "bulleted_list_item", "bulleted_list_item": {"rich_text": rich_text(text)}}


def numbered(text: str) -> dict[str, Any]:
    return {"object": "block", "type": "numbered_list_item", "numbered_list_item": {"rich_text": rich_text(text)}}


def markdown_to_blocks(markdown: str, max_quotes: int = 3) -> list[dict[str, Any]]:
    blocks: list[dict[str, Any]] = []
    quote_count = 0
    in_code = False
    code_lines: list[str] = []
    code_lang = "plain text"

    for raw_line in markdown.splitlines():
        line = raw_line.rstrip()
        if line.startswith("```"):
            if in_code:
                blocks.append(code_block("\n".join(code_lines), code_lang or "plain text"))
                code_lines = []
                in_code = False
            else:
                in_code = True
                code_lang = line.strip("`").strip() or "plain text"
            continue
        if in_code:
            code_lines.append(line)
            continue
        if not line.strip():
            continue
        if line.strip() == "---":
            blocks.append(divider())
            continue
        if line.startswith("#### "):
            blocks.append(heading(3, line[5:]))
            continue
        if line.startswith("### "):
            blocks.append(heading(3, line[4:]))
            continue
        if line.startswith("## "):
            blocks.append(heading(2, line[3:]))
            continue
        if line.startswith("# "):
            blocks.append(heading(1, line[2:]))
            continue
        if line.startswith("> "):
            if quote_count < max_quotes:
                blocks.append(quote(line[2:]))
                quote_count += 1
            else:
                blocks.append(paragraph(f"Referência: {line[2:]}"))
            continue
        if line.startswith("- "):
            blocks.append(bulleted(line[2:]))
            continue
        if len(line) > 3 and line[0].isdigit() and ". " in line[:5]:
            blocks.append(numbered(line.split(". ", 1)[1]))
            continue
        blocks.append(paragraph(line.replace("**", "").replace("*", "")))

    return blocks
