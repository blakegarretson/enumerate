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
import ast
import math
import operator
import re
from unitclass import Unit
import unitclass


class BeeParser():
    num_re = r"([.]\b(?:\d+)(?:[Ee]([+-])?(?:\d+)?)?\b)|(?:\b(?:\d+)(?:[.,]?(?:\d+))?(?:[Ee](?:[+-])?(?:\d+)?)?)"
    # num_re = r"((?:[-+])?[.,]\b(?:\d+)(?:[Ee]([+-])?(?:\d+)?)?\b)|(?:(?:[+-])?\b(?:\d+)(?:[.,]?(?:\d+))?(?:[Ee](?:[+-])?(?:\d+)?)?)"
    unit_re = re.compile(r"(?<!Unit\(')(?<![a-zA-Z])(" + num_re + r")?\s*([a-zA-Z_Ωμ°]+(?![(])(?:(?:\^|\*\*)?[0-9]+)*)(?:\b|$|(?=\)))(?!\s*[=])")
    # unit_re = re.compile(r"(?<!Unit\(')(?<![a-zA-Z])(" + num_re + r")?\s*([a-zA-Z_Ωμ°]+(?![(])(?:(?:\^|(?:\*\*))?[0-9]+)?)\b(?!\s*[=])")
    # unit_percent = re.compile(r"(?<!Unit\(')((?<![a-zA-Z])\(*\s*[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?\s*\)*)(?![eE][^a-zA-Z])\s*(%\)*)(?!\s*[0-9])" )
    percent_re = re.compile(r"%(?!\s*\d)")
    # unit_re = re.compile(r"(?<!Unit\(')((?<![a-zA-Z])[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?)(?![eE][^a-zA-Z])\s*((?:[a-zA-Z_Ωμ°]+(?:\^|\*\*)*[0-9]*)|(?:%(?!\s+-*\+*[0-9])))" )
    in_re = re.compile(r"([a-zA-Z]\d*\)*)\s+in\s+(?=[(a-zA-Z]+)")
    money_re = re.compile(r"\$([0-9.]+)\b")
    money_to_re = re.compile(r" to\s+\$")
    to_re = re.compile(r"\s+to\s+")
    of_re = re.compile(r"%\s+of\s+")
    factorial_re = re.compile(r"(\d+)\s*!")
    # names_re = re.compile(r"\b[a-zA-Z]+\b(?!\s*=)")
    names_re = re.compile(r"(?<![\w.@)] )\b([a-zA-Z]\w*)\b(?!=| =)")
    # (?<![\d.)])\s*(\b[a-zA-Z]\w*\b)\s*(?!=)
    parens_math = re.compile(r"(?<!\w)\([0-9 +-/*^]+?\)")
    extra_spaces_re = re.compile(r"\s\s+")
    eliminate_spaces_re = re.compile(r" (?=\))|(?<=\() | (?=[+\-*/^])|(?<=[+\-*/^]) ")
    double_in_re = re.compile(r" in in\s+(?!$)")

    to_specials = str.maketrans("0123456789*", "⁰¹²³⁴⁵⁶⁷⁸⁹·")
    from_specials = str.maketrans("⁰¹²³⁴⁵⁶⁷⁸⁹⋅·×", "0123456789***")

    def __init__(self, vars=None) -> None:
        self.vars = vars or {}

        self.constants = {
            'e': math.e,
            'pi': math.pi,
            'π': math.pi,
            'φ': (1 + math.sqrt(5)) / 2,
            'phi': (1 + math.sqrt(5)) / 2,
            'tau': math.tau,
            'τ': math.tau,
        }

        self.operations = {
            ast.Add: operator.add,
            ast.Sub: operator.sub,
            ast.Mult: operator.mul,
            ast.Div: operator.truediv,
            ast.FloorDiv: operator.floordiv,
            ast.Mod: operator.mod,
            ast.Pow: operator.pow,
            ast.LShift: operator.lshift,
            ast.RShift: operator.rshift,
            ast.BitOr: operator.or_,
            # ast.BitXor: operator.pow,
            ast.BitAnd: operator.and_,
            ast.USub: operator.neg,
            ast.UAdd: operator.pos,
            ast.In: self.convert,
        }

        self.functions = {
            'mod': operator.mod,
            'acos': math.acos,
            'acosh': math.acosh,
            'asin': math.asin,
            'asinh': math.asinh,
            'atan': math.atan,
            'atan2': math.atan2,
            'atanh': math.atanh,
            # 'cbrt': math.cbrt, # py 3.11
            'ceil': math.ceil,
            'comb': math.comb,
            'cos': math.cos,
            'cosh': math.cosh,
            'dist': math.dist,
            'erf': math.erf,
            'erfc': math.erfc,
            'exp': math.exp,
            # 'exp2': math.exp2, # py 3.11
            'expm1': math.expm1,
            'fabs': math.fabs,
            'factorial': math.factorial,
            'floor': math.floor,
            'fmod': math.fmod,
            'frexp': math.frexp,
            'gamma': math.gamma,
            'gcd': math.gcd,
            'hypot': math.hypot,
            'lcm': math.lcm,
            'ldexp': math.ldexp,
            'lgamma': math.lgamma,
            'log': math.log,
            'log10': math.log10,
            'log1p': math.log1p,
            'log2': math.log2,
            'modf': math.modf,
            'perm': math.perm,
            'remainder': math.remainder,
            'sin': math.sin,
            'sinh': math.sinh,
            'sqrt': math.sqrt,
            'tan': math.tan,
            'tanh': math.tanh,
            'trunc': math.trunc,
            'ulp': math.ulp,
            'degrees': math.degrees,
            'radians': math.radians,
            'abs': abs,
            'bin': bin,
            'complex': complex,
            'divmod': divmod,
            'float': float,
            'int': int,
            'hex': hex,
            'oct': oct,
            'max': max,
            'min': min,
            'pow': pow,
            'round': round,
            'expand':self._expand,
            'simplify':self._simplify,
        }

        self.angle_funcs = ['cos', 'sin', 'tan']

    def _replacer(self, match):
        repl = self.constants.get(match.group(1).strip()) or self.vars.get(match.group(1).strip())
        # print('trying to replace...')
        # print('   match: ', match.group(1).strip())
        if repl:
            # return str(f'{repl}')
            # print('   replacing ', repl)
            return f'({repl})'
        else:
            return match.group()  # no replacement
    def _expand(self, value):
        if isinstance(value, Unit):
            return value.expand()
        else:  # left side was not a unit
            return Unit(value).expand()

    def _simplify(self, value):
        if isinstance(value, Unit):
            return value.simplify()
        else:  # left side was not a unit
            return Unit(value).simplify()



    def parse(self, text, debug=False):
        """Preprocess input string before parsing

        The 'of' operator must come at the end of the line, only folowed by a number.
        """
        # print('>>', text)
        text = text.strip().replace('^', '**')
        # print('>>>', text)

        text = self.extra_spaces_re.sub(' ', text)
        text = self.eliminate_spaces_re.sub('', text)

        if '#' in text:
            text = text[:text.find('#')]

        text = text.replace('@', 'ans')
        text = self.double_in_re.sub(' in to ', text)

        # process 'of' first so % doesn't get confused with the % unit
        if match := self.of_re.search(text):
            text = '((' + text[:match.start()] + \
                f')/100)*' + text[match.end():]
            
        text = self.percent_re.sub('pct', text)

        while match := self.factorial_re.search(text):
            text = text[:match.start()] + f'factorial({match.group(1)})' + text[match.end():]

        # preprocess vars/constants to make them work with units
        # print("BEFORE:",text)
        text = self.names_re.sub(self._replacer, text)
        # print("     >:",text)

        # handle money, $ prefix to USD suffix
        while match := self.money_re.search(text):
            text = text[:match.start()] + f'{match.group(1)} USD' + text[match.end():]
            # print("money1:",text)
        while match := self.money_to_re.search(text):
            text = text[:match.start()] + f' to USD' + text[match.end():]
            # print("money2:",text)

        # process 'in' conversion
        ## swap "to" and "in" for @@@ so it doesn't get confused during unit detection
        text = self.to_re.sub(' @@@ ', text)
        # text = self.in_re.sub('@@@', text)
        # while match := self.to_re.search(text):
        #     text = text[:match.start()] + '@@@' + text[match.end():]
        # while match := self.in_re.search(text):
        #     text = text[:match.start()] + match.group(1)+ ' @@@ ' + text[match.end():]
