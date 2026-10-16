import os

from box_sdk_gen import BoxClient, UpdateFileByIdParent

from metadata import apply_metadata

STATUS_FOLDER_ENV = {
    "Draft": "DRAFT_FOLDER_ID",
    "Creative review": "CREATIVE_REVIEW_FOLDER_ID",
    "Legal review": "LEGAL_REVIEW_FOLDER_ID",
    "Approved": "APPROVED_FOLDER_ID",
    "Published": "PUBLISHED_FOLDER_ID",
    "Retired": "RETIRED_FOLDER_ID",
}


def advance_lifecycle(
    client: BoxClient, file_id: str, lifecycle_status: str
) -> dict:
    """Set lifecycleStatus and move the file to the matching stage folder.

    The status strings must match the Lifecycle Status dropdown options in
    the Brand Asset template exactly.
    """
    env_name = STATUS_FOLDER_ENV.get(lifecycle_status)
    if not env_name:
        raise ValueError(
            f"Unknown lifecycle status: {lifecycle_status}. "
            f"Allowed: {', '.join(STATUS_FOLDER_ENV)}"
        )

    folder_id = os.getenv(env_name)
    apply_metadata(client, file_id, {"lifecycleStatus": lifecycle_status})
    client.files.update_file_by_id(
        file_id, parent=UpdateFileByIdParent(id=folder_id)
    )
    return {"file_id": file_id, "lifecycle_status": lifecycle_status, "folder_id": folder_id}
