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
import parser
import os


class BaseObject(object):

    def is_statement(self):
        return False

    def is_action(self):
        return False

    def is_header(self):
        return False

    def is_condition(self):
        return False


class MetaCommentable(object):
    meta_title = None
    meta_comment = None
    meta_custom = None

    def _get_meta(self, ident):
        s = []
        if self.meta_title:
            s.append(u"%s#title: %s\n" % ("    " * ident, self.meta_title))
        if self.meta_comment:
            s.append(u"%s#comment: %s\n" % ("    " * ident, self.meta_comment))
        if self.meta_custom:
            s.append(u"%s#custom: %s\n" % ("    " * ident, self.meta_custom))
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


class Statement(BaseObject):
    """Base classe for procmail's statements"""
    id = None

    is_first = False
    is_last = False

    parent = None

    def delete(self):
        """Remove the statement from a ProcmailRC structure, raise a
        RuntimeError if the statement is not inside a ProcmailRC structure
        return the parent id"""
        if self.parent is None:
            raise RuntimeError(
                "Current statement has no parent, so it cannot "
                + "be deleted form a procmailrc structure"
            )
        elif self.id is None:
            raise RuntimeError("id not set but have a parent, this should not be happening")
        else:
            parent_id = self.parent.id
            index = int(self.id.split('.')[-1])
            self.parent.pop(index)
            self.parent = None
            self.id = None
            return parent_id

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

    def __eq__(self, y):
        if isinstance(y, Comment):
            if y.str == self.str:
                if self.id is not None and y.id is not None:
                    return self.id == y.id
                else:
                    return True
        return False

    def render(self, ident=0):
        return u"%s# %s" % ("    " * ident, self.str)

    def is_comment(self):
        return True

    def gen_title(self):
        if len(self.str) > 24:
            return u"# %s…" % self.str[:24]
        else:
            return u"# %s" % self.str


class Assignment(Statement, Commentable, MetaCommentable):
    """Variable names are customarily upper case."""
    def __init__(
        self, variables, comment=None, meta_title=None,
        meta_comment=None, meta_custom=None
    ):
        self.variables = variables  # list of (variable_name, variable_value)
        self.comment = comment
        self.meta_comment = meta_comment
        self.meta_title = meta_title
        self.meta_custom = meta_custom

    def __eq__(self, y):
        if isinstance(y, Assignment):
            if y.variables == self.variables:
                if self.id is not None and y.id is not None:
                    return self.id == y.id
                else:
                    return True
        return False

    def render(self, ident=0):
        variables = []
        for name, value, quote in self.variables:
            if value:
                if quote:
                    variables.append(
                        '%s=%s%s%s' % (name, quote, value.replace(quote, '\\%s' % quote), quote)
                    )
                else:
                    variables.append('%s=%s' % (name, value))
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
        if len(self.variables) > 1:
            susp = u"…"
        if len(self.variables[0][0]) > 20:
            susp = u"…"
        title = 'Set %s' % (self.variables[0][0],)
        return "%s%s" % (title[:24], susp)


class Header(BaseObject, Commentable):
    """First line of a procmail recipe"""
    def __init__(self, number='0', flag="", lockfile=None, comment=None):
        if 'H' not in flag and 'B' not in flag:
            flag += 'H'
        if 'h' not in flag and 'b' not in flag:
            flag += 'hb'
        self._flag = flag
        self.number = number
        self.lockfile = lockfile
        self.comment = comment

    def __eq__(self, y):
        if isinstance(y, Header):
            if self.number == y.number and self.lockfile == y.lockfile:
                flag1 = [f for f in self.flag]
                flag2 = [f for f in y.flag]
                flag1.sort()
                flag2.sort()
                return flag1 == flag2
        return False

    def is_header(self):
        return True

    @property
    def flag(self):
        flag = self._flag
        # hb is the default
        # Lone h turns off b and vice versa; use hb to explicitly turn on both.
        if self.h and self.b:
            for letter in ['h', 'b']:
                flag = flag.replace(letter, '')
        # H is the default
        # Lone B turns off H; use HB to examine both headers and body.
        if self.H and not self.B:
            for letter in ['H']:
                flag = flag.replace(letter, '')
        return flag

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
            self._flag = self._flag.replace(letter, "")

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


def register_type(classe):
    classe.__bases__[0]._types[classe.type] = classe
    return classe


class Typed(object):

    type = None

    _types = {}

    @classmethod
    def from_type(cls, type):
        return cls._types[type]


class Condition(BaseObject, Commentable, Typed):
    """Base class for procmail's conditions"""

    _types = {}

    def render(self, ident=0):
        return u"%s* %s%s" % ("    " * ident, self.pre_render(), self._get_comment())

    def is_condition(self):
        return True

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

    def is_nested(self):
        return False


