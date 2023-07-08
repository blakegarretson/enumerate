"""
Bee Calc: Cross-platform notebook calculator with robust unit support

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
import beecalc as bc
import math, os, re, json
from pathlib import Path
import unitclass
import kivy
kivy.require('1.10.0')
from kivy.app import App
from kivy.config import Config
Config.set(section='kivy', option='default_font', value=['DejaVuSans','data/fonts/DejaVuSans.ttf'])
Config.set(section='kivy', option='window_icon', value='beecalc.png')
from kivy.uix.button import Label, Button
from kivy.uix.textinput import TextInput
from kivy.uix.codeinput import CodeInput
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.spinner import Spinner, SpinnerOption
from kivy.properties import OptionProperty
from kivy.core.window import Window
from kivy.metrics import dp, sp

from pygments.style import Style
from pygments.token import Token, Comment, Name, String, Number, Operator

default_settings = {
    'fmt_str': '.10g',
    'font': 'data/fonts/DejaVuSans.ttf',
    'font_size': 18,
    'syntaxt_style': 'custom',
    'colors':{
            'text_input': (0.9, 0.9, 0.9),
            'text_output': (0.9, 0.9, 0.9),
            'background_input': (0.15, 0.15, 0.15),
            'background_output': (0.15, 0.15, 0.15),
            'cursor': (1, 0, 0)
    },
    'styles':{
        'punctuation': '#fff292',  # parens, commas
        'comment': '#ff8f73',  # #comment
        'name': '#aff1ba',  # sin(), pi 
        'string': '#d6a9d5',  # 'string'
        'operator': '#77f6ff',  # + - / etc
        'number': '#f5f8f8'  # 1 1.0
    }
}  # 'stata-dark', 'inkpot', 'monokai', etc.
# ['default', 'emacs', 'friendly', 'friendly_grayscale', 'colorful', 'autumn',
# 'murphy', 'manni', 'material', 'monokai', 'perldoc', 'pastie', 'borland',
# 'trac', 'native', 'fruity', 'bw', 'vim', 'vs', 'tango', 'rrt', 'xcode',
# 'igor', 'paraiso-light', 'paraiso-dark', 'lovelace', 'algol', 'algol_nu',
# 'arduino', 'rainbow_dash', 'abap', 'solarized-dark', 'solarized-light', 'sas',
# 'staroffice', 'stata', 'stata-light', 'stata-dark', 'inkpot', 'zenburn',
# 'gruvbox-dark', 'gruvbox-light', 'dracula', 'one-dark', 'lilypond', 'nord',
# 'nord-darker', 'github-dark']

default_notepads = {'current':0,
                   'notepads':[
                                ['# Welcome to BeeCalc!',
                                 '2+3',
                                 '@+1',
                                 '2 lb in grams',
                                 'width = 20 ft', 
                                 'length = 10 ft',
                                 'area = length*width', 
                                 '@ in in2',
                                 'sin(90deg)',
                                  'sin(pi/2)'],
                                ['a=1',
                                 'b=2 # this is a comment',
                                 'c=3',
                                 'total=a+b+c'
                                 ]
                   ]
}

settings = default_settings.copy()

beecalc_home = Path().home() / ".config" / "beecalc"
beecalc_settings = beecalc_home / 'settings.json'
beecalc_notepads = beecalc_home / 'notepads.json'

        
def save_default_notepads():
    with beecalc_notepads.open('w') as jsonfile:
        json.dump(default_notepads, jsonfile, indent=2)

def save_notepads(current, notepads):
    with beecalc_notepads.open('w') as jsonfile:
        json.dump({'current':current, 'notepads':notepads}, jsonfile, indent=2)

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

    if  beecalc_settings.exists():
        settings = load_settings()
    else:
        settings = default_settings.copy()
        save_settings(settings)

    if not beecalc_notepads.exists():
        save_default_notepads()
    current, notepads = load_notepads()

    return settings, current, notepads

settings, current, notepads = initililize_config()

def get_notepad_text(num):
    return "\n".join(notepads[num])

def get_notepad_headers():
    trim = 10
    return [f'{x}: {y}' for x,y in enumerate([x[0][:trim] for x in notepads], 1)]

def get_font_size(multiplier=1):
    return f'{settings["font_size"]*multiplier}sp'

class BeeStyle(Style):

    styles = {
        Token.Punctuation: settings['styles']['punctuation'],  # parens, commas
        Comment: settings['styles']['comment'],  # #comment
        Name: settings['styles']['name'],  # sin(), pi 
        String: settings['styles']['string'],  # 'string'
        Operator: settings['styles']['operator'],  # + - / etc
        Number: settings['styles']['number']  # 1 1.0
    }

class BeeCalc(App):

    def build(self):
        self.notepad = bc.BeeNotepad()
        input_text = get_notepad_text(current)

        layout_main = BoxLayout(orientation='vertical')
        layout_nb = BoxLayout(orientation='horizontal')
        mb_size = dp(30)
        layout_menubar = BoxLayout(orientation='horizontal', size=(0,mb_size),size_hint=(None, None))

        layout_menubar.add_widget(Button(text='⌘', size=(mb_size,mb_size), size_hint=(None, None)))
        layout_menubar.add_widget(Button(text='+', size=(mb_size,mb_size), size_hint=(None, None)))
        layout_menubar.add_widget(Button(text='▢', size=(mb_size,mb_size), size_hint=(None, None)))
        layout_menubar.add_widget(Button(text='⚙', size=(mb_size,mb_size), size_hint=(None, None)))
        layout_menubar.add_widget(Button(text='⚒', size=(mb_size,mb_size), size_hint=(None, None)))
        layout_menubar.add_widget(Button(text='☰', size=(mb_size,mb_size), size_hint=(None, None)))
        layout_menubar.add_widget(Button(text='⚒', size=(mb_size,mb_size), size_hint=(None, None)))
        layout_menubar.add_widget(Button(text='☑', size=(mb_size,mb_size), size_hint=(None, None)))
        layout_menubar.add_widget(Button(text='☒', size=(mb_size,mb_size), size_hint=(None, None)))
        layout_menubar.add_widget(Button(text='☐', size=(mb_size,mb_size), size_hint=(None, None)))
        headers = get_notepad_headers()
        self.nplist = Spinner(
                    text=headers[current],
                    values=headers,
                    size_hint=(None, None),
                    size=(dp(100), dp(30)),
                    pos_hint={'center_x': 1, 'center_y': 0.5},
                    sync_height=True,
                    text_autoupdate=False)
        #nblist.add_widget(SpinnerOption(text="One"))
        self.nplist.bind(text=self.on_notepad_change)
        layout_menubar.add_widget(self.nplist)


        layout_main.add_widget(layout_menubar)
        layout_main.add_widget(layout_nb)

        textinput_params = dict(text=input_text,
                                multiline=True,
                                background_color=settings['colors']['background_input'],
                                cursor_color=settings['colors']['cursor'],
                                foreground_color=settings['colors']['text_input'],
                                # font_name=settings['font'],
                                font_size=get_font_size(),
                                size_hint=(.6, 1),
                                line_spacing=get_font_size(0.2))
        if settings['syntaxt_style'] == 'custom':
            textinput_params['style'] = BeeStyle
        else:
            textinput_params['style_name'] = settings['syntaxt_style']
        self.textinput = CodeInput(**textinput_params)
        self.textinput.bind(text=self.on_text)

        output_text = "".join(self.process_notepad(text=input_text,getoutput=True))
        textoutput_params = dict(text=output_text,
                                 multiline=True,
                                 background_color=settings['colors']['background_output'],
                                 cursor_color=settings['colors']['cursor'],
                                 foreground_color=settings['colors']['text_output'],
                                #  font_name=settings['font'],
                                 font_size=get_font_size(),
                                 size_hint=(.4, 1),
                                line_spacing=get_font_size(0.2))
        if settings['syntaxt_style'] == 'custom':
            textoutput_params['style'] = BeeStyle
        else:
            textoutput_params['style_name'] = settings['syntaxt_style']
        self.textoutput = CodeInput(**textoutput_params)

        layout_nb.add_widget(self.textinput)
        layout_nb.add_widget(self.textoutput)
        # textinput.bind(on_text_validate=self.on_enter)
        #self.textoutput.insert_text("DSDSSD")
        return layout_main
    
    def on_start(self, **kwargs):
        pass

    def save_current_notepad(self):
        notepads[current] = self.textinput.text.split("\n")

    def switch_notepad(self, number):
        self.save_current_notepad()
        global current
        current = number
        text = get_notepad_text(number)
        self.textinput.text = text
        self.process_notepad()


    def on_notepad_change(self, instance, value):
        print(value)
        number = int(value.split(":")[0])-1
        self.switch_notepad(number)

    def on_text(self, instance, value):
        # print('The widget', instance, 'have:', value)
        self.process_notepad()

    def process_notepad(self, text=False, getoutput=False):
        print("RUN")
        self.notepad.clear()
        if not getoutput:
            self.textoutput.select_all()
            self.textoutput.delete_selection()
        print(self.textinput.text)
        if not text:
            text = self.textinput.text
        all_output = []
        for line in text.split('\n'):
            try:
                out = self.notepad.append(line)
                if out not in ([], ):  # weed out empty lines
                    if (not isinstance(out, complex)) and math.isclose(out, 0, abs_tol=1e-15):
                        out = 0
                    if isinstance(out, (float, unitclass.Unit)):
                        fmt_str = '{:' + settings["fmt_str"] + '}\n'
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
            if not getoutput:
                self.textoutput.insert_text(outtext)
            else:
                all_output.append(outtext)
        return all_output

    def on_stop(self, **kwargs):
        self.save_current_notepad()
        save_notepads(current, notepads)
        save_settings(settings)


Window.size = (dp(300), dp(250))

beecalc = BeeCalc()
beecalc.run()