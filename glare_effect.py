# Using base moviepy imports instead of moviepy.editor
from moviepy.video.io.ImageSequenceClip import ImageSequenceClip
from moviepy.video.VideoClip import ImageClip
from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip
from moviepy.video.fx.Resize import Resize
import random
import numpy as np
from PIL import Image
import math

def create_glare_effect(width, height, glare_width=200, glare_opacity=0.3, glare_angle=15):
    """
    Create a glare effect as a numpy array
    
    Args:
        width (int): Width of the glare effect
        height (int): Height of the glare effect
        glare_width (int): Width of the glare streak
        glare_opacity (float): Opacity of the glare (0-1)
        glare_angle (float): Angle of the glare in degrees
    
    Returns:
        numpy.ndarray: RGBA array with glare effect
    """
    # Create coordinate grids
    y, x = np.ogrid[:height, :width]
    
    # Convert angle to radians
    angle_rad = math.radians(glare_angle)
    
    # Calculate rotated coordinates
    x_rot = x * math.cos(angle_rad) + y * math.sin(angle_rad)
    
    # Create glare gradient (brightest in center, fading to edges)
    glare_center = width // 2
    distance_from_center = np.abs(x_rot - glare_center)
    
    # Create smooth falloff
    glare_mask = np.maximum(0, 1 - (distance_from_center / glare_width))
    
    # Apply smooth curve for more natural look
    glare_mask = np.power(glare_mask, 0.5)
    
    # Create RGBA array (white glare with alpha channel)
    glare_array = np.zeros((height, width, 4), dtype=np.uint8)
    glare_array[:, :, 0] = 255  # Red
    glare_array[:, :, 1] = 255  # Green  
    glare_array[:, :, 2] = 255  # Blue
    glare_array[:, :, 3] = (glare_mask * glare_opacity * 255).astype(np.uint8)  # Alpha
    
    return glare_array

def create_animated_glare_clip(width, height, duration, glare_speed=1.0, glare_width=200, 
                              glare_opacity=0.3, glare_angle=15):
    """
    Create an animated glare effect that moves across the screen
    
    Args:
        width (int): Width of the effect
        height (int): Height of the effect
        duration (float): Duration in seconds
        glare_speed (float): Speed multiplier for glare movement
        glare_width (int): Width of the glare streak
        glare_opacity (float): Opacity of the glare (0-1)
        glare_angle (float): Angle of the glare in degrees
    
    Returns:
        VideoClip: Animated glare effect clip
    """
    def make_frame(t):
        # Better looping calculation
        cycle_time = duration / max(glare_speed, 0.1)  # Prevent division by zero
        normalized_progress = (t % cycle_time) / cycle_time
        
        # Move glare from left to right across the screen
        glare_x_offset = int((width + glare_width * 2) * normalized_progress - glare_width)
        
        # Create coordinate grids
        y, x = np.ogrid[:height, :width]
        
        # Convert angle to radians
        angle_rad = math.radians(glare_angle)
        
        # Calculate rotated coordinates with offset
        x_rot = x * math.cos(angle_rad) + y * math.sin(angle_rad)
        
        # Calculate distance from glare center
        distance_from_center = np.abs(x_rot - glare_x_offset)
        
        # Create glare gradient
        glare_mask = np.maximum(0, 1 - (distance_from_center / glare_width))
        glare_mask = np.power(glare_mask, 0.5)
        
        # Create RGBA array
        glare_array = np.zeros((height, width, 4), dtype=np.uint8)
        glare_array[:, :, 0] = 255  # Red
        glare_array[:, :, 1] = 255  # Green  
        glare_array[:, :, 2] = 255  # Blue
        glare_array[:, :, 3] = (glare_mask * glare_opacity * 255).astype(np.uint8)  # Alpha
        
        return glare_array
    
    # Create the main clip and mask separately
    def make_rgb_frame(t):
        return make_frame(t)[:, :, :3]
    
    def make_mask_frame(t):
        return make_frame(t)[:, :, 3]
    
    # Create clip and mask
    clip = ImageClip(make_rgb_frame, duration=duration)
    mask = ImageClip(make_mask_frame, duration=duration, is_mask=True)
    
    return clip.set_mask(mask)

