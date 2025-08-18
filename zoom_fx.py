import moviepy as mp
from moviepy import *
import math
from PIL import Image, ImageFilter
import numpy as np
from scipy.ndimage import gaussian_filter

def zoom_out_effect_advanced(clip, start_zoom=2.0, end_zoom=1.0, add_blur=True, easing='ease_out'):
    """
    Advanced zoom out effect with easing and optional motion blur
    """
    
    # Easing functions
    def ease_out_cubic(t):
        return 1 - math.pow(1 - t, 3)
    
    def ease_in_out_sine(t):
        return 0.5 * (1 - math.cos(t * math.pi))
    
    def linear(t):
        return t
    
    # Choose easing function
    easing_funcs = {
        'ease_out': ease_out_cubic,
        'ease_in_out': ease_in_out_sine,
        'linear': linear
    }
    ease_func = easing_funcs.get(easing, ease_out_cubic)
    
    def effect(get_frame, t):
        img = Image.fromarray(get_frame(t))
        
        # Convert to RGB if not already (FIX FOR MODE ERROR)
        if img.mode != 'RGB':
            print(f"Converting image from {img.mode} to RGB")
            img = img.convert('RGB')
        
        base_size = img.size
        
        # Calculate progress (0 to 1 over clip duration)
        progress = t / clip.duration
        eased_progress = ease_func(progress)
        
        # Calculate current zoom level with easing
        current_zoom = start_zoom - ((start_zoom - end_zoom) * eased_progress)
        
        # Calculate new size based on zoom
        new_size = [
            math.ceil(img.size[0] * current_zoom),
            math.ceil(img.size[1] * current_zoom)
        ]
        
        # Ensure even dimensions for video encoding
        new_size[0] = new_size[0] + (new_size[0] % 2)
        new_size[1] = new_size[1] + (new_size[1] % 2)
        
        # Resize to new size
        img = img.resize(new_size, Image.Resampling.LANCZOS)
        
        # Calculate crop coordinates to center the image
        x = math.ceil((new_size[0] - base_size[0]) / 2)
        y = math.ceil((new_size[1] - base_size[1]) / 2)
        
        # Crop from center and resize back to base size
        img = img.crop([
            x, y, 
            new_size[0] - x, 
            new_size[1] - y
        ]).resize(base_size, Image.Resampling.LANCZOS)
        
        # Convert to numpy array
        result = np.array(img)
        
        # Add motion blur if requested
        if add_blur:
            # Calculate blur strength based on zoom speed
            prev_t = max(0, t - 0.033)  # Previous frame (assuming 30fps)
            prev_progress = prev_t / clip.duration
            prev_eased = ease_func(prev_progress)
            prev_zoom = start_zoom - ((start_zoom - end_zoom) * prev_eased)
            
            zoom_speed = abs(current_zoom - prev_zoom) * 10
            blur_strength = min(zoom_speed, 1.5)  # Cap blur amount
            
            if blur_strength > 0.1:
                result = gaussian_filter(result, sigma=blur_strength)
                result = result.astype('uint8')
        
        img.close()
        return result
    
    return clip.transform(effect)

