# Caption Wave Pro (PC Version)

Caption Wave Pro is a user-friendly desktop application that automatically generates and overlays captions on video files. It uses state-of-the-art speech recognition technology to transcribe the audio and creates visually appealing, synchronized captions.

## Features

- Easy-to-use graphical interface
- Automatic speech recognition and transcription
- Customizable caption appearance
- Support for various video formats
- Real-time processing progress updates
- Option to adjust maximum words per caption line

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package installer)

### Steps

1. Clone this repository:https://github.com/NeutronStar00/Caption-Wave-Pro
   cd caption-wave-pro

2. Create a virtual environment: python -m venv venv

3. Activate the virtual environment:
- On Windows:
  ```
  venv\Scripts\activate
  ```
- On macOS and Linux:
  ```
  source venv/bin/activate
  ```

4. Install the required packages: pip install -r requirements.txt

## Usage

1. Run the application: python .\caption_maker_app.py

2. The Caption Wave Pro window will appear.

3. Click "Select Video" to choose the video file you want to caption.

4. (Optional) Adjust the "Max words per line" setting to your preference.

5. (Optional) Enter a custom name for the output file in the "Output file name" field.

6. Click "Process Video" to start the captioning process.

7. Wait for the processing to complete. The progress bar and status messages will keep you informed.

8. Once processing is finished, you can click "Open Video" to view the result.

## Creating an Executable

You can create a standalone executable of Caption Wave Pro using PyInstaller. This allows you to run the application without needing Python installed.

1. Install PyInstaller: pip install pyinstaller
2. Create the executable: pyinstaller --clean caption_maker_app.spec
3. The executable will be created in the `dist` folder. You can run it by double-clicking the `caption_maker_app.exe` file (on Windows) or `caption_maker_app` (on macOS/Linux) in this folder.

Note: Make sure to distribute the entire `dist` folder, as it contains necessary dependencies.

## Customization

- Font files: The application uses Gilroy-Bold.ttf and Gilroy-Heavy.ttf for captions. You can replace these files in the project directory to use different fonts.

- Whisper model: The application uses the "base" Whisper model by default. You can modify the `transcribe_video` function in the code to use a different model if desired.

## Troubleshooting

- If you encounter any issues, check the `stdout.log` and `stderr.log` files in the project directory for error messages.

- Ensure that you have sufficient disk space for processing videos, especially for longer files.

- Some video codecs might not be supported. If you encounter issues with a specific video, try converting it to a widely supported format like MP4 (H.264) first.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the [MIT License](LICENSE).

## Acknowledgements

- OpenAI's Whisper for speech recognition
- MoviePy for video processing
- PyQt6 for the graphical interface
