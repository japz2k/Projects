# WeighStation Comparison App

is a desktop application for managing weigh station entries with live data validation, screenshots, Excel export, and recovery from crash using autosave. Designed for use in logistics, transport compliance, and vehicle weight monitoring stations.

## 🛠️ Features

- GUI interface with Tkinter
- Drop-down station selector
- Read-only date with editable toggle
- Real-time input validation (axle class, speed, weights, plate number)
- Smart auto-completion for cargo types
- Screenshot capture with automatic folder structure
- Save entries into memory with up to 100-entry history
- Export data to pre-formatted Excel sheets
- History viewer with row striping
- Autosave + crash recovery of unsaved inputs
- F1–F4 keyboard shortcuts for common actions
- Tooltip hints for all actions

## 📁 Folder Structure
project/
├── assets/ # Contains icons (PNG/ICO)
├── data/ # Excel template (comparison.xlsx)
├── backups/ # Autosave JSONs
├── comparison_1.2.py # Main application script

## 🚀 Getting Started

### Requirements

- Python 3.8+
- Dependencies:
  - `tkinter`
  - `Pillow`
  - `openpyxl`
  - `tkcalendar`

Install dependencies using pip:

```bash
pip install pillow openpyxl tkcalendar

