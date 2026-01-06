"""Image cropping service for non-square image handling."""
from pathlib import Path
from PIL import Image, ImageOps


def _load_and_rotate(img_path: Path) -> Image.Image | None:
    """Load image and apply EXIF rotation.

    Args:
        img_path: Path to image file.

    Returns:
        Rotated PIL Image object, or None on error.
    """
    try:
        img = Image.open(img_path)
        # Apply EXIF rotation if present
        img = ImageOps.exif_transpose(img)
        return img
    except Exception:
        return None


def get_image_dimensions(filename: str) -> dict[str, int] | None:
    """Get width and height of image file with EXIF rotation applied.

    Args:
        filename: Image filename.

    Returns:
        Dict with 'width' and 'height' keys, or None if unable to read.
    """
    img_path = get_safe_image_path(filename)
    if not img_path:
        return None

    img = _load_and_rotate(img_path)
    if not img:
        return None

    try:
        return {'width': img.width, 'height': img.height}
    finally:
        img.close()


def is_square_image(filename: str) -> bool:
    """Check if image has square dimensions.

    Args:
        filename: Image filename.

    Returns:
        True if image width equals height, False otherwise.
    """
    dims = get_image_dimensions(filename)
    if not dims:
        return False
    return dims['width'] == dims['height']


def get_safe_image_path(filename: str) -> Path | None:
    """Retrieve safe path to image file with directory traversal prevention.

    Args:
        filename: Image filename to retrieve.

    Returns:
        Path object if file exists and is in img directory, None otherwise.
    """
    img_dir = Path(__file__).parent.parent / 'img'
    file_path = img_dir / filename

    # Prevent directory traversal attacks
    if file_path.resolve().parent != img_dir.resolve():
        return None

    return file_path if file_path.exists() else None


def copy_square_image(filename: str) -> str | None:
    """Copy already-square image to squared subfolder.

    Args:
        filename: Original image filename.

    Returns:
        Copied filename (e.g., 'photo_square.jpg') if successful, None otherwise.
    """
    img_path = get_safe_image_path(filename)
    if not img_path:
        return None

    try:
        # Copy image to squared subfolder
        name_without_ext = img_path.stem
        square_filename = f"{name_without_ext}_square.jpg"
        img_dir = img_path.parent
        squared_dir = img_dir / 'squared'
        squared_dir.mkdir(exist_ok=True)
        square_path = squared_dir / square_filename

        # If already JPEG, copy directly; otherwise convert
        if img_path.suffix.lower() in {'.jpg', '.jpeg'}:
            import shutil
            shutil.copy2(img_path, square_path)
        else:
            img = _load_and_rotate(img_path)
            if not img:
                return None
            img.save(square_path, 'JPEG', quality=95)
            img.close()

        return square_filename
    except Exception:
        return None


def save_cropped_image(filename: str, crop_box: dict) -> str | None:
    """Crop image and save to squared subfolder.

    Applies EXIF rotation before cropping to handle portrait/rotated photos.

    Args:
        filename: Original image filename.
        crop_box: Dict with 'x', 'y', 'size' keys specifying crop region.

    Returns:
        Cropped filename (e.g., 'photo_square.jpg') if successful, None otherwise.
    """
    img_path = get_safe_image_path(filename)
    if not img_path:
        return None

    try:
        img = _load_and_rotate(img_path)
        if not img:
            return None

        x, y, size = crop_box['x'], crop_box['y'], crop_box['size']
        cropped = img.crop((x, y, x + size, y + size))

        # Save to squared subfolder
        name_without_ext = img_path.stem
        square_filename = f"{name_without_ext}_square.jpg"
        img_dir = img_path.parent
        squared_dir = img_dir / 'squared'
        squared_dir.mkdir(exist_ok=True)
        square_path = squared_dir / square_filename
        cropped.save(square_path, 'JPEG', quality=95)

        return square_filename
    except Exception:
        return None


def get_largest_square_dimensions(filename: str) -> dict | None:
    """Calculate largest square that fits in image.

    Args:
        filename: Image filename.

    Returns:
        Dict with 'size', 'x', 'y' keys for centered square, None on error.
    """
    dims = get_image_dimensions(filename)
    if not dims:
        return None

    size = min(dims['width'], dims['height'])
    x = (dims['width'] - size) // 2
    y = (dims['height'] - size) // 2

    return {'size': size, 'x': x, 'y': y}
