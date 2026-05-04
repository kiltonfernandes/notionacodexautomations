from __future__ import annotations

import argparse
import base64
import datetime as dt
import os
import pathlib
import re
from dataclasses import dataclass

import requests
from bs4 import BeautifulSoup
from openai import OpenAI

from notion_api import NotionClient, markdown_to_blocks


TOC_URL = "https://www.churchofjesuschrist.org/study/manual/come-follow-me-for-home-and-church-old-testament-2026?lang=por"


@dataclass
class Automation:
    key: str
    root_id: str
    schedule_label: str
    prompt: str
    needs_image: bool = False
    week_offset_days: int = 0


AUTOMATIONS = {
    "fhe": Automation(
        key="fhe",
        root_id="fe3751fcbdd64ab5a63a204937b7de38",
        schedule_label="family-home-evening",
        week_offset_days=7,
        prompt=(
            "Crie uma Family Home Evening em pt-BR para Amanda, Kilton, Aurora de 8 anos e Augusto de 1 ano. "
            "Use a lição da semana seguinte, H1/H2/H3/H4, perguntas com respostas possíveis, atividade simples, "
            "callouts simulados e no máximo 3 quote blocks."
        ),
    ),
    "mas": Automation(
        key="mas",
        root_id="31a195bb0be880eaa37ffa97bd1d188d",
        schedule_label="mas",
        prompt=(
            "Crie uma aula para jovens solteiros 18-30 em pt-BR, página quinzenal, formato Notion legível com "
            "H1/H2/H3/H4, FAQ, perguntas abertas, callouts simulados e no máximo 3 quote blocks."
        ),
    ),
    "daily-cfm": Automation(
        key="daily-cfm",
        root_id="f2734aa2347a42bc9b5b19f32e03144c",
        schedule_label="diario",
        needs_image=True,
        prompt=(
            "Crie uma página diária de estudo Come Follow Me em pt-BR, 500-1000 palavras, "
            "com H1/H2/H3, no máximo 3 quote blocks, callouts simulados, tabela, próximos passos, "
            "e foco inédito do dia baseado na lição semanal."
        ),
    ),
    "sunday-school": Automation(
        key="sunday-school",
        root_id="355195bb0be88017af23c31334ab856a",
        schedule_label="sunday-school",
        needs_image=True,
        prompt=(
            "Crie uma aula para jovens solteiros 18-30 em pt-BR, formato Notion legível com H1/H2/H3/H4, "
            "FAQ, perguntas abertas, callouts simulados e no máximo 3 quote blocks."
        ),
    ),
    "seminary": Automation(
        key="seminary",
        root_id="31a195bb0be88051867fece209c28997",
        schedule_label="seminario",
        needs_image=True,
        prompt=(
            "Crie duas aulas de Seminário para adolescentes 14-18, quarta e sexta, em pt-BR. "
            "Cada aula deve ter H1/H2/H3/H4, discussão, atividade, fechamento, callouts e no máximo 3 quote blocks."
        ),
    ),
}


def parse_date(value: str | None) -> dt.date:
    if value:
        return dt.date.fromisoformat(value)
    return dt.datetime.now(dt.timezone.utc).astimezone().date()


def pt_month(month: int) -> str:
    return [
        "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
        "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro",
    ][month - 1]


def quarter(month: int) -> str:
    return f"Q{((month - 1) // 3) + 1}"


def current_week(date: dt.date) -> tuple[dt.date, dt.date]:
    start = date - dt.timedelta(days=date.weekday())
    return start, start + dt.timedelta(days=6)


def week_title(start: dt.date, end: dt.date) -> str:
    if start.month == end.month:
        return f"{start.day} a {end.day} de {pt_month(start.month).lower()}"
    return f"{start.day} de {pt_month(start.month).lower()} a {end.day} de {pt_month(end.month).lower()}"


