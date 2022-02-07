
# plain_tohtml.py

from __future__ import print_function

from plain_grammar import Grammar, Rule, Expression, Alternative, Ebnf, Nonterminal, Terminal
from plain_output import Output

try :
   from html import escape
except :
   from cgi import escape

# --------------------------------------------------------------------------

class ToHtml (Output) :

   def putHRef (self, url, txt) :
       self.put ("<a href=" + '"' + url + '"' + ">" + txt + "</a>");

   def putAName (self, name, txt) :
       self.put ("<a name=" + '"' + name + '"' + ">" + txt + "</a>");

   def putHtmlBegin (self) :
       self.putLn ("<!DOCTYPE html>")
       self.putLn ("<html>")
       self.incIndent ()

       self.putLn ("<head>")
       self.incIndent ()
       self.putLn ("<title></title>")
       self.decIndent ()
       self.putLn ("</head>")
       self.putLn ("<body>")
       self.incIndent ()

       self.putLn ("<pre>")

   def putHtmlEnd (self) :
       self.putLn ("</pre>")
       self.decIndent ()
       self.putLn ("</body>")
       self.decIndent ()
       self.putLn ("</html>")

# --------------------------------------------------------------------------

   def htmlFromRules (self, grammar) :
       self.putHtmlBegin ()
       for rule in grammar.rules :
           self.htmlFromRule (grammar, rule)
       self.putHtmlEnd ()

   def htmlFromRule (self, grammar, rule) :
       self.putAName (rule.name, rule.name)
       self.put (" ")
       self.put (":")
       self.putEol ()
       self.incIndent ()
       self.htmlFromExpression (grammar, rule.expr)
       self.putCondEol ()
       self.decIndent ()
       self.put (";")
       self.putEol ()
       self.putEol ()

   def htmlFromExpression (self, grammar, expr) :
       n = 0;
       for alt in expr.alternatives :
          n = n + 1
          if n > 1 :
             self.put ("|")
             self.putEol ()
          self.htmlFromAlternative (grammar, alt)

   def htmlFromAlternative (self, grammar, alt) :
       for item in alt.items :
           if isinstance (item, Terminal) :
              self.htmlFromTerminal (grammar, item)
           elif isinstance (item, Nonterminal) :
              self.htmlFromNonterminal (grammar, item)
           elif isinstance (item, Ebnf) :
              self.htmlFromEbnf (grammar, item)
           else :
              raise Exception ("Unknown alternative item")

   def htmlFromEbnf (self, grammar, ebnf) :
       self.putCondEol ()
       self.put ("(")
       self.putEol ()
       self.incIndent ()
       self.htmlFromExpression (grammar, ebnf.expr)
       self.putEol ()
       self.decIndent ()
       self.put (")")
       if ebnf.mark == '>' :
          self.put (escape (" => "))
       else :
          self.put (ebnf.mark)
       self.putEol ()

   def htmlFromNonterminal (self, grammar, item) :
       name = item.rule_name
       self.putHRef ("#" + name, name)

   def htmlFromTerminal (self, grammar, item) :
       if item.multiterminal_name != "" :
          self.put (item.multiterminal_name)
       else :
          name = item.text
          name = '"' + name + '"'
          self.put (escape (name))

# --------------------------------------------------------------------------

if __name__ == "__main__" :
    grammar = Grammar ()
    grammar.openFile ("./input/cecko.g")
    grammar.parseRules ()

    product = ToHtml ()
    product.htmlFromRules (grammar)

# python small_tohtml.py > tmp.html ; firefox tmp.html

# --------------------------------------------------------------------------

# kate: indent-width 1; show-tabs true; replace-tabs true; remove-trailing-spaces all
