"""Split irregular layouts along verified light-pixel seams without warping."""

import numpy as np
from PIL import Image


def _path(white, positions, prior):
    """Find a smooth light-pixel path, with at most two pixels of movement."""
    depth, width = white.shape
    indices = np.arange(width)
    parents = np.empty((depth, width), dtype=np.int32)
    previous = np.where(white[0], prior[0], np.inf)
    for row in range(1, depth):
        # Refinement positions can form a moving corridor.
        shifts = positions[row, 0] - positions[row - 1, 0]
        candidates = indices[None, :] + shifts + np.arange(-2, 3)[:, None]
        valid = (candidates >= 0) & (candidates < width)
        clipped = np.clip(candidates, 0, width - 1)
        costs = np.where(valid, previous[clipped], np.inf)
        costs += np.abs(np.arange(-2, 3))[:, None] * .002
        best = np.argmin(costs, axis=0)
        parents[row] = clipped[best, indices]
        previous = np.where(white[row], costs[best, indices] + prior[row], np.inf)
        if not np.isfinite(previous).any():
            return None
    column = int(np.argmin(previous))
    if not np.isfinite(previous[column]):
        return None
    path = np.empty(depth, dtype=np.int32)
    for row in range(depth - 1, -1, -1):
        path[row] = positions[row, column]
        if row:
            column = parents[row, column]
    return path


def _native_seam(gray, seed):
    # Narrow gutters can disappear at preview resolution.
    if gray.width * gray.height > 2_000_000:
        return None
    pixels = np.asarray(gray)
    depth, width = pixels.shape
    positions = np.broadcast_to(np.arange(width), (depth, width))
    white = pixels >= 220
    margin = max(2, int(width * .12))
    white[:, :margin] = False
    white[:, width - margin:] = False
    prior = np.broadcast_to(((np.arange(width) / width - seed) ** 2) * .2,
                            (depth, width))
    return _path(white, positions, prior)


def _seam(gray, seed):
    """Search at preview size, then verify/refine on original pixels."""
    preview = gray.copy()
    preview.thumbnail((320, 480), Image.Resampling.BOX)
    small = np.asarray(preview)
    depth, width = small.shape
    positions = np.broadcast_to(np.arange(width), (depth, width))
    white = small >= 220
    margin = max(2, int(width * .12))
    white[:, :margin] = False
    white[:, width - margin:] = False
    prior = np.broadcast_to(((np.arange(width) / width - seed) ** 2) * .2,
                            (depth, width))
    path = _path(white, positions, prior)
    if path is None:
        return _native_seam(gray, seed)

    original = np.asarray(gray)
    height, span = original.shape
    centres = np.rint(np.interp(np.arange(height),
                               np.linspace(0, height - 1, depth), path)
                      * (span / width)).astype(np.int32)
    radius = max(4, int(np.ceil(span / width * 3)))
    offsets = np.arange(-radius, radius + 1)
    positions = centres[:, None] + offsets[None, :]
    valid = (positions >= int(span * .1)) & (positions < span * .9)
    white = (original[np.arange(height)[:, None], np.clip(positions, 0, span - 1)] >= 220) & valid
    prior = np.broadcast_to((offsets / max(1, radius)) ** 2 * .002, positions.shape)
    refined = _path(white, positions, prior)
    return _native_seam(gray, seed) if refined is None else refined


def _score(gray, path):
    ink = np.asarray(gray) < 220
    height, width = ink.shape
    if np.ptp(path) > width * .35:
        return None
    counts = np.pad(np.cumsum(ink, axis=1), ((0, 0), (1, 0)))
    rows = np.arange(height)
    left_ink = counts[rows, path].sum()
    total = counts[:, -1].sum()
    balance = min(left_ink, total - left_ink) / max(1, total)
    area = path.sum() / (height * width)
    if balance < .10 or min(area, 1 - area) < .12:
        return None
    radius = max(5, int(width * .05))
    left = counts[rows, path] - counts[rows, np.maximum(0, path - radius)]
    right = counts[rows, np.minimum(width, path + radius)] - counts[rows, path]
    support = np.mean((left > 0) & (right > 0))
    if support < .30:
        return None
    return balance * support


def _trim(image):
    bbox = image.convert("L").point(lambda value: 255 if value < 245 else 0).getbbox()
    if bbox is None:
        return image
    left, top, right, bottom = bbox
    return image.crop((max(0, left - 2), max(0, top - 2),
                       min(image.width, right + 2), min(image.height, bottom + 2)))


def _children(image, axis, path):
    height, width = image.height, image.width
    if axis == "columns":
        mask = np.arange(width)[None, :] < path[:, None]
    else:
        mask = np.arange(height)[:, None] < path[None, :]
    children = []
    for region in (mask, ~mask):
        child = Image.new("RGB", image.size, "white")
        child.paste(image.convert("RGB"), mask=Image.fromarray(region.astype(np.uint8) * 255))
        children.append(_trim(child))
    return children


def _substantial_region(image):
    # Check ink bounds rather than masked canvas dimensions.
    bbox = image.convert("L").point(lambda value: 255 if value < 220 else 0).getbbox()
    if bbox is None:
        return False
    width, height = bbox[2] - bbox[0], bbox[3] - bbox[1]
    return min(width, height) / max(width, height) >= .18


def irregular_panel_crops(image, right_to_left=True, min_fit_scale=.75,
                          target_width=480, target_height=800, rotate=True):
    """Return at most four ordered groups, using only verified light seams."""
    canvas_width, canvas_height = ((target_height, target_width) if rotate
                                   else (target_width, target_height))
    reference_scale = canvas_width / image.width

    def visit(region, depth):
        scale = min(canvas_width / region.width, canvas_height / region.height)
        if depth >= 3 or scale / reference_scale >= min_fit_scale or min(region.size) < 32:
            return [region]
        gray = region.convert("L")
        candidates = []
        for axis in ("rows", "columns"):
            view = gray.transpose(Image.Transpose.TRANSPOSE) if axis == "rows" else gray
            for seed in (.33, .5, .67):
                path = _seam(view, seed)
                score = None if path is None else _score(view, path)
                if score is not None and all(_substantial_region(child)
                                             for child in _children(region, axis, path)):
                    candidates.append((score, axis, path))
        if not candidates:
            return [region]
        _, axis, path = max(candidates, key=lambda candidate: candidate[0])
        children = _children(region, axis, path)
        if axis == "columns" and right_to_left:
            children.reverse()
        results = [crop for child in children for crop in visit(child, depth + 1)]
        return results if len(results) <= 4 else children

    return visit(image, 0)
