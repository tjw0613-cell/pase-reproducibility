"""Select installed fonts; do not bundle or download proprietary font files."""
from functools import lru_cache
import hashlib
import os
from pathlib import Path
import warnings
from matplotlib import font_manager


@lru_cache(maxsize=1)
def resolve_fonts():
    """Prefer manuscript Arial, then documented metrically similar fallbacks.

    The optional PASE_FIGURE_FONT_FAMILY variable permits testing the portable
    fallback. Native Origin PDF labels retain their already embedded fonts.
    """
    requested = os.environ.get('PASE_FIGURE_FONT_FAMILY')
    families = [requested] if requested else ['Arial', 'Liberation Sans', 'DejaVu Sans']
    for family in families:
        try:
            regular = font_manager.findfont(font_manager.FontProperties(family=family, weight='normal'), fallback_to_default=False)
            bold = font_manager.findfont(font_manager.FontProperties(family=family, weight='bold'), fallback_to_default=False)
        except ValueError:
            continue
        if family != 'Arial':
            warnings.warn(f'Arial is not selected; using {family} for new labels. The layout is regenerated, but pixels need not match the Arial submission.', stacklevel=2)
        return {'family': family, 'regular': regular, 'bold': bold,
                'regular_sha256': hashlib.sha256(Path(regular).read_bytes()).hexdigest(),
                'bold_sha256': hashlib.sha256(Path(bold).read_bytes()).hexdigest(),
                'fallback': family != 'Arial', 'font_files_distributed': False}
    raise RuntimeError('Install Arial, Liberation Sans or DejaVu Sans, or select an installed family with PASE_FIGURE_FONT_FAMILY.')
