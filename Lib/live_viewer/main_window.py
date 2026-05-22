from pathlib import Path
from time import sleep, time as _now_ts

import os
import sys

import numpy as np
import vtk
from vtkmodules.vtkCommonCore import vtkLookupTable
from vtkmodules.vtkCommonDataModel import vtkDataObject, vtkPlane
from vtkmodules.vtkCommonTransforms import vtkTransform
from vtkmodules.vtkFiltersCore import vtkThreshold
from vtkmodules.vtkFiltersGeneral import vtkTransformFilter
from vtkmodules.vtkFiltersGeometry import vtkDataSetSurfaceFilter, vtkGeometryFilter
from vtkmodules.vtkFiltersParallel import vtkRemoveGhosts

from PySide6.QtCore import QThread, QMimeData, QTimer, Qt, QRect, Signal
from PySide6.QtGui import QDropEvent, QDragEnterEvent, QPen, QColor
from PySide6.QtWidgets import (QApplication, QMainWindow, QLayout, QHBoxLayout, QWidget,
                                QTreeWidget, QTreeWidgetItem, QSlider, QAbstractItemView,
                                QStyledItemDelegate, QStyleOptionViewItem, QLabel, QComboBox)


# DataHub가 .vtk 파일을 쓰는 중에 읽으면 발생하는 race condition 에러를 콘솔에서 숨김
_vtk_null_output = vtk.vtkFileOutputWindow()
_vtk_null_output.SetFileName(os.devnull)
vtk.vtkOutputWindow.SetInstance(_vtk_null_output)


class GroupSeparatorDelegate(QStyledItemDelegate):
    def paint(self, painter, option, index):
        item = self.parent().itemFromIndex(index)
        if item and item.parent() is None:
            tree = self.parent()
            root = tree.invisibleRootItem()
            if root.indexOfChild(item) > 0:
                painter.save()
                pen = QPen(QColor(200, 200, 200))
                pen.setWidth(1)
                painter.setPen(pen)
                y = option.rect.top()
                painter.drawLine(option.rect.left(), y, option.rect.right(), y)
                painter.restore()
        super().paint(painter, option, index)


