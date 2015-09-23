# -*- coding: utf-8 -*-
import parser


class MetaCommentable(object):
    meta_title = None
    meta_comment = None

    def _get_meta(self, ident):
        s = []
        if self.meta_title:
            s.append(u"%s#title: %s\n" % ("    " * ident, self.meta_title))
        if self.meta_comment:
            s.append(u"%s#comment: %s\n" % ("    " * ident, self.meta_comment))
        return "".join(s)


class Commentable(object):
    """Mixin class for commentable procmail objects"""
    comment = None

    def has_comment(self):
        return True if self.comment else False

    def _get_comment(self):
        if self.comment:
            return u" %s" % self.comment.render()
        else:
            return u""


class Statement(object):
    """Base classe for procmail's statements"""
    id = None

    is_first = False
    is_last = False

    def is_statement(self):
        return True

    def is_comment(self):
        return False

    def is_assignment(self):
        return False

    def is_recipe(self):
        return False

    def gen_title(self):
        return repr(self)

class Comment(Statement):
    """Older versions are a bit picky about where they accept comments and whitespace.
    Never put a comment on the same line as a regular expression."""
    def __init__(self, str):
        self.str = str

    def render(self, ident=0):
        return u"%s# %s" % ("    " * ident, self.str)

    def is_comment(self):
        return True

    def gen_title(self):
        if len(self.str) > 10:
            return u"# %s…" % self.str[:10]
        else:
            return u"# %s" % self.str


class Assignment(Statement, Commentable, MetaCommentable):
    """Variable names are customarily upper case."""
    def __init__(self, variables, comment=None, meta_title=None, meta_comment=None):
        self.variables = variables  # list of (variable_name, variable_value)
        self.comment = comment
        self.meta_comment = meta_comment
        self.meta_title = meta_title

    def render(self, ident=0):
        variables = []
        for name, value in self.variables:
            if value:
                variables.append('%s="%s"' % (name, value))
            else:
                variables.append(name)
        return u"".join([
            self._get_meta(ident),
            "    " * ident,
            " ".join(variables),
            self._get_comment()
        ])

    def is_assignment(self):
        return True

    def gen_title(self):
        susp = u""
        if len(self.variables)>1:
            susp = u"…"
        if len(self.variables[0][0]) + len(self.variables[0][1]) > 10:
            susp = u"…"
        title = '%s="%s"' % self.variables[0]
        return "%s%s" % (title[:11], susp)

