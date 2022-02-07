
# plain_tolout.py

from __future__ import print_function

from plain_grammar import Grammar, Rule, Expression, Alternative, Ebnf, Nonterminal, Terminal
from plain_output import Output

# --------------------------------------------------------------------------

class ToLout (Output) :

   def loutFromRules (self, grammar) :
       self.putLn ("@SysInclude { tbl }")
       self.putLn ("@SysInclude { diag }")
       self.putLn ("@SysInclude { xrgb }") # colors
       self.putLn ("@SysInclude { doc }")
       self.putLn ("@Doc @Text @Begin")
       self.putLn ("")
       for rule in grammar.rules :
           self.loutFromRule (grammar, rule)
       self.putLn ("@End @Text")

   def loutFromRule (self, grammar, rule) :
       self.putLn ("@SyntaxDiag")
       self.putLn ("title {" + rule.name + "}")
       self.putLn ("{")
       self.incIndent ()

       self.putLn ("@StartRight")

       self.loutFromExpression (grammar, rule.expr)

       self.decIndent ()
       self.putLn ("}")
       self.putLn ("@PP")
       self.putLn ("@PP")
       self.putLn ("")

   def loutFromExpression (self, grammar, expr) :
       count = len (expr.alternatives)
       if count == 0 :
          self.putLn ("@Skip")
       if count > 1 :
          self.putLn ("@Select")

       inx = 0
       groups = 0 # groups of 10 items
       for alt in expr.alternatives :
           inx = inx + 1
           if count > 1 :
              self.put (self.nodeName (inx) + " {")
              self.incIndent ()
              if inx == 10 and count > 10 : # maximum is 10 items
                 self.putEol ()
                 self.putLn ("@Select")
                 inx = 1 # count again from 1
                 groups = groups + 1
                 self.put (self.nodeName (inx) + " {")
           self.loutFromAlternative (grammar, alt)
           if count > 1 :
              self.decIndent ()
              self.putLn ("}")

       while groups > 0 :
          self.decIndent ()
          self.putLn ("}")
          groups = groups - 1

   def nodeName (self, inx) :
       if inx <= 26 :
           name = chr (ord ('A') + inx - 1)
       else :
           name = 'Z' + str (inx)
       return name

   def loutFromAlternative (self, grammar, alt) :
       count = len (alt.items)
       if count == 0 :
          self.putLn ("@Skip")
       if count > 1 :
          self.putLn ("@Sequence")

       inx = 0
       groups = 0
       for item in alt.items :
           inx = inx + 1
           if count > 1 :
              self.put (self.nodeName (inx) + " {")
              self.incIndent ()
              if inx == 10 and count > 10 : # maximum is 10 items
                 self.putEol ()
                 self.putLn ("@Sequence")
                 inx = 1 # count again from 1
                 groups = groups + 1
                 self.put (self.nodeName (inx) + " {")
           if isinstance (item, Terminal) :
              self.loutFromTerminal (grammar, item)
           elif isinstance (item, Nonterminal) :
              self.loutFromNonterminal (grammar, item)
           elif isinstance (item, Ebnf) :
              self.loutFromEbnf (grammar, item)
           elif isinstance (item, Directive) :
              pass
           else :
              raise Exception ("Unknown alternative item")
           if count > 1 :
              self.decIndent ()
              self.putLn ("}")

       while groups > 0 :
          self.decIndent ()
          self.putLn ("}")
          groups = groups - 1

   def loutFromEbnf (self, grammar, ebnf) :
       if ebnf.mark != '>' :
          if ebnf.mark == '?' :
             self.putLn ("@Optional")
          if ebnf.mark == '*' :
             self.putLn ("@Optional")
             self.putLn ("@RepeatOpposite")
          if ebnf.mark == '+' :
             self.putLn ("@Optional")
             self.putLn ("@RepeatOpposite")
          self.incIndent ()
          self.loutFromExpression (grammar, ebnf.expr)
          self.decIndent ()

   def loutFromNonterminal (self, grammar, item) :
       name = item.rule_name
       self.put ("@ACell " + '"' + name + '"')

   def loutFromTerminal (self, grammar, item) :
       if item.multiterminal_name != "" :
          value = item.multiterminal_name
          value = "@BCell " + value
          value = "{ @Xrgb orange } @Color " + value
       else :
          value = item.text
          value = '"' + value + '"'
          if len (value) == 1 :
             value = "@CCell " + value
          else :
             value = "@BCell " + value
          value = "blue @Color " + value
       self.put (value)

# --------------------------------------------------------------------------

if __name__ == "__main__" :
    grammar = Grammar ()
    grammar.openFile ("./input/cecko.g")
    grammar.parseRules ()

    product = ToLout ()
    product.loutFromRules (grammar)

# python small_tolout.py > tmp.lout && lout tmp.lout -o tmp.ps && atril tmp.ps

# --------------------------------------------------------------------------

# kate: indent-width 1; show-tabs true; replace-tabs true; remove-trailing-spaces all
