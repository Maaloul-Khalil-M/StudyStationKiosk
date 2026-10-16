"""Kiosk security dialogs and screen lock overlay for Study Station."""

from __future__ import annotations
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QKeyEvent
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from study_station.core.security import hash_password, verify_password
from study_station.ui.theme import (
    BUTTON_PRIMARY_STYLE,
    BUTTON_SECONDARY_STYLE,
    get_modern_font,
)


class KioskUnlockDialog(QDialog):
    """Modern modal dialog prompting for kiosk administrator password."""

    def __init__(
        self,
        expected_hash: str,
        action_title: str = "Kiosk Exit Protection",
        action_desc: str = "Enter the kiosk password to proceed.",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._expected_hash = expected_hash
        self.setWindowTitle(action_title)
        self.setFixedSize(400, 240)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self._init_ui(action_title, action_desc)

    def _init_ui(self, title_text: str, desc_text: str) -> None:
        container = QFrame(self)
        container.setObjectName("kioskDialogContainer")
        container.setStyleSheet("""
            QFrame#kioskDialogContainer {
                background-color: #111115;
                border: 1px solid #24242C;
                border-radius: 14px;
            }
            QLabel {
                color: #F4F4F5;
            }
            QLineEdit {
                background-color: #16161B;
                color: #FFFFFF;
                border: 1px solid #282832;
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 1.5px solid #10B981;
                background-color: #1A1A22;
            }
        """)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(6, 6, 6, 6)
        main_layout.addWidget(container)

        layout = QVBoxLayout(container)
        layout.setContentsMargins(22, 18, 22, 18)
        layout.setSpacing(12)

        # Header with close button
        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)

        lbl_icon = QLabel("🔒")
        lbl_icon.setFont(get_modern_font("sans", 16))
        header_layout.addWidget(lbl_icon)

        title = QLabel(title_text)
        title.setFont(get_modern_font("sans", 14, QFont.Weight.Bold))
        header_layout.addWidget(title)
        header_layout.addStretch()

        btn_close = QPushButton("✕")
        btn_close.setFixedSize(24, 24)
        btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_close.setStyleSheet("""
            QPushButton {
                background-color: #1C1C1F;
                color: #A1A1AA;
                font-size: 12px;
                border-radius: 12px;
                border: 1px solid #27272A;
            }
            QPushButton:hover {
                background-color: #27272A;
                color: #FFFFFF;
            }
        """)
        btn_close.clicked.connect(self.reject)
        header_layout.addWidget(btn_close)
        layout.addLayout(header_layout)

        # Description
        lbl_desc = QLabel(desc_text)
        lbl_desc.setFont(get_modern_font("sans", 11))
        lbl_desc.setStyleSheet("color: #A1A1AA;")
        lbl_desc.setWordWrap(True)
        layout.addWidget(lbl_desc)

        # Password Input Row with reveal toggle
        input_row = QHBoxLayout()
        input_row.setSpacing(6)

        self.input_password = QLineEdit()
        self.input_password.setPlaceholderText("Enter password...")
        self.input_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.input_password.returnPressed.connect(self._on_unlock_clicked)
        input_row.addWidget(self.input_password, stretch=1)

        self.btn_toggle_echo = QPushButton("👁")
        self.btn_toggle_echo.setFixedSize(36, 36)
        self.btn_toggle_echo.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_toggle_echo.setToolTip("Show / Hide password")
        self.btn_toggle_echo.setStyleSheet("""
            QPushButton {
                background-color: #16161B;
                color: #71717A;
                border: 1px solid #282832;
                border-radius: 8px;
                font-size: 14px;
            }
            QPushButton:hover {
                color: #FFFFFF;
                border-color: #3F3F4E;
            }
        """)
        self.btn_toggle_echo.clicked.connect(self._toggle_echo_mode)
        input_row.addWidget(self.btn_toggle_echo)
        layout.addLayout(input_row)

        # Error label
        self.lbl_error = QLabel("")
        self.lbl_error.setFont(get_modern_font("sans", 10, QFont.Weight.Medium))
        self.lbl_error.setStyleSheet("color: #EF4444; margin-top: -4px;")
        self.lbl_error.hide()
        layout.addWidget(self.lbl_error)

        layout.addStretch()

        # Action Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        btn_layout.addStretch()

        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.setFixedSize(90, 32)
        self.btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_cancel.setStyleSheet(BUTTON_SECONDARY_STYLE)
        self.btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(self.btn_cancel)

        self.btn_unlock = QPushButton("Unlock")
        self.btn_unlock.setFixedSize(100, 32)
        self.btn_unlock.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_unlock.setStyleSheet(BUTTON_PRIMARY_STYLE)
        self.btn_unlock.clicked.connect(self._on_unlock_clicked)
        btn_layout.addWidget(self.btn_unlock)

        layout.addLayout(btn_layout)

    def showEvent(self, event) -> None:
        super().showEvent(event)
        self.input_password.setFocus()

    def _toggle_echo_mode(self) -> None:
        if self.input_password.echoMode() == QLineEdit.EchoMode.Password:
            self.input_password.setEchoMode(QLineEdit.EchoMode.Normal)
            self.btn_toggle_echo.setStyleSheet("""
                QPushButton {
                    background-color: #202028;
                    color: #10B981;
                    border: 1px solid #10B981;
                    border-radius: 8px;
                    font-size: 14px;
                }
            """)
        else:
            self.input_password.setEchoMode(QLineEdit.EchoMode.Password)
            self.btn_toggle_echo.setStyleSheet("""
                QPushButton {
                    background-color: #16161B;
                    color: #71717A;
                    border: 1px solid #282832;
                    border-radius: 8px;
                    font-size: 14px;
                }
                QPushButton:hover {
                    color: #FFFFFF;
                    border-color: #3F3F4E;
                }
            """)

    def _on_unlock_clicked(self) -> None:
        entered = self.input_password.text()
        if verify_password(self._expected_hash, entered):
            self.lbl_error.hide()
            self.accept()
        else:
            self.lbl_error.setText("Incorrect password. Access denied.")
            self.lbl_error.show()
            self.input_password.selectAll()
            self.input_password.setFocus()
            self.input_password.setStyleSheet("""
                QLineEdit {
                    background-color: #1F1416;
                    color: #FFFFFF;
                    border: 1.5px solid #EF4444;
                    border-radius: 8px;
                    padding: 8px 12px;
                    font-size: 14px;
                }
            """)