class Header(Commentable):
    """First line of a procmail recipe"""
    def __init__(self, number, flag="", lockfile=None, comment=None):
        if flag == "":
            self._flag = u"Hhb"
        else:
            self._flag = flag
        self.number = number
        self.lockfile = lockfile
        self.comment = comment

    @property
    def flag(self):
        if self.H and self.h and self.b and len(self._flag) == 3:
            return u""
        else:
            return self._flag

    def render(self, ident=0):
        if self.lockfile:
            if self.lockfile is True:
                lockfile = ":"
            else:
                lockfile = ":%s" % self.lockfile
        else:
            lockfile = ""
        return u"%s:%s%s%s%s" % (
            "    " * ident, self.number, self.flag, lockfile, self._get_comment()
        )

    def _get_flag(self, letter):
        return letter in self._flag

    def _set_flag(self, letter, value):
        if value and letter not in self._flag:
            self._flag += letter
        elif not value and letter in self._flag:
            self._flag.replace(letter, "")

    @property
    def H(self):
        """Condition lines examine the headers of the message"""
        return self._get_flag("H")

    @H.setter
    def H(self, value):
        return self._set_flag("H", value)

    @property
    def B(self):
        """Condition lines examine the body of the message"""
        return self._get_flag("B")

    @B.setter
    def B(self, value):
        return self._set_flag("B", value)

    @property
    def h(self):
        """Action line gets fed the headers of the message."""
        return self._get_flag("h")

    @h.setter
    def h(self, value):
        return self._set_flag("h", value)

    @property
    def b(self):
        """Action line gets fed the body of the message. """
        return self._get_flag("b")

    @b.setter
    def b(self, value):
        return self._set_flag("b", value)

    @property
    def c(self):
        """Clone message and execute the action(s) in a subprocess if the
        conditions match. The parent process continues with the original
        message after the clone process finishes."""
        return self._get_flag("c")

    @c.setter
    def c(self, value):
        return self._set_flag("c", value)

    @property
    def A(self):
        """Execute this recipe if the previous recipe's conditions were met. """
        return self._get_flag("A")

    @A.setter
    def A(self, value):
        return self._set_flag("A", value)

    @property
    def a(self):
        """Execute this recipe if the previous recipe's conditions were
        met and its action(s) were completed successfully."""
        return self._get_flag("a")

    @a.setter
    def a(self, value):
        return self._set_flag("a", value)

    @property
    def E(self):
        """Execute this recipe if the previous recipe's conditions were not met."""
        return self._get_flag("E")

    @E.setter
    def E(self, value):
        return self._set_flag("E", value)

    @property
    def e(self):
        """Execute this recipe if the previous recipe's conditions were met,
        but its action(s) couldn't be completed."""
        return self._get_flag("e")

    @e.setter
    def e(self, value):
        return self._set_flag("e", value)

    @property
    def f(self):
        """Feed the message to the pipeline on the action line if the conditions are met,
        and continue processing with the output of the pipeline
        (replacing the original message)."""
        return self._get_flag("f")

    @f.setter
    def f(self, value):
        return self._set_flag("f", value)

    @property
    def i(self):
        """Suppress error checking when writing to a pipeline.
        This is typically used to get rid of SIGPIPE errors when the pipeline doesn't
        eat all of the input Procmail wants to feed it."""
        return self._get_flag("i")

    @i.setter
    def i(self, value):
        return self._set_flag("i", value)

    @property
    def r(self):
        """Raw mode: Don't do any "fixing" of the original message when writing it out
        (such as adding a final newline if the message didn't have one originally)."""
        return self._get_flag("r")

    @r.setter
    def r(self, value):
        return self._set_flag("r", value)

    @property
    def w(self):
        """Wait for the program in the action line to finish before continuing.
        Otherwise, Procmail will spawn off the program and leave it executing on its own."""
        return self._get_flag("w")

    @w.setter
    def w(self, value):
        return self._set_flag("w", value)

    @property
    def W(self):
        """Like w, but additionally suppresses any "program failure" messages
        from the action pipeline."""
        return self._get_flag("W")

    @W.setter
    def W(self, value):
        return self._set_flag("W", value)

    @property
    def D(self):
        """Pay attention to character case when matching: "a" is treated as distinct from
        "A" and so on. Some of the special macros are always matched case-insensitively."""
        return self._get_flag("D")

    @D.setter
    def D(self, value):
        return self._set_flag("D", value)


class Condition(Commentable):
    """Base class for procmail's conditions"""
    def render(self, ident=0):
        return u"%s* %s%s" % ("    " * ident, self.pre_render(), self._get_comment())

    def is_empty(self):
        return False

    def is_shell(self):
        return False

    def is_size(self):
        return False

    def is_regex(self):
        return False

    def is_negate(self):
        return False

    def is_variable(self):
        return False

    def is_substitute(self):
        return False

    def is_score(self):
        return False


class ConditionEmpty(Condition):
    """The empty condition, always match"""
    def __init__(self, comment=None):
        self.comment = comment

    def pre_render(self):
        return u""

    def is_empty(self):
        return True


class ConditionShell(Condition):
    """Test exit code of external program"""
    def __init__(self, cmd, comment=None):
        self.cmd = cmd
        self.comment = comment

    def pre_render(self):
        return u"? %s" % self.cmd

    def is_shell(self):
        return True


class ConditionSize(Condition):
    """Test size of message part"""
    def __init__(self, sign, size, comment=None):
        self.sign = sign
        self.size = size
        self.comment = comment

    def pre_render(self):
        return u"%s %s" % (self.sign, self.size)

    def is_size(self):
        return True


class ConditionRegex(Condition):
    """Tests with regular expressions """
    def __init__(self, regex, comment=None):
        self.regex = regex
        self.comment = comment

    def pre_render(self):
        return u"%s" % self.regex

    def is_regex(self):
        return True


class ConditionVariable(Condition):
    """Test the value of `variable` against `condition`"""
    def __init__(self, variable, condition, comment=None):
        self.variable = variable
        self.condition = condition
        self.comment = comment

    def pre_render(self):
        return u"%s ?? %s" % (self.variable, self.condition.pre_render())

    def is_variable(self):
        return True


class ConditionNegate(Condition):
    """Negation"""
    def __init__(self, condition, comment=None):
        self.condition = condition
        self.comment = comment

    def pre_render(self):
        return u"! %s" % self.condition.pre_render()

    def is_negate(self):
        return True


