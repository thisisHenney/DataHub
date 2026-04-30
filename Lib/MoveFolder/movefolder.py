import os
import shutil
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QWidget, QPushButton, QFileDialog, QVBoxLayout, QLabel


class FileMoverApp(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("파일 이동기")
        self.setGeometry(200, 200, 400, 200)

        # UI 구성
        self.layout = QVBoxLayout()

        self.info_label = QLabel("파일을 이동할 폴더와 새로운 목적지를 선택하세요.")
        self.layout.addWidget(self.info_label)

        self.select_source_btn = QPushButton("기존 폴더 선택")
        self.select_source_btn.clicked.connect(self.select_source_folder)
        self.layout.addWidget(self.select_source_btn)

        self.select_dest_btn = QPushButton("새로운 폴더 선택")
        self.select_dest_btn.clicked.connect(self.select_destination_folder)
        self.layout.addWidget(self.select_dest_btn)

        self.move_files_btn = QPushButton("파일 이동")
        self.move_files_btn.clicked.connect(self.move_files)
        self.layout.addWidget(self.move_files_btn)

        self.setLayout(self.layout)

        self.source_folder = None
        self.dest_folder = None

    def select_source_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "기존 폴더 선택")
        if folder:
            self.source_folder = folder
            self.info_label.setText(f"기존 폴더: {folder}")

    def select_destination_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "새로운 폴더 선택")
        if folder:
            self.dest_folder = folder
            self.info_label.setText(f"새로운 폴더: {folder}")

    def move_files(self):
        if not self.source_folder or not self.dest_folder:
            self.info_label.setText("기존 폴더와 새로운 폴더를 모두 선택해주세요.")
            return

        try:
            # 기존 폴더에서 모든 파일 가져오기
            files = [f for f in os.listdir(self.source_folder) if os.path.isfile(os.path.join(self.source_folder, f))]
            print(len(files))

            # 파일을 새로운 폴더로 이동
            for file in files:
                src_path = os.path.join(self.source_folder, file)
                dest_path = os.path.join(self.dest_folder, file)
                shutil.move(src_path, dest_path)

            self.info_label.setText(f"파일들이 성공적으로 이동되었습니다.")

        except Exception as e:
            self.info_label.setText(f"오류 발생: {str(e)}")


if __name__ == "__main__":
    app = QApplication([])
    window = FileMoverApp()
    window.show()
    app.exec()
