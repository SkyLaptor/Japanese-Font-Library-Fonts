from __future__ import annotations

import contextlib
import io
import os
import re
import shutil
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import yaml
from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw, ImageFont
from PyQt6.QtCore import QObject, Qt, QThread, pyqtSignal
from PyQt6.QtGui import QDragEnterEvent, QDragMoveEvent, QDropEvent, QKeyEvent, QPixmap
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QButtonGroup,
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
    QRadioButton,
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
    EXCLUDE_CHARS,
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
    TEMPLATE_FONTSWF_PATH,
)
from core.ffdec_wrapper import (
    detect_java_executable,
    ensure_ffdec_runtime,
    ensure_java_runtime,
)
from core.font_processor import reopen_font
from modules.anonymize_info import anonymize_info
from modules.change_weight import change_weight
from modules.create_subset import create_subset
from modules.harmonize_font_metrics import apply_font_transform, harmonize_font_metrics
from modules.merge_font import merge_font_objects
from modules.remove_empty_glyphs import remove_empty_glyphs
from modules.skyrim_builder import ACTION_MAP, dispatch_action
from modules.skyrim_swf_patcher import (
    patch_swf_internal_fontname,
    patch_swf_internal_fontnames,
    replace_glyph_in_swf,
    replace_glyphs_in_swf,
)
from utils.file_io import load_text

PREVIEW_SAMPLE_TEXT = "0Aa永あ"


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
    horizontal_offset: float
    vertical_offset: float
    glyph_weight_offset: int
    metric_ascent: int | None
    metric_descent: int | None
    metric_line_gap: int | None
    metric_underline_position: int | None
    metric_underline_thickness: int | None
    base_font_path: str
    merge_fonts: list[str]


@dataclass(slots=True)
class EmbedItem:
    ttf_path: str
    internal_name: str


@dataclass(slots=True)
class SingleEmbedTaskConfig:
    output_swf: str
    items: list[EmbedItem]


@dataclass(slots=True)
class BatchTaskConfig:
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
            if Path(path).suffix.lower() != ".ttf":
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
            if Path(path).suffix.lower() != ".ttf":
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