class ConditionSubstitute(Condition):
    """
    Subject condition to variable and backtick substitution before actually evaluating
    the condition.
    In particular, this will resolve any references to variables ($VAR) which will otherwise be
    interpreted literally (because $ is a regular-expression character which you normally
    don't want Procmail to tamper with). Incidentally, quoted strings will also have their quotes
    stripped and backticks will be evaluated, too. (In other words, quotes have to be
    backslash-escaped and ordinarily backslash-escaped literal characters need to have their
    backslashes doubled.)
    You can stack multiple $ flags to force multiple substitution passes.
    """
    def __init__(self, condition, comment=None):
        self.condition = condition
        self.comment = comment

    def pre_render(self):
        return u"$ %s" % self.condition.pre_render()

    def is_substitute(self):
        return True


class ConditionScore(Condition):
    """
    Scoring: If the condition is true, add a number to the total score.
    x is the number to add on the first match;
    y influences by how much the score should be adjusted for subsequent matches.
    When y is zero, only add x the first time the condition matches.
    An empty condition always matches.
    The final score is in the $? pseudovariable and the action is taken
    if the final score is positive.
    """
    def __init__(self, x, y, condition, comment=None):
        self.x = x
        self.y = y
        self.condition = condition
        self.comment = comment

    def pre_render(self):
        return u"%s ^ %s %s" % (self.x, self.y, self.condition.pre_render())

    def is_score(self):
        return True


class Action(object):
    """Base class for procmail's actions"""
    def is_save(self):
        return False

    def is_forward(self):
        return False

    def is_shell(self):
        return False

    def is_nested(self):
        return False


class ActionForward(Action, Commentable):
    """Forward to other address(es)"""
    def __init__(self, recipients=None, comment=None):
        self.recipients = [] if recipients is None else recipients
        self.comment = comment

    def render(self, ident=0):
        return u"%s! %s%s" % ("    " * ident, " ".join(self.recipients), self._get_comment())

    def is_save(self):
        return True


class ActionShell(Action, Commentable):
    def __init__(self, cmd, variable=None, lockfile=None, comment=None):
        """The pipeline is expected to save the message somewhere;
        you can play with the recipe's flags to tell Procmail otherwise.
        (Always use locking when writing to a file.)

        The output of the command pipeline can be assigned to a variable.
        This makes the recipe non-delivering.
        """
        self.cmd = cmd
        self.variable = variable
        self.lockfile = lockfile
        self.comment = comment

    def is_shell(self):
        return True

    def render(self, ident=0):
        if self.lockfile:
            lockfile = " >> %s" % self.lockfile
        else:
            lockfile = ""
        if self.variable:
            variable = "%s=" % self.variable
        else:
            variable = ""
        return u"%s%s|%s%s%s" % ("    " * ident, variable, self.cmd, lockfile, self._get_comment())


class ActionSave(Action, Commentable):
    """
    /path/to/filename
        Save to a plain file; if there is no path given, MAILDIR is used as the directory.
        Always use locking when writing to a plain file (except /dev/null).
    directory/.
        Save to an MH folder. Note the trailing /.
        You can list several MH folders at the same time. Only one file will actually be written,
        the rest will be hard links.
    directory/
        Save to a directory. The trailing slash is not strictly necessary.
        You can list several directories at the same time. Only one file will actually be written,
        the rest will be hard links.
    """
    def __init__(self, path, comment=None):
        self.path = path
        self.comment = comment

    def is_save(self):
        return True

    def render(self, ident=0):
        return u"%s%s%s" % ("    " * ident, self.path, self._get_comment())


class ActionNested(Action, list):
    """
    Instead of a single action line, an entire block of recipes can be used when the condition
    matches.
    The stuff between the braces can be any valid Procmail construct
    """

    def render(self, ident=0):
        return u"%s{\n%s\n%s}\n" % (
            "    " * ident, "\n".join(s.render(ident+1) for s in self), "    " * ident
        )

    def is_nested(self):
        return True


