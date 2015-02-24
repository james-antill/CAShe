#! /usr/bin/python -O

try:
    import cashe
except ImportError:
    import sys
    print >> sys.stderr, """\
There was a problem importing one of the Python modules
required to run cashe. The error leading to this problem was:

   %s

Please install a package which provides this module, or
verify that the module is installed correctly.

It's possible that the above module doesn't match the
current version of Python, which is:
%s
""" % (sys.exc_value, sys.version)
    sys.exit(1)

cashe._main()
