from PyQt5.QtWidgets import QMessageBox, QWidget
from PyQt5.QtCore import Qt

class ErrorDialog:
    """Utility class for showing error dialogs"""
    
    @staticmethod
    def show_error(parent: QWidget, title: str, message: str):
        """Show error message dialog"""
        msg = QMessageBox(parent)
        msg.setIcon(QMessageBox.Critical)
        msg.setWindowTitle(title)
        msg.setText(message)
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()
    
    @staticmethod
    def show_warning(parent: QWidget, title: str, message: str):
        """Show warning message dialog"""
        msg = QMessageBox(parent)
        msg.setIcon(QMessageBox.Warning)
        msg.setWindowTitle(title)
        msg.setText(message)
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()
    
    @staticmethod
    def show_info(parent: QWidget, title: str, message: str):
        """Show information message dialog"""
        msg = QMessageBox(parent)
        msg.setIcon(QMessageBox.Information)
        msg.setWindowTitle(title)
        msg.setText(message)
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()
    
    @staticmethod
    def ask_question(parent: QWidget, title: str, question: str) -> bool:
        """Ask yes/no question"""
        reply = QMessageBox.question(
            parent, title, question,
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        return reply == QMessageBox.Yes