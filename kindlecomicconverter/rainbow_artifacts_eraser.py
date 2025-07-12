import numpy as np
from PIL import Image

def fourier_transform_image(img):
    """
    Performs a 2D Fourier transform on a PIL image.
    
    Args:
        img: PIL Image (can be color or grayscale)
    
    Returns:
        fft_result: Complex result of the 2D FFT
    """
    # Convert PIL image to NumPy array
    img_array = np.array(img)
    
    # Perform 2D Fourier transform
    fft_result = np.fft.fft2(img_array)
    
    return fft_result
    
def attenuate_diagonal_frequencies(fft_spectrum, freq_threshold=0.3, target_angle=135, 
                                 angle_tolerance=15, attenuation_factor=0.1):
    """
    Attenuates specific frequencies in the Fourier domain (optimized version).
    
    Args:
        fft_spectrum: Result of 2D Fourier transform (non-centered)
        freq_threshold: Frequency threshold in cycles/pixel (default: 0.3, theoretical max: 0.5)
        target_angle: Target angle in degrees (default: 135)
        angle_tolerance: Angular tolerance in degrees (default: 15)
        attenuation_factor: Attenuation factor (0.1 = 90% attenuation)
    
    Returns:
        np.ndarray: Modified FFT with applied attenuation (same format as input)
    """
    
    # Get dimensions
    height, width = fft_spectrum.shape
    
    # Create frequency grids in an optimized way
    freq_y = np.fft.fftfreq(height, d=1.0)
    freq_x = np.fft.fftfreq(width, d=1.0)
    
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
    
    # Optimize angular condition
    # Calculate both target angles at once
    target_angle_2 = (target_angle + 180) % 360
    
    # Create angular conditions in a vectorized way
    angle_condition = np.zeros_like(angles_deg, dtype=bool)
    
    # Process both angles simultaneously
    for angle in [target_angle, target_angle_2]:
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
        fft_spectrum[combined_condition] = 0
        return fft_spectrum
    elif attenuation_factor == 1:
        # Special case: no attenuation
        return fft_spectrum
    else:
        # General case: partial attenuation
        fft_spectrum[combined_condition] *= attenuation_factor
        return fft_spectrum

def inverse_fourier_transform_image(fft_spectrum):
    """
    Performs an inverse Fourier transform to reconstruct a PIL image.
    
    Args:
        fft_spectrum: Fourier transform result (complex array)
    
    Returns:
        PIL.Image: Reconstructed image
    """
    # Perform inverse Fourier transform
    img_reconstructed = np.fft.ifft2(fft_spectrum)
    
    # Take real part (eliminate imaginary artifacts due to numerical errors)
    img_reconstructed = np.real(img_reconstructed)
    
    # Normalize values between 0 and 255
    img_reconstructed = np.clip(img_reconstructed, 0, 255)
    img_reconstructed = img_reconstructed.astype(np.uint8)
    
    # Convert to PIL image
    pil_image = Image.fromarray(img_reconstructed, mode='L')
    
    return pil_image
    
import numpy as np
    
def erase_rainbow_artifacts(img):
    fft_spectrum = fourier_transform_image(img)
    clean_spectrum = attenuate_diagonal_frequencies(fft_spectrum)
    clean_image = inverse_fourier_transform_image(clean_spectrum)
    return clean_image