🎵 Music Lyric App
Automatically create synchronized lyric videos for any English song with dynamic visual effects

This Python-powered application takes a song title and artist name, then generates a professional-quality lyric video where each word appears precisely when it's sung, complete with beat-synchronized background effects and intensity-based visual styling.

✨ Features
🎯 Automatic Lyric Synchronization: Each word appears exactly when sung
🎨 Dynamic Visual Effects: Background effects change with the beat
📊 Audio Analysis: Intelligent classification of song sections (verse, chorus) based on energy levels
🖼️ Smart Image Fetching: Automatically sources relevant images from Spotify and Wikipedia
🔊 Vocal Isolation: Separates vocals from instruments for precise alignment
⚡ Beat Detection: Uses advanced audio analysis to sync effects perfectly
🚀 How It Works
Step 1: Audio Preparation
Download your song into the working directory as a .wav file using the format:

<title>_<artist>.wav
Example: blindinglights_theweeknd.wav

⚠️ Note: Remove capitals, spaces, and special characters from the filename

Step 2: Launch the Application
Open genius4.py
Enter the song name and artist
Click "CREATE LYRIC VIDEO"
Step 3: Automated Processing Pipeline
🔍 Lyric Extraction & Parsing
Fetches lyrics using the Genius API
Parses text word-by-word and sentence-by-sentence
Identifies sentence boundaries for proper timing
🎤 Vocal Separation
Uses the Demucs library to isolate vocals from instruments
Creates clean vocal track for accurate word alignment
⏱️ Word Alignment
ForceAlign library maps each word to its exact timestamp
Creates precise timing data: {index: (word, start_time, end_time)}
Generates similar dictionary for sentence-level timing
🖼️ Visual Asset Collection
Spotify API: Sources album artwork and artist images
Wikipedia API: Fetches additional contextual imagery
Builds comprehensive visual library for the video
🎬 Video Generation
MoviePy: Creates dynamic background effects
PIL (Python Imaging Library): Handles text rendering and styling
Combines all elements into synchronized video output
🎵 Advanced Audio Analysis
Librosa library performs comprehensive audio analysis:
Beat detection and timing
Amplitude and frequency analysis
Energy calculation for each beat
Generates visual energy graph using Matplotlib
🎯 Smart Section Classification
Calculates median and mean energy levels
Above mean energy → Chorus sections
Below mean energy → Verse sections
Classifies each lyric by "intensity level"
🎨 Dynamic Visual Effects
Applies visual effects based on intensity classification
Synchronizes effect changes with detected beats
Creates immersive, music-responsive experience
🛠️ Technology Stack
Component	Library/API	Purpose
Lyrics	Genius API	Lyric fetching
Audio Processing	Demucs	Vocal separation
Word Alignment	ForceAlign	Timestamp synchronization
Images	Spotify + Wikipedia APIs	Visual assets
Video Creation	MoviePy	Effects and composition
Text Rendering	PIL	Typography and styling
Audio Analysis	Librosa	Beat detection and energy analysis
Visualization	Matplotlib	Energy graphing
📁 Project Structure
music_lyric_app/
├── genius4.py              # Main application file
├── <song>_<artist>.wav     # Audio files
├── output/                 # Generated videos
├── images/                 # Fetched visual assets
└── analysis/              # Audio analysis data
🎯 Output
The final video features:

Word-perfect synchronization with audio
Beat-responsive background effects
Intensity-based visual styling (verses vs. chorus)
Professional typography and smooth transitions
High-quality visual assets relevant to the song
Transform any song into a captivating lyric video with the power of Python and advanced audio processing!

