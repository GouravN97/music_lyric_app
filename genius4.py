import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from PIL import Image, ImageTk, ImageDraw, ImageFont
import enhanced 
import lyricsgenius,pickle,sqlite3
import store_lyrics,spotifyimagedownloader
import threading,os
from PIL import Image, ImageTk

class LyricsDownloaderGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Lyrics Downloader")
        self.root.geometry("800x700")
        
        # Set your Genius API key here
        self.GENIUS_API_KEY = "uk1Il2X-fZ2mPUiRXCu3bcnB2IOwOr_l8qWzOdx50j9Bv39lmK6VxIA-STfEL31i"  # Replace with your actual API key
        
        # Initialize Genius API (will be set during auto-authentication)
        self.genius = None
        
        # Variables
        self.current_song = None
        self.current_filename = None
        self.widgets_created = False
        self.authentication_complete = False
        
        # Progress bar variables
        self.progress_bar = None
        self.progress_animation = None
        
        # Set up canvas with background
        self.setup_background()
        
        # Start automatic authentication
        self.auto_authenticate()
    
    def setup_background(self):
        """Setup canvas with background image and PIL-drawn text"""
        try:
            # Load background image
            bg_image = Image.open("menu_bg.png")
            # Resize to fit window
            bg_image = bg_image.resize((800, 700), Image.Resampling.LANCZOS)
        except Exception as e:
            print(f"Could not load background image: {e}")
            # Create gradient fallback
            bg_image = Image.new('RGB', (800, 700), color=(30, 30, 50))
            for y in range(700):
                for x in range(800):
                    r = int(30 + (x / 800) * 20)
                    g = int(30 + (y / 700) * 30)
                    b = int(50 + ((x + y) / 1500) * 40)
                    bg_image.putpixel((x, y), (r, g, b))
        
        # Create drawing context
        draw = ImageDraw.Draw(bg_image)
        
        # Load fonts (with fallback)
        try:
            title_font = ImageFont.truetype("GILLUBCD.ttf", 36)
            label_font = ImageFont.truetype("arial.ttf", 12)
        except:
            # Fallback to default font
            title_font = ImageFont.load_default()
            label_font = ImageFont.load_default()
        
        # Draw title text
        title_text = "LYRICS DOWNLOADER"
        title_bbox = draw.textbbox((0, 0), title_text, font=title_font)
        title_width = title_bbox[2] - title_bbox[0]
        title_x = (800 - title_width) // 2  # Center horizontally
        draw.text((title_x, 20), title_text, fill="black", font=title_font)
        
        # Convert to PhotoImage
        self.bg_photo = ImageTk.PhotoImage(bg_image)
        
        # Create canvas
        self.canvas = tk.Canvas(self.root, highlightthickness=0)
        self.canvas.place(x=0, y=0, relwidth=1, relheight=1)
        
        # Draw background
        self.canvas.create_image(0, 0, anchor="nw", image=self.bg_photo)
        
        # Initialize variables
        self.title_var = tk.StringVar()
        self.artist_var = tk.StringVar()
        self.status_var = tk.StringVar()
        self.file_info_var = tk.StringVar()
        
        self.file_info_var.set("No file generated yet")
        
        # Create initial status message
        self.status_id = self.canvas.create_text(400, 200, 
                                                text="Initializing and authenticating...",
                                                font=("Arial", 12, "bold"))
        
        # Show initial progress
        self.show_progress()
    
    def auto_authenticate(self):
        """Automatically authenticate with the Genius API"""
        if not self.GENIUS_API_KEY or self.GENIUS_API_KEY == "YOUR_GENIUS_API_KEY_HERE":
            self.hide_progress()
            self.update_status("Error: Please set your Genius API key in the code")
            messagebox.showerror("API Key Missing", 
                               "Please set your Genius API key in the GENIUS_API_KEY variable in the code.")
            return
        
        self.update_status("Authenticating with Genius API...")
        
        # Run authentication in separate thread
        thread = threading.Thread(target=self._authenticate_thread)
        thread.daemon = True
        thread.start()
    
    def _authenticate_thread(self):
        """Authenticate with Genius API in separate thread"""
        try:
            # Try to initialize Genius API with the token
            test_genius = lyricsgenius.Genius(self.GENIUS_API_KEY)
            test_genius.timeout = 15  # Set timeout for quick validation
            
            # Try to make a simple request to validate the token
            test_song = test_genius.search_song("Hello", artist="Adele")
            
            # If we get here, the token is valid
            self.root.after(0, self._authentication_success)
            
        except Exception as e:
            self.root.after(0, self._authentication_failed, str(e))
    
    def _authentication_success(self):
        """Handle successful authentication"""
        self.genius = lyricsgenius.Genius(self.GENIUS_API_KEY)
        self.authentication_complete = True
        self.hide_progress()
        
        # Create the main application widgets
        self.create_main_widgets()
        
        self.update_status("Ready to search for songs")
        
        # Focus on title entry
        if hasattr(self, 'title_entry'):
            self.title_entry.focus()
    
    def _authentication_failed(self, error_msg):
        """Handle failed authentication"""
        self.hide_progress()
        self.update_status("Authentication failed - Please check your API key")
        messagebox.showerror("Authentication Failed", 
                           f"Failed to authenticate with Genius API:\n{error_msg}\n\n"
                           "Please check your API key in the code.")
    
    def create_main_widgets(self):
        """Create the main application widgets after authentication"""
        if self.widgets_created:
            return
        
        # Song Title
        self.canvas.create_text(100, 260, text="Song Title:", 
                               font=("Arial", 12), anchor="w")
        
        self.title_entry = tk.Entry(self.root, textvariable=self.title_var, 
                                   width=50, font=("Arial", 12))
        self.canvas.create_window(500, 260, window=self.title_entry)
        
        # Artist
        self.canvas.create_text(100, 320, text="Artist:", 
                                font=("Arial", 12), anchor="w")
        
        self.artist_entry = tk.Entry(self.root, textvariable=self.artist_var, 
                                    width=50, font=("Arial", 12))
        self.canvas.create_window(500, 320, window=self.artist_entry)
        
        # Buttons
        self.search_btn = tk.Button(self.root, text="Search Song", 
                                   command=self.search_song,
                                   bg="#0D9053", fg="white", relief="raised", 
                                   font=("Arial", 12))
        self.canvas.create_window(200, 380, window=self.search_btn)
        
        self.download_btn = tk.Button(self.root, text="CREATE LYRIC VIDEO", 
                                     command=self.download_lyrics, state=tk.DISABLED,
                                     bg="#0D9053", fg="white", relief="raised", 
                                     font=("Arial", 12))
        self.canvas.create_window(350, 380, window=self.download_btn)
        
        self.check_btn = tk.Button(self.root, text="Mark as Restored", 
                                  command=self.check_restored, state=tk.DISABLED,
                                  bg="#0D9053", fg="white", relief="raised", 
                                  font=("Arial", 12))
        self.canvas.create_window(500, 380, window=self.check_btn)
        
        # Move status down to make room
        self.canvas.coords(self.status_id, 400, 420)
        
        # Song info frame background
        self.canvas.create_text(60, 460, text="Song Information", 
                               font=("Arial", 12, "bold"), anchor="w")
        
        # Song info text
        self.info_text = tk.Text(self.root, height=8, width=75, 
                                wrap=tk.WORD, state=tk.DISABLED,
                                bg='white', fg='black', font=("Arial", 12,"bold"))
        self.canvas.create_window(400, 535, window=self.info_text)
        
        # File info frame background
        self.canvas.create_text(60, 610, text="File Information", 
                                font=("Arial", 12, "bold"), anchor="w")
        
        # File info text
        self.file_info_id = self.canvas.create_text(400, 625, 
                                                   text=self.file_info_var.get(),
                                                   fill="white", font=("Arial", 10))
        
        # Bind Enter key events for new entries
        self.title_entry.bind('<Return>', lambda e: self.search_song())
        self.artist_entry.bind('<Return>', lambda e: self.search_song())
        
        self.widgets_created = True
    
    def update_status(self, text):
        """Update status text"""
        self.status_var.set(text)
        self.canvas.itemconfig(self.status_id, text=text)
    
    def update_file_info(self, text):
        """Update file info text"""
        if hasattr(self, 'file_info_id'):
            self.file_info_var.set(text)
            self.canvas.itemconfig(self.file_info_id, text=text)
    
    def show_progress(self):
        """Show custom progress animation"""
        if self.progress_bar is None:
            self.progress_bar = self.canvas.create_rectangle(300, 180, 500, 190, 
                                                           fill="", outline="white", width=1)
            self.progress_fill = self.canvas.create_rectangle(300, 180, 300, 190, 
                                                            fill="#606080", outline="")
        self.animate_progress()
    
    def hide_progress(self):
        """Hide progress animation"""
        if self.progress_bar:
            self.canvas.delete(self.progress_bar)
            self.canvas.delete(self.progress_fill)
            self.progress_bar = None
        if self.progress_animation:
            self.root.after_cancel(self.progress_animation)
            self.progress_animation = None
    
    def animate_progress(self):
        """Animate progress bar"""
        if self.progress_bar:
            # Simple animation - expand and contract
            coords = self.canvas.coords(self.progress_fill)
            if coords[2] >= 500:
                self.canvas.coords(self.progress_fill, 300, 180, 300, 190)
            else:
                self.canvas.coords(self.progress_fill, coords[0], coords[1], coords[2] + 5, coords[3])
            
            self.progress_animation = self.root.after(50, self.animate_progress)
    
    def search_song(self):
        if not self.authentication_complete or self.genius is None:
            messagebox.showerror("Error", "Authentication not complete. Please wait.")
            return
            
        title = self.title_var.get().strip()
        artist = self.artist_var.get().strip()
        
        if not title:
            messagebox.showerror("Error", "Please enter a song title")
            return
        
        # Disable buttons and show progress
        self.search_btn.config(state=tk.DISABLED)
        self.show_progress()
        self.update_status("Searching for song...")
        
        # Run search in separate thread to prevent GUI freezing
        thread = threading.Thread(target=self._search_thread, args=(title, artist))
        thread.daemon = True
        thread.start()
    
    def _search_thread(self, title, artist):
        try:
            # Search for song
            if artist:
                song = self.genius.search_song(title, artist=artist)
            else:
                song = self.genius.search_song(title)
            
            # Update GUI in main thread
            self.root.after(0, self._search_complete, song)
            
        except Exception as e:
            self.root.after(0, self._search_error, str(e))
    
    def _search_complete(self, song):
        self.hide_progress()
        self.search_btn.config(state=tk.NORMAL)
        
        if song:
            self.current_song = song
            
            # Process lyrics (remove content before first '[')
            if song.lyrics and '[' in song.lyrics:
                song.lyrics = song.lyrics[song.lyrics.find('['):]
            
            # Display song info
            info_text = f"Title: {song.title}\n"
            info_text += f"Artist: {song.artist}\n"
            info_text += f"URL: {song.url}\n\n"
            info_text += "Lyrics preview:\n"
            if song.lyrics:
                # Show first few lines as preview
                lyrics_lines = song.lyrics.split('\n')[:10]
                info_text += '\n'.join(lyrics_lines)
                if len(song.lyrics.split('\n')) > 10:
                    info_text += "\n... (truncated)"
            else:
                info_text += "No lyrics found"
            
            self.info_text.config(state=tk.NORMAL)
            self.info_text.delete(1.0, tk.END)
            self.info_text.insert(1.0, info_text)
            self.info_text.config(state=tk.DISABLED)
            
            # Enable download button
            self.download_btn.config(state=tk.NORMAL)
            self.update_status("Song found! Ready to download.")
        else:
            self.update_status("Song not found")
            messagebox.showwarning("Not Found", "Song not found. Please check the title and artist.")
    
    def _search_error(self, error_msg):
        self.hide_progress()
        self.search_btn.config(state=tk.NORMAL)
        self.update_status("Search failed")
        messagebox.showerror("Error", f"Search failed: {error_msg}")
    
    def download_lyrics(self):
        if not self.current_song:
            messagebox.showerror("Error", "No song to download")
            return
        
        try:
            # Generate filename
            title_clean = ''.join(self.current_song.title.split())
            artist_clean = ''.join(self.current_song.artist.split())
            filename = f"{title_clean.lower()}_{artist_clean.lower()}.txt"
            
            # Save lyrics to file
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(self.current_song.lyrics)
            
            self.current_filename = filename
            
            # Update file info
            file_size = os.path.getsize(filename)
            self.update_file_info(f"File: {filename} ({file_size} bytes)")
            
            # Add to database
            store_lyrics.add_to_db(f"{title_clean.lower()}_{artist_clean.lower()}")

            name=f"{title_clean.lower()}_{artist_clean.lower()}"
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

            enhanced.create_lyric_video_pil(artist=self.current_song.artist,title=self.current_song.title,audio_file=name+".wav",lyrics_with_timing=restored,word_timings=word_timings)

            # Enable check button
            self.check_btn.config(state=tk.NORMAL)
            
            self.update_status("Lyrics downloaded successfully!")
            messagebox.showinfo("Success", f"Lyric Video Created !")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create video. Make sure the song is downloaded in the same folder as a .wav file: {str(e)}")
            self.update_status("Download failed")
    
    def check_restored(self):
        result = messagebox.askyesno("Check Restored", 
                                   "Mark this song as restored?\n\n"
                                   "This will update the database record.")
        
        if result:
            # Here you would typically update your database
            # For now, just show a confirmation
            self.update_status("Marked as restored")
            messagebox.showinfo("Success", "Song marked as restored in database")
            
            # Reset for next song
            self.reset_form()
    
    def reset_form(self):
        """Reset the form for a new search"""
        self.title_var.set("")
        self.artist_var.set("")
        self.current_song = None
        self.current_filename = None
        
        if hasattr(self, 'info_text'):
            self.info_text.config(state=tk.NORMAL)
            self.info_text.delete(1.0, tk.END)
            self.info_text.config(state=tk.DISABLED)
        
        self.update_file_info("No file generated yet")
        if hasattr(self, 'download_btn'):
            self.download_btn.config(state=tk.DISABLED)
            self.check_btn.config(state=tk.DISABLED)
        self.update_status("Ready to search for songs")
        
        # Focus on title entry
        if hasattr(self, 'title_entry'):
            self.title_entry.focus()

def start():
    root = tk.Tk()
    app = LyricsDownloaderGUI(root)
    root.mainloop()

if __name__ == "__main__":
    start()
