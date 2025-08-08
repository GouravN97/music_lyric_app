from moviepy import ImageClip, CompositeVideoClip
import random
import numpy as np
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

def create_clip(image_path, duration, output_path="sliding_clip.mp4", 
                            screen_width=1920, screen_height=1080, direction=None, 
                            color_filter_type="warm"):
    """
    Create a video clip from a still image with sliding pan effect.
    
    Args:
        image_path (str): Path to the input image
        duration (float): Duration of the clip in seconds
        output_path (str): Path for the output video file
        screen_width (int): Width of the output video
        screen_height (int): Height of the output video
        direction (str): 'left' or 'right'. If None, chooses randomly
        color_filter_type (str): 'warm', 'cool', 'sepia', or 'none'
    
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
    # If color_filter_type == "none", no filter is applied
    
    # Create ImageClip from the filtered array
    img_clip = ImageClip(image_array, duration=duration)
    
    # Get image dimensions
    img_height, img_width = image_array.shape[:2]
    
    # Calculate scaling to fill screen height while maintaining aspect ratio
    scale_factor = screen_height / img_height
    new_width = int(img_width * scale_factor)
    new_height = screen_height
    
    # Resize the image
    img_clip = img_clip.resized((new_width, new_height))
    
    # Choose direction randomly if not specified
    if direction is None:
        direction = random.choice(['left', 'right'])
    
    # Calculate sliding parameters
    if new_width > screen_width:
        # Image is wider than screen - we can slide across the image content
        max_slide = new_width - screen_width
        
        if direction == 'left':
            start_pos = 0
            end_pos = -max_slide
        else:  # direction == 'right'
            start_pos = -max_slide
            end_pos = 0
    else:
        # Image is narrower than screen - slide the image itself across the screen
        max_slide = screen_width - new_width
        
        if direction == 'left':
            start_pos = max_slide
            end_pos = 0
        else:  # direction == 'right'
            start_pos = 0
            end_pos = max_slide
    
    # Create the sliding animation function
    def get_position(t):
        progress = t / duration
        current_x = start_pos + (end_pos - start_pos) * progress
        return (current_x, 0)
    
    # Apply position animation
    img_clip = img_clip.with_position(get_position)
    
    # Create final composite with black background
    clip = CompositeVideoClip([img_clip], size=(screen_width, screen_height))
    
    # Write the video file
    #clip.write_videofile(output_path, fps=24, codec='libx264')
    
    return clip

# Advanced color filters using matrix transformations
def apply_advanced_color_filter(image_array, filter_type="sepia"):
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
    
    return np.clip(filtered_image, 0, 255).astype(np.uint8)

def create_sliding_image_clip_advanced(image_path, duration, output_path="sliding_clip.mp4", 
                                     screen_width=1920, screen_height=1080, direction=None, 
                                     filter_type="sepia"):
    """
    Advanced version with matrix-based color filters
    """
    # Load and process the image
    pil_image = Image.open(image_path)
    if pil_image.mode != 'RGB':
        pil_image = pil_image.convert('RGB')
    
    image_array = np.array(pil_image)
    
    # Apply advanced color filter
    if filter_type != "none":
        image_array = apply_advanced_color_filter(image_array, filter_type)
    
    # Create ImageClip from the filtered array
    img_clip = ImageClip(image_array, duration=duration)
    
    # Rest of the function remains the same as the basic version
    img_height, img_width = image_array.shape[:2]
    scale_factor = screen_height / img_height
    new_width = int(img_width * scale_factor)
    new_height = screen_height
    
    img_clip = img_clip.resized((new_width, new_height))
    
    if direction is None:
        direction = random.choice(['left', 'right'])
    
    if new_width > screen_width:
        max_slide = new_width - screen_width
        if direction == 'left':
            start_pos = 0
            end_pos = -max_slide
        else:
            start_pos = -max_slide
            end_pos = 0
    else:
        max_slide = screen_width - new_width
        if direction == 'left':
            start_pos = max_slide
            end_pos = 0
        else:
            start_pos = 0
            end_pos = max_slide
    
    def get_position(t):
        progress = t / duration
        current_x = start_pos + (end_pos - start_pos) * progress
        return (current_x, 0)
    
    img_clip = img_clip.with_position(get_position)
    clip = CompositeVideoClip([img_clip], size=(screen_width, screen_height))
    
    clip.write_videofile(output_path, fps=24, codec='libx264')
    return clip

# Example usage
if __name__ == "__main__":
    image_path = "CD/cte.jpg"
    duration = 4
    output_path = "sliding_clip.mp4"
    
    # Basic version with simple color filters
    clip = create_clip(
        image_path=image_path,
        duration=duration,
        output_path=output_path,
        screen_width=1920,
        screen_height=1080,
        direction='left',
        color_filter_type="warm"  # "warm", "cool", "sepia", or "none"
    )
    clip.write_videofile(output_path, fps=24, codec='libx264')
    
    # Or use the advanced version with matrix-based filters
    # clip = create_sliding_image_clip_advanced(
    #     image_path=image_path,
    #     duration=duration,
    #     output_path="CD/advanced_sliding_clip.mp4",
    #     direction='left',
    #     filter_type="sepia"  # "sepia", "vintage", "cold", "dramatic", or "none"
    # )
    
    print(f"Sliding clip created: {output_path}")
    print(f"Duration: {duration} seconds")
    print(f"Direction: sliding to the left")