class GroupDragTreeWidget(QTreeWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._drag_item = None

    def startDrag(self, supportedActions):
        item = self.currentItem()
        if item and item.parent() is None:
            self._drag_item = item
            super().startDrag(supportedActions)
        else:
            self._drag_item = None

    def dropEvent(self, event: QDropEvent):
        target = self.itemAt(event.position().toPoint())
        if self._drag_item is None:
            event.ignore()
            return
        if target is not None and target.parent() is not None:
            target = target.parent()
        if target == self._drag_item:
            event.ignore()
            return

        root = self.invisibleRootItem()
        old_index = root.indexOfChild(self._drag_item)
        if old_index < 0:
            event.ignore()
            return

        slider_items = {}
        for gi in range(root.childCount()):
            group = root.child(gi)
            for ci in range(group.childCount()):
                child = group.child(ci)
                w = self.itemWidget(child, 0)
                if w:
                    slider_items[id(child)] = w

        self.blockSignals(True)

        taken = root.takeChild(old_index)
        if target is None:
            root.addChild(taken)
        else:
            new_index = root.indexOfChild(target)
            if new_index >= old_index:
                new_index += 1
            root.insertChild(new_index, taken)

        for gi in range(root.childCount()):
            group = root.child(gi)
            group.setExpanded(True)
            for ci in range(group.childCount()):
                child = group.child(ci)
                cid = id(child)
                if cid in slider_items:
                    self.setItemWidget(child, 0, slider_items[cid])

        self.blockSignals(False)
        self._drag_item = None
        event.accept()
from vtkmodules.vtkCommonColor import vtkNamedColors
from vtkmodules.vtkIOImage import vtkPNGReader

from vtkmodules.vtkIOLegacy import vtkUnstructuredGridReader, vtkDataSetReader
from vtkmodules.vtkRenderingCore import vtkDataSetMapper, vtkActor, vtkRenderWindow, vtkRenderer, \
    vtkColorTransferFunction, vtkCompositePolyDataMapper
from vtkmodules.vtkRenderingCore import (
    vtkActor,
    vtkPolyDataMapper,
    vtkProperty,
    vtkRenderWindow,
    vtkRenderWindowInteractor,
    vtkRenderer
)

# from Lib.live_viewer.main_window_ui import Ui_MainWindow
from main_window_ui import Ui_MainWindow
# from vtk_json_converter.rendering_widget_for_test.rendering_dock import RenderingView
from vtkmodules.vtkIOLegacy import vtkUnstructuredGridReader, vtkDataSetReader
from vtkmodules.vtkRenderingCore import vtkDataSetMapper, vtkActor
from PySide6.QtWidgets import QApplication


# PINTEL_VTK_PATH = Path('./dummy/pintel')
# KETI_VTK_PATH = Path('./dummy/keti')
# VUERON1_VTK_PATH = Path('./dummy/vueron_01')
# VUERON2_VTK_PATH = Path('./dummy/vueron_02')

COMMON_PATH = Path(f'{Path.home()}/AppData/Local/NEXTfoam/DataHub/v1.2/received_data')
PINTEL_VTK_PATH = COMMON_PATH / 'pintel/VTK'
KETI_VTK_PATH = COMMON_PATH / 'keti/VTK'
VUERON1_VTK_PATH = COMMON_PATH / 'vueron_02/VTK'
VUERON2_VTK_PATH = COMMON_PATH / 'vueron_01/VTK'
UNION_VTK_PATH = COMMON_PATH / 'keti/Send/VTK'

# 지도 파일별 VTK 좌표계 정렬 파라미터
# translate: 이미지 원점 오프셋 (tx, ty, tz)
# rotate: Z축 회전각 (도)
# scale: 픽셀 → 미터 변환 비율 (sx, sy, sz)
# 적용 순서: Translate → RotateZ → Scale
MAP_CONFIG = {
    'Nanji 20260522': {
        'file': 'nanji_20260522_001.png',
        'translate': (-67.5, -87, 0),
        'rotate': 0,
        'scale': (0.20825, 0.20825, 1),
    },
    'Nanji (original)': {
        'file': 'nanji_drawing_new.png',
        'translate': (-11.2, -3, 0),
        'rotate': 0,
        'scale': (0.10155, 0.10155, 1),
    },
}


_REFRESH_OPTIONS = [
    ('갱신 안함', 0), ('1초', 1), ('2초', 2), ('3초', 3), ('4초', 4), ('5초', 5),
    ('10초', 10), ('30초', 30), ('1분', 60), ('2분', 120), ('3분', 180),
    ('5분', 300), ('10분', 600), ('20분', 1200), ('30분', 1800),
]


_WRITE_GUARD_SEC = 0.15  # 이 시간보다 최근에 수정된 파일은 아직 쓰는 중일 수 있어 건너뜀


def _scan_folder(folder, sensors):
    results = {name: (None, 0, 0) for name, _ in sensors}
    if not folder.is_dir():
        return results

    prefix_map = {}
    union_names = []
    for name, ids in sensors:
        if ids >= 0:
            prefix_map[f'{ids:04d}'] = name
        else:
            union_names.append(name)

    cutoff = _now_ts() - _WRITE_GUARD_SEC

    try:
        with os.scandir(folder) as it:
            for entry in it:
                fname = entry.name
                if not fname.endswith('.vtk'):
                    continue
                stem = fname[:-4]

                if prefix_map and len(stem) > 4 and stem[4] == '_':
                    name = prefix_map.get(stem[:4])
                    if name is not None:
                        parts = stem.split('_', 2)
                        if len(parts) == 3:
                            try:
                                fdate, ftime = int(parts[1]), int(parts[2])
                                _, cur_date, cur_time = results[name]
                                if fdate > cur_date or (fdate == cur_date and ftime > cur_time):
                                    try:
                                        if entry.stat().st_mtime > cutoff:
                                            continue
                                    except OSError:
                                        continue
                                    results[name] = (entry.path, fdate, ftime)
                            except ValueError:
                                pass
                        continue

                if union_names:
                    parts = stem.split('_', 1)
                    if len(parts) == 2:
                        try:
                            fdate, ftime = int(parts[0]), int(parts[1])
                            need_update = any(
                                fdate > results[n][1] or (fdate == results[n][1] and ftime > results[n][2])
                                for n in union_names
                            )
                            if not need_update:
                                continue
                            try:
                                if entry.stat().st_mtime > cutoff:
                                    continue
                            except OSError:
                                continue
                            for name in union_names:
                                _, cur_date, cur_time = results[name]
                                if fdate > cur_date or (fdate == cur_date and ftime > cur_time):
                                    results[name] = (entry.path, fdate, ftime)
                        except ValueError:
                            pass
    except OSError:
        pass

    return results


class _FileScanThread(QThread):
    scan_done = Signal(dict)

    def __init__(self, tasks, parent=None):
        super().__init__(parent)
        self._tasks = tasks  # [(name, folder, ids), ...]

    def run(self):
        folder_groups = {}
        for name, folder, ids in self._tasks:
            folder_groups.setdefault(folder, []).append((name, ids))

        results = {}
        for folder, sensors in folder_groups.items():
            results.update(_scan_folder(folder, sensors))

        self.scan_done.emit(results)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self._ui = Ui_MainWindow()
        self._ui.setupUi(self)

        self.view_dock = self._ui.view_dock

        self.rainbow_lut = self._make_rainbow_lut()

        self._ui.pushButton.clicked.connect(self.button_clicked)

        self._combo_interval = QComboBox()
        for text, _ in _REFRESH_OPTIONS:
            self._combo_interval.addItem(text)
        self._combo_interval.setCurrentIndex(4)  # 기본값: 4초

        row_widget = QWidget()
        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(0, 0, 0, 0)
        self._ui.verticalLayout.removeWidget(self._ui.pushButton)
        row_layout.addWidget(self._ui.pushButton)
        row_layout.addWidget(QLabel('갱신 시간:'))
        row_layout.addWidget(self._combo_interval)
        self._ui.verticalLayout.insertWidget(1, row_widget)

        self._combo_interval.currentIndexChanged.connect(self._on_interval_changed)

        self.reader_dict: dict[str, vtkDataSetReader] = {}
        self.actor_dict: dict[str, vtkActor] = {}
        self._group_order = []
        self.init_vtk_actor()
        self._build_tree_panel()

        self.timer = QTimer()
        self._refresh_interval = 4
        self.time = self._refresh_interval
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self.time_goes_on)
        self.timer.start()

        self._scan_thread = None
        self._enabled_items = {}
        self._last_loaded = {}

        if getattr(sys, 'frozen', False):
            self._dir_path = sys._MEIPASS
        else:
            self._dir_path = os.path.dirname(os.path.abspath(__file__))
        self._map_actor = None
        self._map_reader = None
        self._map_tr = None
        self._map_trs = None
        for name in MAP_CONFIG:
            self._ui.comboBox_map.addItem(name)
        self._ui.comboBox_map.currentIndexChanged.connect(self._on_map_changed)

    def init_vtk_actor(self):
        # Pintel
        for i in range(1, 65):
            reader = vtkDataSetReader()
            reader.SetFileName('')
            self.reader_dict[f'Pintel {i}'] = reader

            surfaceFilter = vtkDataSetSurfaceFilter()
            surfaceFilter.SetInputConnection(reader.GetOutputPort())

            removeGhosts = vtkRemoveGhosts()
            removeGhosts.SetInputConnection(surfaceFilter.GetOutputPort())

            mapper = vtkDataSetMapper()
            mapper.SetInputConnection(removeGhosts.GetOutputPort())
            mapper.SetScalarVisibility(True)

            mapper.SetScalarModeToUseCellFieldData()
            mapper.SelectColorArray('number of people')
            mapper.SetColorModeToMapScalars()
            mapper.SetScalarRange(0, 40)
            mapper.SetLookupTable(self.rainbow_lut)

            actor = vtkActor()
            actor.SetMapper(mapper)
            actor.SetPosition(-944860, -1951930, 1)
            self.actor_dict[f'Pintel {i}'] = actor

        # Vueron
        for i in range(1, 3):
            reader = vtkDataSetReader()
            reader.SetFileName('')
            self.reader_dict[f'Vueron {i}'] = reader

            mapper = vtkPolyDataMapper()
            mapper.SetInputConnection(reader.GetOutputPort())
            # mapper.ScalarVisibilityOn()
            # mapper.SetScalarModeToUseCellData()
            # mapper.SetScalarModeToUsePointFieldData()
            # mapper.SelectColorArray('velocity')
            # mapper.SetColorModeToMapScalars()
            # mapper.SelectColorArray()
            mapper.SetColorModeToDefault()
            # mapper.SetScalarRange(0, 5)
            # mapper.SetLookupTable(self.rainbow_lut)

            actor = vtkActor()
            actor.SetMapper(mapper)
            actor.SetPosition(-944860, -1951930, 1.1)
            actor.GetProperty().SetPointSize(3)
            self.actor_dict[f'Vueron {i}'] = actor

        # KETI
        for i in [0]:
            reader = vtkDataSetReader()
            reader.SetFileName('')
            self.reader_dict['KETI'] = reader

            ths = vtkThreshold()
            ths.SetInputConnection(reader.GetOutputPort())
            ths.SetThresholdFunction(ths.THRESHOLD_BETWEEN)
            ths.SetLowerThreshold(0.1)
            ths.SetUpperThreshold(20)
            ths.SetInputArrayToProcess(0, 0, 0, vtkDataObject.FIELD_ASSOCIATION_CELLS, "density")

            # mapper = vtkCompositePolyDataMapper()
            mapper = vtkDataSetMapper()
            mapper.SetInputConnection(ths.GetOutputPort())
            mapper.ScalarVisibilityOn()

            mapper.SetScalarModeToUseCellFieldData()
            mapper.SelectColorArray('density')
            mapper.SetColorModeToMapScalars()
            mapper.SetScalarRange(0, 2)

            lut = vtkLookupTable()
            lut.SetNumberOfTableValues(64)
            lut.Build()

            ctf = vtkColorTransferFunction()
            ctf.SetColorSpaceToHSV()
            ctf.AddRGBPoint(0.0, 1.0, 1.0, 1.0)
            ctf.AddRGBPoint(1.0, 0.0, 0.0, 0.0)
            mapper.SetLookupTable(lut)

            for i in range(64):
                t = 300.0 + 100.0 * (i / 64.0)
                r, g, b = ctf.GetColor((t - 300.0) / 100.0)
                lut.SetTableValue(i, r, g, b, 1.0)

            actor = vtkActor()
            actor.SetMapper(mapper)
            actor.SetPosition(-944860, -1951930, 1)
            self.actor_dict['KETI'] = actor

        # Union
        for i, field in [(1, 'density'), (2, 'pintel_density'), (3, 'keti_density'), (4, 'vueron_density')]:
            reader = vtkDataSetReader()
            reader.SetFileName('')
            self.reader_dict[f'Union {i}'] = reader

            # ths = vtkThreshold()
            # ths.SetInputConnection(reader.GetOutputPort())
            # ths.SetThresholdFunction(ths.THRESHOLD_BETWEEN)
            # ths.SetLowerThreshold(0.1)
            # ths.SetUpperThreshold(20)
            # ths.SetInputArrayToProcess(0, 0, 0, vtkDataObject.FIELD_ASSOCIATION_CELLS, field)

            # mapper = vtkCompositePolyDataMapper()
            mapper = vtkDataSetMapper()
            mapper.SetInputConnection(reader.GetOutputPort())
            mapper.ScalarVisibilityOn()

            mapper.SetScalarModeToUseCellFieldData()
            mapper.SelectColorArray(field)
            mapper.SetColorModeToMapScalars()
            mapper.SetScalarRange(0, 10)
            if i == 4:
                mapper.SetLookupTable(self._make_white_lut())
            else:
                mapper.SetLookupTable(self.rainbow_lut)

            actor = vtkActor()
            actor.SetMapper(mapper)
            actor.SetPosition(-944860, -1951930, 10)
            actor.GetProperty().SetOpacity(0.5 if i == 4 else 0.8)
            self.actor_dict[f'Union {i}'] = actor

        # Grid
        for i in [2, 10, 100]:
            plane_dict = {
                2:   ((0, 0, 0.1), (290, 0, 0.1), (0, 240, 0.1), 145, 120, (1, 1, 1), 1),
                10:  ((0, 0, 0.2), (290, 0, 0.2), (0, 240, 0.2), 29, 24, (1, 0.7, 0.4), 2),
                100: ((-60, -30, 0.3), (340, -30, 0.3), (-60, 270, 0.3), 4, 3, (1, 0, 0), 2)}
            plane = vtk.vtkPlaneSource()
            plane.SetOrigin(*plane_dict[i][0])
            plane.SetPoint1(*plane_dict[i][1])
            plane.SetPoint2(*plane_dict[i][2])
            plane.SetResolution(plane_dict[i][3], plane_dict[i][4])

            mapper = vtkPolyDataMapper()
            mapper.SetInputConnection(plane.GetOutputPort())
            mapper.SetColorModeToDefault()

            actor = vtkActor()
            actor.SetMapper(mapper)
            actor.GetProperty().SetColor(*plane_dict[i][5])
            actor.GetProperty().SetRepresentationToWireframe()
            actor.GetProperty().SetLineWidth(plane_dict[i][6])
            actor.GetProperty().SetOpacity(0.3)
            self.actor_dict[f'grid {i}'] = actor

    def _build_tree_panel(self):
        old_list = self._ui.listWidget
        layout = old_list.parentWidget().layout()

        self.tree = GroupDragTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setColumnCount(2)
        self.tree.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.tree.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.tree.setIndentation(16)
        self.tree.setRootIsDecorated(True)
        self.tree.setItemDelegate(GroupSeparatorDelegate(self.tree))

        groups = [
            ('Grid', ['grid 2', 'grid 10', 'grid 100'], False),
            ('Pintel', [f'Pintel {i}' for i in range(1, 65)], False),
            ('KETI', ['KETI'], False),
            ('Vueron', ['Vueron 1', 'Vueron 2'], False),
            ('Union', ['Union 1', 'Union 2', 'Union 3', 'Union 4'], False),
        ]

        self._group_items = {}
        self._child_items = {}
        self._sliders = {}

        for group_name, children, default_checked in groups:
            group = QTreeWidgetItem(self.tree)
            group.setText(0, group_name)
            group.setFlags(group.flags() | Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsDragEnabled)
            group.setCheckState(0, Qt.CheckState.Checked if default_checked else Qt.CheckState.Unchecked)
            group.setExpanded(True)
            self._group_items[group_name] = group

            for child_name in children:
                child = QTreeWidgetItem(group)
                child.setText(0, child_name)
                child.setFlags(child.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                child.setFlags(child.flags() & ~Qt.ItemFlag.ItemIsDragEnabled & ~Qt.ItemFlag.ItemIsDropEnabled)
                child.setCheckState(0, Qt.CheckState.Checked if default_checked else Qt.CheckState.Unchecked)
                self._child_items[child_name] = child

            slider = QSlider(Qt.Orientation.Horizontal)
            slider.setRange(0, 100)
            slider.setValue(80 if group_name != 'Grid' else 100)
            slider.setFixedHeight(16)
            slider.setToolTip(f'{group_name} opacity')

            from PySide6.QtWidgets import QLabel, QHBoxLayout
            slider_widget = QWidget()
            slider_layout = QHBoxLayout(slider_widget)
            slider_layout.setContentsMargins(0, 0, 0, 0)
            slider_layout.setSpacing(4)
            opacity_label = QLabel('투명도')
            opacity_label.setFixedWidth(36)
            opacity_label.setStyleSheet('font-size: 8pt; color: #888;')
            slider_layout.addWidget(opacity_label)
            slider_layout.addWidget(slider)

            sep = QTreeWidgetItem(group)
            sep.setFlags(Qt.ItemFlag.NoItemFlags)
            self.tree.setItemWidget(sep, 0, slider_widget)
            self._sliders[group_name] = slider

            slider.valueChanged.connect(lambda val, gn=group_name: self._on_opacity_changed(gn, val))

        self.tree.header().setStretchLastSection(False)
        self.tree.header().setSectionResizeMode(0, self.tree.header().ResizeMode.Stretch)
        self.tree.setColumnWidth(1, 0)

        from PySide6.QtWidgets import QLabel
        hint_label = QLabel('▲▼ 그룹을 드래그하여 출력 순서 변경')
        hint_label.setStyleSheet('font-size: 7pt; color: #999; padding: 2px 0;')
        hint_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        idx = layout.indexOf(old_list)
        layout.removeWidget(old_list)
        old_list.deleteLater()
        layout.insertWidget(idx, hint_label)
        layout.insertWidget(idx + 1, self.tree)

        self.tree.itemChanged.connect(self._on_item_changed)
        self._group_order = [g[0] for g in groups]

    def _on_item_changed(self, item, column):
        if column != 0:
            return

        if item in self._group_items.values():
            checked = item.checkState(0)
            self.tree.blockSignals(True)
            for i in range(item.childCount()):
                child = item.child(i)
                if child.flags() & Qt.ItemFlag.ItemIsUserCheckable:
                    child.setCheckState(0, checked)
            self.tree.blockSignals(False)
            self._sync_actors()
        elif any(item is v for v in self._child_items.values()):
            self._sync_actors()

    def _sync_actors(self):
        for name, child in self._child_items.items():
            if child.checkState(0) == Qt.CheckState.Checked:
                if name in self.reader_dict and not self.reader_dict[name].GetFileName():
                    continue
                self.view_dock.addActor(self.actor_dict[name])
            else:
                self.view_dock.removeActor(self.actor_dict[name])
        self._apply_render_order()
        self.view_dock.refresh()

    def _on_opacity_changed(self, group_name, value):
        opacity = value / 100.0
        group = self._group_items[group_name]
        for i in range(group.childCount()):
            child = group.child(i)
            if not (child.flags() & Qt.ItemFlag.ItemIsUserCheckable):
                continue
            name = child.text(0).split(':')[0]
            if name in self.actor_dict:
                self.actor_dict[name].GetProperty().SetOpacity(opacity)
        self.view_dock.refresh()

    def _apply_render_order(self):
        renderer = self.view_dock._view.renderer()
        known_actors = set(self.actor_dict.values())

        actors = renderer.GetActors()
        actors.InitTraversal()
        current_actors = []
        other_actors = []
        for _ in range(actors.GetNumberOfItems()):
            a = actors.GetNextActor()
            if a:
                if a in known_actors:
                    current_actors.append(a)
                else:
                    other_actors.append(a)

        for actor in current_actors:
            renderer.RemoveActor(actor)

        root = self.tree.invisibleRootItem()
        for gi in range(root.childCount()):
            group = root.child(gi)
            for ci in range(group.childCount()):
                child = group.child(ci)
                if child.flags() & Qt.ItemFlag.ItemIsUserCheckable:
                    name = child.text(0).split(':')[0]
                    if name in self.actor_dict and self.actor_dict[name] in current_actors:
                        renderer.AddActor(self.actor_dict[name])

    def _init_map(self):
        name = self._ui.comboBox_map.currentText()
        cfg = MAP_CONFIG[name]
        filepath = os.path.join(self._dir_path, cfg['file'])
        tx, ty, tz = cfg['translate']
        rotate = cfg.get('rotate', 0)
        sx, sy, sz = cfg['scale']

        self._map_reader = vtkPNGReader()
        self._map_reader.SetFileName(filepath)

        self._map_tr = vtkTransform()
        self._map_tr.Translate(tx, ty, tz)
        self._map_tr.RotateZ(rotate)
        self._map_tr.Scale(sx, sy, sz)

        self._map_trs = vtkTransformFilter()
        self._map_trs.SetInputConnection(self._map_reader.GetOutputPort())
        self._map_trs.SetTransform(self._map_tr)

        mapper = vtkDataSetMapper()
        mapper.SetInputConnection(self._map_trs.GetOutputPort())

        self._map_actor = vtkActor()
        self._map_actor.SetMapper(mapper)
        self.view_dock.addActor(self._map_actor)

    def _on_map_changed(self, index):
        if self._map_reader is None:
            return
        name = self._ui.comboBox_map.itemText(index)
        cfg = MAP_CONFIG[name]
        filepath = os.path.join(self._dir_path, cfg['file'])
        tx, ty, tz = cfg['translate']
        rotate = cfg.get('rotate', 0)
        sx, sy, sz = cfg['scale']

        self._map_reader.SetFileName(filepath)
        self._map_reader.Modified()

        self._map_tr.Identity()
        self._map_tr.Translate(tx, ty, tz)
        self._map_tr.RotateZ(rotate)
        self._map_tr.Scale(sx, sy, sz)
        self._map_tr.Modified()

        self.view_dock.refresh()

    def button_clicked(self):
        self.time = self._refresh_interval
        self.read_latest_file()

    def time_goes_on(self):
        if self._refresh_interval == 0:
            self._ui.pushButton.setText('Refresh')
            return
        if self.time > 60:
            self._ui.pushButton.setText(f'refresh in {self.time // 60}m {self.time % 60}s')
        else:
            self._ui.pushButton.setText(f'refresh in {self.time} sec')
        self.time -= 1
        if self.time < 0:
            self.time = self._refresh_interval
            self.read_latest_file()

    def _on_interval_changed(self, index):
        self._refresh_interval = _REFRESH_OPTIONS[index][1]
        self.time = self._refresh_interval
        if self._refresh_interval == 0:
            self._ui.pushButton.setText('Refresh')
        elif self._refresh_interval > 60:
            self._ui.pushButton.setText(f'refresh in {self._refresh_interval // 60}m {self._refresh_interval % 60}s')
        else:
            self._ui.pushButton.setText(f'refresh in {self._refresh_interval} sec')

    def read_latest_file(self):
        if self._scan_thread is not None and self._scan_thread.isRunning():
            return

        tasks = []
        enabled_items = {}
        for name, item in self._child_items.items():
            if item.checkState(0) == Qt.CheckState.Unchecked:
                continue

            base_name = name.split(':')[0]
            if base_name[:4] == 'grid':
                continue
            elif base_name == 'KETI':
                folder, ids = KETI_VTK_PATH, 1
            elif base_name[:6] == 'Pintel':
                folder, ids = PINTEL_VTK_PATH, 100+int(base_name[7:])
            elif base_name == 'Vueron 1':
                folder, ids = VUERON1_VTK_PATH, 1
            elif base_name == 'Vueron 2':
                folder, ids = VUERON2_VTK_PATH, 2
            elif base_name[:5] == 'Union':
                folder, ids = UNION_VTK_PATH, -1
            else:
                continue

            tasks.append((base_name, folder, ids))
            enabled_items[base_name] = item

        if not tasks:
            return

        self._enabled_items = enabled_items
        self._scan_thread = _FileScanThread(tasks, self)
        self._scan_thread.scan_done.connect(self._on_scan_complete)
        self._scan_thread.start()

    def _on_scan_complete(self, results):
        self.tree.blockSignals(True)
        changed = False
        for base_name, (latest_path, latest_date, latest_time) in results.items():
            item = self._enabled_items.get(base_name)
            if item is None:
                continue

            if latest_path is None:
                item.setText(0, base_name + ': Not Found')
                self.view_dock.removeActor(self.actor_dict[base_name])
                self._last_loaded.pop(base_name, None)
                continue

            if self._last_loaded.get(base_name) != latest_path:
                self.reader_dict[base_name].SetFileName(latest_path)
                self.reader_dict[base_name].Modified()
                self.actor_dict[base_name].Modified()
                self._last_loaded[base_name] = latest_path
                changed = True

            lt = str(latest_time)
            times = lt[:-7]+':'+lt[-7:-5]+':'+lt[-5:-3]+'.'+lt[-3]
            item.setText(0, base_name + ': '+f'{latest_date:08d}'[-4:]+' '+times)
            self.view_dock.addActor(self.actor_dict[base_name])
        self.tree.blockSignals(False)
        if changed:
            self.view_dock.refresh()

    def _make_rainbow_lut(self):
        lut = vtkLookupTable()
        lut.SetNumberOfTableValues(64)
        lut.Build()

        ctf = vtkColorTransferFunction()
        ctf.SetColorSpaceToHSV()
        ctf.AddRGBPoint(0.0, 0.0, 0.0, 1.0)  # Blue
        ctf.AddRGBPoint(0.2, 0.0, 1.0, 1.0)  # Cyan
        ctf.AddRGBPoint(0.4, 0.0, 1.0, 0.0)  # Green
        ctf.AddRGBPoint(0.6, 1.0, 1.0, 0.0)  # Yellow
        ctf.AddRGBPoint(0.8, 1.0, 0.5, 0.0)  # Orange
        ctf.AddRGBPoint(1.0, 1.0, 0.0, 0.0)  # Red

        lut.SetTableValue(0, 0.0, 0.0, 0.0, 0.0)
        for i in range(1, 64):
            t = 300.0 + 100.0 * (i / 64.0)
            r, g, b = ctf.GetColor((t - 300.0) / 100.0)
            lut.SetTableValue(i, r, g, b, 0.7)
        lut.SetNanColor(0.0, 0.0, 0.0, 0.0)
        lut.SetBelowRangeColor(0.0, 0.0, 0.0, 0.0)
        lut.UseBelowRangeColorOn()
        return lut

    def _make_white_lut(self):
        lut = vtkLookupTable()
        lut.SetNumberOfTableValues(64)
        lut.Build()
        lut.SetTableValue(0, 0.0, 0.0, 0.0, 0.0)
        for i in range(1, 64):
            alpha = 0.15 + 0.45 * (i / 63.0)
            lut.SetTableValue(i, 1.0, 1.0, 1.0, alpha)
        lut.SetNanColor(0.0, 0.0, 0.0, 0.0)
        lut.SetBelowRangeColor(0.0, 0.0, 0.0, 0.0)
        lut.UseBelowRangeColorOn()
        return lut


def run():
    app = QApplication(sys.argv)

    if getattr(sys, 'frozen', False):
        style_path = Path(sys._MEIPASS) / 'settings' / 'style.qss'
    else:
        style_path = Path(os.path.abspath(__file__)).parent.parent.parent / 'settings' / 'style.qss'

    if style_path.is_file():
        with open(style_path, 'r', encoding='utf-8') as f:
            app.setStyleSheet(f.read())

    window = MainWindow()
    window.resize(800, 600)
    window.show()
    window.raise_()
    window.activateWindow()
    window.setWindowState((window.windowState() & ~Qt.WindowState.WindowMinimized) | Qt.WindowState.WindowActive)
    QTimer.singleShot(50, lambda: (window.raise_(), window.activateWindow()))

    window._init_map()

    camera = window.view_dock.view().renderer().GetActiveCamera()
    camera.SetClippingRange(1, 1e9)

    window.view_dock.refresh()
    window.view_dock.fitCamera()

    app.exec()


if __name__ == '__main__':
    run()