# 


        # print('7>', text)
        text = text.translate(self.from_specials)

        unit_replacements = {}
        unit_idx = 1
        while match := self.unit_re.search(text):
            # print('unit match:', match.group())
            numstr = match.group(1) or 1
            unitstr = match.group(4)
            # print(f'  num: "{numstr}"')
            # print(f'  unit: "{unitstr}"')
            if unitstr in ('i', 'j'):
                replacement = f'complex(0,{float(numstr)})'
            else:
                replacement = f"Unit('{numstr} {unitstr}')"
            idx = f'@@{unit_idx}@@'
            unit_idx += 1
            unit_replacements[idx] = replacement
            text = text[:match.start()] + idx + text[match.end():]
        for key, val in unit_replacements.items():
            text = text.replace(key, val)
        # print('8>', text)
        
        # Restore the to placeholder for the in operator
        text = text.replace('@@@','in ')
        # implied multiplication
        text = text.replace(")Unit('", ")*Unit('")

        if debug:
            print("Preprocessed text:", text)
            print(ast.dump(ast.parse(text), indent=2))
        
        print('evaluate:',text)
        value = self.evaluate(text)
        return value

    def evaluate(self, node):
        # print(ast.dump(ast.parse('x + y', mode='eval'), indent=4))

        if isinstance(node, str):
            return self.evaluate(ast.parse(node))

        elif isinstance(node, ast.Module):
            values = []
            for body in node.body:
                values.append(self.evaluate(body))
            if len(values) == 1:
                values = values[0]
            return values

        elif isinstance(node, (list, tuple)):
            return [self.evaluate(child_node) for child_node in node]

        elif isinstance(node, ast.Expr):
            return self.evaluate(node.value)

        elif isinstance(node, ast.BinOp):
            left = self.evaluate(node.left)
            right = self.evaluate(node.right)
            try:
                return self.operations[type(node.op)](left, right)  # type: ignore
            except KeyError:
                raise ValueError(f"Bad Operator: {node.op.__class__.__name__}")

        elif isinstance(node, ast.UnaryOp):
            try:
                return self.operations[type(node.op)](self.evaluate(node.operand))  # type: ignore
            except KeyError:
                raise ValueError(f"Bad Operator: {node.op.__class__.__name__}")

        elif isinstance(node, ast.Assign):
            value = self.evaluate(node.value)
            for target in node.targets:
                self.vars[target.id] = value # type: ignore
            return value

        elif isinstance(node, ast.Compare):
            left = self.evaluate(node.left)
            right = self.evaluate(node.comparators[0])

            op = node.ops[0]
            try:
                return self.operations[type(op)](left, right) # type: ignore
            except KeyError:
                raise ValueError(f"Bad Operator: {op.__class__.__name__}")

        elif isinstance(node, ast.Call):
            if isinstance(node.func,
                          ast.Constant):  # implied multiplication of number
                return node.func.value * self.evaluate(node.args[0])
            elif isinstance(node.func,
                            ast.Name):  # implied multiplication of var/const
                const = self.constants.get(node.func.id)
                var = self.vars.get(node.func.id)
                if any([var, const]):
                    return (const or var) * self.evaluate(node.args[0])

            func = node.func.id # type: ignore

            if func == 'Unit':
                if len(node.args) == 1:
                    return Unit(node.args[0].value) # type: ignore
                elif len(node.args) == 2:
                    return Unit(self.evaluate(node.args[0]),
                                node.args[1].value) # type: ignore
                else:
                    return Unit(self.evaluate(node.args[0]),
                                node.args[1].value, node.args[2].value) # type: ignore
                    # return Unit(node.args[0].value, node.args[1].value)

            args = [self.evaluate(arg) for arg in node.args]

            if func in self.angle_funcs:  # convert to radians
                if isinstance(args[0], Unit):
                    args[0] = args[0].to('rad')

            try:
                return self.functions[func](*args)
            except KeyError:
                raise ValueError(f"Bad Function: {func}")
        elif isinstance(node, ast.Name):
            const = self.constants.get(node.id)
            var = self.vars.get(node.id)
            if not any([const, var]):
                try:  # could be unit with no value
                    return Unit(node.id)
                except:
                    raise ValueError(f"Bad constant or variable: {node.id}")
            else:
                return var or const

        elif isinstance(node, ast.Constant):
            return node.value
        else:
            raise TypeError(f"Unsupported operation: {node.__class__.__name__}")

    def convert(self, from_unit, to_unit):
        if isinstance(from_unit, Unit):
            return from_unit.to(to_unit.unit)
        else:  # left side was not a unit
            return Unit(from_unit, to_unit.unit)


