Pyprocmail
==================


.. image:: https://img.shields.io/pypi/v/pyprocmail.svg
    :target: https://pypi.python.org/pypi/pyprocmail

.. image:: https://img.shields.io/pypi/l/pyprocmail.svg
    :target: https://www.gnu.org/licenses/gpl-3.0.html

Pyprocmail is a python parser and AST definitions for procmail's procmailrc files.

The grammar of procmailrc files is build after `<quickref.html>`_.


Installation
------------

Install with pip::

    sudo pip install pyprocmail

or from source code::

    sudo make install


Basic usages
------------

.. code-block:: python

    In [1]: import pyprocmail

    In [2]: prc = pyprocmail.parse("examples/procmailrc1")

    In [3]: prc
    Out[3]: 
    [<pyprocmail.procmail.Comment at 0x7fdaf8dc1fd0>,
     <pyprocmail.procmail.Comment at 0x7fdaf8dc8850>,
     <pyprocmail.procmail.Comment at 0x7fdaf8d9d790>,
     <pyprocmail.procmail.Comment at 0x7fdaed0bb4d0>,
     <pyprocmail.procmail.Comment at 0x7fdaed0bbf90>,
     <pyprocmail.procmail.Comment at 0x7fdaed0bbd90>,
     <pyprocmail.procmail.Comment at 0x7fdaed0b10d0>,
     <pyprocmail.procmail.Comment at 0x7fdaed0b1bd0>,
     <pyprocmail.procmail.Assignment at 0x7fdaed0c52d0>,
     ...
     <pyprocmail.procmail.Comment at 0x7fdaed0c8ad0>,
     <pyprocmail.procmail.Recipe at 0x7fdaed0c8bd0>,
     <pyprocmail.procmail.Comment at 0x7fdaed0c8c10>,
     <pyprocmail.procmail.Recipe at 0x7fdaed0c8cd0>]

    In [4]: prc[8].render()
    Out[4]: u'PATH=/bin:/usr/bin:/usr/local/bin:/opt/local/bin/:$HOME/bin:$HOME:'

    In [5]: prc[-1].is_recipe()
    Out[5]: True

    In [6]: prc[-1].action.is_save()
    Out[6]: True

    In [7]: prc[-1].action.path
    Out[7]: u'/dev/null'

    In [8]: prc[-1].action.path = "INBOX"

    In [9]: print prc[-1].render()

    :0
    INBOX

