"""
    Minecraft Universal In-Game Timer
    Copyright (C) 2020  NinjaSnail1080  (Discord User: @NinjaSnail1080#8581)

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.
    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.
    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5 import uic
from nbt.nbt import NBTFile
import rapidjson as json

import sys
import os

import utils

try:
    DIRECTORY = sys._MEIPASS
except:
    DIRECTORY = os.path.dirname(__file__)

__version__ = open(os.path.join(DIRECTORY, "VERSION.txt")).read()

SETTINGS = QSettings(QSettings.NativeFormat, QSettings.UserScope, "Minecraft Universal In-Game Timer")


def get_last_played_level():
    levels = []
    mc_dir = SETTINGS.value("MinecraftDirectory", utils.get_default_minecraft_dir())
    mc_saves = os.path.join(mc_dir, "saves")

    if os.path.exists(os.path.join(mc_dir, "stats")):
        with open(os.path.join(mc_dir, "stats", os.listdir(os.path.join(mc_dir, "stats"))[0])) as f:
            pre17_stats = json.load(f)

    for world in os.listdir(mc_saves):
        try:
            level = NBTFile(os.path.join(mc_saves, world, "level.dat"))
            if not int(str(level["Data"]["Time"])):
                continue
            try:
                with open(os.path.join(mc_saves, world, "stats", os.listdir(os.path.join(mc_saves, world, "stats"))[0]), "r") as f:
                    stats = json.load(f)
            except: #* If it's pre 1.7.2
                stats = None

            try:
                data = {
                    "name": str(level["Data"]["LevelName"]),
                    "last_played": int(str(level["Data"]["LastPlayed"])),
                    "version": str(level["Data"]["Version"]["Name"]),
                    "igt": stats["stat.playOneMinute"] if int(str(level["Data"]["Version"]["Id"])) < 1451 else stats["stats"]["minecraft:custom"]["minecraft:play_one_minute"],
                    "pre17": False
                }
            except: #* If it's pre 1.9
                try:
                    data = {
                        "name": str(level["Data"]["LevelName"]),
                        "last_played": int(str(level["Data"]["LastPlayed"])),
                        "version": "Pre 1.9",
                        "igt": stats["stat.playOneMinute"],
                        "pre17": False
                    }
                except: #* If it's pre 1.7.2
                    data = {
                        "name": str(level["Data"]["LevelName"]),
                        "last_played": int(str(level["Data"]["LastPlayed"])),
                        "version": "Pre 1.7.2",
                        "igt": next(i for i in pre17_stats["stats-change"] if "1100" in i)["1100"],
                        "pre17": True
                    }
            levels.append(data)
        except:
            continue

    return sorted(levels, key=lambda d: d["last_played"], reverse=True)[0]


class SettingsWindow(QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        uic.loadUi(os.path.join(DIRECTORY, "SettingsWindow.ui"), self)
        self.setWindowFlag(Qt.WindowStaysOnTopHint)
        self.setWindowIcon(QIcon(os.path.join(DIRECTORY, "Resources", "icons.ico")))

        self.author_text.linkActivated.connect(self.open_link)
        self.author_text.setText(f"By NinjaSnail1080\u3000|\u3000<a href='https://github.com/NinjaSnail1080/mc-universal-in-game-timer'>Github</a> (v{__version__})")

        self.browse_field.setText(SETTINGS.value("MinecraftDirectory", utils.get_default_minecraft_dir()))

        self.browse_button.clicked.connect(self.browse_for_mc_dir)

        self.opacity_slider.setMinimum(10)
        self.opacity_slider.setMaximum(100)
        self.opacity_slider.setSingleStep(1)
        self.opacity_slider.setTickInterval(10)
        self.opacity_slider.setTickPosition(QSlider.TicksBothSides)
        self.opacity_slider.valueChanged.connect(self.change_opacity_percentage)
        self.opacity_slider.setValue(int(float(SETTINGS.value("Opacity", 0.5))*100))

        if SETTINGS.value("Theme", "dark") == "dark":
            self.dark_theme_button.setChecked(True)
        else:
            self.light_theme_button.setChecked(True)

        if sys.platform == "darwin":
            self.continue_button.setText("Save  (double-click)") #* idk why this bug exists
        else:
            self.continue_button.setText("Save")
        self.continue_button.clicked.connect(self.save_and_exit_settings)

        self.setFixedSize(420, 420)
        self.show()

    def browse_for_mc_dir(self):
        browse = QFileDialog(self)
        browse.setFileMode(QFileDialog.DirectoryOnly)
        if browse.exec_():
            mc_dir = browse.selectedFiles()[0]
            self.browse_field.setText(mc_dir)

    def change_opacity_percentage(self):
        self.opacity_text.setText(f"Opacity: {self.opacity_slider.value()}%")

    def open_link(self, link):
        QDesktopServices.openUrl(QUrl(link))

    def save_and_exit_settings(self):
        if self.browse_field.text() == "":
            SETTINGS.setValue("MinecraftDirectory", utils.get_default_minecraft_dir())
        else:
            SETTINGS.setValue("MinecraftDirectory", self.browse_field.text())
        SETTINGS.setValue("Opacity", self.opacity_slider.value() / 100)
        if self.dark_theme_button.isChecked():
            SETTINGS.setValue("Theme", "dark")
        elif self.light_theme_button.isChecked():
            SETTINGS.setValue("Theme", "light")

        self.close()
        self.new = TimerWindow()
        self.new.show()


class TimerWindow(QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setWindowOpacity(float(SETTINGS.value("Opacity", 0.5)))
        self.setWindowIcon(QIcon(os.path.join(DIRECTORY, "Resources", "icons.ico")))

        with open(os.path.join(DIRECTORY, "Resources", "Minecraftia-Regular-1.ttf"), "rb") as f:
            self.small_font = QFont(QFontDatabase.applicationFontFamilies(QFontDatabase.addApplicationFontFromData(f.read()))[0], 12)
        with open(os.path.join(DIRECTORY, "Resources", "Minecraftia-Regular-2.ttf"), "rb") as f:
            self.large_font = QFont(QFontDatabase.applicationFontFamilies(QFontDatabase.addApplicationFontFromData(f.read()))[0], 24)

        self.timer = QTimer()
        self.timer.setTimerType(Qt.PreciseTimer)
        self.timer.timeout.connect(self.update_igt)

        self.igt = QLabel("--:--:--.---")
        self.igt.setAlignment(Qt.AlignCenter)
        if SETTINGS.value("Theme", "dark") == "dark":
            self.igt.setStyleSheet("color: white;")
        self.igt.setFont(self.large_font)
        self.setCentralWidget(self.igt)

        self.toolbar = QToolBar("Main toolbar")
        self.toolbar.setIconSize(QSize(16, 16))
        self.addToolBar(self.toolbar)

        self.pre17_toolbar = QToolBar("Pre 1.7 Toolbar")

        if SETTINGS.value("Theme", "dark") == "dark":
            self.close_button = QAction(QIcon(os.path.join(DIRECTORY, "Resources", "white_x")), "", self)
            self.settings_button = QAction(QIcon(os.path.join(DIRECTORY, "Resources", "white_gear")), "", self)
        else:
            self.close_button = QAction(QIcon(os.path.join(DIRECTORY, "Resources", "black_x")), "", self)
            self.settings_button = QAction(QIcon(os.path.join(DIRECTORY, "Resources", "black_gear")), "", self)
        self.close_button.triggered.connect(self.close_window)
        self.settings_button.triggered.connect(self.open_settings)

        self.world_name = QLabel("Searching...")
        if SETTINGS.value("Theme", "dark") == "dark":
            self.world_name.setStyleSheet("color: white;")
        self.world_name.setFont(self.small_font)

        self.right_click_text = QLabel("Right-click to reset timer")
        if SETTINGS.value("Theme", "dark") == "dark":
            self.right_click_text.setStyleSheet("color: white;")
        self.right_click_text.setFont(self.small_font)

        self.left_spacer = QWidget()
        self.left_spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.right_spacer = QWidget()
        self.right_spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.toolbar.addAction(self.close_button)
        self.toolbar.addWidget(self.left_spacer)
        self.toolbar.addWidget(self.world_name)
        self.toolbar.addWidget(self.right_spacer)
        self.toolbar.addAction(self.settings_button)
        self.toolbar.setMovable(False)
        self.toolbar.setContextMenuPolicy(Qt.PreventContextMenu)
        self.toolbar.setStyleSheet("border: none;")

        self.left_spacer = QWidget()
        self.left_spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.right_spacer = QWidget()
        self.right_spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.pre17_toolbar.addWidget(self.left_spacer)
        self.pre17_toolbar.addWidget(self.right_click_text)
        self.pre17_toolbar.addWidget(self.right_spacer)
        self.pre17_toolbar.setMovable(False)
        self.pre17_toolbar.setContextMenuPolicy(Qt.PreventContextMenu)
        self.pre17_toolbar.setStyleSheet("border: none;")

        if SETTINGS.value("Theme", "dark") == "dark":
            self.setStyleSheet("background-color: black;")
        self.move(int(SETTINGS.value("TimerPosX", 0)), int(SETTINGS.value("TimerPosY", 0)))

        self.right_clicked = False

        self.show()
        self.timer.start(200)

    def update_igt(self):
        try:
            level_data = get_last_played_level()
            self.world_name.setText(f"{level_data['name']} ({level_data['version']})")

            if level_data["pre17"]:
                self.addToolBar(Qt.BottomToolBarArea, self.pre17_toolbar)
                if self.right_clicked:
                    SETTINGS.setValue("ResetTime", level_data["igt"])
                    self.right_clicked = False
                ticks = level_data["igt"] - int(SETTINGS.value("ResetTime", level_data["igt"]))
            else:
                self.removeToolBar(self.pre17_toolbar)
                ticks = level_data["igt"]

            seconds = ticks // 20
            h = str(seconds // 60 // 60)
            m = str(seconds // 60 % 60)
            s = str(seconds % 60)
            ms = str(int(ticks % 20 / 2 * 100))

            self.igt.setText(f"{h.zfill(2)}:{m.zfill(2)}:{s.zfill(2)}.{ms.zfill(3)}")
            if level_data["pre17"]:
                self.setFixedWidth(max([self.toolbar.sizeHint().width(), self.pre17_toolbar.sizeHint().width(), self.igt.sizeHint().width()]) + 16)
            else:
                self.setFixedWidth(max([self.toolbar.sizeHint().width(), self.igt.sizeHint().width()]) + 16)
        except:
            self.world_name.setText("ERROR:  No World Found")
            self.world_name.setStyleSheet("color: red;")
            self.igt.setText("--:--:--.---")
            self.setFixedWidth(max([self.toolbar.sizeHint().width(), self.igt.sizeHint().width()]) + 16)

    def close_window(self):
        SETTINGS.setValue("TimerPosX", self.x())
        SETTINGS.setValue("TimerPosY", self.y())
        self.timer.stop()
        self.close()

    def open_settings(self):
        self.close_window()
        self.setStyleSheet("")
        SettingsWindow(self)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.timer.stop()
            self.oldPos = event.globalPos()
        else:
            self.right_clicked = True

    def mouseReleaseEvent(self, event):
        self.timer.start(200)

    def mouseMoveEvent(self, event):
        try:
            delta = QPoint(event.globalPos() - self.oldPos)
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.oldPos = event.globalPos()
        except AttributeError:
            pass


if __name__ == "__main__":
    app = QApplication([])
    if sys.platform == "darwin":
        app.setStyle(QStyleFactory.create("macintosh"))
    else:
        app.setStyle(QStyleFactory.create("Fusion"))

    window = TimerWindow()
    app.exec_()
    sys.exit()
