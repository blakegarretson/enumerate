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
import math, re
import kivy, unitclass
kivy.require('1.10.0')

from kivy.app import App
from kivy.uix.button import Label
from kivy.uix.textinput import TextInput
from kivy.uix.codeinput import CodeInput
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import OptionProperty

from pygments.style import Style
from pygments.token import Token, Comment, Name, String, Number, Operator

class BeeStyle(Style):

    styles = {
        Token.Punctuation:  'bold #fff292', # parens, commas
        Comment:            'bold #ff8f73', # #comment
        Name:               'bold #aff1ba', # sin(), pi 
        # Name.Builtin:       '#aff1ba', # abs(), max(), etc.
        String:             'bold #d6a9d5', # 'string'
        Operator:           'bold #77f6ff', # + - / etc
        Number:             'bold #f5f8f8' # 1 1.0
    }

colors = {
    'text_input': (0.9,0.9,0.9),
    'text_output': (0.9,0.9,0.9),
    'background_input': (0.15,0.15,0.15),
    'background_output': (0.15,0.15,0.15),
    'cursor': (1,0,0),
}

settings = {'fmt_str':'.10g',
            'font':'Roboto',
            # 'font':'RobotoMono-Regular',
            'font_size':'18sp',
            'syntaxt_style':'custom'} # 'stata-dark', 'inkpot', 'monokai', etc.
# ['default', 'emacs', 'friendly', 'friendly_grayscale', 'colorful', 'autumn',
# 'murphy', 'manni', 'material', 'monokai', 'perldoc', 'pastie', 'borland',
# 'trac', 'native', 'fruity', 'bw', 'vim', 'vs', 'tango', 'rrt', 'xcode',
# 'igor', 'paraiso-light', 'paraiso-dark', 'lovelace', 'algol', 'algol_nu',
# 'arduino', 'rainbow_dash', 'abap', 'solarized-dark', 'solarized-light', 'sas',
# 'staroffice', 'stata', 'stata-light', 'stata-dark', 'inkpot', 'zenburn',
# 'gruvbox-dark', 'gruvbox-light', 'dracula', 'one-dark', 'lilypond', 'nord',
# 'nord-darker', 'github-dark']

class BeeCalc(App):
    def build(self):
        self.notepad = bc.BeeNotepad()

        layout_main = BoxLayout(orientation='vertical')
        layout_nb = BoxLayout(orientation='horizontal')
        layout_main.add_widget(layout_nb)

        textinput_params = dict(text='', multiline=True, background_color=colors['background_input'],
                              cursor_color=colors['cursor'], foreground_color=colors['text_input'], 
                              font_name=settings['font'], font_size=settings['font_size'], size_hint=(.5, 1))
        if settings['syntaxt_style'] == 'custom':
            textinput_params['style'] = BeeStyle
        else:
            textinput_params['style_name'] = settings['syntaxt_style']
        self.textinput = CodeInput(**textinput_params)
        self.textinput.bind(text=self.on_text)
 
        textoutput_params = dict(text='', multiline=True, background_color=colors['background_output'],
                                cursor_color=colors['cursor'], foreground_color=colors['text_output'], 
                              font_name=settings['font'], font_size=settings['font_size'], size_hint=(.5, 1))
        if settings['syntaxt_style'] == 'custom':
            textoutput_params['style'] = BeeStyle
        else:
            textoutput_params['style_name'] = settings['syntaxt_style']
        self.textoutput = CodeInput(**textoutput_params)


        layout_nb.add_widget(self.textinput)
        layout_nb.add_widget(self.textoutput)
        # textinput.bind(on_text_validate=self.on_enter)

        return layout_main

    def on_text(self, instance, value):
        # print('The widget', instance, 'have:', value)
        self.notepad.clear()
        self.textoutput.select_all()
        self.textoutput.delete_selection()
        
        for line in value.split('\n'):
            try:
                out = self.notepad.append(line)
                if out not in ([],): # weed out empty lines
                    if math.isclose(out, 0, abs_tol=1e-15):
                        out = 0
                    if isinstance(out, (float,unitclass.Unit)):
                        fmt_str = '{:'+settings["fmt_str"]+'}\n'
                        outtext = fmt_str.format(out)
                    else:
                        outtext = f'{out}\n'
                    self.textoutput.insert_text(outtext)
                else:
                    self.textoutput.insert_text("\n")
                if out:
                    self.notepad.parser.vars['ans'] = out
            except (ValueError, NameError, SyntaxError, unitclass.UnavailableUnit, 
                    unitclass.InconsistentUnitsError, TypeError, AttributeError, Exception) as err:
                print(err)
                self.textoutput.insert_text("?\n")
                

beecalc = BeeCalc()
beecalc.run()