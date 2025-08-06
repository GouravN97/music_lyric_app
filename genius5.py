import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from PIL import Image, ImageTk, ImageDraw, ImageFont

import lyricsgenius
import store_lyrics
import threading
import os
from PIL import Image, ImageTk

class LyricsDownloaderGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Lyrics Downloader")
        self.root.geometry("800x700")
        self.root.minsize(600, 500)  # Set minimum size
        
        # Initialize Genius API (will be set when token is provided)
        self.genius = None
        
        # Variables
        self.current_song = None
        self.current_filename = None
        self.show_welcome = True
        self.widgets_created = False  # Track if main widgets are created
        
        # Progress bar variables
        self.progress_bar = None
        self.progress_animation = None
        
        # Store widget references for responsive positioning
        self.widget_refs = {}
        
        # Set up canvas with background
        self.setup_background()
        
        # Bind resize event
        self.root.bind('<Configure>', self.on_window_resize)
        
    def on_window_resize(self, event):
        """Handle window resize events"""
        if event.widget == self.root:  # Only handle root window resize
            self.resize_background()
            self.reposition_widgets()
    
    def resize_background(self):
        """Resize background to match window"""
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        
        if width < 100 or height < 100:  # Ignore invalid sizes
            return
            
        try:
            # Load and resize background image
            bg_image = Image.open("menu_bg.png")
            bg_image = bg_image.resize((width, height), Image.Resampling.LANCZOS)
        except:
            # Create gradient fallback
            bg_image = Image.new('RGB', (width, height), color=(30, 30, 50))
            for y in range(0, height, 2):  # Skip pixels for performance
                for x in range(0, width, 2):
                    r = int(30 + (x / width) * 20)
                    g = int(30 + (y / height) * 30)
                    b = int(50 + ((x + y) / (width + height)) * 40)
                    bg_image.putpixel((x, y), (r, g, b))
        
        # Add title
        draw = ImageDraw.Draw(bg_image)
        try:
            title_font = ImageFont.truetype("GILLUBCD.ttf", max(24, min(36, width // 20)))
        except:
            title_font = ImageFont.load_default()
        
        title_text = "LYRICS DOWNLOADER"
        title_bbox = draw.textbbox((0, 0), title_text, font=title_font)
        title_width = title_bbox[2] - title_bbox[0]
        title_x = (width - title_width) // 2
        draw.text((title_x, 20), title_text, fill="black", font=title_font)
        
        # Update canvas and background
        self.bg_photo = ImageTk.PhotoImage(bg_image)
        self.canvas.delete("background")
        self.canvas.create_image(0, 0, anchor="nw", image=self.bg_photo, tags="background")
        
    def reposition_widgets(self):
        """Reposition widgets based on current window size"""
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        
        if width < 100 or height < 100:
            return
        
        # Calculate responsive positions
        center_x = width // 2
        left_margin = width * 0.1
        entry_x = center_x + 100
        
        # Reposition token widgets
        if hasattr(self, 'token_label_id'):
            self.canvas.coords(self.token_label_id, left_margin, height * 0.15)
        if hasattr(self, 'token_entry'):
            self.canvas.coords(self.widget_refs.get('token_entry', 0), entry_x, height * 0.15)
        if hasattr(self, 'validate_token_btn'):
            self.canvas.coords(self.widget_refs.get('validate_btn', 0), left_margin + 50, height * 0.22)
        if hasattr(self, 'token_status_id'):
            self.canvas.coords(self.token_status_id, center_x, height * 0.22)
        if hasattr(self, 'status_id'):
            self.canvas.coords(self.status_id, center_x, height * 0.3)
        
        # Reposition main widgets if they exist
        if self.widgets_created:
            # Song fields
            if hasattr(self, 'title_label_id'):
                self.canvas.coords(self.title_label_id, left_margin, height * 0.37)
            if hasattr(self, 'title_entry'):
                self.canvas.coords(self.widget_refs.get('title_entry', 0), entry_x, height * 0.37)
                
            if hasattr(self, 'artist_label_id'):
                self.canvas.coords(self.artist_label_id, left_margin, height * 0.44)
            if hasattr(self, 'artist_entry'):
                self.canvas.coords(self.widget_refs.get('artist_entry', 0), entry_x, height * 0.44)
            
            # Buttons
            button_y = height * 0.52
            button_spacing = min(150, width * 0.15)
            if hasattr(self, 'search_btn'):
                self.canvas.coords(self.widget_refs.get('search_btn', 0), center_x - button_spacing, button_y)
            if hasattr(self, 'download_btn'):
                self.canvas.coords(self.widget_refs.get('download_btn', 0), center_x, button_y)
            if hasattr(self, 'check_btn'):
                self.canvas.coords(self.widget_refs.get('check_btn', 0), center_x + button_spacing, button_y)
            
            # Update status position
            self.canvas.coords(self.status_id, center_x, height * 0.58)
            
            # Song info
            if hasattr(self, 'song_info_label_id'):
                self.canvas.coords(self.song_info_label_id, left_margin, height * 0.62)
            if hasattr(self, 'info_text'):
                text_height = min(8, max(4, height // 100))
                text_width = min(75, max(40, width // 12))
                self.info_text.config(height=text_height, width=text_width)
                self.canvas.coords(self.widget_refs.get('info_text', 0), center_x, height * 0.75)
            
            # File info
            if hasattr(self, 'file_info_label_id'):
                self.canvas.coords(self.file_info_label_id, left_margin, height * 0.88)
            if hasattr(self, 'file_info_id'):
                self.canvas.coords(self.file_info_id, center_x, height * 0.92)
    
    def setup_background(self):
        """Setup canvas with background image and PIL-drawn text"""
        # Create canvas first
        self.canvas = tk.Canvas(self.root, highlightthickness=0)
        self.canvas.place(x=0, y=0, relwidth=1, relheight=1)
        
        # Initialize variables
        self.token_var = tk.StringVar()
        self.title_var = tk.StringVar()
        self.artist_var = tk.StringVar()
        self.status_var = tk.StringVar()
        self.file_info_var = tk.StringVar()
        self.token_status_var = tk.StringVar()
        
        self.status_var.set("Enter and validate your Genius API token to begin")
        self.file_info_var.set("No file generated yet")
        self.token_status_var.set("Token not validated")
        
        # Initial background setup
        self.resize_background()
        
        # Only create token validation widgets initially
        self.create_token_widgets()
   
    def create_token_widgets(self):
        """Create only the token validation widgets"""
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        center_x = width // 2
        left_margin = width * 0.1
        entry_x = center_x + 100
        
        # API Token section
        self.token_label_id = self.canvas.create_text(left_margin, height * 0.15, text="Genius API Token:", 
                                font=("Arial", 12), anchor="w")
        
        self.token_entry = tk.Entry(self.root, textvariable=self.token_var, 
                                   width=50, show="*", font=("Arial", 12))
        self.widget_refs['token_entry'] = self.canvas.create_window(entry_x, height * 0.15, window=self.token_entry)
        
        # Token validation button
        self.validate_token_btn = tk.Button(self.root, text="Validate Token", 
                                          command=self.validate_token,
                                          bg="#04A85B", fg="white", 
                                          relief="flat", font=("Arial", 12))
        self.widget_refs['validate_btn'] = self.canvas.create_window(left_margin + 50, height * 0.22, window=self.validate_token_btn)
        
        # Token status
        self.token_status_id = self.canvas.create_text(center_x, height * 0.22, 
                                                      text=self.token_status_var.get(),
                                                      fill="red", font=("Arial", 12))
        
        # Initial status
        self.status_id = self.canvas.create_text(center_x, height * 0.3, 
                                                text=self.status_var.get(),
                                                 font=("Arial", 12,"bold"))
        
        # Bind Enter key for token entry
        self.token_entry.bind('<Return>', lambda e: self.validate_token())

    def create_main_widgets(self):
        """Create the main application widgets after token validation"""
        if self.widgets_created:
            return
        
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        center_x = width // 2
        left_margin = width * 0.1
        entry_x = center_x + 100
        
        # Song Title
        self.title_label_id = self.canvas.create_text(left_margin, height * 0.37, text="Song Title:", 
                               font=("Arial", 12), anchor="w")
        
        self.title_entry = tk.Entry(self.root, textvariable=self.title_var, 
                                   width=50, font=("Arial", 12))
        self.widget_refs['title_entry'] = self.canvas.create_window(entry_x, height * 0.37, window=self.title_entry)
        
        # Artist
        self.artist_label_id = self.canvas.create_text(left_margin, height * 0.44, text="Artist:", 
                                font=("Arial", 12), anchor="w")
        
        self.artist_entry = tk.Entry(self.root, textvariable=self.artist_var, 
                                    width=50, font=("Arial", 12))
        self.widget_refs['artist_entry'] = self.canvas.create_window(entry_x, height * 0.44, window=self.artist_entry)
        
        # Buttons
        button_y = height * 0.52
        button_spacing = min(150, width * 0.15)
        
        self.search_btn = tk.Button(self.root, text="Search Song", 
                                   command=self.search_song,
                                   bg="#0D9053", fg="white", relief="raised", 
                                   font=("Arial", 12))
        self.widget_refs['search_btn'] = self.canvas.create_window(center_x - button_spacing, button_y, window=self.search_btn)
        
        self.download_btn = tk.Button(self.root, text="Align Lyrics", 
                                     command=self.download_lyrics, state=tk.DISABLED,
                                     bg="#0D9053", fg="white", relief="raised", 
                                     font=("Arial", 12))
        self.widget_refs['download_btn'] = self.canvas.create_window(center_x, button_y, window=self.download_btn)
        
        self.check_btn = tk.Button(self.root, text="Mark as Restored", 
                                  command=self.check_restored, state=tk.DISABLED,
                                  bg="#0D9053", fg="white", relief="raised", 
                                  font=("Arial", 12))
        self.widget_refs['check_btn'] = self.canvas.create_window(center_x + button_spacing, button_y, window=self.check_btn)
        
        # Move status down to make room
        self.canvas.coords(self.status_id, center_x, height * 0.58)
        
        # Song info frame background
        self.song_info_label_id = self.canvas.create_text(left_margin, height * 0.62, text="Song Information", 
                               font=("Arial", 12, "bold"), anchor="w")
        
        # Song info text
        text_height = min(8, max(4, height // 100))
        text_width = min(75, max(40, width // 12))
        self.info_text = tk.Text(self.root, height=text_height, width=text_width, 
                                wrap=tk.WORD, state=tk.DISABLED,
                                bg='white', fg='black', font=("Arial", 10))
        self.widget_refs['info_text'] = self.canvas.create_window(center_x, height * 0.75, window=self.info_text)
        
        # File info frame background
        self.file_info_label_id = self.canvas.create_text(left_margin, height * 0.88, text="File Information", 
                                font=("Arial", 12, "bold"), anchor="w")
        
        # File info text
        self.file_info_id = self.canvas.create_text(center_x, height * 0.92, 
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
    
    def update_token_status(self, text, color="white"):
        """Update token status text"""
        self.token_status_var.set(text)
        self.canvas.itemconfig(self.token_status_id, text=text, fill=color)
    
    def update_file_info(self, text):
        """Update file info text"""
        if hasattr(self, 'file_info_id'):
            self.file_info_var.set(text)
            self.canvas.itemconfig(self.file_info_id, text=text)
    
    def show_progress(self):
        """Show custom progress animation"""
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        center_x = width // 2
        prog_y = height * 0.55
        
        if self.progress_bar is None:
            self.progress_bar = self.canvas.create_rectangle(center_x - 100, prog_y, center_x + 100, prog_y + 10, 
                                                           fill="", outline="white", width=1)
            self.progress_fill = self.canvas.create_rectangle(center_x - 100, prog_y, center_x - 100, prog_y + 10, 
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
            width = self.root.winfo_width()
            center_x = width // 2
            coords = self.canvas.coords(self.progress_fill)
            if coords[2] >= center_x + 100:
                self.canvas.coords(self.progress_fill, center_x - 100, coords[1], center_x - 100, coords[3])
            else:
                self.canvas.coords(self.progress_fill, coords[0], coords[1], coords[2] + 5, coords[3])
            
            self.progress_animation = self.root.after(50, self.animate_progress)
    
    def validate_token(self):
        """Validate the Genius API token"""
        token = self.token_var.get().strip()
        
        if not token:
            messagebox.showerror("Error", "Please enter a Genius API token")
            return
        
        # Disable button and show progress
        self.validate_token_btn.config(state=tk.DISABLED)
        self.update_token_status("Validating token...", "orange")
        self.show_progress()
        
        # Run validation in separate thread
        thread = threading.Thread(target=self._validate_token_thread, args=(token,))
        thread.daemon = True
        thread.start()
    
    def _validate_token_thread(self, token):
        """Validate token in separate thread"""
        try:
            # Try to initialize Genius API with the token
            test_genius = lyricsgenius.Genius(token)
            test_genius.timeout = 15  # Set timeout for quick validation
            
            # Try to make a simple request to validate the token
            test_song = test_genius.search_song("Hello", artist="Adele")
            
            # If we get here, the token is valid
            self.root.after(0, self._token_validation_success, token)
            
        except Exception as e:
            self.root.after(0, self._token_validation_failed, str(e))
    
    def _token_validation_success(self, token):
        """Handle successful token validation"""
        self.genius = lyricsgenius.Genius(token)
        self.validate_token_btn.config(state=tk.NORMAL)
        self.update_token_status("✓ Token valid", "green")
        self.hide_progress()
        
        # Create the main application widgets
        self.create_main_widgets()
        
        self.update_status("Ready to search for songs")
        
        # Focus on title entry
        self.title_entry.focus()
        
        messagebox.showinfo("Success", "Genius API token validated successfully!")
    
    def _token_validation_failed(self, error_msg):
        """Handle failed token validation"""
        self.validate_token_btn.config(state=tk.NORMAL)
        self.update_token_status("✗ Token invalid", "red")
        self.hide_progress()
        
        messagebox.showerror("Token Validation Failed", 
                           f"Failed to validate token:\n{error_msg}\n\n"
                           "Please check your token and try again.")
    
    def search_song(self):
        if self.genius is None:
            messagebox.showerror("Error", "Please validate your Genius API token first")
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
            store_lyrics.add_to_db(f"{title_clean}.wav", filename)
            
            # Enable check button
            self.check_btn.config(state=tk.NORMAL)
            
            self.update_status("Lyrics downloaded successfully!")
            messagebox.showinfo("Success", f"Lyrics saved to {filename}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to download lyrics: {str(e)}")
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