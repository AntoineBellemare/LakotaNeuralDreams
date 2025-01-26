import tkinter as tk
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
        self.root = tk.Tk()
        self.root.title("Latent Dreamscape GUI")
        self.root.geometry("600x500")
        self.last_activity_time = time.time()
        self.mode = "text"

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
        self.pen_color = "black"           # Default pen color
        self.eraser_mode = False           # Eraser state

        self.load_symbols("../dream_language_symbols/no_bg_square")
        
        self.action_stack = []  # Stack to track actions for undo
        
        self.current_drawn_lines = []  # Temporary storage for lines in the current drawing action
        
        # GUI Components
        self.setup_gui()
        self.server.bind(b"/eeg_status", self.eeg_status_callback)
        self.check_inactivity()

    def setup_gui(self):
        """Setup the GUI layout with drawing mode menu for pen size and color."""
        # Configure root grid for centering
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_rowconfigure(1, weight=0)
        self.root.grid_rowconfigure(2, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        # Main container frame
        self.main_frame = tk.Frame(self.root, bg="#f0f0f0")
        self.main_frame.pack(fill="both", expand=True)

        # Text Frame on the left
        self.text_frame = tk.Frame(self.main_frame, bg="#f0f0f0", width=300)
        self.text_frame.pack(side="left", fill="y", padx=20)  # Add padding on the left

        self.text_label = tk.Label(self.text_frame, text="Write your dream:", font=("Courier", 14), bg="#f0f0f0")
        self.text_label.pack(pady=5)
        self.text_entry = tk.Text(self.text_frame, width=40, height=20, wrap="word",
                                relief="solid", bd=2, font=("Courier", 12))
        self.text_entry.pack(pady=(100, 5))  # Adjust the top padding (100 is an example)
        self.send_button = tk.Button(self.text_frame, text="Send", command=self.send_text, font=("Courier", 12))
        self.send_button.pack(pady=5)

        # EEG Status Section (Added below the text box)
        self.eeg_frame = tk.Frame(self.text_frame, bg="#f0f0f0")
        self.eeg_frame.pack(pady=(20, 0), fill="x")  # Add spacing and ensure it spans the width

        self.eeg_label = tk.Label(self.eeg_frame, text="EEG Status", font=("Courier", 14), bg="#f0f0f0")
        self.eeg_label.pack(anchor="center")  # Center the label within the frame

        self.eeg_status_canvas = tk.Canvas(self.eeg_frame, width=60, height=60, bd=0, highlightthickness=0)
        self.eeg_status_canvas.pack(anchor="center", pady=(5, 0))  # Center the canvas below the label

        # EEG Legend Box
        self.eeg_legend_frame = tk.Frame(self.eeg_frame, bg="#f0f0f0")
        self.eeg_legend_frame.pack(anchor="center", pady=(10, 0))

        # Legend Items
        # Green Circle and Label
        self.green_canvas = tk.Canvas(self.eeg_legend_frame, width=20, height=20, bd=0, highlightthickness=0)
        self.green_canvas.create_oval(2, 2, 18, 18, fill="green")
        self.green_canvas.grid(row=0, column=0, padx=5)
        green_label = tk.Label(self.eeg_legend_frame, text="EEG good signal", font=("Courier", 10), bg="#f0f0f0")
        green_label.grid(row=0, column=1, sticky="w")

        # Yellow Circle and Label
        self.yellow_canvas = tk.Canvas(self.eeg_legend_frame, width=20, height=20, bd=0, highlightthickness=0)
        self.yellow_canvas.create_oval(2, 2, 18, 18, fill="yellow")
        self.yellow_canvas.grid(row=1, column=0, padx=5)
        yellow_label = tk.Label(self.eeg_legend_frame, text="EEG bad signal", font=("Courier", 10), bg="#f0f0f0")
        yellow_label.grid(row=1, column=1, sticky="w")

        # Red Circle and Label
        self.red_canvas = tk.Canvas(self.eeg_legend_frame, width=20, height=20, bd=0, highlightthickness=0)
        self.red_canvas.create_oval(2, 2, 18, 18, fill="red")
        self.red_canvas.grid(row=2, column=0, padx=5)
        red_label = tk.Label(self.eeg_legend_frame, text="EEG disconnected", font=("Courier", 10), bg="#f0f0f0")
        red_label.grid(row=2, column=1, sticky="w")


        # Drawing Frame on the right
        self.drawing_frame = tk.Frame(self.main_frame, bg="#f0f0f0")
        self.drawing_frame.pack(side="right", fill="both", expand=True, padx=(20, 20))

        self.drawing_label = tk.Label(self.drawing_frame, text="Draw your dream:", font=("Courier", 14), bg="#f0f0f0")
        self.drawing_label.pack(pady=5)

        # Button Panel (Top row for tools)
        self.button_panel = tk.Frame(self.drawing_frame, bg="#f0f0f0")
        self.button_panel.pack(pady=5)

        # Pen Size Selector
        tk.Label(self.button_panel, text="Pen Size:", font=("Courier", 12), bg="#f0f0f0").pack(side="left", padx=5)
        pen_size_menu = tk.OptionMenu(self.button_panel, self.pen_size, 1, 2, 3, 5, 8, 10, 15, 20, 30, 50, 100)
        pen_size_menu.config(font=("Courier", 12))
        pen_size_menu.pack(side="left", padx=5)

        # Color Picker Button
        self.color_button = tk.Button(self.button_panel, text="Choose Color", command=self.choose_color, font=("Courier", 12))
        self.color_button.pack(side="left", padx=5)

        # Eraser Button
        self.eraser_button = tk.Button(self.button_panel, text="Eraser", command=self.toggle_eraser, font=("Courier", 12))
        self.eraser_button.pack(side="left", padx=5)

        # Drawing Canvas
        self.canvas = tk.Canvas(self.drawing_frame, width=1000, height=600, bg="white", relief="solid", bd=2)
        self.canvas.pack(pady=5)
        self.canvas.bind("<B1-Motion>", self.draw)
        self.canvas.bind("<ButtonPress-1>", self.reset_last_position)
        self.canvas.bind("<ButtonRelease-1>", self.reset_last_position)

        # Clear Button Panel (Bottom row for actions)
        self.clear_panel = tk.Frame(self.drawing_frame, bg="#f0f0f0")
        self.clear_panel.pack(pady=5)

        # Clear Button
        self.clear_button = tk.Button(self.clear_panel, text="Clear", command=self.clear_canvas, font=("Courier", 12))
        self.clear_button.pack(side="left", padx=5)

        # Symbol Size Slider
        tk.Label(self.clear_panel, text="Symbol Size:", font=("Courier", 12), bg="#f0f0f0").pack(side="left", padx=5)
        self.symbol_size = tk.IntVar(value=50)  # Default size
        size_slider = tk.Scale(self.clear_panel, from_=20, to=200, orient="horizontal", variable=self.symbol_size)
        size_slider.pack(side="left", padx=5)

        # Rotation Angle Selector
        tk.Label(self.clear_panel, text="Rotation Angle:", font=("Courier", 12), bg="#f0f0f0").pack(side="left", padx=5)
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
        self.symbol_panel = tk.Frame(self.drawing_frame, bg="#f0f0f0")
        self.symbol_panel.pack(side="top", fill="x", padx=10)

        # Center title label
        tk.Label(self.symbol_panel, text="Symbols:", font=("Courier", 12), bg="#f0f0f0").pack(pady=5)

        # Symbol container with centering
        symbol_container = tk.Frame(self.symbol_panel, bg="#f0f0f0")
        symbol_container.pack(anchor="center")  # Center the frame containing the icons

        # Keep references to avoid garbage collection
        self.symbol_images = []

        # Add symbols to the container in a grid
        columns = 11  # Number of icons per row
        for idx, (name, img) in enumerate(self.symbols.items()):
            self.symbol_images.append(img)  # Keep reference to avoid garbage collection
            symbol_button = tk.Button(
                symbol_container, image=img, command=partial(self.select_symbol, name), relief="flat", bd=1
            )
            row = idx // columns
            col = idx % columns
            symbol_button.grid(row=row, column=col, padx=5, pady=5)

        # Center-align all columns in the grid
        for col in range(columns):
            symbol_container.columnconfigure(col, weight=1)  # Center each column
        
        # Undo Button
        self.undo_button = tk.Button(self.button_panel, text="Undo", command=self.undo_last_action, font=("Courier", 12))
        self.undo_button.pack(side="left", padx=5)


    def load_symbols(self, folder):
        """Load all symbols (images) from the given folder into a dictionary."""
        from PIL import Image, ImageTk  # Ensure PIL is available for image handling
        self.symbols = {}  # Dictionary to store loaded symbols
        supported_formats = (".jpg", ".jpeg", ".png")

        try:
            for file in os.listdir(folder):
                if file.lower().endswith(supported_formats):
                    path = os.path.join(folder, file)
                    name = os.path.splitext(file)[0]
                    img = Image.open(path).resize((50, 50), Image.Resampling.LANCZOS)  # Resize to thumbnail
                    self.symbols[name] = ImageTk.PhotoImage(img)  # Load into Tkinter-compatible format
        except Exception as e:
            print(f"Error loading symbols: {e}")

                
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
                rotated_img = img.rotate(rotation_angle, expand=True)  # Rotate the image
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
        """Fix the symbol in place or finalize drawing."""
        if hasattr(self, 'temp_symbol'):
            symbol_size = self.symbol_size.get()
            rotation_angle = self.rotation_angle.get()
            img_path = os.path.join("../dream_language_symbols/no_bg_square", f"{self.selected_symbol}.png")
            
            try:
                img = Image.open(img_path).resize((symbol_size, symbol_size), Image.Resampling.LANCZOS)
                rotated_img = img.rotate(rotation_angle, expand=True)  # Apply rotation
                tk_image = ImageTk.PhotoImage(rotated_img)
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
            except Exception as e:
                print(f"Error placing symbol: {e}")
        else:
            # Finalize drawing
            self.reset_last_position(event)

    def toggle_eraser(self):
        """Toggle eraser mode on or off."""
        self.eraser_mode = not self.eraser_mode
        if self.eraser_mode:
            self.eraser_button.config(relief="sunken")
            self.pen_color = "white"
        else:
            self.eraser_button.config(relief="raised")

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


    def reset_last_position(self, event):
        """Reset the last position when the mouse is released or pressed."""
        if self.current_drawn_lines:  # If there are lines in the current draw action
            self.action_stack.append(self.current_drawn_lines)  # Add the group of lines to the action stack
            self.current_drawn_lines = []  # Reset the temporary list
        self.last_x, self.last_y = None, None



    def clear_canvas(self):
        """Clear the drawing canvas."""
        self.canvas.delete("all")
        self.last_activity_time = time.time()

    def send_text(self):
        """Send text input via OSC with green feedback."""
        text = self.text_entry.get("1.0", tk.END).strip()
        if text:
            self.client.send_message(b"/text_input", [text.encode()])
            self.text_entry.config(highlightbackground="green", highlightthickness=2)
            self.root.after(1000, lambda: self.text_entry.config(highlightthickness=0))
        self.last_activity_time = time.time()

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
                self.root.after(0, self.update_eeg_status, value)  # Schedule GUI update in main thread
            else:
                print(f"Unexpected EEG status value: {value}")
        except ValueError:
            print("Invalid EEG status received.")
            self.root.after(0, self.update_eeg_status, 0)


            
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
        if time.time() - self.last_activity_time > 10:  # 5 minutes
            # Criteria met: send True
            self.client.send_message(b"/default_mode", [b"True"])
            print("Default Mode Triggered: True sent.")
        else:
            # Send False every second if criteria not met
            self.client.send_message(b"/default_mode", [b"False"])
            print("Default Mode Active: False sent.")

        # Check inactivity again after 1 second
        self.root.after(1000, self.check_inactivity)

    def run(self):
        """Run the main GUI loop."""
        self.root.mainloop()


# Run the GUI
if __name__ == "__main__":
    app = LatentDreamscapeGUI()
    app.run()
