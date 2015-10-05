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

# This grammar is induced from the file joined quickref.html also avaible at
# http://www.zer0.org/procmail/quickref.html

# Unicode printables minus spaces
unicodePrintables = u''.join(unichr(c) for c in xrange(65536) if not unichr(c).isspace())
# Unicodes spaces minus carriage returnand line break
unicodeSpaces = u''.join(
    unichr(c) for c in xrange(65536) if unichr(c).isspace() and unichr(c) not in ["\n", "\r"]
)
unicodePrintablesSpaces = unicodePrintables + unicodeSpaces

NL = Suppress(LineEnd())
CR = Suppress(Literal("\r"))
escape = Literal('\\')
continuation = escape + LineEnd()

# Variable names that support affectation
# use sames rules thant for C languge
variable = Word(alphas + '_', alphanums + '_')

# Add some meta comment to the grammar to convey more informations
title_comment_flag = Literal('title') + ~NL + Literal(':')
comment_comment_flag = Literal('comment') + ~NL + Literal(':')
comment_custom_flag = Literal('custom') + ~NL + Literal(':')

meta_comment_flag = title_comment_flag | comment_comment_flag | comment_custom_flag

title_comment = (
    Literal('#').suppress()
    + ~NL + title_comment_flag.suppress()
    + Optional(~NL + Word(unicodePrintablesSpaces)).setResultsName('meta_title')
    + Optional(~NL + CR)
    + LineEnd().suppress()
)
comment_comment = (
    Literal('#').suppress()
    + ~NL + comment_comment_flag.suppress()
    + Optional(~NL + Word(unicodePrintablesSpaces)).setResultsName('meta_comment')
    + Optional(~NL + CR)
    + LineEnd().suppress()
)
comment_custom = (
    Literal('#').suppress()
    + ~NL + comment_custom_flag.suppress()
    + Optional(~NL + Word(unicodePrintablesSpaces)).setResultsName('meta_custom')
    + Optional(~NL + CR)
    + LineEnd().suppress()
)
meta_comment = title_comment | comment_comment | comment_custom

# A comment : A '#' + optionally anything except \r and \n
# ends with a \n
comment_raw = (
    Literal('#').suppress()
    + ~meta_comment_flag
    + Optional(~NL + Word(unicodePrintablesSpaces))
    + Optional(~NL + CR)
    + LineEnd().suppress()
)
comment = comment_raw.setResultsName('comment')

# The end of a line may contain a comment line
end_of_line = (
    (Optional(~NL + CR) + LineEnd().suppress())
    | comment_raw.setResultsName('comment_line')
)
start_line = Optional((ZeroOrMore(Word(' \t'))).suppress())

# Assignement as VARNAME="value"
assignement = variable + Optional(
    ~NL + Literal('=').suppress() +
    Optional(~NL + (
        QuotedString('"', "\\").setResultsName('double_quote')
        | QuotedString("'", "\\").setResultsName('single_quote')
        | QuotedString("`", "\\").setResultsName('shell_eval')
        | Word(unicodePrintables).setResultsName('no_quote')
    ))
)

# You can have multiple assignements on the same line
assignements = ZeroOrMore(meta_comment) + (
    Group(assignement) +
    ZeroOrMore(Group(~NL + assignement)) + Optional(end_of_line)
    ).setResultsName('assignements')


# Substitution of a variable name by its value
substitution_variable = (
    variable
    | Word(nums)
    | Literal('#')  # Procmail's command-line arguments,
    | Literal('$')  # like in the shell: $1 is the first command-line
    | Literal('-')  # argument, etc.; $@ contains all arguments, and $#
    | Literal('=')  # contains the number of arguments.
    | Literal('?')
    | Literal('@')
)

substitution = Literal('$') + ~NL + substitution_variable
substitution |= Literal('$\\') + ~NL + substitution_variable
substitution |= (
    Literal('$')
    + ~NL + Literal('{')
    + ~NL + substitution_variable
    + Optional(~NL + Literal(':'))
    + ~NL + (Literal('-') | Literal('+'))
    + ~NL + Word(unicodePrintables.replace('}', ''))
    + ~NL + Literal('}')
)
substitution |= QuotedString('`', "\\")
substitution = substitution.setResultsName('substitution')

