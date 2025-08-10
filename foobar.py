from moviepy.video.tools.drawing import color_gradient
import sqlite3
import pickle
import ana3
import moviepy as mp
import numpy as np
from typing import Dict, Tuple
import flash_fx_trial as flashfx
import zoom_fx,slide_fx,rotation_fx
import os
from PIL import Image, ImageDraw, ImageFont
import random
import advanced_textfx as tfx
import classifying_lyrics,metadata_analysis

# Text effects functions from the second program
def random_blinking_effect(text, duration=3, size=(1920, 1080), fontsize=80, start_time=0):
    """
    Effect: Characters randomly appear in their final positions
    Modified to work with the lyric video system
    """
    # Create base transparent clip
    base = mp.ColorClip(size=size, color=(0, 0, 0), duration=duration, is_mask=False).with_opacity(0)
    
    # Get final text position
    try:
        final_text = mp.TextClip(text=text, font_size=fontsize, color='white', font='STENCIL.ttf')
    except:
        final_text = mp.TextClip(text=text, font_size=fontsize, color='white')
    
    final_x = (size[0] - final_text.w) // 2
    final_y = (size[1] - final_text.h) // 2
    
    clips = [base]
    
    # Create individual character clips
    for i, chr in enumerate(text):
        if chr == ' ':
            continue
            
        # Create character clip
        try:
            char_clip = mp.TextClip(text=chr, font_size=fontsize, color='white', font='STENCIL.ttf', duration=duration)
        except:
            char_clip = mp.TextClip(text=chr, font_size=fontsize, color='white', duration=duration)
        
        # Calculate final position for this character
        char_width = fontsize * 0.6  # Approximate character width
        target_x = final_x + (i * char_width)
        target_y = final_y
        
        # Random appearance time
        appear_time = random.uniform(0, duration * 0.8)
        
        # Set character to appear at random time in final position
        animated_char = char_clip.with_position((target_x, target_y)).with_start(start_time + appear_time)
        
        clips.append(animated_char)
    
    return mp.CompositeVideoClip(clips).with_start(start_time)

def random_character_appearance_effect(text, duration=3, size=(1920, 1080), fontsize=80, start_time=0):
    """
    Effect: Characters randomly appear and move to form the final word
    Modified to work with the lyric video system
    """
    # Create base transparent clip
    base = mp.ColorClip(size=size, color=(0, 0, 0), duration=duration, is_mask=False).with_opacity(0)
    
    # Get final text position
    try:
        final_text = mp.TextClip(text=text, font_size=fontsize, color='white', font='STENCIL.ttf')
    except:
        final_text = mp.TextClip(text=text, font_size=fontsize, color='white')
    
    final_x = (size[0] - final_text.w) // 2
    final_y = (size[1] - final_text.h) // 2
    
    clips = [base]
    
    # Create individual character clips
    for i, char in enumerate(text):
        if char == ' ':
            continue
            
        # Create character clip
        try:
            char_clip = mp.TextClip(text=char, font_size=fontsize, color='white', font='STENCIL.ttf', duration=duration)
        except:
            char_clip = mp.TextClip(text=char, font_size=fontsize, color='white', duration=duration)
        
        # Calculate final position for this character
        char_width = fontsize * 0.6  # Approximate character width
        target_x = final_x + (i * char_width)
        target_y = final_y
        
        # Random starting position
        start_x = random.randint(0, size[0] - char_clip.w)
        start_y = random.randint(0, size[1] - char_clip.h)
        
        # Random appearance time
        appear_time = random.uniform(0, duration * 0.3)
        move_duration = duration - appear_time
        
        # Position animation from random start to final position
        def make_pos_func(sx, sy, tx, ty, at, md):
            def pos_func(t):
                if t < at:
                    return (sx, sy)  # Stay at start position until appear time
                else:
                    # Smooth transition to target
                    progress = min((t - at) / md, 1)
                    # Ease-out animation
                    progress = 1 - (1 - progress) ** 3
                    x = sx + (tx - sx) * progress
                    y = sy + (ty - sy) * progress
                    return (x, y)
            return pos_func
        
        # Apply position animation
        animated_char = char_clip.with_position(
            make_pos_func(start_x, start_y, target_x, target_y, appear_time, move_duration)
        )
        
        clips.append(animated_char)
    
    return mp.CompositeVideoClip(clips).with_start(start_time)

