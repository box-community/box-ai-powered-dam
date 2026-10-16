# Box AI-powered DAM

A minimal, runnable reference service for a brand digital asset management
(DAM) library in Box. When a product image, logo, or campaign file lands in a
Draft folder, the service extracts brand metadata with
[Box AI Extract](https://developer.box.com/guides/box-ai/ai-tutorials/extract-metadata-structured)
and writes those values back to the file. It then moves files through a
review lifecycle, from Draft to Retired, one folder per stage.

It implements the **webhook > extract > metadata > lifecycle** flow. A Flask
backend receives a `FILE.UPLOADED` webhook (or a simulated curl payload),
calls `POST /2.0/ai/extract_structured` with your Brand Asset metadata
template, and attaches the result with
`POST /2.0/files/:id/metadata/:scope/:template`. A `/lifecycle` endpoint
updates the status and moves the file to the matching stage folder.

The companion repository to the tutorial is:
**[Build an AI-powered DAM system with Box](https://developer.box.com/tutorials/ai-powered-dam)**.

## What it does

| Capability | How |
| --- | --- |
| Detect new uploads in Draft | Box webhooks (`FILE.UPLOADED`) or a local curl simulation |
| Extract brand fields from images | `POST /2.0/ai/extract_structured` with a metadata template |
| Write values back to the file | `POST /2.0/files/:id/metadata/enterprise/:template`, with a JSON-Patch update on `409` |
| Advance the lifecycle | `POST /lifecycle` updates `lifecycleStatus` and moves the file with `PUT /2.0/files/:id` |
| Invite a vendor to Draft only | `invite_vendor.py` creates a Viewer Uploader collaboration with an expiration |
| Publish approved files | `publish_hub.py` creates a Box Hub and adds the Published folder |
| Optional camera EXIF | `exif.py` parses EXIF locally and merges it into the same metadata instance |

## Project layout

```text
box-ai-powered-dam/
├── app.py                # Flask webhook listener and lifecycle endpoint
├── box_client.py         # CCG Service Account auth
├── extract.py            # Box AI structured extract
├── metadata.py           # Attach or update metadata on the file
├── lifecycle.py          # Status-to-folder mapping and move
├── invite_vendor.py      # Invite an external vendor to Draft
├── publish_hub.py        # Create a Box Hub for the Published folder
├── exif.py               # Optional local EXIF parsing
├── make_sample_asset.py  # Generates sample-asset.jpg for testing
├── sample-asset.jpg
├── requirements.txt
├── .env.example
└── .gitignore
```

## Prerequisites

- **Python 3.11+**
- A [free Box developer account](https://account.box.com/signup/developer),
  or a [Box Enterprise account](https://www.box.com/pricing) with **Box AI**
  enabled. Box Hubs is required only for `publish_hub.py`.
- A **Client Credentials Grant (CCG)** Platform App, **authorized** in the
  Admin Console, with these scopes enabled:
  - **Read and write all files and folders stored in Box**
  - **Manage AI**
  - **Manage webhooks**
- A **Brand Asset** metadata template in the Admin Console (see Setup below)
- A **Brand DAM** folder tree in Box, with the app's **Service Account**
  invited as an **Editor** collaborator

## Setup

1. **Clone and enter the project**

   ```bash
   git clone https://github.com/box-community/box-ai-powered-dam.git
   cd box-ai-powered-dam
   ```

2. **Create a virtual environment and install dependencies**

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   python -m pip install -r requirements.txt
   ```

3. **Create the Brand Asset metadata template** (Admin Console > **Metadata**
   > **New**). Name it `Brand Asset` and add these fields:

   | Field name | Type | Description |
   | --- | --- | --- |
   | Asset Type | Dropdown | Options: `Product imagery`, `Logo`, `Marketing material` |
   | Campaign | Text | Campaign or collection name |
   | Product Name | Text | Product, SKU, or offering |
   | Brand | Text | Brand or sub-brand |
   | Lifecycle Status | Dropdown | Options: `Draft`, `Creative review`, `Legal review`, `Approved`, `Published`, `Retired` |
   | Usage Rights | Dropdown | Options: `Internal only`, `External`, `Restricted` |
   | Description | Text | Short visual summary |
   | Capture Date | Date | Camera capture date from EXIF |
   | Camera Make | Text | Camera manufacturer from EXIF |
   | Camera Model | Text | Camera model from EXIF |

   Save, then copy the **template key** shown under Template Name. You need it
   for `.env`. The Lifecycle Status options must match the strings above
   exactly, including the lowercase `review`.

4. **Create the Brand DAM folders** in Box:

   ```text
   Brand DAM/
   ├── Draft/
   ├── Creative Review/
   ├── Legal Review/
   ├── Approved/
   ├── Published/
   └── Retired/
   ```

   Note each folder ID from the URL (`https://app.box.com/folder/123456789` >
   `123456789`).

   **Critical:** invite the app's Service Account as an **Editor** on
   `Brand DAM` so the child folders inherit access. Find the Service Account
   email in Developer Console > your app > **Configuration** > **App Details**
   sidebar > **Service Account ID** (looks like
   `AutomationUser_xxxxx_xxxxxx@boxdevedition.com`). Without this
   collaboration, API calls return `404 Not Found`.

5. **Configure credentials**

   ```bash
   cp .env.example .env
   ```

   Edit `.env` and fill in:

   - `BOX_CLIENT_ID`, `BOX_CLIENT_SECRET`, `BOX_ENTERPRISE_ID` from the
     Developer Console
   - `BOX_METADATA_TEMPLATE_KEY` from step 3
   - The six `*_FOLDER_ID` values from step 4

   > **Never commit `.env`.** It is already in `.gitignore`.

## Run

```bash
python app.py
```

The server starts on `http://127.0.0.1:5000` (with auto-reload enabled).

> Do not use `debug=True` in production.

## Try it

You can exercise the whole pipeline locally without a public URL or a real
webhook. You need **two terminals**: one running the Flask server, one sending
requests.

1. **Upload `sample-asset.jpg`** to your Draft folder in Box (regenerate any
   time with `python make_sample_asset.py`). Note the **file ID** from the
   file URL (`https://app.box.com/file/123456789` > `123456789`). Use the file
   ID, not the folder ID.

2. **Start the server** (terminal 1):

   ```bash
   source .venv/bin/activate
   python app.py
   ```

3. **Simulate a webhook** (terminal 2, replace `<FILE_ID>`):

   ```bash
   curl -X POST http://127.0.0.1:5000/webhook \
     -H "Content-Type: application/json" \
     -d '{
       "trigger": "FILE.UPLOADED",
       "source": {
         "id": "<FILE_ID>",
         "name": "sample-asset.jpg"
       }
     }'
   ```

   Terminal 1 prints the extracted fields and confirms metadata was applied.
   Open the file in Box > **Metadata** tab to verify. Running the same request
   again updates the existing instance instead of failing.

4. **Advance the file** through the lifecycle:

   ```bash
   curl -X POST http://127.0.0.1:5000/lifecycle \
     -H "Content-Type: application/json" \
     -d '{
       "file_id": "<FILE_ID>",
       "lifecycle_status": "Published"
     }'
   ```

   The file moves to the **Published** folder and `lifecycleStatus` becomes
   `Published`. An unknown status returns `400` with the allowed values.

### Invite a vendor to Draft

```bash
python invite_vendor.py vendor@example.com
```

The vendor gets **Viewer Uploader** access to Draft only, expiring in 30 days.
`expires_at` requires the **Automatically remove invited collaborators: Allow
folder owners to extend the expiry date** setting in Admin Console >
**Enterprise Settings**. If that setting is off, remove `expires_at` from
`invite_vendor.py`.

### Publish to a Box Hub

```bash
python publish_hub.py
```

Run this **once**. It creates a hub named `Brand asset library` and adds the
Published folder, so files you later move to Published appear there. Running
it again creates another hub. The Service Account owns the hub, so collaborate
your own user onto it to see it under **Hubs** in the Box web app.

### Optional: camera EXIF

Box AI Extract reads visible content, not camera EXIF. To fill `cameraMake`,
`cameraModel`, and `captureDate` from EXIF, uncomment the `enrich_exif` block
in `handle_webhook` in `app.py`. `sample-asset.jpg` includes EXIF
(`Canon`, `Canon EOS R6`, `2026-09-12`) so you can confirm the merge.

### Register a real webhook (production)

For automatic processing when files arrive, expose the app over HTTPS (for
example with a tunnel) and register a webhook on the Draft folder:

```bash
curl -X POST https://api.box.com/2.0/webhooks \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "target": {
      "id": "<DRAFT_FOLDER_ID>",
      "type": "folder"
    },
    "address": "<webhook_url>/webhook",
    "triggers": ["FILE.UPLOADED"]
  }'
```

In production, [verify webhook signatures](https://developer.box.com/guides/webhooks/v2/signatures-v2)
before processing.

## How it works

1. An image lands in Draft (or you POST a simulated webhook).
2. `extract.py` calls Box AI with your Brand Asset metadata template, so
   product names, campaign lettering, and brand marks come back as typed
   fields.
3. `metadata.py` writes those values, plus `lifecycleStatus: Draft`, onto the
   file. If an instance already exists, it sends a JSON-Patch `add` update.
4. Reviewers call `POST /lifecycle` after each decision. `lifecycle.py`
   updates the status and moves the file to the matching folder.
5. `publish_hub.py` exposes the Published folder through a Box Hub, which
   inherits permissions from the source files.

## Security notes

- Keep the client secret, enterprise ID, and access tokens server-side.
- Collaborate external vendors on Draft only. Do not give them access to
  `Brand DAM` or Published masters.
- Add only the Published folder to a Hub.
- Verify webhook signatures in production.
- Box expects a `2xx` within 30 seconds and retries otherwise. In production,
  return `200` right away and run extraction from a queue.

## Troubleshooting

| Symptom | Fix |
| --- | --- |
| `unauthorized_client` | Authorize the app in the Admin Console (Developer Console > Authorization > Review and Submit). |
| `invalid_client` | Check `BOX_CLIENT_ID` / `BOX_CLIENT_SECRET` / `BOX_ENTERPRISE_ID` in `.env`. |
| `404 Not Found` | Invite the Service Account as **Editor** on `Brand DAM`. |
| `metadata_template must have both scope and template_key` | Set `BOX_METADATA_TEMPLATE_KEY` in `.env` to the key from the Admin Console. |
| `Unknown lifecycle status` | Use one of the six dropdown values exactly, for example `Legal review`, not `legal review`. |
| `ModuleNotFoundError` | Activate the venv: `source .venv/bin/activate`. |
| Extraction fails / AI errors | Confirm the **Manage AI** scope is enabled and the app was re-authorized after enabling it. Box AI must be available on the account. |
| `publish_hub.py` fails to create the hub | Box Hubs must be enabled for the Service Account. Otherwise authenticate as a managed user who can create hubs. |

## License

[MIT](./LICENSE)