class SetKioskPasswordDialog(QDialog):
    """Dialog allowing user to configure or change the kiosk administrator password."""

    def __init__(self, current_hash: str = "", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._current_hash = current_hash
        self.new_password_hash: str = ""

        is_changing = bool(current_hash)
        self.setWindowTitle("Change Kiosk Password" if is_changing else "Set Kiosk Password")
        height = 340 if is_changing else 290
        self.setFixedSize(420, height)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self._init_ui(is_changing)

    def _init_ui(self, is_changing: bool) -> None:
        container = QFrame(self)
        container.setObjectName("setKioskContainer")
        container.setStyleSheet("""
            QFrame#setKioskContainer {
                background-color: #111115;
                border: 1px solid #24242C;
                border-radius: 14px;
            }
            QLabel {
                color: #F4F4F5;
            }
            QLineEdit {
                background-color: #16161B;
                color: #FFFFFF;
                border: 1px solid #282832;
                border-radius: 8px;
                padding: 7px 12px;
                font-size: 13px;
            }
            QLineEdit:focus {
                border: 1.5px solid #10B981;
                background-color: #1A1A22;
            }
        """)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(6, 6, 6, 6)
        main_layout.addWidget(container)

        layout = QVBoxLayout(container)
        layout.setContentsMargins(22, 18, 22, 18)
        layout.setSpacing(10)

        # Header
        header_layout = QHBoxLayout()
        title_text = "Change Kiosk Password" if is_changing else "Set Kiosk Password"
        title = QLabel(f"🔒 {title_text}")
        title.setFont(get_modern_font("sans", 14, QFont.Weight.Bold))
        header_layout.addWidget(title)
        header_layout.addStretch()

        btn_close = QPushButton("✕")
        btn_close.setFixedSize(24, 24)
        btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_close.setStyleSheet("""
            QPushButton {
                background-color: #1C1C1F;
                color: #A1A1AA;
                font-size: 12px;
                border-radius: 12px;
                border: 1px solid #27272A;
            }
            QPushButton:hover {
                background-color: #27272A;
                color: #FFFFFF;
            }
        """)
        btn_close.clicked.connect(self.reject)
        header_layout.addWidget(btn_close)
        layout.addLayout(header_layout)

        subtitle = QLabel("Require this password to exit fullscreen or close the application.")
        subtitle.setFont(get_modern_font("sans", 11))
        subtitle.setStyleSheet("color: #A1A1AA;")
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)

        # Current password field if changing
        if is_changing:
            lbl_cur = QLabel("Current Password")
            lbl_cur.setFont(get_modern_font("sans", 10, QFont.Weight.DemiBold))
            lbl_cur.setStyleSheet("color: #71717A;")
            layout.addWidget(lbl_cur)

            self.input_current = QLineEdit()
            self.input_current.setPlaceholderText("Enter current password")
            self.input_current.setEchoMode(QLineEdit.EchoMode.Password)
            layout.addWidget(self.input_current)
        else:
            self.input_current = None

        # New password
        lbl_new = QLabel("New Password")
        lbl_new.setFont(get_modern_font("sans", 10, QFont.Weight.DemiBold))
        lbl_new.setStyleSheet("color: #71717A;")
        layout.addWidget(lbl_new)

        self.input_new = QLineEdit()
        self.input_new.setPlaceholderText("Enter new password")
        self.input_new.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.input_new)

        # Confirm password
        lbl_confirm = QLabel("Confirm Password")
        lbl_confirm.setFont(get_modern_font("sans", 10, QFont.Weight.DemiBold))
        lbl_confirm.setStyleSheet("color: #71717A;")
        layout.addWidget(lbl_confirm)

        self.input_confirm = QLineEdit()
        self.input_confirm.setPlaceholderText("Re-enter new password")
        self.input_confirm.setEchoMode(QLineEdit.EchoMode.Password)
        self.input_confirm.returnPressed.connect(self._on_save_clicked)
        layout.addWidget(self.input_confirm)

        # Error label
        self.lbl_error = QLabel("")
        self.lbl_error.setFont(get_modern_font("sans", 10, QFont.Weight.Medium))
        self.lbl_error.setStyleSheet("color: #EF4444;")
        self.lbl_error.hide()
        layout.addWidget(self.lbl_error)

        layout.addStretch()

        # Action buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        btn_layout.addStretch()

        btn_cancel = QPushButton("Cancel")
        btn_cancel.setFixedSize(90, 32)
        btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_cancel.setStyleSheet(BUTTON_SECONDARY_STYLE)
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_cancel)

        btn_save = QPushButton("Save Password")
        btn_save.setFixedSize(130, 32)
        btn_save.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_save.setStyleSheet(BUTTON_PRIMARY_STYLE)
        btn_save.clicked.connect(self._on_save_clicked)
        btn_layout.addWidget(btn_save)

        layout.addLayout(btn_layout)

    def showEvent(self, event) -> None:
        super().showEvent(event)
        if self.input_current:
            self.input_current.setFocus()
        else:
            self.input_new.setFocus()

    def _on_save_clicked(self) -> None:
        if self.input_current is not None:
            cur_text = self.input_current.text()
            if not verify_password(self._current_hash, cur_text):
                self.lbl_error.setText("Current password is incorrect.")
                self.lbl_error.show()
                self.input_current.selectAll()
                self.input_current.setFocus()
                return

        new_text = self.input_new.text()
        if not new_text or not new_text.strip():
            self.lbl_error.setText("Password cannot be blank.")
            self.lbl_error.show()
            self.input_new.setFocus()
            return

        confirm_text = self.input_confirm.text()
        if new_text != confirm_text:
            self.lbl_error.setText("Passwords do not match.")
            self.lbl_error.show()
            self.input_confirm.selectAll()
            self.input_confirm.setFocus()
            return

        self.new_password_hash = hash_password(new_text)
        self.lbl_error.hide()
        self.accept()


