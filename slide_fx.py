from moviepy import ImageClip, CompositeVideoClip, ColorClip, vfx
import random
import numpy as np
import math
from PIL import Image

def apply_color_filter_to_image(image_array, red_factor=1.0, green_factor=1.0, blue_factor=1.0):
    """
    Apply color filter directly to a numpy image array
    """
    # Make a copy to avoid modifying original
    filtered_image = image_array.copy()
    
    # Apply color multiplication
    filtered_image[:, :, 0] = np.clip(filtered_image[:, :, 0] * red_factor, 0, 255)    # Red
    filtered_image[:, :, 1] = np.clip(filtered_image[:, :, 1] * green_factor, 0, 255)  # Green  
    filtered_image[:, :, 2] = np.clip(filtered_image[:, :, 2] * blue_factor, 0, 255)   # Blue
    
    return filtered_image.astype(np.uint8)

def apply_custom_rgb_filter(image_array, rgb_color, intensity=0.5, blend_mode='multiply'):
    """
    Apply a custom RGB color filter to the image
    
    Args:
        image_array: Input image as numpy array
        rgb_color: Tuple of (R, G, B) values (0-255)
        intensity: Filter intensity (0.0 to 1.0)
        blend_mode: 'multiply', 'overlay', 'screen', or 'color_dodge'
    """
    filtered_image = image_array.copy().astype(np.float32)
    r, g, b = rgb_color
    
    if blend_mode == 'multiply':
        # Multiply blend mode
        filter_layer = np.zeros_like(filtered_image)
        filter_layer[:, :, 0] = r
        filter_layer[:, :, 1] = g
        filter_layer[:, :, 2] = b
        
        # Normalize to 0-1 range for multiplication
        filtered_image = filtered_image / 255.0
        filter_layer = filter_layer / 255.0
        
        # Apply multiply blend
        blended = filtered_image * filter_layer
        
        # Mix with original based on intensity
        result = (1 - intensity) * filtered_image + intensity * blended
        
    elif blend_mode == 'overlay':
        # Overlay blend mode
        normalized_img = filtered_image / 255.0
        filter_color = np.array([r/255.0, g/255.0, b/255.0])
        
        # Overlay formula
        mask = normalized_img < 0.5
        overlay = np.where(mask, 
                          2 * normalized_img * filter_color,
                          1 - 2 * (1 - normalized_img) * (1 - filter_color))
        
        result = (1 - intensity) * normalized_img + intensity * overlay
        
    elif blend_mode == 'screen':
        # Screen blend mode
        normalized_img = filtered_image / 255.0
        filter_color = np.array([r/255.0, g/255.0, b/255.0])
        
        # Screen formula: 1 - (1-a) * (1-b)
        screen = 1 - (1 - normalized_img) * (1 - filter_color)
        result = (1 - intensity) * normalized_img + intensity * screen
        
    elif blend_mode == 'color_dodge':
        # Color dodge blend mode
        normalized_img = filtered_image / 255.0
        filter_color = np.array([r/255.0, g/255.0, b/255.0])
        
        # Avoid division by zero
        filter_color = np.where(filter_color >= 1.0, 0.999, filter_color)
        dodge = normalized_img / (1 - filter_color)
        dodge = np.clip(dodge, 0, 1)
        
        result = (1 - intensity) * normalized_img + intensity * dodge
    
    else:
        # Default to multiply if unknown mode
        result = filtered_image / 255.0
    
    return np.clip(result * 255, 0, 255).astype(np.uint8)

def calculate_angle_movement(angle_degrees, distance, screen_width, screen_height):
    """
    Calculate movement vector and bounds for any angle movement
    
    Args:
        angle_degrees (float): Angle in degrees (0-360)
        distance (float): Total distance to move
        screen_width (int): Width of the screen
        screen_height (int): Height of the screen
    
    Returns:
        tuple: (dx, dy, extra_width, extra_height) - movement vector and extra canvas needed
    """
    # Convert angle to radians
    angle_rad = math.radians(angle_degrees)
    
    # Calculate movement vector
    dx = math.cos(angle_rad) * distance
    dy = math.sin(angle_rad) * distance
    
    # Calculate extra canvas size needed for diagonal movements
    # This ensures the image doesn't get clipped during movement
    abs_dx = abs(dx)
    abs_dy = abs(dy)
    
    extra_width = int(abs_dx) if abs_dx > 0 else 0
    extra_height = int(abs_dy) if abs_dy > 0 else 0
    
    return dx, dy, extra_width, extra_height

