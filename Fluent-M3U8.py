# coding:utf-8
import os
import sys
from inspect import getsourcefile
from pathlib import Path

os.chdir(Path(getsourcefile(lambda: 0)).resolve().parent)

# Nuitka standalone compiles certifi into the binary, breaking its
# __file__-based cacert.pem lookup (ImportError at startup). Point
# requests at the data file shipped next to the executable instead.
_certifi_bundle = Path(os.getcwd()) / "certifi" / "cacert.pem"
if _certifi_bundle.exists():
    os.environ["REQUESTS_CA_BUNDLE"] = str(_certifi_bundle)

from PySide6.QtCore import Qt, QTranslator
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication
from qfluentwidgets import FluentTranslator

from app.common.config import cfg
from app.common.application import SingletonApplication
from app.view.main_window import MainWindow


# enable dpi scale
if cfg.get(cfg.dpiScale) != "Auto":
    os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "0"
    os.environ["QT_SCALE_FACTOR"] = str(cfg.get(cfg.dpiScale))

# create application
app = SingletonApplication(sys.argv, "Fluent-M3U8")
app.setAttribute(Qt.AA_DontCreateNativeWidgetSiblings)

if sys.platform == "darwin":
    from AppKit import NSApplication
    NSApplication.sharedApplication()

# internationalization
locale = cfg.get(cfg.language).value
translator = FluentTranslator(locale)
galleryTranslator = QTranslator()
galleryTranslator.load(locale, "app", ".", ":/app/i18n")

app.installTranslator(translator)
app.installTranslator(galleryTranslator)

# create main window
w = MainWindow()
app.aboutToQuit.connect(w.onExit)
w.show()

app.exec()
