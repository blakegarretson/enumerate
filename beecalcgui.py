import kivy
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

        layout_main = BoxLayout(orientation='vertical')
        layout_nb = BoxLayout(orientation='horizontal')
        layout_main.add_widget(layout_nb)

        textinput = CodeInput(text='Hello world', multiline=True, background_color=colors['background_input'],
                              cursor_color=colors['cursor'], foreground_color=colors['text_input'], 
                              font_name="iosevka-fixed-extendedbold", font_size="36", size_hint=(.7, 1), 
                              style_name='inkpot')
                            #   style_name='monokai')
# ['default', 'emacs', 'friendly', 'friendly_grayscale', 'colorful', 'autumn',
# 'murphy', 'manni', 'material', 'monokai', 'perldoc', 'pastie', 'borland',
# 'trac', 'native', 'fruity', 'bw', 'vim', 'vs', 'tango', 'rrt', 'xcode',
# 'igor', 'paraiso-light', 'paraiso-dark', 'lovelace', 'algol', 'algol_nu',
# 'arduino', 'rainbow_dash', 'abap', 'solarized-dark', 'solarized-light', 'sas',
# 'staroffice', 'stata', 'stata-light', 'stata-dark', 'inkpot', 'zenburn',
# 'gruvbox-dark', 'gruvbox-light', 'dracula', 'one-dark', 'lilypond', 'nord',
# 'nord-darker', 'github-dark']

        textinput.bind(text=self.on_text)

        textoutput = TextInput(text='Output', multiline=True, background_color=colors['background_output'],
                              cursor_color=colors['cursor'], foreground_color=colors['text_output'], 
                              font_name="iosevka-fixed-extendedbold", font_size="36", size_hint=(.3, 1))

        layout_nb.add_widget(textinput)
        layout_nb.add_widget(textoutput)
        # textinput.bind(on_text_validate=self.on_enter)
    
        return layout_main

    def on_text(self, instance, value):
        print('The widget', instance, 'have:', value)


beecalc = BeeCalc()
beecalc.run()