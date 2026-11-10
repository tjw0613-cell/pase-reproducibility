"""Exact pure display-colour functions extracted from the Origin panel builder."""
import numpy as np

def _hex_mix(a: str, b: str, fraction: float) -> str:
    fraction = min(1.0, max(0.0, float(fraction)))
    ar = [int(a[i:i + 2], 16) for i in (1, 3, 5)]
    br = [int(b[i:i + 2], 16) for i in (1, 3, 5)]
    rgb = [round(x * (1 - fraction) + y * fraction) for x, y in zip(ar, br)]
    return "#" + "".join(f"{v:02X}" for v in rgb)


def colour_contract(spec: dict) -> dict:
    """Pure, deterministic colour contract with a shared nominal centre.

    Colour levels are a display lookup and do not transform matrix values.
    White is assigned to the two narrow bins immediately adjoining the centre.
    The exact bin boundaries are returned for the external shared colour bar.
    """
    lo, mid, hi = (float(spec[k]) for k in ("zmin", "zmid", "zmax"))
    if not all(np.isfinite([lo, mid, hi])) or not lo < mid < hi:
        raise ValueError("Require finite zmin < zmid < zmax")
    mode = str(spec.get("cmap", spec.get("direction", spec.get("mode", "coverage")))).lower()
    if mode in {"error", "type_i", "type_i_error", "rejection"}:
        low_colour, high_colour = "#01665E", "#8C510A"
    elif mode == "coverage":
        low_colour, high_colour = "#8C510A", "#01665E"
    else:
        raise ValueError(f"Unsupported semantic colour direction: {mode}")
    if spec.get('palette')=='purple_teal':
        low_colour, high_colour = ('#569EA4','#70449D') if mode in {'error','type_i','type_i_error','rejection'} else ('#70449D','#569EA4')
    n = int(spec.get("colour_bins_per_side", 100))
    if not 10 <= n <= 200:
        raise ValueError("colour_bins_per_side must be 10..200")
    edges = np.r_[np.linspace(lo, mid, n + 1), np.linspace(mid, hi, n + 1)[1:]]
    colours = []
    for i in range(2 * n):
        if i < n:
            colour = _hex_mix(low_colour, "#FFFFFF", i / max(1, n - 1))
        else:
            colour = _hex_mix("#FFFFFF", high_colour, (i - n) / max(1, n - 1))
        colours.append(colour)
    return {
        "direction": mode,
        "zmin": lo,
        "zmid": mid,
        "zmax": hi,
        "levels": edges.tolist(),
        "colours": colours,
        "below_colour": low_colour,
        "above_colour": high_colour,
        "white_bin_indices_one_based": [n, n + 1],
        "semantics": "fixed original-percent scale; nominal-centred piecewise colour mapping",
        "data_transformation": "none",
    }