def create_title_card_with_effects(artist="ARTIST", title="SONG TITLE", duration_each=3):
    """
    Creates title cards using the text effects from the second program
    """
    # Create title effect (random character appearance)
    title_effect = random_character_appearance_effect(title, duration=duration_each, fontsize=120)
    
    # Create artist effect (random blinking) - starts after title
    artist_effect = random_blinking_effect(artist, duration=duration_each, fontsize=80, start_time=duration_each)
    
    # Combine both effects
    title_card = mp.CompositeVideoClip([title_effect, artist_effect])
    
    return title_card

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

def get_sentence_timings(audio_file):
    #to visualise the classification
    #import metadata_analysis
    #high_intensity, df_analyzed = metadata_analysis.analyze_moving_average_above_thresholds('cigarettedaydreams_cagetheelephant_beats.csv')
    details=[]
    current=""
    with open(audio_file[:-4]+'.txt','r') as lyric_file:
        for i,line in enumerate(lyric_file.readlines()):
            if line.__contains__('[') :
                if   line.__contains__('Pre-Chorus'):
                    current='Pre-Chorus'
                elif line.__contains__('Chorus'):
                    current='Chorus'
                elif line.__contains__('Verse'):
                    current='Verse'
                elif line.__contains__('Bridge')  :
                    current='Bridge'
                    
                else:
                    pass
            else:
                if len(line)!=1:
                    details.append(current)
    lyric_file.close()
    #print(details)
    return details
    
        

