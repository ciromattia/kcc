from PIL import ImageOps, ImageFilter
import numpy as np

'''
Some assupmptions on the page number sizes
We assume that the size of the number (including all digits) is between
'min_shape_size_tolerated_size' and 'max_shape_size_tolerated_size' relative to the image size.
We assume the distance between the digit is no more than 'max_dist_size' (x,y), and no more than 3 digits.
'''
max_shape_size_tolerated_size = (0.015*3, 0.02) # percent
min_shape_size_tolerated_size = (0.003, 0.006)  # percent
window_h_size = max_shape_size_tolerated_size[1]*1.25 # percent
max_dist_size = (0.01, 0.002) # percent


'''
E-reader screen real-estate is an important resource.
More available screensize means more details can be better seen, especially text.
Text is one of the most important elements that need to be clearly readable on e-readers,
which mostly are smaller devices where the need to zoom is unwanted.

By cropping the page number on the bottom of the page, 2%-5% of the page height can be regained
that allows us to upscale the image even more.
- Most of the times the screen height is the limiting factor in upscaling, rather than its width.

    Parameters:
            img (PIL image): A PIL image.
            power (float): The power to 'chop' through pixels matching the background. Values in range[0,3].
            background_color (string): 'white' for white background, anything else for black.
    Returns:
            bbox (4-tuple, left|top|right|bot): The tightest bounding box calculated after trying to remove the bottom page number. Returns None if couldnt find anything satisfactory
'''
def get_bbox_crop_margin_page_number(img, power=1, background_color='white'):
    if img.mode != 'L':
        img = ImageOps.grayscale(img)
    
    if background_color != 'white':
        img = ImageOps.invert(img)
        
    '''
    Autocontrast: due to some threshold values, it's important that the blacks will be blacks and white will be whites.
    Box/MeanFilter: Allows us to reduce noise like bad a page scan or compression artifacts.
    Note: MedianFilter works better in my experience, but takes 2x-3x longer to perform.
    '''
    img = ImageOps.autocontrast(img, 1).filter(ImageFilter.BoxBlur(1))
    
    '''
    The 'power' parameters determines the threshold. The higher the power, the more "force" it can crop through black pixels (in case of white background)
    and the lower the power, more sensitive to black pixels. 
    '''
    threshold = threshold_from_power(power)
    bw_img = img.point(lambda p: 255 if p <= threshold else 0)
    left, top_y_pos, right, bot_y_pos = bw_img.getbbox()
    
    '''
    We inspect the lower bottom part of the image where we suspect might be a page number.
    We assume that page number consist of 1 to 3 digits and the total min and max size of the number
    is between 'min_shape_size_tolerated_size' and 'max_shape_size_tolerated_size'.
    '''
    window_h = int(img.size[1] * window_h_size)
    img_part = img.crop((left,bot_y_pos-window_h, right, bot_y_pos))

    '''
    We detect related-pixels by proximity, with max distance defined in 'max_dist_size'.
    Related pixels (in x axis) for each image-row are then merged to boxes with adjacent rows (in y axis)
    to form bounding boxes of the detected objects (which one of them could be the page number).
    '''
    img_part_mat = np.array(img_part)
    window_groups = []
    for i in range(img_part.size[1]):
        row_groups = [(g[0], g[1], i, i) for g in group_pixels(img_part_mat[i], img.size[0]*max_dist_size[0], threshold)]
        window_groups.extend(row_groups)

    window_groups = np.array(window_groups)

    boxes = merge_boxes(window_groups, (img.size[0]*max_dist_size[0], img.size[1]*max_dist_size[1]))
    '''
    We assume that the lowest part of the image that has black pixels on is the page number.
    In case that there are more than one detected object in the loewst part, we assume that one of them is probably
    manga-content and shouldn't be cropped.
    '''
    # filter all small objects
    boxes = list(filter(lambda box: box[1]-box[0] >= img.size[0]*min_shape_size_tolerated_size[0] 
                        and box[3]-box[2] >= img.size[1]*min_shape_size_tolerated_size[1], boxes))
    lowest_boxes = list(filter(lambda box: box[3] == window_h-1, boxes))
    
    min_y_of_lowest_boxes = 0
    if len(lowest_boxes) > 0:
        min_y_of_lowest_boxes = np.min(np.array(lowest_boxes)[:,2])
    
    boxes_in_same_y_range = list(filter(lambda box: box[3] >= min_y_of_lowest_boxes, boxes))

    max_shape_size_tolerated = (img.size[0] * max_shape_size_tolerated_size[0], 
                                max(img.size[1] *max_shape_size_tolerated_size[1], 3))

    should_force_crop = (
        len(boxes_in_same_y_range) == 1
        and (boxes_in_same_y_range[0][1] - boxes_in_same_y_range[0][0] <= max_shape_size_tolerated[0])
        and (boxes_in_same_y_range[0][3] - boxes_in_same_y_range[0][2] <= max_shape_size_tolerated[1])
    )
        
    cropped_bbox = (0, 0, img.size[0], img.size[1])
    if should_force_crop:
        cropped_bbox = (0, 0, img.size[0], bot_y_pos-(window_h-boxes_in_same_y_range[0][2]+1))

    cropped_bbox = bw_img.crop(cropped_bbox).getbbox()
    
    return cropped_bbox


