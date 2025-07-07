from moviepy.config import change_settings
change_settings({"IMAGEMAGICK_BINARY": None})

from moviepy.video.tools.drawing import color_gradient
import sqlite3
import pickle

import moviepy.editor as mp
import numpy as np
from typing import Dict, Tuple, Optional
import os

def create_lyric_video(audio_file: str, 
                      lyrics_with_timing: Dict[int, Tuple[str, float, float]], 
                      output_file: str = "lyric_video.mp4"):
    """
    Create a lyric video with synchronized text and audio.
    Fixed for Windows compatibility issues.
    
    Args:
        audio_file: Path to the audio file
        lyrics_with_timing: Dictionary with format:
            {0: ("Hello world", 0.00, 10.00), 1: ("This is a song", 10.00, 12.00)}
        output_file: Output video file path
    
    Returns:
        Path to the created video file
    """
    
    # Load audio
    audio = mp.AudioFileClip(audio_file)
    duration = audio.duration
    print(f"Audio duration: {duration:.2f} seconds")
    
    # Create background (gradient or solid color)
    def make_background(t):
        # Create animated gradient background
        width, height = 1920, 1080
        
        # Create gradient manually
        gradient = np.zeros((height, width, 3), dtype=np.uint8)
        
        # Animate colors based on time
        r1 = int(127 + 127 * np.sin(t * 0.5))
        g1 = int(127 + 127 * np.cos(t * 0.3))
        b1 = int(127 + 127 * np.sin(t * 0.7))
        
        r2 = int(127 + 127 * np.cos(t * 0.4))
        g2 = int(127 + 127 * np.sin(t * 0.6))
        b2 = int(127 + 127 * np.cos(t * 0.8))
        
        # Create horizontal gradient
        for x in range(width):
            ratio = x / width
            r = int(r1 * (1 - ratio) + r2 * ratio)
            g = int(g1 * (1 - ratio) + g2 * ratio)
            b = int(b1 * (1 - ratio) + b2 * ratio)
            gradient[:, x] = [r, g, b]
        
        return gradient
    
    background = mp.VideoClip(make_background, duration=duration)
    
    # Create text clips for each lyric
    text_clips = []
    
    for idx, (txt, start, end) in lyrics_with_timing.items():
        print(f"Creating text clip {idx}: '{txt}' ({start:.2f}s - {end:.2f}s)")
        
        try:
            # Method 1: Try with no font specified (uses default)
            clip = (
                mp.TextClip(txt,
                           fontsize=80,
                           color='white',
                           stroke_color='black',
                           stroke_width=3,
                           method='label')
                .set_start(start)
                .set_duration(end - start)
                .set_position('center')
                .crossfadein(0.3)
                .crossfadeout(0.3)
            )
            
        except Exception as e1:
            print(f"Method 1 failed: {e1}")
            try:
                # Method 2: Try with common Windows fonts
                clip = (
                    mp.TextClip(txt,
                               fontsize=80,
                               font='Arial',
                               color='white',
                               stroke_color='black',
                               stroke_width=3,
                               method='label')
                    .set_start(start)
                    .set_duration(end - start)
                    .set_position('center')
                    .crossfadein(0.3)
                    .crossfadeout(0.3)
                )
                
            except Exception as e2:
                print(f"Method 2 failed: {e2}")
                try:
                    # Method 3: Try with caption method instead of label
                    clip = (
                        mp.TextClip(txt,
                                   fontsize=80,
                                   color='white',
                                   method='caption',
                                   size=(1600, None))
                        .set_start(start)
                        .set_duration(end - start)
                        .set_position('center')
                        .crossfadein(0.3)
                        .crossfadeout(0.3)
                    )
                    
                except Exception as e3:
                    print(f"Method 3 failed: {e3}")
                    try:
                        # Method 4: Minimal TextClip
                        clip = (
                            mp.TextClip(txt, fontsize=80, color='white')
                            .set_start(start)
                            .set_duration(end - start)
                            .set_position('center')
                        )
                        
                    except Exception as e4:
                        print(f"All methods failed for text: '{txt}'. Error: {e4}")
                        # Skip this text clip and continue
                        continue
        
        text_clips.append(clip)
    
    if not text_clips:
        print("Warning: No text clips were created successfully!")
        return None
    
    print(f"Created {len(text_clips)} text clips successfully")
    
    # Combine everything
    final_video = mp.CompositeVideoClip([background] + text_clips)
    final_video = final_video.set_audio(audio)
    
    # Write video file
    print("Writing video file...")
    final_video.write_videofile(output_file,
                               fps=24,
                               codec='libx264',
                               audio_codec='aac',
                               temp_audiofile='temp-audio.m4a',
                               remove_temp=True)
    
    # Clean up
    audio.close()
    final_video.close()
    
    print(f"Video created successfully: {output_file}")
    return output_file