class Recipe(Statement, MetaCommentable):
    """
    Recipes consist of three parts:

    A `Header` object
    A list of conditions (may be empty) which are instance of `Condition` (use subclasses)
    An action instance of `Action` (use subclasses)
    """
    def __init__(self, header, action, conditions=None, meta_title=None, meta_comment=None):
        self.header = header
        self.action = action
        self.conditions = [] if conditions is None else conditions
        self.meta_title = meta_title
        self.meta_comment = meta_comment

    def is_recipe(self):
        return True

    def render(self, ident=0):
        s = []
        s.append("\n")
        s.append(self._get_meta(ident))
        s.append(self.header.render(ident))
        s.append("\n")
        for cond in self.conditions:
            s.append(cond.render(ident))
            s.append("\n")
        s.append(self.action.render(ident))
        s.append("\n")
        return u"".join(s)

    def gen_title(self):
        return "Recipe %s" % self.id


class ProcmailRc(list):
    """A list of `Statement` objetcs (use subclasses)"""

    def render(self):
        return u"\n".join(s.render() for s in self)


def _parse_comment(p):
    return Comment(p.comment[0])


def _parse_assignements(p):
    if p.assignements.comment_line:
        comment = Comment(p.assignements.comment_line[0])
    else:
        comment = None
    meta_title = p.meta_title if p.meta_title else None
    meta_comment = p.meta_comment if p.meta_comment else None
    variables = []
    for assignment in p.assignements:
        if isinstance(assignment, parser.ParseResults):
            if len(assignment) >= 2:
                variables.append((assignment[0], assignment[1]))
            else:
                variables.append((assignment[0], None))
    return Assignment(
        variables,
        comment=comment,
        meta_title=meta_title,
        meta_comment=meta_comment
    )


def _parse_condition(p, comment=None):
    if p.substitute:
        return ConditionSubstitute(_parse_condition(p.substitute[0]), comment=comment)
    elif p.negate:
        return ConditionNegate(_parse_condition(p.negate[0]), comment=comment)
    elif p.variable:
        return ConditionVariable(
            p.variable.variable, _parse_condition(p.variable.condition),
            comment=comment
        )
    elif p.score:
        return ConditionScore(
            p.score.x,
            p.score.y,
            _parse_condition(p.score.condition),
            comment=comment
        )
    elif p.regex:
        return ConditionRegex(p.regex, comment=comment)
    elif p.shell:
        return ConditionShell(p.shell[0], comment=comment)
    elif p.size:
        return Condition(p.size.sign, p.size.size, comment=comment)
    else:
        return ConditionEmpty(comment=comment)


def _parse_recipe(p):
    lockfile = False
    if p.header.lockfile:
        if len(p.header.lockfile) > 1:
            lockfile = p.header.lockfile[1]
        else:
            lockfile = True
    if p.header.comment_line:
        comment = Comment(p.header.comment_line[0])
    else:
        comment = None
    header = Header(p.header.number, "".join(p.header.flags), lockfile, comment=comment)
    conditions = []
    if p.conditions:
        for cond in p.conditions:
            if cond.comment_line:
                comment = Comment(cond.comment_line[0])
            else:
                comment = None
            conditions.append(_parse_condition(cond, comment=comment))
    if p.action.comment_line:
        comment = Comment(p.action.comment_line[0])
    else:
        comment = None
    if p.action.statements:
        action = ActionNested(_parse_statements(p.action.statements))
    elif p.action.forward:
        action = ActionForward(p.action.forward.asList(), comment=comment)
    elif p.action.shell:
        action = ActionShell(
            p.action.shell.cmd,
            p.action.shell.variable,
            p.action.shell.lockfile[1],
            comment=comment
        )
    elif p.action.path:
        action = ActionSave(p.action.path, comment=comment)
    else:
        raise RuntimeError("Unknown action %r" % p.action)
    return Recipe(
        header, action, conditions,
        meta_title=p.meta_title if p.meta_title else None,
        meta_comment=p.meta_comment if p.meta_comment else None
    )


def set_id(stmts, prefix=""):
    i = 0
    for stmt in stmts:
        stmt.id = "%s%s" % (prefix, i)
        if stmt.is_recipe() and stmt.action.is_nested():
            set_id(stmt.action, stmt.id + ".")
        i += 1
    stmts[0].is_first = True
    stmts[-1].is_last = True


def _parse_statements(p):
    stmt = []
    for s in p:
        if s.assignements:
            stmt.append(_parse_assignements(s))
        elif s.comment:
            stmt.append(_parse_comment(s))
        elif s.header:
            stmt.append(_parse_recipe(s))
    set_id(stmt)
    return stmt


def parse(file):
    p = parser.parse(file)
    return ProcmailRc(_parse_statements(p))


def parseString(string):
    p = parser.parseString(string)
    return ProcmailRc(_parse_statements(p))
