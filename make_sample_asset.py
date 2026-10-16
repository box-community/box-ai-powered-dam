"""Generate sample-asset.jpg: a campaign image with on-image text and camera EXIF.

Upload the result to your Draft folder to test Box AI extraction and the
optional EXIF step. Requires Pillow.
"""
from PIL import Image, ImageDraw, ImageFont

OUTPUT = "sample-asset.jpg"

# EXIF tag IDs
MAKE = 0x010F
MODEL = 0x0110
EXIF_IFD = 0x8769
DATE_TIME_ORIGINAL = 0x9003


def load_font(size: int):
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


def main():
    image = Image.new("RGB", (1200, 800), (28, 61, 90))
    draw = ImageDraw.Draw(image)

    draw.rectangle([80, 260, 1120, 620], fill=(240, 236, 226))
    draw.text((80, 70), "NORTHWIND", font=load_font(72), fill=(255, 255, 255))
    draw.text((80, 170), "Autumn 2026 Campaign", font=load_font(48), fill=(255, 196, 92))
    draw.text((130, 360), "Trail Runner", font=load_font(96), fill=(28, 61, 90))
    draw.text((130, 500), "All-terrain running shoe", font=load_font(44), fill=(90, 90, 90))
    draw.text((80, 690), "Approved for external use", font=load_font(32), fill=(255, 255, 255))

    exif = Image.Exif()
    exif[MAKE] = "Canon"
    exif[MODEL] = "Canon EOS R6"
    exif.get_ifd(EXIF_IFD)[DATE_TIME_ORIGINAL] = "2026:09:12 10:30:00"

    image.save(OUTPUT, "JPEG", quality=90, exif=exif)
    print(f"Wrote {OUTPUT}")


if __name__ == "__main__":
    main()
