# Notion + Codex Automations

Cloud automations for LDS study, teaching preparation, family study, and Notion publishing.

This project runs scheduled GitHub Actions that read weekly content from ChurchofJesusChrist.org, generate structured study/lesson pages, create infographics with OpenAI, and publish everything to Notion through the official Notion API.

The main goal is simple: keep the weekly and daily spiritual-study workflows organized, beautiful, and automatic, without depending on a local PC being turned on.

---

## What This Project Does

This repository powers five automation families:

| Automation | Schedule Sao Paulo | Output | Image Upload |
|---|---:|---|---|
| `daily-cfm` | Daily 05:00 | Daily Come Follow Me study page | Yes |
| `seminary` | Monday 21:00 | Two Seminary class pages, Wednesday and Friday | Yes |
| `mas` | Monday 23:00 | Biweekly MAS lesson page | No |
| `fhe` | Tuesday 14:00 | Family Home Evening page | No |
| `sunday-school` | Thursday 19:00 | Biweekly Sunday School lesson page | Yes |

All automations use Notion page hierarchies such as:

```text
Root Page
+-- 2026
    +-- Q2
        +-- Maio
            +-- 4 a 10 de maio
                +-- Generated pages
```

For biweekly pages, the final level is a two-week interval:

```text
Root Page
+-- 2026
    +-- Q2
        +-- Maio
            +-- 4 a 17 de maio
```

---

## Repository Structure

```text
.github/workflows/cloud-automations.yml
  GitHub Actions schedules and manual workflow dispatcher.

tools/lds_automation_runner.py
  Main runner. Finds the LDS lesson, generates content and images, creates Notion pages.

tools/notion_api.py
  Lightweight Notion API client and Markdown-to-Notion block helpers.

tools/notion_image_upload.py
  Utility script for uploading a local image to Notion as an image block.

tools/notion_archive_pages.py
  Utility script for archiving Notion test pages by ID.

requirements.txt
  Python dependencies for GitHub Actions.
```

---

## Required Accounts And Tokens

### Notion

The Notion integration is managed here:

