
# plain_toparser.py

from __future__ import print_function

import time

from plain_grammar import Grammar, Rule, Expression, Alternative, Ebnf, Nonterminal, Terminal
from plain_symbols import Symbol, initSymbols
from plain_lexer   import quoteString
from plain_output  import Output

# --------------------------------------------------------------------------

generate_tree = True
extended_tree = True

class ToParser (Output) :

   def extended_info (self, value) :
       if generate_tree and extended_tree :
          self.putLn ("result.append (" + str (value) + ")")

   def addToDictionary (self, tree, name) :
       ref = tree
       for c in name :
           if c not in ref :
               ref[c] = { }
           ref = ref[c]

   def prindKeywordItem (self, dictionary, inx, name) :
       self.incIndent ()
       if len (dictionary) == 0 :
          self.putLn ("self.token = " + "self.keyword_" + name )
       else :
          self.printKeywordDictionary (dictionary, inx+1, name)
       self.decIndent ()

   def printKeywordDictionary (self, dictionary, inx, name) :
       if len (dictionary) == 1 :
          start_inx = inx
          substr = ""
          while len (dictionary) == 1:
             for c in sorted (dictionary.keys ()) : # only one
                 substr = substr + c
                 dictionary = dictionary [c]
                 inx = inx + 1
                 name = name + c
          inx = inx - 1
          if start_inx == inx :
             self.putLn ("if s[" + str (inx) + "] == " + "'" + substr + "'" + " :")
          else :
             self.putLn ("if s[" + str (start_inx) + ":" + str (inx+1) + "] == " + '"' + substr + '"' + " :")
          self.prindKeywordItem (dictionary, inx, name)
       else :
           first_item = True
           for c in sorted (dictionary.keys ()) :
               if first_item :
                  cmd = "if"
                  first_item = False
               else :
                  cmd = "elif"
               self.putLn (cmd + " s[" + str (inx) + "] == "  "'" + c + "'" + " :")
               self.prindKeywordItem (dictionary[c], inx, name+c)

   def selectKeywords (self, grammar) :
       self.putLn ("def lookupKeyword (self) :")
       self.incIndent ()
       self.putLn ("s = self.tokenText")
       self.putLn ("n = len (s)")

       lim = 0
       for name in grammar.keyword_dict :
           n = len (name)
           if n > lim :
              lim = n

       size = 1
       first_item = True
       while size <= lim :
          tree = { }
          for name in grammar.keyword_dict :
              if len (name) == size :
                 self.addToDictionary (tree, name)
          if len (tree) != 0 :
             if first_item :
                cmd = "if"
                first_item = False
             else :
                cmd = "elif"
             self.putLn (cmd + " n == " + str (size) + " :")
             self.incIndent ()
             self.printKeywordDictionary (tree, 0, "")
             self.decIndent ()
          size = size + 1

       self.decIndent ()
       self.putLn ()