class KioskLockOverlay(QFrame):
    """Full-screen lock overlay covering the entire window until unlocked."""

    unlocked = Signal()

    def __init__(self, expected_hash_getter, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._expected_hash_getter = expected_hash_getter
        self.setObjectName("kioskLockOverlay")
        self.setStyleSheet("""
            QFrame#kioskLockOverlay {
                background-color: rgba(9, 9, 11, 0.98);
                border: none;
            }
        """)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        self._init_ui()

    def _init_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        card = QFrame(self)
        card.setFixedSize(380, 290)
        card.setStyleSheet("""
            QFrame {
                background-color: #111115;
                border: 1px solid #24242C;
                border-radius: 16px;
            }
            QLabel {
                color: #F4F4F5;
            }
            QLineEdit {
                background-color: #16161B;
                color: #FFFFFF;
                border: 1px solid #282832;
                border-radius: 8px;
                padding: 10px 14px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 1.5px solid #10B981;
                background-color: #1A1A22;
            }
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(28, 28, 28, 28)
        card_layout.setSpacing(14)
        card_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        lbl_icon = QLabel("🔒")
        lbl_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_icon.setStyleSheet("font-size: 32px; border: none; background: transparent;")
        card_layout.addWidget(lbl_icon)

        lbl_title = QLabel("STATION LOCKED")
        lbl_title.setFont(get_modern_font("sans", 15, QFont.Weight.Bold))
        lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_title.setStyleSheet("letter-spacing: 2px; color: #FFFFFF; border: none; background: transparent;")
        card_layout.addWidget(lbl_title)

        lbl_sub = QLabel("Enter password to resume Study Station")
        lbl_sub.setFont(get_modern_font("sans", 11))
        lbl_sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_sub.setStyleSheet("color: #71717A; border: none; background: transparent;")
        card_layout.addWidget(lbl_sub)

        self.input_pwd = QLineEdit(card)
        self.input_pwd.setPlaceholderText("Enter password...")
        self.input_pwd.setEchoMode(QLineEdit.EchoMode.Password)
        self.input_pwd.returnPressed.connect(self._on_unlock)
        card_layout.addWidget(self.input_pwd)

        self.lbl_err = QLabel("", card)
        self.lbl_err.setFont(get_modern_font("sans", 10))
        self.lbl_err.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_err.setStyleSheet("color: #EF4444; border: none; background: transparent;")
        self.lbl_err.hide()
        card_layout.addWidget(self.lbl_err)

        btn_unlock = QPushButton("Unlock Station", card)
        btn_unlock.setFixedSize(160, 36)
        btn_unlock.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_unlock.setStyleSheet(BUTTON_PRIMARY_STYLE)
        btn_unlock.clicked.connect(self._on_unlock)
        card_layout.addWidget(btn_unlock, alignment=Qt.AlignmentFlag.AlignCenter)

        main_layout.addWidget(card)

    def show_lock(self) -> None:
        """Display the lock overlay and focus the input."""
        self.input_pwd.clear()
        self.lbl_err.hide()
        if self.parentWidget():
            self.setGeometry(self.parentWidget().rect())
        self.raise_()
        self.show()
        self.input_pwd.setFocus()

    def _on_unlock(self) -> None:
        expected = self._expected_hash_getter()
        entered = self.input_pwd.text()
        if verify_password(expected, entered):
            self.lbl_err.hide()
            self.input_pwd.clear()
            self.hide()
            self.unlocked.emit()
        else:
            self.lbl_err.setText("Incorrect password.")
            self.lbl_err.show()
            self.input_pwd.selectAll()
            self.input_pwd.setFocus()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        """Trap all key events so user cannot bypass overlay with Esc or Tab."""
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self._on_unlock()
        else:
            super().keyPressEvent(event)