# Initialisation of the recursive definition of a recipe
recipe = Forward()

# The procmails statements
# I don't think it's valid to find substitution in the midle
# of nowhere.
statement = ZeroOrMore(Optional(~NL + CR) + LineEnd()).suppress() \
    + (comment | assignements | substitution | recipe) \
    + ZeroOrMore(Optional(~NL + CR) + LineEnd()).suppress()
statements = ZeroOrMore(Group(statement))

##### Recipe definition ######

flag = Literal('A') | Literal('a') | Literal('B') | Literal('b') | Literal('c') \
    | Literal('D') | Literal('E') | Literal('e') | Literal('f') | Literal('H') \
    | Literal('h') | Literal('i') | Literal('r') | Literal('W') | Literal('w')
flags = Optional(flag + ZeroOrMore(~NL + flag)).setResultsName('flags')
lockfile = (Literal(':') + Optional(~NL + Word(printables))).setResultsName('lockfile')
# first line of a recipe
colon_line = (
    start_line + ~NL + Literal(':').suppress() + ~NL + Word(nums).setResultsName('number')
    + Optional(~NL + flags) + Optional(~NL + lockfile) + end_of_line
    ).setResultsName('header')


regex_line = (
    Word(unicodePrintablesSpaces, excludeChars='\\')
    + ZeroOrMore(
        OneOrMore(~NL + escape)
        + ~NL + Word(unicodePrintablesSpaces, excludeChars='\\')
    )
)
regex = Combine(
    regex_line
    + ZeroOrMore(
        ~NL + continuation.suppress()
        + ~NL + ZeroOrMore(~NL + continuation.suppress())
        + ~NL + regex_line
    )
)
# Definition of a condition
condition = Forward()
condition_regex = regex
condition_size = (Literal('>') | Literal('<')).setResultsName("sign") \
    + ~NL + Word(nums).setResultsName("size")
condition_shell = Literal('?').suppress() + ~NL + Word(unicodePrintablesSpaces)
condition << (
    (
        variable.setResultsName("variable")
        + ~NL + Literal('??')
        + ~NL + Group(condition).setResultsName("condition")
    ).setResultsName("variable") |
    condition_size.setResultsName("size") |
    condition_shell.setResultsName("shell") |
    (Literal('!').suppress() + ~NL + Group(condition).setResultsName("negate")) |
    (Literal('$').suppress() + ~NL + Group(condition).setResultsName("substitute")) |
    (
        Word(nums).setResultsName("x")
        + ~NL + Literal('^').suppress()
        + ~NL + Word(nums).setResultsName("y")
        + ~NL + Group(condition).setResultsName("condition")
    ).setResultsName("score") |
    condition_regex.setResultsName("regex")
    )
condition = (start_line + ~NL + Literal('*').suppress() + Optional(~NL + condition) + end_of_line)

# Definition of possibles actions
action_first_char = unicodePrintablesSpaces
for char in ['{', '!', '|', '*']:
    action_first_char = action_first_char.replace(char, '')

action_forward = Literal('!').suppress() + ~NL + OneOrMore(~NL + Word(unicodePrintables))
action_shell = Optional(variable.setResultsName("variable") + ~NL + Literal('=')) \
    + ~NL + Literal('|') + ~NL + Word(unicodePrintablesSpaces).setResultsName("cmd")
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

# Finelly recursive definition of a recipe
recipe << (
    ZeroOrMore(meta_comment)
    + colon_line
    + Optional(comment_raw).setResultsName('comment_condition')
    + ZeroOrMore(Group(condition)).setResultsName('conditions')
    + Optional(comment_raw).setResultsName('comment_action')
    + action
)

# From start to end of the procmailrc everithing must
# be parsed (no garbage)
base_statements = StringStart() + statements + StringEnd()


def parse(file, charset="utf-8"):
    with open(file, 'r') as f:
        return (base_statements).parseString(f.read().decode(charset))


def parseString(string):
    return (base_statements).parseString(string)
