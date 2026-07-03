# Material Design 3 Inspired Style definitions for Bhumi Billing

DARK_QSS = """
/* Dialogs (including QDialog, QMessageBox) */
QDialog, QMessageBox {
    background-color: #1e1e1e;
    color: #e0e0e0;
    border: 1px solid #2d2d2d;
    border-radius: 8px;
}

QDialog QLineEdit, QMessageBox QLineEdit {
    background-color: #242424;
    color: #ffffff;
    border: 1.5px solid #3c3c3c;
    border-radius: 6px;
    padding: 6px 12px;
}

QComboBox {
    background-color: #2d2d2d;
    color: #e0e0e0;
    border: 1px solid #3c3c3c;
    border-radius: 6px;
    padding: 4px 8px;
}

QComboBox QAbstractItemView {
    background-color: #2d2d2d;
    color: #e0e0e0;
    selection-background-color: #3a3a3a;
    selection-color: #ffffff;
}


QWidget {
    color: #e0e0e0;
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 13px;
}

QLabel {
    background: transparent;
}

/* Primary Header Card */
#HeaderCard {
    background-color: #1e1e1e;
    border-radius: 8px;
    padding: 10px;
    border: 1px solid #2d2d2d;
}

/* Text Inputs / Edits */
QLineEdit, QTextEdit {
    background-color: #242424;
    border: 1.5px solid #3c3c3c;
    border-radius: 6px;
    padding: 6px 12px;
    color: #ffffff;
    selection-background-color: #0d6efd;
}

/* Glow Border on Focused inputs for extreme keyboard visibility */
QLineEdit:focus, QTextEdit:focus {
    border: 2px solid #3b82f6;
    background-color: #2a2a2a;
}

/* Labels on inputs */
QLabel#input_label {
    font-weight: bold;
    color: #9ca3af;
    font-size: 11px;
}

/* Table Widget styling */
QTableWidget {
    background-color: #1e1e1e;
    alternate-background-color: #242424;
    border: 1px solid #2d2d2d;
    gridline-color: #2d2d2d;
    border-radius: 6px;
    color: #e0e0e0;
    selection-background-color: #0d6efd;
    selection-color: #ffffff;
}

QTableWidget::item {
    padding: 8px;
}

QHeaderView::section {
    background-color: #2d2d2d;
    padding: 6px;
    border: 1px solid #1e1e1e;
    font-weight: bold;
    color: #ffffff;
}

/* Dropdown list popup */
QListWidget {
    background-color: #1e1e1e;
    border: 2px solid #3b82f6;
    border-radius: 6px;
    color: #ffffff;
}

QListWidget::item {
    padding: 8px 12px;
    border-bottom: 1px solid #2d2d2d;
}

QListWidget::item:selected {
    background-color: #0d6efd;
    color: #ffffff;
}

QListWidget::item:hover {
    background-color: #2a2a2a;
}

/* Buttons */
QPushButton {
    background-color: #2d2d2d;
    border: 1px solid #3c3c3c;
    border-radius: 6px;
    padding: 8px 16px;
    color: #ffffff;
    font-weight: bold;
}

QPushButton:hover {
    background-color: #3d3d3d;
}

QPushButton:pressed {
    background-color: #1e1e1e;
}

QPushButton:focus {
    border: 2px solid #3b82f6;
}

/* Primary Action Buttons */
QPushButton#primary_btn {
    background-color: #0d6efd;
    border: 1px solid #0d6efd;
}

QPushButton#primary_btn:hover {
    background-color: #0b5ed7;
}

QPushButton#success_btn {
    background-color: #198754;
    border: 1px solid #198754;
}

QPushButton#success_btn:hover {
    background-color: #157347;
}

QPushButton#danger_btn {
    background-color: #dc3545;
    border: 1px solid #dc3545;
}

QPushButton#danger_btn:hover {
    background-color: #bb2d3b;
}

/* Tabs */
QTabWidget::pane {
    border: 1px solid #2d2d2d;
    background-color: #121212;
    top: -1px;
}

QTabBar::tab {
    background-color: #1e1e1e;
    border: 1px solid #2d2d2d;
    border-bottom-color: none;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    padding: 8px 16px;
    color: #9ca3af;
    font-weight: bold;
}

QTabBar::tab:selected, QTabBar::tab:hover {
    background-color: #121212;
    color: #ffffff;
    border-bottom: 2px solid #0d6efd;
}

/* Combobox */
QComboBox QAbstractItemView {
    background-color: #1e1e1e;
    selection-background-color: #0d6efd;
    color: #ffffff;
}
QComboBox QAbstractItemView::item {
    background-color: #1e1e1e;
    color: #ffffff;
}


QComboBox {
    background-color: #242424;
    border: 1.5px solid #3c3c3c;
    border-radius: 6px;
    padding: 6px 12px;
    color: #ffffff;
}
QComboBox:focus {
    border: 2px solid #3b82f6;
}

QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 25px;
    border-left-width: 0px;
    background: #242424;
}

/* Scrollbars */
QScrollBar:vertical {
    border: none;
    background: #1e1e1e;
    width: 10px;
    margin: 0px;
}

QScrollBar::handle:vertical {
    background: #3c3c3c;
    min-height: 20px;
    border-radius: 5px;
}

QScrollBar::handle:vertical:hover {
    background: #5c5c5c;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

/* QCalendarWidget Dark Mode Styling */
QCalendarWidget {
    background-color: #1e1e1e;
    border: 1.5px solid #2d2d2d;
    border-radius: 8px;
}
QCalendarWidget QWidget#qt_calendar_navigationbar {
    background-color: #242424;
    border-bottom: 1px solid #2d2d2d;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
}
QCalendarWidget QToolButton {
    background: transparent;
    color: #ffffff;
    border: none;
    border-radius: 4px;
    padding: 4px;
    font-weight: bold;
    font-size: 12px;
}
QCalendarWidget QToolButton:hover {
    background-color: #3c3c3c;
}
QCalendarWidget QToolButton:pressed {
    background-color: #1a1a1a;
}
QCalendarWidget QMenu {
    background-color: #1e1e1e;
    color: #ffffff;
    border: 1px solid #2d2d2d;
}
QCalendarWidget QMenu::item:selected {
    background-color: #0d6efd;
    color: #ffffff;
}
QCalendarWidget QSpinBox {
    background-color: #242424;
    color: #ffffff;
    border: 1px solid #3c3c3c;
    border-radius: 4px;
    padding: 2px;
}
QCalendarWidget QSpinBox::up-button, QCalendarWidget QSpinBox::down-button {
    subcontrol-origin: border;
    width: 16px;
}
QCalendarWidget QAbstractItemView:enabled {
    background-color: #1e1e1e;
    color: #e0e0e0;
    selection-background-color: #0d6efd;
    selection-color: #ffffff;
    border: none;
    outline: none;
}
QCalendarWidget QAbstractItemView:disabled {
    color: #5c5c5c;
}
QCalendarWidget QAbstractItemView:hover {
    background-color: #2a2a2a;
}
"""

