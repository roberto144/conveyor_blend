from PyQt5.QtWidgets import QMessageBox, QDialog, QVBoxLayout, QTextEdit, QPushButton, QHBoxLayout
from PyQt5.QtCore import Qt
import traceback

class ErrorDialog(QDialog):
    """Enhanced error dialog with details and copy functionality"""
    
    def __init__(self, parent=None, title="Error", message="An error occurred", details=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.resize(500, 300)
        
        layout = QVBoxLayout()
        
        # Main message
        self.message_label = QTextEdit()
        self.message_label.setPlainText(message)
        self.message_label.setMaximumHeight(100)
        self.message_label.setReadOnly(True)
        layout.addWidget(self.message_label)
        
        # Details section (if provided)
        if details:
            self.details_text = QTextEdit()
            self.details_text.setPlainText(details)
            self.details_text.setReadOnly(True)
            layout.addWidget(self.details_text)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        copy_button = QPushButton("Copy to Clipboard")
        copy_button.clicked.connect(self.copy_to_clipboard)
        button_layout.addWidget(copy_button)
        
        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.accept)
        ok_button.setDefault(True)
        button_layout.addWidget(ok_button)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
        
        self.details = details
        self.full_message = message
    
    def copy_to_clipboard(self):
        """Copy error information to clipboard"""
        from PyQt5.QtWidgets import QApplication
        
        clipboard_text = f"Error: {self.full_message}"
        if self.details:
            clipboard_text += f"\n\nDetails:\n{self.details}"
        
        QApplication.clipboard().setText(clipboard_text)
    
    @staticmethod
    def show_error(parent, title, message, details=None):
        """Show error dialog"""
        if details:
            dialog = ErrorDialog(parent, title, message, details)
            dialog.exec_()
        else:
            QMessageBox.critical(parent, title, message)
    
    @staticmethod
    def show_warning(parent, title, message):
        """Show warning dialog"""
        QMessageBox.warning(parent, title, message)
    
    @staticmethod
    def show_info(parent, title, message):
        """Show information dialog"""
        QMessageBox.information(parent, title, message)
    
    @staticmethod
    def show_exception(parent, title, exception):
        """Show exception with traceback"""
        message = str(exception)
        details = traceback.format_exc()
        ErrorDialog.show_error(parent, title, message, details)
    
    @staticmethod
    def show_validation_error(parent, validation_errors):
        """Show validation errors in a formatted way"""
        if isinstance(validation_errors, list):
            message = "Validation failed with the following errors:"
            details = "\n".join(f"• {error}" for error in validation_errors)
        else:
            message = "Validation Error"
            details = str(validation_errors)
        
        ErrorDialog.show_error(parent, "Validation Error", message, details)

class ProgressDialog(QDialog):
    """Progress dialog for long operations"""
    
    def __init__(self, parent=None, title="Please wait...", message="Processing..."):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setWindowFlags(Qt.Dialog | Qt.CustomizeWindowHint | Qt.WindowTitleHint)
        
        from PyQt5.QtWidgets import QProgressBar, QLabel
        
        layout = QVBoxLayout()
        
        self.label = QLabel(message)
        layout.addWidget(self.label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # Indeterminate
        layout.addWidget(self.progress_bar)
        
        self.setLayout(layout)
        self.resize(300, 100)
    
    def update_message(self, message):
        """Update the progress message"""
        self.label.setText(message)
    
    def set_progress(self, value, maximum=100):
        """Set progress value"""
        self.progress_bar.setRange(0, maximum)
        self.progress_bar.setValue(value)