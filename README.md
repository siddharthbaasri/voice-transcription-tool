# Voice Transcription Desktop App

A macOS desktop application for recording audio from your microphone and transcribing it to text using the kyutai speech-to-text model. The app provides a simple interface to 
start, stop, and pause recordings, as well as to view previously transcribed recordings.

## Features

- 🎙️ Record audio directly from your microphone  
- ⏯️ Start, stop, and pause recording from the UI  
- 🧠 Instant speech-to-text transcription with just 0.5 seconds delay and automatic pause detection.
- 💾 Transcriptions saved locally as text files  
- 📂 View previous recordings within the app  
- 🖥️ Native macOS desktop experience built with PyQt

## Model

This project uses the following Hugging Face speech-to-text model:

- **Model Repo:** `kyutai/stt-1b-en_fr-mlx`  
- **Languages:** English and French  
- **Backend:** MLX (optimized for Apple Silicon)

The model is loaded and used in `record.py` to perform transcription once recording is complete.

### Prerequisites

- macOS
- Python 3.9+ (Apple Silicon recommended for MLX performance)
- Microphone access enabled for Terminal / Python

## Installation

1. Clone the repository:

```bash
git clone voice-transcription-tool
cd voice-transcription-tool
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

> **Note:** On first run, the Hugging Face model will be downloaded automatically.

## Usage

To run the application, execute:

```bash
python app.py
```

Once the app is launched, you can:

- Start recording using the UI
- Pause or stop the recording at any time
- Automatically transcribe audio after stopping
- View previously saved transcriptions

All transcriptions are stored locally as plain text files.

## Permissions

macOS may prompt you to allow microphone access.  
If the app is unable to record audio, make sure microphone permissions are enabled for the terminal or Python interpreter you are using.

## Notes & Limitations

- Only **microphone input** is supported
- Transcriptions are saved as **plain text files**
- Built specifically for **macOS** (uses MLX and PyQt)
- No cloud storage or syncing — all data remains local

## Future Work

Planned features for upcoming releases include:

- AI-powered summaries for saved recordings  
- Ability to listen to the raw audio (.wav) files in addition to viewing the transcribed text
