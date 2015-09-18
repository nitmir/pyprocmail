from pyparsing import *
unicodePrintables = u''.join(unichr(c) for c in xrange(65536) if not unichr(c).isspace())
unicodePrintablesSpaces = unicodePrintables + ' \t'
NL = Suppress(LineEnd())


variable = Word(alphanums.replace('*', ''), alphanums)

comment_raw = Literal('#') + Word(unicodePrintablesSpaces) + LineEnd().suppress()
comment = comment_raw.setResultsName('comment')

end_of_line = (LineEnd().suppress() | comment_raw.setResultsName('comment_line'))
start_line = Optional((ZeroOrMore(Word(' \t'))).suppress())

assignement = variable + ~NL + '=' + ~NL \
    + (QuotedString('"', "\\") | QuotedString("'", "\\") | Word(unicodePrintables))
assignements = (
    OneOrMore(Group(assignement)) + Optional(end_of_line)
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
statements = OneOrMore(Group(statement))

flag = Literal('A') | Literal('a') | Literal('B') | Literal('b') | Literal('c') \
    | Literal('D') | Literal('E') | Literal('e') | Literal('f') | Literal('H') \
    | Literal('h') | Literal('i') | Literal('r') | Literal('W') | Literal('w')
flags = ZeroOrMore(flag).setResultsName('flags')
lockfile = (Literal(':') + ~NL + Word(printables)).setResultsName('lockfile')
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
        variable.setResultsName("variable") + Literal('??') + condition.setResultsName("condition")
    ).setResultsName("variable") |
    condition_size.setResultsName("size") |
    condition_shell.setResultsName("shell") |
    (Literal('!').suppress() + condition).setResultsName("negate") |
    (Literal('$').suppress() + condition).setResultsName("substitute") |
    (
        Word(nums).setResultsName("x") + Literal('^').suppress() + Word(nums).setResultsName("y") +
        condition.setResultsName("condition")
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

recipe << (colon_line + ZeroOrMore(Group(condition)).setResultsName('conditions') + action)

base_statements = statements + StringEnd()


def parse(file, charset="utf-8"):
    with open(file, 'r') as f:
        return (base_statements).parseString(f.read().decode(charset))