[https://www.notion.com/my-integrations](https://www.notion.com/my-integrations)

Current integration name:

```text
Codex Publisher
```

Recommended capabilities:

- Read content
- Insert content
- Update content

Webhooks are not required because these automations run on schedules.

### OpenAI

The workflows need an OpenAI API key to generate:

- lesson text;
- study pages;
- infographics.

---

## GitHub Setup

Open this repository:

[https://github.com/kiltonfernandes/notionacodexautomations](https://github.com/kiltonfernandes/notionacodexautomations)

Go to:

```text
Settings -> Secrets and variables -> Actions
```

Direct link:

[Repository Actions Secrets](https://github.com/kiltonfernandes/notionacodexautomations/settings/secrets/actions)

Create these repository secrets:

```text
NOTION_TOKEN
OPENAI_API_KEY
```

Optional repository variables:

```text
OPENAI_MODEL=gpt-5.2
OPENAI_IMAGE_MODEL=gpt-image-2
```

If the variables are not set, the workflow uses those defaults.

---

## Notion Access Setup

In Notion, the integration must have access to the top-level page containing the LDS pages.

Recommended approach:

1. Open the top-level Notion page that contains all target pages.
2. Click `...` or `Share`.
3. Invite/add the connection `Codex Publisher`.
4. Confirm it has access to child pages.

The current automation roots are:

| Automation | Root |
|---|---|
| FHE | `Family home evening` |
| MAS | `Professora do MAS` |
| Sunday School | `Sunday School Teacher` |
| Seminary | `Professora Seminario` |
| Daily CFM | `Come Follow Me` |

---

## Schedule Map

GitHub Actions cron runs in UTC. Sao Paulo is UTC-03.

| Automation | Sao Paulo Time | GitHub Cron |
|---|---:|---|
| `daily-cfm` | Daily 05:00 | `0 8 * * *` |
| `seminary` | Monday 21:00 | `0 0 * * 2` |
| `mas` | Monday 23:00 | `0 2 * * 2` |
| `fhe` | Tuesday 14:00 | `0 17 * * 2` |
| `sunday-school` | Thursday 19:00 | `0 22 * * 4` |

Important: GitHub Actions may delay scheduled runs by a few minutes during busy periods.

---

## Manual Run

Use manual dispatch for testing.

1. Open [Actions](https://github.com/kiltonfernandes/notionacodexautomations/actions).
2. Select `Cloud Notion Automations`.
3. Click `Run workflow`.
4. Choose one automation:
   - `daily-cfm`
   - `seminary`
   - `mas`
   - `fhe`
   - `sunday-school`
5. Optional: provide a date override, for example:

```text
2026-05-04
```

The date override is useful for testing a specific lesson week.

---

## Local Development

From the repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Set local environment variables:

```powershell
$env:NOTION_TOKEN="your_notion_token"
$env:OPENAI_API_KEY="your_openai_key"
```

Run a dry test:

```powershell
python tools\lds_automation_runner.py --automation daily-cfm --date 2026-05-04 --dry-run
```

Run a real local test:

```powershell
python tools\lds_automation_runner.py --automation daily-cfm --date 2026-05-04
```

Archive test pages:

```powershell
python tools\notion_archive_pages.py PAGE_ID_1 PAGE_ID_2
```

Upload an image to a page:

```powershell
python tools\notion_image_upload.py --page-id PAGE_ID --image "C:\path\image.png" --caption "Infográfico"
```

---

## Formatting Rules

All generated pages should follow these rules:

- Use H1, H2, H3, and H4 style hierarchy where appropriate.
- Use short paragraphs.
- Use **bold** for key principles.
- Use *italic* for gentle emphasis or invitations.
- Use simulated callouts:
  - `💡 Insight`
  - `✅ Action`
  - `⚠️ Attention`
  - `📌 Key takeaway`
  - `🟨 Reflection`
- Use no more than 3 quote blocks per page.
- Prefer faithful paraphrase plus references when more textual grounding is needed.
- Keep emoji usage useful and light.

---

## Image Upload Strategy

The Notion MCP connector did not expose local file upload.

This project uses the official Notion File Upload API instead:

1. Generate a local PNG infographic.
2. Create a Notion file upload.
3. Send the file bytes to Notion.
4. Append an image block to the target page.

The reusable script is:

```powershell
python tools\notion_image_upload.py --page-id PAGE_ID --image "C:\path\image.png" --caption "Infográfico"
```

In GitHub Actions, this happens in the cloud using `NOTION_TOKEN`.

---

## Operational Notes

- GitHub Actions allows the automations to run even when the local PC is off.
- Secrets should live only in GitHub Secrets or local environment variables.
- Do not commit tokens or API keys to the repository.
- If the Notion token is exposed, refresh it at [https://www.notion.com/my-integrations](https://www.notion.com/my-integrations).
- If pages are duplicated, first check whether the local Codex App automations are still active. Once GitHub Actions is validated, local duplicates should be paused.

---

## Changelog

### 2026-05-04

- Created dedicated repository `notionacodexautomations`.
- Migrated automation assets out of the unrelated `ProtoFlow` project.
- Added GitHub Actions workflow for cloud execution.
- Added schedule coverage for:
  - Daily Come Follow Me.
  - Seminary.
  - MAS.
  - Family Home Evening.
  - Sunday School.
- Added `workflow_dispatch` manual runner with automation selector and optional date override.
- Added `tools/lds_automation_runner.py` as the main cloud runner.
- Added `tools/notion_api.py` for Notion page creation, hierarchy lookup, block append, archive, and image upload.
- Added `tools/notion_image_upload.py` for standalone image upload to Notion.
- Added `tools/notion_archive_pages.py` for archiving test pages.
- Added official Notion File Upload API path for image blocks.
- Added max-3 quote block rule across generated pages.
- Added consistent Notion formatting rules:
  - H1/H2/H3/H4.
  - short paragraphs.
  - callout simulations.
  - bold and italic guidance.
- Added `.gitignore` to prevent committing Python cache, generated images, virtualenvs, and `.env`.
- Removed generated Python cache files from the repository.
- Added this README as project landing page, setup guide, operations guide, and changelog.

### Earlier Context

- Built initial local Codex App automations for:
  - Family Home Evening.
  - MAS lessons.
  - Sunday School lessons with infographics.
  - Seminary lessons with two weekly pages.
  - Daily Come Follow Me study pages.
- Validated Notion API token locally with bot name `Codex Publisher`.
- Archived non-FHE test pages after setting up the Notion token locally.
