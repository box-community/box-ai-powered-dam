import json

from dotenv import load_dotenv
from flask import Flask, jsonify, request

from box_client import get_box_client
from extract import extract_brand_fields
from lifecycle import STATUS_FOLDER_ENV, advance_lifecycle
from metadata import apply_metadata

load_dotenv()
app = Flask(__name__)

IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".tif", ".tiff", ".webp")


@app.route("/")
def index():
    """Friendly landing page with usage hints."""
    return jsonify(
        {
            "service": "Box AI-powered DAM",
            "endpoints": {
                "POST /webhook": (
                    "Receive FILE.UPLOADED webhook payloads for the Draft "
                    "folder, extract brand fields with Box AI, and write metadata"
                ),
                "POST /lifecycle": (
                    "Set lifecycleStatus and move the file to the matching "
                    "stage folder"
                ),
                "GET /health": "Liveness check",
            },
            "lifecycle_statuses": list(STATUS_FOLDER_ENV),
        }
    )


@app.route("/health")
def health():
    return jsonify({"status": "ok"}), 200


@app.route("/webhook", methods=["POST"])
def handle_webhook():
    """Handle Box FILE.UPLOADED webhooks for the Draft folder.

    In production, verify webhook signatures and respond before running
    extraction. Box retries deliveries that do not get a 2xx within 30
    seconds. See:
    https://developer.box.com/guides/webhooks/v2/signatures-v2
    """
    payload = request.get_json()

    if not payload or payload.get("trigger") != "FILE.UPLOADED":
        return jsonify({"status": "ignored"}), 200

    file_id = payload["source"]["id"]
    file_name = payload["source"]["name"]

    if not file_name.lower().endswith(IMAGE_EXTENSIONS):
        return jsonify({"status": "skipped, not a supported image"}), 200

    client = get_box_client()
    extracted = extract_brand_fields(client, file_id)
    extracted["lifecycleStatus"] = "Draft"

    # Optional: merge camera EXIF parsed locally. Requires Pillow.
    # from exif import enrich_exif
    # try:
    #     extracted.update(enrich_exif(client, file_id) or {})
    # except Exception:
    #     pass

    print(f"Extracted from {file_name}: {json.dumps(extracted, indent=2)}")

    apply_metadata(client, file_id, extracted)
    print(f"Metadata applied to file {file_id}")

    return jsonify({"status": "processed", "file_id": file_id}), 200


@app.route("/lifecycle", methods=["POST"])
def handle_lifecycle():
    body = request.get_json()
    file_id = body["file_id"]
    lifecycle_status = body["lifecycle_status"]

    client = get_box_client()
    try:
        result = advance_lifecycle(client, file_id, lifecycle_status)
    except ValueError as error:
        return jsonify({"error": str(error)}), 400
    return jsonify(result), 200


if __name__ == "__main__":
    app.run(port=5000, debug=True)
