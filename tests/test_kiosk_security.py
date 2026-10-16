"""Unit tests for kiosk mode and password security."""

import unittest
from unittest.mock import patch
from PySide6.QtCore import Qt
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import QApplication, QDialog

from study_station.core.security import hash_password, verify_password
from study_station.core.settings import AppSettings
from study_station.ui.kiosk_dialogs import (
    KioskLockOverlay,
    KioskUnlockDialog,
    SetKioskPasswordDialog,
)
from study_station.ui.main_window import MainWindow

app = QApplication.instance() or QApplication([])


class TestKioskSecurity(unittest.TestCase):
    """Test PBKDF2 password hashing and verification."""

    def test_hashing_and_verification(self) -> None:
        pwd = "KioskSecretPass2026!"
        pwd_hash = hash_password(pwd)

        self.assertTrue(bool(pwd_hash))
        self.assertIn(":", pwd_hash)

        # Verification with exact password
        self.assertTrue(verify_password(pwd_hash, pwd))

        # Verification with incorrect password
        self.assertFalse(verify_password(pwd_hash, "wrong_password"))
        self.assertFalse(verify_password(pwd_hash, ""))

        # Verification with corrupt or empty hash
        self.assertFalse(verify_password("", pwd))
        self.assertFalse(verify_password("not-a-valid-hash", pwd))
        self.assertFalse(verify_password("salt_only", pwd))

    def test_unique_salts(self) -> None:
        """Ensure hashing the same password twice yields different salts and hashes."""
        pwd = "same_password"
        hash1 = hash_password(pwd)
        hash2 = hash_password(pwd)

        self.assertNotEqual(hash1, hash2)
        self.assertTrue(verify_password(hash1, pwd))
        self.assertTrue(verify_password(hash2, pwd))

    def test_empty_password_handling(self) -> None:
        self.assertEqual(hash_password(""), "")
        self.assertFalse(verify_password("", ""))


class TestAppSettingsKiosk(unittest.TestCase):
    """Test AppSettings kiosk mode serialization and helper methods."""

    def test_default_settings(self) -> None:
        settings = AppSettings()
        self.assertFalse(settings.kiosk_mode_enabled)
        self.assertEqual(settings.kiosk_password_hash, "")
        self.assertFalse(settings.has_kiosk_password())

    def test_password_management_helpers(self) -> None:
        settings = AppSettings()
        settings.set_kiosk_password("my_admin_pass")
        self.assertTrue(settings.has_kiosk_password())
        self.assertTrue(settings.verify_kiosk_password("my_admin_pass"))
        self.assertFalse(settings.verify_kiosk_password("wrong_pass"))

        settings.kiosk_mode_enabled = True
        settings.clear_kiosk_password()
        self.assertFalse(settings.has_kiosk_password())
        self.assertFalse(settings.kiosk_mode_enabled)

    def test_serialization_round_trip(self) -> None:
        settings = AppSettings(
            kiosk_mode_enabled=True,
            kiosk_password_hash="test_salt:test_hex",
        )
        data = settings.to_dict()
        self.assertTrue(data["kiosk_mode_enabled"])
        self.assertEqual(data["kiosk_password_hash"], "test_salt:test_hex")

        restored = AppSettings.from_dict(data)
        self.assertTrue(restored.kiosk_mode_enabled)
        self.assertEqual(restored.kiosk_password_hash, "test_salt:test_hex")


