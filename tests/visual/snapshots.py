"""Image helpers of the screenshot regression: compare with a reference image and put the
design next to the Streamlit page (#40)."""

from PIL import Image, ImageChops, ImageDraw, ImageFont

CHANNEL_TOLERANCE = 32  # anti-aliasing noise stays below this per colour channel
MAX_CHANGED_PIXELS = 100  # two runs render identically; a lost focus ring is already 2000
MARK = (220, 0, 0)
HEADER = 64  # height of the label row above the side-by-side image
BACKDROP = (200, 200, 200)  # below the shorter image


def on_canvas(image: Image.Image, size: tuple[int, int]) -> Image.Image:
    canvas = Image.new("RGB", size, "white")
    canvas.paste(image.convert("RGB"))
    return canvas


def changed_mask(actual: Image.Image, reference: Image.Image) -> Image.Image:
    """Mode "L" image of the larger size: 255 where a pixel differs by more than the tolerance;
    an area only one image covers counts as changed."""
    size = (max(actual.width, reference.width), max(actual.height, reference.height))
    diff = ImageChops.difference(on_canvas(actual, size), on_canvas(reference, size))
    mask = diff.convert("L").point(lambda v: 255 if v > CHANNEL_TOLERANCE else 0)
    overlap = Image.new("L", size, 255)
    overlap.paste(0, (0, 0, min(actual.width, reference.width),
                      min(actual.height, reference.height)))
    return ImageChops.lighter(mask, overlap)


def compare(actual: Image.Image, reference: Image.Image) -> Image.Image | None:
    """None if both look the same, otherwise the faded actual image with changes in red."""
    mask = changed_mask(actual, reference)
    if mask.histogram()[255] <= MAX_CHANGED_PIXELS:
        return None
    white = Image.new("RGB", mask.size, "white")
    faded = Image.blend(on_canvas(actual, mask.size), white, 0.7)
    faded.paste(MARK, mask=mask)
    return faded


def side_by_side(design: Image.Image, streamlit: Image.Image) -> Image.Image:
    """Design artboard left, Streamlit page right, each labelled; a template, not an oracle."""
    width, height = design.width + streamlit.width, max(design.height, streamlit.height)
    image = Image.new("RGB", (width, height + HEADER), BACKDROP)
    image.paste(design.convert("RGB"), (0, HEADER))
    image.paste(streamlit.convert("RGB"), (design.width, HEADER))
    draw, font = ImageDraw.Draw(image), ImageFont.load_default(size=HEADER // 2)
    draw.rectangle((0, 0, width, HEADER - 1), fill="white")
    for x, label in ((0, "Design"), (design.width, "Streamlit")):
        draw.text((x + 16, HEADER // 4), label, fill="black", font=font)
    return image
