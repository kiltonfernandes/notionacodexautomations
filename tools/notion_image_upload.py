import argparse
import mimetypes
import os
import pathlib
import sys

import requests


NOTION_VERSION = "2022-06-28"


def notion_headers(token: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "Notion-Version": NOTION_VERSION,
    }


def create_file_upload(token: str, filename: str, content_type: str) -> str:
    response = requests.post(
        "https://api.notion.com/v1/file_uploads",
        headers={
            **notion_headers(token),
            "Content-Type": "application/json",
        },
        json={
            "filename": filename,
            "content_type": content_type,
        },
        timeout=60,
    )
    response.raise_for_status()
    return response.json()["id"]


def send_file_upload(token: str, upload_id: str, image_path: pathlib.Path, content_type: str) -> None:
    with image_path.open("rb") as image_file:
        response = requests.post(
            f"https://api.notion.com/v1/file_uploads/{upload_id}/send",
            headers=notion_headers(token),
            files={"file": (image_path.name, image_file, content_type)},
            timeout=120,
        )
    response.raise_for_status()


def append_image_block(token: str, page_id: str, upload_id: str, caption: str | None) -> dict:
    image_block = {
        "object": "block",
        "type": "image",
        "image": {
            "type": "file_upload",
            "file_upload": {"id": upload_id},
        },
    }
    if caption:
        image_block["image"]["caption"] = [
            {
                "type": "text",
                "text": {"content": caption},
            }
        ]

    response = requests.patch(
        f"https://api.notion.com/v1/blocks/{page_id}/children",
        headers={
            **notion_headers(token),
            "Content-Type": "application/json",
        },
        json={"children": [image_block]},
        timeout=60,
    )
    response.raise_for_status()
    return response.json()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Upload a local image to Notion and append it as an image block to a page."
    )
    parser.add_argument("--page-id", required=True, help="Target Notion page ID.")
    parser.add_argument("--image", required=True, help="Local image path.")
    parser.add_argument("--caption", default=None, help="Optional image caption.")
    args = parser.parse_args()

    token = os.environ.get("NOTION_TOKEN")
    if not token:
        print("Missing NOTION_TOKEN environment variable.", file=sys.stderr)
        return 2

    image_path = pathlib.Path(args.image).expanduser().resolve()
    if not image_path.exists():
        print(f"Image not found: {image_path}", file=sys.stderr)
        return 2

    content_type = mimetypes.guess_type(image_path.name)[0] or "image/png"
    upload_id = create_file_upload(token, image_path.name, content_type)
    send_file_upload(token, upload_id, image_path, content_type)
    append_image_block(token, args.page_id, upload_id, args.caption)
    print(f"Uploaded {image_path} to Notion page {args.page_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
