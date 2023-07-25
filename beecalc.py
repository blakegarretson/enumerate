import json
import math
import re
import sys
from pathlib import Path

import unitclass
from PyQt6.QtCore import (QCoreApplication, QEvent, QMargins, QPoint,
                          QRegularExpression, QSize, Qt, QTimer)
from PyQt6.QtGui import (QAction, QColor, QFont, QFontDatabase, QIcon,
                         QKeySequence, QPixmap, QShortcut, QSyntaxHighlighter,
                         QTextCharFormat, QTextOption)
from PyQt6.QtWidgets import (QApplication, QCheckBox, QColorDialog, QComboBox,
                             QDialog, QDialogButtonBox, QFontComboBox, QFrame,
                             QGroupBox, QHBoxLayout, QLabel, QLineEdit,
                             QMainWindow, QMessageBox, QPushButton,
                             QRadioButton, QSizePolicy, QSpinBox, QSplitter,
                             QStatusBar, QStyle, QTextEdit, QToolBar,
                             QVBoxLayout, QWidget, QScrollBar)

import beenotepad

# import ctypes
# ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('BTG.BeeCalc.BeeCalc.1')


class ConfirmationDialog(QDialog):
    def __init__(self, parent, title, message):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.buttonBox = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
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
        color_background="#2c292d",
        color_comment="#ff6289",
        color_constant="#ff6289",
        color_function="#aadc76",
        color_operator="#ffd866",
        color_variable="#79dce8",
        color_unit="#ab9df3",
        color_conversion="#fd9967",
        color_error='#fe2020',
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
        color_error='#fe2020',
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
        color_error='#fe2020',
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
        color_error='#fe2020',
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
function_list = sorted(list(parser.functions.keys()))
constant_list = list(parser.constants.keys())
unit_list = []
for name, unit in unitclass._units.items():
    unit_list.extend([name] + (unit['aliases'] if unit['aliases'] else []))
unit_list.sort()


class BeeInputSyntaxHighlighter(QSyntaxHighlighter):
    def __init__(self, settings, variables, parent=None):
        super().__init__(parent)  # type: ignore

        self.rules = []
        self.var_re_str = r'(?<!\w )\b({})\b'
        self.var_re = QRegularExpression(r'|'.join([self.var_re_str.format(w) for w in variables]))
        rule_pairs = [  # order matters below, more general go first and are overridden by more specific
            (r'[a-zA-Z_Ωμ°]+[0-9⁰¹²³⁴⁵⁶⁷⁸⁹]*\b', settings.color_unit),  # units
            (r'\$', settings.color_unit),  # units
            (r'(?<=\d)\s*%', settings.color_unit),  # %
            (r'(?<=\d)\s*%\s*(?=\d)', settings.color_operator),  # %
            ('|'.join([rf'(\b{i}\()' for i in function_list]), settings.color_function),  # function call
            (r'[+-/*=(),]', settings.color_operator),  # operator
            (r'\?', settings.color_error),  # ERROR
            ('|'.join([rf'(\b{i}\b)' for i in constant_list]), settings.color_constant),  # constant
            (r"\b\d+\.*\d*([Ee][-+]?)?\d?", settings.color_text),  # numbers
            (r'(?<=[a-zA-Z_Ωμ°][0-9⁰¹²³⁴⁵⁶⁷⁸⁹])|(?<=[a-zA-Z_Ωμ°@])\s*(( in )|( to ))(?=[a-zA-Z_Ωμ°])', settings.color_conversion),  # conversion
            # (r'(?<=[a-zA-Z_Ωμ°][0-9⁰¹²³⁴⁵⁶⁷⁸⁹])|(?<=[a-zA-Z_Ωμ°@])\s*(( in )|( to ))\s*(?=[a-zA-Z_Ωμ°])', settings.color_conversion),  # conversion
            (r'(?<=%)\s+of\s+', settings.color_conversion),  # conversion
            (r'@', settings.color_variable),  # variable name
            (r'\w+\s*(?==)', settings.color_variable),  # variable name
            (self.var_re,settings.color_variable),  # variable name
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
        self.var_re.setPattern(r'|'.join([self.var_re_str.format(w) for w in variables]))

    def highlightBlock(self, text):
        # print(self.var_re)
        for pattern, char_format in self.rules:
            match_iterator = QRegularExpression(pattern).globalMatch(text)
            while match_iterator.hasNext():
                match = match_iterator.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), char_format)


