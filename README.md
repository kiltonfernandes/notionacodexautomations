# Cloud Notion Automations

This repository includes a GitHub Actions workflow that can run the LDS/Notion automations in the cloud, without depending on a local PC being on.

## Required GitHub Secrets

Open the repository on GitHub:

`https://github.com/kiltonfernandes/ProtoFlow`

Then go to:

`Settings -> Secrets and variables -> Actions -> New repository secret`

Create these secrets:

- `NOTION_TOKEN`: the internal connection token from https://www.notion.com/my-integrations
- `OPENAI_API_KEY`: an OpenAI API key used to generate lesson text and infographics

Optional repository variables:

- `OPENAI_MODEL`: defaults to `gpt-5.2`
- `OPENAI_IMAGE_MODEL`: defaults to `gpt-image-2`

## Notion Access

In the Notion integration portal, grant the `Codex Publisher` connection access to the top-level page that contains the LDS pages.

Recommended capabilities:

- Read content
- Insert content
- Update content

No webhooks are required for the scheduled workflows.

## Schedules

GitHub cron runs in UTC. The workflow maps these to America/Sao_Paulo:

- `daily-cfm`: every day at 05:00 Sao_Paulo
- `seminary`: Monday at 21:00 Sao_Paulo
- `mas`: Monday at 23:00 Sao_Paulo
- `fhe`: Tuesday at 14:00 Sao_Paulo
- `sunday-school`: Thursday at 19:00 Sao_Paulo

## Manual Test

After pushing this workflow to GitHub:

1. Open `Actions`.
2. Select `Cloud Notion Automations`.
3. Click `Run workflow`.
4. Choose an automation, for example `daily-cfm`.
5. Optionally provide a date override like `2026-05-04`.

The workflow will create a Notion page and, for image-enabled automations, upload the infographic through the official Notion File Upload API.
