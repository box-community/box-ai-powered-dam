"""Live end-to-end test against a real Box enterprise.

Runs the tutorial flow through the Flask routes: upload sample-asset.jpg to the
Draft folder, post a simulated FILE.UPLOADED webhook so Box AI fills the Brand
Asset template, then advance the asset to Creative review with /lifecycle and
check it moved. Also checks the optional EXIF step against the sample's known
camera values.

Uploads under a unique name and deletes the file at the end, wherever the
lifecycle step moved it. Reads the same variables as .env.example, from the
environment or a local .env.
"""

import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

from box_sdk_gen import (  # noqa: E402
    GetFileMetadataByIdScope,
    UploadFileAttributes,
    UploadFileAttributesParentField,
)

from app import app  # noqa: E402
from box_client import get_box_client  # noqa: E402
from exif import enrich_exif  # noqa: E402

REQUIRED_ENV = [
    "BOX_CLIENT_ID",
    "BOX_CLIENT_SECRET",
    "BOX_ENTERPRISE_ID",
    "BOX_METADATA_TEMPLATE_KEY",
    "DRAFT_FOLDER_ID",
    "CREATIVE_REVIEW_FOLDER_ID",
    "LEGAL_REVIEW_FOLDER_ID",
    "APPROVED_FOLDER_ID",
    "PUBLISHED_FOLDER_ID",
    "RETIRED_FOLDER_ID",
]


def read_metadata(client, file_id: str) -> dict:
    metadata = client.file_metadata.get_file_metadata_by_id(
        file_id,
        GetFileMetadataByIdScope.ENTERPRISE,
        os.getenv("BOX_METADATA_TEMPLATE_KEY"),
    )
    return metadata.extra_data or {}


def check_extraction(test_client, client, file_id: str, file_name: str) -> None:
    response = test_client.post(
        "/webhook",
        json={"trigger": "FILE.UPLOADED", "source": {"id": file_id, "name": file_name}},
    )
    assert response.status_code == 200, f"/webhook returned {response.status_code}"
    assert response.get_json() == {"status": "processed", "file_id": file_id}, response.get_json()

    fields = read_metadata(client, file_id)
    print(f"Metadata after extraction: {fields}")
    assert fields.get("lifecycleStatus") == "Draft", "lifecycleStatus should start as Draft"
    assert "northwind" in str(fields.get("brand", "")).lower(), "brand should mention Northwind"
    assert "trail runner" in str(fields.get("productName", "")).lower(), "productName mismatch"


def check_lifecycle(test_client, client, file_id: str) -> None:
    response = test_client.post(
        "/lifecycle", json={"file_id": file_id, "lifecycle_status": "Creative review"}
    )
    assert response.status_code == 200, f"/lifecycle returned {response.status_code}"

    parent_id = client.files.get_file_by_id(file_id).parent.id
    assert parent_id == os.getenv("CREATIVE_REVIEW_FOLDER_ID"), "File was not moved"
    assert read_metadata(client, file_id).get("lifecycleStatus") == "Creative review"
    print("Moved to Creative review and updated lifecycleStatus")

    rejected = test_client.post(
        "/lifecycle", json={"file_id": file_id, "lifecycle_status": "Shipped"}
    )
    assert rejected.status_code == 400, f"Unknown status returned {rejected.status_code}"


def check_exif(client, file_id: str) -> None:
    enrichment = enrich_exif(client, file_id)
    print(f"EXIF enrichment: {enrichment}")
    assert enrichment == {
        "cameraMake": "Canon",
        "cameraModel": "Canon EOS R6",
        "captureDate": "2026-09-12T00:00:00Z",
    }, "EXIF values do not match make_sample_asset.py"


def main() -> None:
    missing = [name for name in REQUIRED_ENV if not os.getenv(name)]
    if missing:
        sys.exit(f"Missing environment variables: {', '.join(missing)}")

    client = get_box_client()
    run_id = os.getenv("GITHUB_RUN_ID") or f"local-{int(time.time())}"
    file_name = f"ci-run-{run_id}-sample-asset.jpg"

    with open("sample-asset.jpg", "rb") as image:
        uploaded = client.uploads.upload_file(
            UploadFileAttributes(
                name=file_name,
                parent=UploadFileAttributesParentField(id=os.getenv("DRAFT_FOLDER_ID")),
            ),
            image,
        )
    file_id = uploaded.entries[0].id
    print(f"Uploaded {file_name} as file {file_id}")

    try:
        test_client = app.test_client()
        check_extraction(test_client, client, file_id, file_name)
        check_lifecycle(test_client, client, file_id)
        check_exif(client, file_id)
        print("Live test passed")
    finally:
        client.files.delete_file_by_id(file_id)
        print(f"Deleted test file {file_id}")


if __name__ == "__main__":
    main()
