from PyQt5.QtCore import Qt, QRectF, QRect, QSize, pyqtSignal, \
    QPropertyAnimation, QAbstractAnimation
from PyQt5.QtGui import QPalette, QColor, QTextOption, QPainter, \
    QKeySequence
from PyQt5.QtWidgets import QLabel, QWidget, \
    QVBoxLayout, QSizeGrip, QHBoxLayout, QColorDialog, \
    QMenu, QAction, QFontDialog, QShortcut, \
    QGraphicsOpacityEffect, QApplication, QDesktopWidget

from feeluown.helpers import resize_font


class Window(QWidget):
    FADING_TIME = 200

    play_previous_needed = pyqtSignal()
    play_next_needed = pyqtSignal()

    def __init__(self):
        super().__init__(parent=None)
        flags = self.windowFlags() | Qt.WindowStaysOnTopHint \
            | Qt.FramelessWindowHint | Qt.Tool | Qt.BypassWindowManagerHint
        self.setWindowFlags(flags)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.c = Container(self)
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)
        self._layout.addWidget(self.c)

        # for fade-in & fadeout animation
        self.effect = QGraphicsOpacityEffect()
        self.setGraphicsEffect(self.effect)
        self.animation = QPropertyAnimation(self.effect, b'opacity')
        self.set_default_pos()

        self._old_pos = None

        QShortcut(QKeySequence.ZoomIn, self).activated.connect(self.zoomin)
        QShortcut(QKeySequence.ZoomOut, self).activated.connect(self.zoomout)
        QShortcut(QKeySequence('Ctrl+='), self).activated.connect(self.zoomin)
        QShortcut(QKeySequence.Cancel, self).activated.connect(self.hide)

        self.setToolTip('''
* 右键可以弹出设置菜单
* Ctrl+= 或者 Ctrl++ 可以增大字体
* Ctrl+- 可以减小字体
* 鼠标前进后退键可以播放前一首/下一首
''')

    def set_default_pos(self):
        frame: QRect = self.frameGeometry()
        desktop: QDesktopWidget = QApplication.desktop()
        screen = desktop.screenNumber(QApplication.desktop().cursor().pos())
        geo: QRect = desktop.availableGeometry(screen)
        frame.moveTop(geo.bottom() - 80)
        frame.moveLeft((geo.width() - frame.width()) / 2)
        self.move(frame.topLeft())

    def set_sentence(self, text):
        if self.isVisible():
            self.c.label.setText(text)

    def mousePressEvent(self, e):
        self._old_pos = e.globalPos()

    def mouseMoveEvent(self, e):
        # NOTE: e.button() == Qt.LeftButton don't work on Windows
        # on Windows, even I drag with LeftButton, the e.button() return 0,
        # which means no button
        if self._old_pos is not None:
            delta = e.globalPos() - self._old_pos
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self._old_pos = e.globalPos()

    def mouseReleaseEvent(self, e):
        if not self.rect().contains(e.pos()):
            return
        if e.button() == Qt.BackButton:
            self.play_previous_needed.emit()
        elif e.button() == Qt.ForwardButton:
            self.play_next_needed.emit()

    def zoomin(self):
        label = self.c.label
        font = label.font()
        resize_font(font, +1)
        label.setFont(font)

    def zoomout(self):
        label = self.c.label
        font = label.font()
        resize_font(font, - 1)
        label.setFont(font)

    def sizeHint(self):
        return QSize(500, 60)

    def show(self):
        super(Window, self).show()
        self.animation.setDuration(self.FADING_TIME)
        self.animation.setStartValue(0)
        self.animation.setEndValue(1)
        self.animation.start()

    def hide(self):
        self.animation.setDuration(self.FADING_TIME)
        self.animation.setStartValue(1)
        self.animation.setEndValue(0)
        self.animation.finished.connect(self._hide)
        self.animation.start(QAbstractAnimation.DeleteWhenStopped)

    def _hide(self):
        super().hide()
        self.animation = QPropertyAnimation(self.effect, b'opacity')


class Container(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self._border_radius = 10
        self.label = QLabel('...', self)
        self._size_grip = QSizeGrip(self)
        self._size_grip.setFixedWidth(self._border_radius * 2)

        font = self.font()
        font.setPointSize(24)
        self.label.setFont(font)
        self.label.setAlignment(Qt.AlignBaseline | Qt.AlignVCenter | Qt.AlignHCenter)
        self.label.setWordWrap(False)

        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)
        self._layout.addSpacing(self._border_radius * 2)
        self._layout.addWidget(self.label)
        self._layout.addWidget(self._size_grip)
        self._layout.setAlignment(self._size_grip, Qt.AlignBottom)

    def paintEvent(self, e):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(Qt.NoPen)
        painter.setBrush(self.palette().color(QPalette.Window))
        painter.drawRoundedRect(self.rect(), self._border_radius, self._border_radius)
        painter.save()
        painter.setPen(QColor('white'))
        option = QTextOption()
        option.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        rect = QRect(self.mapToParent(self._size_grip.pos()), self._size_grip.size())
        painter.drawText(QRectF(rect), '●', option)
        painter.restore()

    def show_color_dialog(self, bg=True):

        def set_color(color):
            palette = self.palette()
            if bg:
                palette.setColor(QPalette.Active, QPalette.Window, color)
                palette.setColor(QPalette.Active, QPalette.Base, color)
                palette.setColor(QPalette.Inactive, QPalette.Window, color)
                palette.setColor(QPalette.Inactive, QPalette.Base, color)
            else:
                palette.setColor(QPalette.Active, QPalette.WindowText, color)
                palette.setColor(QPalette.Active, QPalette.Text, color)
                palette.setColor(QPalette.Inactive, QPalette.WindowText, color)
                palette.setColor(QPalette.Inactive, QPalette.Text, color)
            self.label.setPalette(palette)
            self.setPalette(palette)

        dialog = QColorDialog(self)
        dialog.currentColorChanged.connect(set_color)
        dialog.colorSelected.connect(set_color)
        dialog.setOption(QColorDialog.ShowAlphaChannel, True)
        dialog.exec()

    def show_font_dialog(self):
        dialog = QFontDialog(self.label.font(), self)
        dialog.currentFontChanged.connect(self.label.setFont)
        dialog.fontSelected.connect(self.label.setFont)
        dialog.exec()

    def contextMenuEvent(self, e):
        menu = QMenu()
        bg_color_action = QAction('背景颜色', menu)
        fg_color_action = QAction('文字颜色', menu)
        font_action = QAction('字体', menu)
        menu.addAction(bg_color_action)
        menu.addAction(fg_color_action)
        menu.addSeparator()
        menu.addAction(font_action)
        bg_color_action.triggered.connect(lambda: self.show_color_dialog(bg=True))
        fg_color_action.triggered.connect(lambda: self.show_color_dialog(bg=False))
        font_action.triggered.connect(self.show_font_dialog)
        menu.exec(e.globalPos())
