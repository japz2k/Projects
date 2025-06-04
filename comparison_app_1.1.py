import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from PIL import ImageGrab, Image, ImageTk
import time
import os
import openpyxl
import sys
from datetime import datetime
import json

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
close_icon_path = resource_path("assets\\exit.png")
workbook = openpyxl.load_workbook(excel_path)
sheet = workbook.active

screenshot_taken = False
input_history = []
MAX_HISTORY = 100

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
            'speed': int(speed)
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

        for field_key, var in entry_vars.items():
            widget = getattr(var, "widget", None)
            if widget:
                if field_key == "CARGO TYPE":
                    widget.config(state='disabled')
                elif field_key == "WEIGHT DIFF":
                    widget.config(state='disabled')
                else:
                    widget.config(state='normal')
                    widget.configure(background="white", fg="black")

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
            "DUKHAN STATION NO. 1": "DUKHAN-1",
            "DUKHAN STATION NO. 2": "DUKHAN-2",
            "NORTH ROAD STATION NO. 1": "NR1",
            "NORTH ROAD STATION NO. 2": "NR2",
            "NORTH ROAD STATION NO. 3": "NR3",
            "SALWA STATION NO. 1": "SW1",
            "SALWA STATION NO. 2": "SW2",
            "SALWA STATION NO. 3": "SW3",
            "SALWA STATION NO. 4": "SW4",
            "SALWA STATION NO. 5": "SW5",
            "SALWA STATION NO. 6": "SW6",
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

def check_speed():
    speed = entry_vars['SPEED'].get()
    print(f"Checking speed: {speed}")

def reset_speed():
    entry_vars['SPEED'].set('')

def validate_integer(new_value):
    if new_value == "":
        return True
    return new_value.isdigit()

def disable_tab(event):
    return 'break'

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
    history_win.geometry("700x400")
    #history_win.resizable(False, False)

    columns = ["#"] + [k for k in input_history[0].keys() if k not in ("station", "date")]

    # Define display names and widths
    column_config = {
        "#": ("#", 20),
        "axle_class": ("Axle Class", 30),
        "plate_number": ("Plate Number", 60),
        "cargo_type": ("Cargo Type", 150),
        "ramp_bridge": ("Ramp Weight", 50),
        "static_scale": ("Static Weight", 50),
        "speed": ("Speed", 20),
    }

    style = ttk.Style()
    style.theme_use("default")  # Ensure consistent styling on all systems

    # Configure Treeview headers
    style.configure("Treeview.Heading", 
                    background="lightgray", 
                    foreground="black", 
                    font=('Arial', 10, 'bold'),
                    relief="raised")

    # Optional: Configure row appearance
    style.configure("Treeview", 
                    rowheight=25, 
                    font=('Arial', 10),
                    background="white",
                    fieldbackground="white")

    tree = ttk.Treeview(history_win, columns=columns, show='headings')

    style = ttk.Style()
    style.configure("Treeview.Heading", anchor="center")
    style.configure("Treeview", rowheight=25)

    for col in columns:
        heading, width = column_config.get(col, (col.title(), 100))
        tree.heading(col, text=heading, anchor="center")
        tree.column(col, width=width, anchor="center")

    for idx, entry in enumerate(input_history):
        values = [idx + 1] + [entry.get(col, '') for col in columns[1:]]
        tree.insert("", "end", values=values)

    tree.pack(fill='both', expand=True)

    def edit_selected():
        selected = tree.focus()
        if not selected:
            messagebox.showwarning("Warning", "Select an entry to edit.")
            return

        values = tree.item(selected)['values']
        index = int(values[0]) - 1
        entry = input_history[index]

        edit_win = tk.Toplevel(history_win)
        edit_win.title(f"Edit Entry #{index+1}")

        updated_vars = {}

        visible_fields = [k for k in entry.keys() if k not in ("station", "date")]
        for i, key in enumerate(visible_fields):
            value = entry[key]
            label_text = column_config.get(key, (key.title(),))[0]
            tk.Label(edit_win, text=label_text).grid(row=i, column=0, padx=5, pady=2, sticky="e")
            var = tk.StringVar(value=str(value))
            tk.Entry(edit_win, textvariable=var, width=40).grid(row=i, column=1, padx=5, pady=2)
            updated_vars[key] = var

        def save_edits():
            for k, v in updated_vars.items():
                val = v.get()
                # Try to convert to int if original value was int
                if isinstance(entry[k], int):
                    try:
                        val = int(val)
                    except ValueError:
                        messagebox.showerror("Invalid Input", f"{k} must be an integer.")
                        return
                entry[k] = val
            tree.item(selected, values=[index+1] + [entry.get(col, '') for col in columns[1:]])
            backup_input_history()
            edit_win.destroy()

        tk.Button(edit_win, text="Save Changes", command=save_edits).grid(row=len(entry), column=0, columnspan=2, pady=10)

    tk.Button(history_win, text="Edit Selected Entry", command=edit_selected).pack(pady=5)