def create_lens_flare_effect(width, height, center_x, center_y, intensity=0.5):
    """
    Create a lens flare effect
    
    Args:
        width (int): Width of the effect
        height (int): Height of the effect
        center_x (int): X position of the flare center
        center_y (int): Y position of the flare center
        intensity (float): Intensity of the flare (0-1)
    
    Returns:
        numpy.ndarray: RGBA array with lens flare effect
    """
    y, x = np.ogrid[:height, :width]
    
    # Calculate distance from center
    distance = np.sqrt((x - center_x)**2 + (y - center_y)**2)
    
    # Create multiple circular flares of different sizes
    flare1 = np.exp(-(distance**2) / (2 * (50**2)))  # Main flare
    flare2 = np.exp(-(distance**2) / (2 * (100**2))) * 0.5  # Outer glow
    flare3 = np.exp(-(distance**2) / (2 * (20**2))) * 1.5  # Bright center
    
    # Combine flares
    combined_flare = np.clip(flare1 + flare2 + flare3, 0, 1)
    
    # Create RGBA array
    flare_array = np.zeros((height, width, 4), dtype=np.uint8)
    flare_array[:, :, 0] = 255  # Red
    flare_array[:, :, 1] = 255  # Green
    flare_array[:, :, 2] = 200  # Blue (slightly yellow tint)
    flare_array[:, :, 3] = (combined_flare * intensity * 255).astype(np.uint8)  # Alpha
    
    return flare_array

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

