def colorCheck(image, original_color_mode, opt):
    if original_color_mode in ("L", "1"):
        return False
    if opt.webtoon:
        return True
    if calculate_color(image, opt):
        return True
    return False

# cut off pixels from both ends of the histogram to remove jpg compression artifacts
# for better accuracy, you could split the image in half and analyze each half separately
def histograms_cutoff(cb_hist, cr_hist, cutoff=(2, 2)):
    if cutoff == (0, 0):
        return cb_hist, cr_hist

    for h in cb_hist, cr_hist:
        # get number of pixels
        n = sum(h)
        # remove cutoff% pixels from the low end
        cut = int(n * cutoff[0] // 100)
        for lo in range(256):
            if cut > h[lo]:
                cut = cut - h[lo]
                h[lo] = 0
            else:
                h[lo] -= cut
                cut = 0
            if cut <= 0:
                break
        # remove cutoff% samples from the high end
        cut = int(n * cutoff[1] // 100)
        for hi in range(255, -1, -1):
            if cut > h[hi]:
                cut = cut - h[hi]
                h[hi] = 0
            else:
                h[hi] -= cut
                cut = 0
            if cut <= 0:
                break
    return cb_hist, cr_hist

def color_precision(cb_hist_original, cr_hist_original, cutoff, diff_threshold, opt):
    cb_hist, cr_hist = histograms_cutoff(cb_hist_original.copy(), cr_hist_original.copy(), cutoff)

    cb_nonzero = [i for i, e in enumerate(cb_hist) if e]
    cr_nonzero = [i for i, e in enumerate(cr_hist) if e]
    cb_spread = cb_nonzero[-1] - cb_nonzero[0]
    cr_spread = cr_nonzero[-1] - cr_nonzero[0]

    # bias adjustment, don't go lower than 7
    SPREAD_THRESHOLD = 7
    if opt.forcecolor:
        if any([
            cb_nonzero[0] > 128,
            cr_nonzero[0] > 128,
            cb_nonzero[-1] < 128,
            cr_nonzero[-1] < 128,
        ]):
            return True, True
    elif cb_spread < SPREAD_THRESHOLD and cr_spread < SPREAD_THRESHOLD:
        return True, False

    DIFF_THRESHOLD = diff_threshold
    if any([
        cb_nonzero[0] <= 128 - DIFF_THRESHOLD, 
        cr_nonzero[0] <= 128 - DIFF_THRESHOLD, 
        cb_nonzero[-1] >= 128 + DIFF_THRESHOLD, 
        cr_nonzero[-1] >= 128 + DIFF_THRESHOLD,
    ]):
        return True, True
    
    return False, None

def calculate_color(image, opt):
    img = image.convert("YCbCr")
    _, cb, cr = img.split()
    cb_hist_original = cb.histogram()
    cr_hist_original = cr.histogram()

    # you can increase 22 but don't increase 10. 4 maybe can go higher
    for cutoff, diff_threshold in [((0, 0), 22), ((.2, .2), 10), ((3, 3), 4)]:
        done, decision = color_precision(cb_hist_original, cr_hist_original, cutoff, diff_threshold, opt)
        if done:
            return decision
    return False