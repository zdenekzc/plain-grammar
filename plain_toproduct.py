
# plain_toproduct.py

from __future__ import print_function

from plain_grammar import Grammar, Rule, Expression, Alternative, Ebnf, Nonterminal, Terminal
from plain_output import Output
from plain_toparser import ToParser

# --------------------------------------------------------------------------

decode_tree = True # decode_tree requires generate_tree and extended_tree in plain_toparser

class ToProduct (Output) :

   def __init__ (self) :
       super (ToProduct, self).__init__ ()

   def productFromRules (self, grammar) :
       self.last_rule = None
       for rule in grammar.rules :
           self.productFromRule (grammar, rule)

   def productFromRule (self, grammar, rule) :
       grammar.updatePosition (rule)
       if decode_tree :
          self.putLn ("def send_" + rule.name + " (self, param) :")
       else :
          self.putLn ("def send_" + rule.name + " (self) :")

       self.incIndent ()
       if decode_tree :
          self.putLn ("inx = 1") # skip rule name
       self.productFromExpression (grammar, rule, rule.expr)
       self.decIndent ()
       self.putEol ()

   def recall (self, variable) :
       if decode_tree :
          self.putLn (variable + " = param [inx]")
          self.putLn ("inx = inx + 1")

   def productFromExpression (self, grammar, rule, expr) :
       cnt = len (expr.alternatives)
       inx = 0
       if cnt > 1 :
          self.recall ("alt")
       for alt in expr.alternatives :
           if cnt > 1 :
              cond = "cond"
              if decode_tree :
                 cond = "alt == " + str (inx)
              if inx == 0 :
                 self.putLn ("if " + cond + " :")
              else :
                 self.putLn ("elif " + cond + " :")
              self.incIndent ()
           self.productFromAlternative (grammar, rule, alt)
           if cnt > 1 :
              self.decIndent ()
           inx = inx + 1

   def productFromAlternative (self, grammar, rule, alt) :
       grammar.updatePosition (alt)
       any = False
       for item in alt.items :
           if isinstance (item, Terminal) :
              self.productFromTerminal (grammar, item)
              any = True
           elif isinstance (item, Nonterminal) :
              self.productFromNonterminal (grammar, item)
              any = True
           elif isinstance (item, Ebnf) :
              self.productFromEbnf (grammar, rule, item)
              any = True
           else :
              raise Exception ("Unknown alternative item")
       if not any :
          self.putLn ("pass")

   def productFromEbnf (self, grammar, rule, ebnf) :
       grammar.updatePosition (ebnf)
       block = False

       cond = "cond"
       if decode_tree :
          if ebnf.mark == '?' or ebnf.mark == '*' or ebnf.mark == '+' :
             self.recall ("cont")
             cond = "cont"

       if ebnf.mark == '?' :
          self.putLn ("if " + cond + " :")
          block = True
       if ebnf.mark == '*' or ebnf.mark == '+' :
          self.putLn ("while " + cond + " :")
          block = True

       if block :
          self.incIndent ()

       self.productFromExpression (grammar, rule, ebnf.expr)

       if decode_tree :
          if ebnf.mark == '*' or ebnf.mark == '+' :
             self.recall ("cont")

       if block :
          self.decIndent ()

   def productFromNonterminal (self, grammar, item) :
       grammar.updatePosition (item)
       proc = "send_" + item.rule_name
       param = "value"
       if decode_tree :
          self.recall ("value")
          param = "value"

       self.putLn ("self." + proc + " (" + param + ")")

   def productFromTerminal (self, grammar, item) :
       if item.multiterminal_name != "" :

          param = "value"
          if decode_tree :
             self.recall ("value")
             param = "value"

          self.putLn ("self.send (" + param + ")")

       else :
          self.putLn ("self.send (" + '"' + item.text + '"' + ")")

# --------------------------------------------------------------------------

   def productFromGrammar (self, grammar, parser_module = "") :

       self.putLn ()
       if parser_module != "" :
          self.putLn ("from " + parser_module + " import *")
       self.putLn ("from plain_output import Output")
       self.putLn ()

       self.putLn ("class Product (Output) :")
       self.putLn ("")
       self.incIndent ()

       self.productFromRules (grammar)

       self.decIndent ()

# --------------------------------------------------------------------------

if __name__ == "__main__" :
    grammar = Grammar ()
    grammar.openFile ("./input/cecko.g")
    grammar.parseRules ()

    product = ToParser ()
    product.parserFromGrammar (grammar)

    product = ToProduct ()
    product.productFromGrammar (grammar)

# --------------------------------------------------------------------------

# kate: indent-width 1; show-tabs true; replace-tabs true; remove-trailing-spaces all