LIGHT_QSS = """
QMainWindow {
    background-color: #f8f9fa;
}

QWidget {
    color: #212529;
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 13px;
}

QLabel {
    background: transparent;
}

/* Primary Header Card */
#HeaderCard {
    background-color: #ffffff;
    border-radius: 8px;
    padding: 10px;
    border: 1px solid #dee2e6;
}

/* Text Inputs / Edits */
QLineEdit, QTextEdit {
    background-color: #ffffff;
    border: 1.5px solid #ced4da;
    border-radius: 6px;
    padding: 6px 12px;
    color: #212529;
    selection-background-color: #0d6efd;
}

QLineEdit:focus, QTextEdit:focus {
    border: 2px solid #0d6efd;
    background-color: #ffffff;
}

QLabel#input_label {
    font-weight: bold;
    color: #495057;
    font-size: 11px;
}

/* Table Widget styling */
QTableWidget {
    background-color: #ffffff;
    alternate-background-color: #f8f9fa;
    border: 1px solid #dee2e6;
    gridline-color: #dee2e6;
    border-radius: 6px;
    color: #212529;
    selection-background-color: #0d6efd;
    selection-color: #ffffff;
}

QTableWidget::item {
    padding: 8px;
}

QHeaderView::section {
    background-color: #e9ecef;
    padding: 6px;
    border: 1px solid #dee2e6;
    font-weight: bold;
    color: #212529;
}

/* Dropdown list popup */
QListWidget {
    background-color: #ffffff;
    border: 2px solid #0d6efd;
    border-radius: 6px;
    color: #212529;
}

QListWidget::item {
    padding: 8px 12px;
    border-bottom: 1px solid #dee2e6;
}

QListWidget::item:selected {
    background-color: #0d6efd;
    color: #ffffff;
}

QListWidget::item:hover {
    background-color: #f1f3f5;
}

/* Buttons */
QPushButton {
    background-color: #e9ecef;
    border: 1px solid #ced4da;
    border-radius: 6px;
    padding: 8px 16px;
    color: #212529;
    font-weight: bold;
}

QPushButton:hover {
    background-color: #dee2e6;
}

QPushButton:pressed {
    background-color: #ced4da;
}

QPushButton:focus {
    border: 2px solid #0d6efd;
}

/* Primary Action Buttons */
QPushButton#primary_btn {
    background-color: #0d6efd;
    border: 1px solid #0d6efd;
    color: #ffffff;
}

QPushButton#primary_btn:hover {
    background-color: #0b5ed7;
}

QPushButton#success_btn {
    background-color: #198754;
    border: 1px solid #198754;
    color: #ffffff;
}

QPushButton#success_btn:hover {
    background-color: #157347;
}

QPushButton#danger_btn {
    background-color: #dc3545;
    border: 1px solid #dc3545;
    color: #ffffff;
}

QPushButton#danger_btn:hover {
    background-color: #bb2d3b;
}

/* Tabs */
QTabWidget::pane {
    border: 1px solid #dee2e6;
    background-color: #f8f9fa;
    top: -1px;
}

QTabBar::tab {
    background-color: #ffffff;
    border: 1px solid #dee2e6;
    border-bottom-color: none;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    padding: 8px 16px;
    color: #6c757d;
    font-weight: bold;
}

QTabBar::tab:selected, QTabBar::tab:hover {
    background-color: #f8f9fa;
    color: #212529;
    border-bottom: 2px solid #0d6efd;
}

/* Combobox */
QComboBox {
    background-color: #ffffff;
    border: 1.5px solid #ced4da;
    border-radius: 6px;
    padding: 6px 12px;
    color: #212529;
}

QComboBox:focus {
    border: 2px solid #0d6efd;
}

/* Scrollbars */
QScrollBar:vertical {
    border: none;
    background: #f8f9fa;
    width: 10px;
    margin: 0px;
}

QScrollBar::handle:vertical {
    background: #ced4da;
    min-height: 20px;
    border-radius: 5px;
}

QScrollBar::handle:vertical:hover {
    background: #adb5bd;
}

/* QCalendarWidget Light Mode Styling */
QCalendarWidget {
    background-color: #ffffff;
    border: 1.5px solid #dee2e6;
    border-radius: 8px;
}
QCalendarWidget QWidget#qt_calendar_navigationbar {
    background-color: #f1f3f5;
    border-bottom: 1px solid #dee2e6;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
}
QCalendarWidget QToolButton {
    background: transparent;
    color: #212529;
    border: none;
    border-radius: 4px;
    padding: 4px;
    font-weight: bold;
    font-size: 12px;
}
QCalendarWidget QToolButton:hover {
    background-color: #e9ecef;
}
QCalendarWidget QMenu {
    background-color: #ffffff;
    color: #212529;
    border: 1px solid #dee2e6;
}
QCalendarWidget QMenu::item:selected {
    background-color: #0d6efd;
    color: #ffffff;
}
QCalendarWidget QSpinBox {
    background-color: #ffffff;
    color: #212529;
    border: 1px solid #ced4da;
    border-radius: 4px;
    padding: 2px;
}
QCalendarWidget QAbstractItemView:enabled {
    background-color: #ffffff;
    color: #212529;
    selection-background-color: #0d6efd;
    selection-color: #ffffff;
    border: none;
    outline: none;
}
QCalendarWidget QAbstractItemView:disabled {
    color: #adb5bd;
}
"""
