import sys
from pathlib import Path

from PySide6.QtCore import QUrl
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import QApplication

app = QApplication(sys.argv)

view = QWebEngineView()
html_path = Path(__file__).parent / "ui" / "index.html"
view.load(QUrl.fromLocalFile(str(html_path)))

view.setWindowTitle("DriverPay-Tracker")
view.resize(1200, 800)
view.show()

sys.exit(app.exec())
