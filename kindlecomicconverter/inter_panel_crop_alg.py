from PIL import Image, ImageFilter, ImageOps
import numpy as np
from typing import Literal
from .common_crop import threshold_from_power, group_close_values


'''
Crops inter-panel empty spaces (ignores empty spaces near borders - for that use crop margins).

    Parameters:
            img (PIL image): A PIL image.
            direction (horizontal or vertical or both): To crop rows (horizontal), cols (vertical) or both.
            keep (float): Distance to keep between panels after cropping (in percentage relative to the original distance).
            background_color (string): 'white' for white background, anything else for black.
    Returns:
            img (PIL image): A PIL image after cropping empty sections.
'''
def crop_empty_inter_panel(img, direction: Literal["horizontal", "vertical", "both"], keep=0.04, background_color='white'):
    img_temp = img
    
    if img.mode != 'L':
        img_temp = ImageOps.grayscale(img)
        
    if background_color != 'white':
        img_temp = ImageOps.invert(img)
        
    img_mat = np.array(img)
    
    power = 1
    img_temp = ImageOps.autocontrast(img_temp, 1).filter(ImageFilter.BoxBlur(1))
    img_temp = img_temp.point(lambda p: 255 if p <= threshold_from_power(power) else 0)
    
    if direction in ["horizontal", "both"]:
        rows_idx_to_remove = empty_sections(img_temp, keep, horizontal=True)
        img_mat = np.delete(img_mat, rows_idx_to_remove, 0)
        
    if direction in ["vertical", "both"]:
        cols_idx_to_remove = empty_sections(img_temp, keep, horizontal=False)
        img_mat = np.delete(img_mat, cols_idx_to_remove, 1)

    return Image.fromarray(img_mat)


'''
Finds empty sections (excluding near borders).

    Parameters:
            img (PIL image): A PIL image.
            keep (float): Distance to keep between panels after cropping (in percentage relative to the original distance).
            horizontal (boolean): True to find empty rows, False to find empty columns.
    Returns:
            Itertable (list or NumPy array): indices of rows or columns to remove.
'''
def empty_sections(img, keep, horizontal=True):
    axis = 1 if horizontal else 0
    
    img_mat = np.array(img)
    img_mat_max = np.max(img_mat, axis=axis)
    img_mat_empty_idx = np.where(img_mat_max == 0)[0]
        
    empty_sections = group_close_values(img_mat_empty_idx, 1)
    sections_to_remove = []
    for section in empty_sections:
        if section[1] < img.size[1] * 0.99 and section[0] > img.size[1] * 0.01: # if not near borders
            sections_to_remove.append(section)
        
    if len(sections_to_remove) != 0:
        sections_to_remove_after_keep = [(int(x1+(keep/2)*(x2-x1)), int(x2-(keep/2)*(x2-x1))) for x1,x2 in sections_to_remove]
        idx_to_remove = np.concatenate([np.arange(x1, x2) for x1,x2 in sections_to_remove_after_keep])

        return idx_to_remove
    
    return []