def create_sliding_image_clip(image_path, duration, output_path="sliding_clip.mp4", 
                            screen_width=1920, screen_height=1080, direction=None, 
                            color_filter_type="warm", add_glare=True, glare_type="sweep"):
    """
    Create a video clip from a still image with sliding pan effect and optional glare.
    
    Args:
        image_path (str): Path to the input image
        duration (float): Duration of the clip in seconds
        output_path (str): Path for the output video file
        screen_width (int): Width of the output video
        screen_height (int): Height of the output video
        direction (str): 'left' or 'right'. If None, chooses randomly
        color_filter_type (str): 'warm', 'cool', 'sepia', or 'none'
        add_glare (bool): Whether to add glare effect
        glare_type (str): 'sweep', 'pulse', 'lens_flare'
    
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
    
    # Apply resize effect
    img_clip = img_clip.fx(Resize, newsize=(new_width, new_height))
    
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
        progress = min(t / duration, 1.0)  # Prevent progress > 1
        current_x = start_pos + (end_pos - start_pos) * progress
        return (current_x, 0)
    
    # Apply position animation
    img_clip = img_clip.set_position(get_position)
    
    # Prepare clips list for composition
    clips_to_composite = [img_clip]
    
    # Add glare effect if requested
    if add_glare:
        if glare_type == "sweep":
            # Sweeping glare effect
            glare_clip = create_animated_glare_clip(
                screen_width, screen_height, duration,
                glare_speed=0.8,  # Speed of the glare sweep
                glare_width=150,  # Width of the glare
                glare_opacity=0.4,  # Opacity
                glare_angle=15    # Angle in degrees
            )
            clips_to_composite.append(glare_clip)
            
        elif glare_type == "pulse":
            # Pulsing glare effect in center
            def make_pulse_frame(t):
                # Create pulsing intensity
                pulse_intensity = 0.3 + 0.2 * math.sin(t * 2 * math.pi * 0.5)  # Pulse every 2 seconds
                return create_lens_flare_effect(
                    screen_width, screen_height,
                    screen_width // 2, screen_height // 2,
                    pulse_intensity
                )
            
            # Proper mask handling for pulse effect
            def make_pulse_rgb(t):
                return make_pulse_frame(t)[:, :, :3]
            
            def make_pulse_mask(t):
                return make_pulse_frame(t)[:, :, 3]
            
            pulse_clip = ImageClip(make_pulse_rgb, duration=duration)
            pulse_mask = ImageClip(make_pulse_mask, duration=duration, is_mask=True)
            pulse_clip = pulse_clip.set_mask(pulse_mask)
            clips_to_composite.append(pulse_clip)
            
        elif glare_type == "lens_flare":
            # Moving lens flare effect
            def make_flare_frame(t):
                # Move flare from one corner to another
                progress = min(t / duration, 1.0)  # Prevent progress > 1
                flare_x = int(screen_width * 0.2 + (screen_width * 0.6) * progress)
                flare_y = int(screen_height * 0.3 + (screen_height * 0.4) * progress)
                
                return create_lens_flare_effect(
                    screen_width, screen_height,
                    flare_x, flare_y,
                    0.6
                )
            
            # Proper mask handling for lens flare
            def make_flare_rgb(t):
                return make_flare_frame(t)[:, :, :3]
            
            def make_flare_mask(t):
                return make_flare_frame(t)[:, :, 3]
            
            flare_clip = ImageClip(make_flare_rgb, duration=duration)
            flare_mask = ImageClip(make_flare_mask, duration=duration, is_mask=True)
            flare_clip = flare_clip.set_mask(flare_mask)
            clips_to_composite.append(flare_clip)
    
    # Create final composite with black background
    clip = CompositeVideoClip(clips_to_composite, size=(screen_width, screen_height))
    
    # Write the video file
    clip.write_videofile(output_path, fps=24, codec='libx264')
    
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
                                     filter_type="sepia", add_glare=True, glare_type="sweep"):
    """
    Advanced version with matrix-based color filters and glare effects
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
    
    # Get dimensions and calculate scaling
    img_height, img_width = image_array.shape[:2]
    scale_factor = screen_height / img_height
    new_width = int(img_width * scale_factor)
    new_height = screen_height
    
    # Apply resize effect
    img_clip = img_clip.fx(Resize, newsize=(new_width, new_height))
    
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
        progress = min(t / duration, 1.0)  # Prevent progress > 1
        current_x = start_pos + (end_pos - start_pos) * progress
        return (current_x, 0)
    
    img_clip = img_clip.set_position(get_position)
    
    # Prepare clips for composition
    clips_to_composite = [img_clip]
    
    # Add glare effect if requested
    if add_glare:
        if glare_type == "sweep":
            glare_clip = create_animated_glare_clip(
                screen_width, screen_height, duration,
                glare_speed=1.2, glare_width=120, glare_opacity=0.5, glare_angle=20
            )
            clips_to_composite.append(glare_clip)
        elif glare_type == "double_sweep":
            # Two glares moving in opposite directions
            glare1 = create_animated_glare_clip(
                screen_width, screen_height, duration,
                glare_speed=0.8, glare_width=100, glare_opacity=0.3, glare_angle=15
            )
            
            # Create second glare with proper negative speed handling
            def make_reverse_glare_frame(t):
                # Reverse direction by flipping the progress calculation
                cycle_time = duration / 0.6
                normalized_progress = 1.0 - ((t % cycle_time) / cycle_time)
                
                glare_x_offset = int((screen_width + 80 * 2) * normalized_progress - 80)
                
                y, x = np.ogrid[:screen_height, :screen_width]
                angle_rad = math.radians(-10)
                x_rot = x * math.cos(angle_rad) + y * math.sin(angle_rad)
                distance_from_center = np.abs(x_rot - glare_x_offset)
                glare_mask = np.maximum(0, 1 - (distance_from_center / 80))
                glare_mask = np.power(glare_mask, 0.5)
                
                glare_array = np.zeros((screen_height, screen_width, 4), dtype=np.uint8)
                glare_array[:, :, 0] = 255
                glare_array[:, :, 1] = 255
                glare_array[:, :, 2] = 255
                glare_array[:, :, 3] = (glare_mask * 0.2 * 255).astype(np.uint8)
                
                return glare_array
            
            def make_reverse_rgb(t):
                return make_reverse_glare_frame(t)[:, :, :3]
            
            def make_reverse_mask(t):
                return make_reverse_glare_frame(t)[:, :, 3]
            
            glare2 = ImageClip(make_reverse_rgb, duration=duration)
            glare2_mask = ImageClip(make_reverse_mask, duration=duration, is_mask=True)
            glare2 = glare2.set_mask(glare2_mask)
            
            clips_to_composite.extend([glare1, glare2])
    
    clip = CompositeVideoClip(clips_to_composite, size=(screen_width, screen_height))
    
    clip.write_videofile(output_path, fps=24, codec='libx264')
    return clip

# Example usage
if __name__ == "__main__":
    image_path = "CD/cte.jpg"
    duration = 10
    output_path = "CD/sliding_clip.mp4"
    
    # Basic version with simple color filters and glare
    clip = create_sliding_image_clip(
        image_path=image_path,
        duration=duration,
        output_path=output_path,
        screen_width=1920,
        screen_height=1080,
        direction='left',
        color_filter_type="warm",  # "warm", "cool", "sepia", or "none"
        add_glare=True,           # Enable glare effect
        glare_type="lens_flare"        # "sweep", "pulse", "lens_flare"
    )
    
    print(f"Sliding clip created: {output_path}")
    print(f"Duration: {duration} seconds")
    print(f"Direction: sliding to the left")
    print(f"Glare effect: enabled (sweep type)")