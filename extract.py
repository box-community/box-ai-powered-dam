import os

from dotenv import load_dotenv
from box_sdk_gen import (
    AiItemBase,
    BoxClient,
    CreateAiExtractStructuredMetadataTemplate,
    CreateAiExtractStructuredMetadataTemplateTypeField,
)

load_dotenv()


def extract_brand_fields(client: BoxClient, file_id: str) -> dict:
    """Call Box AI structured extract with the Brand Asset metadata template.

    Structured extract runs OCR on JPEG, PNG, TIFF, and WEBP, so product
    shots and logos do not need converting to PDF first.
    """
    template_key = os.getenv("BOX_METADATA_TEMPLATE_KEY")

    result = client.ai.create_ai_extract_structured(
        items=[AiItemBase(id=file_id)],
        metadata_template=CreateAiExtractStructuredMetadataTemplate(
            template_key=template_key,
            type=CreateAiExtractStructuredMetadataTemplateTypeField.METADATA_TEMPLATE,
            scope="enterprise",
        ),
    )

    return result.to_dict()["answer"]
