# steganography-tool-2025

Steganography Tool 

## Overview
Overview goes here!

## Features
- Detects LSB
- Generates Stego pngs
- Makes graphs for Chi mean distribution, RS mean, sample pair
deviation, sample pair equal ratio, and suspicious score
- runs analysis 
- ui display of graphs(?)

## Requirements
- Python 3.8 or newer
- Imported Packages (install via pip)
    - opencv-python
    - numpy
    - pandas
    - scipy
    - matplotlib
    - nicegui
- Google chrome or other browser compatible with nicegui


## Installation
1. Open steganography-tool-2025 directory in terminal
2. Optional: Create and activate a virtual environment (venv)
    - `python3 -m venv venv`
    - `source venv/bin/activate`
3. Confirm pip is working and install dependencies
    - `pip install --upgrade pip`
    - `pip install opencv-python numpy pandas scipy matplotlib nicegui`
4. Ensure all of the imports have no affiliated errors. Install or re-install where applicable.
5. Run any of the included program using command listed below

## Usage
- Detect Lsb
    - `python3 code/detect_lsb.py`
- Stego Generation 
    - `python3 code/generate_stego_png.py`
- Make Graphs
    - `python3 code/make_graphs.py`
- Analysis
    - `python3 code/run_analysis.py`
- UI Display (note: this will automatically run make_graphs.py)
    - `python3 code/ui.py`