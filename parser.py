# ⁻*- coding: utf-8 -*-
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License version 3 for
# more details.
#
# You should have received a copy of the GNU General Public License version 3
# along with this program; if not, write to the Free Software Foundation, Inc., 51
# Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#
# (c) 2015 Valentin Samir
from pyparsing import *
unicodePrintables = u''.join(unichr(c) for c in xrange(65536) if not unichr(c).isspace())
unicodePrintablesSpaces = unicodePrintables + u' \t\xa0'
NL = Suppress(LineEnd())


variable = Word(printables.replace('*', ''), printables)

# Add some meta comment to the grammar to convey more informations
title_comment_flag = Literal('title') + Literal(':')
comment_comment_flag = Literal('comment') + Literal(':')

meta_comment_flag = title_comment_flag | comment_comment_flag

title_comment = (
    Literal('#').suppress()
    + title_comment_flag.suppress()
    + Optional(Word(unicodePrintablesSpaces)).setResultsName('meta_title')
    + LineEnd().suppress()
)
comment_comment = (
    Literal('#').suppress()
    + comment_comment_flag.suppress()
    + Optional(Word(unicodePrintablesSpaces)).setResultsName('meta_comment')
    + LineEnd().suppress()
)

meta_comment = title_comment | comment_comment


comment_raw = (
    Literal('#').suppress()
    + ~meta_comment_flag
    + Optional(~NL + Word(unicodePrintablesSpaces))
    + LineEnd().suppress()
)
comment = comment_raw.setResultsName('comment')


end_of_line = (LineEnd().suppress() | comment_raw.setResultsName('comment_line'))
start_line = Optional((ZeroOrMore(Word(' \t'))).suppress())

assignement = variable + Optional(
    ~NL + Literal('=').suppress() +
    Optional(~NL + (
        QuotedString('"', "\\").setResultsName('double_quote')
        | QuotedString("'", "\\").setResultsName('single_quote')
        | QuotedString("`", "\\").setResultsName('shell_eval')
        | Word(unicodePrintables)
    ))
)
assignements = ZeroOrMore(meta_comment) + (
    Group(assignement) +
    ZeroOrMore(Group(~NL + assignement)) + Optional(end_of_line)
    ).setResultsName('assignements')

substitution = Literal('$') + ~NL + variable
substitution |= Literal('$\\') + ~NL + variable
substitution |= Literal('$') + ~NL + Literal('{') + ~NL + variable + Optional(~NL + Literal(':')) \
    + ~NL + (Literal('-') | Literal('+')) + ~NL + Word(unicodePrintables.replace('}', '')) + ~NL \
    + Literal('}')
substitution |= QuotedString('`', "\\")
substitution = substitution.setResultsName('substitution')

recipe = Forward()

statement = ZeroOrMore(LineEnd()).suppress() \
    + (comment | assignements | substitution | recipe) \
    + ZeroOrMore(LineEnd()).suppress()
statements = ZeroOrMore(Group(statement))

flag = Literal('A') | Literal('a') | Literal('B') | Literal('b') | Literal('c') \
    | Literal('D') | Literal('E') | Literal('e') | Literal('f') | Literal('H') \
    | Literal('h') | Literal('i') | Literal('r') | Literal('W') | Literal('w')
flags = ZeroOrMore(flag).setResultsName('flags')
lockfile = (Literal(':') + Optional(~NL + Word(printables))).setResultsName('lockfile')
colon_line = (
    start_line + ~NL + Literal(':').suppress() + ~NL + Word(nums).setResultsName('number')
    + Optional(~NL + flags) + Optional(~NL + lockfile) + end_of_line
    ).setResultsName('header')


condition = Forward()
condition_regex = Word(unicodePrintablesSpaces)
condition_size = (Literal('>') | Literal('<')).setResultsName("sign") \
    + Word(nums).setResultsName("size")
condition_shell = Literal('?').suppress() + Word(unicodePrintablesSpaces)
condition << (
    (
        variable.setResultsName("variable")
        + Literal('??')
        + Group(condition).setResultsName("condition")
    ).setResultsName("variable") |
    condition_size.setResultsName("size") |
    condition_shell.setResultsName("shell") |
    (Literal('!').suppress() + Group(condition).setResultsName("negate")) |
    (Literal('$').suppress() + Group(condition).setResultsName("substitute")) |
    (
        Word(nums).setResultsName("x") + Literal('^').suppress() + Word(nums).setResultsName("y") +
        Group(condition).setResultsName("condition")
    ).setResultsName("score") |
    condition_regex.setResultsName("regex")
    )
condition = (start_line + ~NL + Literal('*').suppress() + Optional(~NL + condition) + end_of_line)

action_first_char = unicodePrintablesSpaces
for char in ['{', '!', '|', '*']:
    action_first_char = action_first_char.replace(char, '')

action_forward = Literal('!').suppress() + ~NL + OneOrMore(~NL + Word(unicodePrintables))
action_shell = Optional(variable.setResultsName("variable") + ~NL + Literal('=')) \
    + ~NL + Literal('|') + ~NL + Word(unicodePrintablesSpaces).setResultsName("cmd") \
    + Optional(
        ~NL + Literal('>>') + ~NL + Word(unicodePrintablesSpaces)
    ).setResultsName('lockfile')
action_save = Word(action_first_char, unicodePrintablesSpaces)
action_list = Literal('{').suppress() + statements + Literal('}').suppress()
action = (
    start_line + ~NL +
    (
        action_forward.setResultsName("forward") |
        action_list.setResultsName('statements') |
        action_shell.setResultsName("shell") |
        action_save.setResultsName("path")
    ) + end_of_line
    ).setResultsName('action')

recipe << (
    ZeroOrMore(meta_comment)
    + colon_line
    + ZeroOrMore(Group(condition)).setResultsName('conditions')
    + action
)

base_statements = StringStart() + statements + StringEnd()


def parse(file, charset="utf-8"):
    with open(file, 'r') as f:
        return (base_statements).parseString(f.read().decode(charset))


def parseString(string):
    return (base_statements).parseString(string)
