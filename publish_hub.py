import os

from dotenv import load_dotenv
from box_sdk_gen import (
    FolderReferenceV2025R0,
    HubItemOperationV2025R0,
    HubItemOperationV2025R0ActionField,
)

from box_client import get_box_client

load_dotenv()


def main():
    """Create a Box Hub and add the Published folder to it.

    Run once. Each run creates a new hub; files you later move to
    Published appear in the existing hub automatically.
    """
    client = get_box_client()
    hub = client.hubs.create_hub_v2025_r0(
        "Brand asset library",
        description=(
            "Approved product imagery, logos, and marketing materials. "
            "Use only files in this hub for external distribution."
        ),
    )
    client.hub_items.manage_hub_items_v2025_r0(
        hub.id,
        operations=[
            HubItemOperationV2025R0(
                action=HubItemOperationV2025R0ActionField.ADD,
                item=FolderReferenceV2025R0(id=os.getenv("PUBLISHED_FOLDER_ID")),
            )
        ],
    )
    print(f"Hub ready: {hub.title} (ID: {hub.id})")


if __name__ == "__main__":
    main()
