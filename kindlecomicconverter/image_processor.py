from .image import Image
from .common_crop import CommonCrop

def process_image_for_output(img: Image, options) -> list[Image]:
    """
    Processes a single image, applying cropping and splitting spreads if necessary.

    This function ensures that global cropping (e.g., smart cropping, margin removal)
    is applied to the entire image first. If the image is a spread and needs splitting,
    it is split *after* the initial cropping, preserving artwork alignment.

    Args:
        img: The input Image object.
        options: An object containing conversion options (e.g., spread, cropping settings).

    Returns:
        A list of processed Image objects (one for a single page, two for a spread).
    """
    # Apply global cropping first to the entire image.
    # This ensures consistent cropping across spreads before splitting.
    cropped_img = CommonCrop.apply(img, options)

    # Check if the cropped image should be split into a spread.
    # Splitting occurs only if 'spread' option is enabled, the image is landscape,
    # and it hasn't been split already.
    if options.spread and cropped_img.is_landscape() and not cropped_img.is_split():
        # Split the pre-cropped image into two halves.
        left_half = cropped_img.crop_half(left=True)
        right_half = cropped_img.crop_half(left=False)
        return [left_half, right_half]
    else:
        # Return the single (possibly cropped) image.
        return [cropped_img]
