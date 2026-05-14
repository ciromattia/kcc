import numpy as np
from PIL import Image, ImageFile

ImageFile.LOAD_TRUNCATED_IMAGES = True

       
def fourier_transform_image(img):
    """
    Memory-optimized version that modifies the array in place when possible.
    """
    # Convert with minimal copy
    img_array = np.asarray(img, dtype=np.float32)
    
    # Use rfft2 if the image is real to save memory
    # and computation time (approximately 2x faster)
    fft_result = np.fft.rfft2(img_array)
    
    return fft_result
     
def attenuate_diagonal_frequencies(fft_spectrum, freq_threshold=0.30, target_angle=135, 
                                     angle_tolerance=10, attenuation_factor=0.10):
    """
    Attenuates specific frequencies in the Fourier domain (optimized version for rfft2).
    
    Args:
        fft_spectrum: Result of 2D real Fourier transform (from rfft2)
        freq_threshold: Frequency threshold in cycles/pixel (default: 0.3, theoretical max: 0.5)
        target_angle: Target angle in degrees (default: 135)
        angle_tolerance: Angular tolerance in degrees (default: 15)
        attenuation_factor: Attenuation factor (0.1 = 90% attenuation)
    
    Returns:
        np.ndarray: Modified FFT with applied attenuation (same format as input)
    """
    
    # Get dimensions of the rfft2 result
    if fft_spectrum.ndim == 2:
        height, width_rfft = fft_spectrum.shape
    else:  # 3D array (color channels)
        height, width_rfft = fft_spectrum.shape[:2]
    
    # For rfft2, the original width is (width_rfft - 1) * 2
    width_original = (width_rfft - 1) * 2
    
    # Create frequency grids for rfft2 format
    freq_y = np.fft.fftfreq(height, d=1.0)
    freq_x = np.fft.rfftfreq(width_original, d=1.0)  # Use rfftfreq for the X dimension
    
    
    # Use broadcasting to create grids without meshgrid (more efficient)
    freq_y_grid = freq_y.reshape(-1, 1)  # Column
    freq_x_grid = freq_x.reshape(1, -1)   # Row
    
    # Calculate squared radial frequencies (avoid sqrt)
    freq_radial_sq = freq_x_grid**2 + freq_y_grid**2
    freq_threshold_sq = freq_threshold**2
    
    # Frequency condition
    freq_condition = freq_radial_sq >= freq_threshold_sq
    
    # Early exit if no frequency satisfies the condition
    if not np.any(freq_condition):
        return fft_spectrum
    
    # Calculate angles only where necessary
    # Use atan2 directly with broadcasting
    angles_rad = np.arctan2(freq_y_grid, freq_x_grid)
    
    # Convert to degrees and normalize in a single operation
    angles_deg = np.rad2deg(angles_rad) % 360
    
    # Calculation of complementary angle
    target_angle_2 = (target_angle + 180) % 360
    
    # Calulation of perpendicular angles (135° + 45° to maximize compatibility until we know for sure which angle configure for each device)
    target_angle_3 = (target_angle + 90) % 360
    target_angle_4 = (target_angle_3 + 180) % 360
    
    # Create angular conditions in a vectorized way
    angle_condition = np.zeros_like(angles_deg, dtype=bool)
    
    # Process both angles simultaneously
    for angle in [target_angle, target_angle_2, target_angle_3, target_angle_4]:
        min_angle = (angle - angle_tolerance) % 360
        max_angle = (angle + angle_tolerance) % 360
        
        if min_angle > max_angle:  # Interval crosses 0°
            angle_condition |= (angles_deg >= min_angle) | (angles_deg <= max_angle)
        else:  # Normal interval
            angle_condition |= (angles_deg >= min_angle) & (angles_deg <= max_angle)
    
    # Combine conditions
    combined_condition = freq_condition & angle_condition
    
    # Apply attenuation directly (avoid creating a full mask)
    if attenuation_factor == 0:
        # Special case: complete suppression
        if fft_spectrum.ndim == 2:
            fft_spectrum[combined_condition] = 0
        else:  # 3D array
            fft_spectrum[combined_condition, :] = 0
        return fft_spectrum
    elif attenuation_factor == 1:
        # Special case: no attenuation
        return fft_spectrum
    else:
        # General case: partial attenuation
        if fft_spectrum.ndim == 2:
            fft_spectrum[combined_condition] *= attenuation_factor
        else:  # 3D array
            fft_spectrum[combined_condition, :] *= attenuation_factor
        return fft_spectrum
    