def create_clip(image_paths_list, duration, output_path='CD/high_quality_zoom1.mp4'):
    """
    Create a high-quality zoom video with all enhancements - FIXED for image mode errors
    """
    
    # Handle single image path
    if type(image_paths_list) != list:
        image_paths_list = [image_paths_list]
    
    # Validate inputs
    if not image_paths_list:
        print("Error: No image paths provided!")
        return None
    
    if duration <= 0:
        print("Error: Duration must be positive!")
        return None
        
    slides = []
    
    for i, img_path in enumerate(image_paths_list):
        try:
            print(f"Processing image {i+1}/{len(image_paths_list)}: {img_path}")
            
            # Verify image exists and can be opened
            try:
                test_img = Image.open(img_path)
                print(f"Original image mode: {test_img.mode}, size: {test_img.size}")
                test_img.close()
            except Exception as e:
                print(f"Cannot open image {img_path}: {e}")
                continue
            
            # Create main clip with zoom effect
            clip = mp.ImageClip(img_path, duration=duration)
            
            # Ensure clip has proper duration
            if clip.duration is None or clip.duration <= 0:
                clip = clip.with_duration(duration)
            
            clip = clip.with_effects([vfx.Resize((1080, 1080))])
            clip = zoom_out_effect_advanced(
                clip, 
                start_zoom=2.0,      
                end_zoom=1.0,
                add_blur=True,
                easing='ease_in_out'
            )
            
            # Create blurred background - FIX FOR MODE ERROR
            pil_image = Image.open(img_path)
            print(f"Background image original mode: {pil_image.mode}")
            
            # Convert to RGB BEFORE any operations
            if pil_image.mode != 'RGB':
                print(f"Converting background image from {pil_image.mode} to RGB")
                pil_image = pil_image.convert('RGB')
            
            # Apply blur and resize properly
            blurred_pil = pil_image.resize((1920, 1080), Image.Resampling.LANCZOS)
            
            # Now safe to apply Gaussian blur since we're in RGB mode
            try:
                blurred_pil = blurred_pil.filter(ImageFilter.GaussianBlur(radius=18))
                print("Gaussian blur applied successfully")
            except Exception as blur_error:
                print(f"Blur error: {blur_error}")
                print(f"Image mode before blur: {blurred_pil.mode}")
                # Fallback: try converting again or skip blur
                blurred_pil = blurred_pil.convert('RGB')
                blurred_pil = blurred_pil.filter(ImageFilter.GaussianBlur(radius=18))
            
            # Create background clip with proper duration
            bg_array = np.array(blurred_pil)
            bg = mp.ImageClip(bg_array, duration=duration)
            
            # Clean up PIL image
            pil_image.close()
            blurred_pil.close()
            
            # Composite: background first, then main clip on top
            composite_clip = mp.CompositeVideoClip([
                bg,  # Background layer (blurred)
                clip.with_position("center")  # Main clip centered on top
            ], size=(1920, 1080))  # Explicitly set size
            
            # Set duration explicitly for composite
            composite_clip = composite_clip.with_duration(duration)
            
            # Add fade effects
            composite_clip = composite_clip.with_effects([
                vfx.FadeIn(0.5),
                vfx.FadeOut(0.5)
            ])
            
            slides.append(composite_clip)
            print(f"Successfully processed image {i+1}")
            
        except Exception as e:
            print(f"Error processing {img_path}: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    # Debug: Check all clips have valid duration
    print(f"\nChecking {len(slides)} created clips:")
    valid_slides = []
    for i, slide in enumerate(slides):
        if hasattr(slide, 'duration') and slide.duration is not None and slide.duration > 0:
            print(f"Slide {i}: duration = {slide.duration} ✓")
            valid_slides.append(slide)
        else:
            print(f"Slide {i}: invalid duration = {getattr(slide, 'duration', 'None')} ✗")

    if not valid_slides:
        print("Error: No valid slides created!")
        return None
        
    print(f"\nCreating final video with {len(valid_slides)} valid slides...")
    
    try:
        # Handle single vs multiple clips
        if len(valid_slides) == 1:
            final_video = valid_slides[0]
        else:
            final_video = mp.concatenate_videoclips(valid_slides, method='compose')
        
        return final_video
        
    except Exception as e:
        print(f"Error creating final video: {e}")
        import traceback
        traceback.print_exc()
        return None

def create_and_save_clip(image_paths_list, duration, output_path='CD/high_quality_zoom1.mp4'):
    """
    Create and save the video clip
    """
    final_video = create_clip(image_paths_list, duration, output_path)
    
    if final_video is None:
        print("Failed to create video clip")
        return None
    
    try:
        final_video.write_videofile(
            output_path,
            fps=20,
            bitrate='8000k',
            codec='libx264',
            preset='slow',
            ffmpeg_params=[
                '-crf', '20',
                '-profile:v', 'high',
                '-pix_fmt', 'yuv420p'
            ]
        )
        
        print(f"High quality zoom video saved to: {output_path}")
        
        # Clean up
        final_video.close()
        return output_path
        
    except Exception as e:
        print(f"Error saving video: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == '__main__':
    # Example usage
    test_images = ["CD/cte4.jpg"]  # Replace with actual paths
    create_and_save_clip(test_images, duration=3.0)