class TestKioskDialogs(unittest.TestCase):
    """Test KioskUnlockDialog and SetKioskPasswordDialog workflows."""

    def test_unlock_dialog_validation(self) -> None:
        expected_hash = hash_password("correct_pass")
        dlg = KioskUnlockDialog(expected_hash=expected_hash)

        # Enter wrong password
        dlg.input_password.setText("wrong_pass")
        dlg._on_unlock_clicked()
        self.assertFalse(dlg.lbl_error.isHidden())
        self.assertIn("Incorrect password", dlg.lbl_error.text())
        self.assertEqual(dlg.result(), QDialog.DialogCode.Rejected)

        # Enter correct password
        dlg.input_password.setText("correct_pass")
        dlg._on_unlock_clicked()
        self.assertEqual(dlg.result(), QDialog.DialogCode.Accepted)

    def test_set_password_dialog_initial(self) -> None:
        dlg = SetKioskPasswordDialog(current_hash="")
        self.assertIsNone(dlg.input_current)

        # Blank password error
        dlg.input_new.setText("")
        dlg.input_confirm.setText("")
        dlg._on_save_clicked()
        self.assertFalse(dlg.lbl_error.isHidden())
        self.assertIn("cannot be blank", dlg.lbl_error.text())

        # Mismatch error
        dlg.input_new.setText("secret1")
        dlg.input_confirm.setText("secret2")
        dlg._on_save_clicked()
        self.assertFalse(dlg.lbl_error.isHidden())
        self.assertIn("Passwords do not match", dlg.lbl_error.text())

        # Success
        dlg.input_new.setText("secret123")
        dlg.input_confirm.setText("secret123")
        dlg._on_save_clicked()
        self.assertEqual(dlg.result(), QDialog.DialogCode.Accepted)
        self.assertTrue(verify_password(dlg.new_password_hash, "secret123"))

    def test_set_password_dialog_change_password(self) -> None:
        cur_hash = hash_password("old_pass")
        dlg = SetKioskPasswordDialog(current_hash=cur_hash)
        self.assertIsNotNone(dlg.input_current)

        # Wrong current password
        dlg.input_current.setText("bad_old_pass")
        dlg.input_new.setText("new_pass")
        dlg.input_confirm.setText("new_pass")
        dlg._on_save_clicked()
        self.assertFalse(dlg.lbl_error.isHidden())
        self.assertIn("Current password is incorrect", dlg.lbl_error.text())

        # Correct current password
        dlg.input_current.setText("old_pass")
        dlg._on_save_clicked()
        self.assertEqual(dlg.result(), QDialog.DialogCode.Accepted)
        self.assertTrue(verify_password(dlg.new_password_hash, "new_pass"))


class TestMainWindowKioskEnforcement(unittest.TestCase):
    """Test MainWindow closeEvent and fullscreen interception."""

    def _create_window(self) -> MainWindow:
        window = MainWindow()
        if hasattr(window, "_status_timer"):
            window._status_timer.stop()
        if hasattr(window, "_timer_sync_timer"):
            window._timer_sync_timer.stop()
        return window

    def test_close_event_unrestricted_when_kiosk_disabled(self) -> None:
        window = self._create_window()
        window._settings.kiosk_mode_enabled = False
        event = QCloseEvent()
        window.closeEvent(event)
        self.assertTrue(event.isAccepted())

    def test_close_event_guarded_when_kiosk_enabled(self) -> None:
        window = self._create_window()
        window._settings.kiosk_mode_enabled = True
        window._settings.set_kiosk_password("admin_pass")

        # Simulate user canceling unlock dialog
        with patch.object(window, "_require_kiosk_unlock", return_value=False):
            event = QCloseEvent()
            window.closeEvent(event)
            self.assertFalse(event.isAccepted())

        # Simulate user entering valid password
        with patch.object(window, "_require_kiosk_unlock", return_value=True):
            event = QCloseEvent()
            window.closeEvent(event)
            self.assertTrue(event.isAccepted())

    def test_toggle_fullscreen_guarded_when_kiosk_enabled(self) -> None:
        window = self._create_window()
        window._settings.kiosk_mode_enabled = True
        window._settings.set_kiosk_password("admin_pass")

        # Set fullscreen state
        window.showFullScreen()
        self.assertTrue(window.isFullScreen())

        # User denies password prompt -> remains fullscreen
        with patch.object(window, "_require_kiosk_unlock", return_value=False):
            window.toggle_fullscreen()
            self.assertTrue(window.isFullScreen())

        # User provides password -> exits fullscreen
        with patch.object(window, "_require_kiosk_unlock", return_value=True):
            window.toggle_fullscreen()
            self.assertFalse(window.isFullScreen())

    def test_lock_overlay_show_and_unlock(self) -> None:
        window = self._create_window()
        window._settings.set_kiosk_password("station_pass")
        window.lock_station()

        self.assertFalse(window._kiosk_lock_overlay.isHidden())

        # Wrong password does not unlock
        window._kiosk_lock_overlay.input_pwd.setText("wrong")
        window._kiosk_lock_overlay._on_unlock()
        self.assertFalse(window._kiosk_lock_overlay.isHidden())

        # Correct password unlocks and hides overlay
        window._kiosk_lock_overlay.input_pwd.setText("station_pass")
        window._kiosk_lock_overlay._on_unlock()
        self.assertTrue(window._kiosk_lock_overlay.isHidden())


if __name__ == "__main__":
    unittest.main()
