import os
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from PySide6.QtWidgets import QApplication
from View.main_window import MainWindow


@dataclass
class AppInfo:
    title: str = 'DataHub'
    version: str = 'v1.01'

    timestamp: str = ''

    app_path: Path = Path(os.path.dirname(__file__))
    settings_path: Path = Path(f'{Path.home()}/AppData/Local/NEXTfoam/{title}/{version}')
    data_path: Path = Path(f'{settings_path}/received_data')

    pintel_path: Path = Path(f'{data_path}/pintel')
    vueron_01_path: Path = Path(f'{data_path}/vueron_01')
    vueron_02_path: Path = Path(f'{data_path}/vueron_02')
    keti_path: Path = Path(f'{data_path}/keti')
    e8ight_path: Path = Path(f'{data_path}/e8ight')
    nextfoam_path: Path = Path(f'{data_path}/nextfoam')

    on_point_data: int = 0


class Main:
    def __init__(self):
        self.app_info = AppInfo()
        self.app_info.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.main = MainWindow(self.app_info)

    def start(self):
        self.main.set_defaults()
        self.main.show()


if __name__ == '__main__':
    app = QApplication(sys.argv)

    # 스타일시트 적용 (파일이 있으면 적용, 없으면 기본 테마)
    style_path = Path(os.path.dirname(__file__)) / 'settings' / 'style.qss'
    if style_path.is_file():
        with open(style_path, 'r', encoding='utf-8') as f:
            app.setStyleSheet(f.read())

    main = Main()
    main.start()

    sys.exit(app.exec())