def inverse_fourier_transform_image(fft_spectrum, is_color, original_shape=None):
    """
    Performs an optimized inverse Fourier transform to reconstruct a PIL image.
    
    Args:
        fft_spectrum: Fourier transform result (complex array from rfft2)
        is_color: Boolean indicating if the image is to be treated as color
    
    Returns:
        PIL.Image: Reconstructed image
    """    
    # Perform inverse Fourier transform with original shape if provided
    if original_shape is not None:
        img_reconstructed = np.fft.irfft2(fft_spectrum, s=original_shape)
    else:
        img_reconstructed = np.fft.irfft2(fft_spectrum)
    
    # Normalize values between 0 and 255
    img_reconstructed = np.clip(img_reconstructed, 0, 255)
    img_reconstructed = img_reconstructed.astype(np.uint8)
    
    # Convert to PIL image
    if is_color and img_reconstructed.ndim == 3:
        pil_image = Image.fromarray(img_reconstructed, mode='RGB')
    else:
        pil_image = Image.fromarray(img_reconstructed, mode='L')
    
    return pil_image

def rgb_to_yuv(rgb_array):
    """
    Convert RGB to YUV color space.
    Y = luminance, U and V = chrominance
    """
    # Coefficients for RGB to YUV conversion
    rgb_to_yuv_matrix = np.array([
        [0.299, 0.587, 0.114],      # Y
        [-0.14713, -0.28886, 0.436],  # U
        [0.615, -0.51499, -0.10001]   # V
    ])
    
    # Reshape for matrix multiplication
    original_shape = rgb_array.shape
    rgb_flat = rgb_array.reshape(-1, 3)
    
    # Apply transformation
    yuv_flat = rgb_flat @ rgb_to_yuv_matrix.T
    
    # Reshape back
    yuv_array = yuv_flat.reshape(original_shape)
    
    return yuv_array

def yuv_to_rgb(yuv_array):
    """
    Convert YUV to RGB color space.
    """
    # Coefficients for YUV to RGB conversion
    yuv_to_rgb_matrix = np.array([
        [1.0, 0.0, 1.13983],         # R
        [1.0, -0.39465, -0.58060],   # G
        [1.0, 2.03211, 0.0]          # B
    ])
    
    # Reshape for matrix multiplication
    original_shape = yuv_array.shape
    yuv_flat = yuv_array.reshape(-1, 3)
    
    # Apply transformation
    rgb_flat = yuv_flat @ yuv_to_rgb_matrix.T
    
    # Reshape back
    rgb_array = rgb_flat.reshape(original_shape)
    
    return rgb_array

def erase_rainbow_artifacts(img, is_color):
    """
    Remove rainbow artifacts from grayscale or color images.
    
    Args:
        img: PIL Image (grayscale or RGB)
        is_color: Boolean indicating if the image is to be treated as color
    
    Returns:
        PIL.Image: Cleaned image
    """
    # Auto-detect color mode if not specified
    if is_color is None:
        color = img.mode in ('RGB', 'RGBA', 'L') and len(np.array(img).shape) == 3
    
    if is_color and img.mode in ('RGB', 'RGBA'):
        # Convert to RGB if needed
        if img.mode == 'RGBA':
            img = img.convert('RGB')
        
        # Convert to numpy array
        img_array = np.array(img, dtype=np.float32)
        
        # Convert to YUV color space
        yuv_array = rgb_to_yuv(img_array)
        
        # Extract luminance channel (Y)
        luminance = yuv_array[:, :, 0]
        
        # Process only the luminance channel
        fft_spectrum = fourier_transform_image(luminance)
        clean_spectrum = attenuate_diagonal_frequencies(fft_spectrum)
        clean_luminance = np.fft.irfft2(clean_spectrum, s=luminance.shape)
        
        # Normalize and clip luminance
        clean_luminance = np.clip(clean_luminance, 0, 255)
        
        # Replace luminance in YUV array
        yuv_array[:, :, 0] = clean_luminance
        
        # Convert back to RGB
        rgb_array = yuv_to_rgb(yuv_array)
        rgb_array = np.clip(rgb_array, 0, 255).astype(np.uint8)
        
        # Convert back to PIL image
        clean_image = Image.fromarray(rgb_array, mode='RGB')
        
    else:
        # Grayscale processing (original behavior)
        if img.mode != 'L':
            img = img.convert('L')

        # Get original image dimensions
        original_shape = (img.height, img.width)

        fft_spectrum = fourier_transform_image(img)
        clean_spectrum = attenuate_diagonal_frequencies(fft_spectrum)
        clean_image = inverse_fourier_transform_image(clean_spectrum, is_color, original_shape)
    
    return clean_image