# Alternative function using PIL for text rendering (more reliable on Windows)
def create_lyric_video_pil(audio_file: str, 
                          lyrics_with_timing: Dict[int, Tuple[str, float, float]], 
                          output_file: str = "lyric_video.mp4"):
    """
    Alternative implementation using PIL for text rendering.
    This is more reliable on Windows systems.
    """
    from PIL import Image, ImageDraw, ImageFont
    
    # Load audio
    audio = mp.AudioFileClip(audio_file)
    duration = audio.duration
    
    def make_text_image(text, font_size=80, img_size=(1920, 1080)):
        """Create an image with text using PIL"""
        img = Image.new('RGBA', img_size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        try:
            # Try to use a system font
            font = ImageFont.truetype("arial.ttf", font_size)
        except:
            try:
                font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", font_size)
            except:
                # Fallback to default font
                font = ImageFont.load_default()
        
        # Get text dimensions
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        # Center the text
        x = (img_size[0] - text_width) // 2
        y = (img_size[1] - text_height) // 2
        
        # Draw text with outline
        outline_width = 3
        for dx in range(-outline_width, outline_width + 1):
            for dy in range(-outline_width, outline_width + 1):
                if dx != 0 or dy != 0:
                    draw.text((x + dx, y + dy), text, font=font, fill='black')
        
        # Draw main text
        draw.text((x, y), text, font=font, fill='white')
        
        return np.array(img)
    
    # Create background
    def make_background(t):
        width, height = 1920, 1080
        gradient = np.zeros((height, width, 3), dtype=np.uint8)
        
        # Simple animated gradient
        r1 = int(127 + 127 * np.sin(t * 0.5))
        g1 = int(127 + 127 * np.cos(t * 0.3))
        b1 = int(127 + 127 * np.sin(t * 0.7))
        
        r2 = int(127 + 127 * np.cos(t * 0.4))
        g2 = int(127 + 127 * np.sin(t * 0.6))
        b2 = int(127 + 127 * np.cos(t * 0.8))
        
        for x in range(width):
            ratio = x / width
            r = int(r1 * (1 - ratio) + r2 * ratio)
            g = int(g1 * (1 - ratio) + g2 * ratio)
            b = int(b1 * (1 - ratio) + b2 * ratio)
            gradient[:, x] = [r, g, b]
        
        return gradient
    
    background = mp.VideoClip(make_background, duration=duration)
    
    # Create text clips using PIL
    text_clips = []
    for idx, (txt, start, end) in lyrics_with_timing.items():
        print(f"Creating PIL text clip {idx}: '{txt}'")
        
        # Create text image
        text_img = make_text_image(txt)
        
        # Create video clip from image
        clip = (
            mp.ImageClip(text_img, duration=end-start, transparent=True)
            .set_start(start)
            .crossfadein(0.0)
            .crossfadeout(0.0)
        )
        
        text_clips.append(clip)
    
    # Combine everything
    final_video = mp.CompositeVideoClip([background] + text_clips)
    final_video = final_video.set_audio(audio)
    
    # Write video
    final_video.write_videofile(output_file,
                               fps=24,
                               codec='libx264',
                               audio_codec='aac',
                               temp_audiofile='temp-audio.m4a',
                               remove_temp=True)
    
    # Clean up
    audio.close()
    final_video.close()
    
    return output_file

# Advanced version with more effects
def create_fancy_lyric_video(audio_file, lyrics_with_timing, background_image=None):
    """More advanced version with background image and animations"""
    
    audio = mp.AudioFileClip(audio_file)
    duration = audio.duration
    
    # Background
    if background_image:
        # Use image background with zoom effect
        bg_img = (mp.ImageClip(background_image, duration=duration)
                 .resize(height=1080)
                 .set_position('center')
                 .resize(lambda t: 1 + 0.02*t))  # Slow zoom
        background = bg_img
    else:
        # Animated gradient
        def make_gradient(t):
            return color_gradient((1920, 1080), 
                                [int(100 + 155 * np.sin(t * 0.1)), 50, 150],
                                [50, int(100 + 155 * np.cos(t * 0.15)), 200])
        background = mp.VideoClip(make_gradient, duration=duration)
    
    text_clips = []
    
    for i, lyric in enumerate(lyrics_with_timing):
        # Alternating positions for variety
        position = 'center' if i % 2 == 0 else ('center', 300)
        
        text_clip = (mp.TextClip(lyric["text"],
                                fontsize=90,
                                color='white',
                                font='Arial-Bold',
                                stroke_color='black',
                                stroke_width=4)
                    .set_position(position)
                    .set_start(lyric["start"])
                    .set_duration(lyric["end"] - lyric["start"])
                    .crossfadein(0.5)
                    .crossfadeout(0.5)
                    .resize(lambda t: 1 + 0.1 * np.sin(10 * t)))  # Pulsing effect
        
        text_clips.append(text_clip)
    
    final_video = mp.CompositeVideoClip([background] + text_clips)
    final_video = final_video.set_audio(audio)
    
    return final_video

# Quick LRC parser
'''
def parse_lrc_file(lrc_file):
    """Parse .lrc lyric files"""
    lyrics = []
    with open(lrc_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    for line in lines:
        if line.startswith('[') and ']' in line:
            try:
                time_part = line.split(']')[0][1:]  # Remove [ and ]
                text_part = line.split(']')[1].strip()
                
                if ':' in time_part and text_part:
                    minutes, seconds = time_part.split(':')
                    start_time = int(minutes) * 60 + float(seconds)
                    lyrics.append({"text": text_part, "start": start_time})
            except:
                continue
    
    # Calculate end times
    for i in range(len(lyrics) - 1):
        lyrics[i]["end"] = lyrics[i + 1]["start"]
    
    if lyrics:
        lyrics[-1]["end"] = lyrics[-1]["start"] + 3  # Last line duration
    
    return lyrics
'''
if __name__ == "__main__":

    conn=sqlite3.connect("lyricsdb.db")
    c=conn.cursor()
    c.execute("SELECT data FROM records_pickled WHERE record_id = ? ",("GORILLAZ_RHINESTONEEYES",))
    row=c.fetchone()
    restored={}
    if row:
        restored=pickle.loads(row[0])
    create_lyric_video_pil("audio.wav",lyrics_with_timing=restored)
