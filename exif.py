import io
from datetime import datetime

from box_sdk_gen import BoxClient
from PIL import Image
from PIL.ExifTags import TAGS


def enrich_exif(client: BoxClient, file_id: str) -> dict:
    """Download the file and return camera EXIF values as template fields.

    Box AI Extract does not read camera EXIF, so this parses it locally.
    Files without EXIF (logos, exports) return an empty dict.
    """
    content = client.downloads.download_file(file_id)
    data = content.read() if hasattr(content, "read") else content
    image = Image.open(io.BytesIO(data))
    raw = image.getexif()
    if not raw:
        return {}

    tagged = {TAGS.get(key, key): value for key, value in raw.items()}
    # DateTimeOriginal is in the Exif sub-IFD (0x8769), not the main block
    tagged.update({TAGS.get(key, key): value for key, value in raw.get_ifd(0x8769).items()})
    enrichment = {}

    make = tagged.get("Make")
    model = tagged.get("Model")
    captured = tagged.get("DateTimeOriginal") or tagged.get("DateTime")

    if make:
        enrichment["cameraMake"] = str(make).strip()
    if model:
        enrichment["cameraModel"] = str(model).strip()
    if captured:
        try:
            parsed = datetime.strptime(str(captured), "%Y:%m:%d %H:%M:%S")
            enrichment["captureDate"] = parsed.strftime("%Y-%m-%dT00:00:00Z")
        except ValueError:
            pass

    return enrichment
