import sys
import beenotepad
import math
import json
from pathlib import Path
import unitclass

from PyQt6.QtCore import QSize, Qt
from PyQt6.QtWidgets import (QApplication, QMainWindow, QPushButton, QLabel, QLineEdit, QVBoxLayout, QStyle,
                             QFontComboBox, QComboBox, QColorDialog, QToolBar,
                             QHBoxLayout, QWidget, QPlainTextEdit, QTextEdit)
from PyQt6.QtGui import (QTextCharFormat, QColor, QSyntaxHighlighter, QAction, QPixmap,  QShortcut, QTextOption,
                         QIcon, QFont, QFontDatabase, QKeySequence)
from PyQt6.QtCore import Qt, QRegularExpression, QCoreApplication

# import ctypes
# ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('BTG.BeeCalc.BeeCalc.1')

default_settings = dict(
    fmt_str='.10g',
    font='data/fonts/DejaVuSans.ttf',
    font_size=18,
    cursor_width=4,
    lines_to_scroll=2,
    colors=dict(text_input='#e6e6e6',
                text_output='#e6e6e6',
                background_input='#262626',
                background_output='#262626',
                cursor='#ffa342'),
    styles=dict(
        punctuation='#fff292',  # parens, commas
        comment='#ff8f73',  # #comment
        name='#aff1ba',  # sin(), pi
        string='#d6a9d5',  # 'string'
        operator='#77f6ff',  # + - / etc
        number='#f5f8f8'  # 1 1.0
    ))

