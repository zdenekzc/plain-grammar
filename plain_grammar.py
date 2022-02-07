
# plain_grammar.py

from __future__ import print_function

from plain_lexer import Lexer

# --------------------------------------------------------------------------

class Rule (object) :
   def __init__ (self) :
       self.name = ""
       self.expr = None
       # self.nullable = False
       # self.first = [ ]
       # self.line = 1

class Expression (object) :
   def __init__ (self) :
       self.alternatives = [ ]
       # self.nullable = False
       # self.first = [ ]
       # self.follow = [ ]
       # self.line = 1

class Alternative (object) :
   def __init__ (self) :
       self.items = [ ]
       # self.nullable = False
       # self.first = [ ]
       # self.follow = [ ]
       # self.line = 1

class Ebnf (object) :
   def __init__ (self) :
       self.mark = ""
       self.expr = None
       # self.nullable = False
       # self.first = [ ]
       # self.follow = [ ]
       # self.line = 1

class Nonterminal (object) :
   def __init__ (self) :
       self.rule_name = ""
       # self.symbol = None
       # self.nullable = False
       # self.first = [ ]
       # self.line = 1

class Terminal (object) :
   def __init__ (self) :
       self.text = ""
       self.multiterminal_name = ""
       # self.nullable = False
       # self.first = [ ]
       # self.line = 1

# --------------------------------------------------------------------------

class Grammar (Lexer) :

   def __init__ (self) :
       super (Grammar, self).__init__ ()
       self.rules = [ ]
       self.multiterminals = [ "identifier",
                               "number",
                               "real_number",
                               "character_literal",
                               "string_literal" ]

       # self.multiterminal_dict = { }
       # self.keyword_dict = { }
       # self.separator_dict = { }
       #
       # self.symbol_cnt = 0
       # self.symbols = [ ]
       # self.symbol_dict = { }
       #
       # self.rule_dict = { }
       # self.nullableChanged = True
       # self.firstChanged = True
       # self.followChanged = True

   def setPosition (self, item) :
       # item.src_file = self.fileName
       item.src_line = self.tokenLineNum
       item.src_column = self.tokenColNum
       item.src_pos = self.tokenByteOfs

   def updatePosition (self, item) :
       "set position for error reporting, used by small_symbols"
       self.tokenLineNum = item.src_line
       self.tokenColNum = item.src_column
       self.tokenByteOfs = item.src_pos

   # -- rules --

   def parseRules (self) :
       while not self.isEndOfSource () :
             self.parseRule ()

   def parseRule (self) :
       rule = Rule ()

       rule.name = self.readIdentifier ("Rule identifier expected")
       self.setPosition (rule)

       self.checkSeparator (':')
       rule.expr = self.parseExpression ()
       self.checkSeparator (';')

       self.rules.append (rule)

   # -- expression --

   def parseExpression (self) :
       expr = Expression ()
       self.setPosition (expr)

       alt = self.parseAlternative ()
       expr.alternatives.append (alt)

       while self.isSeparator ('|') :
          self.nextToken ()

          alt = self.parseAlternative ()
          expr.alternatives.append (alt)

       return expr

   def parseAlternative (self) :
       alt = Alternative ()
       self.setPosition (alt)

       while not self.isSeparator ('|') and not self.isSeparator (')') and not self.isSeparator (';') :

          if self.token == self.identifier :
             if self.tokenText in self.multiterminals :
                item = self.parseMultiterminal ()
             else :
                item = self.parseNonterminal ()
             alt.items.append (item)

          elif self.token == self.character_literal or self.token == self.string_literal :
             item = self.parseTerminal ()
             alt.items.append (item)

          elif self.isSeparator ('(') :
             ebnf = self.parseEbnf ()
             alt.items.append (ebnf)

          else :
             self.error ("Unknown grammar item")

       return alt

   def parseEbnf (self) :
       item = Ebnf ()
       self.setPosition (item)

       self.checkSeparator ('(')
       item.expr = self.parseExpression ()
       self.checkSeparator (')')

       if self.isSeparator ('?') or self.isSeparator ('+') or self.isSeparator ('*') :
          item.mark = self.tokenText
          self.nextToken ()

       return item

   def parseNonterminal (self) :
       item = Nonterminal ()
       self.setPosition (item)
       item.rule_name = self.tokenText
       self.nextToken ()
       return item

   def parseTerminal (self) :
       item = Terminal ()
       self.setPosition (item)
       item.text = self.tokenText
       self.nextToken ()
       return item

   def parseMultiterminal (self) :
       item = Terminal ()
       self.setPosition (item)
       item.multiterminal_name = self.tokenText
       self.nextToken ()
       return item

# --------------------------------------------------------------------------

if __name__ == "__main__" :
    grammar = Grammar ()
    grammar.openFile ("./input/cecko.g")
    grammar.parseRules ()
    for rule in grammar.rules :
       print (rule.name)

# kate: indent-width 1; show-tabs true; replace-tabs true; remove-trailing-spaces all
