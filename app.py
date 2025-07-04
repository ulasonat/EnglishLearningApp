import json
import os
from dataclasses import dataclass, asdict
from typing import List, Optional

from PySide6.QtCore import Qt, QUrl, QTimer
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFileDialog,
    QLineEdit,
    QTextEdit,
    QMessageBox,
)
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtMultimediaWidgets import QVideoWidget


@dataclass
class Word:
    term: str
    beginTimestamp: str
    endTimestamp: str
    englishMeaning: str
    turkishMeaning: str
    sampleSentenceInEnglish: str
    sampleSentenceInTurkish: str

    def begin_ms(self) -> int:
        return timestamp_to_ms(self.beginTimestamp) - 1000  # minus 1 second

    def end_ms(self) -> int:
        return timestamp_to_ms(self.endTimestamp) + 1000  # plus 1 second


def timestamp_to_ms(ts: str) -> int:
    h, m, rest = ts.split(":")
    s, ms = rest.split(",")
    total_ms = (int(h) * 3600 + int(m) * 60 + int(s)) * 1000 + int(ms)
    return total_ms


def ms_to_timestamp(ms: int) -> str:
    s, ms = divmod(ms, 1000)
    m, s = divmod(s, 60)
    h, m = divmod(m, 60)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


class UploadWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Vocabulary Learning App")
        layout = QVBoxLayout()

        self.video_path = QLineEdit()
        btn_video = QPushButton("Browse Video")
        btn_video.clicked.connect(self.browse_video)
        hl = QHBoxLayout()
        hl.addWidget(QLabel("Video File:"))
        hl.addWidget(self.video_path)
        hl.addWidget(btn_video)
        layout.addLayout(hl)

        self.srt_path = QLineEdit()
        btn_srt = QPushButton("Browse SRT")
        btn_srt.clicked.connect(self.browse_srt)
        hl = QHBoxLayout()
        hl.addWidget(QLabel("SRT File:"))
        hl.addWidget(self.srt_path)
        hl.addWidget(btn_srt)
        layout.addLayout(hl)

        self.json_path = QLineEdit()
        btn_json = QPushButton("Browse JSON")
        btn_json.clicked.connect(self.browse_json)
        btn_clip = QPushButton("Use Clipboard")
        btn_clip.clicked.connect(self.use_clipboard)
        hl = QHBoxLayout()
        hl.addWidget(QLabel("JSON File:"))
        hl.addWidget(self.json_path)
        hl.addWidget(btn_json)
        hl.addWidget(btn_clip)
        layout.addLayout(hl)

        self.start_btn = QPushButton("Start")
        self.start_btn.clicked.connect(self.start)
        layout.addWidget(self.start_btn)

        self.setLayout(layout)

    def browse_video(self):
        file, _ = QFileDialog.getOpenFileName(self, "Select Video", filter="Video Files (*.mp4 *.mkv *.avi)")
        if file:
            self.video_path.setText(file)

    def browse_srt(self):
        file, _ = QFileDialog.getOpenFileName(self, "Select SRT", filter="Subtitle Files (*.srt)")
        if file:
            self.srt_path.setText(file)

    def browse_json(self):
        file, _ = QFileDialog.getOpenFileName(self, "Select JSON", filter="JSON Files (*.json)")
        if file:
            self.json_path.setText(file)

    def use_clipboard(self):
        text = QApplication.clipboard().text()
        if text:
            tmp = os.path.join(os.getcwd(), "clipboard.json")
            with open(tmp, "w", encoding="utf-8") as f:
                f.write(text)
            self.json_path.setText(tmp)
        else:
            QMessageBox.warning(self, "Clipboard", "Clipboard is empty")

    def start(self):
        video = self.video_path.text()
        srt = self.srt_path.text()
        json_file = self.json_path.text()
        if not (video and srt and json_file):
            QMessageBox.warning(self, "Input", "Please provide video, SRT and JSON files")
            return
        try:
            with open(json_file, encoding="utf-8") as f:
                data = json.load(f)
            words = [Word(**d) for d in data]
        except Exception as e:
            QMessageBox.critical(self, "JSON Error", str(e))
            return
        self.hide()
        self.session = SessionWidget(video, words, json_file)
        self.session.show()


