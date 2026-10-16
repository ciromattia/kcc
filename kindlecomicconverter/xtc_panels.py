# -*- coding: utf-8 -*-
"""Adaptive panel grouping with whole-page fallback for ambiguous layouts."""

from PIL import Image, ImageFilter, ImageOps


def _runs(values, threshold, minimum):
    runs = []
    start = None
    for index, value in enumerate(values):
        if value <= threshold and start is None:
            start = index
        elif value > threshold and start is not None:
            if index - start >= minimum:
                runs.append((start, index))
            start = None
    if start is not None and len(values) - start >= minimum:
        runs.append((start, len(values)))
    return runs


def _gutter_runs(gray, axis, threshold, minimum):
    # A small blur suppresses halftone noise while retaining white gutters.
    blurred = gray if minimum == 1 else gray.filter(ImageFilter.GaussianBlur(radius=1))
    pixels = blurred.load()
    width, height = blurred.size
    white_level = 220 if minimum == 1 else 245
    if axis == "rows":
        values = [sum(pixels[x, y] >= white_level for x in range(width)) / width
                  for y in range(height)]
    else:
        values = [sum(pixels[x, y] >= white_level for y in range(height)) / height
                  for x in range(width)]
    return _runs([1 - value for value in values], threshold, minimum)


def _band_columns(gray, top, bottom, threshold, minimum):
    band = gray.crop((0, top, gray.width, bottom))
    gutters = _gutter_runs(band, "columns", threshold, minimum)
    if _has_black_border(band):
        gutters += _gutter_runs(ImageOps.invert(band), "columns", threshold, minimum)
    return _merge_gutters(gutters)


def _has_black_border(gray):
    edges = (gray.crop((0, 0, 1, gray.height)),
             gray.crop((gray.width - 1, 0, gray.width, gray.height)))
    black = sum(sum(edge.histogram()[:16]) for edge in edges)
    return black >= gray.height


def _merge_gutters(gutters):
    merged = []
    for start, end in sorted(gutters):
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(end, merged[-1][1]))
        else:
            merged.append((start, end))
    return merged


def _framed_row_gutters(gray):
    """Recognise a shaded/crossed gap between two long horizontal borders."""
    mask = gray.point(lambda value: 255 if value < 150 else 0).tobytes()
    line = b"\xff" * max(1, int(gray.width * .5))
    borders = _runs([0 if line in mask[y * gray.width:(y + 1) * gray.width]
                     else 1 for y in range(gray.height)], 0, 1)
    gutters = []
    for (_, end), (start, _) in zip(borders, borders[1:]):
        if not 2 <= start - end <= gray.height * .05:
            continue
        gap = gray.crop((0, end, gray.width, start))
        # Require frame edges so dark interiors are not mistaken for gutters.
        histogram = gap.histogram()
        area = gap.width * gap.height
        mean = sum(value * count for value, count in enumerate(histogram)) / area
        if sum(histogram[:150]) / area < .25 and mean >= 200:
            gutters.append((end, start))
    return gutters


