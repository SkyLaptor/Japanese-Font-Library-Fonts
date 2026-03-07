from __future__ import annotations

import contextlib
import io
import os
import re
import shutil
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

import yaml
from fontTools.ttLib import TTFont
from otf2ttf.cli import otf_to_ttf
from PIL import Image, ImageDraw, ImageFont
from PyQt6.QtCore import QObject, Qt, QThread, pyqtSignal
from PyQt6.QtGui import QDragEnterEvent, QDragMoveEvent, QDropEvent, QKeyEvent, QPixmap
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QDialog,
    QDoubleSpinBox,
    QFileDialog,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QSpinBox,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTextEdit,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from const import (
    BLANK_GLYPHS,
    DATA_DIR,
    MAIN_WINDOW_TITLE,
    NORMALIZED_UPM,
    PREVIEW_BASELINE_COLOR,
    PREVIEW_BASELINE_WIDTH,
    PREVIEW_DASH_GAP,
    PREVIEW_DASH_LENGTH,
    PREVIEW_FONT_SIZE,
    PREVIEW_LEGEND_BACKGROUND_COLOR,
    PREVIEW_LEGEND_FONT_CANDIDATES,
    PREVIEW_LEGEND_FONT_SIZE,
    PREVIEW_LEGEND_MARGIN_X,
    PREVIEW_LEGEND_MARGIN_Y,
    PREVIEW_LEGEND_PADDING,
    PREVIEW_LEGEND_RESERVED_HEIGHT,
    PREVIEW_LEGEND_ROW_GAP,
    PREVIEW_LEGEND_TEXT_COLOR,
    PREVIEW_METRIC_COLOR,
    PREVIEW_METRIC_WIDTH,
    PREVIEW_MIN_HEIGHT,
    PREVIEW_MIN_WIDTH,
    PREVIEW_PADDING,
    PREVIEW_UNDERLINE_COLOR,
    PREVIEW_WINDOW_TITLE,
    SUBSETS_DIR,
)
from core.ffdec_wrapper import (
    detect_java_executable,
    ensure_ffdec_runtime,
    ensure_java_runtime,
)
from core.font_loader import reopen_font
from core.font_processor import is_otf_path, process_font
from core.swf_processor import process_swf
from modules.change_weight import change_weight
from modules.create_subset import create_subset
from modules.harmonize_font_metrics import apply_font_transform, harmonize_font_metrics

PREVIEW_SAMPLE_TEXT = "0Aa永あ"
ACCEPTABLE_INPUT_FONT_SUFFIXES = {".ttf", ".otf"}


@dataclass(slots=True)
class MergeFontItem:
    font_path: str
    offset_width: int
    offset_height: int
    weight_offset: int


@dataclass(slots=True)
class SingleFontTaskConfig:
    input_ttf: str
    output_ttf: str
    subset_text_path: str
    remove_empty_glyphs: bool
    anonymize: bool
    anonymize_font_name: str
    mode: str
    horizontal_percent: float
    vertical_percent: float
    horizontal_offset: int
    vertical_offset: int
    glyph_weight_offset: int
    metric_ascent: int | None
    metric_descent: int | None
    metric_line_gap: int | None
    metric_underline_position: int | None
    metric_underline_thickness: int | None
    base_font_path: str
    merge_fonts: list[MergeFontItem]
    preview_text: str


@dataclass(slots=True)
class EmbedItem:
    ttf_path: str
    internal_name: str


@dataclass(slots=True)
class SingleEmbedTaskConfig:
    output_swf: str
    items: list[EmbedItem]


@dataclass(slots=True)
class BatchFontProcessingTaskConfig:
    recipe_path: str
    input_dir: str
    output_dir: str


@dataclass(slots=True)
class BatchSwfProcessingTaskConfig:
    recipe_path: str
    input_dir: str
    output_dir: str


class BackgroundTaskWorker(QObject):
    log_emitted = pyqtSignal(str)
    finished = pyqtSignal(bool, str)

    def __init__(
        self,
        task: Callable[[Callable[[str], None]], None],
        *,
        task_name: str,
    ) -> None:
        super().__init__()
        self._task = task
        self._task_name = task_name

    def run(self) -> None:
        try:
            self.log_emitted.emit(f"[{self._task_name}] 開始")
            self._task(self.log_emitted.emit)
            self.log_emitted.emit(f"[{self._task_name}] 完了")
            self.finished.emit(True, "")
        except Exception as error:
            message = f"[{self._task_name}] 失敗: {error}"
            self.log_emitted.emit(message)
            self.finished.emit(False, str(error))


class MergeFontsListWidget(QListWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setDragEnabled(True)
        self.setDropIndicatorShown(True)
        self.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.setDefaultDropAction(Qt.DropAction.MoveAction)

    @staticmethod
    def _normalized_path_key(path: str) -> str:
        normalized = str(Path(path).resolve(strict=False))
        return normalized.casefold()

    def add_paths(self, paths: list[str]) -> None:
        existing_keys = {
            self._normalized_path_key(self.item(index).text())
            for index in range(self.count())
        }

        for path in paths:
            if Path(path).suffix.lower() not in ACCEPTABLE_INPUT_FONT_SUFFIXES:
                continue

            key = self._normalized_path_key(path)
            if key in existing_keys:
                continue

            self.addItem(path)
            existing_keys.add(key)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            return
        super().dragEnterEvent(event)

    def dragMoveEvent(self, event: QDragMoveEvent) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            return
        super().dragMoveEvent(event)

    def dropEvent(self, event: QDropEvent) -> None:
        if event.mimeData().hasUrls():
            paths = [
                url.toLocalFile()
                for url in event.mimeData().urls()
                if url.isLocalFile()
            ]
            self.add_paths(paths)
            event.acceptProposedAction()
            return
        super().dropEvent(event)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace):
            for item in self.selectedItems():
                self.takeItem(self.row(item))
            event.accept()
            return
        super().keyPressEvent(event)


class SingleEmbedTableWidget(QTableWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(0, 2, parent)
        self.setAcceptDrops(True)
        self.setDragEnabled(True)
        self.setDropIndicatorShown(True)
        self.setDragDropMode(QAbstractItemView.DragDropMode.DragDrop)
        self.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.setDragDropOverwriteMode(False)
        self.horizontalHeader().setStretchLastSection(False)

    @staticmethod
    def _normalized_path_key(path: str) -> str:
        normalized = str(Path(path).resolve(strict=False))
        return normalized.casefold()

    def add_paths(self, paths: list[str]) -> None:
        existing_keys = {
            self._normalized_path_key(self.item(index, 0).text().strip())
            for index in range(self.rowCount())
            if self.item(index, 0) and self.item(index, 0).text().strip()
        }

        for path in paths:
            if Path(path).suffix.lower() not in ACCEPTABLE_INPUT_FONT_SUFFIXES:
                continue

            key = self._normalized_path_key(path)
            if key in existing_keys:
                continue

            row = self.rowCount()
            self.insertRow(row)
            self.setItem(row, 0, QTableWidgetItem(path))
            default_internal_name = Path(path).stem
            self.setItem(row, 1, QTableWidgetItem(default_internal_name))
            existing_keys.add(key)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            return
        super().dragEnterEvent(event)

    def dragMoveEvent(self, event: QDragMoveEvent) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            return
        super().dragMoveEvent(event)

    def dropEvent(self, event: QDropEvent) -> None:
        if event.mimeData().hasUrls():
            paths = [
                url.toLocalFile()
                for url in event.mimeData().urls()
                if url.isLocalFile()
            ]
            self.add_paths(paths)
            event.acceptProposedAction()
            return

        if event.source() is self:
            selected_rows = {
                index.row() for index in self.selectionModel().selectedRows()
            }
            if not selected_rows:
                event.ignore()
                return

            drop_position = event.position().toPoint()
            target_row = self.rowAt(drop_position.y())
            self._move_selected_rows(target_row)
            event.setDropAction(Qt.DropAction.CopyAction)
            event.accept()
            return

        super().dropEvent(event)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace):
            selected_rows = sorted(
                {index.row() for index in self.selectionModel().selectedRows()},
                reverse=True,
            )
            for row in selected_rows:
                self.removeRow(row)
            event.accept()
            return
        super().keyPressEvent(event)

    def _move_selected_rows(self, target_row: int) -> None:
        selected_rows = sorted(
            {index.row() for index in self.selectionModel().selectedRows()}
        )
        if not selected_rows:
            return

        row_payloads: list[list[QTableWidgetItem]] = []
        for row in selected_rows:
            payload: list[QTableWidgetItem] = []
            for column in range(self.columnCount()):
                item = self.item(row, column)
                payload.append(item.clone() if item else QTableWidgetItem(""))
            row_payloads.append(payload)

        if target_row < 0:
            target_row = self.rowCount()

        for row in reversed(selected_rows):
            self.removeRow(row)
            if row < target_row:
                target_row -= 1

        for offset, payload in enumerate(row_payloads):
            row = target_row + offset
            self.insertRow(row)
            for column, item in enumerate(payload):
                self.setItem(row, column, item)

        self.clearSelection()
        for offset in range(len(row_payloads)):
            self.selectRow(target_row + offset)

    def _apply_column_ratio(self) -> None:
        if self.columnCount() < 2:
            return
        width = self.viewport().width()
        if width <= 0:
            return
        left_width = int(width * 0.6)
        self.setColumnWidth(0, left_width)
        self.setColumnWidth(1, max(1, width - left_width))

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._apply_column_ratio()


class _LogStream(io.TextIOBase):
    def __init__(self, emit_line: Callable[[str], None]) -> None:
        self._emit_line = emit_line
        self._buffer = ""

    def write(self, text: str) -> int:
        if not text:
            return 0

        self._buffer += text
        while "\n" in self._buffer:
            line, self._buffer = self._buffer.split("\n", 1)
            line = line.rstrip("\r")
            if line:
                self._emit_line(line)
        return len(text)

    def flush(self) -> None:
        if self._buffer:
            line = self._buffer.rstrip("\r")
            if line:
                self._emit_line(line)
            self._buffer = ""