def get_movement_distance_and_scale(image_width, image_height, screen_width, screen_height, 
                                  angle_degrees, movement_type='fit_height'):
    """
    Calculate optimal scaling and movement distance for the given angle
    
    Args:
        image_width, image_height: Original image dimensions
        screen_width, screen_height: Target screen dimensions
        angle_degrees: Movement angle in degrees
        movement_type: 'fit_height', 'fit_width', 'fill_screen', or 'contain'
    
    Returns:
        tuple: (scale_factor, movement_distance, new_width, new_height)
    """
    if movement_type == 'fit_height':
        scale_factor = screen_height / image_height
    elif movement_type == 'fit_width':
        scale_factor = screen_width / image_width
    elif movement_type == 'fill_screen':
        scale_factor = max(screen_width / image_width, screen_height / image_height)
    else:  # contain
        scale_factor = min(screen_width / image_width, screen_height / image_height)
    
    new_width = int(image_width * scale_factor)
    new_height = int(image_height * scale_factor)
    
    # Calculate movement distance based on angle and image size
    angle_rad = math.radians(angle_degrees)
    
    # For diagonal movements, we need more distance
    if new_width > screen_width:
        horizontal_distance = new_width - screen_width
    else:
        horizontal_distance = screen_width - new_width
    
    if new_height > screen_height:
        vertical_distance = new_height - screen_height
    else:
        vertical_distance = screen_height - new_height
    
    # Calculate required distance based on angle
    cos_val = abs(math.cos(angle_rad))
    sin_val = abs(math.sin(angle_rad))
    
    movement_distance = horizontal_distance * cos_val + vertical_distance * sin_val
    
    # Add some padding for smoother movement
    movement_distance += max(screen_width, screen_height) * 0.1
    
    return scale_factor, movement_distance, new_width, new_height

def create_angled_sliding_clip(image_path, duration, output_path="angled_sliding_clip.mp4", 
                             screen_width=1920, screen_height=1080, angle_degrees=0,
                             color_filter_type="none", custom_filter_rgb=None, filter_intensity=0.5,
                             filter_blend_mode='multiply', background_color=(0, 0, 0),
                             movement_type='fit_height', zoom_factor=1.0, reverse_direction=False):
    """
    Create a video clip from a still image with sliding pan effect at any angle.
    
    Args:
        image_path (str): Path to the input image
        duration (float): Duration of the clip in seconds
        output_path (str): Path for the output video file
        screen_width (int): Width of the output video
        screen_height (int): Height of the output video
        angle_degrees (float): Sliding angle in degrees (0-360)
                              0° = right, 90° = up, 180° = left, 270° = down
        color_filter_type (str): 'warm', 'cool', 'sepia', 'custom', or 'none'
        custom_filter_rgb (tuple): RGB color for custom filter (R, G, B) values 0-255
        filter_intensity (float): Intensity of the custom filter (0.0 to 1.0)
        filter_blend_mode (str): Blend mode for custom filter
        background_color (tuple): RGB background color (R, G, B) values 0-255
        movement_type (str): 'fit_height', 'fit_width', 'fill_screen', or 'contain'
        zoom_factor (float): Additional zoom factor (1.0 = no additional zoom)
        reverse_direction (bool): If True, reverses the movement direction
    
    Returns:
        VideoClip: The final video clip
    """
    
    # Load and process the image with PIL first
    pil_image = Image.open(image_path)
    
    # Convert to RGB if not already
    if pil_image.mode != 'RGB':
        pil_image = pil_image.convert('RGB')
    
    # Convert to numpy array
    image_array = np.array(pil_image)
    
    # Apply color filter to the image array
    if color_filter_type == "warm":
        image_array = apply_color_filter_to_image(image_array, red_factor=1.3, green_factor=1.1, blue_factor=0.8)
    elif color_filter_type == "cool":
        image_array = apply_color_filter_to_image(image_array, red_factor=0.8, green_factor=1.0, blue_factor=1.3)
    elif color_filter_type == "sepia":
        image_array = apply_color_filter_to_image(image_array, red_factor=1.2, green_factor=1.0, blue_factor=0.7)
    elif color_filter_type == "custom" and custom_filter_rgb is not None:
        image_array = apply_custom_rgb_filter(image_array, custom_filter_rgb, filter_intensity, filter_blend_mode)
    
    # Get original image dimensions
    img_height, img_width = image_array.shape[:2]
    
    # Calculate scaling and movement parameters
    scale_factor, movement_distance, new_width, new_height = get_movement_distance_and_scale(
        img_width, img_height, screen_width, screen_height, angle_degrees, movement_type)
    
    # Apply additional zoom factor
    scale_factor *= zoom_factor
    new_width = int(new_width * zoom_factor)
    new_height = int(new_height * zoom_factor)
    movement_distance *= zoom_factor
    
    # Create ImageClip from the filtered array
    img_clip = ImageClip(image_array, duration=duration)
    img_clip = img_clip.resized((new_width, new_height))
    
    # Calculate movement vector and canvas requirements
    dx, dy, extra_width, extra_height = calculate_angle_movement(
        angle_degrees, movement_distance, screen_width, screen_height)
    
    # Reverse direction if requested
    if reverse_direction:
        dx = -dx
        dy = -dy
    
    # Calculate starting and ending positions
    # Center the image initially, then apply movement
    center_x = (screen_width - new_width) // 2
    center_y = (screen_height - new_height) // 2
    
    # Calculate start and end positions with movement
    start_x = center_x - dx / 2
    start_y = center_y - dy / 2
    end_x = center_x + dx / 2
    end_y = center_y + dy / 2
    
    # Create the sliding animation function
    def get_position(t):
        progress = t / duration
        
        # Smooth easing function (ease-in-out)
        # Comment out the next line for linear movement
        progress = 0.5 * (1 - math.cos(progress * math.pi))
        
        current_x = start_x + (end_x - start_x) * progress
        current_y = start_y + (end_y - start_y) * progress
        
        return (current_x, current_y)
    
    # Apply position animation
    img_clip = img_clip.with_position(get_position)
    
    # Create colored background with extra size if needed
    canvas_width = screen_width + extra_width
    canvas_height = screen_height + extra_height
    
    bg_color_normalized = [c/255.0 for c in background_color]
    background = ColorClip(size=(canvas_width, canvas_height), 
                          color=bg_color_normalized, 
                          duration=duration)
    
    # Create final composite
    clip = CompositeVideoClip([background, img_clip], size=(screen_width, screen_height))
    
    return clip

