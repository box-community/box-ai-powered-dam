import os

from dotenv import load_dotenv
from box_sdk_gen import (
    BoxAPIError,
    BoxClient,
    CreateFileMetadataByIdScope,
    UpdateFileMetadataByIdRequestBody,
    UpdateFileMetadataByIdRequestBodyOpField,
    UpdateFileMetadataByIdScope,
)

load_dotenv()


def apply_metadata(client: BoxClient, file_id: str, metadata: dict) -> dict:
    """Attach values to the file as a Brand Asset metadata instance.

    Creating the instance fails with 409 if the file already has one, so
    fall back to a JSON-Patch update. The `add` operation sets a value
    whether or not the field is already present.
    """
    template_key = os.getenv("BOX_METADATA_TEMPLATE_KEY")

    try:
        attached = client.file_metadata.create_file_metadata_by_id(
            file_id=file_id,
            scope=CreateFileMetadataByIdScope.ENTERPRISE,
            template_key=template_key,
            request_body=metadata,
        )
    except BoxAPIError as error:
        if error.response_info.status_code != 409:
            raise

        attached = client.file_metadata.update_file_metadata_by_id(
            file_id=file_id,
            scope=UpdateFileMetadataByIdScope.ENTERPRISE,
            template_key=template_key,
            request_body=[
                UpdateFileMetadataByIdRequestBody(
                    op=UpdateFileMetadataByIdRequestBodyOpField.ADD,
                    path=f"/{key}",
                    value=value,
                )
                for key, value in metadata.items()
            ],
        )

    return attached.to_dict()
