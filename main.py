import argparse
import sys

try:
    import winreg
except Exception:  # pragma: no cover - Windows以外向け
    winreg = None

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QPalette
from PyQt6.QtWidgets import QApplication

from src.gui.main_window import MainWindow


def parse_cli_args(argv: list[str]) -> tuple[bool, list[str]]:
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", action="store_true")
    parsed, qt_args = parser.parse_known_args(argv[1:])

    app_argv = [argv[0], *qt_args]
    return parsed.debug, app_argv


def run_app(app: QApplication, *, debug: bool = False) -> int:
    window = MainWindow()
    if debug:
        window.append_log("[DEBUG] Debug mode is enabled")
    window.show()
    return app.exec()


def _detect_dark_mode(app: QApplication) -> bool:
    style_hints = app.styleHints()
    color_scheme = style_hints.colorScheme()
    if color_scheme == Qt.ColorScheme.Dark:
        return True
    if color_scheme == Qt.ColorScheme.Light:
        return False

    if winreg is not None:
        try:
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize",
            ) as key:
                apps_use_light_theme, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
                return apps_use_light_theme == 0
        except OSError:
            pass

    return True


def _apply_theme(app: QApplication, *, dark_mode: bool) -> None:
    app.setStyle("Fusion")
    palette = QPalette()

    if dark_mode:
        palette.setColor(QPalette.ColorRole.Window, QColor(30, 30, 30))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(230, 230, 230))
        palette.setColor(QPalette.ColorRole.Base, QColor(42, 42, 42))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(52, 52, 52))
        palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(40, 40, 40))
        palette.setColor(QPalette.ColorRole.ToolTipText, QColor(235, 235, 235))
        palette.setColor(QPalette.ColorRole.Text, QColor(230, 230, 230))
        palette.setColor(QPalette.ColorRole.Button, QColor(45, 45, 45))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(230, 230, 230))
        palette.setColor(QPalette.ColorRole.BrightText, QColor(255, 80, 80))
        palette.setColor(QPalette.ColorRole.Highlight, QColor(86, 156, 214))
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))

        app.setStyleSheet(
            """
            QLineEdit, QSpinBox, QDoubleSpinBox, QTextEdit, QPlainTextEdit, QListWidget, QTableWidget {
                background-color: #2f2f2f;
                color: #e6e6e6;
                border: 1px solid #575757;
                border-radius: 4px;
                selection-background-color: #569cd6;
            }
            QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QTextEdit:focus, QPlainTextEdit:focus {
                border: 1px solid #6aa8df;
            }
            """
        )
    else:
        palette.setColor(QPalette.ColorRole.Window, QColor(245, 245, 245))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(35, 35, 35))
        palette.setColor(QPalette.ColorRole.Base, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(240, 240, 240))
        palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.ToolTipText, QColor(35, 35, 35))
        palette.setColor(QPalette.ColorRole.Text, QColor(35, 35, 35))
        palette.setColor(QPalette.ColorRole.Button, QColor(240, 240, 240))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(35, 35, 35))
        palette.setColor(QPalette.ColorRole.BrightText, QColor(220, 20, 60))
        palette.setColor(QPalette.ColorRole.Highlight, QColor(0, 120, 215))
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))

        app.setStyleSheet("")

    app.setPalette(palette)


def main() -> None:
    debug, app_argv = parse_cli_args(sys.argv)

    app = QApplication(app_argv)
    _apply_theme(app, dark_mode=_detect_dark_mode(app))
    sys.exit(run_app(app, debug=debug))


if __name__ == "__main__":
    main()
