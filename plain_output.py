
# plain_output.py

from __future__ import print_function

import sys, time
from io import StringIO, BytesIO

from plain_lexer import quoteString

# --------------------------------------------------------------------------

class Output (object) :

   def __init__ (self) :
       self.initialize ()

   def initialize (self) :
       self.indentation = 0
       self.addSpace = False
       self.extraSpace = False
       self.startLine = True
       self.outputFile = sys.stdout

   def open (self, fileName,) :
       self.initialize ()
       if fileName == "" :
          self.outputFile = sys.stdout
       else :
          self.outputFile = open (fileName, "w")

   def close (self) :
       self.outputFile.close ()
       self.outputFile = sys.stdout

   def write (self, txt) :
       self.outputFile.write (txt)

   # -----------------------------------------------------------------------

   def openString (self) :
       self.initialize ()
       if sys.version_info >= (3,) :
          self.outputFile = StringIO ()
       else :
          self.outputFile = BytesIO ()

   def closeString (self) :
       result = self.outputFile.getvalue ()
       self.outputFile.close ()
       self.outputFile = sys.stdout
       return result

   # -----------------------------------------------------------------------

   # put

   def incIndent (self) :
       self.indentation = self.indentation + 3

   def decIndent (self) :
       self.indentation = self.indentation - 3

   def indent (self) :
       self.incIndent ()

   def unindent (self) :
       self.decIndent ()

   def put (self, txt) :
       if txt != "" :
          if self.startLine :
             self.write (" " * self.indentation)
          self.startLine = False
          self.write (txt)

   def putEol (self) :
       self.startLine = True
       self.addSpace = False
       self.extraSpace = False
       self.write ("\n")

   def putCondEol (self) :
       if not self.startLine :
          self.putEol ()

   def putLn (self, txt = "") :
       if txt != "":
          self.put (txt)
       self.putEol ()

   # -----------------------------------------------------------------------

   # send

   def isLetterOrDigit (self, c) :
       return c >= 'A' and c <= 'Z' or c >= 'a' and c <= 'z' or c >= '0' and c <= '9' or c == '_'

   def send (self, txt) :
       if txt != "" :
          if self.startLine :
             self.write (" " * self.indentation)
             self.addSpace = False
             self.extraSpace = False
          self.startLine = False

          c = txt [0]
          if c == ',' or c == ';' or c == ')' :
             self.extraSpace = False
          if not self.isLetterOrDigit (c) :
             self.addSpace = False

          if self.addSpace or self.extraSpace :
             txt = " " + txt

          self.write (txt)

          c = txt [-1]
          self.addSpace = self.isLetterOrDigit (c)
          self.extraSpace = c != '('

   def sendChr (self, txt) :
       self.send (quoteString (txt, "'"))

   def sendStr (self, txt) :
       self.send (quoteString (txt))

   def style_no_space (self) :
       self.extraSpace = False

   def style_indent (self) :
       self.putCondEol ()
       self.incIndent ()

   def style_unindent (self) :
       self.decIndent ()
       self.putCondEol ()

   def style_new_line (self) :
       self.putCondEol ()

   def style_empty_line (self) :
       self.putCondEol ()
       self.putLn ()

# --------------------------------------------------------------------------

# kate: indent-width 1; show-tabs true; replace-tabs true; remove-trailing-spaces all
