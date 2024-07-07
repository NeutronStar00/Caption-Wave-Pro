import sys
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QPushButton, QVBoxLayout, QHBoxLayout,
                             QWidget, QFileDialog, QLabel, QProgressBar, QStyle, QLineEdit, QRadioButton, QButtonGroup)
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from PyQt6.QtGui import QIcon
import whisper
from moviepy.editor import VideoFileClip, ImageClip, CompositeVideoClip, AudioFileClip
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import subprocess

# Redirect stdout and stderr to files
sys.stdout = open('stdout.log', 'w')
sys.stderr = open('stderr.log', 'w')

class VideoProcessingThread(QThread):
    progress_update = pyqtSignal(str)
    progress_percent = pyqtSignal(int)
    finished = pyqtSignal(str)

    def __init__(self, video_path, output_path, max_words_per_line):  # Add max_words_per_line
        super().__init__()
        self.video_path = video_path
        self.output_path = output_path
        self.max_words_per_line = max_words_per_line  # Store the value

    def run(self):
        try:
            output_path = self.process_video_file(self.video_path)
            self.progress_percent.emit(100)
            self.finished.emit(output_path)
        except Exception as e:
            self.finished.emit(f"Error: {str(e)}")

    def process_video_file(self, video_path):
        if os.path.exists(video_path):
            self.progress_update.emit("Loading video...")
            video = VideoFileClip(video_path)
            video_width, video_height = video.size

            self.progress_update.emit("Generating transcription...")
            transcription = self.transcribe_video(video_path, self.max_words_per_line)  # Pass the value here

            self.progress_update.emit("Creating caption frames...")
            frames = self.make_caption_frames(transcription, video.duration, video_width, video_height)

            self.progress_update.emit("Combining video and captions...")
            final_video = self.create_final_video(video, frames)

            self.progress_update.emit("Writing final video...")
            final_video.write_videofile(self.output_path, codec='libx264', audio_codec='aac', threads=4, preset='ultrafast')

            return self.output_path
        else:
            raise FileNotFoundError("The specified video file does not exist.")

    def transcribe_video(self, video_path, max_words_per_line):
        self.progress_update.emit("Extracting audio from video...")
        video = VideoFileClip(video_path)
        audio = video.audio
        audio.write_audiofile("temp_audio.wav")

        self.progress_update.emit("Loading Whisper model...")
        model = whisper.load_model("base")

        self.progress_update.emit("Transcribing audio...")
        result = model.transcribe("temp_audio.wav", word_timestamps=True)

        os.remove("temp_audio.wav")

        new_segments = []
        for segment in result["segments"]:
            words = segment['words']
            for i in range(0, len(words), max_words_per_line):
                chunk = words[i:i+max_words_per_line]
                start = chunk[0]['start']
                end = chunk[-1]['end']
                new_segments.append({'start': start, 'end': end, 'words': chunk})

        return new_segments

    def create_caption_image(self, segment, current_word_index, video_width, video_height):
        words = segment['words']
        
        font_size = int(video_height / 20)
        
        img = Image.new('RGBA', (video_width, video_height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        font_path = os.path.join(os.path.dirname(__file__), "Gilroy-Bold.ttf") 
        font = ImageFont.truetype(font_path, font_size) 
        highlight_font_path = os.path.join(os.path.dirname(__file__), "Gilroy-Heavy.ttf") 
        highlight_font = ImageFont.truetype(highlight_font_path, int(font_size * 1.2))
        outline_width = 2

        max_width = video_width - 40

        x = 20
        y = video_height - int(video_height / 4)
        line_height = int(font_size * 1.5)
        words_with_spaces = [word_info['word'] + ' ' for word_info in words]
        words_with_spaces[-1] = words_with_spaces[-1].strip()

        lines = []
        current_line = []
        current_line_width = 0

        for i, word in enumerate(words_with_spaces):
            word_width = draw.textlength(word.upper(), font=font if i != current_word_index else highlight_font)
            
            if current_line_width + word_width <= max_width:
                current_line.append((i, word))
                current_line_width += word_width
            else:
                lines.append(current_line)
                current_line = [(i, word)]
                current_line_width = word_width

        if current_line:
            lines.append(current_line)

        y -= (len(lines) - 1) * line_height // 2

        for line in lines:
            line_width = sum(draw.textlength(word.upper(), font=font if i != current_word_index else highlight_font) for i, word in line)
            x = (video_width - line_width) // 2
            
            for i, word in line:
                if i == current_word_index:
                    word_width = draw.textlength(word.upper(), font=highlight_font)
                    
                    for xo in range(-outline_width, outline_width + 1):
                        for yo in range(-outline_width, outline_width + 1):
                            draw.text((x + xo, y + yo), word.upper(), font=highlight_font, fill=(0, 0, 0, 255))
                    
                    draw.text((x, y), word.upper(), font=highlight_font, fill=(255, 255, 0, 255))
                else:
                    word_width = draw.textlength(word.upper(), font=font)
                    
                    for xo in range(-outline_width, outline_width + 1):
                        for yo in range(-outline_width, outline_width + 1):
                            draw.text((x + xo, y + yo), word.upper(), font=font, fill=(0, 0, 0, 255))
                    
                    draw.text((x, y), word.upper(), font=font, fill=(255, 255, 255, 255))
                
                x += word_width
            
            y += line_height

        return np.array(img)

    def make_caption_frames(self, transcription, video_duration, video_width, video_height):
        frames = []
        total_words = sum(len(segment['words']) for segment in transcription)
        processed_words = 0

        for segment in transcription:
            for i, word_info in enumerate(segment['words']):
                start = word_info['start']
                end = word_info['end']
                caption_image = self.create_caption_image(segment, i, video_width, video_height)
                frames.append((start, end, caption_image))

                processed_words += 1
                progress = int((processed_words / total_words) * 100 * 0.8)
                self.progress_percent.emit(progress)

        if frames and frames[-1][1] < video_duration:
            last_frame = frames[-1]
            frames.append((video_duration, video_duration, last_frame[2]))

        return frames

    def create_final_video(self, video, frames):
        caption_clips = []
        for start, end, caption in frames:
            duration = end - start
            caption_clip = ImageClip(caption).set_start(start).set_duration(duration)
            caption_clips.append(caption_clip)

        final_clip = CompositeVideoClip([video] + caption_clips)
        return final_clip

class CaptionMakerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Caption Wave Pro")
        self.setGeometry(100, 100, 800, 600)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2c3e50;
            }
            QPushButton {
                background-color: #3498db;
                color: white;
                padding: 10px;
                font-size: 14px;
                border-radius: 5px;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:disabled {
                background-color: #95a5a6;
            }
            QLabel {
                font-size: 14px;
                color: #ecf0f1;
            }
            QLineEdit {
                padding: 8px;
                font-size: 14px;
                border: 1px solid #34495e;
                border-radius: 3px;
                background-color: #ecf0f1;
            }
            QProgressBar {
                border: 2px solid #3498db;
                border-radius: 5px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #3498db;
            }
        """)

        main_layout = QVBoxLayout()
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(30, 30, 30, 30)

        # Set fixed size for the window
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.WindowStaysOnTopHint)
        self.setFixedSize(800, 600) 
        
        # Title
        title_label = QLabel("Caption Wave Pro")
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #3498db; font-family: 'Gilroy';")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title_label)

        # File selection
        file_layout = QHBoxLayout()
        self.file_label = QLabel("No file selected")
        self.file_label.setStyleSheet("font-style: italic;")
        self.select_button = QPushButton("Select Video")
        self.select_button.clicked.connect(self.select_video)
        self.select_button.setIcon(QIcon(QApplication.style().standardIcon(QStyle.StandardPixmap.SP_DialogOpenButton)))
        file_layout.addWidget(self.file_label)
        file_layout.addWidget(self.select_button)
        main_layout.addLayout(file_layout)

        # Caption line length settings
        radio_layout = QHBoxLayout()
        radio_layout.addWidget(QLabel("Max words per line:"))
        self.radio_group = QButtonGroup()
        self.radio_buttons = []
        for i in range(1, 5): 
            radio_button = QRadioButton(str(i))
            radio_button.setStyleSheet("color: white;")  
            self.radio_group.addButton(radio_button)
            self.radio_buttons.append(radio_button)
            radio_layout.addWidget(radio_button)
        self.radio_buttons[0].setChecked(True)  
        main_layout.addLayout(radio_layout)

        # Output file name
        output_layout = QHBoxLayout()
        self.output_label = QLabel("Output file name:")
        self.output_edit = QLineEdit()
        self.output_edit.setPlaceholderText("Enter output file name (optional)")
        output_layout.addWidget(self.output_label)
        output_layout.addWidget(self.output_edit)
        main_layout.addLayout(output_layout)

        # Process button
        self.process_button = QPushButton("Process Video")
        self.process_button.clicked.connect(self.process_video)
        self.process_button.setEnabled(False)
        main_layout.addWidget(self.process_button, alignment=Qt.AlignmentFlag.AlignCenter)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)

        # Status label
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setWordWrap(True)
        main_layout.addWidget(self.status_label)

        # Open video button
        self.open_video_button = QPushButton("Open Video")
        self.open_video_button.setVisible(False)
        self.open_video_button.clicked.connect(self.open_video)
        main_layout.addWidget(self.open_video_button, alignment=Qt.AlignmentFlag.AlignCenter)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

    def select_video(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Select Video File", "", "Video Files (*.mp4 *.avi *.mov)")
        if file_name:
            self.file_label.setText(os.path.basename(file_name))
            self.process_button.setEnabled(True)
            self.video_path = file_name
            default_output = f"{os.path.splitext(os.path.basename(file_name))[0]}_captioned.mp4"
            self.output_edit.setText(default_output)

    def process_video(self):
        if not hasattr(self, 'video_path'):
            self.status_label.setText("Please select a video file first.")
            return

        output_name = self.output_edit.text() or f"{os.path.splitext(os.path.basename(self.video_path))[0]}_captioned.mp4"
        output_path = os.path.join(os.path.dirname(self.video_path), output_name)
        max_words_per_line = int(self.radio_group.checkedButton().text())

        self.process_button.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.status_label.setText("Processing video...")

        self.processing_thread = VideoProcessingThread(self.video_path, output_path, max_words_per_line) # Pass the value here
        self.processing_thread.progress_update.connect(self.update_progress)
        self.processing_thread.progress_percent.connect(self.update_progress_bar)
        self.processing_thread.finished.connect(self.processing_finished)
        self.processing_thread.start() # remove max_words_per_line
        

    def update_progress(self, message):
        self.status_label.setText(message)

    def update_progress_bar(self, value):
        self.progress_bar.setValue(value)

    def processing_finished(self, result):
        self.progress_bar.setVisible(False)
        self.process_button.setEnabled(True)
        if result.startswith("Error:"):
            self.status_label.setText(result)
        else:
            self.status_label.setText(f"Processing complete. Output saved to:\n{result}")
            self.open_video_button.setVisible(True)
            self.output_path = result

    def open_video(self):
        if hasattr(self, 'output_path'):
            if sys.platform == "win32":
                os.startfile(self.output_path)
            elif sys.platform == "darwin":
                subprocess.call(("open", self.output_path))
            else:
                subprocess.call(("xdg-open", self.output_path))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CaptionMakerApp()
    window.show()
    sys.exit(app.exec())