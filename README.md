# EnglishLearningApp

A desktop application for learning English vocabulary from movie scenes. The app allows you to upload a video file, the corresponding subtitle file and a JSON word list. For each vocabulary item the relevant video excerpt is played while the definitions and example sentences are shown on the side. You can mark words that you already know and export a filtered JSON list at the end.

## Features

- Supports video formats such as MP4, MKV and AVI.
- Displays vocabulary details next to the video segment.
- Lets you mark whether you knew the word.
- Saves a new JSON file excluding the words you already knew.
- JSON data can be loaded from a file or directly from the clipboard.

## Installation

1. Install [Python 3.10+](https://www.python.org/downloads/) if you don't have it.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

This installs `PySide6` which provides the GUI and multimedia components.

## Usage

1. Launch the application:

```bash
python app.py
```

2. In the first window choose your video file, SRT subtitle file and the JSON vocabulary file. If the JSON text is in your clipboard, press **Use Clipboard** instead of selecting a file.
3. Click **Start**. The session window will open, displaying the first word.
4. Watch each excerpt and read the information on the right. Use the green **I already knew** or red **I didn't know** buttons for each word. Navigate with **Previous** and **Next**.
5. After the last word click **Finish**. A new file ending with `_filtered.json` will be created in the same folder as your original JSON, containing only the words you marked as unknown.

## Sample Data

Example subtitle (.srt) and vocabulary (.json) files are provided in the project description. You can use them to try the application.

## Notes

- Video playback relies on your system's multimedia backend. On macOS the default backend should work out of the box.
- The application saves a temporary `clipboard.json` file in the current directory if you import JSON from the clipboard.