default_notepads = {
    'current':
    0,
    'notepads': [[
        '# Welcome to BeeCalc!', '2+3', '@+1', '2 lb in grams',
        'width = 20 ft', 'length = 10 ft', 'area = length*width', '@ in in2',
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
        json.dump(settings, jsonfile, indent=2)


def load_settings():
    with beecalc_settings.open() as jsonfile:
        return json.load(jsonfile)


def initililize_config():
    if not beecalc_home.exists():
        beecalc_home.mkdir(parents=True)

    if beecalc_settings.exists():
        settings = load_settings()
    else:
        settings = default_settings.copy()
        save_settings(settings)

    if not beecalc_notepads.exists():
        save_default_notepads()
    current, notepads = load_notepads()

    return settings, current, notepads


class BeeSyntaxHighlighter(QSyntaxHighlighter):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.rules = []

        rule_pairs = [
            (r'[A-Za-z]+(?:([+-/* ]|$))', '#a457a3'),  # units
            (r"\b\d+\.*\d*([Ee]|[Ee]-)*\d*", "#d6a9d5"),  # numbers
            (r'\w+(?:\()', '#aff1ba'),  # function call
            (r'\w+(?:\s*=)', '#3e93e9'),  # variable name
            (r'[(),]', '#fff292'),  # punctuation e.g. parens, commas
            (r'[+-/*=]', '#77f6ff'),  # operator
            (r'( in )|( to )', '#ff738a'),  # conversion
            (r'#.*$', '#ff8f73'),  # comment
        ]
        test = """
123
123.123
123.2e43
1e3
3e-3
4 g in lb
# comment
4 # comment
sin(34 deg)
a = 4
2+3-4/4
(43+43)
round(1.23, 4)
"""
        for regexp, color in rule_pairs:
            rule_format = QTextCharFormat()
            rule_format.setForeground(QColor(color))
            self.rules.append((QRegularExpression(regexp), rule_format))

    def highlightBlock(self, text):
        for pattern, char_format in self.rules:
            match_iterator = QRegularExpression(pattern).globalMatch(text)
            while match_iterator.hasNext():
                match = match_iterator.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), char_format)


# Subclass QMainWindow to customize your application's main window
class MainWindow(QMainWindow):
    def __init__(self, settings, current, notepads):
        super().__init__()

        self.settings = settings
        self.current = current
        self.notepads = notepads

        self.resize(400, 500)
        self.setWindowTitle("BeeCalc")

        self.notepad = beenotepad.BeeNotepad()
        input_text = self.getNotepadText(self.current)

        common_options = dict()

        font = QFont(QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont))
        font.setPointSize(16)
        self.input = QTextEdit()
        self.input.setFont(font)
        self.input.setWordWrapMode(QTextOption.WrapMode.NoWrap)

        # self.input = QTextEdit(**(common_options | dict(text=input_text)))
        self.syntax_highlighter_in = BeeSyntaxHighlighter(self.input.document())

        self.output = QTextEdit()
        self.output.setFont(font)
        self.output.setWordWrapMode(QTextOption.WrapMode.NoWrap)
        self.syntax_highlighter_out = BeeSyntaxHighlighter(self.output.document())

        self.input.verticalScrollBar().valueChanged.connect(self.syncScroll)
        self.output.verticalScrollBar().valueChanged.connect(self.syncScroll)

        # self.output.setCurrentFont(font)
        # self.input.textChanged.connect(self.output.setText)
        layout = QHBoxLayout()
        layout.addWidget(self.input, stretch=3)
        layout.addWidget(self.output, stretch=2)
        layout.setSpacing(0)

        container = QWidget()
        container.setLayout(layout)

        self.makeMainToolbar()
        self.makeFormatToolbar()
        self.formatbar.hide()

        # shortcuts
        shortcut_menu = QShortcut(QKeySequence('Ctrl+M'), self)
        shortcut_menu.activated.connect(self.toggleMenuToolbar)
        shortcut_format = QShortcut(QKeySequence('Ctrl+Shift+F'), self)
        shortcut_format.activated.connect(self.toggleFormatToolbar)
        shortcut_debug = QShortcut(QKeySequence('Ctrl+Shift+D'), self)
        shortcut_debug.activated.connect(self.debug)
        shortcut_save = QShortcut(QKeySequence('Ctrl+S'), self)
        shortcut_save.activated.connect(self.saveAll)

        self.setCentralWidget(container)

        self.input.textChanged.connect(self.processNotepad)
        self.input.setText(input_text)

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
        self.notepads.append([''])
        self.populateNotepadBox()
        self.notepadBox.setCurrentIndex(len(self.notepads)-1)
        self.changeNotepad()

    def deleteNotepad(self):
        self.notepads = self.notepads[:self.current] + self.notepads[self.current+1:]
        if not self.notepads:
            self.notepads = ['']
        self.notepadBox.setCurrentIndex(self.current-1)
        self.changeNotepad()

    def closeEvent(self, event):
        self.saveAll()
        super().closeEvent(event)

    def syncScroll(self, value):
        print('syncing scroll')
        sender = self.sender()
        if sender == self.input:
            self.output.verticalScrollBar().setValue(value)
        elif sender == self.output:
            self.input.verticalScrollBar().setValue(value)

    def debug(self):
        print(dir(self.input))

    def toggleFormatToolbar(self):
        if self.formatbar.isVisible():
            self.formatbar.hide()
        else:
            self.formatbar.show()

    def toggleMenuToolbar(self):
        print('TRIGGER')
        if self.menubar.isVisible():
            self.menubar.hide()
        else:
            self.menubar.show()

    def populateNotepadBox(self):
        self.notepadBox.clear()
        for i in self.getNotepadHeaders():
            self.notepadBox.addItem(i)

    def showNotepadPopup(self):
        self.saveCurrentNotepad()
        self.populateNotepadBox()
        self.notepadBox.setCurrentIndex(self.current)
        # self.notepadBox.currentIndexChanged.connect(self.test)
        self.notepadBox.currentIndexChanged.connect(self.changeNotepad)
        self.notepadBox.showPopup()

    def test(self):
        print(f'index changed {self.notepadBox.currentIndex()}')
    def changeNotepad(self):
        if self.notepadBox.currentIndex() != -1:
            # NOTE: self.saveCurrentNotepad() needs to be called in the calling fuction before calling this fuction!
            self.current = self.notepadBox.currentIndex()
            print(self.notepadBox.currentIndexChanged.signal)
            # # this is a kludge for when disconnect is called without being connected first
            # self.notepadBox.currentIndexChanged.connect(self.changeNotepad)
            # self.notepadBox.currentIndexChanged.disconnect()
            self.input.setText(self.getNotepadText(self.current))
            self.processNotepad()
        # else:
        # this is a kludge for when disconnect is called without being connected first
        self.notepadBox.currentIndexChanged.connect(self.changeNotepad)
        self.notepadBox.currentIndexChanged.disconnect()

    def makeMainToolbar(self):
        # self.menu_toggle = QAction('', self)
        # self.menu_toggle.triggered.connect(self.toggle_menu_toolbar)
        # self.menu_toggle.setShortcut('Ctrl+Shift+M')
        font = QFont(QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont))
        font.setPointSize(18)

        self.notepadButton = QAction('☰', self)
        self.notepadButton.triggered.connect(self.showNotepadPopup)
        self.notepadButton.setFont(font)

        self.notepadBox = QComboBox(self)
        self.populateNotepadBox()
        self.notepadBox.setCurrentIndex(self.current)
        # self.notepadBox.currentIndexChanged.connect(self.changeNotepad)
        # self.notepadBox.currentTextChanged.connect(self.changeNotepad)
        # self.notepadBox.setMaximumWidth(200)
        self.notepadAddButton = QAction('+', self)
        self.notepadAddButton.triggered.connect(self.addNotepad)
        self.notepadAddButton.setFont(font)

        self.notepadDeleteButton = QAction('×', self)
        self.notepadDeleteButton.triggered.connect(self.deleteNotepad)
        self.notepadDeleteButton.setFont(font)

        # backColor = QAction(QIcon("icons/highlight.png"), "Change background color", self)
        settings_button = QAction("⚙", self)
        settings_button.setFont(font)
        # settings_button.setShortcut('Ctrl+Q')
        settings_button.triggered.connect(self.openSettings)

        self.format_button = QAction("⚒", self)
        font = QFont(QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont))
        font.setPointSize(18)
        self.format_button.setFont(font)
        # backColor.setShortcut('Ctrl+Q')
        self.format_button.triggered.connect(self.toggleFormatToolbar)

        self.menubar = self.addToolBar("Main Menu")
        self.menubar.setMovable(False)
        # self.menubar.setFeatures(Qt.NoDockWidgetFeatures)

        self.menubar.addAction(self.notepadButton)
        self.menubar.addAction(self.notepadAddButton)
        self.menubar.addAction(self.notepadDeleteButton)
        self.menubar.addSeparator()
        # self.menubar.addWidget(QLabel("Notepad:"))
        # self.menubar.addWidget(self.notepadBox)
        self.menubar.addAction(settings_button)
        self.menubar.addAction(self.format_button)
        self.menubar.addSeparator()

    def makeFormatToolbar(self):
        fontBox = QFontComboBox(self)
        fontBox.currentFontChanged.connect(self.changeFont)

        fontSize = QComboBox(self)
        fontSize.setEditable(True)

        # Minimum number of chars displayed
        fontSize.setMinimumContentsLength(3)

        fontSize.activated.connect(self.fontSize)

        # Typical font sizes
        fontSizes = ['6', '7', '8', '9', '10', '11', '12', '13', '14',
                     '15', '16', '18', '20', '22', '24', '26', '28',
                     '32', '36', '40', '44', '48', '54', '60', '66',
                     '72', '80', '88', '96']

        for i in fontSizes:
            fontSize.addItem(i)

        # icon = self.style().standardIcon(QStyle.StandardPixmap.SP_TrashIcon)
        # fontColor = QAction(icon, "Change font color", self)
        # fontColor.triggered.connect(self.change_font_color)

        # backColor = QAction("⚙", self)
        # font = QFont(QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont))
        # font.setPointSize(18)
        # backColor.setFont(font)
        # backColor.triggered.connect(self.highlight)

        self.formatbar = QToolBar('Format')
        self.addToolBar(Qt.ToolBarArea.BottomToolBarArea, self.formatbar)
        self.formatbar.setMovable(False)

        # self.formatbar = self.addToolBar("Format")

        self.formatbar.addWidget(fontBox)
        self.formatbar.addWidget(fontSize)

        self.formatbar.addSeparator()

        # self.formatbar.addAction(fontColor)
        # self.formatbar.addAction(backColor)

        self.formatbar.addSeparator()

    def openSettings(self):
        print("SETTINGS!")

    def saveCurrentNotepad(self):
        self.notepads[self.current] = self.input.toPlainText().split("\n")

    def changeFont(self, font):
        self.input.setFont(font)
        self.output.setFont(font)

    def fontSize(self, fontsize):
        self.input.setFontPointSize(int(fontsize))

    # def change_font_color(self):
    #     color = QColorDialog.getColor()
    #     self.input.setTextColor(color)

    def processNotepad(self):
        self.notepad.clear()
        self.output.setReadOnly(False)
        all_output = []
        for line in self.input.toPlainText().split('\n'):
            try:
                out = self.notepad.append(line)
                if out not in ([], ):  # weed out empty lines
                    if (not isinstance(out, complex)) and math.isclose(out, 0, abs_tol=1e-15):
                        out = 0
                    if isinstance(out, (float, unitclass.Unit)):
                        fmt_str = '{:' + self.settings["fmt_str"] + '}\n'
                        outtext = fmt_str.format(out)
                    else:
                        outtext = f'{out}\n'
                else:
                    outtext = "\n"
                if out:
                    self.notepad.parser.vars['ans'] = out
            except (ValueError, NameError, SyntaxError,
                    unitclass.UnavailableUnit,
                    unitclass.InconsistentUnitsError, TypeError,
                    AttributeError, Exception) as err:
                print(err)
                outtext = "?\n"
            all_output.append(outtext)
        self.output.setText("".join(all_output).rstrip())
        self.output.setReadOnly(True)


app = QApplication(sys.argv)
app.setStyle('Fusion')
window = MainWindow(*initililize_config())
app.setWindowIcon(QIcon("beecalc.png"))
window.show()
app.exec()


# app.setStyleSheet("QWidget { color: #e6e6e6; background-color: #262626; }")

# button = QPushButton('One')
# button.setStyleSheet(
#     "background-color: #262626; "
#     "font-family: times; "
#     "font-size: 20px;"
# )

# self.setStyleSheet("""
#             QWidget {
#                 background-color: #333333;
#                 color: #ffffff;
#             }
#             QPushButton {
#                 background-color: #555555;
#                 color: #ffffff;
#                 border: none;
#                 padding: 5px;
#             }
#             QPushButton:hover {
#                 background-color: #666666;
#             }
#             QLineEdit {
#                 background-color: #444444;
#                 color: #ffffff;
#             }
#         """)