def find_lesson_url(date: dt.date) -> str:
    html = requests.get(TOC_URL, timeout=60).text
    soup = BeautifulSoup(html, "html.parser")
    text_month = {
        1: "janeiro", 2: "fevereiro", 3: "março", 4: "abril", 5: "maio", 6: "junho",
        7: "julho", 8: "agosto", 9: "setembro", 10: "outubro", 11: "novembro", 12: "dezembro",
    }
    start, end = current_week(date)
    candidates = [
        f"{start.day} a {end.day} de {text_month[start.month]}",
        f"{start.day} de {text_month[start.month]} a {end.day} de {text_month[end.month]}",
    ]
    for link in soup.find_all("a", href=True):
        label = " ".join(link.get_text(" ", strip=True).lower().split())
        if any(candidate in label for candidate in candidates):
            href = link["href"]
            if href.startswith("/"):
                return f"https://www.churchofjesuschrist.org{href}"
            return href
    # Conservative fallback for current May 4-10 test week.
    return "https://www.churchofjesuschrist.org/study/manual/come-follow-me-for-home-and-church-old-testament-2026/19?lang=por"


def fetch_lesson(url: str) -> str:
    html = requests.get(url, timeout=60).text
    soup = BeautifulSoup(html, "html.parser")
    main = soup.find("main") or soup
    for element in main.select("nav, footer, script, style"):
        element.decompose()
    text = "\n".join(line.strip() for line in main.get_text("\n").splitlines() if line.strip())
    return text[:30000]


def create_content(client: OpenAI, automation: Automation, lesson_url: str, lesson_text: str, today: dt.date) -> str:
    response = client.responses.create(
        model=os.environ.get("OPENAI_MODEL", "gpt-5.2"),
        input=[
            {
                "role": "system",
                "content": "Você escreve conteúdo em pt-BR para Notion, com Markdown limpo e sem mais de 3 quote blocks.",
            },
            {
                "role": "user",
                "content": (
                    f"Data: {today.isoformat()}\nFonte: {lesson_url}\n\n"
                    f"Instrução da automação: {automation.prompt}\n\n"
                    "Use no máximo 3 linhas iniciadas com > no documento inteiro. "
                    "Use callouts simulados, H1/H2/H3/H4, parágrafos curtos e referências claras.\n\n"
                    f"Texto da lição LDS.org:\n{lesson_text}"
                ),
            },
        ],
    )
    return response.output_text


def create_image(client: OpenAI, automation: Automation, lesson_text: str, today: dt.date, out_dir: pathlib.Path) -> str:
    prompt = (
        "Gere um infográfico 9:16 portrait em pt-BR, mobile-first, baseado diretamente nesta lição LDS.org. "
        "Estilo lineart editorial, denso e organizado, fundo branco/quase branco, 3-5 cores, títulos curtos, "
        "bullets compactos, sem texto corrido, sem inventar dados. "
        f"Automação: {automation.key}. Data: {today.isoformat()}. Conteúdo: {lesson_text[:6000]}"
    )
    result = client.images.generate(
        model=os.environ.get("OPENAI_IMAGE_MODEL", "gpt-image-2"),
        prompt=prompt,
        size="1024x1792",
    )
    image_b64 = result.data[0].b64_json
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{automation.key}-{today.isoformat()}.png"
    path.write_bytes(base64.b64decode(image_b64))
    return str(path)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--automation", required=True, choices=AUTOMATIONS.keys())
    parser.add_argument("--date")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    token = os.environ["NOTION_TOKEN"]
    openai_client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    notion = NotionClient(token)
    automation = AUTOMATIONS[args.automation]
    today = parse_date(args.date)
    lesson_date = today + dt.timedelta(days=automation.week_offset_days)
    start, end = current_week(lesson_date)
    lesson_url = find_lesson_url(lesson_date)
    lesson_text = fetch_lesson(lesson_url)

    content = create_content(openai_client, automation, lesson_url, lesson_text, today)
    title_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
    page_title = title_match.group(1)[:80] if title_match else f"{automation.key} - {today.strftime('%d.%m')}"

    parent = notion.ensure_path(
        automation.root_id,
        [str(start.year), quarter(start.month), pt_month(start.month), week_title(start, end)],
    )
    if args.dry_run:
        print(content[:2000])
        return 0

    page_id = notion.create_child_page(parent, page_title, markdown_to_blocks(content, max_quotes=3))
    if automation.needs_image:
        image_path = create_image(openai_client, automation, lesson_text, today, pathlib.Path("generated"))
        notion.upload_image_block(page_id, image_path, f"Infográfico - {today.strftime('%d.%m')}")
    print(f"Created Notion page: {page_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
