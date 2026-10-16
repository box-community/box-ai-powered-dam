import os
from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv
from box_sdk_gen import (
    BoxAPIError,
    CreateCollaborationAccessibleBy,
    CreateCollaborationAccessibleByTypeField,
    CreateCollaborationItem,
    CreateCollaborationItemTypeField,
    CreateCollaborationRole,
)

from box_client import get_box_client

load_dotenv()


def invite_vendor(login: str, days: int = 30) -> dict:
    """Invite an external vendor to the Draft folder as Viewer Uploader.

    `expires_at` requires the "Allow folder owners to extend the expiry
    date" enterprise setting. If that setting is off, remove `expires_at`.
    """
    client = get_box_client()
    folder_id = os.getenv("DRAFT_FOLDER_ID")
    expires_at = datetime.now(timezone.utc) + timedelta(days=days)

    try:
        collaboration = client.user_collaborations.create_collaboration(
            item=CreateCollaborationItem(
                type=CreateCollaborationItemTypeField.FOLDER,
                id=folder_id,
            ),
            accessible_by=CreateCollaborationAccessibleBy(
                type=CreateCollaborationAccessibleByTypeField.USER,
                login=login,
            ),
            role=CreateCollaborationRole.VIEWER_UPLOADER,
            expires_at=expires_at,
            notify=True,
        )
    except BoxAPIError as error:
        if error.response_info.code != "user_already_collaborator":
            raise
        return {"status": "already_collaborator", "login": login}

    return collaboration.to_dict()


if __name__ == "__main__":
    import sys

    email = sys.argv[1] if len(sys.argv) > 1 else os.getenv("VENDOR_EMAIL")
    if not email:
        raise SystemExit("Pass a vendor email or set VENDOR_EMAIL")
    print(invite_vendor(email))
