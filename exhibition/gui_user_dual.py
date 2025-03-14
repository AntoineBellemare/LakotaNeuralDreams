import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *

import time
import threading
from oscpy.client import OSCClient
from oscpy.server import OSCThreadServer
import tkinter.colorchooser as colorchooser  # For color wheel functionality
import os
from functools import partial
from PIL import Image, ImageTk

class LatentDreamscapeGUI:
    def __init__(self):
        self.color_palette = [
            "#F8F8F2", "#A9CCE3", '#bc5e48', "#944c64", "#C29250", "#317873", "#A3A04E", "#7A5C72"
        ]

        self.root = ttk.Window(themename="darkly")
        #self.root.after(100, lambda: self.canvas.config(bg="white"))  # Set canvas background to white
        # Track whether the title bar is hidden
        self.title_bar_hidden = False  # Start with title bar visible

        # Bind the key combo Ctrl+T to toggle title bar
        self.root.bind("<Control-0>", self.toggle_title_bar)



        self.root.title("Latent Dreamscape GUI")
        self.root.geometry("600x500")
        self.last_activity_time = time.time()
        self.current_eeg_status = 0  # Default to disconnected


        # OSC Setup using oscpy
        self.send_port = 9000  # Matches GoofyPipe's OSCIn node
        self.receive_port = 5005  # For receiving EEG status
        self.osc_address = "127.0.0.1"

        # OSC client and server
        self.client = OSCClient(self.osc_address.encode(), self.send_port)
        self.server = OSCThreadServer()
        self.server.listen(address=self.osc_address.encode(), port=self.receive_port, default=True)
        

        # Default pen settings
        self.pen_size = tk.IntVar(value=3)  # Default pen size
        self.pen_color = "#F8F8F2"          # Default pen color
        self.eraser_mode = False           # Eraser state

        self.load_symbols("../dream_language_symbols/no_bg_square")
        
        self.action_stack = []  # Stack to track actions for undo
        
        self.current_drawn_lines = []  # Temporary storage for lines in the current drawing action
        
        # GUI Components
        self.setup_gui()
        self.server.bind(b"/eeg_status", self.eeg_status_callback)
        self.check_inactivity()
        self.send_state()
        self.client.send_message(b"/text_input", [b""])  # Send an initial empty text
        # style = ttk.Style()
        # style.theme_use('alt')  # You can experiment with 'clam', 'alt', 'default', or 'classic'
        # style.configure('TButton', font=('Courrier', 12), padding=6)
        # style.configure('TLabel', font=('Courrier', 12))


    def setup_gui(self):

        """Setup the GUI layout with drawing mode menu for pen size and color."""
        # Configure root grid for centering
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_rowconfigure(1, weight=0)
        self.root.grid_rowconfigure(2, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        # Main container frame
        self.main_frame = ttk.Frame(self.root)  # no bg param
        self.main_frame.pack(fill="both", expand=True)


        # Text Frame on the left
        self.text_frame = tk.Frame(self.main_frame, bg="#2B2B2B", width=250, height=200)
        self.text_frame.pack(side="left", fill="y", padx=20)  # Add padding on the left

        self.text_label = tk.Label(self.text_frame, text="Write your dream:", font=("Courier", 14), bg="#2B2B2B", fg="#F5F5F5")
        self.text_label.pack(pady=5)
        self.text_entry = tk.Text(self.text_frame, width=40, height=20, wrap="word",
                                relief="solid", bd=2, font=("Courier", 12),
                                fg="#F8F8F2",  # Off-white text color
                                bg="#2B2B2B")  # Optional: Dark background for contrast

        self.text_entry.bind("<Key>", lambda event: self.schedule_text_send())
        self.text_entry.pack(pady=(20, 5))  # Reduce top padding to move it up
        # Frame to hold Send and Clear buttons side by side
        self.text_button_frame = tk.Frame(self.text_frame, bg="#2B2B2B")
        self.text_button_frame.pack(pady=5)

        # Send Button
        # Instead of tk.Button(...):
        # self.send_button = ttk.Button(
        #     self.text_button_frame,
        #     text="Send",
        #     command=self.send_text,
        #     bootstyle="success"  # pick from 'primary', 'secondary', 'success', etc.
        # )
        # self.send_button.pack(side="left", padx=5)

        # Clear Button
        self.clear_text_button = ttk.Button(self.text_button_frame, text="Clear", command=self.clear_text, bootstyle="danger")
        self.clear_text_button.pack(side="left", padx=5)


        # EEG Status Section (Added below the text box)
        self.eeg_frame = tk.Frame(self.text_frame, bg="#2B2B2B")
        self.eeg_frame.pack(pady=(5, 0), fill="x", padx=10, anchor="w")  # Align left, move up

        self.eeg_label = tk.Label(self.eeg_frame, text="EEG Status", font=("Courier", 14), bg="#2B2B2B", fg="#F5F5F5")
        self.eeg_label.pack(anchor="w")  # Align left

        # Container for EEG status light and legend
        self.eeg_status_container = tk.Frame(self.eeg_frame, bg="#2B2B2B")
        self.eeg_status_container.pack(fill="x", padx=5, pady=5)

        # EEG Status Light
        self.eeg_status_canvas = tk.Canvas(self.eeg_status_container, width=60, height=60, bd=0, highlightthickness=0)
        self.eeg_status_canvas.pack(side="left", padx=(0, 10), pady=5)  # Align left, space right

        # EEG Legend Box (Right of the status light)
        self.eeg_legend_frame = tk.Frame(self.eeg_status_container, bg="#f0f0f0")
        self.eeg_legend_frame.pack(side="left", padx=10)  # Move descriptions to the right of the light

        # Green Circle and Label
        self.green_canvas = tk.Canvas(self.eeg_legend_frame, width=20, height=20, bd=0, highlightthickness=0)
        self.green_canvas.create_oval(2, 2, 18, 18, fill="green")
        self.green_canvas.grid(row=0, column=0, padx=5)
        green_label = tk.Label(self.eeg_legend_frame, text="Good Signal", font=("Courier", 10), bg="#f0f0f0")
        green_label.grid(row=0, column=1, sticky="w")

        # Yellow Circle and Label
        self.yellow_canvas = tk.Canvas(self.eeg_legend_frame, width=20, height=20, bd=0, highlightthickness=0)
        self.yellow_canvas.create_oval(2, 2, 18, 18, fill="yellow")
        self.yellow_canvas.grid(row=1, column=0, padx=5)
        yellow_label = tk.Label(self.eeg_legend_frame, text="Weak Signal", font=("Courier", 10), bg="#f0f0f0")
        yellow_label.grid(row=1, column=1, sticky="w")

        # Red Circle and Label
        self.red_canvas = tk.Canvas(self.eeg_legend_frame, width=20, height=20, bd=0, highlightthickness=0)
        self.red_canvas.create_oval(2, 2, 18, 18, fill="red")
        self.red_canvas.grid(row=2, column=0, padx=5)
        red_label = tk.Label(self.eeg_legend_frame, text="Disconnected", font=("Courier", 10), bg="#f0f0f0")
        red_label.grid(row=2, column=1, sticky="w")

        # Load dreamy border texture
        # try:
        #     border_img = Image.open("background.png")  # Ensure correct path
        #     border_img = border_img.resize((210, 60), Image.Resampling.LANCZOS)  # Slightly larger for border effect
        #     self.border_image = ImageTk.PhotoImage(border_img)
        # except Exception as e:
        #     print(f"Error loading border image: {e}")
        self.border_image = None  # Fallback if image doesn't load

        # Load button background image (optional) or use a solid color
        self.button_bg_color = "#d9d9d9"  # Light gray, or change as needed

        # Create a frame with the texture as background
        self.button_frame = tk.Label(self.text_frame, image=self.border_image, bg="#2B2B2B")
        self.button_frame.pack(pady=10)

        # Contribute to the Collective Dream Button (inside the frame)
        self.contribute_button = tk.Button(
            self.button_frame, text="Contribute to the\nCollective Dream",
            font=("Courier", 12, "bold"), fg="black", justify="center",
            command=self.send_collective_dream_signal, relief="raised",
            bg=self.button_bg_color, width=25, height=2  # Ensuring readable text
        )
        self.contribute_button.pack(padx=5, pady=5)  # Padding to reveal the border


        # Drawing Frame on the right
        self.drawing_frame = tk.Frame(self.main_frame, bg="#F5F5DC")
        self.drawing_frame.pack(side="right", fill="both", expand=True, padx=(20, 20))

        self.drawing_label = tk.Label(self.drawing_frame, text="Draw your dream:", font=("Courier", 14), bg="#2B2B2B", fg="#F5F5F5")
        self.drawing_label.pack(pady=5)

        # Button Panel (Top row for tools)
        self.button_panel = tk.Frame(self.drawing_frame, bg="#f0f0f0")
        self.button_panel.pack(pady=5)

        # Pen Size Selector
        tk.Label(self.button_panel, text="Pen Size:", font=("Courier", 12), bg="#f0f0f0").pack(side="left", padx=5)
        pen_size_menu = tk.OptionMenu(self.button_panel, self.pen_size, 1, 2, 3, 5, 8, 10, 15, 20, 30, 50, 100)
        pen_size_menu.config(font=("Courier", 12))
        pen_size_menu.pack(side="left", padx=5)

        # Color Picker Panel (Replacing the traditional color picker)
        self.color_frame = tk.Frame(self.button_panel, bg="#f0f0f0")
        self.color_frame.pack(side="left", padx=10)

        # Create color selection buttons
        style = ttk.Style()

        for i, color in enumerate(self.color_palette):
            # Create a unique style name for each color
            style_name = f"ColorSwatch{i}.TButton"

            # Configure that style to have the background you want
            # (some themes only respond to 'foreground' and 'background' in certain element settings)
            style.configure(style_name, background=color)

            # Then create the button using that style
            color_btn = ttk.Button(
                self.color_frame,
                text="",
                style=style_name,
                command=lambda c=color: self.set_pen_color(c),
                width=2
            )
            color_btn.pack(side="left", padx=2)



        # Eraser Button
        self.eraser_button = tk.Button(self.button_panel, text="Eraser", command=self.toggle_eraser, font=("Courier", 12))
        self.eraser_button.pack(side="left", padx=5)

        # Drawing Canvas
        self.canvas = tk.Canvas(self.drawing_frame, width=600, height=400, bg="#F5F5DC", relief="solid", bd=2)
        self.canvas.pack(pady=5)


        self.canvas.bind("<B1-Motion>", self.draw)
        self.canvas.bind("<ButtonPress-1>", self.reset_last_position)
        self.canvas.bind("<ButtonRelease-1>", self.reset_last_position)

        # Clear Button Panel (Bottom row for actions)
        self.clear_panel = tk.Frame(self.drawing_frame, bg="#2B2B2B")
        self.clear_panel.pack(pady=5)

        # Clear Button
        
        self.clear_button = ttk.Button(self.clear_panel, text="Clear", command=self.clear_canvas, bootstyle="danger")
        self.clear_button.pack(side="left", padx=5)

        # Symbol Size Slider
        tk.Label(self.clear_panel, text="Symbol Size:", font=("Courier", 12), bg="#2B2B2B", fg="#F5F5F5").pack(side="left", padx=5)
        self.symbol_size = tk.IntVar(value=50)  # Default size
        size_slider = tk.Scale(self.clear_panel, from_=20, to=200, orient="horizontal", variable=self.symbol_size, bg="#2B2B2B", fg="#F5F5F5")
        size_slider.pack(side="left", padx=5)

        # Rotation Angle Selector
        tk.Label(self.clear_panel, text="Rotation Angle:", font=("Courier", 12), bg="#2B2B2B", fg="#F5F5F5").pack(side="left", padx=5)
        self.rotation_angle = tk.IntVar(value=0)  # Default angle is 0
        rotation_menu = tk.OptionMenu(self.clear_panel, self.rotation_angle, 0, 45, 90, 135, 180, 225, 270, 315)
        rotation_menu.config(font=("Courier", 12))
        rotation_menu.pack(side="left", padx=5)

        self.drawing_frame.grid_remove()


        self.update_eeg_status(0)


        # Bind canvas events for placing symbols dynamically
        self.canvas.bind("<ButtonPress-1>", self.place_symbol_start)   # Start placing
        self.canvas.bind("<B1-Motion>", self.place_symbol_drag)        # Drag the symbol
        self.canvas.bind("<ButtonRelease-1>", self.place_symbol_release)  # Fix symbol on release

        
        # Symbol Panel (Centering the icons)
        self.symbol_panel = tk.Frame(self.drawing_frame, bg="#2B2B2B")
        self.symbol_panel.pack(side="top", fill="x", padx=10)

        # Center title label
        tk.Label(self.symbol_panel, text="Symbols:", font=("Courier", 12), bg="#2B2B2B", fg="#F5F5F5").pack(pady=5)

        # Symbol container with centering
        symbol_container = tk.Frame(self.symbol_panel, bg="#2B2B2B")
        symbol_container.pack(anchor="center")  # Center the frame containing the icons

        # Keep references to avoid garbage collection
        self.symbol_images = []

        # Add symbols to the container in a grid
        columns = 11  # Number of icons per row
        for idx, (name, img) in enumerate(self.symbols.items()):
            row = idx // columns
            col = idx % columns
            self.symbol_images.append(img)  # Keep reference to avoid garbage collection
            symbol_label = tk.Label(symbol_container, image=img)
            symbol_label.bind("<Button-1>", lambda e, name=name: self.select_symbol(name))
            symbol_label.grid(row=row, column=col, padx=5, pady=5)



            
            #symbol_button.grid(row=row, column=col, padx=5, pady=5)

        # Center-align all columns in the grid
        for col in range(columns):
            symbol_container.columnconfigure(col, weight=1)  # Center each column
        
        # Undo Button
        self.undo_button = tk.Button(self.button_panel, text="Undo", command=self.undo_last_action, font=("Courier", 12))
        self.undo_button.pack(side="left", padx=5)


    
    def resize_background(self, event):
        """Resize and reposition the background image to fit the window."""
        if self.bg_image:
            new_width = event.width
            new_height = event.height
            resized_img = Image.open("background.png").resize((new_width, new_height), Image.Resampling.LANCZOS)
            self.bg_image = ImageTk.PhotoImage(resized_img)

            # Update canvas background
            self.bg_canvas.delete("bg_image")  # Remove previous image
            self.bg_canvas.create_image(0, 0, image=self.bg_image, anchor="nw", tags="bg_image")

    def toggle_title_bar(self, event=None):
        """Toggle the title bar on and off."""
        self.title_bar_hidden = not self.title_bar_hidden
        self.root.overrideredirect(self.title_bar_hidden)

    def load_symbols(self, folder):
        """Load all symbols (images) from the given folder into a dictionary."""
        from PIL import Image, ImageTk, ImageOps  # Ensure PIL is available for image handling
        self.symbols = {}  # Dictionary to store loaded symbols
        supported_formats = (".jpg", ".jpeg", ".png")

        try:
            for file in os.listdir(folder):
                if file.lower().endswith(supported_formats):
                    path = os.path.join(folder, file)
                    name = os.path.splitext(file)[0]
                    img = Image.open(path).resize((50, 50), Image.Resampling.LANCZOS)  # Resize to thumbnail
                    # take the negative of the image
                    img = img.convert("RGBA")  # Ensure it has an alpha channel
                    r, g, b, a = img.split()  # Split channels
                    rgb_inverted = ImageOps.invert(Image.merge("RGB", (r, g, b)))  # Invert only RGB
                    img = Image.merge("RGBA", (rgb_inverted.split()[0], rgb_inverted.split()[1], rgb_inverted.split()[2], a))  # Merge back with original alpha

                    self.symbols[name] = ImageTk.PhotoImage(img)  # Load into Tkinter-compatible format
        except Exception as e:
            print(f"Error loading symbols: {e}")

    def set_pen_color(self, color):
        """Set the pen color from the predefined palette and reset symbol selection."""
        self.pen_color = color
        self.eraser_mode = False  # Disable eraser mode when choosing a new color
        self.eraser_button.config(relief="raised")  # Reset eraser button state
        self.selected_symbol = None  # Reset symbol selection when switching to pen
        print(f"Selected Pen Color: {color}, switched to drawing mode.")


                
    def select_symbol(self, symbol_name):
        """Store the selected symbol name for placement."""
        self.selected_symbol = symbol_name
        print(f"Selected symbol: {symbol_name}")


    def place_symbol_start(self, event):
        """Start placing a symbol or drawing if no symbol is selected."""
        if hasattr(self, 'selected_symbol') and self.selected_symbol:
            symbol_size = self.symbol_size.get()
            rotation_angle = self.rotation_angle.get()  # Get the current rotation angle
            img_path = os.path.join("../dream_language_symbols/no_bg_square", f"{self.selected_symbol}.png")

            try:
                img = Image.open(img_path).resize((symbol_size, symbol_size), Image.Resampling.LANCZOS)

                # Convert to RGBA to modify colors
                img = img.convert("RGBA")
                data = img.getdata()

                # Replace black pixels with off-white
                new_data = []
                for item in data:
                    if item[:3] == (0, 0, 0):  # If the pixel is black
                        new_data.append((248, 248, 242, item[3]))  # Replace with off-white while keeping transparency
                    else:
                        new_data.append(item)  # Keep other colors the same

                img.putdata(new_data)

                # Rotate and convert for Tkinter
                rotated_img = img.rotate(rotation_angle, expand=True)
                self.dragged_symbol = ImageTk.PhotoImage(rotated_img)
                self.temp_symbol = self.canvas.create_image(event.x, event.y, image=self.dragged_symbol, anchor="center")

            except Exception as e:
                print(f"Error loading symbol: {e}")
        else:
            # Default to drawing mode if no symbol is selected
            self.reset_last_position(event)


    def place_symbol_drag(self, event):
        """Drag the symbol if selected, otherwise allow drawing."""
        if hasattr(self, 'temp_symbol'):
            self.canvas.coords(self.temp_symbol, event.x, event.y)
        else:
            # Drawing behavior
            self.draw(event)

    
    def place_symbol_release(self, event):
        """Fix the symbol in place and then focus on the text entry."""
        if hasattr(self, 'temp_symbol'):
            symbol_size = self.symbol_size.get()
            rotation_angle = self.rotation_angle.get()
            img_path = os.path.join("../dream_language_symbols/no_bg_square", f"{self.selected_symbol}.png")

            try:
                if hasattr(self, 'dragged_symbol'):  # Use the already transformed image
                    tk_image = self.dragged_symbol  # Keep the off-white image
                else:
                    # Fallback in case the image was not stored properly
                    img = Image.open(img_path).resize((symbol_size, symbol_size), Image.Resampling.LANCZOS)
                    img = img.convert("RGBA")
                    data = img.getdata()
                    new_data = [(248, 248, 242, item[3]) if item[:3] == (0, 0, 0) else item for item in data]
                    img.putdata(new_data)
                    rotated_img = img.rotate(rotation_angle, expand=True)
                    tk_image = ImageTk.PhotoImage(rotated_img)

                symbol = self.canvas.create_image(event.x, event.y, image=tk_image, anchor="center")

                # Store reference to prevent garbage collection
                if not hasattr(self, "canvas_images"):
                    self.canvas_images = []
                self.canvas_images.append(tk_image)

                self.action_stack.append(symbol)  # Add to stack for undo
                self.canvas.delete(self.temp_symbol)
                del self.temp_symbol

                symbol = self.canvas.create_image(event.x, event.y, image=tk_image, anchor="center")

                # Store reference to avoid garbage collection
                if not hasattr(self, "canvas_images"):
                    self.canvas_images = []
                self.canvas_images.append(tk_image)

                self.action_stack.append(symbol)  # Add symbol to the stack

                self.canvas.delete(self.temp_symbol)
                del self.temp_symbol

                print(f"Symbol '{self.selected_symbol}' placed permanently at ({event.x}, {event.y}) with rotation {rotation_angle}°")
                self.selected_symbol = None  # Reset symbol selection
                print("Switched back to drawing mode.")
                
                self.text_entry.focus_set()  # Automatically focus on text entry after placing a symbol
                
            except Exception as e:
                print(f"Error placing symbol: {e}")
        else:
            self.reset_last_position(event)

    def toggle_eraser(self):
        """Toggle eraser mode on or off."""
        if self.eraser_mode:
            # If eraser mode is on, switch back to the last selected pen color
            self.eraser_mode = False
            self.pen_color = self.last_pen_color  # Restore the saved pen color
            self.eraser_button.config(relief="raised")
        else:
            # Save current pen color before switching to eraser
            self.last_pen_color = self.pen_color  
            self.eraser_mode = True
            self.pen_color = "white"
            self.eraser_button.config(relief="sunken")


    def choose_color(self):
        """Open color picker to choose a pen color."""
        color_code = colorchooser.askcolor(title="Choose Pen Color")[1]
        if color_code:
            self.pen_color = color_code
            self.eraser_mode = False
            self.eraser_button.config(relief="raised")

    def draw(self, event):
        """Draw on the canvas with the selected pen size and color."""
        pen_size = self.pen_size.get()
        pen_color = "white" if self.eraser_mode else self.pen_color

        if self.last_x is None or self.last_y is None:
            self.last_x, self.last_y = event.x, event.y

        line = self.canvas.create_line(self.last_x, self.last_y, event.x, event.y,
                                    width=pen_size, fill=pen_color, capstyle=tk.ROUND, smooth=True)
        self.current_drawn_lines.append(line)  # Track this line for the current draw action
        self.last_x, self.last_y = event.x, event.y
        self.send_state()



    def reset_last_position(self, event):
        """Reset the last position when the mouse is released or pressed, then focus on text entry."""
        if self.current_drawn_lines:  # If there are lines in the current draw action
            self.action_stack.append(self.current_drawn_lines)  # Add the group of lines to the action stack
            self.current_drawn_lines = []  # Reset the temporary list
        self.last_x, self.last_y = None, None
        self.text_entry.focus_set()  # Automatically focus on text entry after drawing



    def clear_canvas(self):
        """Clear the drawing canvas and reset the action stack."""
        self.canvas.delete("all")
        self.action_stack.clear()  # Clear the action stack
        self.last_activity_time = time.time()
        self.send_state()  # Update the state after clearing


    def send_text(self):
        """Send text input via OSC without changing text boldness."""
        text = self.text_entry.get("1.0", tk.END).strip()
        if text:
            self.client.send_message(b"/text_input", [text.encode()])
            
            # Temporarily change text background to indicate it was sent
            self.text_entry.config(fg="green")
            self.root.after(1000, lambda: self.text_entry.config(fg="#F8F8F2"))  # Reset color

        self.last_activity_time = time.time()
        self.send_state()

    def clear_text(self):
        """Clear the text entry box."""
        self.text_entry.delete("1.0", tk.END)


    def schedule_text_send(self):
        """Schedule sending text after 1 second of inactivity."""
        self.last_activity_time = time.time()  # Update the last activity time
        if hasattr(self, 'text_send_timer'):
            self.root.after_cancel(self.text_send_timer)  # Cancel the previous timer
        self.text_send_timer = self.root.after(1000, self.send_text_if_inactive)  # Schedule a new timer

    def send_text_if_inactive(self):
        """Send the text if 1 second has passed since the last activity."""
        if time.time() - self.last_activity_time >= 1:
            self.send_text()


    def calculate_state(self):
        """Calculate the current state based on text and drawing activity."""
        text_present = bool(self.text_entry.get("1.0", tk.END).strip())  # Check if text exists
        drawing_present = bool(self.action_stack)  # Check if any drawing actions exist

        if text_present and drawing_present:
            return 3  # Both text and drawing
        elif text_present:
            return 1  # Only text
        elif drawing_present:
            return 2  # Only drawing
        else:
            return 0  # Neither text nor drawing

    def send_state(self):
        """Send the current state as an OSC message."""
        state = self.calculate_state()
        self.client.send_message(b"/current_state", [state])  # Sending as integer
        print(f"State sent: {state}")


    def update_eeg_status(self, status):
        """Update EEG status light."""
        if not hasattr(self, "eeg_status_canvas"):
            print("EEG status canvas is not initialized yet.")
            return
        
        color = "red"  # Default color
        if status == 1:
            color = "yellow"
        elif status == 2:
            color = "green"

        self.eeg_status_canvas.delete("all")
        self.eeg_status_canvas.create_oval(10, 10, 50, 50, fill=color)



    def eeg_status_callback(self, status):
        """Callback for EEG status updates."""
        try:
            value = int(status)
            if 0 <= value <= 2:  # Ensure the value is within the expected range
                self.current_eeg_status = value  # Store current EEG status
                self.root.after(0, self.update_eeg_status, value)  # Schedule GUI update in main thread
            else:
                print(f"Unexpected EEG status value: {value}")
        except ValueError:
            print("Invalid EEG status received.")
            self.current_eeg_status = 0
            self.root.after(0, self.update_eeg_status, 0)


    def send_collective_dream_signal(self):
        """Send an OSC message with value 1 for 10 seconds, then reset to 0."""
        
        # Show the disclaimer window
        self.show_disclaimer()

        # Send the first OSC message (1)
        self.client.send_message(b"/collective_dream", [1])
        print("Collective Dream: Activated")

        # Change button appearance to indicate activation
        self.contribute_button.config(bg="lightgray", state="disabled")  

        # After 10 seconds, reset back to 0
        self.root.after(10000, self.reset_collective_dream)

            
    def reset_collective_dream(self):
        """Reset the collective dream state to 0 after 10 seconds."""
        
        # Send the second OSC message (0)
        self.client.send_message(b"/collective_dream", [0])
        print("Collective Dream: Deactivated")

        # Restore button appearance
        self.contribute_button.config(bg=self.button_bg_color, state="normal")


    def show_disclaimer(self):
        """Display a disclaimer window about data privacy."""
        disclaimer_window = tk.Toplevel(self.root)
        disclaimer_window.title("Data Privacy Notice")
        disclaimer_window.geometry("650x240")
        disclaimer_window.configure(bg="#f0f0f0")

        message = (
            "⚠️ Important Notice ⚠️\n\n"
            "The content of your dream will be recorded\n"
            "for the next 30 seconds as part of the\n"
            "Collective Dream visualization.\n\n"
            "🧠 No raw EEG data is recorded.\n"
            "🔒 Your participation remains anonymous."
            )

        label = tk.Label(disclaimer_window, text=message, font=("Courier", 12), bg="#f0f0f0", justify="center")
        label.pack(pady=20)

        close_button = tk.Button(disclaimer_window, text="OK", command=disclaimer_window.destroy, font=("Courier", 12))
        close_button.pack(pady=10)

        # Ensure the window stays on top
        disclaimer_window.transient(self.root)
        disclaimer_window.grab_set()
        self.root.wait_window(disclaimer_window)  # Pause interaction with the main window

            
    def undo_last_action(self):
        """Undo the last action on the canvas."""
        if self.action_stack:
            last_action = self.action_stack.pop()  # Get the most recent action
            if isinstance(last_action, list):  # If it's a group of lines
                for line in last_action:  # Delete each line in the group
                    self.canvas.delete(line)
            else:  # If it's a single item like a symbol
                self.canvas.delete(last_action)
            print("Undo: Removed last action.")
        else:
            print("Undo: No actions to undo.")



    def check_inactivity(self):
        """Check for user inactivity and send OSC updates for default mode."""
        inactivity_time = time.time() - self.last_activity_time
        text_present = bool(self.text_entry.get("1.0", tk.END).strip())  # Check if text exists
        drawing_present = bool(self.action_stack)  # Check if any drawing actions exist
        eeg_disconnected = self.current_eeg_status == 0  # Assuming 0 means disconnected

        # Determine if default mode should be active
        default_mode_active = 0.0  # Default to 0 (False)

        if not text_present and not drawing_present and eeg_disconnected:
            default_mode_active = 1.0  # No input + EEG disconnected

        elif inactivity_time > 180 and eeg_disconnected:
            default_mode_active = 1.0  # 3 minutes of inactivity + EEG disconnected

        # Send OSC message
        self.client.send_message(b"/default_mode", [default_mode_active])  
        print(f"Default Mode State Sent: {default_mode_active}")

        # Schedule the next inactivity check
        self.root.after(1000, self.check_inactivity)



    def run(self):
        """Run the main GUI loop."""
        self.root.mainloop()


# Run the GUI
if __name__ == "__main__":
    app = LatentDreamscapeGUI()
    app.run()