def _intervals(length, gutters, minimum, overlap=False):
    """Partition at gutter centres and merge undersized regions."""
    cuts = [0] + [(start + end) // 2 for start, end in gutters
                  if start > 0 and end < length] + [length]
    intervals = list(zip(cuts, cuts[1:]))
    index = 0
    while len(intervals) > 1 and index < len(intervals):
        start, end = intervals[index]
        if end - start >= minimum:
            index += 1
        elif index == 0:
            intervals[:2] = [(start, intervals[1][1])]
        else:
            intervals[index - 1:index + 1] = [(intervals[index - 1][0], end)]
            index -= 1
    if overlap:
        edges = {(start + end) // 2: (start, end) for start, end in gutters}
        # Overlap preserves artwork protruding into gutters.
        intervals = [(edges[start][0] if start in edges else start,
                      edges[end][1] if end in edges else end)
                     for start, end in intervals]
    return intervals


def _trim_white_margin(image):
    # Ignore light scan noise when finding margins.
    mask = image.convert("L").point(lambda value: 255 if value < 245 else 0)
    bbox = mask.getbbox()
    if bbox is None:
        return image
    padding = max(2, int(min(image.size) * .003))
    left, top, right, bottom = bbox
    return image.crop((max(0, left - padding), max(0, top - padding),
                       min(image.width, right + padding),
                       min(image.height, bottom + padding)))


def _usable_crop(crop, page_size):
    """Reject detector outputs that are slivers or contain almost no ink."""
    page_width, page_height = page_size
    width_ratio = crop.width / max(1, page_width)
    height_ratio = crop.height / max(1, page_height)
    if min(width_ratio, height_ratio) < 0.08:
        return False
    gray = crop.convert("L")
    histogram = gray.histogram()
    dark_ratio = sum(histogram[:220]) / max(1, crop.width * crop.height)
    if dark_ratio < 0.0015:
        return False
    bbox = gray.point(lambda value: 255 if value < 220 else 0).getbbox()
    if bbox is None:
        return False
    bbox_area = (bbox[2] - bbox[0]) * (bbox[3] - bbox[1])
    return bbox_area / max(1, crop.width * crop.height) >= 0.025


def readability_views(image, target_width=800, target_height=480):
    """Enlarge tall regions up to 2x with 25% overlap; balloons may span views."""
    width, height = image.size
    fit = min(target_width / width, target_height / height)
    if fit * width >= target_width * .75:
        return [image]
    scale = min(target_width / width, fit * 2)
    view_height = min(height, max(1, round(target_height / scale)))
    step = max(1, round(view_height * .75))
    starts = list(range(0, height - view_height + 1, step))
    if starts[-1] != height - view_height:
        starts.append(height - view_height)
    views = [image.crop((0, start, width, start + view_height)) for start in starts]
    for view in views:
        gray = view.convert('L')
        bbox = gray.point(lambda value: 255 if value < 220 else 0).getbbox()
        if (bbox is None or sum(gray.histogram()[:220]) / (view.width * view.height) < .01
                or min((bbox[2] - bbox[0]) / view.width,
                       (bbox[3] - bbox[1]) / view.height) < .10):
            return [image]
    return views


def auto_orient_x4(image, target_width=480, target_height=800, rotate_right=False):
    """Prefer landscape unless bezel-aligned portrait enlarges content by 25%."""
    portrait_fit = min(target_width / image.width, target_height / image.height)
    landscape_fit = min(target_height / image.width, target_width / image.height)
    if portrait_fit >= landscape_fit * 1.25:
        # Align portrait content with the X4's broad bottom bezel.
        return image.transpose(Image.Transpose.ROTATE_180)
    return rotate_x4(image, rotate_right=rotate_right)


def rotate_x4(image, rotate_right=False):
    """Rotate clockwise for storage; rotate_right selects the opposite bezel."""
    angle = 90 if rotate_right else -90
    return image.rotate(angle, expand=True)


def adaptive_panel_crops(image, right_to_left=True, min_panel_ratio=0.08,
                         min_gutter_ratio=0.006, min_fit_scale=0.75,
                         target_width=480, target_height=800, rotate=True,
                         rotate_right=False):
    """Return grouped crops in reading order, preserving ambiguous pages.

    min_fit_scale is relative to a full-width band on the target screen.
    """
    if image.width < 2 or image.height < 2:
        return [image]
    gray = image.convert("L")
    if gray.getextrema()[0] >= 250:
        return [image]

    def orient(page):
        if not rotate:
            return page
        return rotate_x4(page, rotate_right=rotate_right)

    image = _trim_white_margin(image)
    gray = image.convert("L")
    min_gutter = max(4, int(min(image.width, image.height) * min_gutter_ratio))
    # Continuous side borders must disqualify near-white rows as gutters.
    gutter_minimum = max(2, min_gutter // 2)
    row_gutters = _gutter_runs(gray, "rows", .001, 1)
    black_gutters = [(start, end) for start, end in
                     _gutter_runs(ImageOps.invert(gray), "rows", .001, gutter_minimum)
                     if start > 0 and end < gray.height]
    if len(black_gutters) >= 2 or _has_black_border(gray):
        row_gutters += black_gutters
    row_gutters = _merge_gutters(row_gutters + _framed_row_gutters(gray))
    bands = _intervals(image.height, row_gutters,
                       max(min_gutter * 3, image.height * min_panel_ratio), overlap=True)

    groups = []
    for top, bottom in bands:
        col_gutters = _band_columns(gray, top, bottom, .001, gutter_minimum)
        # Merge small cells to preserve narrow panels and speech bubbles.
        minimum_width = max(image.width * min_panel_ratio,
                            image.width * image.height * min_panel_ratio / (bottom - top))
        columns = _intervals(image.width, col_gutters, minimum_width)
        cells = [(left, top, right, bottom)
                 for left, right in columns]

        order = list(reversed(cells)) if right_to_left else cells
        merged = []
        current = order[0]
        for cell in order[1:]:
            candidate = (
                min(current[0], cell[0]), min(current[1], cell[1]),
                max(current[2], cell[2]), max(current[3], cell[3]),
            )
            candidate_width = candidate[2] - candidate[0]
            candidate_height = candidate[3] - candidate[1]
            canvas_width, canvas_height = ((target_height, target_width) if rotate
                                           else (target_width, target_height))
            fit_scale = min(canvas_width / candidate_width,
                            canvas_height / candidate_height)
            full_width_scale = canvas_width / image.width
            if fit_scale / full_width_scale >= min_fit_scale:
                current = candidate
            else:
                merged.append(current)
                current = cell
        merged.append(current)
        groups.extend(merged)

    if len(groups) <= 1:
        # Straight projections miss diagonal gutters and mixed-height layouts.
        from .xtc_layout import irregular_panel_crops
        crops = irregular_panel_crops(
            image, right_to_left=right_to_left, min_fit_scale=min_fit_scale,
            target_width=target_width, target_height=target_height, rotate=rotate,
        )
        if len(crops) > 1 and all(_usable_crop(crop, image.size) for crop in crops):
            return [orient(crop) for crop in crops]
        return [orient(image)]
    raw_crops = [_trim_white_margin(image.crop((left, top, right, bottom)))
                 for left, top, right, bottom in groups]
    if not all(_usable_crop(crop, image.size) for crop in raw_crops):
        return [orient(image)]
    return [orient(crop) for crop in raw_crops]
