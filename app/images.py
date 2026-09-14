import base64
import binascii
import io
import warnings

from PIL import Image, ImageOps, UnidentifiedImageError

MAX_BYTES = 5 * 1024 * 1024


def prepare_image(encoded):
    if not encoded:
        return None
    try:
        raw = base64.b64decode(encoded, validate=True)
        if len(raw) > MAX_BYTES:
            raise ValueError('Screenshot must be 5 MB or smaller.')
        with warnings.catch_warnings():
            warnings.simplefilter('error', Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(raw)) as source:
                if source.format not in ('PNG', 'JPEG', 'WEBP'):
                    raise ValueError('Use a PNG, JPEG, or WebP screenshot.')
                if source.width * source.height > 20_000_000:
                    raise ValueError('Screenshot must be at most 20 megapixels.')
                source.load()
                clean = ImageOps.exif_transpose(source).convert('RGB')
                clean.thumbnail((2400, 2400))
                output = io.BytesIO()
                clean.save(output, format='JPEG', quality=90)
        return 'data:image/jpeg;base64,' + base64.b64encode(output.getvalue()).decode()
    except (binascii.Error, UnidentifiedImageError, OSError, Image.DecompressionBombError,
            Image.DecompressionBombWarning) as exc:
        raise ValueError('Screenshot is invalid or too large. Use PNG, JPEG, or WebP.') from exc
