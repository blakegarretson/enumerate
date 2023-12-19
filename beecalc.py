"""
BeeCalc: Cross-platform notebook calculator with robust unit support

    Copyright (C) 2023  Blake T. Garretson

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.


"""

import json
import math
import re
import sys
import os
import pydoc
from pathlib import Path
from fractions import Fraction
import unitclass
from PyQt6.QtCore import (QCoreApplication, QEvent, QMargins, QPoint, QFile, QTextStream,
                          QRegularExpression, QSize, Qt, QTimer)
from PyQt6.QtGui import (QAction, QColor, QFont, QFontDatabase, QIcon,
                         QKeySequence, QPixmap, QShortcut, QSyntaxHighlighter,
                         QTextCharFormat, QTextOption, QTextCursor)
from PyQt6.QtWidgets import (QApplication, QCheckBox, QColorDialog, QComboBox, QToolTip,
                             QDialog, QDialogButtonBox, QFontComboBox, QFrame, QMenu, QTabWidget,
                             QGroupBox, QHBoxLayout, QLabel, QLineEdit, QTableWidgetItem,
                             QMainWindow, QMessageBox, QPushButton, QTableWidget, QPlainTextEdit,
                             QRadioButton, QSizePolicy, QSpinBox, QSplitter, QHeaderView,
                             QStatusBar, QStyle, QTextEdit, QToolBar, QToolButton,QSizePolicy,
                             QVBoxLayout, QWidget, QScrollBar)

import beenotepad
import time
# resources not explicitly used, but used in QFile, QIcon, QPixmap, etc.
import resources

basedir = os.path.dirname(__file__)
sys.path.append(basedir)


class ConfirmationDialog(QDialog):
    def __init__(self, parent, title, message):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.buttonBox = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        layout = QVBoxLayout()
        layout.addWidget(QLabel(message))
        layout.addWidget(self.buttonBox)
        self.setLayout(layout)


class settingsdict(dict):
    """Dict class with dot notation for ease of use"""
    __getattr__ = dict.get
    __setattr__ = dict.__setitem__  # type: ignore
    __delattr__ = dict.__delitem__  # type: ignore


default_themes = {
    'Monokai': dict(
        theme='Monokai',
        color_text="#fefaf4",
        color_background="#262728",
        color_comment="#ff6289",
        color_constant="#ff6289",
        color_function="#aadc76",
        color_operator="#ffd866",
        color_variable="#79dce8",
        color_unit="#ab9df3",
        color_conversion="#fd9967",
        color_error='#ff6289',
        color_menu='#959595',
        color_status='#959595',
        color_stats='#535353',
    ),
    'Muted': dict(
        theme='Muted',
        color_text='#d3c6aa',
        color_background='#2d353b',
        color_comment='#e67e81',  # #comment
        color_constant='#e67e81',
        color_function='#a7c081',  # sin(), pi
        color_operator='#e79875',  # + - / etc
        color_variable='#7fbcb3',
        color_unit='#d799b6',
        color_conversion='#85928a',
        color_error='#e67e81',
        color_menu='#959595',
        color_status='#959595',
        color_stats='#535353',
    ),
    'Solarized': dict(
        theme='Solarized',
        color_text='#839496',
        color_background='#002b36',
        color_comment='#dc322f',  # #comment
        color_constant='#d33682',
        color_function='#268bd2',  # sin(), pi
        color_operator='#2aa198',  # + - / etc
        color_variable='#859900',
        color_unit='#6c71c4',
        color_conversion='#cb4b16',
        color_error='#dc322f',
        color_menu='#959595',
        color_status='#959595',
        color_stats='#535353',
    ),
    'Light': dict(
        theme='Light',
        color_text='#55555b',
        color_background='#ffffff',
        color_comment='#c76a2f',  # #comment
        color_constant='#ee6997',
        color_function='#464386',  # sin(), pi
        color_operator='#e56c96',  # + - / etc
        color_variable='#64ae4e',
        color_unit='#5f6abf',
        color_conversion='#e99b42',
        color_error='#dc3939',
        color_menu='#808080',
        color_status='#464646',
        color_stats='#a4a4a4',
    )

}

num_formats = {'Auto': 'g', 'Fix': 'f'}

default_settings = dict(
    num_fixdigits='5',
    num_autodigits='10',
    num_digits='10',
    num_fmt='Auto',
    font='',
    font_size=16,
    font_bold=False,
    align=False,
    line_spacing=1.0,
) | default_themes['Monokai']

default_notepads = {
    'current':
    0,
    'notepads': [[
        '# Welcome to BeeCalc!', '2+3', '@+1', '2 lb to grams',
        'width = 20 ft', 'length = 10 ft', 'area = length*width', '@ to in2',
        'sin(90deg)', 'sin(pi/2)'
    ], ['a=1', 'b=2 # this is a comment', 'c=3', 'total=a+b+c']]
}

beecalc_home = Path().home() / ".config" / "beecalc"
beecalc_settings = beecalc_home / 'settings.json'
beecalc_notepads = beecalc_home / 'notepads.json'


def save_default_notepads():
    with beecalc_notepads.open('w') as jsonfile:
        json.dump(default_notepads, jsonfile, indent=2)


def save_notepads(current, notepads):
    with beecalc_notepads.open('w') as jsonfile:
        json.dump({
            'current': current,
            'notepads': notepads
        },
            jsonfile,
            indent=2)


