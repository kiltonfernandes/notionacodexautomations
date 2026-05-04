import argparse
import os
import sys

import requests


NOTION_VERSION = "2022-06-28"


def archive_page(token: str, page_id: str) -> None:
    response = requests.patch(
        f"https://api.notion.com/v1/pages/{page_id}",
        headers={
            "Authorization": f"Bearer {token}",
            "Notion-Version": NOTION_VERSION,
            "Content-Type": "application/json",
        },
        json={"archived": True},
        timeout=60,
    )
    response.raise_for_status()


def main() -> int:
    parser = argparse.ArgumentParser(description="Archive one or more Notion pages by ID.")
    parser.add_argument("page_ids", nargs="+", help="Notion page IDs to archive.")
    args = parser.parse_args()

    token = os.environ.get("NOTION_TOKEN")
    if not token:
        print("Missing NOTION_TOKEN environment variable.", file=sys.stderr)
        return 2

    for page_id in args.page_ids:
        archive_page(token, page_id)
        print(f"Archived {page_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