# --------------------------------------------------------------------------

   def printDictionary (self, dictionary) :
       for c in sorted (dictionary.keys ()) :
           self.putLn ("'" + c + "'" + " :")
           self.incIndent ()
           if len (dictionary[c]) == 0 :
              self.putLn ("#")
           else :
              printDictionary (dictionary[c])
           self.decIndent ()

   def selectBranch (self, grammar, dictionary, level, prefix) :
       for c in sorted (dictionary.keys ()) :
           if level == 1 :
              self.putLn ("if self.tokenText == " + "'" + c + "'" + " :")
           else :
              self.putLn ("if self.ch == " + "'" + c + "'" + " :")
           self.incIndent ()
           name = prefix + c
           if name in grammar.separator_dict :
              self.putLn ("self.token = " + str ( grammar.separator_dict[name].inx)) # !?
           if level > 1 :
              self.putLn ("self.tokenText = self.tokenText + self.ch")
              self.putLn ("self.nextChar ()")
           if len (dictionary[c]) != 0 :
              self.selectBranch (grammar, dictionary[c], level+1, prefix+c)
           self.decIndent ()

   def selectSeparators (self, grammar) :
       self.putLn ("def processSeparator (self) :")
       self.incIndent ()

       tree = { }
       for name in grammar.separator_dict :
           self.addToDictionary (tree, name)

       self.selectBranch (grammar, tree, 1, "")

       self.putLn ("if self.token == self.separator :")
       self.incIndent ()
       self.putLn ("self.error (" + '"' + "Unknown separator" + '"' + ")")
       self.decIndent ()

       self.decIndent ()
       self.putLn ()

   # -----------------------------------------------------------------------

   def declareTerminals (self, grammar) :
       for symbol in grammar.symbols :
           if symbol.keyword :
              self.putLn ("self." + symbol.ident + " = " + str (symbol.inx))
           elif symbol.separator :
              if symbol.ident != "" :
                 self.putLn ("self." + symbol.ident + " = " + str (symbol.inx) + " # " + symbol.text)
              else :
                 self.putLn ("# " + symbol.text + " " + str (symbol.inx))
           else :
              self.putLn ("# " + symbol.ident + " = " + str (symbol.inx))

   def convertTerminals (self, grammar) :
       self.putLn ("def tokenToString (self, value) :")
       self.incIndent ()

       for symbol in grammar.symbols :
           self.putLn ("if value == " + str (symbol.inx) + ": " + "return " + '"' + symbol.alias + '"')

       self.putLn ("return " + '"' + "<unknown symbol>" + '"')
       self.decIndent ()
       self.putLn ()

   # --------------------------------------------------------------------------

   def initCollections (self, grammar) :
       grammar.collections = [ ]

   def registerCollection (self, grammar, collection) :
       "collection is set of (at least four) symbols"
       data = [ ]
       for inx in range (len (collection)) :
           if collection [inx] :
              data = data + [inx]
       if data not in grammar.collections :
          grammar.collections = grammar.collections + [data]
       return grammar.collections.index (data)

   def declareStoreLocation (self, grammar) :
       self.putLn ("def storeLocation (self, item) :")
       self.incIndent ()
       # self.putLn ("item.src_file = self.tokenFileInx")
       self.putLn ("item.src_line = self.tokenLineNum")
       self.putLn ("item.src_column = self.tokenColNum")
       self.putLn ("item.src_pos = self.tokenByteOfs")
       self.putLn ("item.src_end = self.charByteOfs")
       self.decIndent ()
       self.putLn ()

   def declareAlloc (self, grammar) :
       self.putLn ("def alloc (self, items) :")
       self.incIndent ()
       self.putLn ("result = [False] * " + str (grammar.symbol_cnt))
       self.putLn ("for item in items :")
       self.incIndent ()
       self.putLn ("result [item] = True")
       self.decIndent ()
       self.putLn ("return result")
       self.decIndent ()
       self.putLn ()

   def declareCollections (self, grammar) :
       num = 0
       for data in grammar.collections :

           self.put ("self.set_" + str (num) + " = self.alloc (" )

           self.put ("[")
           any = False
           for inx in data :
              if any :
                 self.put (", ")
              any = True
              symbol = grammar.symbols [inx]
              if symbol.ident != "" :
                 self.put ("self." + symbol.ident)
              else :
                 self.put (str (inx))
           self.put ("]")

           self.put ( ") #" )

           for inx in data :
               self.put (" ")
               symbol = grammar.symbols [inx]
               if symbol.text != "" :
                  self.put (" " +symbol.text)
               else :
                  self.put (" " +symbol.ident)

           self.putEol ()
           num = num + 1

   def condition (self, grammar, collection) :
       cnt = 0
       for inx in range (len (collection)) :
           if collection [inx] :
              cnt = cnt + 1

       complex = False
       if cnt == 0 :
          # grammar.error ("Empty set")
          # return "nothing"
          code = "True" # !?
       elif cnt <= 3 :
          if cnt > 1 :
             complex = True
          code = ""
          start = True
          for inx in range (len (collection)) :
              if collection [inx] :
                 if not start :
                    code = code + " or "
                 start = False
                 symbol = grammar.symbols[inx]
                 if symbol.text != "" :
                    code = code + "self.tokenText == " + '"' + symbol.text + '"'
                 else :
                    code = code + "self.token == self." + symbol.ident
       else :
          num = self.registerCollection (grammar, collection)
          code = "self.set_" + str (num) + " [self.token]";

       return code

   def conditionFromAlternative (self, grammar, alt) :
       code = self.condition (grammar, alt.first)
       return code

   def conditionFromExpression (self, grammar, expr) :
       code = ""
       for alt in expr.alternatives :
           if code != "" :
              code = code + " or "
           code = code + self.conditionFromAlternative (grammar, alt)
       return code

   def conditionFromRule (self, grammar, name) :
       if name not in grammar.rule_dict :
          grammar.error ("Unknown rule: " + name)
       rule = grammar.rule_dict [name]
       return self.condition (grammar, rule.first)

   # -----------------------------------------------------------------------

   def simpleExpression (self, expr) :
       simple = len (expr.alternatives) != 0
       for alt in expr.alternatives :
           if not self.simpleAlternative (alt) :
              simple = False
       return simple

   def simpleAlternative (self, alt) :
       simple = False
       if len (alt.items) == 1 :
          item = alt.items [0]
          if isinstance (item, Terminal) :
             simple = True
       return simple

   # def simpleEbnf (self, ebnf) :
   #     return self.simpleExpression (ebnf.expr)

   # -----------------------------------------------------------------------

   def parserFromRules (self, grammar) :
       for rule in grammar.rules :
           self.parserFromRule (grammar, rule)

   def parserFromRule (self, grammar, rule) :
       grammar.updatePosition (rule)

       self.putLn ("def parse_" + rule.name + " (self) :")

       self.incIndent ()

       if generate_tree :
           if extended_tree :
              self.putLn ("result = [ " + quoteString (rule.name) + " ]")
           else :
              self.putLn ("result = [ ]")

       self.parserFromExpression (grammar, rule, rule.expr)

       if generate_tree :
          self.putLn ("return result")

       self.decIndent ()
       self.putEol ()

   def parserFromExpression (self, grammar, rule, expr) :
       cnt = len (expr.alternatives)
       inx = 0
       start = True
       for alt in expr.alternatives :
           if cnt > 1 :
              cond = self.conditionFromAlternative (grammar, alt)
              if start :
                 self.put ("if")
              else :
                 self.put ("elif")
              start = False
              self.putLn (" " + cond + " :")
              self.incIndent ()
              self.extended_info (str (inx)) # alternative number
           self.parserFromAlternative (grammar, rule, alt)
           if cnt > 1 :
              self.decIndent ()
           inx = inx + 1
       if cnt > 1 :
          self.putLn ("else :")
          self.incIndent ()
          self.putLn ("self.error (" +  '"' + "Unexpected token" + '"' + ")")
          self.decIndent ()

   def parserFromAlternative (self, grammar, rule, alt) :
       for item in alt.items :
           if isinstance (item, Terminal) :
              self.parserFromTerminal (grammar, rule, item)
           elif isinstance (item, Nonterminal) :
              self.parserFromNonterminal (grammar, rule, item)
           elif isinstance (item, Ebnf) :
              self.parserFromEbnf (grammar, rule, item)
           else :
              grammar.error ("Unknown alternative item: " + item.__class__.__name__)

   def parserFromEbnf (self, grammar, rule, ebnf) :
       if ebnf.mark == '?' :
          self.put ("if ")
       elif ebnf.mark == '*' :
          self.put ("while ")
       elif ebnf.mark == '+' :
          self.put ("while ")

       if ebnf.mark != "" :
          cond = self.conditionFromExpression (grammar, ebnf.expr)
          self.put (cond)
          self.putLn (" :")
          self.incIndent ()
          self.extended_info (True) # enter into branch

       self.parserFromExpression (grammar, rule, ebnf.expr)

       if ebnf.mark != "" :
          self.decIndent ()

       if ebnf.mark == "+" or ebnf.mark == "*" :
          self.extended_info (False) # end of loop

       if ebnf.mark == "?" :
          self.putLn ("else :")
          self.incIndent ()
          self.extended_info (False) # end of loop
          self.decIndent ()

   def parserFromNonterminal (self, grammar, rule, item) :

       if generate_tree :
          self.put ("result.append (")

       self.put ("self.parse_" + item.rule_name + " ()")

       if generate_tree :
          self.put (")")

       self.putEol ()

   def parserFromTerminal (self, grammar, rule, item) :
       symbol = item.symbol_ref
       if symbol.multiterminal :

          func = symbol.ident
          if func.endswith ("_number") :
             func = func [ : -7 ]
          if func.endswith ("_literal") :
             func = func [ : -8 ]
          func = "read" + func.capitalize()

          if generate_tree :
             self.put ("result.append (")

          self.put ("self." + func + " ()")

          if generate_tree :
             self.put (")")

          self.putEol ()
       else :
          if symbol.text != "":
             self.putLn ("self.check (" + '"' + symbol.text + '"' + ")")

   # -----------------------------------------------------------------------

   def note (self, txt) :
       # txt == "" ... init timer
       if 0 :
          start = self.start
          stop = time.clock ()
          if start == 0 :
             start = stop # first time measurement
          if txt != "" :
             print (txt + ", time %0.4f s" % (stop - start))
          self.start = stop

   # -----------------------------------------------------------------------

   def parserFromGrammar (self, grammar, class_name = "Parser") :
       self.note ("")
       grammar.parseRules ()
       self.note ("grammar parsed")

       initSymbols (grammar)
       self.initCollections (grammar)
       self.note ("symbols initialized")

       self.putLn ()
       self.putLn ("from plain_lexer import Lexer")
       self.putLn ()

       self.putLn ("class " + class_name + " (Lexer) :")
       self.incIndent ()

       self.parserFromRules (grammar)
       self.note ("parser methods generated")

       self.selectKeywords (grammar)
       self.selectSeparators (grammar)
       self.convertTerminals (grammar)
       self.declareStoreLocation (grammar)
       self.declareAlloc (grammar)

       self.putLn ("def __init__ (self) :")
       self.incIndent ()
       self.putLn ("super (" + class_name + ", self).__init__ ()")
       self.putLn ()
       self.declareTerminals (grammar)
       self.putLn ()
       self.declareCollections (grammar)
       self.decIndent ()
       self.putLn ()

       self.decIndent () # end of class

       self.note ("finished")

# --------------------------------------------------------------------------

if __name__ == "__main__" :
    grammar = Grammar ()
    grammar.openFile ("./input/cecko.g")

    product = ToParser ()
    product.parserFromGrammar (grammar)

# --------------------------------------------------------------------------

# kate: indent-width 1; show-tabs true; replace-tabs true; remove-trailing-spaces all