@register_type
class ConditionEmpty(Condition):
    """The empty condition, always match"""

    type = "empty"

    def __init__(self, comment=None):
        self.comment = comment

    def __eq__(self, y):
        if isinstance(y, Condition):
            return y.type == self.type
        return False

    def pre_render(self):
        return u""

    def is_empty(self):
        return True


@register_type
class ConditionShell(Condition):
    """Test exit code of external program"""

    type = "shell"

    def __init__(self, cmd, comment=None):
        self.cmd = cmd
        self.comment = comment

    def __eq__(self, y):
        if isinstance(y, Condition):
            return y.type == self.type and self.cmd == y.cmd
        return False

    def pre_render(self):
        return u"? %s" % self.cmd

    def is_shell(self):
        return True


@register_type
class ConditionSize(Condition):
    """Test size of message part"""

    type = "size"

    def __init__(self, sign, size, comment=None):
        self.sign = sign
        self.size = size
        self.comment = comment

    def __eq__(self, y):
        if isinstance(y, Condition):
            return y.type == self.type and self.sign == y.sign and self.size == y.size
        return False

    def pre_render(self):
        return u"%s %s" % (self.sign, self.size)

    def is_size(self):
        return True


@register_type
class ConditionRegex(Condition):
    """Tests with regular expressions """

    type = "regex"

    def __init__(self, regex, comment=None):
        self.regex = regex
        self.comment = comment

    def __eq__(self, y):
        if isinstance(y, Condition):
            return y.type == self.type and self.regex == y.regex
        return False

    def pre_render(self):
        return u"%s" % self.regex

    def is_regex(self):
        return True


@register_type
class ConditionVariable(Condition):
    """Test the value of `variable` against `condition`"""

    type = "variable"

    def __init__(self, variable, condition, comment=None):
        self.variable = variable
        self.condition = condition
        self.comment = comment

    def __eq__(self, y):
        if isinstance(y, Condition):
            return (
                y.type == self.type
                and self.variable == y.variable
                and self.condition == y.condition
            )
        return False

    def pre_render(self):
        return u"%s ?? %s" % (self.variable, self.condition.pre_render())

    def is_variable(self):
        return True

    def is_nested(self):
        return True


@register_type
class ConditionNegate(Condition):
    """Negation"""

    type = "negate"

    def __init__(self, condition, comment=None):
        self.condition = condition
        self.comment = comment

    def __eq__(self, y):
        if isinstance(y, Condition):
            return y.type == self.type and self.condition == y.condition
        return False

    def pre_render(self):
        return u"! %s" % self.condition.pre_render()

    def is_negate(self):
        return True

    def is_nested(self):
        return True


@register_type
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

    type = "subtitute"

    def __init__(self, condition, comment=None):
        self.condition = condition
        self.comment = comment

    def __eq__(self, y):
        if isinstance(y, Condition):
            return y.type == self.type and self.condition == y.condition
        return False

    def pre_render(self):
        return u"$ %s" % self.condition.pre_render()

    def is_substitute(self):
        return True

    def is_nested(self):
        return True


@register_type
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

    type = "score"

    def __init__(self, x, y, condition, comment=None):
        self.x = x
        self.y = y
        self.condition = condition
        self.comment = comment

    def __eq__(self, y):
        if isinstance(y, Condition):
            return (
                y.type == self.type
                and self.x == y.x
                and self.y == y.y
                and self.condition == y.condition
            )
        return False

    def pre_render(self):
        return u"%s ^ %s %s" % (self.x, self.y, self.condition.pre_render())

    def is_score(self):
        return True

    def is_nested(self):
        return True


class Action(BaseObject, Typed):
    """Base class for procmail's actions"""

    _types = {}

    def is_action(self):
        return True

    def is_save(self):
        return False

    def is_forward(self):
        return False

    def is_shell(self):
        return False

    def is_nested(self):
        return False


@register_type
class ActionForward(Action, Commentable):
    """Forward to other address(es)"""

    type = "forward"

    def __init__(self, recipients=None, comment=None):
        self.recipients = [] if recipients is None else recipients
        self.comment = comment

    def __eq__(self, y):
        if isinstance(y, Action):
            return y.type == self.type and set(self.recipients) == set(y.recipients)
        return False

    def render(self, ident=0):
        return u"%s! %s%s" % ("    " * ident, " ".join(self.recipients), self._get_comment())

    def is_forward(self):
        return True


