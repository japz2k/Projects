import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from PIL import ImageGrab, Image, ImageTk
import time
import os
import openpyxl
import sys
from datetime import datetime
import json
from tkcalendar import DateEntry
date_edit_mode = False

def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller .exe"""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

excel_path = resource_path("data\\comparison.xlsx")
excel_path = resource_path("data\\comparison.xlsx")
excel_icon_path = resource_path("assets\\excel.png")
save_icon_path = resource_path("assets\\save.png")
camera_icon_path = resource_path("assets\\camera.png")
view_history_icon_path = resource_path("assets\\clock.png")
reset_icon_path = resource_path("assets\\reset.png")
browse_icon_path = resource_path("assets\\open-folder.png")
confirm_icon_path = resource_path("assets\\check.png")
change_date_icon_path = resource_path("assets\\exchange.png")
revert_icon_path = resource_path("assets\\revert.png")
workbook = openpyxl.load_workbook(excel_path)
sheet = workbook.active

screenshot_taken = False  
input_history = []
MAX_HISTORY = 100


class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tip_window = None
        widget.bind("<Enter>", self.show_tip)
        widget.bind("<Leave>", self.hide_tip)

    def show_tip(self, event=None):
        if self.tip_window or not self.text:
            return
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 30
        y += self.widget.winfo_rooty() + 20
        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(tw, text=self.text, justify='left',
                         background="#ffffe0", relief='solid', borderwidth=1,
                         font=("tahoma", "9", "normal"))
        label.pack(ipadx=5, ipady=2)

    def hide_tip(self, event=None):
        if self.tip_window:
            self.tip_window.destroy()
            self.tip_window = None


def save_data():
    """Store input data in memory (up to 100 entries)"""
    global screenshot_taken

    try:
        # First check: Is station selected?
        if not station_var.get():
            messagebox.showwarning("Warning", "Please select a station first.")
            return

        # Second check: Is date entered?
        if not date_entry.get().strip():
            messagebox.showwarning("Warning", "Please enter the date first.")
            return
        
        # Third check: Are all required fields filled?
        axle_class = entry_vars['AXLE CLASS'].get().strip()
        plate_number = entry_vars['PLATE NUMBER'].get().strip().upper()
        cargo_type = entry_vars['CARGO TYPE'].get().strip()
        ramp_bridge = entry_vars['RAMP BRIDGE WEIGHT'].get().strip()
        static_scale = entry_vars['STATIC SCALE WEIGHT'].get().strip()
        speed = entry_vars['SPEED'].get().strip()

        if not (axle_class and plate_number and cargo_type and ramp_bridge and static_scale and speed):
            messagebox.showwarning("Warning", "Please complete all the details first.")
            return

        # Fourth check: Was a screenshot taken?
        if not screenshot_taken:
            messagebox.showwarning("Warning", "Please take a screenshot first before saving the input.")
            return

        # If all checks pass → proceed to save
        entry = {
            'station': station_var.get(),
            'date': date_entry.get(),
            'axle_class': int(axle_class),
            'plate_number': plate_number,
            'cargo_type': cargo_type,
            'ramp_bridge': int(ramp_bridge),
            'static_scale': int(static_scale),
            'speed': int(speed),
            'destination': destination_var.get()
        }

        input_history.append(entry)
        update_counter()
        backup_input_history()

        if len(input_history) > MAX_HISTORY:
            input_history.pop(0)

        # Clear fields for next entry
        entry_vars['AXLE CLASS'].set('')
        entry_vars['PLATE NUMBER'].set('')
        entry_vars['CARGO TYPE'].set('')
        entry_vars['RAMP BRIDGE WEIGHT'].set('')
        entry_vars['STATIC SCALE WEIGHT'].set('')
        entry_vars['SPEED'].set('')

        screenshot_taken = False

        for field_key, var in entry_vars.items():
            widget = getattr(var, "widget", None)
            if widget:
                if field_key == "CARGO TYPE":
                    widget.config(state='readonly')
                elif field_key == "WEIGHT DIFF":
                    widget.config(state='disabled')
                else:
                    widget.config(state='normal')
                    widget.configure(background="white", fg="black")
                    
        setup_readonly_keyboard_filter(cargo_dropdown, cargo_types)

        # After successful save, reset screenshot flag
        screenshot_taken = False

        status_label.config(text=f"Success! Input stored in memory", bg="skyblue", fg="black")
        root.after(3000, lambda: status_label.config(text="Ready", bg="green", fg="white"))

    except ValueError:
        messagebox.showerror("Error", "Numeric fields must contain valid numbers")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to store data:\n{str(e)}")

def print_data():
    """Save all stored inputs to Excel using the template when button is pressed"""
    if not input_history:
        messagebox.showwarning("Warning", "No data to save")
        return
        
    try:
        station_short_mapping = {
            "D STATION NO. 1": "D-1",
            "D STATION NO. 2": "D-2",
            "NR STATION NO. 1": "NR1",
            "NR STATION NO. 2": "NR2",
            "NR STATION NO. 3": "NR3",
            "S STATION NO. 1": "S1",
            "S STATION NO. 2": "S2",
            "S STATION NO. 3": "S3",
            "S STATION NO. 4": "S4",
            "S STATION NO. 5": "S5",
            "S STATION NO. 6": "S6",
        }
        
        selected_station_full = station_var.get()
        station_short = station_short_mapping.get(selected_station_full, "STATION")
        
        # Show save file dialog
        file_path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx")],
            title="Save Excel File As",
            initialfile=f"RAMP & STATIC {station_short} {datetime.now().strftime('%B %d, %Y')}.xlsx"
            )  
        
        if not file_path:  # User cancelled
            return

        # Load the template workbook
        template_workbook = openpyxl.load_workbook(excel_path)
        template_sheet = template_workbook.active
        
        # Update A1 with station name from dropdown
        selected_station = station_var.get()
        if selected_station:
            template_sheet['A1'] = f"{selected_station} WEIGH STATION"
        else:
            template_sheet['A1'] = "WEIGH STATION"

        # Write each entry to specific cells in the template
        for i, entry in enumerate(input_history):
            # Convert numeric values to integers
            try:
                axle_class = int(entry['axle_class'])
                plate_number = entry['plate_number']
                ramp_bridge = int(entry['ramp_bridge'])
                static_scale = int(entry['static_scale'])
                speed = int(entry['speed'])
            except (ValueError, TypeError):
                messagebox.showerror("Error", "Invalid numeric values in data")
                return

            # For first entry, use the template positions
            if i == 0:
                template_sheet['B2'] = entry['date']
                template_sheet['B8'] = axle_class
                template_sheet['C8'] = plate_number
                template_sheet['D8'] = entry['cargo_type']
                template_sheet['E8'] = ramp_bridge
                template_sheet['F8'] = static_scale
                template_sheet['H8'] = speed
            else:
                # For additional entries, find next empty row
                next_row = 9
                while template_sheet[f'B{next_row}'].value is not None:
                    next_row += 1
                
                # Write data to next available row as numbers
                template_sheet[f'B{next_row}'] = axle_class
                template_sheet[f'C{next_row}'] = plate_number
                template_sheet[f'D{next_row}'] = entry['cargo_type']
                template_sheet[f'E{next_row}'] = ramp_bridge
                template_sheet[f'F{next_row}'] = static_scale
                template_sheet[f'H{next_row}'] = speed

        # Save to user-selected location
        template_workbook.save(file_path)
        messagebox.showinfo("Success", f"Saved {len(input_history)} entries to:\n{file_path}")

        input_history.clear()
        update_counter()

        autosave_path = os.path.join(os.path.abspath("."), "backups", "autosave_input_history.json")
        if os.path.exists(autosave_path):
            os.remove(autosave_path)

        station_dropdown.config(state="readonly")
        station_var.set('')  # Clear selected station
        confirm_button.config(text="Confirm", command=confirm_action)

        date_entry.delete(0, tk.END)  # Clear the date
        destination_var.set('')

        status_label.config(text="Ready", bg="green", fg="white")
        
    except PermissionError:
        messagebox.showerror("Error", "Please close the template Excel file before saving")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to save data:\n{str(e)}")

def setup_readonly_keyboard_filter(combobox, valid_list):
    typed_chars = {"text": ""}

    def on_key(event):
        if event.keysym == "BackSpace":
            typed_chars["text"] = typed_chars["text"][:-1]
        elif len(event.char) == 1 and event.char.isprintable():
            typed_chars["text"] += event.char
        else:
            return

        matches = [item for item in valid_list if item.lower().startswith(typed_chars["text"].lower())]
        if matches:
            combobox.set(matches[0])

    def reset_typed_chars(event):
        typed_chars["text"] = ""

    combobox.bind("<KeyPress>", on_key)
    combobox.bind("<FocusOut>", reset_typed_chars)



def validate_integer(new_value):
    if new_value == "":
        return True
    return new_value.isdigit()

def disable_tab(event):
    return 'break'

def reset():
    # Check if all main fields are already empty
    if all(not entry_vars[key].get().strip() for key in [
        'AXLE CLASS', 'PLATE NUMBER', 'CARGO TYPE',
        'RAMP BRIDGE WEIGHT', 'STATIC SCALE WEIGHT', 'SPEED'
    ]):
        messagebox.showinfo("Info", "There is nothing to clear — all fields are already empty.")
        return

    # Ask for confirmation before resetting
    confirm = messagebox.askyesno(
        "Confirm Reset",
        "Are you sure you want to clear all input fields?",
        icon='warning'
    )

    if confirm:
        # Clear all fields
        entry_vars['AXLE CLASS'].set('')
        entry_vars['PLATE NUMBER'].set('')
        entry_vars['CARGO TYPE'].set('')
        entry_vars['RAMP BRIDGE WEIGHT'].set('')
        entry_vars['STATIC SCALE WEIGHT'].set('')
        entry_vars['SPEED'].set('')

        global screeshot_taken
        screenshot_taken = False

        # Re-enable input fields as needed
        for field_key, var in entry_vars.items():
            widget = getattr(var, "widget", None)
            if widget:
                if field_key == "CARGO TYPE":
                    widget.config(state='readonly')
                elif field_key == "WEIGHT DIFF":
                    widget.config(state='disabled')
                else:
                    widget.config(state='normal')

        entry_vars['AXLE CLASS'].widget.focus()

        status_label.config(text="All inputs cleared", bg="skyblue", fg="black")
        root.after(3000, lambda: status_label.config(text="Ready", bg="green", fg="white"))

def browse_folder():
    folder_selected = filedialog.askdirectory()
    if folder_selected:
        destination_var.set(folder_selected)

def view_history_window():
    if not input_history:
        messagebox.showinfo("History", "No history available.")
        return

    history_win = tk.Toplevel(root)
    history_win.title("Input History")
    screen_width = history_win.winfo_screenwidth()
    screen_height = history_win.winfo_screenheight()
    x = (screen_width / 2) - (700 / 2)
    y = (screen_height / 2) - (400 / 2)
    history_win.geometry(f"700x400+{int(x)}+{int(y)}")
    history_win.resizable(False, False)

    icon_path = resource_path("assets\\dump-truck.ico")
    try:
        history_win.iconbitmap(icon_path)
    except Exception as e:
        print(f"Icon load failed: {e}")

    # Display names and column widths
    column_config = {
        "#": ("#", 40),
        "axle_class": ("Axle Class", 80),
        "plate_number": ("Plate Number", 120),
        "cargo_type": ("Cargo Type", 150),
        "ramp_bridge": ("Ramp Weight", 100),
        "static_scale": ("Static Weight", 100),
        "speed": ("Speed", 80),
    }

    columns = ["#"] + [k for k in input_history[0].keys() if k not in ("station", "date", "destination")]

    # Treeview styling
    style = ttk.Style()
    style.configure("History.Treeview",
                    background="white",
                    foreground="black",
                    rowheight=25,
                    fieldbackground="white",
                    font=('Arial', 10))
    style.configure("History.Treeview.Heading",
                    background="lightgray",
                    foreground="black",
                    font=('Arial', 10, 'bold'),
                    relief="raised")
    style.map("History.Treeview",
              background=[("selected", "#d0e0ff")],
              foreground=[("selected", "black")])

    # Frame for Treeview + scrollbars
    tree_frame = tk.Frame(history_win)
    tree_frame.pack(fill='both', expand=True)

    vsb = ttk.Scrollbar(tree_frame, orient="vertical")
    vsb.pack(side="right", fill="y")

    hsb = ttk.Scrollbar(tree_frame, orient="horizontal")
    hsb.pack(side="bottom", fill="x")

    tree = ttk.Treeview(tree_frame, columns=columns, show='headings',
                        yscrollcommand=vsb.set, xscrollcommand=hsb.set,
                        style="History.Treeview")
    tree.pack(fill='both', expand=True)

    vsb.config(command=tree.yview)
    hsb.config(command=tree.xview)

    for col in columns:
        heading, width = column_config.get(col, (col.title(), 100))
        tree.heading(col, text=heading, anchor="center")
        tree.column(col, width=width, anchor="center")

    tree.tag_configure('oddrow', background='#f0f0f0')
    tree.tag_configure('evenrow', background='white')

    for idx, entry in enumerate(input_history):
        row = [idx + 1] + [entry.get(col, "") for col in columns[1:]]
        tag = 'evenrow' if idx % 2 == 0 else 'oddrow'
        tree.insert("", "end", values=row, tags=(tag,))


def validate_axle_class_input(P):
    if P == "":
        return True  # Allow clearing the field
    if P.isdigit() and len(P) <= 2:
        return True
    return False

def station_selected():
    station_dropdown.config(state='disabled')

def take_screenshot():
    global screenshot_taken
    if screenshot_taken:
        response = messagebox.askyesno("Warning", 
                                     "A screenshot has already been taken for this input.\n"
                                     "Do you want to take another screenshot?")
        if not response:
            return
        
    dest_folder = destination_var.get()
    if not dest_folder:
        messagebox.showwarning("Warning", "Please select a destination folder first.")
        return

    plate_number = entry_vars['PLATE NUMBER'].get().strip()

    if not (plate_number):
        messagebox.showwarning("Warning", "Please put a plate number first.")
        return

    try:
        # Create the overlay window
        overlay = tk.Toplevel(root)
        overlay.overrideredirect(True)
        overlay.geometry(f"{root.winfo_screenwidth()}x{root.winfo_screenheight()}+0+0")
        overlay.configure(bg='black')
        overlay.attributes('-alpha', 0.0)  # Start fully transparent
        overlay.lift()

        do_screenshot()

        for field_key, var in entry_vars.items():
            widget = getattr(var, "widget", None)
            if widget:
                if field_key == "CARGO TYPE":
                    widget.config(state='readonly')  # Keep usable for keyboard typing
                elif field_key == "WEIGHT DIFF":
                    widget.config(state='disabled')  # Always disabled (computed)
                else:
                    widget.config(state='normal')

    except Exception as e:
        messagebox.showerror("Error", f"An error occurred:\n{e}")

def do_screenshot():
    station_folder_mapping = {
    "D STATION NO. 1": "SAMPLE D-1",
    "D STATION NO. 2": "SAMPLE D-2",
    "NR STATION NO. 1": "SAMPLE NR1",
    "NR STATION NO. 2": "SAMPLE NR2",
    "NR STATION NO. 3": "SAMPLE NR3",
    "S STATION NO. 1": "SAMPLE S1",
    "S STATION NO. 2": "SAMPLE S2",
    "S STATION NO. 3": "SAMPLE S3",
    "S STATION NO. 4": "SAMPLE S4",
    "S STATION NO. 5": "SAMPLE S5",
    "S STATION NO. 6": "SAMPLE S6"
    }
    try:
        root.withdraw()
        time.sleep(0.2)
        screenshot = ImageGrab.grab()
        dest_folder = destination_var.get()
        station_name = station_var.get()
        folder_name = station_folder_mapping.get(station_name, "SAMPLE")  # Default to SAMPLE if not found
        screenshot_folder = os.path.join(dest_folder, folder_name)
        os.makedirs(screenshot_folder, exist_ok=True)

        plate_number = entry_vars['PLATE NUMBER'].get().strip()
        safe_plate_number = "".join(c for c in plate_number if c.isalnum())

        screenshot_filename = f"{safe_plate_number}.jpeg"
        screenshot_path = os.path.join(screenshot_folder, screenshot_filename)

        count = 1
        while os.path.exists(screenshot_path):
            screenshot_filename = f"{safe_plate_number}({count}).jpeg"
            screenshot_path = os.path.join(screenshot_folder, screenshot_filename)
            count += 1

        screenshot = screenshot.convert("RGB")
        screenshot.save(screenshot_path, "JPEG")
        status_label.config(text=f"Success, Screenshot saved as: {screenshot_filename}", bg="lightgreen", fg="black")
        root.after(3000, lambda: status_label.config(text="Complete all the details and Save Input", bg="green", fg="white"))

        global screenshot_taken
        screenshot_taken = True             

        for field_key, var in entry_vars.items():
            widget = getattr(var, "widget", None)
            if widget:
                widget.config(state='disabled')

    except Exception as e:
        messagebox.showerror("Error", f"An error occurred:\n{e}")
    finally:
        root.deiconify()

def update_weight_diff(*args):
    """Calculate and update weight difference automatically"""
    try:
        ramp = entry_vars['RAMP BRIDGE WEIGHT'].get()
        static = entry_vars['STATIC SCALE WEIGHT'].get()
        
        if ramp and static:
            diff = int(ramp) - int(static)
            entry_vars['WEIGHT DIFF'].set(str(diff))
            
            # Optional: Color code negative differences
            if diff < 0:
                entry_vars['WEIGHT DIFF'].widget.config(fg='red')
            else:
                entry_vars['WEIGHT DIFF'].widget.config(fg='black')
        else:
            entry_vars['WEIGHT DIFF'].set('')
    except ValueError:
        entry_vars['WEIGHT DIFF'].set('')

def update_status(message, bg_color="lightgreen", duration=3000):
    status_label.config(text=message, bg=bg_color, fg="black")
    root.after(duration, lambda: status_label.config(text="", bg="white", fg="black"))

def update_counter():
    counter_label.config(text=f"Inputs: {len(input_history)}", fg="blue")
    
    # Flash effect
    def flash():
        counter_label.config(fg="green")
        root.after(200, lambda: counter_label.config(fg="blue"))  # After 200ms, go back to blue

    flash()

def backup_input_history():
    try:
        backup_dir = os.path.join(os.path.abspath("."), "backups")
        os.makedirs(backup_dir, exist_ok=True)
        autosave_path = os.path.join(backup_dir, "autosave_input_history.json")
        with open(autosave_path, "w") as f:
            json.dump(input_history, f)
    except Exception as e:
        print(f"Failed to autosave input history: {e}")


def validate_plate_number(P):
    """Allow letters, numbers, and spaces"""
    if P == "":
        return True  # Allow clearing
    return all(c.isalnum() or c.isspace() for c in P)


# Create main window
root = tk.Tk()
root.title("Weigh Station Comparison v1.2")
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
x = (screen_width / 2) - (670 / 2)
y = (screen_height / 2) - (200 / 2)
root.geometry(f"670x220+{int(x)}+{int(y)}")
root.resizable(False, False)

icon_path = resource_path("assets\\dump-truck.ico")
try:
    root.iconbitmap(icon_path)
except Exception as e:
    print(f"Icon load failed: {e}")

# Center frame
main_frame = tk.Frame(root, highlightbackground="grey", highlightthickness=1)
main_frame.pack(padx=10, pady=10)

# ---- First Row: Dropdown and Station Label ----
first_row = tk.Frame(main_frame)
first_row.pack(pady=5)

def confirm_action():
    if not station_var.get().strip():
        messagebox.showwarning("Warning", "Please select a station before confirming.")
        return
    station_dropdown.config(state="disabled")
    confirm_button.config(image=revert_photo, command=revert_action)
    confirm_button.image = revert_photo
    for child in confirm_button.winfo_children():
        if isinstance(child, tk.Toplevel):  # This is the tooltip window
            child.destroy()
    ToolTip(confirm_button, "Change station")

def revert_action():
    station_dropdown.config(state="readonly")
    confirm_button.config(image=confirm_photo, command=confirm_action)
    confirm_button.image = confirm_photo

station_label = tk.Label(first_row, text="CHOOSE STATION :", font=('Arial', 12, 'bold'))
station_label.grid(row=0, column=0, padx=5, sticky="w")

station_var = tk.StringVar()
station_dropdown = ttk.Combobox(first_row, textvariable=station_var, values=[
    "D STATION NO. 1", "D STATION NO. 2",
    "NR STATION NO. 1", "NR STATION NO. 2", "NR STATION NO. 3",
    "S STATION NO. 1", "S STATION NO. 2", "S STATION NO. 3",
    "S STATION NO. 4", "S STATION NO. 5", "S STATION NO. 6",
], width=27, state='readonly')
station_dropdown.bind('<<ComboboxSelected>>')
station_dropdown.grid(row=0, column=1, padx=5, sticky="w")

# Confirm icon
confirm_img = Image.open(confirm_icon_path).resize((15, 15), Image.LANCZOS)
confirm_photo = ImageTk.PhotoImage(confirm_img)

# Revert icon
revert_img = Image.open(revert_icon_path).resize((15, 15), Image.LANCZOS)
revert_photo = ImageTk.PhotoImage(revert_img)

confirm_button = tk.Button(first_row, image=confirm_photo, command=confirm_action, width=17, height=17)
confirm_button.image = confirm_photo
confirm_button.grid(row=0, column=2, padx=5, sticky="w")
ToolTip(confirm_button, "Confirm station selection")

# ---- Second Row: Date and Destination Folder----
second_row = tk.Frame(main_frame)
second_row.pack(pady=2)

# Date Section
date_label = tk.Label(second_row, text="Date:", font=('Arial', 10, 'bold'))
date_label.grid(row=0, column=0, padx=5, sticky="w")

# --- Date Entry (pre-filled with system date, initially read-only) ---
date_entry = tk.Entry(second_row, width=17)
date_entry.grid(row=0, column=1, padx=5, sticky="w")
date_entry.insert(0, datetime.now().strftime("%B %d, %Y"))
date_entry.config(state='readonly')

# --- Toggle Button for Change / OK ---
def toggle_date_edit():
    global date_edit_mode

    if not date_edit_mode:
        # First click — enable editing
        date_entry.config(state='normal')
        date_entry.focus()
        change_date_button.config(image=confirm_photo)
        change_date_button.image = confirm_photo
        date_edit_mode = True
    else:
        # Second click — finalize edit
        new_date = date_entry.get().strip()
        if not new_date:
            messagebox.showwarning("Invalid Date", "Date cannot be empty.")
            return
        date_entry.config(state='readonly')
        change_date_button.config(image=revert_photo)
        change_date_button.image = revert_photo
        date_edit_mode = False
        # Update tooltip
        for child in change_date_button.winfo_children():
            if isinstance(child, tk.Toplevel):  # This is the tooltip window
                child.destroy()
        ToolTip(change_date_button, "Change date")

change_date_button = tk.Button(second_row, image=revert_photo, command=toggle_date_edit,
                               width=17, height=17)
change_date_button.image = revert_photo
change_date_button.grid(row=0, column=2, padx=5, sticky="w")
ToolTip(change_date_button, "Change date")

# Destination Folder
destination_label = tk.Label(second_row, text="Destination:", font=('Arial', 10, 'bold'))
destination_label.grid(row=0, column=3, padx=5, sticky="w")

destination_var = tk.StringVar()
destination_entry = tk.Entry(second_row, state="readonly", textvariable=destination_var, width=20)
destination_entry.grid(row=0, column=4, padx=5, pady=2, sticky="w")

browse_image = Image.open(browse_icon_path)
browse_image = browse_image.resize((20, 20), Image.LANCZOS)
browse_photo = ImageTk.PhotoImage(browse_image)

browse_button = tk.Button(second_row, image=browse_photo, compound="left", text=" Browse", width=70, command=browse_folder)
browse_button.grid(row=0, column=5, padx=5, pady=2, sticky="w")

# ---- Third and Fourth Rows: Labels and Entry Inputs ----
fields_frame = tk.Frame(main_frame)
fields_frame.pack(pady=2)

fields = [
    ("AXLE\nCLASS", "AXLE CLASS", 4),
    ("PLATE\nNUMBER", "PLATE NUMBER", 12),
    ("CARGO\nTYPE", "CARGO TYPE", 25),
    ("RAMP BRIDGE\nWEIGHT", "RAMP BRIDGE WEIGHT", 12),
    ("STATIC SCALE\nWEIGHT", "STATIC SCALE WEIGHT", 12),
    ("WEIGHT\nDIFF", "WEIGHT DIFF", 12),
    ("\nSPEED", "SPEED", 4),
]

entry_vars = {}

def setup_autocomplete_combobox(combobox, valid_list):
    last_valid = {"value": ""}

    def on_keyrelease(event):
        value = combobox.get().strip().lower()
        matches = [item for item in valid_list if item.lower().startswith(value)]
        if matches:
            combobox.set(matches[0])
            combobox.icursor(len(value))  # Keep user's typed cursor position

    def on_focusout(event):
        value = combobox.get().strip()
        if value not in valid_list:
            messagebox.showwarning("Invalid Entry", f"'{value}' is not a valid option.")
            combobox.set(last_valid["value"])
        else:
            last_valid["value"] = value

    combobox.bind("<KeyRelease>", on_keyrelease)
    combobox.bind("<FocusOut>", on_focusout)
    combobox.bind("<Return>", on_focusout)


vcmd = root.register(validate_integer)
vcmd2 = root.register(validate_axle_class_input)
vcmd_plate = root.register(validate_plate_number)

for idx, (label_text, field_key, field_width) in enumerate(fields):
    mini_frame = tk.Frame(fields_frame)
    mini_frame.grid(row=0, column=idx, padx=2, pady=2)

    lbl = tk.Label(mini_frame, text=label_text, font=("Arial", 10, "bold"), justify="center", anchor="center")
    lbl.pack()

    var = tk.StringVar()
    cargo_types = ["SAND", "SEWAGE WATER", "CEMENT", "DRINKING WATER", "OIL AND GAS", "OTHERS", 
                  "READYMIX CEMENT", "AGRICULTURAL PRODUCTS", "ASPHALT", "BLOCKS",
                  "STEEL", "LIVE STOCKS", "CONSTRUCTION DEBRIS", "STONE"]
    
    if field_key == "CARGO TYPE":
        cargo_dropdown = ttk.Combobox(mini_frame, textvariable=var, values=cargo_types, width=field_width, state="readonly")
        cargo_dropdown.pack()
        entry_vars[field_key] = var  # ✅ Add to entry_vars first
        entry_vars[field_key].widget = cargo_dropdown  # ✅ Now safe to attach widget reference
        setup_readonly_keyboard_filter(cargo_dropdown, cargo_types)
    elif field_key == "WEIGHT DIFF":
        entry = tk.Entry(mini_frame, textvariable=var, width=field_width, state="disabled", justify="center")
        entry.bind("<Tab>", disable_tab)
        entry.pack()
        entry_vars[field_key] = var
        entry_vars[field_key].widget = entry  # Store reference to the widget
    elif field_key == "AXLE CLASS":
        entry = tk.Entry(mini_frame, textvariable=var, width=field_width, justify='center', validate='key', validatecommand=(vcmd2, '%P'))
        entry.pack()
        entry_vars[field_key] = var  # ✅ First assign the variable
        entry_vars[field_key].widget = entry  # ✅ Then attach the widget
    elif field_key == "PLATE NUMBER":
        entry = tk.Entry(mini_frame, textvariable=var, justify="center", width=field_width, validate='key', validatecommand=(vcmd_plate, '%P'))
        entry.pack()
    else:
        entry = tk.Entry(mini_frame, textvariable=var, justify="center", width=field_width, validate='key', validatecommand=(vcmd, '%P'))
        entry.pack()
    
    entry_vars[field_key] = var

# Set up weight difference auto-calculation
entry_vars['RAMP BRIDGE WEIGHT'].trace_add('write', update_weight_diff)
entry_vars['STATIC SCALE WEIGHT'].trace_add('write', update_weight_diff)

# ---- Fifth Row: Save, New, Close Buttons ----
fifth_row = tk.Frame(main_frame)
fifth_row.pack(pady=7)

# Load icons and create buttons (using your existing resource_path function)
confirm_img = Image.open(confirm_icon_path).resize((15, 15), Image.LANCZOS)
confirm_photo = ImageTk.PhotoImage(confirm_img)

revert_img = Image.open(revert_icon_path).resize((15, 15), Image.LANCZOS)
revert_photo = ImageTk.PhotoImage(revert_img)

reset_image = Image.open(reset_icon_path)
reset_image = reset_image.resize((20, 20), Image.LANCZOS)
reset_photo = ImageTk.PhotoImage(reset_image)

reset_button = tk.Button(fifth_row, text=" Clear Input", image=reset_photo, compound="left", width=90, command=reset)
reset_button.grid(row=0, column=2, padx=5)

camera_image = Image.open(camera_icon_path)
camera_image = camera_image.resize((20, 20), Image.LANCZOS)
camera_photo = ImageTk.PhotoImage(camera_image)

screenshot_button = tk.Button(fifth_row, text=" Screenshot", image=camera_photo, compound="left", width=90, command=take_screenshot)
screenshot_button.grid(row=0, column=0, padx=5)

save_image = Image.open(save_icon_path)
save_image = save_image.resize((20, 20), Image.LANCZOS)
save_photo = ImageTk.PhotoImage(save_image)

save_button = tk.Button(fifth_row, text=" Save Input", image=save_photo, compound="left", width=90, command=save_data)
save_button.grid(row=0, column=1, padx=5)

excel_image = Image.open(excel_icon_path)
excel_image = excel_image.resize((20, 20), Image.LANCZOS)
excel_photo = ImageTk.PhotoImage(excel_image)

excel_button = tk.Button(fifth_row, text=" Save Excel", image=excel_photo, compound="left", width=90, command=print_data)
excel_button.grid(row=0, column=3, padx=5)

history_image = Image.open(view_history_icon_path)
history_image = history_image.resize((20, 20), Image.LANCZOS)
history_photo = ImageTk.PhotoImage(history_image)

view_history_button = tk.Button(fifth_row, text=" View History", image=history_photo, compound="left", width=100, command=view_history_window)
view_history_button.grid(row=0, column=4, padx=5)

ToolTip(reset_button, "Clear Input")
ToolTip(screenshot_button, "Shortcut: F1")
ToolTip(save_button, "Shortcut: F2")
ToolTip(excel_button, "Shortcut: F3")
ToolTip(view_history_button, "Shortcut: F4")

# Bind function key shortcuts
root.bind("<F1>", lambda event: screenshot_button.invoke())
root.bind("<F2>", lambda event: save_button.invoke())
root.bind("<F3>", lambda event: excel_button.invoke())
root.bind("<F4>", lambda event: view_history_button.invoke())
root.bind("<Control-s>", lambda event: save_button.invoke())


# ---- Counter Label ----
counter_label = tk.Label(fifth_row, text="Inputs: 00", font=("Arial", 10, "bold"), fg="blue")
counter_label.grid(row=0, column=5, padx=5)

# ---- Status Bar ----
status_frame = tk.Frame(root)
status_frame.pack(fill='x', side='bottom')

status_label = tk.Label(status_frame, text="Ready", bg='green', fg='white', anchor='center', padx=5, font=("Arial", 10))
status_label.pack(fill='x', side='bottom')

# --- Recover from crash if autosave exists ---
backup_dir = os.path.join(os.path.abspath("."), "backups")
autosave_path = os.path.join(backup_dir, "autosave_input_history.json")

if os.path.exists(autosave_path):
    try:
        with open(autosave_path, "r") as f:
            recovered_data = json.load(f)
        if recovered_data:
            restore = messagebox.askyesno("Recover Inputs", f"{len(recovered_data)} unsaved entries found. Recover them?")
            if restore:
                input_history.extend(recovered_data)
                update_counter()

                # Set station and date based on the first recovered entry
                first_entry = recovered_data[0]
                station_var.set(first_entry.get("station", ""))
                date_entry.delete(0, tk.END)
                date_entry.insert(0, first_entry.get("date", ""))
                destination_var.set(first_entry.get("destination", ""))

                # Lock station selection as if "Confirm" was pressed
                confirm_action()

    except Exception as e:
        print(f"Failed to recover autosave: {e}")

def on_exit():
    if messagebox.askokcancel("Exit", "Are you sure you want to exit the application?"):
        root.destroy()

root.protocol("WM_DELETE_WINDOW", on_exit)

root.mainloop()