'''
    Parameters:
            img (PIL image): A PIL image.
            power (float): The power to 'chop' through pixels matching the background. Values in range[0,3].
            background_color (string): 'white' for white background, anything else for black.
    Returns:
            bbox (4-tuple, left|top|right|bot): The tightest bounding box calculated after trying to remove the bottom page number. Returns None if couldnt find anything satisfactory
'''
def get_bbox_crop_margin(img, power=1, background_color='white'):
    if img.mode != 'L':
        img = ImageOps.grayscale(img)
    
    if background_color != 'white':
        img = ImageOps.invert(img)
        
    '''
    Autocontrast: due to some threshold values, it's important that the blacks will be blacks and white will be whites.
    Box/MeanFilter: Allows us to reduce noise like bad a page scan or compression artifacts.
    Note: MedianFilter works better in my experience, but takes 2x-3x longer to perform.
    '''
    img = ImageOps.autocontrast(img, 1).filter(ImageFilter.BoxBlur(1))
    
    '''
    The 'power' parameters determines the threshold. The higher the power, the more "force" it can crop through black pixels (in case of white background)
    and the lower the power, more sensitive to black pixels. 
    '''
    threshold = threshold_from_power(power)
    bw_img = img.point(lambda p: 255 if p <= threshold else 0)

    return bw_img.getbbox()


'''
Groups close pixels together (x axis)
'''
def group_pixels(row, max_dist_tolerated, threshold):
    groups = []
    idx = np.where(row <= threshold)[0]

    group_start = -1
    group_end = 0
    for i in range(len(idx)):
        dist = idx[i] - group_end
        if group_start == -1:
            group_start = idx[i]
            group_end = idx[i]
        elif dist <= max_dist_tolerated:
            group_end = idx[i]
        else:
            groups.append((group_start, group_end))
            group_start = -1
            group_end = -1
            
    if group_start != -1:
        groups.append((group_start, group_end))
        
    return groups


def box_intersect(box1, box2, max_dist):
    return not (box2[0]-max_dist[0] > box1[1]
        or box2[1]+max_dist[0] < box1[0]
        or box2[2]-max_dist[1] > box1[3]
        or box2[3]+max_dist[1] < box1[2])

'''
Merge close bounding boxes (left,right, top,bot) (x axis) with distance threshold defined in
'max_dist_tolerated'. Boxes with less 'max_dist_tolerated' distance (Chebyshev distance).
'''
def merge_boxes(boxes, max_dist_tolerated):
    j = 0
    while j < len(boxes)-1:
        g1 = boxes[j]
        intersecting_boxes = []
        other_boxes = []
        for i in range(j+1,len(boxes)):
            g2 = boxes[i]
            if box_intersect(g1,g2, max_dist_tolerated):
                intersecting_boxes.append(g2)
            else:
                other_boxes.append(g2)
        
        if len(intersecting_boxes) > 0:
            intersecting_boxes = np.array([g1, *intersecting_boxes])
            merged_box = np.array([
                np.min(intersecting_boxes[:,0]), 
                np.max(intersecting_boxes[:,1]),
                np.min(intersecting_boxes[:,2]), 
                np.max(intersecting_boxes[:,3])
            ])
            other_boxes.append(merged_box)
            boxes = np.concatenate([boxes[:j], other_boxes])
            j = 0
        else:
            j += 1
    return boxes


def threshold_from_power(power):
    return 240-(power*64)