import sys
import beenotepad
import math
import json
from pathlib import Path
import unitclass

from PyQt6.QtCore import QSize, Qt
from PyQt6.QtWidgets import (QApplication, QMainWindow, QPushButton, QLabel, QLineEdit, QVBoxLayout, QStyle, QFrame, QSplitter,
                             QFontComboBox, QComboBox, QColorDialog, QToolBar, QMessageBox, QDialog, QDialogButtonBox,
                             QHBoxLayout, QWidget, QPlainTextEdit, QTextEdit)
from PyQt6.QtGui import (QTextCharFormat, QColor, QSyntaxHighlighter, QAction, QPixmap,  QShortcut, QTextOption,
                         QIcon, QFont, QFontDatabase, QKeySequence)
from PyQt6.QtCore import Qt, QRegularExpression, QCoreApplication, QMargins, QPoint

# import ctypes
# ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('BTG.BeeCalc.BeeCalc.1')


class ConfirmationDialog(QDialog):
    def __init__(self, parent, title, message):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.buttonBox = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        self.layout = QVBoxLayout()
        self.layout.addWidget(QLabel(message))
        self.layout.addWidget(self.buttonBox)
        self.setLayout(self.layout)


class settingsdict(dict):
    """Dict class with dot notation for ease of use"""
    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__


default_themes = {
    'Monokai': dict(
        theme='Monokai',
        color_text="#fefaf4",
        color_background="#2c292d",
        color_comment="#ff6289",
        color_constant="#ff6289",
        color_function="#aadc76",
        color_operator="#ffd866",
        color_variable="#79dce8",
        color_unit="#ab9df3",
        color_conversion="#fd9967",
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
    ),
    'Light': dict(
        theme='Light',
        color_text='#000000',
        color_background='#ffffff',
        color_comment='#f25c02',  # #comment
        color_constant='#f92f77',
        color_function='#268509',  # sin(), pi
        color_operator='#f92f77',  # + - / etc
        color_variable='#2c92b0',
        color_unit='#4553bf',
        color_conversion='#fe9720',
    )

}

default_settings = dict(
    fmt_str='.10g',
    font='',
    font_size=16,
    font_bold=False,
) | default_themes['Monokai']

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
function_list = list(parser.functions.keys())
constant_list = list(parser.constants.keys())