@register_type
class ActionShell(Action, Commentable):

    type = "shell"

    def __init__(self, cmd, variable=None, comment=None):
        """The pipeline is expected to save the message somewhere;
        you can play with the recipe's flags to tell Procmail otherwise.
        (Always use locking when writing to a file.)

        The output of the command pipeline can be assigned to a variable.
        This makes the recipe non-delivering.
        """
        self.cmd = cmd
        self.variable = variable
        self.comment = comment

    def __eq__(self, y):
        if isinstance(y, Action):
            return y.type == self.type and self.cmd == y.cmd and self.variable == y.variable
        return False

    def is_shell(self):
        return True

    def render(self, ident=0):
        if self.variable:
            variable = "%s=" % self.variable
        else:
            variable = ""
        return u"%s%s|%s%s" % ("    " * ident, variable, self.cmd, self._get_comment())


@register_type
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

    type = "save"

    def __init__(self, path, comment=None):
        self.path = path
        self.comment = comment

    def __eq__(self, y):
        if isinstance(y, Action):
            return y.type == self.type and self.path == y.path
        return False

    def is_save(self):
        return True

    def render(self, ident=0):
        return u"%s%s%s" % ("    " * ident, self.path, self._get_comment())


@register_type
class ActionNested(Action, list):
    """
    Instead of a single action line, an entire block of recipes can be used when the condition
    matches.
    The stuff between the braces can be any valid Procmail construct
    """

    type = "nested"

    def __eq__(self, y):
        if isinstance(y, Action):
            return y.type == self.type and super(ActionNested, self).__eq__(y)
        return False

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

    _recipe_id = None

    def __init__(
        self, header, action, conditions=None, meta_title=None,
        meta_comment=None, comment_condition=None, comment_action=None,
        meta_custom=None
    ):
        self.header = header
        self.action = action
        self.conditions = [] if conditions is None else conditions
        self.meta_title = meta_title
        self.meta_comment = meta_comment
        self.meta_custom = meta_custom
        self.comment_condition = comment_condition
        self.comment_action = comment_action

    def __eq__(self, y):
        if isinstance(y, Recipe):
            if (
                self.header == y.header
                and self.action == y.action
                and self.conditions == y.conditions
            ):
                if self.id is not None and y.id is not None:
                    return self.id == y.id
                else:
                    return True
        return False

    def is_recipe(self):
        return True

    def __getitem__(self, index):
        return self.action[index]

    def _set_id(self):
        set_id(self, self.id + ".", self._recipe_id + ".")

    def __setitem__(self, index, value):
        self._test_item(value, "set")
        self.action[index] = value
        self._set_id()

    def __len__(self):
        if not self.action.is_nested():
            raise ValueError("can only compute length if action is nested")
        return len(self.action)

    def append(self, item):
        self._test_item(item, "append")
        self.action.append(item)
        self._set_id()
        return item.id

    def remove(self, item):
        self._test_item(item, "remove")
        ret = self.action.remove(item)
        self._set_id()
        return ret

    def extend(self, stmts):
        stmt_list = list(stmts)
        if not self.action.is_nested():
            raise ValueError("can only extend if action is nested")
        if not all(isinstance(item, Statement) for item in stmt_list):
            raise ValueError("can only extend with Statement")
        ret = self.action.extend(stmt_list)
        self._set_id()
        return ret

    def index(self, item, *args, **kwargs):
        if not self.action.is_nested():
            raise ValueError("can only index if action is nested")
        return self.action.index(item, *args, **kwargs)

    def count(self):
        if not self.action.is_nested():
            raise ValueError("can only count if action is nested")
        return self.action.count()

    def insert(self, index, item):
        self._test_item(item, "insert")
        self.action.insert(index, item)
        self._set_id()
        return item.id

    def pop(self, *args, **kwargs):
        if not self.action.is_nested():
            raise ValueError("can only pop if action is nested")
        ret = self.action.pop(*args, **kwargs)
        self._set_id()
        return ret

    def reverse(self):
        if not self.action.is_nested():
            raise ValueError("can only reverse if action is nested")
        ret = self.action.reverse()
        self._set_id()
        return ret

    def sort(self):
        if not self.action.is_nested():
            raise ValueError("can only sort if action is nested")
        ret = self.action.sort()
        self._set_id()
        return ret

    def _test_item(self, item, action):
        if not self.action.is_nested():
            raise ValueError("can only %s if action is nested" % action)
        if not isinstance(item, Statement):
            raise ValueError("can only %s Statement" % action)

    def render(self, ident=0):
        s = []
        s.append("\n")
        s.append(self._get_meta(ident))
        s.append(self.header.render(ident))
        s.append("\n")
        if self.comment_condition:
            s.append(self.comment_condition.render(ident))
            s.append("\n")
        for cond in self.conditions:
            s.append(cond.render(ident))
            s.append("\n")
        if self.comment_action:
            s.append(self.comment_action.render(ident))
            s.append("\n")
        s.append(self.action.render(ident))
        s.append("\n")
        return u"".join(s)

    def gen_title(self):
        return "Recipe %s" % self._recipe_id