def create_lyric_video_pil(audio_file: str, lyrics_with_timing: Dict[int, Tuple[str, float, float]], word_timings: Dict[int, Tuple[str, float, float]],
                          output_file: str = "lyric_video8.mp4", use_title_effects: bool = True):
   
    zoom_duration=0
    zoom_scale=4.0
    blur_intensity=1.5
    blur_duration=0.5
    duplicatefx=False
    dfx=False
    cyclefx=True
    def make_text_clip(text, start_time, duration, sentence_details, chosen_font='timesi',font_size=81, img_size=(1920, 1080),drop=False,capitalise=False,drop_effect=None):
        """
        Creates a text clip that shows words appearing one by one with proper text wrapping
        """

        print(f"ENTERING make_text_clip function: '{text}'")
        current_color=current
        sentence_words=text.split()
        #print(f"Words: {sentence_words}")
        #print(sentence_details)
        enlarged_font_size = int(font_size * 1.74)
    
        font = ImageFont.truetype(chosen_font+".ttf", font_size)
        smallfont=ImageFont.truetype(chosen_font+".ttf", int(font_size/2))
        enlarged_font = ImageFont.truetype(chosen_font+".ttf", enlarged_font_size)
        superenlarged_font=ImageFont.truetype('STENCIL.ttf',enlarged_font_size*2)
    
        
        # Calculate available width with margins (10% margin on each side)
        margin = int(img_size[0] * 0.1)
        available_width = img_size[0] - (2 * margin)
        
        # Function to wrap text to fit within available width
        def wrap_text_to_width(text_to_wrap,font=font):
            words = text_to_wrap.split()
            lines = []
            current_line = ""
            
            for word in words:
                test_line = current_line + (" " if current_line else "") + word
                temp_img = Image.new('RGBA', (available_width, 100), (0, 0, 0, 0))
                temp_draw = ImageDraw.Draw(temp_img)
                bbox = temp_draw.textbbox((0, 0), test_line, font=font)
                line_width = bbox[2] - bbox[0]
                
                if line_width <= available_width:
                    current_line = test_line
                else:
                    if current_line:
                        lines.append(current_line)
                        current_line = word
                    else:
                        # Single word is too long, force it on its own line
                        lines.append(word)
                        current_line = ""
            
            if current_line:
                lines.append(current_line)
            
            return "\n".join(lines)
        
        # Get wrapped text dimensions
        wrapped_text = wrap_text_to_width(text)
        temp_img = Image.new('RGBA', img_size, (0, 0, 0, 0))
        temp_draw = ImageDraw.Draw(temp_img)
        bbox = temp_draw.multiline_textbbox((0, 0), wrapped_text, font=font, align='center', spacing=24)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        #print(f"Wrapped text dimensions: {text_width}x{text_height}")
        #print(sentence_details)

        # Center position for text placement
        base_x = (img_size[0] - text_width) // 2
        base_y = (img_size[1] - text_height) // 2
        
        # Find word clips
        word_clip=None
        word_clips = []
        accumulated_text = ""        
        font_to_use=font
        last_word_end_time=0.0
        for i, word in enumerate(sentence_words):
            # Build accumulated text (all words up to current word)
            if (i==len(sentence_words)-1 and drop):
                current_color=colors[random.randint(0,len(colors)-1)]
                font_to_use=enlarged_font
                
            if i == 0:
                accumulated_text = word
            else:
                accumulated_text += " " + word
                
            # Wrap the accumulated text
            wrapped_accumulated = wrap_text_to_width(accumulated_text, font_to_use)            
            # Find timing for this word from word_timings
            word_start = sentence_details[i][1]
            word_end = sentence_details[i][2]
            
            # Create image with wrapped accumulated text
            img = Image.new('RGBA', img_size, (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            
            if i==len(sentence_words)-1:
            # Recalculate position for enlarged text
                bbox = draw.multiline_textbbox((0, 0), wrapped_accumulated, font=font_to_use, align='center', spacing=24)
                enlarged_text_width = bbox[2] - bbox[0]
                enlarged_text_height = bbox[3] - bbox[1]
                if zoom_duration>0:
                    enlarged_x = (img_size[0] - enlarged_text_width) // 8
                    enlarged_y = (img_size[1] - enlarged_text_height) // 8
                else:
                    enlarged_x = (img_size[0] - enlarged_text_width) // 2
                    enlarged_y = (img_size[1] - enlarged_text_height) // 2
                if dfx:              
                    draw.multiline_text((enlarged_x/1.04, enlarged_y/1.01), text=wrapped_accumulated, font=font_to_use, 
                                fill='white', spacing=24, align='left')
                    draw.multiline_text((enlarged_x/0.96, enlarged_y/0.99), text=wrapped_accumulated, font=font_to_use, 
                                fill='white', spacing=24, align='left')
                if duplicatefx:
                       
                    draw.multiline_text((enlarged_x, enlarged_y), text=wrapped_accumulated, font=superenlarged_font, 
                                fill='white', spacing=24, align='left')
                    draw.multiline_text((enlarged_x/3, enlarged_y/3), text=wrapped_accumulated, font=enlarged_font, 
                                fill=current_color, spacing=24, align='left') 
                else:
                # Draw wrapped accumulated text with enlarged font
                    draw.multiline_text((enlarged_x, enlarged_y), text=wrapped_accumulated, font=font_to_use, 
                                fill=current_color, spacing=24, align='left')
            else:
                # Draw wrapped accumulated text with normal font and original positioning
                draw.multiline_text((base_x, base_y), text=wrapped_accumulated, font=font_to_use, 
                                fill=current_color, spacing=24, align='left')
                

            # Calculate clip duration - from when this word appears until next word or end
            clip_start=word_start
            clip_duration = word_end - word_start
                      
            if word_start-0.09>=0:
                clip_start = word_start-0.09
            
            try:
                #print(sentence_details[i+1][1])
                clip_duration = sentence_details[i+1][1] - float(clip_start )
                #print("next="+sentence_details[i+1])
            except:
                print("EXCEPT BLOCK")
                clip_duration = word_end - word_start
            
            # Apply duration capping as in original
            '''
            if clip_duration > 3*(avg_dur + avg_gap):
                print(sentence_details[i][0]+" capped")
                clip_duration = avg_dur + avg_gap
            '''
            last_word_end_time=clip_start
            if clip_duration > 0:
                word_clip = mp.ImageClip(np.array(img), duration=clip_duration).with_start(clip_start)
                word_clips.append(word_clip)
                print(f"Word '{word}' clip: start={clip_start:.2f}, duration={clip_duration:.2f}")

        if cyclefx:
            img = Image.new('RGBA', img_size, (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            for i in range(10):
                font_to_use=ImageFont.truetype(random.choice(fonts)+'.ttf',font_size)
                draw.multiline_text((base_x, base_y), text=wrapped_accumulated, font=font_to_use, 
                                fill=current_color, spacing=24, align='left')
                word_clip = mp.ImageClip(np.array(img), duration=1/10).with_start(clip_start+clip_duration+i/10)
                word_clips.append(word_clip)


        if not word_clips:
            print("No word clips created, creating fallback")
            # Create a fallback clip with wrapped text
            img = Image.new('RGBA', img_size, (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            wrapped_fallback = wrap_text_to_width(text)
            
            # Recalculate position for wrapped fallback text
            bbox = draw.multiline_textbbox((0, 0), wrapped_fallback, font=font, align='center', spacing=24)
            fallback_width = bbox[2] - bbox[0]
            fallback_height = bbox[3] - bbox[1]
            fallback_x = (img_size[0] - fallback_width) // 2
            fallback_y = (img_size[1] - fallback_height) // 2
            
            draw.multiline_text((fallback_x, fallback_y), text=wrapped_fallback, font=font, 
                            fill='white', spacing=24, align='center')
            fallback_clip = mp.ImageClip(np.array(img), duration=duration).with_start(start_time)
            return fallback_clip
        
        # Combine all word clips
        final_clip = mp.CompositeVideoClip(word_clips)

        if drop:
        # Create zoom effect that starts after the last word ends
            zoom_start_time = last_word_end_time+0.3
            
            # Define zoom function - starts at scale 1.0 and zooms to zoom_scale
            def zoom_effect(t):
                if t < zoom_start_time:
                    return 1.0
                elif t < zoom_start_time + zoom_duration:
                    # Linear interpolation from 1.0 to zoom_scale
                    progress = (t - zoom_start_time) / zoom_duration
                    return 1.0 + (zoom_scale - 1.0) * progress
                else:
                    return zoom_scale
            
            
            # Apply the zoom effect
            #mp.vfx.Resize(zoom_effect)
            #mp.vfx.SuperSample(0.5,20)
            #mp.vfx.Resize(lambda t:1+int(t/2))
            #mp.vfx.Blink(0.1,0.1)
            #mp.vfx.SlideOut(0.3,'right')
            #final_clip = final_clip.with_effects([mp.vfx.InvertColors()])
            
            print(f"Zoom effect applied: starts at {zoom_start_time:.2f}s, duration={zoom_duration}s, max_scale={zoom_scale}")
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
    """
    Enhanced lyric video creation with integrated text effects
    """        
    colors=["#0D9053","#E0E845","#1B8DBA","#E80E12","#D2D2D2","#900D71","#FD9000"]
    bg_colors=[("#8DB673","#00236A"),
               ("#00236A","#900D71","#DF8A00"),
               ("#000275","#003563","#D560CE","#D8DC4E"),
               ("#D8DC4E","#D560CE"),
               ("#000000","#0D9053","#000275","#E80E12","#900D71","#DF8A00"),
               ("#E384C5","#E80E12"),
               ("#E80E12","#E9FC42")]

    fonts=["BERNHC","BRITANIC","BROADW","COLONNA","ELEPHNT","ELEPHNTI","GILLUBCD","HTOWER","HTOWERI","LBRITE","LBRITED","LBRITEDI","LBRITEI","SCRIPTBL","segoesc","segoescb","times","timesbd","timesbi","timesi","VINERITC","VIVALDII","VLADIMIR","STENCIL"]

    # Load audio
    audio = mp.AudioFileClip(audio_file).subclipped(0,6)
    duration = audio.duration
    neighborhoods, stats, significant_transitions,timestamps=ana3.main_with_neighborhoods(audio_file)

    
    avg_dur=0.0
    avg_gap=0.0
    avg_sentence_dur=0.0
    prev=0.0
    for i in range(len(word_timings)):
        avg_gap=avg_gap*i+(word_timings[i][1]-prev)
        avg_gap/=(i+1)
        avg_dur=avg_dur*i+(word_timings[i][2]-word_timings[i][1])
        avg_dur/=(i+1)
        prev=word_timings[i][2]

    idx=0
    for k,lyric in lyrics_with_timing.items():
        avg_sentence_dur=avg_sentence_dur*idx+(lyric[2]-lyric[1])
        avg_sentence_dur/=(idx+1)
        idx+=1

    classifications=[]
    periods=metadata_analysis.analyze_moving_average_above_thresholds(audio_file[:-4]+'_analysis_beats.csv')
    intensities=classifying_lyrics.classify(lyrics_with_timing,periods=periods)[0]
    parts=get_sentence_timings(audio_file=audio_file)

    print(len(intensities))
    print(len(parts))
    for idx in range(len(parts)):

        classification=(intensities[idx],parts[idx])
        classifications.append(classification)
    
    print(classifications)

    print("average duration =",avg_sentence_dur)
    current="#D2D2D2"

    verses=['VINERITC','timesi','timesbi','segoesc','ELEPHNTI']
    choruses=['STENCIL','BERNHC','BRITANIC','ELEPHNT']
    slow=['LBRITE','COLONNA','LBRITED','LBRITEDI','VIVALDII','HTOWERT','VLADIMIR']
    chosen_font=""

    lyric_fonts=[]
    lyric_fonts.append(random.choice(verses))
    lyric_fonts.append(random.choice(verses))
    lyric_fonts.append(random.choice(choruses))

    bg_clips=[]
    c=0
    #print(neighborhoods)
    '''
    ADD THIS BACK IN
    for n in neighborhoods:
        print(c)
        print("end="+str(n['end_time']))
        
        if n['end_time']<45:
            bg1=get_picture_vid(n['duration']/2)
            bg1=bg1.with_start(n['start_time'])
            bg2=get_picture_vid(n['duration']/2)
            bg2=bg2.with_start(n['start_time']+n['duration']/2)
            bg_clips.append(bg1)
            bg_clips.append(bg2)
            print("duration="+str(n['duration']))
        else:
            bg=mp.VideoClip(make_background,duration=45-n['start_time']).with_start(n['start_time'])
            print(45-n['start_time'])
            bg=bg.with_effects([mp.vfx.FadeOut(0.2)])
            bg_clips.append(bg)
            break
        c+=1
    '''
    bg=mp.VideoClip(make_background,duration=audio.duration)
    bg_clips=[bg]
    # Create text clips using PIL
    text_clips = []

    
    print(f"Processing {len(lyrics_with_timing)} sentences")
    print(f"Word timings has {len(word_timings)} words")
    
    total_words=0
    
    # Check if we should add title effects for the first sentence
    title_card_added = False
    
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
        #print("SENTENCE WORD TIMINGS")
        #print(sentence_word_timings)
        total_words+=len(sentence_words)

        print(f"Found {len(sentence_words)} words for sentence: {sentence_words}")

        if sentence_end_time > duration:
            print(f"Skipping sentence ending at {sentence_end_time} (beyond duration {duration})")
            break
        
        if not sentence_words:
            print("No words found for sentence, skipping")
            continue
        
        # Add title card with effects if this is the first sentence and it has enough duration
        if (sentence_idx == 0 and sentence_duration > avg_sentence_dur * 2 and use_title_effects and not title_card_added):
            print("Adding title card with text effects")
            
            artist = "CAGE THE ELEPHANT"  # You can make this dynamic
            title = "CIGARETTE DAYDREAMS"  # You can make this dynamic
            
            # Calculate duration for each effect (split the available time)
            effect_duration = min(avg_sentence_dur-2, sentence_duration / 3)
            
            # Create title card
            title_card = create_title_card_with_effects(artist=artist, title=title, duration_each=effect_duration)
            title_card = title_card.with_start(sentence_start_time)
            text_clips.append(title_card)
            title_card_added = True
        
        chosen_size=69
        drop=False
        #intensity,part
        if (classifications[sentence_idx][1].lower()!='chorus' ):
            if (classifications[sentence_idx][1].lower()=='verse') :
                chosen_font=lyric_fonts[0]
            else:
                chosen_font=lyric_fonts[1]
                if lyric_fonts[1]==lyric_fonts[0]:
                    lyric_fonts[1]=random.choice(verses)
            
            try:
                if classifications[sentence_idx+1][0].lower()=='high intensity':
                    drop=True
            except:
                drop=False
                
        else:
            chosen_size=81
            drop=True
            if (classifications[sentence_idx][0].lower()=='high intensity'):
                chosen_font=lyric_fonts[2]
            else:
                chosen_font=lyric_fonts[0]
        
        # Create text clip for this sentence with word-by-word reveal
        print(sentence_word_timings)
        sentence_clip = make_text_clip(
            sentence_text,            
            sentence_start_time,
            sentence_duration,
            sentence_word_timings,
            chosen_font=chosen_font,
            drop=True,
            font_size=chosen_size
        )
        
        if sentence_clip:
            text_clips.append(sentence_clip)
    
    print(f"\nCreated {len(text_clips)} text clips")
    
    # Combine everything
    #myvideo = mp.CompositeVideoClip(bg_clips + text_clips)
    myvideo=mp.CompositeVideoClip(text_clips)
    myvideo = myvideo.with_audio(audio)
    
    # Apply flash effects
    for stamp in timestamps:
        try:
            myvideo=flashfx.basic_flash_example(myvideo,stamp[1])
        except Exception as e:
            print(e)
        
    # Write video
    myvideo.write_videofile(output_file,
                               fps=20,
                               bitrate='8000k',
                               codec='libx264',
                               audio_codec='aac',
                               temp_audiofile='temp-audio.m4a',
                               remove_temp=True,
                                )
    
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
    get_sentence_timings(name+".wav")
    create_lyric_video_pil(name+".wav",lyrics_with_timing=restored,word_timings=word_timings)