class SingleFontProcessingTab(QWidget):
    execute_requested = pyqtSignal(object)
    preview_requested = pyqtSignal(object)
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

        io_group = QGroupBox("入力 / 出力")
        io_layout = QVBoxLayout(io_group)
        self.input_ttf_edit = QLineEdit()
        self.output_ttf_edit = QLineEdit()
        input_label = QLabel("入力TTF")
        output_label = QLabel("出力TTF")
        btn_browse_input = QPushButton("入力TTFを選択")
        btn_browse_output = QPushButton("保存先を選択")
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

        mode_group = QGroupBox("モード切り替え")
        mode_layout = QVBoxLayout(mode_group)
        self.mode_manual_radio = QRadioButton("任意変形モード（数値指定）")
        self.mode_base_radio = QRadioButton("ベース基準モード（比較計算）")
        self.mode_manual_radio.setToolTip(
            "入力した拡大率・オフセット・太さ変更量をそのまま適用します。"
        )
        self.mode_base_radio.setToolTip(
            "ベースフォントに近づくように、入力値を基準に比較計算して適用します。"
        )
        self.mode_manual_radio.setChecked(True)
        self.mode_button_group = QButtonGroup(self)
        self.mode_button_group.addButton(self.mode_manual_radio)
        self.mode_button_group.addButton(self.mode_base_radio)
        self.mode_button_group.buttonToggled.connect(self._on_mode_toggled)

        mode_select_row = QWidget()
        mode_select_row_layout = QHBoxLayout(mode_select_row)
        mode_select_row_layout.setContentsMargins(0, 0, 0, 0)
        mode_select_row_layout.addWidget(self.mode_manual_radio)
        mode_select_row_layout.addWidget(self.mode_base_radio)
        mode_select_row_layout.addStretch(1)

        self.base_font_edit = QLineEdit()
        self.base_font_edit.setEnabled(False)
        self.base_font_edit.setToolTip(
            "ベース基準モードで比較対象にするTTFを指定します。"
        )
        self.base_font_edit.editingFinished.connect(
            self._update_metrics_display_from_base_font
        )
        btn_browse_base_font = QPushButton("ベースフォントを選択")
        btn_browse_base_font.setEnabled(False)
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
        base_font_wrapper_row_layout.addWidget(QLabel("ベースフォント"))
        base_font_wrapper_row_layout.addWidget(base_font_row)

        mode_layout.addWidget(mode_select_row)
        mode_layout.addWidget(base_font_wrapper_row)
        root_layout.addWidget(mode_group)

        params_group = QGroupBox("パラメータ")
        params_layout = QVBoxLayout(params_group)

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

        self.horizontal_offset_spin = QDoubleSpinBox()
        self.horizontal_offset_spin.setRange(-5000.0, 5000.0)
        self.horizontal_offset_spin.setValue(0.0)
        self.horizontal_offset_spin.setToolTip(
            "横方向の位置補正です。正の値で右、負の値で左に移動します。"
        )

        self.vertical_offset_spin = QDoubleSpinBox()
        self.vertical_offset_spin.setRange(-5000.0, 5000.0)
        self.vertical_offset_spin.setValue(0.0)
        self.vertical_offset_spin.setToolTip(
            "縦方向の位置補正です。正の値で上、負の値で下に移動します。"
        )

        self.glyph_weight_offset_spin = QSpinBox()
        self.glyph_weight_offset_spin.setRange(-5000, 5000)
        self.glyph_weight_offset_spin.setValue(0)
        self.glyph_weight_offset_spin.setToolTip(
            "入力TTFのグリフ輪郭の太さを調整します。\n"
            "正の値で太く、負の値で細くなります。\n"
            "補完フォント（マージ対象）には適用されません。"
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
            "匿名化後のフォント名を入力します。\n"
            "空白や記号は使用できません（英数字とアンダースコアのみ）。"
        )
        self.anonymize_check.toggled.connect(self.anonymize_font_name_edit.setEnabled)

        self.manual_metrics_check = QCheckBox("メトリクス変更")
        self.manual_metrics_check.setChecked(False)
        self.manual_metrics_check.setToolTip(
            "有効時は下の上端/下端/行間/下線位置/下線太さの値でメトリクスを変更します。"
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
            str((SUBSETS_DIR / "subset_jp_full.txt").resolve())
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
        glyph_weight_label = QLabel("太さ変更量（em）")
        horizontal_percent_unit_label = QLabel("%")
        vertical_percent_unit_label = QLabel("%")
        horizontal_offset_unit_label = QLabel("em")
        vertical_offset_unit_label = QLabel("em")

        unit_label_width = max(
            horizontal_percent_unit_label.sizeHint().width(),
            vertical_percent_unit_label.sizeHint().width(),
            horizontal_offset_unit_label.sizeHint().width(),
            vertical_offset_unit_label.sizeHint().width(),
        )
        horizontal_percent_unit_label.setFixedWidth(unit_label_width)
        vertical_percent_unit_label.setFixedWidth(unit_label_width)
        horizontal_offset_unit_label.setFixedWidth(unit_label_width)
        vertical_offset_unit_label.setFixedWidth(unit_label_width)

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

        btn_preview = QPushButton("プレビュー")
        btn_preview.clicked.connect(self._emit_preview)
        root_layout.addWidget(btn_preview)

        merge_group = QGroupBox("マージ機能（補完フォント）")
        merge_layout = QVBoxLayout(merge_group)
        self.merge_fonts_list = MergeFontsListWidget()
        self.merge_fonts_list.setSelectionMode(
            QAbstractItemView.SelectionMode.ExtendedSelection
        )
        self.merge_fonts_list.setToolTip(
            "補完フォント一覧です。ドラッグ&ドロップで追加、並び順変更ができます。"
        )
        merge_row_height = self.fontMetrics().height() + 8
        self.merge_fonts_list.setFixedHeight(merge_row_height * 3 + 4)
        merge_buttons = QHBoxLayout()
        btn_add_merge = QPushButton("追加")
        btn_remove_merge = QPushButton("削除")
        btn_add_merge.clicked.connect(self._add_merge_fonts)
        btn_remove_merge.clicked.connect(self._remove_merge_fonts)
        merge_buttons.addWidget(btn_add_merge)
        merge_buttons.addWidget(btn_remove_merge)
        merge_layout.addWidget(self.merge_fonts_list)
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

    def _on_mode_toggled(self, button: QRadioButton, checked: bool) -> None:
        if button is not self.mode_base_radio:
            return
        self.base_font_edit.setEnabled(checked)
        self.base_font_button.setEnabled(checked)
        if checked:
            self._update_metrics_display_from_base_font()

    def _select_input_ttf(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "加工対象TTFを選択", "", "TTF (*.ttf)"
        )
        if path:
            self.input_ttf_edit.setText(path)

    def _select_output_ttf(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self,
            "保存先TTFを選択",
            "",
            "TTF (*.ttf)",
        )
        if path:
            self.output_ttf_edit.setText(path)

    def _select_base_font(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "ベースフォントを選択", "", "TTF (*.ttf)"
        )
        if path:
            self.base_font_edit.setText(path)
            self._update_metrics_display_from_base_font()

    def _update_metrics_display_from_base_font(self) -> None:
        if not self.mode_base_radio.isChecked():
            return

        base_font_path = self.base_font_edit.text().strip()
        if not base_font_path:
            return

        path_obj = Path(base_font_path)
        if not path_obj.exists():
            return

        try:
            with TTFont(str(path_obj)) as base_font_obj:
                base_upm = int(base_font_obj['head'].unitsPerEm)
                scale_for_1024 = 1.0
                if base_upm > 0:
                    scale_for_1024 = float(NORMALIZED_UPM) / float(base_upm)

                def _to_1024(value: int) -> int:
                    return int(round(int(value) * scale_for_1024))

                hhea_table = base_font_obj.get('hhea')
                os2_table = base_font_obj.get('OS/2')
                post_table = base_font_obj.get('post')

                if os2_table is not None:
                    self.metric_ascent_spin.setValue(
                        _to_1024(int(os2_table.sTypoAscender))
                    )
                    self.metric_descent_spin.setValue(
                        _to_1024(int(os2_table.sTypoDescender))
                    )
                    self.metric_line_gap_spin.setValue(
                        _to_1024(int(os2_table.sTypoLineGap))
                    )
                elif hhea_table is not None:
                    self.metric_ascent_spin.setValue(_to_1024(int(hhea_table.ascent)))
                    self.metric_descent_spin.setValue(_to_1024(int(hhea_table.descent)))
                    self.metric_line_gap_spin.setValue(
                        _to_1024(int(hhea_table.lineGap))
                    )

                if post_table is not None:
                    self.metric_underline_position_spin.setValue(
                        _to_1024(int(post_table.underlinePosition))
                    )
                    self.metric_underline_thickness_spin.setValue(
                        _to_1024(int(post_table.underlineThickness))
                    )
        except Exception:
            return

    def _add_merge_fonts(self) -> None:
        paths, _ = QFileDialog.getOpenFileNames(
            self,
            "補完用フォントを選択",
            "",
            "TTF (*.ttf)",
        )
        self.merge_fonts_list.add_paths(paths)

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
        for item in self.merge_fonts_list.selectedItems():
            self.merge_fonts_list.takeItem(self.merge_fonts_list.row(item))

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
        delta = value - self._last_vertical_percent
        self._last_vertical_percent = value
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
        config = self._build_single_font_config()
        if config is None:
            return
        self.execute_requested.emit(config)

    def _emit_preview(self) -> None:
        config = self._build_single_font_config()
        if config is None:
            return
        self.preview_requested.emit(config)

    def set_executing_state(self, executing: bool) -> None:
        self.execute_button.setText(
            self._EXECUTING_LABEL if executing else self._EXECUTE_LABEL
        )

    def _build_single_font_config(self) -> SingleFontTaskConfig | None:
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

        is_manual_mode = self.mode_manual_radio.isChecked()
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

        config = SingleFontTaskConfig(
            input_ttf=self.input_ttf_edit.text().strip(),
            output_ttf=self.output_ttf_edit.text().strip(),
            subset_text_path=self.subset_text_edit.text().strip(),
            remove_empty_glyphs=self.remove_empty_glyphs_check.isChecked(),
            anonymize=self.anonymize_check.isChecked(),
            anonymize_font_name=anonymize_font_name,
            mode="base" if self.mode_base_radio.isChecked() else "manual",
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
            merge_fonts=[
                self.merge_fonts_list.item(index).text()
                for index in range(self.merge_fonts_list.count())
            ],
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
        output_label = QLabel("出力SWF")
        btn_output = QPushButton("出力SWFを選択")
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

        table_group = QGroupBox("TTFリスト（内部名付き）")
        table_layout = QVBoxLayout(table_group)
        self.embed_table = SingleEmbedTableWidget()
        self.embed_table.setHorizontalHeaderLabels(["TTFパス", "内部名"])
        self.embed_table.setToolTip(
            "埋め込むTTFと内部名の一覧です。内部名はSWF内の識別名です。"
        )
        self.embed_table._apply_column_ratio()
        self.embed_table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.embed_table.setSelectionMode(
            QAbstractItemView.SelectionMode.ExtendedSelection
        )

        table_buttons = QHBoxLayout()
        btn_add_row = QPushButton("TTF追加")
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
            self, "埋め込みTTFを選択", "", "TTF (*.ttf)"
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
        items: list[EmbedItem] = []
        for row in range(self.embed_table.rowCount()):
            ttf_item = self.embed_table.item(row, 0)
            internal_item = self.embed_table.item(row, 1)
            ttf_path = ttf_item.text().strip() if ttf_item else ""
            internal_name = internal_item.text().strip() if internal_item else ""
            if ttf_path:
                items.append(EmbedItem(ttf_path=ttf_path, internal_name=internal_name))

        config = SingleEmbedTaskConfig(
            output_swf=self.output_swf_edit.text().strip(),
            items=items,
        )
        self.execute_requested.emit(config)

    def set_executing_state(self, executing: bool) -> None:
        self.execute_button.setText(
            self._EXECUTING_LABEL if executing else self._EXECUTE_LABEL
        )


class BatchModeTab(QWidget):
    execute_requested = pyqtSignal(object)
    _EXECUTE_LABEL = "バッチ実行（マージ→SWF埋め込み）"
    _EXECUTING_LABEL = "バッチ実行中..."

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self) -> None:
        root_layout = QVBoxLayout(self)

        form_group = QGroupBox("レシピ / 拠点設定")
        form_layout = QVBoxLayout(form_group)

        self.recipe_edit = QLineEdit()
        self.input_dir_edit = QLineEdit()
        self.output_dir_edit = QLineEdit()
        self.recipe_edit.setToolTip("バッチ処理のレシピYAMLを指定します。")
        self.input_dir_edit.setToolTip(
            "レシピで参照する入力ファイルのルートディレクトリです。"
        )
        self.output_dir_edit.setToolTip("生成結果の出力先ディレクトリです。")

        recipe_label = QLabel("レシピ")
        input_dir_label = QLabel("input_dir")
        output_dir_label = QLabel("output_dir")

        btn_recipe = QPushButton("recipe.ymlを選択")
        btn_input_dir = QPushButton("input_dirを選択")
        btn_output_dir = QPushButton("output_dirを選択")

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

    def _select_input_dir(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "input_dirを選択")
        if path:
            self.input_dir_edit.setText(path)

    def _select_output_dir(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "output_dirを選択")
        if path:
            self.output_dir_edit.setText(path)

    def _emit_execute(self) -> None:
        config = BatchTaskConfig(
            recipe_path=self.recipe_edit.text().strip(),
            input_dir=self.input_dir_edit.text().strip(),
            output_dir=self.output_dir_edit.text().strip(),
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

    def __init__(self) -> None:
        super().__init__()
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
        self.batch_tab = BatchModeTab()
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
        self.tabs.addTab(self.batch_tab, "一括：バッチモード")

        top_layout.addWidget(self.tabs)

        bottom_widget = QWidget()
        bottom_layout = QVBoxLayout(bottom_widget)
        bottom_layout.setContentsMargins(0, 0, 0, 0)
        bottom_layout.addWidget(QLabel("共通ログ"))
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
        self.single_embed_tab.execute_requested.connect(self._start_single_embed_task)
        self.batch_tab.execute_requested.connect(self._start_batch_task)
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
                "通信環境を確認し、data/ffdec と data/java/bin/java(.exe) を手動配置してください。",
            )
        finally:
            self.statusBar().clearMessage()

    def _set_ui_enabled(self, enabled: bool) -> None:
        self.tabs.setEnabled(enabled)
        executing = not enabled
        self.single_font_tab.set_executing_state(executing)
        self.single_embed_tab.set_executing_state(executing)
        self.batch_tab.set_executing_state(executing)
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
        self._validate_path_required(config.input_ttf, "入力TTF")
        input_ttf_path = self._resolve_user_path(config.input_ttf)
        self._validate_file_exists(input_ttf_path, "入力TTF")

        with TTFont(str(input_ttf_path)) as input_font_obj:
            preview_font_obj = reopen_font(input_font_obj)

        preview_font_obj = create_subset(preview_font_obj, PREVIEW_SAMPLE_TEXT)

        if config.glyph_weight_offset != 0:
            preview_font_obj = change_weight(
                preview_font_obj,
                offset_weight=config.glyph_weight_offset,
                debug=True,
            )

        scale_width = config.horizontal_percent / 100.0
        scale_height = config.vertical_percent / 100.0
        offset_width = int(round(config.horizontal_offset))
        offset_height = int(round(config.vertical_offset))

        if config.mode == "base":
            self._validate_path_required(config.base_font_path, "ベースフォント")
            base_font_path = self._resolve_user_path(config.base_font_path)
            self._validate_file_exists(base_font_path, "ベースフォント")
            with TTFont(str(base_font_path)) as base_font_obj:
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
                scale_x=scale_width,
                scale_y=scale_height,
                offset_x=offset_width,
                offset_y=offset_height,
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
            (0, 0), PREVIEW_SAMPLE_TEXT, font=pil_font
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
            PREVIEW_SAMPLE_TEXT,
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

    def _start_batch_task(self, config: BatchTaskConfig) -> None:
        self.append_log(f"[一括:バッチモード] 受信: {config}")

        def task(log: Callable[[str], None]) -> None:
            self._run_recipe(config, log)

        self._start_worker("一括:バッチモード", task)

    def _run_single_font_processing(
        self,
        config: SingleFontTaskConfig,
        log: Callable[[str], None],
    ) -> None:
        self._validate_path_required(config.input_ttf, "入力TTF")
        self._validate_path_required(config.output_ttf, "出力TTF")

        input_ttf_path = self._resolve_user_path(config.input_ttf)
        output_ttf_path = self._resolve_user_path(config.output_ttf)
        self._validate_file_exists(input_ttf_path, "入力TTF")

        subset_text: str | None = None
        if config.subset_text_path:
            subset_path = self._resolve_user_path(config.subset_text_path)
            self._validate_file_exists(subset_path, "サブセットテキスト")
            subset_text = load_text(str(subset_path), EXCLUDE_CHARS)
            log(
                "[個別:フォント加工][前処理] サブセット有効: "
                f"{subset_path}（マージ前に適用）"
            )
        else:
            log("[個別:フォント加工][前処理] サブセット無効: サブセットテキスト未指定")

        with TTFont(str(input_ttf_path)) as input_font_obj:
            current_base_font_obj = reopen_font(input_font_obj)

        if subset_text is not None:
            log(
                "[個別:フォント加工][前処理] 入力TTFへサブセット適用 "
                f"（マージ前）: {input_ttf_path.name}"
            )
            current_base_font_obj = create_subset(current_base_font_obj, subset_text)

        if config.remove_empty_glyphs:
            log("[個別:フォント加工] 空白グリフ除去を実行")
            current_base_font_obj = remove_empty_glyphs(current_base_font_obj)

        if config.glyph_weight_offset != 0:
            log(
                "[個別:フォント加工] グリフ太さ調整を実行 "
                f"(変更量={config.glyph_weight_offset}) [入力TTFのみ]"
            )
            current_base_font_obj = change_weight(
                current_base_font_obj,
                offset_weight=config.glyph_weight_offset,
                debug=True,
            )

        scale_width = config.horizontal_percent / 100.0
        scale_height = config.vertical_percent / 100.0
        offset_width = int(round(config.horizontal_offset))
        offset_height = int(round(config.vertical_offset))

        if config.mode == "base":
            self._validate_path_required(config.base_font_path, "ベースフォント")
            base_font_path = self._resolve_user_path(config.base_font_path)
            self._validate_file_exists(base_font_path, "ベースフォント")
            with TTFont(str(base_font_path)) as base_font_obj:
                result = harmonize_font_metrics(
                    target_font_obj=current_base_font_obj,
                    base_font_obj=base_font_obj,
                    scale_width_manual=scale_width,
                    scale_height_manual=scale_height,
                    offset_width=offset_width,
                    offset_height=offset_height,
                )
                current_base_font_obj = result.font_obj
        else:
            metrics_override = self._build_manual_metrics_override(config)
            manual_new_upm: int | None = None
            if metrics_override:
                manual_new_upm = int(config.metric_ascent) + abs(
                    int(config.metric_descent)
                )
                log(
                    "[個別:フォント加工] 手動メトリクスを適用: "
                    f"上端={config.metric_ascent}, "
                    f"下端={config.metric_descent}, "
                    f"行間={config.metric_line_gap}, "
                    f"下線位置={config.metric_underline_position}, "
                    f"下線太さ={config.metric_underline_thickness}"
                )
                log(
                    f"[個別:フォント加工] UPMをメトリクスから自動決定: {manual_new_upm}"
                )

            current_base_font_obj = apply_font_transform(
                target_font_obj=current_base_font_obj,
                scale_x=scale_width,
                scale_y=scale_height,
                offset_x=offset_width,
                offset_y=offset_height,
                new_upm=manual_new_upm,
                metrics_override=metrics_override,
            )

        for merge_index, merge_font in enumerate(config.merge_fonts, start=1):
            merge_font_path = self._resolve_user_path(merge_font)
            self._validate_file_exists(
                merge_font_path,
                f"補完フォント[{merge_index}]",
            )
            log(
                "[個別:フォント加工][マージ] マージ実行 "
                f"({merge_index}/{len(config.merge_fonts)}): {merge_font_path.name} "
                "[前処理サブセット済み→自動サイズ適合→メトリクス同期→手動変形→浄化]"
            )
            with TTFont(str(merge_font_path)) as merge_font_obj:
                prepared_merge_font_obj = merge_font_obj
                if subset_text is not None:
                    log(
                        "[個別:フォント加工][前処理] 補完フォントへサブセット適用 "
                        f"（マージ前）: {merge_font_path.name}"
                    )
                    prepared_merge_font_obj = create_subset(
                        prepared_merge_font_obj,
                        subset_text,
                    )

                current_base_font_obj = merge_font_objects(
                    base_font_obj=current_base_font_obj,
                    interpolation_font_obj=prepared_merge_font_obj,
                    scale_width=scale_width,
                    scale_height=scale_height,
                    offset_width=offset_width,
                    offset_height=offset_height,
                    remove_empty=config.remove_empty_glyphs,
                    anonymize=config.anonymize,
                    anonymize_font_name=config.anonymize_font_name,
                    debug=True,
                )

        if config.anonymize and not config.merge_fonts:
            log("[個別:フォント加工] 匿名化を実行")
            current_base_font_obj = anonymize_info(
                current_base_font_obj,
                font_name=config.anonymize_font_name,
            )

        if subset_text is not None:
            (
                missing_total,
                missing_unmapped,
                missing_no_outline,
                target_total,
                missing_unmapped_codes,
                missing_no_outline_codes,
            ) = self._count_missing_subset_glyphs(current_base_font_obj, subset_text)
            log(
                "[個別:フォント加工][検査] 出力直前サブセット欠損: "
                f"{missing_total}/{target_total} "
                f"(未マップ={missing_unmapped}, アウトライン無し={missing_no_outline})"
            )

            if missing_total > 0:
                output_ttf_path.parent.mkdir(parents=True, exist_ok=True)
                report_path = output_ttf_path.with_suffix(".txt")
                report_lines = [
                    "[サブセット欠損レポート]",
                    f"出力フォント: {output_ttf_path.name}",
                    f"対象コードポイント数: {target_total}",
                    f"欠損総数: {missing_total}",
                    f"未マップ数: {missing_unmapped}",
                    f"アウトライン無し数: {missing_no_outline}",
                    "",
                    "[未マップ]",
                ]
                report_lines.extend(
                    self._format_codepoint_list(missing_unmapped_codes)
                    if missing_unmapped_codes
                    else ["(なし)"]
                )
                report_lines.append("")
                report_lines.append("[アウトライン無し]")
                report_lines.extend(
                    self._format_codepoint_list(missing_no_outline_codes)
                    if missing_no_outline_codes
                    else ["(なし)"]
                )

                report_path.write_text("\n".join(report_lines), encoding="utf-8")
                log(f"[個別:フォント加工][検査] 欠損レポートを出力: {report_path}")

        output_ttf_path.parent.mkdir(parents=True, exist_ok=True)
        current_base_font_obj.save(str(output_ttf_path))
        log(f"[個別:フォント加工] 完了: {output_ttf_path}")
        if config.mode == "base":
            self._validate_path_required(config.base_font_path, "ベースフォント")

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
        self._validate_path_required(config.output_swf, "出力SWF")
        if not config.items:
            raise ValueError("埋め込み対象TTFが未指定です")

        target_swf = TEMPLATE_FONTSWF_PATH
        output_swf = self._resolve_user_path(config.output_swf)
        self._validate_file_exists(target_swf, "テンプレートSWF")

        output_swf.parent.mkdir(parents=True, exist_ok=True)

        resolved_items: list[tuple[Path, str]] = []
        for index, item in enumerate(config.items, start=1):
            ttf_path = self._resolve_user_path(item.ttf_path)
            self._validate_file_exists(ttf_path, f"埋め込みTTF[{index}]")
            internal_name = item.internal_name.strip() or ttf_path.stem
            resolved_items.append((ttf_path, internal_name))

        if len(resolved_items) == 1:
            ttf_path, internal_name = resolved_items[0]

            self._capture_module_output(
                log,
                lambda: replace_glyph_in_swf(target_swf, output_swf, ttf_path),
            )
            self._capture_module_output(
                log,
                lambda: patch_swf_internal_fontname(output_swf, internal_name),
            )
            log(f"[個別:SWF埋め込み] 完了: {output_swf}")
            return

        ttf_paths = [ttf_path for ttf_path, _ in resolved_items]
        internal_names_by_id = {
            index: internal_name
            for index, (_, internal_name) in enumerate(resolved_items, start=1)
        }

        self._capture_module_output(
            log,
            lambda: replace_glyphs_in_swf(target_swf, output_swf, ttf_paths),
        )
        self._capture_module_output(
            log,
            lambda: patch_swf_internal_fontnames(output_swf, internal_names_by_id),
        )
        log(
            f"[個別:SWF埋め込み] 完了: {output_swf} "
            f"(埋め込み数: {len(resolved_items)})"
        )

    def _run_recipe(
        self,
        config: BatchTaskConfig,
        log: Callable[[str], None],
    ) -> None:
        self._validate_path_required(config.recipe_path, "recipe.yml")
        self._validate_path_required(config.input_dir, "input_dir")
        self._validate_path_required(config.output_dir, "output_dir")
        recipe_path = self._resolve_user_path(config.recipe_path)
        self._validate_file_exists(recipe_path, "recipe.yml")

        with recipe_path.open("r", encoding="utf-8") as recipe_file:
            recipe_data = yaml.safe_load(recipe_file) or {}

        steps = recipe_data.get("steps")
        if not isinstance(steps, list) or not steps:
            actions = recipe_data.get("actions")
            if isinstance(actions, list) and actions:
                steps = [{"action": action_name} for action_name in actions]

        if not isinstance(steps, list) or not steps:
            raise ValueError(
                "recipe.yml に steps または actions が見つかりません。"
                "例: steps: [{action: merge_font}]"
            )

        shared_kwargs = {
            "work_dir": str(self._resolve_user_path(config.input_dir)),
            "base_line": recipe_data.get("base_line", 0),
            "merge_conf": recipe_data.get("merge_conf"),
            "anonymize": bool(recipe_data.get("anonymize", False)),
            "output_font_info": bool(recipe_data.get("output_font_info", False)),
            "debug": bool(recipe_data.get("debug", False)),
        }

        output_dir = self._resolve_user_path(config.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        for step_index, step in enumerate(steps, start=1):
            if isinstance(step, str):
                action_name = step
                step_kwargs: dict[str, object] = {}
            elif isinstance(step, dict):
                action_name = str(step.get("action", "")).strip()
                step_kwargs = {
                    key: value for key, value in step.items() if key != "action"
                }
            else:
                raise ValueError(f"steps[{step_index}] の形式が不正です: {step}")

            if action_name not in ACTION_MAP:
                raise ValueError(f"未対応アクションです: {action_name}")

            run_kwargs = {**shared_kwargs, **step_kwargs, "action": action_name}
            log(f"[一括:バッチモード] 実行 ({step_index}/{len(steps)}): {action_name}")
            self._capture_module_output(
                log, lambda kwargs=run_kwargs: dispatch_action(**kwargs)
            )

        log(f"[一括:バッチモード] 完了: {recipe_path}")

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