def validate_axle_class_input(P):
    if P == "":
        return True  # Allow clearing the field
    if P.isdigit() and len(P) <= 2:
        return True
    return False

def station_selected():
    station_dropdown.config(state='disabled')

def take_screenshot():
    dest_folder = destination_var.get()
    if not dest_folder:
        messagebox.showwarning("Warning", "Please select a destination folder first.")
        return

    axle_class = entry_vars['AXLE CLASS'].get().strip()
    plate_number = entry_vars['PLATE NUMBER'].get().strip()
    cargo_type = entry_vars['CARGO TYPE'].get().strip()
    ramp_bridge = entry_vars['RAMP BRIDGE WEIGHT'].get().strip()
    static_scale = entry_vars['STATIC SCALE WEIGHT'].get().strip()
    speed = entry_vars['SPEED'].get().strip()
    if not (plate_number and axle_class and cargo_type and ramp_bridge and static_scale and speed):
        messagebox.showwarning("Warning", "Please complete all the details first.")
        return

    try:
        # Create the overlay window
        overlay = tk.Toplevel(root)
        overlay.overrideredirect(True)
        overlay.geometry(f"{root.winfo_screenwidth()}x{root.winfo_screenheight()}+0+0")
        overlay.configure(bg='black')
        overlay.attributes('-alpha', 0.0)  # Start fully transparent
        overlay.lift()
        
        # Animate fade-in
        def fade_in(alpha=0.0):
            alpha += 0.05
            if alpha <= 0.3:
                overlay.attributes('-alpha', alpha)
                root.after(30, fade_in, alpha)
            else:
                root.after(100, fade_out)

        # Animate fade-out
        def fade_out(alpha=0.3):
            alpha -= 0.05
            if alpha >= 0.0:
                overlay.attributes('-alpha', alpha)
                root.after(30, fade_out, alpha)
            else:
                overlay.destroy()
                root.after(100, do_screenshot)

        fade_in()

    except Exception as e:
        messagebox.showerror("Error", f"An error occurred:\n{e}")



def do_screenshot():
    station_folder_mapping = {
    "DUKHAN STATION NO. 1": "SAMPLE DUKHAN-1",
    "DUKHAN STATION NO. 2": "SAMPLE DUKHAN-2",
    "NORTH ROAD STATION NO. 1": "SAMPLE NR1",
    "NORTH ROAD STATION NO. 2": "SAMPLE NR2",
    "NORTH ROAD STATION NO. 3": "SAMPLE NR3",
    "SALWA STATION NO. 1": "SAMPLE SW1",
    "SALWA STATION NO. 2": "SAMPLE SW2",
    "SALWA STATION NO. 3": "SAMPLE SW3",
    "SALWA STATION NO. 4": "SAMPLE SW4",
    "SALWA STATION NO. 5": "SAMPLE SW5",
    "SALWA STATION NO. 6": "SAMPLE SW6"
    }
    try:
        root.withdraw()
        time.sleep(0.5)
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
        root.after(3000, lambda: status_label.config(text="", bg="white", fg="black"))

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
root.title("Weigh Station Comparison")
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
    confirm_button.config(text="Revert", command=revert_action)

def revert_action():
    station_dropdown.config(state="readonly")
    confirm_button.config(text="Confirm", command=confirm_action)

station_label = tk.Label(first_row, text="CHOOSE STATION :", font=('Arial', 12, 'bold'))
station_label.grid(row=0, column=0, padx=5, sticky="w")

station_var = tk.StringVar()
station_dropdown = ttk.Combobox(first_row, textvariable=station_var, values=[
    "DUKHAN STATION NO. 1", "DUKHAN STATION NO. 2",
    "NORTH ROAD STATION NO. 1", "NORTH ROAD STATION NO. 2", "NORTH ROAD STATION NO. 3",
    "SALWA STATION NO. 1", "SALWA STATION NO. 2", "SALWA STATION NO. 3",
    "SALWA STATION NO. 4", "SALWA STATION NO. 5", "SALWA STATION NO. 6",
], width=27, state='readonly')
station_dropdown.bind('<<ComboboxSelected>>')
station_dropdown.grid(row=0, column=1, padx=5, sticky="w")