def create_multi_angle_batch(image_path, duration, base_output_path, angles_list=None, 
                           screen_width=1920, screen_height=1080, **kwargs):
    """
    Create multiple clips with different angles in batch
    
    Args:
        image_path (str): Path to the input image
        duration (float): Duration of each clip
        base_output_path (str): Base path for output files (without extension)
        angles_list (list): List of angles to create. If None, creates 8 directions
        screen_width (int): Width of the output video
        screen_height (int): Height of the output video
        **kwargs: Additional parameters to pass to create_angled_sliding_clip
    """
    if angles_list is None:
        # Create 8 direction clips: right, down-right, down, down-left, left, up-left, up, up-right
        angles_list = [0, 45, 90, 135, 180, 225, 270, 315]
    
    angle_names = {
        0: "right", 45: "down_right", 90: "down", 135: "down_left",
        180: "left", 225: "up_left", 270: "up", 315: "up_right"
    }
    
    clips_created = []
    
    for angle in angles_list:
        angle_name = angle_names.get(angle, f"{angle}deg")
        output_path = f"{base_output_path}_{angle_name}.mp4"
        
        print(f"Creating clip for {angle}° ({angle_name})...")
        
        clip = create_angled_sliding_clip(
            image_path=image_path,
            duration=duration,
            output_path=output_path,
            screen_width=screen_width,
            screen_height=screen_height,
            angle_degrees=angle,
            **kwargs
        )
        
        clip.write_videofile(output_path, fps=24, codec='libx264', verbose=False, logger=None)
        clips_created.append(output_path)
        
        print(f"✓ Created: {output_path}")
    
    return clips_created

# Advanced color filters using matrix transformations (keeping original functions)
def apply_advanced_color_filter(image_array, filter_type="sepia", custom_rgb=None, intensity=0.5):
    """
    Apply advanced color filters using matrix transformations
    """
    filtered_image = image_array.copy().astype(np.float32)
    
    if filter_type == "sepia":
        # Sepia transformation matrix
        sepia_matrix = np.array([
            [0.393, 0.769, 0.189],
            [0.349, 0.686, 0.168],
            [0.272, 0.534, 0.131]
        ])
        # Reshape image for matrix multiplication
        h, w, c = filtered_image.shape
        filtered_image = filtered_image.reshape(-1, 3)
        filtered_image = np.dot(filtered_image, sepia_matrix.T)
        filtered_image = filtered_image.reshape(h, w, 3)
        
    elif filter_type == "vintage":
        # Vintage filter with reduced contrast and warm tint
        filtered_image = filtered_image * 0.8 + 30  # Reduce contrast, add warmth
        filtered_image[:, :, 0] *= 1.1  # Slight red boost
        filtered_image[:, :, 2] *= 0.9  # Slight blue reduction
        
    elif filter_type == "cold":
        # Cold/blue filter
        filtered_image[:, :, 0] *= 0.7  # Reduce red
        filtered_image[:, :, 1] *= 0.9  # Slightly reduce green
        filtered_image[:, :, 2] *= 1.3  # Boost blue
        
    elif filter_type == "dramatic":
        # High contrast dramatic look
        filtered_image = (filtered_image - 128) * 1.5 + 128  # Increase contrast
        filtered_image[:, :, 0] *= 1.1  # Slight red boost
        
    elif filter_type == "custom" and custom_rgb is not None:
        # Custom RGB filter
        return apply_custom_rgb_filter(image_array, custom_rgb, intensity)
    
    return np.clip(filtered_image, 0, 255).astype(np.uint8)

# Example usage and demonstrations
if __name__ == "__main__":
    image_path = "CD/cte6.jpg"
    duration = 4
    
    # Example 1: Single angled clip (45 degrees - diagonal down-right)
    print("Creating diagonal sliding clip (45°)...")
    clip = create_angled_sliding_clip(
        image_path=image_path,
        duration=duration,
        output_path="CD/diagonal_45deg_clip.mp4",
        angle_degrees=45,
        color_filter_type="custom",
        custom_filter_rgb=(255, 200, 150),  # Warm filter
        filter_intensity=0.4,
        filter_blend_mode='overlay',
        background_color=(20, 25, 35),
        movement_type='fit_height',
        zoom_factor=1.2
    )
    clip.write_videofile("CD/diagonal_45deg_clip.mp4", fps=24, codec='libx264')
