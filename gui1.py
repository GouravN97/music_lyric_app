import tkinter as tk
from PIL import Image, ImageTk
import genius4

class AnimatedGIF:
    def __init__(self, root, gif_path):
        self.root = root
        self.gif = Image.open(gif_path)
        self.frames = []
        
        try:
            while True:
                self.frames.append(ImageTk.PhotoImage(self.gif.copy()))
                self.gif.seek(len(self.frames))
        except EOFError:
            pass
        
        self.current_frame = 0
        self.canvas = tk.Canvas(root, highlightthickness=0)
        self.canvas.place(x=0, y=0, relwidth=1, relheight=1)
        
        # Bind click event only to items with "clickable" tag
        self.canvas.tag_bind("clickable", "<Button-1>", on_click)
        
        self.animate()
    
    def animate(self):
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor="nw", image=self.frames[self.current_frame])
        
        # Add clickable text with hover effect
        text_id = self.canvas.create_text(700, 300, text="LYRIC VIDEO\n GENERATOR", 
                                         fill="white", font=("GILLUBCD.ttf", 36, "bold"),
                                         tags="clickable")
        
        # Optional: Add hover effects
        self.canvas.tag_bind("clickable", "<Enter>", self.on_enter)
        self.canvas.tag_bind("clickable", "<Leave>", self.on_leave)
        
        self.current_frame = (self.current_frame + 1) % len(self.frames)
        self.root.after(100, self.animate)
    
    def on_enter(self, event):
        # Change cursor when hovering over text
        self.canvas.config(cursor="hand2")
        # Optional: Change text color on hover
        self.canvas.itemconfig("clickable", fill="yellow")
    
    def on_leave(self, event):
        # Reset cursor when leaving text
        self.canvas.config(cursor="")
        # Reset text color
        self.canvas.itemconfig("clickable", fill="white")

def on_click(event):
    print("Text clicked!")
    root.destroy()
    genius4.start()

root = tk.Tk()
root.geometry("400x300")

animated_bg = AnimatedGIF(root, "menu3.gif")

root.mainloop()