confirm_button = tk.Button(first_row, text="Confirm", command=confirm_action, width=7)
confirm_button.grid(row=0, column=2, padx=5, sticky="w")

# ---- Second Row: Date and Destination Folder----
second_row = tk.Frame(main_frame)
second_row.pack(pady=2)

# Date Section
date_label = tk.Label(second_row, text="Date:", font=('Arial', 10, 'bold'))
date_label.grid(row=0, column=0, padx=5, sticky="w")

date_entry = tk.Entry(second_row, width=17)
date_entry.grid(row=0, column=1, padx=5, sticky="w")

example_label = tk.Label(second_row, text="(EX: March 1, 2025)")
example_label.grid(row=0, column=2, padx=5, sticky="w")

# Destination Folder
destination_label = tk.Label(second_row, text="Destination:", font=('Arial', 10, 'bold'))
destination_label.grid(row=0, column=3, padx=5, sticky="w")

destination_var = tk.StringVar()
destination_entry = tk.Entry(second_row, state="readonly", textvariable=destination_var, width=20)
destination_entry.grid(row=0, column=4, padx=5, pady=2, sticky="w")

browse_button = tk.Button(second_row, text="Browse", command=browse_folder)
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

vcmd = root.register(validate_integer)
vcmd2 = root.register(validate_axle_class_input)
vcmd_plate = root.register(validate_plate_number)

for idx, (label_text, field_key, field_width) in enumerate(fields):
    mini_frame = tk.Frame(fields_frame)
    mini_frame.grid(row=0, column=idx, padx=2, pady=2)

    lbl = tk.Label(mini_frame, text=label_text, font=("Arial", 10, "bold"), justify="center", anchor="center")
    lbl.pack()

    var = tk.StringVar()
    cargo_types = ["SAND", "SEWAGE WATER", "DRINKING WATER", "OIL AND GAS", "OTHERS", 
                  "READYMIX CEMENT", "AGRICULTURAL PRODUCTS", "ASPHALT", "BLOCKS",
                  "STEEL", "LIVE STOCKS", "CONSTRUCTION DEBRIS", "STONE"]
    
    if field_key == "CARGO TYPE":
        cargo_dropdown = ttk.Combobox(mini_frame, textvariable=var, values=cargo_types, width=field_width, state="readonly")
        cargo_dropdown.pack()
    elif field_key == "WEIGHT DIFF":
        entry = tk.Entry(mini_frame, textvariable=var, width=field_width, state="disabled", justify="center")
        entry.bind("<Tab>", disable_tab)
        entry.pack()
        entry_vars[field_key] = var
        entry_vars[field_key].widget = entry  # Store reference to the widget
    elif field_key == "AXLE CLASS":
        entry = tk.Entry(mini_frame, textvariable=var, width=field_width, justify='center', validate='key', validatecommand=(vcmd2, '%P'))
        entry.pack()
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
camera_image = Image.open(camera_icon_path)
camera_image = camera_image.resize((20, 20), Image.LANCZOS)
camera_photo = ImageTk.PhotoImage(camera_image)

screenshot_button = tk.Button(fifth_row, text=" 1. Screenshot", image=camera_photo, compound="left", width=100, command=take_screenshot)
screenshot_button.grid(row=0, column=0, padx=5)

save_image = Image.open(save_icon_path)
save_image = save_image.resize((20, 20), Image.LANCZOS)
save_photo = ImageTk.PhotoImage(save_image)

save_button = tk.Button(fifth_row, text=" 2. Save Input", image=save_photo, compound="left", width=100, command=save_data)
save_button.grid(row=0, column=1, padx=5)

excel_image = Image.open(excel_icon_path)
excel_image = excel_image.resize((20, 20), Image.LANCZOS)
excel_photo = ImageTk.PhotoImage(excel_image)

excel_button = tk.Button(fifth_row, text=" 3. Save Excel", image=excel_photo, compound="left", width=100, command=print_data)
excel_button.grid(row=0, column=2, padx=5)

view_history_button = tk.Button(fifth_row, text=" View History", width=12, command=view_history_window)
view_history_button.grid(row=0, column=3, padx=5)

# ---- Counter Label ----
counter_label = tk.Label(fifth_row, text="Inputs: 0", font=("Arial", 10, "bold"), fg="blue")
counter_label.grid(row=0, column=4, padx=10)


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

                # Lock station selection as if "Confirm" was pressed
                station_dropdown.config(state="disabled")
                confirm_button.config(text="Revert", command=revert_action)

    except Exception as e:
        print(f"Failed to recover autosave: {e}")


root.mainloop()
