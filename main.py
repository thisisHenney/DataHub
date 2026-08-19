import os
import sys
from pathlib import Path


def _run_live_viewer():
    if not getattr(sys, 'frozen', False):
        _root = Path(os.path.dirname(os.path.abspath(__file__)))
        sys.path.insert(0, str(_root / 'Lib' / 'live_viewer'))
    from main_window import run
    run()


if '--live-viewer' in sys.argv:
    _run_live_viewer()
    sys.exit(0)


from dataclasses import dataclass
from datetime import datetime
from PySide6.QtWidgets import QApplication
from View.main_window import MainWindow


@dataclass
class AppInfo:
    title: str = 'DataHub'
    version: str = 'v1.2'

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
    # MainWindow의 always-on-top 토글은 setWindowFlags()로 창을 잠깐 hide()했다 다시 보여주는데,
    # 기본값(True)이면 그 순간 "마지막 창이 닫힘"으로 인식돼 앱이 그대로 종료돼버림.
    # 종료는 MainWindow.closeEvent()에서 명시적으로 app.quit()을 호출해 처리한다.
    app.setQuitOnLastWindowClosed(False)

    # 스타일시트 적용 (파일이 있으면 적용, 없으면 기본 테마)
    style_path = Path(os.path.dirname(__file__)) / 'settings' / 'style.qss'
    if style_path.is_file():
        with open(style_path, 'r', encoding='utf-8') as f:
            app.setStyleSheet(f.read())

    main = Main()
    main.start()

    sys.exit(app.exec())