class MergeFontsTableWidget(QTableWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(0, 4, parent)
        self.setAcceptDrops(True)
        self.setDragEnabled(True)
        self.setDropIndicatorShown(True)
        self.setDragDropMode(QAbstractItemView.DragDropMode.DragDrop)
        self.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.setDragDropOverwriteMode(False)
        self.horizontalHeader().setStretchLastSection(False)

    @staticmethod
    def _normalized_path_key(path: str) -> str:
        normalized = str(Path(path).resolve(strict=False))
        return normalized.casefold()

    def add_paths(self, paths: list[str]) -> None:
        existing_keys = {
            self._normalized_path_key(self.item(index, 0).text().strip())
            for index in range(self.rowCount())
            if self.item(index, 0) and self.item(index, 0).text().strip()
        }

        for path in paths:
            if Path(path).suffix.lower() not in ACCEPTABLE_INPUT_FONT_SUFFIXES:
                continue

            key = self._normalized_path_key(path)
            if key in existing_keys:
                continue

            row = self.rowCount()
            self.insertRow(row)
            self.setItem(row, 0, QTableWidgetItem(path))

            w_spin = QSpinBox()
            w_spin.setRange(-5000, 5000)
            w_spin.setValue(0)
            self.setCellWidget(row, 1, w_spin)

            h_spin = QSpinBox()
            h_spin.setRange(-5000, 5000)
            h_spin.setValue(0)
            self.setCellWidget(row, 2, h_spin)

            weight_spin = QSpinBox()
            weight_spin.setRange(-5000, 5000)
            weight_spin.setValue(0)
            self.setCellWidget(row, 3, weight_spin)

            existing_keys.add(key)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            return
        super().dragEnterEvent(event)

    def dragMoveEvent(self, event: QDragMoveEvent) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            return
        super().dragMoveEvent(event)

    def dropEvent(self, event: QDropEvent) -> None:
        if event.mimeData().hasUrls():
            paths = [
                url.toLocalFile()
                for url in event.mimeData().urls()
                if url.isLocalFile()
            ]
            self.add_paths(paths)
            event.acceptProposedAction()
            return

        if event.source() is self:
            selected_rows = {
                index.row() for index in self.selectionModel().selectedRows()
            }
            if not selected_rows:
                event.ignore()
                return

            drop_position = event.position().toPoint()
            target_row = self.rowAt(drop_position.y())
            self._move_selected_rows(target_row)
            event.setDropAction(Qt.DropAction.CopyAction)
            event.accept()
            return

        super().dropEvent(event)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace):
            selected_rows = sorted(
                {index.row() for index in self.selectionModel().selectedRows()},
                reverse=True,
            )
            for row in selected_rows:
                self.removeRow(row)
            event.accept()
            return
        super().keyPressEvent(event)

    def _move_selected_rows(self, target_row: int) -> None:
        selected_rows = sorted(
            {index.row() for index in self.selectionModel().selectedRows()}
        )
        if not selected_rows:
            return

        row_payloads: list[tuple[list[QTableWidgetItem], list[object]]] = []
        for row in selected_rows:
            items_payload: list[QTableWidgetItem] = []
            widgets_payload: list[object] = []
            # column 0 is QTableWidgetItem, others are widgets
            item0 = self.item(row, 0)
            items_payload.append(item0.clone() if item0 else QTableWidgetItem(""))
            widgets_payload.append(self.cellWidget(row, 1))
            widgets_payload.append(self.cellWidget(row, 2))
            widgets_payload.append(self.cellWidget(row, 3))
            row_payloads.append((items_payload, widgets_payload))

        if target_row < 0:
            target_row = self.rowCount()

        for row in reversed(selected_rows):
            self.removeRow(row)
            if row < target_row:
                target_row -= 1

        for offset, (items_payload, widgets_payload) in enumerate(row_payloads):
            row = target_row + offset
            self.insertRow(row)
            # restore item
            self.setItem(row, 0, items_payload[0])

            # restore widgets (need to clone values into new widgets)
            def _clone_spin(widget):
                if isinstance(widget, QDoubleSpinBox):
                    s = QDoubleSpinBox()
                    s.setRange(widget.minimum(), widget.maximum())
                    s.setValue(widget.value())
                    return s
                if isinstance(widget, QSpinBox):
                    s = QSpinBox()
                    s.setRange(widget.minimum(), widget.maximum())
                    s.setValue(widget.value())
                    return s
                return None

            w_spin = _clone_spin(widgets_payload[0])
            h_spin = _clone_spin(widgets_payload[1])
            weight_spin = _clone_spin(widgets_payload[2])
            if w_spin:
                self.setCellWidget(row, 1, w_spin)
            if h_spin:
                self.setCellWidget(row, 2, h_spin)
            if weight_spin:
                self.setCellWidget(row, 3, weight_spin)

        self.clearSelection()
        for offset in range(len(row_payloads)):
            self.selectRow(target_row + offset)

    def _apply_column_ratio(self) -> None:
        if self.columnCount() < 4:
            return
        width = self.viewport().width()
        if width <= 0:
            return
        path_width = int(width * 0.6)
        remain = max(1, width - path_width)
        num_cols = 3
        each = max(1, remain // num_cols)
        self.setColumnWidth(0, path_width)
        self.setColumnWidth(1, each)
        self.setColumnWidth(2, each)
        self.setColumnWidth(3, remain - each * 2)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._apply_column_ratio()


class SingleFontProcessingTab(QWidget):
    execute_requested = pyqtSignal(object)
    preview_requested = pyqtSignal(object)
    log_emitted = pyqtSignal(str)
    _EXECUTE_LABEL = "個別処理を実行"
    _EXECUTING_LABEL = "個別処理を実行中..."

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._syncing_scale_values = False
        self._last_horizontal_percent = 100.0
        self._last_vertical_percent = 100.0
        self._build_ui()

    def _build_ui(self) -> None:
        root_layout = QVBoxLayout(self)

        io_group = QGroupBox("入出力")
        io_layout = QVBoxLayout(io_group)
        self.input_ttf_edit = QLineEdit()
        self.output_ttf_edit = QLineEdit()
        input_label = QLabel("対象フォント")
        output_label = QLabel("フォント出力先")
        btn_browse_input = QPushButton("選択")
        btn_browse_output = QPushButton("選択")
        btn_browse_input.clicked.connect(self._select_input_ttf)
        btn_browse_output.clicked.connect(self._select_output_ttf)

        io_label_width = max(
            input_label.sizeHint().width(), output_label.sizeHint().width()
        )
        input_label.setFixedWidth(io_label_width)
        output_label.setFixedWidth(io_label_width)

        io_button_width = max(
            btn_browse_input.sizeHint().width(),
            btn_browse_output.sizeHint().width(),
        )
        btn_browse_input.setFixedWidth(io_button_width)
        btn_browse_output.setFixedWidth(io_button_width)

        self.input_ttf_edit.editingFinished.connect(
            self._update_metrics_display_from_input_font
        )

        input_row = QWidget()
        input_row_layout = QHBoxLayout(input_row)
        input_row_layout.setContentsMargins(0, 0, 0, 0)
        input_row_layout.addWidget(input_label)
        input_row_layout.addWidget(self.input_ttf_edit)
        input_row_layout.addWidget(btn_browse_input)

        output_row = QWidget()
        output_row_layout = QHBoxLayout(output_row)
        output_row_layout.setContentsMargins(0, 0, 0, 0)
        output_row_layout.addWidget(output_label)
        output_row_layout.addWidget(self.output_ttf_edit)
        output_row_layout.addWidget(btn_browse_output)

        io_layout.addWidget(input_row)
        io_layout.addWidget(output_row)
        root_layout.addWidget(io_group)

        # モード切替を撤廃。基準フォント入力をパラメータグループ内へ移動。

        params_group = QGroupBox("パラメータ")
        params_layout = QVBoxLayout(params_group)

        self.base_font_edit = QLineEdit()
        self.base_font_edit.setEnabled(True)
        self.base_font_edit.setToolTip(
            "ここに基準とするフォントを入力した場合、文字のサイズ及びメトリクス値を読み取り、入力されたフォントにそれらの情報を適用します。\n"
            "その際、パラメーター設定にある横幅％/縦幅％の値は、まずは基準フォントの合わせた後に、指定の値で変形が行われる点に留意してください。"
        )
        self.base_font_edit.editingFinished.connect(
            self._update_metrics_display_from_base_font
        )
        btn_browse_base_font = QPushButton("基準フォントを選択")
        btn_browse_base_font.setEnabled(True)
        btn_browse_base_font.clicked.connect(self._select_base_font)
        self.base_font_button = btn_browse_base_font

        base_font_row = QWidget()
        base_font_row_layout = QHBoxLayout(base_font_row)
        base_font_row_layout.setContentsMargins(0, 0, 0, 0)
        base_font_row_layout.addWidget(self.base_font_edit)
        base_font_row_layout.addWidget(btn_browse_base_font)

        base_font_wrapper_row = QWidget()
        base_font_wrapper_row_layout = QHBoxLayout(base_font_wrapper_row)
        base_font_wrapper_row_layout.setContentsMargins(0, 0, 0, 0)
        base_font_wrapper_row_layout.addWidget(QLabel("基準フォント"))
        base_font_wrapper_row_layout.addWidget(base_font_row)

        self.horizontal_percent_spin = QDoubleSpinBox()
        self.horizontal_percent_spin.setRange(1.0, 400.0)
        self.horizontal_percent_spin.setValue(100.0)
        self.horizontal_percent_spin.setToolTip("横方向の拡大率です。100%で等倍です。")

        self.vertical_percent_spin = QDoubleSpinBox()
        self.vertical_percent_spin.setRange(1.0, 400.0)
        self.vertical_percent_spin.setValue(100.0)
        self.vertical_percent_spin.setToolTip("縦方向の拡大率です。100%で等倍です。")

        self.link_scale_check = QToolButton()
        self.link_scale_check.setCheckable(True)
        self.link_scale_check.setChecked(True)
        self.link_scale_check.setText("🔗")
        self.link_scale_check.setAutoRaise(True)
        self.link_scale_check.setFixedWidth(28)
        self.link_scale_check.setToolTip(
            "有効時は選択したモードで横%と縦%を連動させます。"
        )
        self.link_scale_mode_combo = QComboBox()
        self.link_scale_mode_combo.addItems(["同値連動", "増減連動"])
        self.link_scale_mode_combo.setCurrentText("増減連動")
        self.link_scale_mode_combo.setToolTip(
            "同値連動: 片方を変更するともう片方を同じ値にします。\n"
            "増減連動: 片方の増減量をもう片方にも適用します。"
        )
        self.link_scale_check.toggled.connect(self._on_link_scale_toggled)
        self.horizontal_percent_spin.valueChanged.connect(self._sync_vertical_percent)
        self.vertical_percent_spin.valueChanged.connect(self._sync_horizontal_percent)

        self.horizontal_offset_spin = QSpinBox()
        self.horizontal_offset_spin.setRange(-5000, 5000)
        self.horizontal_offset_spin.setValue(0)
        self.horizontal_offset_spin.setToolTip(
            "横方向の位置補正です。正の値で右、負の値で左に移動します。\n"
            "補完フォント（マージ対象）には適用されません。マージ一覧側で個別に設定してください。"
        )

        self.vertical_offset_spin = QSpinBox()
        self.vertical_offset_spin.setRange(-5000, 5000)
        self.vertical_offset_spin.setValue(0)
        self.vertical_offset_spin.setToolTip(
            "縦方向の位置補正です。正の値で上、負の値で下に移動します。\n"
            "補完フォント（マージ対象）には適用されません。マージ一覧側で個別に設定してください。"
        )

        self.glyph_weight_offset_spin = QSpinBox()
        self.glyph_weight_offset_spin.setRange(-5000, 5000)
        self.glyph_weight_offset_spin.setValue(0)
        self.glyph_weight_offset_spin.setToolTip(
            "入力元フォントのグリフ輪郭の太さを調整します。\n"
            "正の値で太く、負の値で細くなります。\n"
            "補完フォント（マージ対象）には適用されません。マージ一覧側で個別に設定してください。"
        )

        self.remove_empty_glyphs_check = QCheckBox("空白グリフを除去")
        self.remove_empty_glyphs_check.setChecked(True)
        self.remove_empty_glyphs_check.setToolTip(
            "アウトラインを持たない意図しない空白グリフを除去します。\n"
            "スペース記号など、意図された空白グリフは除外対象外です。"
        )

        self.anonymize_check = QCheckBox("匿名化")
        self.anonymize_check.setChecked(False)
        self.anonymize_check.setToolTip(
            "フォントの名前情報や作成日時などのメタデータを匿名化します。"
        )

        self.anonymize_font_name_edit = QLineEdit()
        self.anonymize_font_name_edit.setText("Anonymous")
        self.anonymize_font_name_edit.setEnabled(False)
        self.anonymize_font_name_edit.setToolTip(
            "匿名化後のフォントの名前情報を入力します。\n"
            "空白や記号は使用できません（英数字とアンダースコアのみ）。"
        )
        self.anonymize_check.toggled.connect(self.anonymize_font_name_edit.setEnabled)

        self.manual_metrics_check = QCheckBox("メトリクス変更")
        self.manual_metrics_check.setChecked(False)
        self.manual_metrics_check.setToolTip(
            "有効時は下の上端/下端/行間/下線位置/下線太さの値でメトリクスを変更します。\n"
            "意味が分からない場合はデフォルト値から変更しないことをお勧めします。"
        )

        self.metric_ascent_spin = QSpinBox()
        self.metric_ascent_spin.setRange(-5000, 5000)
        self.metric_ascent_spin.setValue(880)
        self.metric_ascent_spin.setEnabled(False)
        self.metric_ascent_spin.setToolTip("上方向のメトリクス値です。")

        self.metric_descent_spin = QSpinBox()
        self.metric_descent_spin.setRange(-5000, 5000)
        self.metric_descent_spin.setValue(-144)
        self.metric_descent_spin.setEnabled(False)
        self.metric_descent_spin.setToolTip(
            "下方向のメトリクス値です。通常は負の値です。"
        )

        self.metric_line_gap_spin = QSpinBox()
        self.metric_line_gap_spin.setRange(-5000, 5000)
        self.metric_line_gap_spin.setValue(0)
        self.metric_line_gap_spin.setEnabled(False)
        self.metric_line_gap_spin.setToolTip("行間の追加メトリクス値です。")

        self.metric_underline_position_spin = QSpinBox()
        self.metric_underline_position_spin.setRange(-5000, 5000)
        self.metric_underline_position_spin.setValue(-100)
        self.metric_underline_position_spin.setEnabled(False)
        self.metric_underline_position_spin.setToolTip(
            "下線の位置メトリクス値です。通常は負の値です。"
        )

        self.metric_underline_thickness_spin = QSpinBox()
        self.metric_underline_thickness_spin.setRange(-5000, 5000)
        self.metric_underline_thickness_spin.setValue(50)
        self.metric_underline_thickness_spin.setEnabled(False)
        self.metric_underline_thickness_spin.setToolTip("下線の太さメトリクス値です。")

        self.manual_metrics_check.toggled.connect(self.metric_ascent_spin.setEnabled)
        self.manual_metrics_check.toggled.connect(self.metric_descent_spin.setEnabled)
        self.manual_metrics_check.toggled.connect(self.metric_line_gap_spin.setEnabled)
        self.manual_metrics_check.toggled.connect(
            self.metric_underline_position_spin.setEnabled
        )
        self.manual_metrics_check.toggled.connect(
            self.metric_underline_thickness_spin.setEnabled
        )

        self.subset_text_edit = QLineEdit()
        self.subset_text_edit.setText(
            str((SUBSETS_DIR / "subset_jp_skyrim_custom.txt").resolve())
        )
        self.subset_text_edit.setToolTip(
            "サブセット化に使用するテキストファイルのパスです。"
        )
        btn_browse_subset_text = QPushButton("サブセットテキストを選択")
        btn_browse_subset_text.clicked.connect(self._select_subset_text)

        subset_text_row = QWidget()
        subset_text_row_layout = QHBoxLayout(subset_text_row)
        subset_text_row_layout.setContentsMargins(0, 0, 0, 0)
        subset_text_row_layout.addWidget(self.subset_text_edit)
        subset_text_row_layout.addWidget(btn_browse_subset_text)

        link_mode_row = QWidget()
        link_mode_row_layout = QHBoxLayout(link_mode_row)
        link_mode_row_layout.setContentsMargins(0, 0, 0, 0)
        link_mode_row_layout.addWidget(self.link_scale_check)
        link_mode_row_layout.addWidget(self.link_scale_mode_combo)
        link_mode_row_layout.addStretch(1)

        horizontal_percent_label = QLabel("横")
        vertical_percent_label = QLabel("縦")
        horizontal_offset_label = QLabel("横オフセット")
        vertical_offset_label = QLabel("縦オフセット")
        glyph_weight_label = QLabel("太さ変更量")
        horizontal_percent_unit_label = QLabel("%")
        vertical_percent_unit_label = QLabel("%")
        horizontal_offset_unit_label = QLabel("em")
        vertical_offset_unit_label = QLabel("em")
        glyph_weight_unit_label = QLabel("em")

        unit_label_width = max(
            horizontal_percent_unit_label.sizeHint().width(),
            vertical_percent_unit_label.sizeHint().width(),
            horizontal_offset_unit_label.sizeHint().width(),
            vertical_offset_unit_label.sizeHint().width(),
            glyph_weight_unit_label.sizeHint().width(),
        )
        horizontal_percent_unit_label.setFixedWidth(unit_label_width)
        vertical_percent_unit_label.setFixedWidth(unit_label_width)
        horizontal_offset_unit_label.setFixedWidth(unit_label_width)
        vertical_offset_unit_label.setFixedWidth(unit_label_width)
        glyph_weight_unit_label.setFixedWidth(unit_label_width)

        transform_label_width = max(
            horizontal_percent_label.sizeHint().width(),
            vertical_percent_label.sizeHint().width(),
            horizontal_offset_label.sizeHint().width(),
            vertical_offset_label.sizeHint().width(),
            glyph_weight_label.sizeHint().width(),
        )
        horizontal_percent_label.setFixedWidth(transform_label_width)
        vertical_percent_label.setFixedWidth(transform_label_width)
        horizontal_offset_label.setFixedWidth(transform_label_width)
        vertical_offset_label.setFixedWidth(transform_label_width)
        glyph_weight_label.setFixedWidth(transform_label_width)

        transform_input_width = max(
            self.horizontal_percent_spin.sizeHint().width(),
            self.vertical_percent_spin.sizeHint().width(),
            self.horizontal_offset_spin.sizeHint().width(),
            self.vertical_offset_spin.sizeHint().width(),
            self.glyph_weight_offset_spin.sizeHint().width(),
        )
        self.horizontal_percent_spin.setFixedWidth(transform_input_width)
        self.vertical_percent_spin.setFixedWidth(transform_input_width)
        self.horizontal_offset_spin.setFixedWidth(transform_input_width)
        self.vertical_offset_spin.setFixedWidth(transform_input_width)
        self.glyph_weight_offset_spin.setFixedWidth(transform_input_width)

        scale_percent_row = QWidget()
        scale_percent_row_layout = QHBoxLayout(scale_percent_row)
        scale_percent_row_layout.setContentsMargins(0, 0, 0, 0)
        scale_percent_row_layout.addWidget(horizontal_percent_label)
        scale_percent_row_layout.addWidget(self.horizontal_percent_spin)
        scale_percent_row_layout.addWidget(horizontal_percent_unit_label)
        scale_percent_row_layout.addSpacing(16)
        scale_percent_row_layout.addWidget(vertical_percent_label)
        scale_percent_row_layout.addWidget(self.vertical_percent_spin)
        scale_percent_row_layout.addWidget(vertical_percent_unit_label)
        scale_percent_row_layout.addStretch(1)

        offset_row = QWidget()
        offset_row_layout = QHBoxLayout(offset_row)
        offset_row_layout.setContentsMargins(0, 0, 0, 0)
        offset_row_layout.addWidget(horizontal_offset_label)
        offset_row_layout.addWidget(self.horizontal_offset_spin)
        offset_row_layout.addWidget(horizontal_offset_unit_label)
        offset_row_layout.addSpacing(16)
        offset_row_layout.addWidget(vertical_offset_label)
        offset_row_layout.addWidget(self.vertical_offset_spin)
        offset_row_layout.addWidget(vertical_offset_unit_label)
        offset_row_layout.addStretch(1)

        weight_row = QWidget()
        weight_row_layout = QHBoxLayout(weight_row)
        weight_row_layout.setContentsMargins(0, 0, 0, 0)
        weight_row_layout.addWidget(glyph_weight_label)
        weight_row_layout.addWidget(self.glyph_weight_offset_spin)
        weight_row_layout.addWidget(glyph_weight_unit_label)
        weight_row_layout.addStretch(1)

        options_row = QWidget()
        options_layout = QHBoxLayout(options_row)
        options_layout.setContentsMargins(0, 0, 0, 0)
        options_layout.addWidget(self.remove_empty_glyphs_check)
        options_layout.addWidget(self.anonymize_check)
        options_layout.addWidget(QLabel("匿名化後フォント名"))
        options_layout.addWidget(self.anonymize_font_name_edit)
        options_layout.addStretch(1)
        metrics_values_row = QWidget()
        metrics_values_row_layout = QHBoxLayout(metrics_values_row)
        metrics_values_row_layout.setContentsMargins(0, 0, 0, 0)
        metrics_values_row_layout.addWidget(QLabel("上端"))
        metrics_values_row_layout.addWidget(self.metric_ascent_spin)
        metrics_values_row_layout.addSpacing(16)
        metrics_values_row_layout.addWidget(QLabel("下端"))
        metrics_values_row_layout.addWidget(self.metric_descent_spin)
        metrics_values_row_layout.addSpacing(16)
        metrics_values_row_layout.addWidget(QLabel("行間"))
        metrics_values_row_layout.addWidget(self.metric_line_gap_spin)
        metrics_values_row_layout.addSpacing(16)
        metrics_values_row_layout.addWidget(QLabel("下線位置"))
        metrics_values_row_layout.addWidget(self.metric_underline_position_spin)
        metrics_values_row_layout.addSpacing(16)
        metrics_values_row_layout.addWidget(QLabel("下線太さ"))
        metrics_values_row_layout.addWidget(self.metric_underline_thickness_spin)
        metrics_values_row_layout.addStretch(1)

        subset_wrapper_row = QWidget()
        subset_wrapper_row_layout = QHBoxLayout(subset_wrapper_row)
        subset_wrapper_row_layout.setContentsMargins(0, 0, 0, 0)
        subset_wrapper_row_layout.addWidget(QLabel("サブセットテキスト"))
        subset_wrapper_row_layout.addWidget(subset_text_row)

        params_layout.addWidget(base_font_wrapper_row)
        params_layout.addWidget(link_mode_row)
        params_layout.addWidget(scale_percent_row)
        params_layout.addWidget(offset_row)
        params_layout.addWidget(weight_row)
        params_layout.addWidget(options_row)
        params_layout.addWidget(self.manual_metrics_check)
        params_layout.addWidget(metrics_values_row)
        params_layout.addWidget(subset_wrapper_row)
        root_layout.addWidget(params_group)

        self._last_horizontal_percent = self.horizontal_percent_spin.value()
        self._last_vertical_percent = self.vertical_percent_spin.value()

        preview_text_row = QWidget()
        preview_text_layout = QHBoxLayout(preview_text_row)
        preview_text_layout.setContentsMargins(0, 0, 0, 0)
        self.preview_text_edit = QLineEdit()
        self.preview_text_edit.setText(PREVIEW_SAMPLE_TEXT)
        self.preview_text_edit.setToolTip(
            "プレビュー画像に表示する文字列を指定します。"
        )
        preview_text_layout.addWidget(QLabel("プレビュー文字列"))
        preview_text_layout.addWidget(self.preview_text_edit)
        root_layout.addWidget(preview_text_row)

        btn_preview = QPushButton("プレビュー")
        btn_preview.clicked.connect(self._emit_preview)
        root_layout.addWidget(btn_preview)

        merge_group = QGroupBox("マージ機能（補完フォント）")
        merge_layout = QVBoxLayout(merge_group)
        self.merge_table = MergeFontsTableWidget()
        self.merge_table.setHorizontalHeaderLabels(
            ["フォントパス", "横オフセット(em)", "縦オフセット(em)", "太さ変更量(em)"]
        )
        self.merge_table.setToolTip(
            "補完フォント一覧です。ドラッグ&ドロップで追加、行の並べ替え、削除ができます。"
        )
        self.merge_table._apply_column_ratio()
        self.merge_table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.merge_table.setSelectionMode(
            QAbstractItemView.SelectionMode.ExtendedSelection
        )
        merge_buttons = QHBoxLayout()
        btn_add_merge = QPushButton("追加")
        btn_remove_merge = QPushButton("削除")
        btn_add_merge.clicked.connect(self._add_merge_fonts)
        btn_remove_merge.clicked.connect(self._remove_merge_fonts)
        merge_buttons.addWidget(btn_add_merge)
        merge_buttons.addWidget(btn_remove_merge)
        merge_layout.addWidget(self.merge_table)
        merge_layout.addLayout(merge_buttons)
        root_layout.addWidget(merge_group)

        self.execute_button = QPushButton(self._EXECUTE_LABEL)
        self.execute_button.setProperty("importance", "primary")
        self.execute_button.clicked.connect(self._emit_execute)

        action_row = QWidget()
        action_layout = QHBoxLayout(action_row)
        action_layout.setContentsMargins(0, 0, 0, 0)
        action_layout.addWidget(self.execute_button)
        root_layout.addWidget(action_row)
        root_layout.addStretch(1)

    def _select_input_ttf(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "加工対象フォントを選択", "", "Font (*.ttf *.otf)"
        )
        if path:
            self.input_ttf_edit.setText(path)
            self._update_metrics_display_from_input_font()

    def _select_output_ttf(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self,
            "保存先を選択",
            "",
            "フォント (*.ttf)",
        )
        if path:
            self.output_ttf_edit.setText(path)

    def _select_base_font(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "基準フォントを選択", "", "Font (*.ttf *.otf)"
        )
        if path:
            self.base_font_edit.setText(path)
            self._update_metrics_display_from_base_font()

    def _update_metrics_display_from_input_font(self) -> None:
        path_str = self.input_ttf_edit.text().strip()
        self._apply_metrics_from_font_path(path_str)

    def _update_metrics_display_from_base_font(self) -> None:
        path_str = self.base_font_edit.text().strip()
        self._apply_metrics_from_font_path(path_str)

    def _apply_metrics_from_font_path(self, font_path_str: str) -> None:
        if not font_path_str:
            return

        path_obj = Path(font_path_str)
        if not path_obj.exists():
            return

        try:
            # TTFontを直接コンテキストマネージャで開く
            with TTFont(str(path_obj)) as font_obj:
                if is_otf_path(path_obj):
                    otf_to_ttf(font_obj)

                upm = int(font_obj["head"].unitsPerEm)
                if upm <= 0:
                    return

                # NORMALIZED_UPM (1024) へのスケーリング係数
                scale_for_1024 = float(NORMALIZED_UPM) / float(upm)

                def _to_1024(value: int | float) -> int:
                    return int(round(float(value) * scale_for_1024))

                hhea = font_obj.get("hhea")
                os2 = font_obj.get("OS/2")
                post = font_obj.get("post")

                # FontForge の Ascent/Descent は通常 hhea テーブルの値に対応する
                asc, desc, lg = 0, 0, 0
                if hhea is not None:
                    asc = int(hhea.ascent)
                    desc = int(hhea.descent)
                    lg = int(hhea.lineGap)
                elif os2 is not None:
                    # hhea が無い場合のフォールバック
                    asc = int(os2.sTypoAscender)
                    desc = int(os2.sTypoDescender)
                    lg = int(os2.sTypoLineGap)

                # 1024基準に変換
                final_ascent = _to_1024(asc)
                final_descent = _to_1024(desc)
                final_line_gap = _to_1024(lg)

                # 合計が 1024 になるように丸め誤差を調整（Descentが負であることを考慮）
                # FontForgeの定義では ascent + abs(descent) = UPM
                if (final_ascent + abs(final_descent)) != NORMALIZED_UPM:
                    # 誤差を Ascent 側で吸収
                    final_ascent = NORMALIZED_UPM - abs(final_descent)

                self.metric_ascent_spin.setValue(final_ascent)
                self.metric_descent_spin.setValue(final_descent)
                self.metric_line_gap_spin.setValue(final_line_gap)

                if post is not None:
                    self.metric_underline_position_spin.setValue(
                        _to_1024(int(post.underlinePosition))
                    )
                    self.metric_underline_thickness_spin.setValue(
                        _to_1024(int(post.underlineThickness))
                    )

                # ログ出力（デバッグ用）
                self.log_emitted.emit(
                    f"フォントからメトリクスを読み取りました: {path_obj.name} "
                    f"(Asc:{final_ascent}, Desc:{final_descent}, UPM:{final_ascent + abs(final_descent)})"
                )

        except Exception as e:
            self.log_emitted.emit(f"フォントのメトリクス読み取りに失敗しました: {e}")
            return

    def _add_merge_fonts(self) -> None:
        paths, _ = QFileDialog.getOpenFileNames(
            self,
            "補完用フォントを選択",
            "",
            "Font (*.ttf *.otf)",
        )
        self.merge_table.add_paths(paths)

    def _select_subset_text(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "サブセットテキストを選択",
            str(SUBSETS_DIR.resolve()),
            "Text (*.txt)",
        )
        if path:
            self.subset_text_edit.setText(path)

    def _remove_merge_fonts(self) -> None:
        selected_rows = sorted(
            {index.row() for index in self.merge_table.selectionModel().selectedRows()},
            reverse=True,
        )
        for row in selected_rows:
            self.merge_table.removeRow(row)

    def _on_link_scale_toggled(self, checked: bool) -> None:
        self.link_scale_check.setText("🔗" if checked else "🔓")
        self._last_horizontal_percent = self.horizontal_percent_spin.value()
        self._last_vertical_percent = self.vertical_percent_spin.value()

    def _sync_vertical_percent(self, value: float) -> None:
        if self._syncing_scale_values:
            return
        delta = value - self._last_horizontal_percent
        self._last_horizontal_percent = value
        if not self.link_scale_check.isChecked():
            self._last_vertical_percent = self.vertical_percent_spin.value()
            return
        self._syncing_scale_values = True
        if self.link_scale_mode_combo.currentText() == "同値連動":
            self.vertical_percent_spin.setValue(value)
        else:
            self.vertical_percent_spin.setValue(
                self.vertical_percent_spin.value() + delta
            )
        self._last_vertical_percent = self.vertical_percent_spin.value()
        self._syncing_scale_values = False

    def _sync_horizontal_percent(self, value: float) -> None:
        if self._syncing_scale_values:
            return
        delta = value - self._last_horizontal_percent
        self._last_horizontal_percent = value
        if not self.link_scale_check.isChecked():
            self._last_horizontal_percent = self.horizontal_percent_spin.value()
            return
        self._syncing_scale_values = True
        if self.link_scale_mode_combo.currentText() == "同値連動":
            self.horizontal_percent_spin.setValue(value)
        else:
            self.horizontal_percent_spin.setValue(
                self.horizontal_percent_spin.value() + delta
            )
        self._last_horizontal_percent = self.horizontal_percent_spin.value()
        self._syncing_scale_values = False

    def _emit_execute(self) -> None:
        config = self._build_single_font_config(require_output=True)
        if config is None:
            return

        reply = QMessageBox.question(
            self,
            "確認",
            "個別処理を開始しますか？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.No:
            return

        self.execute_requested.emit(config)

    def _emit_preview(self) -> None:
        config = self._build_single_font_config(require_output=False)
        if config is None:
            return
        self.preview_requested.emit(config)

    def set_executing_state(self, executing: bool) -> None:
        self.execute_button.setText(
            self._EXECUTING_LABEL if executing else self._EXECUTE_LABEL
        )

    def _build_single_font_config(
        self, *, require_output: bool = True
    ) -> SingleFontTaskConfig | None:
        input_ttf = self.input_ttf_edit.text().strip()
        if not input_ttf:
            QMessageBox.warning(self, "入力不足", "対象フォントを選択してください。")
            return None

        output_ttf = self.output_ttf_edit.text().strip()
        if require_output and not output_ttf:
            QMessageBox.warning(self, "入力不足", "フォント出力先を指定してください。")
            return None

        metric_ascent = None
        metric_descent = None
        metric_line_gap = None
        metric_underline_position = None
        metric_underline_thickness = None
        anonymize_font_name = self.anonymize_font_name_edit.text().strip()
        if self.anonymize_check.isChecked():
            if not anonymize_font_name:
                QMessageBox.warning(
                    self,
                    "入力不足",
                    "匿名化後フォント名を入力してください。",
                )
                return
            if re.search(r"[^\w]", anonymize_font_name):
                QMessageBox.warning(
                    self,
                    "入力エラー",
                    "匿名化後フォント名には空白や記号は使用できません。\n"
                    "英数字とアンダースコアのみ使用できます。",
                )
                return

        base_font_specified = bool(self.base_font_edit.text().strip())
        is_manual_mode = not base_font_specified
        if is_manual_mode and self.manual_metrics_check.isChecked():
            metric_ascent = self.metric_ascent_spin.value()
            metric_descent = self.metric_descent_spin.value()
            metric_line_gap = self.metric_line_gap_spin.value()
            metric_underline_position = self.metric_underline_position_spin.value()
            metric_underline_thickness = self.metric_underline_thickness_spin.value()
            derived_upm = int(metric_ascent) + abs(int(metric_descent))
            if derived_upm != NORMALIZED_UPM:
                QMessageBox.warning(
                    self,
                    "UPM警告",
                    f"上端/下端 から算出される UPM が {NORMALIZED_UPM} ではありません。\n"
                    f"計算値: {derived_upm} (上端={metric_ascent}, 下端={metric_descent})",
                )
                return None

        # マージフォントのテーブルから収集
        merge_items: list[MergeFontItem] = []
        for row in range(getattr(self, 'merge_table').rowCount()):
            path_item = self.merge_table.item(row, 0)
            font_path = path_item.text().strip() if path_item else ""
            if not font_path:
                continue
            w_spin = self.merge_table.cellWidget(row, 1)
            h_spin = self.merge_table.cellWidget(row, 2)
            weight_spin = self.merge_table.cellWidget(row, 3)
            w_off = int(w_spin.value()) if isinstance(w_spin, QSpinBox) else 0
            h_off = int(h_spin.value()) if isinstance(h_spin, QSpinBox) else 0
            wt_off = (
                int(weight_spin.value()) if isinstance(weight_spin, QSpinBox) else 0
            )
            merge_items.append(
                MergeFontItem(
                    font_path=font_path,
                    offset_width=w_off,
                    offset_height=h_off,
                    weight_offset=wt_off,
                )
            )

        config = SingleFontTaskConfig(
            input_ttf=self.input_ttf_edit.text().strip(),
            output_ttf=self.output_ttf_edit.text().strip(),
            subset_text_path=self.subset_text_edit.text().strip(),
            remove_empty_glyphs=self.remove_empty_glyphs_check.isChecked(),
            anonymize=self.anonymize_check.isChecked(),
            anonymize_font_name=anonymize_font_name,
            mode="base" if base_font_specified else "manual",
            horizontal_percent=self.horizontal_percent_spin.value(),
            vertical_percent=self.vertical_percent_spin.value(),
            horizontal_offset=self.horizontal_offset_spin.value(),
            vertical_offset=self.vertical_offset_spin.value(),
            glyph_weight_offset=self.glyph_weight_offset_spin.value(),
            metric_ascent=metric_ascent,
            metric_descent=metric_descent,
            metric_line_gap=metric_line_gap,
            metric_underline_position=metric_underline_position,
            metric_underline_thickness=metric_underline_thickness,
            base_font_path=self.base_font_edit.text().strip(),
            merge_fonts=merge_items,
            preview_text=self.preview_text_edit.text(),
        )
        return config


class SingleSwfEmbedTab(QWidget):
    execute_requested = pyqtSignal(object)
    _EXECUTE_LABEL = "埋め込みを実行"
    _EXECUTING_LABEL = "埋め込みを実行中..."

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self) -> None:
        root_layout = QVBoxLayout(self)

        target_group = QGroupBox("出力")
        target_layout = QVBoxLayout(target_group)
        self.output_swf_edit = QLineEdit()
        self.output_swf_edit.setToolTip("埋め込み後の出力SWFファイルを指定します。")
        output_label = QLabel("SWF出力先")
        btn_output = QPushButton("選択")
        btn_output.clicked.connect(self._select_output_swf)

        output_label.setFixedWidth(output_label.sizeHint().width())

        btn_output.setFixedWidth(btn_output.sizeHint().width())

        output_row = QWidget()
        output_row_layout = QHBoxLayout(output_row)
        output_row_layout.setContentsMargins(0, 0, 0, 0)
        output_row_layout.addWidget(output_label)
        output_row_layout.addWidget(self.output_swf_edit)
        output_row_layout.addWidget(btn_output)

        target_layout.addWidget(output_row)
        root_layout.addWidget(target_group)

        table_group = QGroupBox("フォントリスト（内部名付き）")
        table_layout = QVBoxLayout(table_group)
        self.embed_table = SingleEmbedTableWidget()
        self.embed_table.setHorizontalHeaderLabels(["フォントパス", "内部名"])
        self.embed_table.setToolTip(
            "埋め込むフォントと内部名の一覧です。内部名はSWF内の識別名です。"
        )
        self.embed_table._apply_column_ratio()
        self.embed_table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.embed_table.setSelectionMode(
            QAbstractItemView.SelectionMode.ExtendedSelection
        )

        table_buttons = QHBoxLayout()
        btn_add_row = QPushButton("フォント追加")
        btn_remove_row = QPushButton("選択行を削除")
        btn_add_row.clicked.connect(self._add_ttf_rows)
        btn_remove_row.clicked.connect(self._remove_selected_rows)
        table_buttons.addWidget(btn_add_row)
        table_buttons.addWidget(btn_remove_row)

        table_layout.addWidget(self.embed_table)
        table_layout.addLayout(table_buttons)
        root_layout.addWidget(table_group)

        self.execute_button = QPushButton(self._EXECUTE_LABEL)
        self.execute_button.setProperty("importance", "primary")
        self.execute_button.clicked.connect(self._emit_execute)
        root_layout.addWidget(self.execute_button)

    def _select_output_swf(self) -> None:
        path, _ = QFileDialog.getSaveFileName(self, "出力SWFを選択", "", "SWF (*.swf)")
        if path:
            self.output_swf_edit.setText(path)

    def _add_ttf_rows(self) -> None:
        paths, _ = QFileDialog.getOpenFileNames(
            self, "埋め込みフォントを選択", "", "Font (*.ttf *.otf)"
        )
        self.embed_table.add_paths(paths)

    def _remove_selected_rows(self) -> None:
        selected_rows = sorted(
            {index.row() for index in self.embed_table.selectionModel().selectedRows()},
            reverse=True,
        )
        for row in selected_rows:
            self.embed_table.removeRow(row)

    def _emit_execute(self) -> None:
        output_swf = self.output_swf_edit.text().strip()
        if not output_swf:
            QMessageBox.warning(self, "入力不足", "SWF出力先を指定してください。")
            return

        items: list[EmbedItem] = []
        for row in range(self.embed_table.rowCount()):
            ttf_item = self.embed_table.item(row, 0)
            internal_item = self.embed_table.item(row, 1)
            ttf_path = ttf_item.text().strip() if ttf_item else ""
            internal_name = internal_item.text().strip() if internal_item else ""
            if ttf_path:
                items.append(EmbedItem(ttf_path=ttf_path, internal_name=internal_name))

        if not items:
            QMessageBox.warning(
                self, "入力不足", "埋め込み対象フォントを1つ以上追加してください。"
            )
            return

        reply = QMessageBox.question(
            self,
            "確認",
            "SWF埋め込み処理を開始しますか？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.No:
            return

        config = SingleEmbedTaskConfig(
            output_swf=output_swf,
            items=items,
        )
        self.execute_requested.emit(config)

    def set_executing_state(self, executing: bool) -> None:
        self.execute_button.setText(
            self._EXECUTING_LABEL if executing else self._EXECUTE_LABEL
        )


class BatchFontProcessingTab(QWidget):
    execute_requested = pyqtSignal(object)
    _EXECUTE_LABEL = "一括処理実行（フォント加工）"
    _EXECUTING_LABEL = "一括処理実行中..."

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self) -> None:
        root_layout = QVBoxLayout(self)

        form_group = QGroupBox("レシピ設定")
        form_layout = QVBoxLayout(form_group)

        self.recipe_edit = QLineEdit()
        self.input_dir_edit = QLineEdit()
        self.output_dir_edit = QLineEdit()
        self.recipe_edit.setToolTip(
            "フォント一括処理用のレシピ（YAML）を指定します。\n"
            f"テンプレートは {DATA_DIR.resolve()}/recipe-template_font-process.yml です。任意の場所にコピーして利用して下さい。"
        )
        self.input_dir_edit.setToolTip(
            "レシピで参照する加工対象フォントの親フォルダです。レシピ内の入力系パス指定にて、相対パスを使用する場合の基準ディレクトリになります。"
        )
        self.output_dir_edit.setToolTip(
            "加工後のフォントの出力先親フォルダです。レシピ内の出力系パス指定にて、相対パスを使用する場合の基準ディレクトリになります。"
        )

        recipe_label = QLabel("レシピ")
        input_dir_label = QLabel("対象フォルダ")
        output_dir_label = QLabel("出力フォルダ")

        btn_recipe = QPushButton("選択")
        btn_input_dir = QPushButton("選択")
        btn_output_dir = QPushButton("選択")

        btn_recipe.clicked.connect(self._select_recipe)
        btn_input_dir.clicked.connect(self._select_input_dir)
        btn_output_dir.clicked.connect(self._select_output_dir)

        form_label_width = max(
            recipe_label.sizeHint().width(),
            input_dir_label.sizeHint().width(),
            output_dir_label.sizeHint().width(),
        )
        recipe_label.setFixedWidth(form_label_width)
        input_dir_label.setFixedWidth(form_label_width)
        output_dir_label.setFixedWidth(form_label_width)

        form_button_width = max(
            btn_recipe.sizeHint().width(),
            btn_input_dir.sizeHint().width(),
            btn_output_dir.sizeHint().width(),
        )
        btn_recipe.setFixedWidth(form_button_width)
        btn_input_dir.setFixedWidth(form_button_width)
        btn_output_dir.setFixedWidth(form_button_width)

        recipe_row = QWidget()
        recipe_row_layout = QHBoxLayout(recipe_row)
        recipe_row_layout.setContentsMargins(0, 0, 0, 0)
        recipe_row_layout.addWidget(recipe_label)
        recipe_row_layout.addWidget(self.recipe_edit)
        recipe_row_layout.addWidget(btn_recipe)

        input_dir_row = QWidget()
        input_dir_row_layout = QHBoxLayout(input_dir_row)
        input_dir_row_layout.setContentsMargins(0, 0, 0, 0)
        input_dir_row_layout.addWidget(input_dir_label)
        input_dir_row_layout.addWidget(self.input_dir_edit)
        input_dir_row_layout.addWidget(btn_input_dir)

        output_dir_row = QWidget()
        output_dir_row_layout = QHBoxLayout(output_dir_row)
        output_dir_row_layout.setContentsMargins(0, 0, 0, 0)
        output_dir_row_layout.addWidget(output_dir_label)
        output_dir_row_layout.addWidget(self.output_dir_edit)
        output_dir_row_layout.addWidget(btn_output_dir)

        form_layout.addWidget(recipe_row)
        form_layout.addWidget(input_dir_row)
        form_layout.addWidget(output_dir_row)

        root_layout.addWidget(form_group)

        self.execute_button = QPushButton(self._EXECUTE_LABEL)
        self.execute_button.setProperty("importance", "primary")
        self.execute_button.clicked.connect(self._emit_execute)
        root_layout.addWidget(self.execute_button)
        root_layout.addStretch(1)

    def _select_recipe(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "レシピファイルを選択",
            "",
            "YAML (*.yml *.yaml)",
        )
        if path:
            self.recipe_edit.setText(path)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    recipe = yaml.safe_load(f)
                    if isinstance(recipe, dict):
                        input_dir = recipe.get("input_dir")
                        if input_dir:
                            self.input_dir_edit.setText(str(input_dir))
                        output_dir = recipe.get("output_dir")
                        if output_dir:
                            self.output_dir_edit.setText(str(output_dir))
            except Exception:
                pass

    def _select_input_dir(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "input_dirを選択")
        if path:
            self.input_dir_edit.setText(path)

    def _select_output_dir(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "output_dirを選択")
        if path:
            self.output_dir_edit.setText(path)

    def _emit_execute(self) -> None:
        recipe_path = self.recipe_edit.text().strip()
        if not recipe_path:
            QMessageBox.warning(self, "入力不足", "レシピファイルを選択してください。")
            return

        reply = QMessageBox.question(
            self,
            "確認",
            "一括処理を開始しますか？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.No:
            return

        config = BatchFontProcessingTaskConfig(
            recipe_path=recipe_path,
            input_dir=self.input_dir_edit.text().strip(),
            output_dir=self.output_dir_edit.text().strip(),
        )
        self.execute_requested.emit(config)

    def set_executing_state(self, executing: bool) -> None:
        self.execute_button.setText(
            self._EXECUTING_LABEL if executing else self._EXECUTE_LABEL
        )


class BatchSwfProcessingTab(QWidget):
    execute_requested = pyqtSignal(object)
    _EXECUTE_LABEL = "一括処理実行（SWF埋め込み）"
    _EXECUTING_LABEL = "一括処理実行中..."

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self) -> None:
        root_layout = QVBoxLayout(self)

        form_group = QGroupBox("レシピ設定")
        form_layout = QVBoxLayout(form_group)

        self.recipe_edit = QLineEdit()
        self.input_dir_edit = QLineEdit()
        self.output_edit = QLineEdit()
        self.recipe_edit.setToolTip(
            "SWF一括埋め込み用のレシピ（YAML）を指定します。\n"
            f"テンプレートは {DATA_DIR.resolve()}/recipe-template_swf-embedded.yml です。任意の場所にコピーして利用して下さい。"
        )
        self.input_dir_edit.setToolTip(
            "レシピで参照する埋め込みフォントの親フォルダです。相対パスの基準になります。"
        )
        self.output_edit.setToolTip(
            "出力側の基準フォルダです。ステップの output_swf_path が相対指定の場合、このフォルダを基準に解決します。"
        )

        recipe_label = QLabel("レシピ")
        input_dir_label = QLabel("対象フォルダ")
        output_label = QLabel("出力フォルダ")

        btn_recipe = QPushButton("選択")
        btn_input_dir = QPushButton("選択")
        btn_output_dir = QPushButton("選択")

        btn_recipe.clicked.connect(self._select_recipe)
        btn_input_dir.clicked.connect(self._select_input_dir)
        btn_output_dir.clicked.connect(self._select_output_dir)

        form_label_width = max(
            recipe_label.sizeHint().width(),
            input_dir_label.sizeHint().width(),
            output_label.sizeHint().width(),
        )
        recipe_label.setFixedWidth(form_label_width)
        input_dir_label.setFixedWidth(form_label_width)
        output_label.setFixedWidth(form_label_width)

        form_button_width = max(
            btn_recipe.sizeHint().width(),
            btn_input_dir.sizeHint().width(),
            btn_output_dir.sizeHint().width(),
        )
        btn_recipe.setFixedWidth(form_button_width)
        btn_input_dir.setFixedWidth(form_button_width)
        btn_output_dir.setFixedWidth(form_button_width)

        recipe_row = QWidget()
        recipe_row_layout = QHBoxLayout(recipe_row)
        recipe_row_layout.setContentsMargins(0, 0, 0, 0)
        recipe_row_layout.addWidget(recipe_label)
        recipe_row_layout.addWidget(self.recipe_edit)
        recipe_row_layout.addWidget(btn_recipe)

        input_dir_row = QWidget()
        input_dir_row_layout = QHBoxLayout(input_dir_row)
        input_dir_row_layout.setContentsMargins(0, 0, 0, 0)
        input_dir_row_layout.addWidget(input_dir_label)
        input_dir_row_layout.addWidget(self.input_dir_edit)
        input_dir_row_layout.addWidget(btn_input_dir)

        output_row = QWidget()
        output_row_layout = QHBoxLayout(output_row)
        output_row_layout.setContentsMargins(0, 0, 0, 0)
        output_row_layout.addWidget(output_label)
        output_row_layout.addWidget(self.output_edit)
        output_row_layout.addWidget(btn_output_dir)

        form_layout.addWidget(recipe_row)
        form_layout.addWidget(input_dir_row)
        form_layout.addWidget(output_row)

        root_layout.addWidget(form_group)

        self.execute_button = QPushButton(self._EXECUTE_LABEL)
        self.execute_button.setProperty("importance", "primary")
        self.execute_button.clicked.connect(self._emit_execute)
        root_layout.addWidget(self.execute_button)
        root_layout.addStretch(1)

    def _select_recipe(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "レシピファイルを選択",
            "",
            "YAML (*.yml *.yaml)",
        )
        if path:
            self.recipe_edit.setText(path)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    recipe = yaml.safe_load(f)
                    if isinstance(recipe, dict):
                        input_dir = recipe.get("input_dir")
                        if input_dir:
                            self.input_dir_edit.setText(str(input_dir))
                        output_dir = recipe.get("output_dir")
                        if output_dir:
                            self.output_edit.setText(str(output_dir))
            except Exception:
                pass

    def _select_input_dir(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "input_dirを選択")
        if path:
            self.input_dir_edit.setText(path)

    def _select_output_dir(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "output_dirを選択")
        if path:
            self.output_edit.setText(path)

    def _emit_execute(self) -> None:
        recipe_path = self.recipe_edit.text().strip()
        if not recipe_path:
            QMessageBox.warning(self, "入力不足", "レシピファイルを選択してください。")
            return

        reply = QMessageBox.question(
            self,
            "確認",
            "一括処理を開始しますか？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.No:
            return

        config = BatchSwfProcessingTaskConfig(
            recipe_path=recipe_path,
            input_dir=self.input_dir_edit.text().strip(),
            output_dir=self.output_edit.text().strip(),
        )
        self.execute_requested.emit(config)

    def set_executing_state(self, executing: bool) -> None:
        self.execute_button.setText(
            self._EXECUTING_LABEL if executing else self._EXECUTE_LABEL
        )


class PreviewWindow(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(PREVIEW_WINDOW_TITLE)
        self.setModal(False)
        self.setWindowFlag(Qt.WindowType.Window, True)
        self._original_pixmap = QPixmap()

        layout = QVBoxLayout(self)
        self.preview_image_label = QLabel("プレビュー未生成")
        self.preview_image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_image_label.setFrameShape(QFrame.Shape.Box)
        layout.addWidget(self.preview_image_label)

    def set_preview_pixmap(self, pixmap: QPixmap) -> None:
        if pixmap.isNull():
            self.preview_image_label.setText("プレビュー生成に失敗しました")
            self.preview_image_label.setPixmap(QPixmap())
            self._original_pixmap = QPixmap()
            return

        self._original_pixmap = pixmap
        self.preview_image_label.setFixedSize(pixmap.size())
        self.preview_image_label.setPixmap(pixmap)
        self.preview_image_label.setText("")
        self.adjustSize()
        self.resize(self.sizeHint())


class MainWindow(QMainWindow):
    _STATUSBAR_ERROR_STYLESHEET = (
        "QStatusBar {"
        "background-color: #7a1f1f;"
        "color: #ffffff;"
        "font-weight: 600;"
        "}"
    )

    def __init__(self, *, debug: bool = False) -> None:
        super().__init__()
        self._debug: bool = bool(debug)
        self._task_thread: QThread | None = None
        self._task_worker: BackgroundTaskWorker | None = None
        self._current_task_name: str | None = None
        self._preview_window: PreviewWindow | None = None
        self._build_ui()
        self._ensure_startup_logistics()
        self._bind_events()

    def _build_ui(self) -> None:
        self.setWindowTitle(MAIN_WINDOW_TITLE)
        self.resize(1080, 760)
        self.setStyleSheet(
            """
            QLineEdit:disabled,
            QComboBox:disabled,
            QAbstractSpinBox:disabled {
                background-color: palette(alternate-base);
                color: palette(mid);
                border: 1px solid palette(mid);
            }
            QPushButton:disabled {
                background-color: palette(alternate-base);
                color: palette(mid);
                border: 1px solid palette(mid);
                border-radius: 5px;
                padding: 6px 12px;
            }
            QPushButton[importance=\"primary\"] {
                background-color: #2f7fcf;
                color: #ffffff;
                border: 1px solid #2467ab;
                border-radius: 5px;
                padding: 6px 12px;
                font-weight: 600;
            }
            QPushButton[importance=\"primary\"]:hover {
                background-color: #3a8ee2;
            }
            QPushButton[importance=\"primary\"]:pressed {
                background-color: #2467ab;
            }
            QPushButton[importance=\"danger\"]:enabled {
                background-color: #b33a3a;
                color: #ffffff;
                border: 1px solid #8f2f2f;
                border-radius: 5px;
                padding: 6px 12px;
                font-weight: 600;
            }
            QPushButton[importance=\"danger\"]:enabled:hover {
                background-color: #c64545;
            }
            QPushButton[importance=\"danger\"]:enabled:pressed {
                background-color: #8f2f2f;
            }
            """
        )

        central = QWidget(self)
        layout = QVBoxLayout(central)
        self.setCentralWidget(central)

        splitter = QSplitter()
        splitter.setOrientation(Qt.Orientation.Horizontal)

        top_widget = QWidget()
        top_layout = QVBoxLayout(top_widget)
        top_layout.setContentsMargins(0, 0, 0, 0)
        self.tabs = QTabWidget()
        self.single_font_tab = SingleFontProcessingTab()
        self.single_embed_tab = SingleSwfEmbedTab()
        self.batch_tab = BatchFontProcessingTab()
        self.batch_swf_tab = BatchSwfProcessingTab()
        self.stop_task_button = QPushButton("処理を強制停止")
        self.stop_task_button.setProperty("importance", "danger")
        self.stop_task_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed,
        )
        self.stop_task_button.setMinimumHeight(
            self.single_font_tab.execute_button.sizeHint().height() + 8
        )
        self.stop_task_button.setEnabled(False)

        self.tabs.addTab(self.single_font_tab, "個別：フォント加工")
        self.tabs.addTab(self.single_embed_tab, "個別：SWF埋め込み")
        self.tabs.addTab(self.batch_tab, "一括：フォント加工")
        self.tabs.addTab(self.batch_swf_tab, "一括：SWF埋め込み")

        top_layout.addWidget(self.tabs)

        bottom_widget = QWidget()
        bottom_layout = QVBoxLayout(bottom_widget)
        bottom_layout.setContentsMargins(0, 0, 0, 0)
        bottom_layout.addWidget(QLabel("ログ"))
        self.log_text_edit = QTextEdit()
        self.log_text_edit.setReadOnly(True)
        bottom_layout.addWidget(self.log_text_edit)
        bottom_layout.addWidget(self.stop_task_button)

        splitter.addWidget(top_widget)
        splitter.addWidget(bottom_widget)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)

        layout.addWidget(splitter)

    def _bind_events(self) -> None:
        self.single_font_tab.execute_requested.connect(self._start_single_font_task)
        self.single_font_tab.preview_requested.connect(self._run_single_font_preview)
        self.single_font_tab.log_emitted.connect(self.append_log)
        self.single_embed_tab.execute_requested.connect(self._start_single_embed_task)
        self.batch_tab.execute_requested.connect(self._start_batch_task)
        self.batch_swf_tab.execute_requested.connect(self._start_batch_swf_task)
        self.stop_task_button.clicked.connect(self._force_stop_current_task)

    def append_log(self, message: str) -> None:
        self.log_text_edit.append(message)

    def _ensure_startup_logistics(self) -> None:
        self.statusBar().showMessage("実行環境を準備中...")
        self.append_log("[起動] 実行環境を準備中...")

        try:
            ffdec_jar = ensure_ffdec_runtime(log=self.append_log)
            ensured_java = ensure_java_runtime(log=self.append_log)
            java_executable = detect_java_executable()
            self.append_log(f"[起動] FFDec 確認完了: {ffdec_jar}")
            self.append_log(f"[起動] Javaランタイム 確認完了: {ensured_java}")
            self.append_log(f"[起動] Java 確認完了: {java_executable}")
        except Exception as error:
            self.append_log(f"[起動] 実行環境の準備に失敗: {error}")
            QMessageBox.warning(
                self,
                "実行環境の準備に失敗",
                "実行環境の準備に失敗しました。\n"
                "インターネットにアクセス出来ることを確認してください。",
            )
        finally:
            self.statusBar().clearMessage()

    def _set_ui_enabled(self, enabled: bool) -> None:
        self.tabs.setEnabled(enabled)
        executing = not enabled
        self.single_font_tab.set_executing_state(executing)
        self.single_embed_tab.set_executing_state(executing)
        self.batch_tab.set_executing_state(executing)
        self.batch_swf_tab.set_executing_state(executing)
        self.stop_task_button.setEnabled(executing)

    def _set_status_error(self, is_error: bool) -> None:
        self.statusBar().setStyleSheet(
            self._STATUSBAR_ERROR_STYLESHEET if is_error else ""
        )

    def _force_stop_current_task(self) -> None:
        if self._task_thread is None:
            QMessageBox.information(self, "停止", "停止対象の処理はありません。")
            return

        task_name = self._current_task_name or "処理"
        decision = QMessageBox.question(
            self,
            "強制停止確認",
            f"{task_name} を強制停止しますか？\n未保存の途中成果は失われる可能性があります。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if decision != QMessageBox.StandardButton.Yes:
            return

        self.append_log(f"[{task_name}] ユーザー要求により強制停止を実行")

        task_thread = self._task_thread
        task_thread.terminate()
        task_thread.wait(3000)

        self._set_ui_enabled(True)
        self._set_status_error(True)
        self.statusBar().showMessage(f"{task_name} 強制停止", 5000)
        self._task_worker = None
        self._task_thread = None
        self._current_task_name = None

    def _start_worker(
        self,
        task_name: str,
        task: Callable[[Callable[[str], None]], None],
    ) -> None:
        if self._task_thread is not None:
            QMessageBox.warning(
                self, "実行中", "別の処理が実行中です。完了後に再実行してください。"
            )
            return

        self._task_thread = QThread(self)
        self._task_worker = BackgroundTaskWorker(task=task, task_name=task_name)
        self._task_worker.moveToThread(self._task_thread)

        self._task_thread.started.connect(self._task_worker.run)
        self._task_worker.log_emitted.connect(self.append_log)
        self._task_worker.finished.connect(self._on_worker_finished)
        self._task_worker.finished.connect(self._task_thread.quit)
        self._task_thread.finished.connect(self._task_thread.deleteLater)

        self._current_task_name = task_name
        self._set_status_error(False)
        self.statusBar().showMessage(f"{task_name} 実行中...")
        self._set_ui_enabled(False)
        self._task_thread.start()

    def _on_worker_finished(self, success: bool, detail: str) -> None:
        self._set_ui_enabled(True)
        task_name = self._current_task_name or "処理"
        if success:
            self._set_status_error(False)
            self.statusBar().showMessage(f"{task_name} 完了", 5000)
        else:
            self._set_status_error(True)
            self.statusBar().showMessage(f"{task_name} 失敗", 5000)
        if not success and detail:
            QMessageBox.critical(self, "実行失敗", detail)

        self._task_worker = None
        self._task_thread = None
        self._current_task_name = None

    def _start_single_font_task(self, config: SingleFontTaskConfig) -> None:
        self.append_log(f"[個別:フォント加工] 受信: {config}")

        def task(log: Callable[[str], None]) -> None:
            self._run_single_font_processing(config, log)

        self._start_worker("個別:フォント加工", task)

    def _run_single_font_preview(self, config: SingleFontTaskConfig) -> None:
        self.append_log(f"[個別:フォント加工][プレビュー] 受信: {config}")
        try:
            pixmap = self._generate_single_font_preview_pixmap(config)
        except Exception as error:
            message = f"[個別:フォント加工][プレビュー] 失敗: {error}"
            self.append_log(message)
            QMessageBox.warning(self, "プレビュー失敗", str(error))
            return

        preview_window = self._ensure_preview_window()
        preview_window.set_preview_pixmap(pixmap)
        if preview_window.isMinimized():
            preview_window.showNormal()
        else:
            preview_window.show()
        preview_window.raise_()
        preview_window.activateWindow()
        self.append_log("[個別:フォント加工][プレビュー] 完了")

    def _ensure_preview_window(self) -> PreviewWindow:
        if self._preview_window is None:
            self._preview_window = PreviewWindow(None)
        return self._preview_window

    @staticmethod
    def _draw_dashed_horizontal_line(
        draw: ImageDraw.ImageDraw,
        *,
        y: int,
        x_start: int,
        x_end: int,
        color: tuple[int, int, int, int],
        dash_length: int = PREVIEW_DASH_LENGTH,
        gap_length: int = PREVIEW_DASH_GAP,
        width: int = 1,
    ) -> None:
        x = x_start
        while x <= x_end:
            segment_end = min(x + dash_length, x_end)
            draw.line([(x, y), (segment_end, y)], fill=color, width=width)
            x += dash_length + gap_length

    @staticmethod
    def _get_preview_metrics_for_overlay(
        font_obj: TTFont,
    ) -> tuple[int, int, int, int, int]:
        os2_table = font_obj.get('OS/2')
        hhea_table = font_obj.get('hhea')
        post_table = font_obj.get('post')

        if os2_table is not None:
            ascent = int(os2_table.sTypoAscender)
            descent = int(os2_table.sTypoDescender)
            line_gap = int(os2_table.sTypoLineGap)
        elif hhea_table is not None:
            ascent = int(hhea_table.ascent)
            descent = int(hhea_table.descent)
            line_gap = int(hhea_table.lineGap)
        else:
            ascent = 0
            descent = 0
            line_gap = 0

        underline_position = 0
        underline_thickness = 1
        if post_table is not None:
            underline_position = int(post_table.underlinePosition)
            underline_thickness = int(post_table.underlineThickness)

        return ascent, descent, line_gap, underline_position, underline_thickness

    @staticmethod
    def _draw_preview_legend(draw: ImageDraw.ImageDraw) -> None:
        legend_font = None
        for font_path in PREVIEW_LEGEND_FONT_CANDIDATES:
            if not Path(font_path).exists():
                continue
            try:
                legend_font = ImageFont.truetype(
                    str(font_path),
                    size=PREVIEW_LEGEND_FONT_SIZE,
                )
                break
            except Exception:
                continue

        using_japanese_labels = legend_font is not None
        if legend_font is None:
            legend_font = ImageFont.load_default()

        if using_japanese_labels:
            legend_items = [
                ("solid", PREVIEW_BASELINE_COLOR, "ベースライン"),
                ("solid", PREVIEW_UNDERLINE_COLOR, "下線"),
                ("dashed", PREVIEW_METRIC_COLOR, "上端/下端/行間"),
            ]
        else:
            legend_items = [
                ("solid", PREVIEW_BASELINE_COLOR, "Baseline"),
                ("solid", PREVIEW_UNDERLINE_COLOR, "Underline"),
                ("dashed", PREVIEW_METRIC_COLOR, "Asc/Desc/LineGap"),
            ]

        sample_width = 24
        text_max_width = 0
        text_heights: list[int] = []
        for _, _, label in legend_items:
            bbox = draw.textbbox((0, 0), label, font=legend_font)
            text_max_width = max(text_max_width, max(1, bbox[2] - bbox[0]))
            text_heights.append(max(1, bbox[3] - bbox[1]))

        row_height = max(8, max(text_heights))
        content_height = row_height * len(legend_items) + PREVIEW_LEGEND_ROW_GAP * (
            len(legend_items) - 1
        )
        box_width = PREVIEW_LEGEND_PADDING * 2 + sample_width + 8 + text_max_width
        box_height = PREVIEW_LEGEND_PADDING * 2 + content_height

        image_width, image_height = draw.im.size
        left = PREVIEW_LEGEND_MARGIN_X
        top = max(
            PREVIEW_LEGEND_MARGIN_Y,
            image_height - PREVIEW_LEGEND_MARGIN_Y - box_height,
        )
        right = left + box_width
        bottom = top + box_height
        draw.rectangle(
            [(left, top), (right, bottom)],
            fill=PREVIEW_LEGEND_BACKGROUND_COLOR,
        )

        row_y = top + PREVIEW_LEGEND_PADDING
        sample_left = left + PREVIEW_LEGEND_PADDING
        text_x = sample_left + sample_width + 8

        for line_type, color, label in legend_items:
            line_y = row_y + row_height // 2
            if line_type == "dashed":
                x = sample_left
                while x <= sample_left + sample_width:
                    segment_end = min(
                        x + PREVIEW_DASH_LENGTH, sample_left + sample_width
                    )
                    draw.line([(x, line_y), (segment_end, line_y)], fill=color, width=1)
                    x += PREVIEW_DASH_LENGTH + PREVIEW_DASH_GAP
            else:
                draw.line(
                    [(sample_left, line_y), (sample_left + sample_width, line_y)],
                    fill=color,
                    width=1,
                )

            draw.text(
                (text_x, row_y), label, fill=PREVIEW_LEGEND_TEXT_COLOR, font=legend_font
            )
            row_y += row_height + PREVIEW_LEGEND_ROW_GAP

    def _generate_single_font_preview_pixmap(
        self, config: SingleFontTaskConfig
    ) -> QPixmap:
        self._validate_path_required(config.input_ttf, "入力元")
        input_ttf_path = self._resolve_user_path(config.input_ttf)
        self._validate_file_exists(input_ttf_path, "入力元")

        preview_font_obj = self._load_font_for_processing(
            input_ttf_path,
            "入力元",
            log=self.append_log,
            log_prefix="[個別:フォント加工][プレビュー][前処理]",
        )

        preview_font_obj = create_subset(preview_font_obj, config.preview_text)

        if config.glyph_weight_offset != 0:
            preview_font_obj = change_weight(
                preview_font_obj,
                offset_weight=config.glyph_weight_offset,
                debug=self._debug,
            )

        scale_width = config.horizontal_percent / 100.0
        scale_height = config.vertical_percent / 100.0
        offset_width = config.horizontal_offset
        offset_height = config.vertical_offset

        if config.mode == "base":
            self._validate_path_required(config.base_font_path, "基準フォント")
            base_font_path = self._resolve_user_path(config.base_font_path)
            self._validate_file_exists(base_font_path, "基準フォント")
            base_font_obj = self._load_font_for_processing(
                base_font_path,
                "基準フォント",
                log=self.append_log,
                log_prefix="[個別:フォント加工][プレビュー][前処理]",
            )
            with base_font_obj:
                result = harmonize_font_metrics(
                    target_font_obj=preview_font_obj,
                    base_font_obj=base_font_obj,
                    scale_width_manual=scale_width,
                    scale_height_manual=scale_height,
                    offset_width=offset_width,
                    offset_height=offset_height,
                )
                preview_font_obj = result.font_obj
        else:
            metrics_override = self._build_manual_metrics_override(config)
            manual_new_upm: int | None = None
            if metrics_override:
                manual_new_upm = int(config.metric_ascent) + abs(
                    int(config.metric_descent)
                )

            preview_font_obj = apply_font_transform(
                target_font_obj=preview_font_obj,
                scale_width=scale_width,
                scale_height=scale_height,
                offset_width=offset_width,
                offset_height=offset_height,
                new_upm=manual_new_upm,
                metrics_override=metrics_override,
            )

        buffer = io.BytesIO()
        preview_font_obj.save(buffer)
        buffer.seek(0)

        pil_font = ImageFont.truetype(buffer, size=PREVIEW_FONT_SIZE)

        measurement = Image.new("RGBA", (1, 1), (0, 0, 0, 255))
        measurement_draw = ImageDraw.Draw(measurement)
        left, top, right, bottom = measurement_draw.textbbox(
            (0, 0), config.preview_text, font=pil_font
        )
        text_width = max(1, right - left)
        text_height = max(1, bottom - top)

        padding = PREVIEW_PADDING
        image_width = max(PREVIEW_MIN_WIDTH, text_width + padding * 2)
        image_height = max(
            PREVIEW_MIN_HEIGHT,
            text_height + padding * 2 + PREVIEW_LEGEND_RESERVED_HEIGHT,
        )
        image = Image.new("RGBA", (image_width, image_height), (0, 0, 0, 255))
        draw = ImageDraw.Draw(image)
        text_x = padding - left
        text_y = padding - top
        draw.text(
            (text_x, text_y),
            config.preview_text,
            fill=(255, 255, 255, 255),
            font=pil_font,
        )

        upm = (
            int(preview_font_obj['head'].unitsPerEm)
            if 'head' in preview_font_obj
            else 0
        )
        if upm <= 0:
            upm = NORMALIZED_UPM

        pixel_per_unit = float(PREVIEW_FONT_SIZE) / float(upm)
        ascent, descent, line_gap, underline_position, underline_thickness = (
            self._get_preview_metrics_for_overlay(preview_font_obj)
        )
        pil_ascent, _pil_descent = pil_font.getmetrics()
        baseline_y = int(round(text_y + pil_ascent))

        x_start = padding
        x_end = image_width - padding

        draw.line(
            [(x_start, baseline_y), (x_end, baseline_y)],
            fill=PREVIEW_BASELINE_COLOR,
            width=PREVIEW_BASELINE_WIDTH,
        )

        ascender_y = int(round(baseline_y - float(ascent) * pixel_per_unit))
        descender_y = int(round(baseline_y - float(descent) * pixel_per_unit))
        self._draw_dashed_horizontal_line(
            draw,
            y=ascender_y,
            x_start=x_start,
            x_end=x_end,
            color=PREVIEW_METRIC_COLOR,
            width=PREVIEW_METRIC_WIDTH,
        )
        self._draw_dashed_horizontal_line(
            draw,
            y=descender_y,
            x_start=x_start,
            x_end=x_end,
            color=PREVIEW_METRIC_COLOR,
            width=PREVIEW_METRIC_WIDTH,
        )

        line_gap_y = int(round(descender_y + float(line_gap) * pixel_per_unit))
        self._draw_dashed_horizontal_line(
            draw,
            y=line_gap_y,
            x_start=x_start,
            x_end=x_end,
            color=PREVIEW_METRIC_COLOR,
            width=PREVIEW_METRIC_WIDTH,
        )

        underline_y = int(
            round(baseline_y - float(underline_position) * pixel_per_unit)
        )
        underline_height = max(
            1,
            int(round(abs(float(underline_thickness) * pixel_per_unit))),
        )
        underline_top = underline_y - (underline_height // 2)
        underline_bottom = underline_top + underline_height - 1
        draw.rectangle(
            [(x_start, underline_top), (x_end, underline_bottom)],
            fill=PREVIEW_UNDERLINE_COLOR,
        )

        self._draw_preview_legend(draw)

        png_buffer = io.BytesIO()
        image.save(png_buffer, format="PNG")
        pixmap = QPixmap()
        pixmap.loadFromData(png_buffer.getvalue(), "PNG")
        if pixmap.isNull():
            raise ValueError("プレビュー画像の生成に失敗しました。")
        return pixmap

    def _start_single_embed_task(self, config: SingleEmbedTaskConfig) -> None:
        self.append_log(f"[個別:SWF埋め込み] 受信: {config}")

        def task(log: Callable[[str], None]) -> None:
            self._run_single_embed(config, log)

        self._start_worker("個別:SWF埋め込み", task)

    def _start_batch_task(self, config: BatchFontProcessingTaskConfig) -> None:
        self.append_log(f"[一括:フォント加工] 受信: {config}")

        def task(log: Callable[[str], None]) -> None:
            self._run_font_proccessing_recipe(config, log)

        self._start_worker("一括:フォント加工モード", task)

    def _start_batch_swf_task(self, config: BatchSwfProcessingTaskConfig) -> None:
        self.append_log(f"[一括:SWF埋め込み] 受信: {config}")

        def task(log: Callable[[str], None]) -> None:
            self._run_swf_processing_recipe(config, log)

        self._start_worker("一括:SWF埋め込みモード", task)

    def _run_single_font_processing(
        self,
        config: SingleFontTaskConfig,
        log: Callable[[str], None],
    ) -> None:
        params = self._map_config_to_params(config)
        self._capture_module_output(log, lambda: process_font(params))

    def _map_config_to_params(self, config: SingleFontTaskConfig) -> dict[str, Any]:
        """GUIのコンフィグを一括処理エンジン互換のパラメータ辞書に変換する。"""
        # 一括処理エンジンの仕様（メトリクス指定による正規化）に合わせる。
        params = {
            "input_font_path": self._resolve_user_path(config.input_ttf),
            "output_font_path": self._resolve_user_path(config.output_ttf),
            "subset_text_path": (
                self._resolve_user_path(config.subset_text_path)
                if config.subset_text_path
                else None
            ),
            "remove_blank_glyphs": config.remove_empty_glyphs,
            "anonymize": config.anonymize,
            "font_name": config.anonymize_font_name,
            "mode": config.mode,
            "base_font_path": (
                self._resolve_user_path(config.base_font_path)
                if config.base_font_path
                else None
            ),
            "scale_width": config.horizontal_percent,
            "scale_height": config.vertical_percent,
            "offset_width": config.horizontal_offset,
            "offset_height": config.vertical_offset,
            "weight_offset": config.glyph_weight_offset,
            "modify_metrics": config.metric_ascent is not None,
            "ascent": config.metric_ascent,
            "descent": config.metric_descent,
            "line_gap": config.metric_line_gap,
            "u_pos": config.metric_underline_position,
            "u_thick": config.metric_underline_thickness,
            "merge_fonts": [
                {
                    "font_path": self._resolve_user_path(item.font_path),
                    "offset_width": item.offset_width,
                    "offset_height": item.offset_height,
                    "weight_offset": item.weight_offset,
                }
                for item in config.merge_fonts
            ],
            "output_font_info": True,
            "debug": self._debug,
        }
        return params

    @staticmethod
    def _count_missing_subset_glyphs(
        font_obj: TTFont,
        subset_text: str,
    ) -> tuple[int, int, int, int, list[int], list[int]]:
        target_codes = {ord(char) for char in subset_text}
        target_total = len(target_codes)
        if target_total == 0:
            return 0, 0, 0, 0, [], []

        cmap = font_obj.getBestCmap()
        has_glyf = 'glyf' in font_obj
        glyf_table = font_obj['glyf'] if has_glyf else None

        missing_unmapped = 0
        missing_no_outline = 0
        missing_unmapped_codes: list[int] = []
        missing_no_outline_codes: list[int] = []

        for code in target_codes:
            glyph_name = cmap.get(code)

            # 意図的な空白グリフは欠損扱いしない
            is_intended_blank = code in BLANK_GLYPHS or (
                glyph_name is not None and glyph_name in BLANK_GLYPHS
            )
            if is_intended_blank:
                continue

            if glyph_name is None:
                missing_unmapped += 1
                missing_unmapped_codes.append(code)
                continue

            if not has_glyf or glyf_table is None:
                continue

            if glyph_name not in glyf_table:
                missing_unmapped += 1
                missing_unmapped_codes.append(code)
                continue

            glyph = glyf_table[glyph_name]
            number_of_contours = getattr(glyph, "numberOfContours", 0)
            has_outline = number_of_contours > 0 or (
                number_of_contours < 0 and bool(getattr(glyph, "components", None))
            )
            if not has_outline:
                missing_no_outline += 1
                missing_no_outline_codes.append(code)

        missing_total = missing_unmapped + missing_no_outline
        return (
            missing_total,
            missing_unmapped,
            missing_no_outline,
            target_total,
            sorted(missing_unmapped_codes),
            sorted(missing_no_outline_codes),
        )

    @staticmethod
    def _format_codepoint_list(codes: list[int]) -> list[str]:
        lines: list[str] = []
        for code in codes:
            char = chr(code)
            display_char = repr(char)[1:-1]
            try:
                unicode_name = unicodedata.name(char)
            except ValueError:
                unicode_name = "<NO_UNICODE_NAME>"
            lines.append(f"U+{code:04X}\t{display_char}\t{unicode_name}")
        return lines

    @staticmethod
    def _build_manual_metrics_override(
        config: SingleFontTaskConfig,
    ) -> dict[str, dict[str, int]] | None:
        if (
            config.metric_ascent is None
            or config.metric_descent is None
            or config.metric_line_gap is None
            or config.metric_underline_position is None
            or config.metric_underline_thickness is None
        ):
            return None

        ascent = int(config.metric_ascent)
        descent = int(config.metric_descent)
        line_gap = int(config.metric_line_gap)
        underline_position = int(config.metric_underline_position)
        underline_thickness = int(config.metric_underline_thickness)

        return {
            "os2": {
                "usWinAscent": ascent,
                "usWinDescent": abs(descent),
                "sTypoAscender": ascent,
                "sTypoDescender": descent,
                "sTypoLineGap": line_gap,
            },
            "hhea": {
                "ascent": ascent,
                "descent": descent,
                "lineGap": line_gap,
            },
            "post": {
                "underlinePosition": underline_position,
                "underlineThickness": underline_thickness,
            },
        }

    def _run_single_embed(
        self,
        config: SingleEmbedTaskConfig,
        log: Callable[[str], None],
    ) -> None:
        params = {
            "output_swf_path": self._resolve_user_path(config.output_swf),
            "items": [
                {
                    "font_path": self._resolve_user_path(item.ttf_path),
                    "internal_name": item.internal_name,
                }
                for item in config.items
            ],
            "debug": self._debug,
        }
        self._capture_module_output(log, lambda: process_swf(params))

    def _run_font_proccessing_recipe(
        self,
        config: BatchFontProcessingTaskConfig,
        log: Callable[[str], None],
    ) -> None:
        from core.batch_processor import CLIArgs, run_batch

        cli = CLIArgs(
            recipe_path=self._resolve_user_path(config.recipe_path),
            input_path=self._resolve_user_path(config.input_dir),
            output_dir=self._resolve_user_path(config.output_dir),
            debug=self._debug,
        )
        self._capture_module_output(log, lambda: run_batch(cli))

    def _run_swf_processing_recipe(
        self,
        config: BatchSwfProcessingTaskConfig,
        log: Callable[[str], None],
    ) -> None:
        from core.batch_processor import CLIArgs, run_batch

        # 出力欄はフォルダ想定。相対/絶対どちらも可。
        output_for_cli = (
            self._resolve_user_path(config.output_dir) if config.output_dir else None
        )

        cli = CLIArgs(
            recipe_path=self._resolve_user_path(config.recipe_path),
            input_path=(
                self._resolve_user_path(config.input_dir) if config.input_dir else None
            ),
            output_dir=output_for_cli,
            debug=self._debug,
        )
        self._capture_module_output(log, lambda: run_batch(cli))

    def _load_font_for_processing(
        self,
        font_path: Path,
        label: str,
        log: Callable[[str], None] | None = None,
        log_prefix: str = "[個別:フォント加工][前処理]",
    ) -> TTFont:
        with TTFont(str(font_path)) as source_font_obj:
            loaded_font_obj = reopen_font(source_font_obj)

        if is_otf_path(font_path):
            if loaded_font_obj.sfntVersion != "OTTO" or "CFF " not in loaded_font_obj:
                raise ValueError(f"{label} がOTF形式として解釈できません: {font_path}")
            otf_to_ttf(loaded_font_obj)
            if log is not None:
                log(f"{log_prefix} OTFをオンメモリでフォント変換: {font_path.name}")

        return loaded_font_obj

    @staticmethod
    def _resolve_user_path(value: str) -> Path:
        raw_value = value.strip()
        normalized = raw_value.strip('"\'')
        expanded = os.path.expandvars(os.path.expanduser(normalized))
        return Path(expanded).resolve()

    @staticmethod
    def _validate_file_exists(path: Path, label: str) -> None:
        if not path.exists() or not path.is_file():
            raise ValueError(f"{label} が存在しません: {path}")

    @staticmethod
    def _safe_move_file(src: Path, dst: Path) -> None:
        src_path = src.resolve()
        dst_path = dst.resolve()

        if src_path == dst_path:
            return

        dst_path.parent.mkdir(parents=True, exist_ok=True)

        if dst_path.exists():
            dst_path.unlink()

        same_drive = src_path.drive.casefold() == dst_path.drive.casefold()
        if same_drive:
            os.replace(src_path, dst_path)
            return

        shutil.move(str(src_path), str(dst_path))

    @staticmethod
    def _capture_module_output(
        log: Callable[[str], None],
        action: Callable[[], object],
    ) -> None:
        stream = _LogStream(log)
        with contextlib.redirect_stdout(stream), contextlib.redirect_stderr(stream):
            result = action()
            stream.flush()
        if result is False:
            raise RuntimeError("モジュール処理が失敗しました。ログを確認してください。")

    @staticmethod
    def _validate_path_required(value: str, label: str) -> None:
        if not value:
            raise ValueError(f"{label} が未指定です")
