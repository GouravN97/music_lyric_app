from moviepy.video.tools.drawing import color_gradient
import sqlite3
import pickle
import ana2 
import moviepy as mp
import numpy as np
from typing import Dict, Tuple
import flash_fx_trial as flashfx
import zoom_fx,slide_fx,rotation_fx
import os
from PIL import Image, ImageDraw, ImageFont
import random

def get_picture_vid(duration):
    folder_path =  r'C:\Users\Gourav\music_app\miserybusiness_paramore'
    if not os.path.exists(folder_path):
        print(f"Folder not found: {folder_path}")
        return None
    
    image_extensions = ('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff')
    imgs=[]
    for filename in os.listdir(folder_path):
        if filename.lower().endswith(image_extensions):
            image_path = os.path.join(folder_path, filename)
            
            imgs.append(image_path)
        
    clip= random.choice([zoom_fx,slide_fx,rotation_fx]).create_clip(random.choice(imgs),duration=duration)
    
    clip.with_effects([mp.vfx.FadeOut(0.2)])            
    return clip

#def create_title_card():

def create_lyric_video_pil(audio_file: str, lyrics_with_timing: Dict[int, Tuple[str, float, float]], word_timings: Dict[int, Tuple[str, float, float]],
                          output_file: str = "lyric_video3.mp4"):
    """
    Alternative implementation using PIL for text rendering.
    This is more reliable on Windows systems.
    la  ma  ra    # top‑aligned left/middle/right
    lm  mm  rm    # vertically centered left/middle/right
    ld  md  rd    # bottom‑aligned left/middle/right

    """        
    # Load audio
    audio = mp.AudioFileClip(audio_file).subclipped(0,45)
    duration = audio.duration
    neighborhoods, stats, significant_transitions,timestamps=ana2.main_with_neighborhoods(audio_file)
    
    avg_dur=0.0
    avg_gap=0.0
    prev=0.0
    for i in range(len(word_timings)):
        avg_gap=avg_gap*i+(word_timings[i][1]-prev)
        avg_gap/=(i+1)
        avg_dur=avg_dur*i+(word_timings[i][2]-word_timings[i][1])
        avg_dur/=(i+1)
        prev=word_timings[i][2]

    
    #print("average gap=",avg_gap)
    #print("average duration =",avg_dur)

    def make_text_clip(text, start_time, duration, sentence_details, font_size=81, img_size=(1920, 1080)):
        """
        Creates a text clip that shows words appearing one by one
        
        Args:
            text: Full sentence text
            sentence_words: List of words in the sentence
            start_time: When sentence starts
            duration: Total sentence duration
            sentence_start_idx: Starting word index in word_timings for this sentence
            font_size: Font size
            img_size: Image dimensions
        
        Returns:
            MoviePy CompositeVideoClip with word-by-word animation
        """
        print(f"Creating word-by-word clip for: '{text}'")
        
        
        sentence_words=text.split()
        print(f"Words: {sentence_words}")
        try:
            font = ImageFont.truetype("GILLUBCD.ttf", font_size)
        except:
            print("Font GILLUBCD.ttf not found, using default font")
            font = ImageFont.load_default()
        
        # Find word timings for this sentence
        word_clips = []
        accumulated_text = ""        
        
        temp_img = Image.new('RGBA', img_size, (0, 0, 0, 0))
        temp_draw = ImageDraw.Draw(temp_img)
        bbox = temp_draw.multiline_textbbox((0, 0), text, font=font, align='center', spacing=24)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        print(sentence_details)

        #print(text_width)
        # Center position for consistent text placement
        base_x = (img_size[0] - text_width) // 2
        base_y = (img_size[1] - text_height) // 2
        
        for i, word in enumerate(sentence_words):
            # Build accumulated text (all words up to current word)
            if i == 0:
                accumulated_text = word
            else:
                accumulated_text += " " + word
            
            # Find timing for this word from word_timings
            word_start = sentence_details[i][1]
            word_end = sentence_details[i][2]
            
            # Create image with accumulated text
            img = Image.new('RGBA', img_size, (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            
            # Draw accumulated text
            draw.multiline_text((base_x, base_y), text=accumulated_text, font=font, fill='white', spacing=24, align='left')
            # Calculate clip duration - from when this word appears until sentence ends
            clip_start = word_start
            try:
                clip_duration =  sentence_details[i+1][1] - word_start 
            except:
                clip_duration = word_end - word_start
            
            if (clip_duration)>avg_dur+avg_gap:
                clip_duration=avg_dur+avg_gap
            
            if clip_duration > 0:
                word_clip = mp.ImageClip(np.array(img), duration=clip_duration).with_start(clip_start)
                word_clips.append(word_clip)
                print(f"Word '{word}' clip: start={clip_start:.2f}, duration={clip_duration:.2f}")
        
        if not word_clips:
            print("No word clips created, creating fallback")
            # Create a fallback clip with full text
            img = Image.new('RGBA', img_size, (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            draw.multiline_text((base_x, base_y), text=text, font=font, fill='white', spacing=24, align='center')
            fallback_clip = mp.ImageClip(np.array(img), duration=duration).with_start(start_time)
            return fallback_clip
        
        # Combine all word clips
        final_clip = mp.CompositeVideoClip(word_clips)
        return final_clip

    def make_text_clip_fade(text, words, start_time, duration, font_size=81, img_size=(1920, 1080), fade_duration=0.5):
        """
        Creates text clip with fade-in effect using MoviePy's TextClip with center alignment and auto line wrapping
        """
        # Build complete text with spaces
        s = " ".join(words)
        
        # Create fade-in clip using MoviePy's TextClip
        try:
            text_clip = (
                mp.TextClip(text=s, 
                           font_size=font_size, 
                           color='white', 
                           font='OLDENGL.ttf',
                           size=img_size,
                           method='caption')
                .with_duration(duration)
                .with_start(start_time)
                .with_position('center')
            )
            
            # Apply fade-in effect
            if fade_duration > 0:
                text_clip = text_clip.with_effects([mp.vfx.CrossFadeIn(fade_duration),mp.vfx.CrossFadeOut(fade_duration/2)])
            
            return text_clip
            
        except Exception as e:
            print(f"MoviePy TextClip failed: {e}, falling back to PIL method")
            # Fallback to PIL method if MoviePy TextClip fails
            return make_text_clip_fade_pil(text, words, start_time, duration, font_size, img_size, fade_duration)
    
    def make_text_clip_fade_pil(text, words, start_time, duration, font_size=81, img_size=(1920, 1080), fade_duration=0.5):
        """
        Fallback PIL method with automatic line wrapping and center alignment
        """
        from PIL import Image, ImageDraw, ImageFont
        import textwrap
        
        font = ImageFont.truetype("GILLUBCD.ttf", font_size)
        
        # Build complete text
        s = " ".join(words)
        
        # Calculate max characters per line based on image width and font
        avg_char_width = font.getbbox('A')[2]  # Approximate character width
        max_chars_per_line = int((img_size[0] * 0.8) // avg_char_width)  # Use 80% of screen width
        
        # Wrap text automatically
        wrapped_lines = textwrap.wrap(s, width=max_chars_per_line)
        wrapped_text = '\n'.join(wrapped_lines)
        
        # Create fade frames
        fade_frames = []
        fade_steps = int(fade_duration * 24)  # 24 fps
        
        for step in range(fade_steps):
            alpha = int(255 * (step / max(1, fade_steps - 1)))
            
            img = Image.new('RGBA', img_size, (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            
            # Get text dimensions for centering
            bbox = draw.multiline_textbbox((0, 0), wrapped_text, font=font, align='center', spacing=24)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            # Center the text
            x = (img_size[0] - text_width) // 2
            y = (img_size[1] - text_height) // 2
            
            # Draw text with alpha
            color = (255, 255, 255, alpha)
            draw.multiline_text((x, y), wrapped_text, font=font, fill=color, spacing=24, align='center')
            
            fade_frames.append(np.array(img))
        
        # Create final full opacity frame
        final_img = Image.new('RGBA', img_size, (0, 0, 0, 0))
        final_draw = ImageDraw.Draw(final_img)
        
        # Get text dimensions for centering
        bbox = final_draw.multiline_textbbox((0, 0), wrapped_text, font=font, align='center', spacing=24)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        # Center the text
        x = (img_size[0] - text_width) // 2
        y = (img_size[1] - text_height) // 2
        
        final_draw.multiline_text((x, y), wrapped_text, font=font, fill='white', spacing=24, align='center')
        
        # Create fade-in clip followed by static clip
        frame_duration = fade_duration / fade_steps
        fade_clips = []
        
        for i, frame in enumerate(fade_frames):
            clip = mp.ImageClip(frame, duration=frame_duration, transparent=True).with_start(start_time + i * frame_duration)
            fade_clips.append(clip)
        
        # Add static clip for remaining duration
        static_duration = duration - fade_duration
        if static_duration > 0:
            static_clip = mp.ImageClip(np.array(final_img), duration=static_duration, transparent=True).with_start(start_time + fade_duration)
            fade_clips.append(static_clip)
        
        return mp.CompositeVideoClip(fade_clips)
    
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
    #SORT NEIGHBOURHOODS DICTIONARY
    bg_clips=[]
    c=0
    print(neighborhoods)

    for n in neighborhoods:
        print(c)
        print("end="+str(n['end_time']))
        
        if n['end_time']<45:
            bg1=get_picture_vid(n['duration']/2)
            bg1=bg1.with_start(n['start_time'])
            bg2=get_picture_vid(n['duration']/2)
            bg2=bg2.with_start(n['start_time']+n['duration']/2)
            #bg=mp.VideoClip(make_background,duration=n['duration']).with_start(n['start_time'])
            bg_clips.append(bg1)
            bg_clips.append(bg2)
            print("duration="+str(n['duration']))
        else:
            bg=mp.VideoClip(make_background,duration=45-n['start_time']).with_start(n['start_time'])
            print(45-n['start_time'])
            bg=bg.with_effects([mp.vfx.FadeOut(0.2)])
            bg_clips.append(bg)
            break
            
        #bg=bg.with_effects([mp.vfx.FadeOut(0.2)])
        
        c+=1
    #background = mp.VideoClip(make_background, duration=duration)

    # Create text clips using PIL
    text_clips = []
    
    print(f"Processing {len(lyrics_with_timing)} sentences")
    print(f"Word timings has {len(word_timings)} words")
    
    total_words=0
    # Process each sentence from lyrics_with_timing
    for sentence_idx in range(len(lyrics_with_timing)):
        if sentence_idx not in lyrics_with_timing:
            continue
            
        sentence_text, sentence_start_time, sentence_end_time = lyrics_with_timing[sentence_idx]
        sentence_duration = sentence_end_time - sentence_start_time
        
        print(f"\nProcessing sentence {sentence_idx}: '{sentence_text}'")
        print(f"Timing: {sentence_start_time} to {sentence_end_time} (duration: {sentence_duration})")
        
        # Find words that belong to this sentence based on timing
        sentence_words = sentence_text.split()
        sentence_word_timings = []
        
        for idx in range(total_words,total_words+len(sentence_words)):
            sentence_word_timings.append(word_timings[idx])

        total_words+=len(sentence_words)

        print(f"Found {len(sentence_words)} words for sentence: {sentence_words}")

        if sentence_end_time > duration:
            print(f"Skipping sentence ending at {sentence_end_time} (beyond duration {duration})")
            break
        
        if not sentence_words:
            print("No words found for sentence, skipping")
            continue
        
        # Create text clip for this sentence with word-by-word reveal
        print(sentence_word_timings)
        sentence_clip = make_text_clip(
            sentence_text,            
            sentence_start_time,
            sentence_duration,
            sentence_word_timings
        )
        
        if sentence_clip:
            text_clips.append(sentence_clip)
    
    print(f"\nCreated {len(text_clips)} text clips")
    
    # Combine everything
    myvideo = mp.CompositeVideoClip(bg_clips + text_clips)
    myvideo = myvideo.with_audio(audio)
    for stamp in timestamps:
        try:
            myvideo=flashfx.basic_flash_example(myvideo,stamp[1])
        except Exception as e:
            print(e)
        
    #myvideo.preview()
    # Write video
    myvideo.write_videofile(output_file,
                               fps=24,
                               bitrate='15000k',
                               codec='libx264',
                               audio_codec='aac',
                               temp_audiofile='temp-audio.m4a',
                               remove_temp=True,
                                ffmpeg_params=[
                                '-crf', '20',  
                                '-profile:v', 'high',
                                '-pix_fmt', 'yuv420p'
                            ])
    
    # Clean up
    audio.close()
    myvideo.close()
    
    return output_file


if __name__ == "__main__":
    name=input()
    conn=sqlite3.connect("lyricsdb2.db")
    c=conn.cursor()
    c.execute("SELECT data FROM records_pickled WHERE record_id = ? ",(name+"sentences",))
    row=c.fetchone()
    c.execute("SELECT data FROM records_pickled WHERE record_id = ? ",(name+"words",))
    word_timings=c.fetchone()

    if word_timings:
        dct={}
        dct=pickle.loads(word_timings[0])
        word_timings=dct

    restored={}
    if row:
        restored=pickle.loads(row[0])

    create_lyric_video_pil(name+".wav",lyrics_with_timing=restored,word_timings=word_timings)
