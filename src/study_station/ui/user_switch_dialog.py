"""Dialog allowing instant switching between user profiles and databases."""

from __future__ import annotations
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from study_station.persistence.user_manager import UserManager
from study_station.ui.theme import (
    BUTTON_DANGER_STYLE,
    BUTTON_NAV_STYLE,
    BUTTON_PRIMARY_STYLE,
    BUTTON_SECONDARY_STYLE,
    get_modern_font,
)


class UserProfileCard(QFrame):
    """Clickable card representing a user profile."""

    clicked_switch = Signal(str)
    clicked_delete = Signal(str)

    def __init__(
        self,
        username: str,
        is_active: bool,
        can_delete: bool = True,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.username = username
        self.is_active = is_active
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        border_color = "#059669" if is_active else "#27272A"
        bg_color = "#14221D" if is_active else "#16161A"

        self.setStyleSheet(f"""
            UserProfileCard {{
                background-color: {bg_color};
                border: 1px solid {border_color};
                border-radius: 10px;
                padding: 10px 14px;
            }}
            UserProfileCard:hover {{
                border-color: #38BDF8;
                background-color: #1C1C22;
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(12)

        # Avatar glyph
        lbl_avatar = QLabel("👤")
        lbl_avatar.setStyleSheet("font-size: 18px; color: #38BDF8;")
        layout.addWidget(lbl_avatar)

        # Username
        lbl_name = QLabel(username)
        lbl_name.setFont(get_modern_font("sans", 13, weight=QFont.Weight.Bold))
        lbl_name.setStyleSheet("color: #FFFFFF; font-size: 14px; font-weight: 700;")
        layout.addWidget(lbl_name, stretch=1)

        # Status badge or switch button
        if is_active:
            lbl_badge = QLabel("● ACTIVE")
            lbl_badge.setStyleSheet("""
                background-color: #064E3B;
                color: #34D399;
                border: 1px solid #059669;
                border-radius: 10px;
                font-size: 10px;
                font-weight: 700;
                padding: 3px 10px;
            """)
            layout.addWidget(lbl_badge)
        else:
            btn_switch = QPushButton("Switch")
            btn_switch.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_switch.setStyleSheet(BUTTON_SECONDARY_STYLE)
            btn_switch.setFixedHeight(28)
            btn_switch.clicked.connect(lambda: self.clicked_switch.emit(self.username))
            layout.addWidget(btn_switch)

        if can_delete and not is_active:
            btn_delete = QPushButton("✕")
            btn_delete.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_delete.setFixedSize(26, 26)
            btn_delete.setStyleSheet("""
                QPushButton {
                    background-color: #27272A;
                    color: #71717A;
                    border: 1px solid #3F3F46;
                    border-radius: 13px;
                    font-size: 11px;
                    font-weight: 700;
                }
                QPushButton:hover {
                    background-color: #451A1A;
                    color: #F87171;
                    border-color: #991B1B;
                }
            """)
            btn_delete.setToolTip("Delete this user profile and database")
            btn_delete.clicked.connect(lambda: self.clicked_delete.emit(self.username))
            layout.addWidget(btn_delete)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton and not self.is_active:
            self.clicked_switch.emit(self.username)
        super().mousePressEvent(event)


class UserSwitchDialog(QDialog):
    """Frictionless kiosk modal for switching or creating user profiles."""

    user_switched = Signal(str)  # Emits chosen username

    def __init__(
        self,
        user_manager: UserManager | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.user_manager = user_manager or UserManager()
        self.selected_user: str | None = None

        self.setWindowTitle("Switch User")
        self.setFixedSize(540, 500)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self._build_ui()
        self._refresh_users_list()

    def _build_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)

        container = QFrame(self)
        container.setObjectName("dialogContainer")
        container.setStyleSheet("""
            QFrame#dialogContainer {
                background-color: #111115;
                border: 1px solid #24242C;
                border-radius: 14px;
            }
        """)
        main_layout.addWidget(container)

        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(24, 20, 24, 20)
        container_layout.setSpacing(14)

        # Header Title
        header_col = QVBoxLayout()
        header_col.setSpacing(3)
        lbl_title = QLabel("SWITCH USER")
        lbl_title.setStyleSheet("color: #FFFFFF; font-size: 15px; font-weight: 800; letter-spacing: 1.5px;")
        header_col.addWidget(lbl_title)

        lbl_desc = QLabel("Select a profile or add a new user. Each user has their own separate timetable & tasks.")
        lbl_desc.setStyleSheet("color: #71717A; font-size: 11px;")
        lbl_desc.setWordWrap(True)
        header_col.addWidget(lbl_desc)
        container_layout.addLayout(header_col)

        # Scroll Area for Profiles
        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("""
            QScrollArea {
                background: transparent;
                border: none;
            }
            QWidget#scrollContent {
                background: transparent;
            }
        """)

        self.scroll_content = QWidget()
        self.scroll_content.setObjectName("scrollContent")
        self.cards_layout = QVBoxLayout(self.scroll_content)
        self.cards_layout.setContentsMargins(0, 4, 0, 4)
        self.cards_layout.setSpacing(8)
        self.cards_layout.addStretch()

        scroll_area.setWidget(self.scroll_content)
        container_layout.addWidget(scroll_area, stretch=1)

        # Add New User Bar
        new_user_box = QFrame()
        new_user_box.setStyleSheet("""
            QFrame {
                background-color: #16161C;
                border: 1px solid #272730;
                border-radius: 10px;
                padding: 4px;
            }
        """)
        new_user_layout = QHBoxLayout(new_user_box)
        new_user_layout.setContentsMargins(8, 6, 8, 6)
        new_user_layout.setSpacing(8)

        self.txt_username = QLineEdit()
        self.txt_username.setPlaceholderText("Enter new user name (e.g. Alice)...")
        self.txt_username.setStyleSheet("""
            QLineEdit {
                background-color: #0E0E12;
                border: 1px solid #27272A;
                border-radius: 8px;
                color: #FFFFFF;
                font-size: 12px;
                padding: 6px 10px;
            }
            QLineEdit:focus {
                border-color: #38BDF8;
            }
        """)
        self.txt_username.returnPressed.connect(self._on_create_user_clicked)
        new_user_layout.addWidget(self.txt_username, stretch=1)

        btn_create = QPushButton("+ Create && Switch")
        btn_create.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_create.setStyleSheet(BUTTON_PRIMARY_STYLE)
        btn_create.setFixedHeight(32)
        btn_create.clicked.connect(self._on_create_user_clicked)
        new_user_layout.addWidget(btn_create)

        container_layout.addWidget(new_user_box)

        # Footer Actions
        footer = QHBoxLayout()
        footer.setContentsMargins(0, 4, 0, 0)
        footer.addStretch()

        btn_close = QPushButton("Close")
        btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_close.setStyleSheet(BUTTON_NAV_STYLE)
        btn_close.clicked.connect(self.reject)
        footer.addWidget(btn_close)

        container_layout.addLayout(footer)

    def _refresh_users_list(self) -> None:
        """Clear and rebuild user cards."""
        # Clear existing card widgets
        while self.cards_layout.count() > 1:
            item = self.cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        users = self.user_manager.list_users()
        active_user = self.user_manager.get_active_user()

        for user in users:
            is_active = (user == active_user)
            can_delete = len(users) > 1 and not is_active
            card = UserProfileCard(
                username=user,
                is_active=is_active,
                can_delete=can_delete,
                parent=self.scroll_content,
            )
            card.clicked_switch.connect(self._on_switch_user)
            card.clicked_delete.connect(self._on_delete_user)
            self.cards_layout.insertWidget(self.cards_layout.count() - 1, card)

    def _on_switch_user(self, username: str) -> None:
        """Switch active user profile."""
        if self.user_manager.set_active_user(username):
            self.selected_user = username
            self.user_switched.emit(username)
            self.accept()

    def _on_create_user_clicked(self) -> None:
        """Create new profile and switch immediately."""
        raw_name = self.txt_username.text().strip()
        if not raw_name:
            return

        safe_name, _ = self.user_manager.create_user(raw_name)
        self.user_manager.set_active_user(safe_name)
        self.selected_user = safe_name
        self.user_switched.emit(safe_name)
        self.accept()

    def _on_delete_user(self, username: str) -> None:
        """Confirm and delete a non-active user profile."""
        reply = QMessageBox.question(
            self,
            "Delete User",
            f"Are you sure you want to delete profile '{username}' and all its data?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.user_manager.delete_user(username, delete_db_file=True)
            self._refresh_users_list()
