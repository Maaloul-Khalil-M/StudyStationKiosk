"""Cognitive Exit Ticket Dialog for Study Station (Milestone 13).

Provides a focused 60-second debrief upon focus timer completion or exit:
1. Completion prompt: [ Complete Task ] vs [ +10m Need More Time ] vs [ Put Aside ].
2. Cognitive confidence rating: 🔴 Foggy / Stuck, 🟡 Getting There, 🟢 Solid.
3. Next Class Question formulation: Captures 1 question to pin to next week's lecture card.
4. 1-sentence Feynman takeaway summary.
"""

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

from study_station.core.engine import ScheduleEngine
from study_station.core.models import ExitTicketResult, StudyTodo
from study_station.ui.theme import (
    BUTTON_NAV_STYLE,
    BUTTON_PRIMARY_STYLE,
    get_modern_font,
)


class ExitTicketDialog(QDialog):
    """Cognitive Exit Ticket modal triggered after a focus sprint."""

    ticket_submitted = Signal(object)  # ExitTicketResult

    def __init__(
        self,
        subject_name: str,
        elapsed_minutes: int,
        todo: StudyTodo | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.subject_name = ScheduleEngine.clean_subject_name(subject_name)
        self.elapsed_minutes = elapsed_minutes
        self.todo = todo

        self.selected_action = "complete"
        self.selected_confidence = getattr(todo, "confidence", None) or "solid"

        self.setFixedSize(680, 580)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self._build_ui()

    def _build_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)

        self.container = QFrame(self)
        self.container.setObjectName("exitTicketContainer")
        self.container.setStyleSheet("""
            QFrame#exitTicketContainer {
                background-color: #121216;
                border: 1px solid #27272A;
                border-radius: 14px;
            }
        """)
        main_layout.addWidget(self.container)

        content = QVBoxLayout(self.container)
        content.setContentsMargins(28, 24, 28, 24)
        content.setSpacing(16)

        # ---------------------------------------------------------------------
        # 1. Header: Session Time & Task Context
        # ---------------------------------------------------------------------
        header_row = QHBoxLayout()
        header_row.setContentsMargins(0, 0, 0, 0)

        header_text = QVBoxLayout()
        header_text.setSpacing(2)

        lbl_top = QLabel(f"SESSION COMPLETE (+{self.elapsed_minutes} MIN)")
        lbl_top.setFont(get_modern_font("mono", 11, QFont.Weight.Bold))
        lbl_top.setStyleSheet("color: #10B981; letter-spacing: 1.5px;")
        header_text.addWidget(lbl_top)

        if self.todo:
            lbl_title = QLabel(f"Task: {self.todo.title}")
            lbl_title.setStyleSheet("color: #FFFFFF; font-size: 16px; font-weight: 700;")
            lbl_title.setWordWrap(True)
            header_text.addWidget(lbl_title)

            lbl_sub = QLabel(f"Subject: {self.subject_name.upper()}")
            lbl_sub.setStyleSheet("color: #71717A; font-size: 11px; font-weight: 600;")
            header_text.addWidget(lbl_sub)
        else:
            lbl_title = QLabel(self.subject_name.upper())
            lbl_title.setStyleSheet("color: #FFFFFF; font-size: 18px; font-weight: 800;")
            header_text.addWidget(lbl_title)

        header_row.addLayout(header_text, stretch=1)
        content.addLayout(header_row)

        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setStyleSheet("color: #27272A; background-color: #27272A; max-height: 1px;")
        content.addWidget(divider)

        # ---------------------------------------------------------------------
        # 2. Action Question: Did you complete this task?
        # ---------------------------------------------------------------------
        sec1 = QVBoxLayout()
        sec1.setSpacing(8)

        lbl_q1 = QLabel("1. Did you complete this task?")
        lbl_q1.setStyleSheet("color: #F4F4F6; font-size: 13px; font-weight: 700;")
        sec1.addWidget(lbl_q1)

        row_actions = QHBoxLayout()
        row_actions.setSpacing(10)

        self.btn_act_complete = QPushButton("✓ Complete Task" if self.todo else "✓ Wrap Up Session")
        self.btn_act_complete.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_act_complete.setFixedHeight(36)
        self.btn_act_complete.clicked.connect(lambda: self._set_action("complete"))
        row_actions.addWidget(self.btn_act_complete)

        self.btn_act_extend = QPushButton("+10m Need More Time")
        self.btn_act_extend.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_act_extend.setFixedHeight(36)
        self.btn_act_extend.clicked.connect(lambda: self._set_action("extend"))
        row_actions.addWidget(self.btn_act_extend)

        self.btn_act_aside = QPushButton("⏸ Put Aside for Later")
        self.btn_act_aside.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_act_aside.setFixedHeight(36)
        self.btn_act_aside.clicked.connect(lambda: self._set_action("put_aside"))
        row_actions.addWidget(self.btn_act_aside)

        sec1.addLayout(row_actions)
        content.addLayout(sec1)

        # ---------------------------------------------------------------------
        # 3. Confidence Rating: Traffic Light (🔴 Foggy / 🟡 Getting There / 🟢 Solid)
        # ---------------------------------------------------------------------
        sec2 = QVBoxLayout()
        sec2.setSpacing(8)

        lbl_q2 = QLabel("2. How confident do you feel about this material?")
        lbl_q2.setStyleSheet("color: #F4F4F6; font-size: 13px; font-weight: 700;")
        sec2.addWidget(lbl_q2)

        row_conf = QHBoxLayout()
        row_conf.setSpacing(10)

        self.btn_conf_foggy = QPushButton("🔴 Foggy / Stuck")
        self.btn_conf_foggy.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_conf_foggy.setFixedHeight(36)
        self.btn_conf_foggy.clicked.connect(lambda: self._set_confidence("foggy"))
        row_conf.addWidget(self.btn_conf_foggy)

        self.btn_conf_prog = QPushButton("🟡 Getting There")
        self.btn_conf_prog.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_conf_prog.setFixedHeight(36)
        self.btn_conf_prog.clicked.connect(lambda: self._set_confidence("progressing"))
        row_conf.addWidget(self.btn_conf_prog)

        self.btn_conf_solid = QPushButton("🟢 Solid")
        self.btn_conf_solid.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_conf_solid.setFixedHeight(36)
        self.btn_conf_solid.clicked.connect(lambda: self._set_confidence("solid"))
        row_conf.addWidget(self.btn_conf_solid)

        sec2.addLayout(row_conf)
        content.addLayout(sec2)

        # ---------------------------------------------------------------------
        # 4. In-Class Question Formulation
        # ---------------------------------------------------------------------
        sec3 = QVBoxLayout()
        sec3.setSpacing(4)

        lbl_q3 = QLabel("3. Formulate 1 Question for Next Class (Optional):")
        lbl_q3.setStyleSheet("color: #F4F4F6; font-size: 13px; font-weight: 700;")
        sec3.addWidget(lbl_q3)

        lbl_q3_hint = QLabel("What made you pause? Pinned to next week's card so you can ask the professor.")
        lbl_q3_hint.setStyleSheet("color: #71717A; font-size: 11px;")
        sec3.addWidget(lbl_q3_hint)

        self.txt_question = QLineEdit()
        self.txt_question.setPlaceholderText("e.g. Why does Kerberos require synchronized system clocks within 5 min?")
        self.txt_question.setStyleSheet("""
            QLineEdit {
                background-color: #18181B;
                color: #FFFFFF;
                border: 1px solid #27272A;
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 12px;
            }
            QLineEdit:focus {
                border-color: #10B981;
            }
        """)
        if self.todo and self.todo.next_class_question:
            self.txt_question.setText(self.todo.next_class_question)
        sec3.addWidget(self.txt_question)
        content.addLayout(sec3)

        # ---------------------------------------------------------------------
        # 5. 1-Sentence Feynman Takeaway
        # ---------------------------------------------------------------------
        sec4 = QVBoxLayout()
        sec4.setSpacing(4)

        lbl_q4 = QLabel("4. 1-Sentence Takeaway / Note (Optional):")
        lbl_q4.setStyleSheet("color: #F4F4F6; font-size: 13px; font-weight: 700;")
        sec4.addWidget(lbl_q4)

        self.txt_takeaway = QLineEdit()
        self.txt_takeaway.setPlaceholderText("e.g. Star schema joins are faster because dimensions are denormalized.")
        self.txt_takeaway.setStyleSheet("""
            QLineEdit {
                background-color: #18181B;
                color: #FFFFFF;
                border: 1px solid #27272A;
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 12px;
            }
            QLineEdit:focus {
                border-color: #10B981;
            }
        """)
        self.txt_takeaway.returnPressed.connect(self._on_save_clicked)
        sec4.addWidget(self.txt_takeaway)
        content.addLayout(sec4)

        content.addStretch()

        # ---------------------------------------------------------------------
        # 6. Bottom Actions: Skip vs Done & Save
        # ---------------------------------------------------------------------
        bottom_row = QHBoxLayout()
        bottom_row.setContentsMargins(0, 0, 0, 0)
        bottom_row.setSpacing(10)

        btn_skip = QPushButton("Skip Debrief")
        btn_skip.setStyleSheet(BUTTON_NAV_STYLE)
        btn_skip.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_skip.clicked.connect(self.reject)
        bottom_row.addWidget(btn_skip)

        bottom_row.addStretch()

        self.btn_save = QPushButton("Done && Save")
        self.btn_save.setStyleSheet(BUTTON_PRIMARY_STYLE)
        self.btn_save.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_save.setFixedHeight(36)
        self.btn_save.clicked.connect(self._on_save_clicked)
        bottom_row.addWidget(self.btn_save)

        content.addLayout(bottom_row)

        # Apply initial visual selection
        self._update_action_styles()
        self._update_confidence_styles()

    def showEvent(self, event) -> None:
        super().showEvent(event)
        if self.parent():
            parent_rect = self.parent().rect()
            self.move(parent_rect.center() - self.rect().center())

    def _set_action(self, action: str) -> None:
        self.selected_action = action
        self._update_action_styles()

    def _update_action_styles(self) -> None:
        style_default = """
            QPushButton {
                background-color: #16161D;
                color: #D4D4D8;
                border: 1px solid #2B2B36;
                border-radius: 8px;
                font-size: 12px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #22222C;
                border-color: #3F3F50;
                color: #FFFFFF;
            }
        """

        style_complete = """
            QPushButton {
                background-color: #064E3B;
                color: #6EE7B7;
                border: 1.5px solid #10B981;
                border-radius: 8px;
                font-size: 12px;
                font-weight: 700;
            }
        """

        style_extend = """
            QPushButton {
                background-color: #082F49;
                color: #7DD3FC;
                border: 1.5px solid #38BDF8;
                border-radius: 8px;
                font-size: 12px;
                font-weight: 700;
            }
        """

        style_aside = """
            QPushButton {
                background-color: #38240D;
                color: #FDE047;
                border: 1.5px solid #F59E0B;
                border-radius: 8px;
                font-size: 12px;
                font-weight: 700;
            }
        """

        self.btn_act_complete.setStyleSheet(style_complete if self.selected_action == "complete" else style_default)
        self.btn_act_extend.setStyleSheet(style_extend if self.selected_action == "extend" else style_default)
        self.btn_act_aside.setStyleSheet(style_aside if self.selected_action == "put_aside" else style_default)

    def _set_confidence(self, conf: str) -> None:
        self.selected_confidence = conf
        self._update_confidence_styles()

    def _update_confidence_styles(self) -> None:
        style_default = """
            QPushButton {
                background-color: #16161D;
                color: #D4D4D8;
                border: 1px solid #2B2B36;
                border-radius: 8px;
                font-size: 12px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #22222C;
                border-color: #3F3F50;
                color: #FFFFFF;
            }
        """

        style_foggy = """
            QPushButton {
                background-color: #451A1A;
                color: #FCA5A5;
                border: 1.5px solid #EF4444;
                border-radius: 8px;
                font-size: 12px;
                font-weight: 700;
            }
        """

        style_prog = """
            QPushButton {
                background-color: #451A03;
                color: #FDE047;
                border: 1.5px solid #F59E0B;
                border-radius: 8px;
                font-size: 12px;
                font-weight: 700;
            }
        """

        style_solid = """
            QPushButton {
                background-color: #064E3B;
                color: #6EE7B7;
                border: 1.5px solid #10B981;
                border-radius: 8px;
                font-size: 12px;
                font-weight: 700;
            }
        """

        self.btn_conf_foggy.setStyleSheet(style_foggy if self.selected_confidence == "foggy" else style_default)
        self.btn_conf_prog.setStyleSheet(style_prog if self.selected_confidence == "progressing" else style_default)
        self.btn_conf_solid.setStyleSheet(style_solid if self.selected_confidence == "solid" else style_default)

    def _on_save_clicked(self) -> None:
        res = self.result
        self.ticket_submitted.emit(res)
        self.accept()

    @property
    def result(self) -> ExitTicketResult:
        return ExitTicketResult(
            action=self.selected_action,
            confidence=self.selected_confidence,
            next_class_question=self.txt_question.text().strip(),
            takeaway_note=self.txt_takeaway.text().strip(),
            extend_minutes=10,
        )

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key.Key_Escape:
            self.reject()
        elif event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            if not self.txt_question.hasFocus():
                self._on_save_clicked()
            else:
                super().keyPressEvent(event)
        else:
            super().keyPressEvent(event)