def load_notepads():
    with beecalc_notepads.open() as jsonfile:
        notepads_dict = json.load(jsonfile)
    return int(notepads_dict['current']), notepads_dict['notepads']


def save_settings(settings):
    with beecalc_settings.open('w') as jsonfile:
        json.dump(dict(settings), jsonfile, indent=2)


def load_settings():
    with beecalc_settings.open() as jsonfile:
        return settingsdict(json.load(jsonfile))


def initililize_config():
    if not beecalc_home.exists():
        beecalc_home.mkdir(parents=True)

    if beecalc_settings.exists():
        settings = load_settings()
    else:
        settings = settingsdict(default_settings.copy())
        save_settings(settings)

    if not beecalc_notepads.exists():
        save_default_notepads()
    current, notepads = load_notepads()

    return settings, current, notepads


parser = beenotepad.BeeParser()
function_list = sorted(list(parser.functions.keys()))
constant_list = list(parser.constants.keys())
unit_list = []
for name, unit in unitclass._units.items():
    # if name not in unit_list:
    #     unit_list.extend([name] + (unit['aliases'] if unit['aliases'] else []))
    unit_variations = [name] + (unit['aliases'] if unit['aliases'] else [])
    unit_list.extend([x for x in unit_variations if x not in unit_list])
unit_list.sort()


class BeeInputSyntaxHighlighter(QSyntaxHighlighter):
    def __init__(self, settings, variables, parent=None):
        super().__init__(parent)  # type: ignore

        self.rules = []
        self.var_re_str = r'(?<!\w )\b({})\b'
        self.var_re = QRegularExpression(
            r'|'.join([self.var_re_str.format(w) for w in variables]))
        rule_pairs = [  # order matters below, more general go first and are overridden by more specific
            (r'[a-zA-Z_Ωμ°]+[0-9⁰¹²³⁴⁵⁶⁷⁸⁹]*', settings.color_unit),  # units
            (r'\$', settings.color_unit),  # units
            (r'(?<=\d)\s*%', settings.color_unit),  # %
            (r'(?<=\d)\s*%\s*(?=\d)', settings.color_operator),  # %
            ('|'.join([rf'(\b{i}\()' for i in function_list]),
             settings.color_function),  # function call
            (r'[+-/*=(),^]', settings.color_operator),  # operator
            (r'\?', settings.color_error),  # ERROR
            ('|'.join([rf'(\b{i}\b)' for i in constant_list]),
             settings.color_constant),  # constant
            (r"\b\d+\.*\d*([Ee][-+]?)?\d?", settings.color_text),  # numbers
            (r' to ', settings.color_conversion),  # conversion
            # (r'(?<=[a-zA-Z_Ωμ°][0-9⁰¹²³⁴⁵⁶⁷⁸⁹])|(?<=[a-zA-Z_Ωμ°@])\s*(( in )|( to ))(?=[a-zA-Z_Ωμ°])', settings.color_conversion),  # conversion
            # (r'(?<=[a-zA-Z_Ωμ°][0-9⁰¹²³⁴⁵⁶⁷⁸⁹])|(?<=[a-zA-Z_Ωμ°@])\s*(( in )|( to ))\s*(?=[a-zA-Z_Ωμ°])', settings.color_conversion),  # conversion
            (r'(?<=%)\s+of\s+', settings.color_conversion),  # conversion
            (r'@', settings.color_variable),  # variable name
            (r'\w+\s*(?==)', settings.color_variable),  # variable name
            (self.var_re, settings.color_variable),  # variable name
            (r'#.*$', settings.color_comment),  # comment
        ]
        for regexp, color in rule_pairs:
            rule_format = QTextCharFormat()
            rule_format.setForeground(QColor(color))
            if isinstance(regexp, str):
                self.rules.append((QRegularExpression(regexp), rule_format))
            else:
                self.rules.append((self.var_re, rule_format))

    def updateVars(self, variables):
        self.var_re.setPattern(
            r'|'.join([self.var_re_str.format(w) for w in variables]))

    def highlightBlock(self, text):
        # print(self.var_re)
        for pattern, char_format in self.rules:
            match_iterator = QRegularExpression(pattern).globalMatch(text)
            while match_iterator.hasNext():
                match = match_iterator.next()
                self.setFormat(match.capturedStart(),
                               match.capturedLength(), char_format)


class BeeOutputSyntaxHighlighter(QSyntaxHighlighter):
    def __init__(self, settings, parent=None):
        super().__init__(parent)  # type: ignore

        self.rules = []
        rule_pairs = [  # order matters below, more general go first and are overridden by more specific
            (r'[a-zA-Z_Ωμ°%]+[0-9⁰¹²³⁴⁵⁶⁷⁸⁹]*', settings.color_unit),  # units
            (r'%', settings.color_unit),  # %
            (r'\$', settings.color_unit),  # units
            (r'[+-/*=(),]', settings.color_operator),  # operator
            (r'\?', settings.color_error),  # ERROR
            (r'<.*?>', settings.color_error),  # ERROR
            (r"\b\d+\.*\d*([Ee]|[Ee]-)*\d*", settings.color_text),  # numbers
        ]
        for regexp, color in rule_pairs:
            rule_format = QTextCharFormat()
            rule_format.setForeground(QColor(color))
            self.rules.append((QRegularExpression(regexp), rule_format))

    def highlightBlock(self, text):
        for pattern, char_format in self.rules:
            match_iterator = QRegularExpression(pattern).globalMatch(text)
            while match_iterator.hasNext():
                match = match_iterator.next()
                self.setFormat(match.capturedStart(),
                               match.capturedLength(), char_format)