class BeeNotepad:

    def __init__(self):
        self.input = []
        self.output = []
        self.parser = BeeParser()
        self._parse = self.parser.parse
        self._vars = self.parser.vars

    def append(self, text, debug=False):
        out = self._parse(text, debug)
        if out:
            self.input.append(text)
            self.output.append(out)

        self._vars['ans'] = out
        return out

    def clear(self):
        self.input = []
        self.output = []
        self.parser.vars = {}


####

if __name__ == '__main__':
    pad = BeeNotepad()
    # pad.append("1+2")
    # pad.append("pi")
    # pad.append("Unit(1,'mm')")
    # pad.append('a=2')
    # pad.append("a*3")
    # pad.append('pi=3')
    # pad.append('pi*2')
    # pad.append("2m*3in")
    # pad.append("2in*3in")
    # pad.append('1 in in mm')
    # pad.append('1    in in mm')
    # pad.append('c = 8 in')
    # pad.append('c in mm')
    # pad.append('8 % 3')
    # pad.append('50 % of 8')
    # pad.append('20% of 100')
    # pad.append('20% in ppm')
    # pad.append('20% in unitless')
    # pad.append('0.8 _ in %')  # , debug=True)
    # pad.append('40 pcf in kg/m3')
    # pad.append('40 lb/ft3 in kg/m3')
    # pad.append('40 lb/ft3 to kg/m3')
    # pad.append('2*5 in in mm')
    # pad.append('12*12 ft2 in m2')
    # pad.append('50.8mm*2in')
    # pad.append('50.8mm*2in in in2')
    # pad.append('50.8mm*2in to in2')
    # pad.append('total = 32')
    # pad.append('rate = 8')
    # pad.append('rate/total')
    # pad.append('3 _ in m')
    # # pad._parse('rate/total in m', debug=True)
    # pad.append('rate/total')
    # pad.append('sin(90 deg in rad)')
    # pad.append('(6in in m) /1kg')
    # pad.append('(6in in m)/kg')
    # pad.append('(39in in m)/kg')
    # pad.append('9.81m/1s/1s in ft/1s/1s')
    # pad.append('(9.81m/s/s in ft/s/s)/kg')
    # pad.append('(9.81m/s/s in ft/(s*s))/kg')
    # pad.append('5*(1+2)')
    # pad.append('5(1+2)')
    # pad.append('a=8')
    # pad.append('a*(1+2)')
    # pad.append('a(1+2)')
    # pad.append('sin(90 deg)')
    # pad.append('sin(pi/2)')
    # # pad.append('sin(pi rad)', debug=True)
    # pad.append('aaa=90', debug=True)
    # pad.append('sin(aaa deg)', debug=True)
    # pad.append('sin(pi rad/2)', debug=True)
    # pad.append('-1', debug=True)
    # pad.append('+1', debug=True)
    # pad.append('# Comment')
    # pad.append('1+3 # Comment')
    # pad.append('316 mm')
    # print('@@@@@')
    # pad.append('@ -300', debug=True)
    # pad.append('3in *3in', debug=True)
    # pad.append('27 lb/ans in psi', debug=True)
    # pad.append('1um', debug=True)
    # pad.append('@ + 1', debug=True)
    # pad.append('1E3')
    # pad.append('1e3')
    # pad.append('1e3 mm', debug=True)
    # pad.append('10.3e3 mm', debug=True)
    # pad.append('(4m to inch)+(5m to mm)', debug=True)
    # pad.append('2.6162e+07 μm', debug=True)
    # pad.append('400g/((4in in mm) * 54mm* (5in in mm))', debug=True)
    # pad.append('ans', debug=True)
    # pad.append('400g/(45mm * 54mm* 5in)')
    # pad.append('ans in pcf', debug=True)
    # pad.append('1j')
    # pad.append('1i')
    # pad.append('3+4j')
    # pad.append('1 USD in pennies')
    # pad.append('10USD in $')
    # pad.append('(5+1/2) inches')
    # pad.append('90 deg + pi rad')
    # pad.append('1 mm + 3 m', debug=True)
    # pad.append('1 m*A/hr')
    # print(pad.append('m/s in in/hr'))
    # print(pad.append('3 (m*g)/(s*g) + 3'))
    # print(pad.append("sin(90 deg)"))
    # print(pad.append("sin(90deg)"))
    # print(pad.append("sin(90°)"))
    # print(pad.append('5!'))
    # print(pad.append('sin().sd'))
