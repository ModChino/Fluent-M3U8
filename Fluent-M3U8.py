# coding:utf-8
import os
import sys
from inspect import getsourcefile
from pathlib import Path

os.chdir(Path(getsourcefile(lambda: 0)).resolve().parent)

# Nuitka standalone compiles certifi into the binary, breaking its
# importlib.resources-based cacert.pem lookup (ImportError at startup).
# Shunt certifi with a stub whose where() points at the cacert.pem data
# file shipped next to the executable, before requests is imported.
_certifi_bundle = Path(os.getcwd()) / "certifi" / "cacert.pem"
if _certifi_bundle.exists() and "certifi" not in sys.modules:
    import types

    _certifi = types.ModuleType("certifi")
    _certifi.where = lambda: str(_certifi_bundle)
    _certifi.contents = lambda: _certifi_bundle.read_text(encoding="ascii")
    _certifi.__version__ = "stub"
    sys.modules["certifi"] = _certifi
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
