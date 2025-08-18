import numpy as np
import moviepy as mp
from moviepy import VideoFileClip
import random

def create_film_grain(clip, intensity=0.3):
    """Add film grain effect to the video"""
    def add_grain(frame):
        h, w = frame.shape[:2]
        
        # Create random noise
        noise = np.random.normal(0, intensity * 255, (h, w, 3))
        
        # Add grain with different intensities for each channel
        grainy_frame = frame.astype(np.float64) + noise
        
        # Clip values to valid range
        grainy_frame = np.clip(grainy_frame, 0, 255).astype(np.uint8)
        
        return grainy_frame
    
    return clip.fl_image(add_grain)

def create_scratches(clip, num_scratches=3):
    """Add vertical scratches that appear randomly"""
    def add_scratches(frame):
        frame = frame.copy()
        h, w = frame.shape[:2]
        
        # Randomly decide if scratches appear in this frame
        if random.random() < 0.3:  # 30% chance of scratches per frame
            for _ in range(random.randint(1, num_scratches)):
                # Random vertical position and thickness
                x_pos = random.randint(0, w-1)
                thickness = random.randint(1, 3)
                
                # Create scratch (bright line)
                scratch_value = random.randint(200, 255)
                
                # Add some randomness to make it look more natural
                for y in range(h):
                    if random.random() < 0.8:  # 80% chance for each pixel
                        x_start = max(0, x_pos - thickness//2)
                        x_end = min(w, x_pos + thickness//2 + 1)
                        frame[y, x_start:x_end] = [scratch_value, scratch_value, scratch_value]
        
        return frame
    
    return clip.fl_image(add_scratches)

def create_vignette(clip, strength=0.4):
    """Add dark vignette effect around edges"""
    def add_vignette(frame):
        h, w = frame.shape[:2]
        
        # Create coordinate arrays
        y, x = np.ogrid[:h, :w]
        center_x, center_y = w // 2, h // 2
        
        # Calculate distance from center
        max_dist = np.sqrt(center_x**2 + center_y**2)
        dist = np.sqrt((x - center_x)**2 + (y - center_y)**2)
        
        # Create vignette mask
        vignette = 1 - (dist / max_dist) * strength
        vignette = np.clip(vignette, 0, 1)
        
        # Apply vignette
        vignette_3d = np.stack([vignette] * 3, axis=2)
        vignetted_frame = frame * vignette_3d
        
        return vignetted_frame.astype(np.uint8)
    
    return clip.fl_image(add_vignette)

def create_dust_spots(clip, num_spots=5, spot_size=3):
    """Add random dust spots and artifacts"""
    def add_dust(frame):
        frame = frame.copy()
        h, w = frame.shape[:2]
        
        # Randomly add dust spots
        if random.random() < 0.2:  # 20% chance of dust per frame
            for _ in range(random.randint(1, num_spots)):
                x = random.randint(spot_size, w - spot_size)
                y = random.randint(spot_size, h - spot_size)
                size = random.randint(1, spot_size)
                
                # Dark or light spots
                spot_color = random.choice([0, 255])
                
                # Create circular dust spot
                for dy in range(-size, size + 1):
                    for dx in range(-size, size + 1):
                        if dx*dx + dy*dy <= size*size:
                            if 0 <= y+dy < h and 0 <= x+dx < w:
                                frame[y+dy, x+dx] = [spot_color, spot_color, spot_color]
        
        return frame
    
    return clip.fl_image(add_dust)

def create_color_degradation(clip, sepia_strength=0.3, contrast_reduction=0.2):
    """Add color degradation and sepia tone"""
    def degrade_color(frame):
        frame = frame.astype(np.float64)
        
        # Reduce contrast
        frame = frame * (1 - contrast_reduction) + 128 * contrast_reduction
        
        # Add sepia tone
        sepia_matrix = np.array([
            [0.393, 0.769, 0.189],
            [0.349, 0.686, 0.168],
            [0.272, 0.534, 0.131]
        ])
        
        # Apply sepia transformation
        original_shape = frame.shape
        frame_flat = frame.reshape(-1, 3)
        sepia_frame = frame_flat @ sepia_matrix.T
        sepia_frame = sepia_frame.reshape(original_shape)
        
        # Blend with original
        frame = frame * (1 - sepia_strength) + sepia_frame * sepia_strength
        
        return np.clip(frame, 0, 255).astype(np.uint8)
    
    return clip.fl_image(degrade_color)

def create_frame_jitter(clip, jitter_strength=2):
    """Add slight frame jitter/shake"""
    def add_jitter(frame):
        # Random offset
        offset_x = random.randint(-jitter_strength, jitter_strength)
        offset_y = random.randint(-jitter_strength, jitter_strength)
        
        h, w = frame.shape[:2]
        
        # Create shifted frame
        shifted_frame = np.zeros_like(frame)
        
        # Calculate source and destination slices
        src_y1 = max(0, -offset_y)
        src_y2 = min(h, h - offset_y)
        src_x1 = max(0, -offset_x)
        src_x2 = min(w, w - offset_x)
        
        dst_y1 = max(0, offset_y)
        dst_y2 = min(h, h + offset_y)
        dst_x1 = max(0, offset_x)
        dst_x2 = min(w, w + offset_x)
        
        # Copy the shifted portion
        shifted_frame[dst_y1:dst_y2, dst_x1:dst_x2] = frame[src_y1:src_y2, src_x1:src_x2]
        
        return shifted_frame
    
    return clip.fl_image(add_jitter)

# Alternative approach if fl_image still doesn't work
def manual_frame_processing(clip, effect_function):
    """Manual frame-by-frame processing as fallback"""
    def make_frame(t):
        frame = clip.get_frame(t)
        return effect_function(frame)
    
    from moviepy import VideoClip
    return VideoClip(make_frame, duration=clip.duration)

def apply_old_film_effect(input_path, output_path, **kwargs):
    """
    Apply complete old film effect to a video
    
    Parameters:
    - input_path: path to input video
    - output_path: path to output video
    - grain_intensity: film grain strength (default: 0.3)
    - num_scratches: number of scratches (default: 3)
    - vignette_strength: vignette darkness (default: 0.4)
    - sepia_strength: sepia tone strength (default: 0.3)
    - jitter_strength: frame shake strength (default: 2)
    - dust_spots: number of dust spots (default: 5)
    """
    
    # Default parameters
    grain_intensity = kwargs.get('grain_intensity', 0.3)
    num_scratches = kwargs.get('num_scratches', 3)
    vignette_strength = kwargs.get('vignette_strength', 0.4)
    sepia_strength = kwargs.get('sepia_strength', 0.3)
    jitter_strength = kwargs.get('jitter_strength', 2)
    dust_spots = kwargs.get('dust_spots', 5)
    
    # Load video
    print("Loading video...")
    clip = VideoFileClip(input_path)
    
    try:
        # Try using fl_image method
        print("Applying film grain...")
        clip = create_film_grain(clip, intensity=grain_intensity)
        
        print("Adding scratches...")
        clip = create_scratches(clip, num_scratches=num_scratches)
        
        print("Adding vignette...")
        clip = create_vignette(clip, strength=vignette_strength)
        
        print("Adding dust spots...")
        clip = create_dust_spots(clip, num_spots=dust_spots)
        
        print("Applying color degradation...")
        clip = create_color_degradation(clip, sepia_strength=sepia_strength)
        
        print("Adding frame jitter...")
        clip = create_frame_jitter(clip, jitter_strength=jitter_strength)
        
    except AttributeError as e:
        print(f"fl_image method not available: {e}")
        print("Using alternative manual processing method...")
        
        # Combined effect function for manual processing
        def combined_effect(frame):
            # Apply all effects in sequence
            frame = frame.copy()
            h, w = frame.shape[:2]
            
            # Film grain
            noise = np.random.normal(0, grain_intensity * 255, (h, w, 3))
            frame = frame.astype(np.float64) + noise
            frame = np.clip(frame, 0, 255).astype(np.uint8)
            
            # Scratches
            if random.random() < 0.3:
                for _ in range(random.randint(1, num_scratches)):
                    x_pos = random.randint(0, w-1)
                    thickness = random.randint(1, 3)
                    scratch_value = random.randint(200, 255)
                    
                    for y in range(h):
                        if random.random() < 0.8:
                            x_start = max(0, x_pos - thickness//2)
                            x_end = min(w, x_pos + thickness//2 + 1)
                            frame[y, x_start:x_end] = [scratch_value, scratch_value, scratch_value]
            
            # Vignette
            y, x = np.ogrid[:h, :w]
            center_x, center_y = w // 2, h // 2
            max_dist = np.sqrt(center_x**2 + center_y**2)
            dist = np.sqrt((x - center_x)**2 + (y - center_y)**2)
            vignette = 1 - (dist / max_dist) * vignette_strength
            vignette = np.clip(vignette, 0, 1)
            vignette_3d = np.stack([vignette] * 3, axis=2)
            frame = frame * vignette_3d
            
            # Dust spots
            if random.random() < 0.2:
                for _ in range(random.randint(1, dust_spots)):
                    x = random.randint(3, w - 3)
                    y = random.randint(3, h - 3)
                    size = random.randint(1, 3)
                    spot_color = random.choice([0, 255])
                    
                    for dy in range(-size, size + 1):
                        for dx in range(-size, size + 1):
                            if dx*dx + dy*dy <= size*size:
                                if 0 <= y+dy < h and 0 <= x+dx < w:
                                    frame[y+dy, x+dx] = [spot_color, spot_color, spot_color]
            
            # Color degradation and sepia
            frame = frame.astype(np.float64)
            frame = frame * (1 - 0.2) + 128 * 0.2  # contrast reduction
            
            sepia_matrix = np.array([
                [0.393, 0.769, 0.189],
                [0.349, 0.686, 0.168],
                [0.272, 0.534, 0.131]
            ])
            
            original_shape = frame.shape
            frame_flat = frame.reshape(-1, 3)
            sepia_frame = frame_flat @ sepia_matrix.T
            sepia_frame = sepia_frame.reshape(original_shape)
            frame = frame * (1 - sepia_strength) + sepia_frame * sepia_strength
            
            # Frame jitter
            offset_x = random.randint(-jitter_strength, jitter_strength)
            offset_y = random.randint(-jitter_strength, jitter_strength)
            
            shifted_frame = np.zeros_like(frame)
            src_y1 = max(0, -offset_y)
            src_y2 = min(h, h - offset_y)
            src_x1 = max(0, -offset_x)
            src_x2 = min(w, w - offset_x)
            dst_y1 = max(0, offset_y)
            dst_y2 = min(h, h + offset_y)
            dst_x1 = max(0, offset_x)
            dst_x2 = min(w, w + offset_x)
            
            shifted_frame[dst_y1:dst_y2, dst_x1:dst_x2] = frame[src_y1:src_y2, src_x1:src_x2]
            
            return np.clip(shifted_frame, 0, 255).astype(np.uint8)
        
        clip = manual_frame_processing(clip, combined_effect)
    
    # Write output
    print("Rendering video...")
    clip.write_videofile(
        output_path,
        fps=24,
        codec='libx264',
        audio_codec='aac'
    )
    
    print(f"Old film effect applied! Output saved to: {output_path}")
    
    # Close clip to free memory
    clip.close()

# Example usage
if __name__ == "__main__":
    # Basic usage
    apply_old_film_effect("sliding_clip.mp4", "output_old_film.mp4")
    
    # Custom parameters for more intense effect
    '''
    apply_old_film_effect(
        "sliding_clip.mp4", 
        "output_intense_old_film.mp4",
        grain_intensity=0.5,
        num_scratches=5,
        vignette_strength=0.6,
        sepia_strength=0.5,
        jitter_strength=3,
        dust_spots=8
    )
    
    # Subtle effect
    apply_old_film_effect(
        "sliding_clip.mp4", 
        "output_subtle_old_film.mp4",
        grain_intensity=0.1,
        num_scratches=1,
        vignette_strength=0.2,
        sepia_strength=0.1,
        jitter_strength=1,
        dust_spots=2
    )
    '''