class ProcmailRc(list):
    """A list of `Statement` objetcs (use subclasses)"""

    id = ""

    def __init__(self, *args, **kwargs):
        super(ProcmailRc, self).__init__(*args, **kwargs)
        self._set_id()

    def _set_id(self):
        set_id(self)

    def append(self, item):
        if not isinstance(item, Statement):
            raise ValueError("can only process Statement")
        super(ProcmailRc, self).append(item)
        self._set_id()
        return item.id

    def remove(self, item):
        if not isinstance(item, Statement):
            raise ValueError("can only process Statement")
        ret = super(ProcmailRc, self).remove(item)
        self._set_id()
        return ret

    def insert(self, index, item):
        if not isinstance(item, Statement):
            raise ValueError("can only process Statement")
        super(ProcmailRc, self).insert(index, item)
        self._set_id()
        return item.id

    def extend(self, stmts):
        stmt_list = list(stmts)
        if not all(isinstance(item, Statement) for item in stmt_list):
            raise ValueError("can only process Statement")
        ret = super(ProcmailRc, self).extend(stmt_list)
        self._set_id()
        return ret

    def pop(self, *args, **kwargs):
        ret = super(ProcmailRc, self).pop(*args, **kwargs)
        self._set_id()
        return ret

    def reverse(self):
        ret = super(ProcmailRc, self).reverse()
        self._set_id()
        return ret

    def sort(self):
        ret = super(ProcmailRc, self).sort()
        self._set_id()
        return ret

    def render(self):
        return u"\n".join(s.render() for s in self)

    def write(self, file, charset="utf-8"):
        data = self.render()
        # check we can still parse the redered data
        new_procmailrc = parseString(data)
        data = data.encode(charset)
        with open(file + '.new', 'w') as f:
            f.write(data)
        os.rename(file + '.new', file)
        return new_procmailrc


def _parse_comment(p):
    return Comment(p.comment[0])


def _parse_assignements(p):
    if p.assignements.comment_line:
        comment = Comment(p.assignements.comment_line[0])
    else:
        comment = None
    meta_title = p.meta_title[0] if p.meta_title else None
    meta_comment = p.meta_comment[0] if p.meta_comment else None
    meta_custom = p.meta_custom[0] if p.meta_custom else None
    variables = []
    for assignment in p.assignements:
        if isinstance(assignment, parser.ParseResults):
            if assignment.shell_eval:
                quote = '`'
            elif assignment.single_quote:
                quote = "'"
            elif assignment.double_quote:
                quote = '"'
            else:
                quote = None
            if len(assignment) >= 2:
                variables.append((assignment[0], assignment[1], quote))
            else:
                variables.append((assignment[0], None, quote))
    return Assignment(
        variables,
        comment=comment,
        meta_title=meta_title,
        meta_comment=meta_comment,
        meta_custom=meta_custom,
    )


def _parse_condition(p, comment=None):
    if p.substitute:
        return ConditionSubstitute(_parse_condition(p.substitute), comment=comment)
    elif p.negate:
        return ConditionNegate(_parse_condition(p.negate), comment=comment)
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
        return ConditionSize(p.size.sign, p.size.size, comment=comment)
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
    if p.action.statements or p.action.statements is not "":
        action = ActionNested(_parse_statements(p.action.statements))
    elif p.action.forward:
        action = ActionForward(p.action.forward.asList(), comment=comment)
    elif p.action.shell:
        action = ActionShell(
            p.action.shell.cmd,
            p.action.shell.variable,
            comment=comment
        )
    elif p.action.path:
        action = ActionSave(p.action.path, comment=comment)
    else:
        raise RuntimeError("Unknown action %r" % p.action)
    return Recipe(
        header, action, conditions,
        meta_title=p.meta_title[0] if p.meta_title else None,
        meta_custom=p.meta_custom[0] if p.meta_custom else None,
        meta_comment=p.meta_comment[0] if p.meta_comment else None,
        comment_condition=Comment(p.comment_condition[0]) if p.comment_condition else None,
        comment_action=Comment(p.comment_action[0]) if p.comment_action else None
    )


def set_id(stmts, prefix="", prefix2=""):
    i = 0
    j = 1
    for stmt in stmts:
        stmt.id = "%s%s" % (prefix, i)
        stmt.parent = stmts
        if stmt.is_recipe():
            stmt._recipe_id = "%s%s" % (prefix2, j)
            j += 1
        if stmt.is_recipe() and stmt.action.is_nested():
            set_id(stmt, stmt.id + ".", stmt._recipe_id + ".")
        i += 1
    if stmts:
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
    return stmt


def parse(file, charset="utf-8"):
    p = parser.parse(file, charset)
    return ProcmailRc(_parse_statements(p))


def parseString(string):
    p = parser.parseString(string)
    return ProcmailRc(_parse_statements(p))
