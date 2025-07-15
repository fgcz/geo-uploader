import logging
import os
import re

from wtforms.validators import ValidationError

logger = logging.getLogger(__name__)


def validate_safe_path(form, field):
    # Windows reserved filenames
    windows_reserved = [
        "CON",
        "PRN",
        "AUX",
        "NUL",
        "COM1",
        "COM2",
        "COM3",
        "COM4",
        "COM5",
        "COM6",
        "COM7",
        "COM8",
        "COM9",
        "LPT1",
        "LPT2",
        "LPT3",
        "LPT4",
        "LPT5",
        "LPT6",
        "LPT7",
        "LPT8",
        "LPT9",
    ]

    # Check for invalid characters
    if re.search(r'[\\/:*?"<>|]', field.data):
        raise ValidationError('Title contains invalid characters: / \\ : * ? " < > |')

    # Check for Windows reserved names
    if field.data.upper() in windows_reserved or re.match(
        r"^(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(\.|$)", field.data.upper()
    ):
        raise ValidationError(f"'{field.data}' is a reserved system name")

    # Check for starting/ending with spaces or periods
    if field.data.startswith((" ", ".")) or field.data.endswith((" ", ".")):
        raise ValidationError("Title cannot start or end with spaces or periods")

    # Check length (max path length varies by OS, but keep it reasonable)
    if len(field.data) > 255:
        raise ValidationError("Title is too long")

    # Check for empty string after removing invalid chars (extra check)
    if not field.data.strip():
        raise ValidationError("Title cannot be empty or just whitespace")

    try:
        # Try to normalize the path to check OS-specific constraints
        # This will fail if the filename isn't valid
        os.path.normpath(os.path.join("dummy_dir", field.data))
    except OSError:
        raise ValidationError("This title would create an invalid file path")