class BeeOutputSyntaxHighlighter(QSyntaxHighlighter):
    def __init__(self, settings, parent=None):
        super().__init__(parent)  # type: ignore

        self.rules = []
        rule_pairs = [  # order matters below, more general go first and are overridden by more specific
            (r'[a-zA-Z_Ωμ°]+[0-9⁰¹²³⁴⁵⁶⁷⁸⁹]*\b', settings.color_unit),  # units
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
                self.setFormat(match.capturedStart(), match.capturedLength(), char_format)



class MainWindow(QMainWindow):
    re_zeropoint = re.compile(r"[. ]|$")
    re_incomplete = re.compile(r'(.*?\s*)\b(\w+)$')
    # re_incomplete = re.compile(r'\b\w+$')

    def __init__(self, settings, current, notepads):
        super().__init__()

        self.setUnifiedTitleAndToolBarOnMac(True)
        self.settings = settings
        self.current = current
        self.notepads = notepads
        self.updateStyle()  # apply stylesheets for widget defaults
        self.status_bar = QStatusBar(self)
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Welcome to BeeCalc!", 3000)

        self.resize(500, 500)
        self.setWindowTitle("BeeCalc")

        self.notepad = beenotepad.BeeNotepad()
        input_text = self.getNotepadText(self.current)

        font_families = QFontDatabase.families()
        if settings.font not in font_families:
            for fontname in ['Consolas', 'Andale Mono', 'Courier New', 'Courier']:
                if fontname in font_families:
                    self.settings.font = fontname
                    break

        self.input = QTextEdit()
        self.output = QTextEdit()
        splitter = QSplitter()
        splitter.addWidget(self.input)
        splitter.addWidget(self.output)
        splitter.setStretchFactor(0, 5)
        splitter.setStretchFactor(1, 4)
        splitter.setHandleWidth(0)
        splitter.setCollapsible(0, False)
        splitter.setCollapsible(1, False)

        self.updateFont()

        self.input.setWordWrapMode(QTextOption.WrapMode.NoWrap)
        self.output.setWordWrapMode(QTextOption.WrapMode.NoWrap)
        self.syntax_highlighter_in = BeeInputSyntaxHighlighter(self.settings, tuple(self.notepad.parser.vars.keys()), self.input.document())
        self.syntax_highlighter_out = BeeOutputSyntaxHighlighter(self.settings, self.output.document())

        self.inputScrollbar = self.input.verticalScrollBar()
        self.inputScrollbar.hide()
        self.outputScrollbar = self.output.verticalScrollBar()
        self.keepScrollSynced = True
        self.inputScrollbar.valueChanged.connect(self.syncScroll)
        self.outputScrollbar.valueChanged.connect(self.syncScroll)

        self.input.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.output.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.input.horizontalScrollBar().setFixedHeight(0)
        self.output.horizontalScrollBar().setFixedHeight(0)

        # need this for tab completion
        self.tabPopupVisable = False

        layout = QVBoxLayout()
        layout.addWidget(splitter)

        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        container = QWidget()
        container.setLayout(layout)

        self.makeMainToolbar()
        self.makeStyleToolbar()
        self.stylebar.hide()

        # shortcuts
        self.input.installEventFilter(self)
        QShortcut(QKeySequence('Ctrl+D'), self).activated.connect(self.duplicateLine)
        QShortcut(QKeySequence('Ctrl+Shift+N'), self).activated.connect(self.deleteNotepad)
        QShortcut(QKeySequence('Ctrl+N'), self).activated.connect(self.addNotepad)
        QShortcut(QKeySequence('Ctrl+M'), self).activated.connect(self.toggleMenuToolbar)
        QShortcut(QKeySequence('Ctrl+Shift+F'), self).activated.connect(self.toggleStyleToolbar)
        QShortcut(QKeySequence('Ctrl+S'), self).activated.connect(self.saveAll)

        self.setCentralWidget(container)

        # self.input.textChanged.connect(self.processNotepad)
        self.input.cursorPositionChanged.connect(self.processNotepad)
        self.input.setText(input_text)
        cursor = self.input.textCursor()
        cursor.setPosition(len(input_text))
        self.input.setTextCursor(cursor)

        
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
            elif event.key() in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace):
                self.timer = QTimer()
                self.timer.timeout.connect(self.processNotepad)
                self.timer.start(20)
                return super().eventFilter(obj, event)
        return super().eventFilter(obj, event)

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

    def updateStyle(self):
        self.setStyleSheet(f"""
            QTextEdit {{
                background-color: {self.settings.color_background};
                color: {self.settings.color_text};
                padding: 0px;
            }}
            """)
        # padding: 5px 5px 7px 5px;
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

    def toggleStyleToolbar(self):
        if self.stylebar.isVisible():
            self.stylebar.hide()
        else:
            self.stylebar.show()

    def toggleMenuToolbar(self):
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

    def makeMainToolbar(self):
        self.notepadButton = QAction('☰', self)
        self.notepadButton.triggered.connect(self.showNotepadPopup)
        self.notepadButton.setStatusTip("Change notepads")

        self.notepadBox = QComboBox(self)
        self.populateNotepadBox()
        self.notepadBox.setCurrentIndex(self.current)
        self.notepadBox.hide()
        self.notepadAddButton = QAction('+', self)
        self.notepadAddButton.triggered.connect(self.addNotepad)
        self.notepadAddButton.setStatusTip("Creat new notepad")

        self.notepadDeleteButton = QAction('×', self)
        self.notepadDeleteButton.triggered.connect(self.deleteNotepad)
        self.notepadDeleteButton.setStatusTip("Delete current notepad")

        # settings_button = QAction("⚙", self)
        # settings_button.triggered.connect(self.openSettings)

        self.style_button = QAction("Aa", self)
        self.style_button.triggered.connect(self.toggleStyleToolbar)
        self.style_button.setStatusTip("Style options")

        self.menubar = self.addToolBar("Main Menu")
        self.menubar.setMovable(False)
        # self.menubar.setFeatures(Qt.NoDockWidgetFeatures)

        self.menubar.addAction(self.notepadButton)
        self.menubar.addAction(self.notepadAddButton)
        self.menubar.addSeparator()
        self.menubar.addAction(self.style_button)

        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.menubar.addWidget(spacer)
        self.menubar.addAction(self.notepadDeleteButton)

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

    def makeStyleToolbar(self):
        self.stylebar = QToolBar('Style')
        self.addToolBar(Qt.ToolBarArea.BottomToolBarArea, self.stylebar)
        self.stylebar.setMovable(False)
        container = QWidget()
        self.stylebar.addWidget(container)

        layout = QVBoxLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        row1 = QHBoxLayout()
        layout.setSpacing(0)
        row1.setContentsMargins(0, 0, 0, 0)
        row2 = QHBoxLayout()
        layout.addLayout(row1)
        layout.addLayout(row2)
        container.setLayout(layout)

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
        theme_hbox1.setContentsMargins(5,5,5,5)
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
        spacer1.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
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
        self.digitsSpinBox.setMaximum(20)
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
        spacer2.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        row2.addWidget(spacer2)


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
        self.syntax_highlighter_in = BeeInputSyntaxHighlighter(self.settings,tuple(self.notepad.parser.vars.keys()), self.input.document())
        self.syntax_highlighter_out = BeeOutputSyntaxHighlighter(self.settings, self.output.document())
        self.updateStyle()

    def openSettings(self):
        print("SETTINGS!")

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
        self.keepScrollSynced = False
        initial_vars = tuple(self.notepad.parser.vars.keys())
        self.notepad.clear()
        self.output.setReadOnly(False)
        all_output = []
        errored = False
        widest_entry = 0
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

                    else:
                        text = f'{out}'
                        zeropt = len(text) - self.re_zeropoint.search(text).start()
                        if zeropt > widest_entry:
                            widest_entry = zeropt
                        outtext = (text, zeropt)
                else:
                    outtext = ('', 0)
                if out:
                    self.notepad.parser.vars['ans'] = out
            except (ValueError, NameError, SyntaxError,
                    unitclass.UnavailableUnit,
                    unitclass.InconsistentUnitsError, TypeError,
                    AttributeError, Exception) as err:
                self.status_bar.showMessage(str(err), 3000)
                errored = True
                outtext = ('?', 1)
            all_output.append(outtext)
        if not errored:
            self.status_bar.clearMessage()

        if self.settings.align:
            all_output = [t+' '*(widest_entry-n) for t, n in all_output]
        else:
            all_output = [t for t, n in all_output]
        self.output.setText("\n".join(all_output))
        self.output.selectAll()
        self.output.setAlignment(Qt.AlignmentFlag.AlignRight)
        cursor = self.output.textCursor()
        cursor.clearSelection()
        self.output.setTextCursor(cursor)
        self.output.setReadOnly(True)
        self.outputScrollbar.setValue(self.inputScrollbar.value())
        self.keepScrollSynced = True
        final_vars = tuple(self.notepad.parser.vars.keys())
        if initial_vars != final_vars:
            self.syntax_highlighter_in.updateVars(self.notepad.parser.vars.keys())   
            self.syntax_highlighter_in.rehighlight()
        # self.syntax_highlighter_in = BeeInputSyntaxHighlighter(self.settings,tuple(self.notepad.parser.vars.keys()), self.input.document())


app = QApplication(sys.argv)
app.setStyle('Fusion')
app.setWindowIcon(QIcon("beecalc.png"))
window = MainWindow(*initililize_config())
window.show()
app.exec()
