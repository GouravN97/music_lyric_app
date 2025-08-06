import moviepy as mp
from moviepy import *
import math
from PIL import Image, ImageFilter
import numpy as np
from scipy.ndimage import gaussian_filter


def fall_effect_advanced(clip, start_zoom=0.05, end_zoom=1.0, add_blur=True, easing='ease_out', rotation_degrees=60):
    """
    Creates falling effect: starts as tiny dot, zooms in to center with rotation
    
    Args:
        rotation_degrees: Total degrees to rotate during the animation (default: 45)
                         Positive values rotate clockwise, negative counter-clockwise
    """
    
    # Easing functions
    def ease_out_cubic(t):
        return 1 - math.pow(1 - t, 3)
    
    def ease_in_out_sine(t):
        return 0.5 * (1 - math.cos(t * math.pi))
    
    def ease_in_cubic(t):
        return t * t * t
    
    def ease_in_square(t):
        return t*t
    
    def linear(t):
        return t
    
    # Choose easing function
    easing_funcs = {
        'ease_out': ease_out_cubic,
        'ease_in_out': ease_in_out_sine,
        'ease_in': ease_in_cubic,
        'linear': linear,
        'square':ease_in_square
    }
    ease_func = easing_funcs.get(easing, ease_out_cubic)
    
    def effect(get_frame, t):
        frame = get_frame(t)
        img = Image.fromarray(frame)
        base_size = img.size
        
        # Calculate progress (0 to 1 over clip duration)
        progress = t / clip.duration
        eased_progress = ease_func(progress)
        
        # Calculate current zoom level with easing (grows from tiny to normal)
        current_zoom = start_zoom + ((end_zoom - start_zoom) * eased_progress)
        
        # Calculate current rotation angle (linear progression)
        current_rotation = rotation_degrees * progress
        
        # Rotate the image first
        rotated_img = img.rotate(current_rotation, expand=True, fillcolor=(0, 0, 0))
        
        # Calculate new size based on zoom
        new_size = [
            max(2, math.ceil(rotated_img.size[0] * current_zoom)),
            max(2, math.ceil(rotated_img.size[1] * current_zoom))
        ]
        
        # Ensure even dimensions for video encoding
        new_size[0] = new_size[0] + (new_size[0] % 2)
        new_size[1] = new_size[1] + (new_size[1] % 2)
        
        # Resize image to new size
        resized_img = rotated_img.resize(new_size, Image.Resampling.LANCZOS)
        
        # Create black canvas of original size
        canvas = Image.new('RGB', base_size, (0, 0, 0))
        
        # Calculate position to center the resized image
        x = (base_size[0] - new_size[0]) // 2
        y = (base_size[1] - new_size[1]) // 2
        
        # Paste resized image onto center of canvas
        canvas.paste(resized_img, (x, y))
        
        # Convert to numpy array
        result = np.array(canvas)
        
        # Add motion blur if requested
        if add_blur and current_zoom < 0.8:  # Only blur when small/growing fast
            # Calculate blur strength based on zoom speed
            prev_t = max(0, t - 0.033)  # Previous frame (assuming 30fps)
            prev_progress = prev_t / clip.duration
            prev_eased = ease_func(prev_progress)
            prev_zoom = start_zoom + ((end_zoom - start_zoom) * prev_eased)
            
            zoom_speed = abs(current_zoom - prev_zoom) * 20
            blur_strength = min(zoom_speed, 2.0)  # Cap blur amount
            
            if blur_strength > 0.2:
                result = gaussian_filter(result, sigma=blur_strength)
                result = result.astype('uint8')
        
        img.close()
        rotated_img.close()
        resized_img.close()
        canvas.close()
        return result
    
    return clip.transform(effect)


def create_falling_fx(image_paths_list,duration):  
    
    slides = []
    target_size = (1920, 1080)
    
    for img_path in image_paths_list:
        try:
            # Create main clip with falling effect
            clip = mp.ImageClip(img_path, duration=duration)
            # Resize to target size first
            clip = clip.with_effects([vfx.Resize(target_size)])
            
            # Apply falling effect with rotation
            clip = fall_effect_advanced(
                clip, 
                start_zoom=0.2,        # Very tiny dot
                end_zoom=2.0,          # Normal size
                add_blur=True,
                easing='square',       # Accelerating growth
                rotation_degrees=30    # Rotate 30 degrees during animation
            )
            clip=clip.with_effects([vfx.FadeIn(0.3),vfx.FadeOut(0.3)])
            slides.append(clip)
            
        except Exception as e:
            print(f"Error processing {img_path}: {e}")
            continue

    final_video = mp.concatenate_videoclips(slides, method='compose')
    return final_video

    '''
    if slides:
        print(f"Creating video with {len(slides)} slides...")
        
        # Combine multiple clips
        final_video = mp.concatenate_videoclips(slides, method='compose')
        final_video.write_videofile(
            'falling_effect_with_rotation.mp4',
            fps=30,
            bitrate='15000k',
            codec='libx264',
            preset='slow',
            ffmpeg_params=[
                '-crf', '18',
                '-profile:v', 'high',
                '-pix_fmt', 'yuv420p'
            ]
        )
        
        print("Falling effect with rotation video created!")
        
        # Clean up
        final_video.close()
        for slide in slides:
            slide.close()
    else:
        print("No valid slides created!")
    '''


if __name__ == "__main__":
    create_falling_fx()