class SessionWidget(QWidget):
    def __init__(self, video_path: str, words: List[Word], json_path: str):
        super().__init__()
        self.setWindowTitle("Vocabulary Session")
        self.video_path = video_path
        self.words = words
        self.json_path = json_path
        self.current = 0
        self.responses: List[Optional[bool]] = [None] * len(words)

        layout = QHBoxLayout(self)

        # Video Area
        self.player = QMediaPlayer()
        self.audio = QAudioOutput()
        self.player.setAudioOutput(self.audio)
        self.video_widget = QVideoWidget()
        self.player.setVideoOutput(self.video_widget)

        layout.addWidget(self.video_widget, 65)

        # Right side text
        right_layout = QVBoxLayout()
        self.term_label = QLabel()
        self.term_label.setStyleSheet("font-size:24px; font-weight:bold;")
        self.meaning_en = QLabel()
        self.meaning_tr = QLabel()
        self.sample_en = QLabel()
        self.sample_tr = QLabel()
        for w in [self.term_label, self.meaning_en, self.meaning_tr, self.sample_en, self.sample_tr]:
            w.setWordWrap(True)
            right_layout.addWidget(w)

        button_layout = QHBoxLayout()
        self.know_btn = QPushButton("I already knew")
        self.know_btn.setStyleSheet("background-color:green; color:white;")
        self.know_btn.clicked.connect(self.mark_known)
        self.dontknow_btn = QPushButton("I didn't know")
        self.dontknow_btn.setStyleSheet("background-color:red; color:white;")
        self.dontknow_btn.clicked.connect(self.mark_unknown)
        button_layout.addWidget(self.know_btn)
        button_layout.addWidget(self.dontknow_btn)
        right_layout.addLayout(button_layout)

        nav_layout = QHBoxLayout()
        self.prev_btn = QPushButton("Previous")
        self.prev_btn.clicked.connect(self.prev_word)
        self.next_btn = QPushButton("Next")
        self.next_btn.clicked.connect(self.next_word)
        nav_layout.addWidget(self.prev_btn)
        nav_layout.addWidget(self.next_btn)
        right_layout.addLayout(nav_layout)

        layout.addLayout(right_layout, 35)

        self.timer = QTimer()
        self.timer.timeout.connect(self.check_position)

        self.update_ui()

    def update_ui(self):
        w = self.words[self.current]
        self.term_label.setText(w.term)
        self.meaning_en.setText(f"English: {w.englishMeaning}")
        self.meaning_tr.setText(f"Turkish: {w.turkishMeaning}")
        self.sample_en.setText(f"Example: {w.sampleSentenceInEnglish}")
        self.sample_tr.setText(f"Türkçe: {w.sampleSentenceInTurkish}")

        self.play_segment(w)
        self.prev_btn.setEnabled(self.current > 0)
        if self.current == len(self.words) - 1:
            self.next_btn.setText("Finish")
        else:
            self.next_btn.setText("Next")

    def play_segment(self, w: Word):
        self.player.setSource(QUrl.fromLocalFile(self.video_path))
        self.player.setPosition(max(0, w.begin_ms()))
        self.player.play()
        self.stop_ms = w.end_ms()
        self.timer.start(100)

    def check_position(self):
        if self.player.position() >= self.stop_ms:
            self.player.pause()
            self.timer.stop()

    def mark_known(self):
        self.responses[self.current] = True

    def mark_unknown(self):
        self.responses[self.current] = False

    def prev_word(self):
        if self.current > 0:
            self.current -= 1
            self.update_ui()

    def next_word(self):
        if self.current == len(self.words) - 1:
            self.finish()
            return
        if self.current < len(self.words) - 1:
            self.current += 1
            self.update_ui()

    def finish(self):
        # filter out known words
        filtered = [asdict(w) for idx, w in enumerate(self.words) if not self.responses[idx]]
        out_path = os.path.splitext(self.json_path)[0] + "_filtered.json"
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(filtered, f, ensure_ascii=False, indent=4)
        QMessageBox.information(self, "Session Complete", f"Saved filtered list to {out_path}")
        self.close()


def main():
    app = QApplication([])
    widget = UploadWidget()
    widget.resize(600, 200)
    widget.show()
    app.exec()


if __name__ == "__main__":
    main()