class BeeSyntaxHighlighter(QSyntaxHighlighter):
    def __init__(self, settings, parent=None):
        super().__init__(parent)

        self.rules = []

        rule_pairs = [  # order matters below, more general go first and are overridden by more specific
            (r'\w+\s*(?==)', settings.color_variable),  # variable name
            (r'(?<=^|[=*-/+])\s*\w+\s*(?=([=*-/+])|( in )|$)', settings.color_variable),  # variable name
            (r'(?<=(\d)|( in ))\s*[A-Za-z]+[1-4⁰¹²³⁴⁵⁶⁷⁸⁹]*(?=([⋅·+-/* )]|$))', settings.color_unit),  # units
            (r"\b\d+\.*\d*([Ee]|[Ee]-)*\d*", settings.color_text),  # numbers
            ('|'.join([rf'(\b{i}\()' for i in function_list]), settings.color_function),  # function call
            # (r'\w+(?=\()', settings.style_function),  # function call
            (r'@', settings.color_variable),  # variable name
            (r'[+-/*=(),]', settings.color_operator),  # operator
            (r'( in )|( to )', settings.color_conversion),  # conversion
            (r'#.*$', settings.color_comment),  # comment
            ('|'.join([rf'(\b{i}\b)' for i in constant_list]), settings.color_constant),  # comment
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
                self.setFormat(match.capturedStart(), match.capturedLength(), char_format)


class MainWindow(QMainWindow):
    def __init__(self, settings, current, notepads):
        super().__init__()

        # self.setUnifiedTitleAndToolBarOnMac(True)
        self.settings = settings
        self.current = current
        self.notepads = notepads

        self.updateStyle()  # apply stylesheets

        self.resize(500, 500)
        self.setWindowTitle("BeeCalc")

        self.notepad = beenotepad.BeeNotepad()
        input_text = self.getNotepadText(self.current)

        self.font_families = QFontDatabase.families()
        self.font = QFont()
        if settings.font not in self.font_families:
            for fontname in ['Consolas', 'Andale Mono', 'Courier New', 'Courier']:
                if fontname in self.font_families:
                    self.settings.font = fontname
                    break

        # font = QFont(QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont))
        # font.setPointSize(16)
        self.input = QTextEdit()
        self.output = QTextEdit()
        splitter = QSplitter()
        splitter.addWidget(self.input)
        splitter.addWidget(self.output)
        splitter.setStretchFactor(0,3)
        splitter.setStretchFactor(1,2)
        splitter.setHandleWidth(0)
        splitter.setCollapsible(0,False)
        splitter.setCollapsible(1,False)

        self.updateFont()

        self.input.setWordWrapMode(QTextOption.WrapMode.NoWrap)
        self.output.setWordWrapMode(QTextOption.WrapMode.NoWrap)
        self.syntax_highlighter_in = BeeSyntaxHighlighter(self.settings, self.input.document())
        self.syntax_highlighter_out = BeeSyntaxHighlighter(self.settings, self.output.document())

        self.inputScrollbar = self.input.verticalScrollBar()
        self.inputScrollbar.hide()
        self.outputScrollbar = self.output.verticalScrollBar()
        self.inputScrollbar.valueChanged.connect(self.syncScroll)
        self.outputScrollbar.valueChanged.connect(self.syncScroll)

        layout = QVBoxLayout()
        layout.addWidget(splitter)

        # layout = QHBoxLayout()
        # layout.addWidget(self.input, stretch=3)
        # layout.addWidget(self.output, stretch=2)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        container = QWidget()
        container.setLayout(layout)

        self.makeMainToolbar()
        self.makeFormatToolbar()
        self.formatbar.hide()

        # shortcuts
        shortcut_menu = QShortcut(QKeySequence('Ctrl+Q'), self)
        shortcut_menu.activated.connect(self.deleteNotepad)
        shortcut_menu = QShortcut(QKeySequence('Ctrl+N'), self)
        shortcut_menu.activated.connect(self.addNotepad)
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

    def updateStyle(self):
        self.setStyleSheet(f"""
            QTextEdit {{
                background-color: {self.settings.color_background};
                color: {self.settings.color_text};
                padding: 5px 5px 10px 5px;
            }}
                    """)
        #         border: none;

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
        confirm = ConfirmationDialog(self, "Delete?", "Delete current notepad?").exec()
        print(confirm)
        if confirm:
            print("deleting notepad")
            self.notepads = self.notepads[:self.current] + self.notepads[self.current+1:]
            print(self.notepads)
            if not self.notepads:
                self.notepads = ['']
            self.notepadBox.setCurrentIndex(self.current-1)
            self.populateNotepadBox()
            self.changeNotepad()

    def closeEvent(self, event):
        self.saveAll()
        super().closeEvent(event)

    def syncScroll(self, value):
        sender = self.sender()
        if sender == self.inputScrollbar:
            self.output.verticalScrollBar().setValue(value)
        elif sender == self.outputScrollbar:
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
        # font = QFont(QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont))
        # font.setPointSize(18)

        self.notepadButton = QAction('☰', self)
        self.notepadButton.triggered.connect(self.showNotepadPopup)
        # self.notepadButton.setFont(font)

        self.notepadBox = QComboBox(self)
        self.populateNotepadBox()
        self.notepadBox.setCurrentIndex(self.current)
        self.notepadBox.hide()
        # self.notepadBox.currentIndexChanged.connect(self.changeNotepad)
        # self.notepadBox.currentTextChanged.connect(self.changeNotepad)
        # self.notepadBox.setMaximumWidth(200)
        self.notepadAddButton = QAction('+', self)
        self.notepadAddButton.triggered.connect(self.addNotepad)
        # self.notepadAddButton.setFont(font)

        self.notepadDeleteButton = QAction('×', self)
        self.notepadDeleteButton.triggered.connect(self.deleteNotepad)
        # self.notepadDeleteButton.setFont(font)

        # backColor = QAction(QIcon("icons/highlight.png"), "Change background color", self)
        settings_button = QAction("⚙", self)
        # settings_button.setFont(font)
        # settings_button.setShortcut('Ctrl+Q')
        settings_button.triggered.connect(self.openSettings)

        self.format_button = QAction("Aa", self)
        font = QFont(QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont))
        # font.setPointSize(16)
        # self.format_button.setFont(font)
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
        fontBox.setCurrentFont(self.font)
        fontBox.setMinimumContentsLength(10)
        fontBox.currentFontChanged.connect(self.changeFont)

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

        self.bold = QPushButton("Bold")
        self.bold.setCheckable(True)
        self.bold.setChecked(True if self.settings.font_bold else False)
        self.bold.setMaximumWidth(int(self.width()/4))
        self.bold.clicked.connect(self.changeFontBold)

        themeBox = QComboBox(self)
        themeBox.setEditable(False)
        themeBox.setMinimumContentsLength(12)
        themes = list(default_themes.keys())
        for i in themes:
            themeBox.addItem(i)
        index = themes.index(self.settings.theme)
        themeBox.setCurrentIndex(index)
        themeBox.currentTextChanged.connect(self.changeTheme)

        self.formatbar = QToolBar('Format')
        self.addToolBar(Qt.ToolBarArea.BottomToolBarArea, self.formatbar)
        self.formatbar.setMovable(False)

        self.formatbar.addWidget(fontBox)
        self.formatbar.addWidget(fontSizeBox)
        self.formatbar.addWidget(self.bold)
        self.formatbar.addWidget(themeBox)

        # self.formatbar.addAction(fontColor)
        # self.formatbar.addAction(backColor)

        # self.formatbar.addSeparator()

    def changeTheme(self, theme):
        print(theme)
        self.settings = settingsdict(self.settings | default_themes[theme])
        self.syntax_highlighter_in = BeeSyntaxHighlighter(self.settings, self.input.document())
        self.syntax_highlighter_out = BeeSyntaxHighlighter(self.settings, self.output.document())
        self.updateStyle()

    def openSettings(self):
        print("SETTINGS!")

    def saveCurrentNotepad(self):
        self.notepads[self.current] = self.input.toPlainText().split("\n")

    def updateFont(self):
        self.font = QFont()
        self.font.setFamily(self.settings.font)
        self.font.setPointSize(self.settings.font_size)
        self.font.setWeight(800 if self.settings.font_bold else 400)
        self.font.setBold(True if self.settings.font_bold else False)
        self.input.setFont(self.font)
        self.output.setFont(self.font)

    def changeFont(self, font):
        self.settings.font = font.family()
        self.updateFont()

    def changeFontWeight(self, font_weight):
        print("changing weight")
        self.settings.font_weight = font_weight
        self.updateFont()

    def changeFontSize(self, font_size):
        self.settings.font_size = int(font_size)
        self.updateFont()

    def changeFontBold(self):
        self.settings.font_bold = True if self.bold.isChecked() else False
        self.updateFont()

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
        self.output.setText("".join(all_output)[:-1])
        self.output.setReadOnly(True)


app = QApplication(sys.argv)
app.setStyle('Fusion')
app.setWindowIcon(QIcon("beecalc.png"))
window = MainWindow(*initililize_config())
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
