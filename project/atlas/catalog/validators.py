from django.core.exceptions import ValidationError

MAX_IMAGE_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB


def validate_image_size(image_file):
    """Pillow (via ImageField) already validates that an upload really IS
    an image — this validates it isn't absurdly LARGE. Without a limit,
    "upload a product photo" is an unauthenticated-looking-but-actually-
    permission-gated denial-of-service vector: repeated multi-gigabyte
    uploads can fill disk or exhaust request-handling workers on nothing
    but I/O, long before any application logic runs."""
    if image_file.size > MAX_IMAGE_SIZE_BYTES:
        raise ValidationError(
            f"Image file too large ({image_file.size / 1024 / 1024:.1f} MB). "
            f"Maximum size is {MAX_IMAGE_SIZE_BYTES / 1024 / 1024:.0f} MB."
        )
