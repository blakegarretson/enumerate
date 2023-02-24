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
import math
import kivy, unitclass
kivy.require('1.10.0')

from kivy.app import App
from kivy.uix.button import Label
from kivy.uix.textinput import TextInput
from kivy.uix.codeinput import CodeInput
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import OptionProperty

colors = {
    'text_input': (0.9,0.9,0.9),
    'text_output': (0.9,0.9,0.9),
    'background_input': (0.2,0.2,0.2),
    'background_output': (0.15,0.2,0.2),
    'cursor': (1,0,0),
}

class BeeCalc(App):
    def build(self):
        self.notebook = bc.BeeNotepad()

        layout_main = BoxLayout(orientation='vertical')
        layout_nb = BoxLayout(orientation='horizontal')
        layout_main.add_widget(layout_nb)

        self.textinput = CodeInput(text='', multiline=True, background_color=colors['background_input'],
                              cursor_color=colors['cursor'], foreground_color=colors['text_input'], 
                              font_name="iosevka-fixed-extendedbold", font_size="36", size_hint=(.7, 1), 
                              style_name='stata-dark')
                            #   style_name='inkpot')
                            #   style_name='monokai')
# ['default', 'emacs', 'friendly', 'friendly_grayscale', 'colorful', 'autumn',
# 'murphy', 'manni', 'material', 'monokai', 'perldoc', 'pastie', 'borland',
# 'trac', 'native', 'fruity', 'bw', 'vim', 'vs', 'tango', 'rrt', 'xcode',
# 'igor', 'paraiso-light', 'paraiso-dark', 'lovelace', 'algol', 'algol_nu',
# 'arduino', 'rainbow_dash', 'abap', 'solarized-dark', 'solarized-light', 'sas',
# 'staroffice', 'stata', 'stata-light', 'stata-dark', 'inkpot', 'zenburn',
# 'gruvbox-dark', 'gruvbox-light', 'dracula', 'one-dark', 'lilypond', 'nord',
# 'nord-darker', 'github-dark']

        #self.textinput.bind(text=self.on_enter)
        self.textinput.bind(text=self.on_text)

        self.textoutput = TextInput(text='', multiline=True, background_color=colors['background_output'],
                              cursor_color=colors['cursor'], foreground_color=colors['text_output'], 
                              font_name="iosevka-fixed-extendedbold", font_size="36", size_hint=(.3, 1))

        layout_nb.add_widget(self.textinput)
        layout_nb.add_widget(self.textoutput)
        # textinput.bind(on_text_validate=self.on_enter)

        return layout_main

    def on_text(self, instance, value):
        # print('The widget', instance, 'have:', value)
        self.notebook.clear()
        self.textoutput.select_all()
        self.textoutput.delete_selection()
        
        for line in value.split('\n'):
            try:
                out = self.notebook.append(line)
                if out not in ([],): # weed out empty lines
                    if math.isclose(out, 0, abs_tol=1e-15):
                        out = 0
                        print("ROUNDED TO 0")
                    self.textoutput.insert_text(f"{out}\n")
                else:
                    self.textoutput.insert_text("\n")
            except (ValueError, NameError, SyntaxError, unitclass.UnavailableUnit, TypeError) as err:
                print(err)
                self.textoutput.insert_text("-\n")
                

beecalc = BeeCalc()
beecalc.run()