class BeeCalcStatusBar(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.initial_pos = None
        status_bar_layout = QHBoxLayout(self)
        status_bar_layout.setContentsMargins(4, 4, 4, 4)
        status_bar_layout.setSpacing(2)

        self.status = QLabel("Status", self)
        self.status.setAlignment(Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)
        self.status.setStyleSheet(f"QLabel {{font-size: 12pt; color: {parent.settings.color_status}; }}")

        self.statslabel = QLabel("")
        # self.statslabel.setFixedHeight(20)
        self.statslabel.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignVCenter)
        self.statslabel.setStyleSheet(f"QLabel {{font-size: 12pt; color: {parent.settings.color_stats}; }}")

        status_bar_layout.addWidget(self.status)
        status_bar_layout.addWidget(self.statslabel)

    def showMessage(self, msg, duration=3000):
        self.status.setText(msg)
        self.timer = QTimer()
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.clearMessage)
        self.timer.start(duration)


    def clearMessage(self):
        self.status.setText("")

class BeeCalcTitleBar(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.initial_pos = None
        title_bar_layout = QHBoxLayout(self)
        title_bar_layout.setContentsMargins(1, 1, 1, 1)
        title_bar_layout.setSpacing(2)

        self.menu_button = QToolButton(self)
        self.menu_button.setText("☰")
        self.menu_button.clicked.connect(parent.showNotepadPopup)
        self.menu_button.setToolTip("Change notepads")
        # self.menu_button.setStatusTip("Change notepads")

        self.add_button = QToolButton(self)
        self.add_button.setText('+')
        self.add_button.clicked.connect(parent.addNotepad)
        self.add_button.setToolTip('Create new notepad')

        self.trash_button = QToolButton(self)
        self.trash_button.setText("–")
        self.trash_button.clicked.connect(parent.deleteNotepad)
        self.trash_button.setToolTip('Delete current notepad')

        self.settings_button = QToolButton(self)
        self.settings_button.setText("⚙")
        self.settings_button.clicked.connect(parent.openSettings)
        # self.settings_button.clicked.connect(parent.settingsMenu)
        self.settings_button.setToolTip("Settings menu")

        self.pin_button = QToolButton(self)
        self.pin_button.setText("○")
        # self.pin_button.setText("⦿")
        self.pin_button.clicked.connect(parent.toggleStayOnTop)
        self.pin_button.setToolTip("Keep window on top")

        self.help_button = QToolButton(self)
        self.help_button.setText("?")
        self.help_button.clicked.connect(parent.helpPopupMenu)
        self.help_button.setToolTip("App Help & Info")

        self.min_button = QToolButton(self)
        self.min_button.setText('_')
        self.min_button.clicked.connect(self.window().showMinimized)

        self.close_button = QToolButton(self)
        self.close_button.setText("×")
        # self.close_button.setText("╳")
        self.close_button.clicked.connect(self.window().close)

        self.buttons = []
        def add_button(button, fontsize=16, weight='normal'):
            self.buttons.append((button, fontsize, weight))
            button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            button.setFixedSize(QSize(20, 20))
            title_bar_layout.addWidget(button)

        # print(">>",self.close_button.fontInfo().pointSize(), self.close_button.fontInfo().pixelSize(), self.close_button.fontInfo().fixedPitch() )
        add_button(self.menu_button)
        add_button(self.add_button)
        add_button(self.trash_button)
        add_button(self.settings_button, 20)
        print(self.settings_button.styleSheet())

        self.title = QLabel(parent.windowTitle(), self)
        self.title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title.setStyleSheet(
            f"QLabel {{color: {parent.settings.color_menu}; }}")  # margin-left: 48px;
        title_bar_layout.addWidget(self.title)

        add_button(self.pin_button)
        add_button(self.help_button)
        add_button(self.min_button, weight='bold')
        add_button(self.close_button, 18, 'bold')
        self.updateButtonStyle()
        # print("<<",self.close_button.fontInfo().pointSize(), self.close_button.fontInfo().pixelSize(), self.close_button.fontInfo().fixedPitch() )
    def updateButtonStyle(self):
        for button, fontsize, weight in self.buttons:
            button.setStyleSheet(
                f"QToolButton {{ border: none; padding: 2px; font-size: {fontsize}pt; color: {self.parent.settings.color_status}; font-weight: {weight}; }}"
            )
            

class MainWindow(QMainWindow):
    re_zeropoint = re.compile(r"[. ]|$")
    re_incomplete = re.compile(r'(.*?\s*)\b(\w+)$')
    re_functionname = re.compile(r'\b(\w+)\($')

    def __init__(self, settings, current, notepads):
        super().__init__()

        self.setUnifiedTitleAndToolBarOnMac(True)
        self.settings = settings
        self.current = current
        self.notepads = notepads

        # Status Bar
        self.status_bar = BeeCalcStatusBar(self)
        self.status = self.status_bar.status
        self.statslabel = self.status_bar.statslabel
        # self.status_bar = QStatusBar(self)
        # self.setStatusBar(self.status_bar)
        # self.statslabel = QLabel("")
        # self.statslabel.setStyleSheet(f"color:#65666b;")
        # self.status_bar.addPermanentWidget(self.statslabel)

        self.notepad = beenotepad.BeeNotepad()
        input_text = self.getNotepadText(self.current)

        font_families = QFontDatabase.families()
        if settings.font not in font_families:
            for fontname in ['Consolas', 'Andale Mono', 'Courier New', 'Noto Sans Mono', 'Monospace', 'Courier']:
                if fontname in font_families:
                    self.settings.font = fontname
                    break

        self.setWindowTitle("BeeCalc")
        self.resize(400, 600)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self.input = QTextEdit()
        self.output = QTextEdit()
        splitter = QSplitter()
        splitter.addWidget(self.input)
        splitter.addWidget(self.output)
        splitter.setStretchFactor(0, 5)
        splitter.setStretchFactor(1, 4)
        splitter.setHandleWidth(2)
        splitter.setCollapsible(0, False)
        splitter.setCollapsible(1, False)

        self.updateFont()

        self.input.setWordWrapMode(QTextOption.WrapMode.NoWrap)
        self.output.setWordWrapMode(QTextOption.WrapMode.NoWrap)
        self.input.setAcceptRichText(False)
        self.syntax_highlighter_in = BeeInputSyntaxHighlighter(
            self.settings, tuple(self.notepad.parser.vars.keys()), self.input.document())
        self.syntax_highlighter_out = BeeOutputSyntaxHighlighter(
            self.settings, self.output.document())

        self.inputScrollbar = self.input.verticalScrollBar()
        self.inputScrollbar.hide()
        self.outputScrollbar = self.output.verticalScrollBar()
        self.keepScrollSynced = True
        self.inputScrollbar.valueChanged.connect(self.syncScroll)
        self.outputScrollbar.valueChanged.connect(self.syncScroll)

        self.input.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.output.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.input.horizontalScrollBar().setFixedHeight(0)
        self.output.horizontalScrollBar().setFixedHeight(0)

        # need this for tab completion
        self.tabPopupVisable = False

        self.title_bar = BeeCalcTitleBar(self)

        # Notepad combo box
        self.notepadBox = QComboBox(self)
        self.populateNotepadBox()
        self.notepadBox.setCurrentIndex(self.current)
        self.notepadBox.hide()

        layout = QVBoxLayout()
        # layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.addWidget(self.title_bar)
        # splitter.setAutoFillBackground(True)
        splitter.setSizePolicy(QSizePolicy.Policy.Expanding,QSizePolicy.Policy.Expanding)
        layout.addWidget(splitter)
        layout.addWidget(self.status_bar)

        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        container = QWidget()
        self.mainwidget = container
        container.setObjectName("Container")
        container.setLayout(layout)
        self.updateStyle()  # apply stylesheets for widget defaults

        self.input.installEventFilter(self)
        QShortcut(QKeySequence('Ctrl+D'),
                  self).activated.connect(self.duplicateLine)
        QShortcut(QKeySequence('Ctrl+Shift+N'),
                  self).activated.connect(self.deleteNotepad)
        QShortcut(QKeySequence('Ctrl+N'),
                  self).activated.connect(self.addNotepad)
        # QShortcut(QKeySequence('Ctrl+M'),
        #           self).activated.connect(self.toggleMenuToolbar)
        # QShortcut(QKeySequence('Ctrl+Shift+F'),
        #           self).activated.connect(self.toggleStyleToolbar)
        QShortcut(QKeySequence('Ctrl+Shift+S'),
                  self).activated.connect(self.simplify)
        QShortcut(QKeySequence('Ctrl+Shift+E'),
                  self).activated.connect(self.expand)

        self.setCentralWidget(container)

        self.input.cursorPositionChanged.connect(self.processNotepad)
        self.input.setText(input_text)
        cursor = self.input.textCursor()
        cursor.setPosition(len(input_text))
        self.input.setTextCursor(cursor)

    def help(self):
        print("Help")

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.initial_pos = event.position().toPoint()
        super().mousePressEvent(event)
        event.accept()

    def mouseMoveEvent(self, event):
        if self.initial_pos is not None:
            delta = event.position().toPoint() - self.initial_pos
            self.window().move(
                self.window().x() + delta.x(),
                self.window().y() + delta.y(),
            )
        super().mouseMoveEvent(event)
        event.accept()

    def mouseReleaseEvent(self, event):
        self.initial_pos = None
        super().mouseReleaseEvent(event)
        event.accept()

    def eventFilter(self, obj, event):
        if obj == self.input and event.type() == QEvent.Type.KeyPress:
            if event.key() == Qt.Key.Key_Tab:
                self.tabCompletion()
                return True
            elif event.key() == Qt.Key.Key_Return:
                # Capture the enter/return on Mac so the keypres on the tab completion popup
                # doesn't pass a return to the QTextEdit box. I think this a bug on Mac since
                # it doesn't happen on Windows?
                if self.tabPopupVisable:
                    self.tabPopupVisable = False
                    return True
                # self.delayedProcessNotepad()
            elif event.key() in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace):
                # this is necessary because deleting blocks of text may not change the cursor
                # position so processNotepad is not called. The delay here is to wait until the
                # return is called and the keypress is executed before running processNotepad
                self.delayedProcessNotepad()
            # else:
            #     self.delayedProcessNotepad()
        return super().eventFilter(obj, event)

    def delayedProcessNotepad(self, t=5):
        self.timer = QTimer()
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.processNotepad)
        self.timer.start(t)

    def tabCompletion(self):
        position = self.input.textCursor().position()
        line = self.input.toPlainText()[:position].split('\n')[-1]
        result = self.re_incomplete.search(line)

        if result:
            print(result.groups())
            print(result.groupdict())
            print(result.start(), result.pos, result.span())
            word = result.groups()[1]
            variables = [x for x in self.notepad.parser.vars.keys() if x.startswith(word)]
            constants = [x for x in self.notepad.parser.constants.keys() if x.startswith(word)]
            funcs = [f'{x}(' for x in function_list if word in x]
            units = [x for x in unit_list if word in x]
            wordlist = variables + constants + funcs + units
            priority = [w for w in wordlist if w.startswith(word)]
            rest = [w for w in wordlist if not w.startswith(word)]
            wordlist = priority + rest
            start, end = position - len(line) + result.start() + len(result.groups()[0]), position
            self.replace_position = (start, end)

            tabpopup = QComboBox(self.input)
            tabpopup.setMaxVisibleItems(12)
            tabpopup.hide()
            tabpopup.clear()
            tabpopup.addItems(wordlist)
            tabpopup.setCurrentText('')
            tabpopup.activated.connect(self.tabReplaceWord)
            self.tabPopupVisable = True
            tabpopup.showPopup()
        elif result := self.re_functionname.search(line):
            word = result.groups()[0]
            if word in self.notepad.parser.functions:
                func = self.notepad.parser.functions[word]
                helptext = pydoc.plain(pydoc.render_doc(func, title="%s>>>>"))
                helptext = helptext[helptext.find('>>>>')+4:].strip().replace(", /)\n",')\n')
                QToolTip.showText(self.pos() + self.status_bar.pos(), helptext)

    def tabReplaceWord(self):
        newword = self.sender().currentText()  # type: ignore
        print(f"Completed word: '{newword}'")
        start, end = self.replace_position
        text = self.input.toPlainText()
        self.input.setText(text[:start]+newword+text[end:])
        self.processNotepad()
        cursor = self.input.textCursor()
        cursor.setPosition(start+len(newword))
        self.input.setTextCursor(cursor)

    def simplify(self):
        cursor = self.input.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.EndOfLine)
        self.input.setTextCursor(cursor)
        self.input.insertPlainText("\nsimplify(@)")
        self.input.ensureCursorVisible()
        # self.inputScrollbar.setValue(self.input.textCursor().position())

    def expand(self):
        cursor = self.input.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.EndOfLine)
        self.input.setTextCursor(cursor)
        self.input.insertPlainText("\nexpand(@)")
        self.input.ensureCursorVisible()

    def updateStyle(self):
        self.setStyleSheet(f"""
            QTextEdit {{
                background-color: transparent;
                color: {self.settings.color_text};
                padding: 0px;
            }}
            """)
        self.mainwidget.setStyleSheet(f"#Container {{ border-radius: 10px; background: {self.settings.color_background} ;}}")
        self.status.setStyleSheet(f"QLabel {{font-size: 12pt; color: {self.settings.color_status}; }}")
        self.statslabel.setStyleSheet(f"QLabel {{font-size: 12pt; color: {self.settings.color_stats}; }}")
        self.title_bar.title.setStyleSheet(f"QLabel {{font-size: 12pt; color: {self.settings.color_menu}; }}")
        self.title_bar.updateButtonStyle()

    def getNotepadText(self, num):
        return "\n".join(self.notepads[num])

    def getNotepadHeaders(self, trim=0):
        if trim:
            return [x[0][:trim] for x in self.notepads]
        else:
            return [x[0] for x in self.notepads]

    def saveAll(self):
        self.saveCurrentNotepad()
        save_notepads(self.current, self.notepads)
        save_settings(self.settings)

    def addNotepad(self):
        self.notepads.append([''])  # type: ignore
        self.populateNotepadBox()
        self.notepadBox.setCurrentIndex(len(self.notepads)-1)
        self.changeNotepad()

    def deleteNotepad(self):
        confirm = ConfirmationDialog(self, "Delete?", "Delete current notepad?").exec()
        if confirm:
            self.notepads = self.notepads[:self.current] + self.notepads[self.current+1:]
            if not self.notepads:
                self.notepads = ['']
            self.notepadBox.setCurrentIndex(self.current-1)
            self.populateNotepadBox()
            self.changeNotepad()

    def closeEvent(self, event):
        self.saveAll()
        super().closeEvent(event)

    def syncScroll(self, value):
        if self.keepScrollSynced:
            sender = self.sender()
            if sender == self.inputScrollbar:
                self.outputScrollbar.setValue(value)
            elif sender == self.outputScrollbar:
                self.inputScrollbar.setValue(value)
    def populateNotepadBox(self):
        self.notepadBox.clear()
        for i in self.getNotepadHeaders():
            self.notepadBox.addItem(i)

    def showNotepadPopup(self):
        self.saveCurrentNotepad()
        self.populateNotepadBox()
        self.notepadBox.setCurrentIndex(self.current)
        self.notepadBox.activated.connect(self.changeNotepad)
        self.notepadBox.showPopup()

    def duplicateLine(self):
        cursor = self.input.textCursor()
        cursor.select(cursor.SelectionType.LineUnderCursor)
        selectedText = cursor.selectedText()
        cursor.movePosition(cursor.MoveOperation.EndOfLine)
        cursor.insertText('\n'+selectedText)

    def changeNotepad(self):
        if self.notepadBox.currentIndex() != -1:
            # NOTE: self.saveCurrentNotepad() needs to be called in the calling fuction before calling this fuction!
            self.current = self.notepadBox.currentIndex()
            self.input.setText(self.getNotepadText(self.current))
            self.processNotepad()
    def helpPopupMenu(self, event):
        # print(event)
        # obj = self.sender()
        cmenu = QMenu(self)
        basicAct = cmenu.addAction("Basic Usage")
        advAct = cmenu.addAction("Advanced Usage")
        webAct = cmenu.addAction("BeeCalc Website")
        licAct = cmenu.addAction("Licenses")
        licAct.triggered.connect(self.showLicenses)
        aboutAct = cmenu.addAction("About")
        aboutAct.triggered.connect(self.showAboutPopup)
        # quitAct = cmenu.addAction("Quit")
        action = cmenu.exec(self.cursor().pos())
        # action = cmenu.exec(self.mapToGlobal(self.cursor().pos()))

        # if action == quitAct:
        #     QApplication.instance().quit()
        return True
    def openSettings(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("Settings")
        #
        tab_widget = QTabWidget()

        settings_pane = QWidget()
        tab_widget.addTab(settings_pane, "Settings")

        layout = QVBoxLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(10, 10, 10, 10)

        row1 = QHBoxLayout()
        layout.setSpacing(0)
        row1.setContentsMargins(0, 0, 0, 0)
        row2 = QHBoxLayout()
        last_row_spacer = QHBoxLayout()
        layout.addLayout(row1)
        layout.addLayout(row2)
        layout.addLayout(last_row_spacer)
        settings_pane.setLayout(layout)

        font_group = QGroupBox("Font Options")
        row1.addWidget(font_group)
        font_hbox1 = QHBoxLayout()
        font_hbox1.setContentsMargins(5, 5, 5, 5)
        font_group.setLayout(font_hbox1)

        fontBox = QFontComboBox(self)
        fontBox.setCurrentFont(QFont(self.settings.font))
        fontBox.setMinimumContentsLength(8)
        fontBox.currentFontChanged.connect(self.changeFont)
        font_hbox1.addWidget(fontBox)

        fontSizeBox = QComboBox(self)
        fontSizeBox.setEditable(True)
        fontSizeBox.setMinimumContentsLength(2)
        font_sizes = [str(i) for i in range(8, 80, 2)]
        for i in font_sizes:
            fontSizeBox.addItem(i)
        if str(self.settings.font_size) in font_sizes:
            index = font_sizes.index(str(self.settings.font_size))
            fontSizeBox.setCurrentIndex(index)
        else:
            fontSizeBox.setCurrentText(str(self.settings.font_size))
        fontSizeBox.currentTextChanged.connect(self.changeFontSize)
        font_hbox1.addWidget(fontSizeBox)

        boldBtn = QPushButton("Bold")
        boldBtn.setCheckable(True)
        boldBtn.setChecked(True if self.settings.font_bold else False)
        boldBtn.setMaximumWidth(int(self.width()/4))
        boldBtn.clicked.connect(self.changeFontBold)
        font_hbox1.addWidget(boldBtn)

        theme_group = QGroupBox("Theme")
        row1.addWidget(theme_group)
        theme_hbox1 = QHBoxLayout()
        theme_hbox1.setContentsMargins(5, 5, 5, 5)
        theme_group.setLayout(theme_hbox1)

        themeBox = QComboBox(self)
        themeBox.setEditable(False)
        themeBox.setMinimumContentsLength(8)
        themes = list(default_themes.keys())
        for i in themes:
            themeBox.addItem(i)
        index = themes.index(self.settings.theme)  # type: ignore
        themeBox.setCurrentIndex(index)
        themeBox.currentTextChanged.connect(self.changeTheme)
        theme_hbox1.addWidget(themeBox)
        spacer1 = QWidget()
        spacer1.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        row1.addWidget(spacer1)

        num_group = QGroupBox("Number Format")
        row2.addWidget(num_group)
        num_hbox1 = QHBoxLayout()
        num_hbox1.setContentsMargins(5, 5, 5, 5)
        num_group.setLayout(num_hbox1)

        for label in ('Auto', 'Fix'):
            numbtn = QRadioButton(label)
            if label == self.settings.num_fmt:
                numbtn.setChecked(True)
            numbtn.toggled.connect(self.changeNumFormat)
            num_hbox1.addWidget(numbtn)

        self.digitsLabel = QLabel(self.getDigitsLabel())
        num_hbox1.addWidget(self.digitsLabel)

        self.digitsSpinBox = QSpinBox()
        self.digitsSpinBox.setMaximum(16)
        self.digitsSpinBox.setMinimum(1)
        self.digitsSpinBox.setValue(int(self.settings.num_digits))  # type: ignore
        self.digitsSpinBox.valueChanged.connect(self.changeNumDigits)
        num_hbox1.addWidget(self.digitsSpinBox)

        self.alignment = QCheckBox('Align Decimals', self)
        self.alignment.setChecked(True if self.settings.align else False)
        self.changeAlignment()
        self.alignment.stateChanged.connect(self.changeAlignment)
        num_hbox1.addWidget(self.alignment)

        spacer2 = QWidget()
        spacer2.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        row2.addWidget(spacer2)

        spacer_last = QWidget()
        spacer_last.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        last_row_spacer.addWidget(spacer_last)

        #=========== Unit pane ===============
        unit_pane = QWidget()
        tab_widget.addTab(unit_pane, "Units")

        # #=========== Functions pane ===============
        # function_pane = QWidget()
        # tab_widget.addTab(function_pane, "Functions")

        dlg.setLayout(QVBoxLayout())
        dlg.layout().addWidget(tab_widget)
        # dlg.setBaseSize(500,500)
        dlg.setGeometry(self.geometry().topLeft().x(), self.geometry().topLeft().y(), 500, 500)
        dlg.exec()

    def showLicenses(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("Licenses")
        #
        tab_widget = QTabWidget()
        for name, filename in (('BeeCalc', 'LICENSE_BeeCalc'),
                               ('GPLv3', 'GPLv3'),
                               ('PyQt6', 'LICENSE_PyQt6'),
                               ('Qt', 'LICENSE_Qt'),
                               ('Python', 'LICENSE_Python'),
                               ('unitclass', 'LICENSE_unitclass'),
                               ):
            tmp = QPlainTextEdit()
            tab_widget.addTab(tmp, name)
            print(filename)
            lfile = QFile(":"+filename)
            lfile.open(QFile.OpenModeFlag.ReadOnly|QFile.OpenModeFlag.Text)
            tmp.setPlainText(QTextStream(lfile).readAll())

        dlg.setLayout(QVBoxLayout())
        dlg.layout().addWidget(tab_widget)
        # dlg.setBaseSize(500,500)
        dlg.setGeometry(self.geometry().topLeft().x(), self.geometry().topLeft().y(), 500, 500)
        dlg.exec()

        # msg = QMessageBox(text="BeeCalc",parent=self)
        # msg.setIconPixmap(QPixmap("images/beecalc-icon256.png"))
        # # msg.setIcon(QMessageBox.Icon.Information)
        # msg.setStandardButtons(QMessageBox.StandardButton.Ok)#|
        #                     #    QMessageBox.StandardButton.Cancel)
        # msg.setDefaultButton(QMessageBox.StandardButton.Ok)

        # tab_widget = QTabWidget()
        # tab_widget.addTab(QWidget(),"Tab 1")
        # tab_widget.addTab(QWidget(),"Tab 2")

        # msg.setLayout(QVBoxLayout())
        # self.layout().addWidget(self.tab_widget)

    def showAboutPopup(self):
        msg = QMessageBox(text="BeeCalc 0.9.0", parent=self)
        msg.setIconPixmap(QPixmap(":beecalc-icon128.png"))
        # msg.setIconPixmap(QPixmap("resources/beecalc-icon128.png"))
        # msg.setIcon(QMessageBox.Icon.Information)
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)  # |
        #    QMessageBox.StandardButton.Cancel)
        msg.setDefaultButton(QMessageBox.StandardButton.Ok)

        msg.setInformativeText("Copyright (C) 2023  Blake T. Garretson\n\n" +
                            "http://www.beecalc.com\n\nEmail comments to blake@beecalc.com")
        msg.exec()

    def toggleStayOnTop(self):
        self.setWindowFlags(self.windowFlags() ^ Qt.WindowType.WindowStaysOnTopHint)
        self.show()
        if bool(self.windowFlags() & Qt.WindowType.WindowStaysOnTopHint):
            self.title_bar.pin_button.setText("⦿")
        else:
            self.title_bar.pin_button.setText("○")

    def changeAlignment(self):
        self.settings.align = self.alignment.isChecked()
        self.output.setReadOnly(False)
        if self.settings.align:
            self.output.setAlignment(Qt.AlignmentFlag.AlignLeft)
        else:
            self.output.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.processNotepad()

    def changeNumFormat(self):
        btn = self.sender()
        self.settings.num_fmt = btn.text()  # type: ignore
        self.settings.num_digits = self.getDigitsStr()
        self.digitsLabel.setText(self.getDigitsLabel())
        self.digitsSpinBox.setValue(int(self.settings.num_digits))  # type: ignore
        self.processNotepad()

    def changeNumDigits(self, value):
        value = str(value)
        self.settings.num_digits = value
        if self.settings.num_fmt == 'Auto':
            self.settings.num_autodigits = value
        else:
            self.settings.num_fixdigits = value
        self.processNotepad()
    def getDigitsLabel(self):
        if self.settings.num_fmt == 'Auto':
            return " Significant Digits: "
        else:
            return " Decimal Places: "

    def getDigitsStr(self):
        if self.settings.num_fmt == 'Auto':
            return self.settings.num_autodigits
        else:
            return self.settings.num_fixdigits

    def changeTheme(self, theme):
        self.settings = settingsdict(self.settings | default_themes[theme])
        self.syntax_highlighter_in = BeeInputSyntaxHighlighter(
            self.settings, tuple(self.notepad.parser.vars.keys()), self.input.document())
        self.syntax_highlighter_out = BeeOutputSyntaxHighlighter(self.settings, self.output.document())
        self.updateStyle()

    def saveCurrentNotepad(self):
        self.notepads[self.current] = self.input.toPlainText().split("\n")  # type: ignore

    def updateFont(self):
        font = QFont()
        font.setFamily(self.settings.font)  # type: ignore
        font.setPointSize(self.settings.font_size)  # type: ignore
        font.setWeight(800 if self.settings.font_bold else 400)
        font.setBold(True if self.settings.font_bold else False)
        self.input.setFont(font)
        self.output.setFont(font)

    def changeFont(self, font):
        self.settings.font = font.family()
        self.updateFont()

    def changeFontWeight(self, font_weight):
        self.settings.font_weight = font_weight
        self.updateFont()

    def changeFontSize(self, font_size):
        self.settings.font_size = int(font_size)
        self.updateFont()

    def changeFontBold(self, value):
        self.settings.font_bold = True if value else False
        self.updateFont()

    def processNotepad(self):
        # try:
        #     self.input.textChanged.disconnect()
        # except TypeError:
        #     pass
        self.keepScrollSynced = False
        initial_vars = tuple(self.notepad.parser.vars.keys())
        self.notepad.clear()
        self.output.setReadOnly(False)
        all_output = []
        errored = False
        any_errored = False
        widest_entry = 0
        total = []
        for line in self.input.toPlainText().split('\n'):
            try:

                out = self.notepad.append(line)
                if out not in ([], ):  # weed out empty lines
                    if (not isinstance(out, complex)) and math.isclose(out, 0, abs_tol=1e-15):
                        out = 0
                    if isinstance(out, (float, unitclass.Unit)):
                        fmt_str = '{:.'+self.settings.num_digits+num_formats[self.settings.num_fmt]+'}'  # type: ignore
                        text = fmt_str.format(out)
                        zeropt = len(text) - self.re_zeropoint.search(text).start()
                        if zeropt > widest_entry:
                            widest_entry = zeropt
                        outtext = (text, zeropt)
                    elif isinstance(out, Fraction):
                        text = str(out)
                        zeropt = len(text) - self.re_zeropoint.search(text).start()
                        if zeropt > widest_entry:
                            widest_entry = zeropt
                        outtext = (text, zeropt)
                    else:
                        text = f'{out}'
                        zeropt = len(text) - self.re_zeropoint.search(text).start()
                        if zeropt > widest_entry:
                            widest_entry = zeropt
                        outtext = (text, zeropt)
                    try:
                        total.append(float(out))
                    except:
                        pass
                else:
                    outtext = ('', 0)
                if out:
                    self.notepad.parser.vars['ans'] = out
            except SyntaxError as err:
                errstr, errored = str(err), True
                print('err object:', errstr)
                if errstr.startswith("'(' was never closed"):
                    out_msg = "<Unclosed '('>"
                    errstr = "'(' was never closed"
                else:
                    out_msg = '?'
                    errstr = "Invalid syntax"
            except IndexError as err:
                errstr, errored = str(err), True
                out_msg = '?'
                errstr = 'Invalid syntax'
            except ZeroDivisionError as err:
                errstr, errored = str(err), True
                out_msg = '<Zero Division>'
                errstr = "Divide by zero not possible"
            except unitclass.InconsistentUnitsError as err:
                errstr, errored = str(err), True
                print('err2', time.asctime())
                out_msg = '<Inconsistent units>'
            except ValueError as err:
                errstr, errored = str(err), True
                if errstr.startswith("Bad Func"):
                    out_msg = '<Unknown function>'
                    errstr = f"{errstr.split()[2]}: no such function"
                else:
                    out_msg = '?'
                    errstr = errstr
            except unitclass.UnavailableUnit as err:
                errstr, errored = str(err), True
                print('err2', time.asctime())
                out_msg = '<No unit/var>'
                errstr = f"{errstr.split()[1]}: no such unit, variable, or constant"
            except (NameError, TypeError,
                    AttributeError, Exception) as err:
                print('err1', time.asctime())
                errstr, errored = str(err), True
                out_msg = '?'

            if errored:
                print('here1:', out_msg)
                print('here2:', errstr)
                any_errored = True
                self.status_bar.showMessage(errstr, 3000)
                outtext = (out_msg, len(out_msg))
            all_output.append(outtext)
            errored = False
        if not any_errored:
            self.status_bar.clearMessage()

        if self.settings.align:
            all_output = [t+' '*(widest_entry-n) for t, n in all_output]
        else:
            all_output = [t for t, n in all_output]
        self.output.setText("\n".join(all_output))
        orig_cursor = self.output.textCursor()
        self.output.selectAll()
        self.output.setAlignment(Qt.AlignmentFlag.AlignRight)
        # cursor = self.output.textCursor()
        # cursor.clearSelection()
        # self.output.setTextCursor(cursor)
        self.output.setTextCursor(orig_cursor)
        self.output.setReadOnly(True)
        self.outputScrollbar.setValue(self.inputScrollbar.value())
        self.keepScrollSynced = True
        final_vars = tuple(self.notepad.parser.vars.keys())
        if initial_vars != final_vars:
            self.syntax_highlighter_in.updateVars(self.notepad.parser.vars.keys())
            self.syntax_highlighter_in.rehighlight()
        # self.syntax_highlighter_in = BeeInputSyntaxHighlighter(self.settings,tuple(self.notepad.parser.vars.keys()), self.input.document())
        # self.input.textChanged.connect(self.processNotepad)
        n = len(total)
        sum_ = sum(total)
        if n:
            avg = f'{sum_/n:g}'
        else:
            avg = 'N/A'
        self.statslabel.setText(f'n={n} sum={sum_:g} avg={avg}')
        print('processed', time.asctime())

app = QApplication(sys.argv)
app.setStyle('Fusion')
app.setWindowIcon(QIcon(":beecalc-icon.svg"))
window = MainWindow(*initililize_config())
window.show()
app.exec()