
# plain_symbols.py

from __future__ import print_function

from plain_grammar import Grammar, Rule, Expression, Alternative, Ebnf, Nonterminal, Terminal

# --------------------------------------------------------------------------

class Symbol (object) :
   def __init__ (self) :
       self.inx = 0
       self.text = ""
       self.ident = ""
       self.alias = ""
       self.multiterminal = False
       self.keyword = False
       self.separator = False

# --------------------------------------------------------------------------

def addSymbol (grammar, symbol) :
    symbol.inx = grammar.symbol_cnt
    grammar.symbol_cnt = grammar.symbol_cnt + 1
    grammar.symbols.append (symbol)

def symbolsFromRules (grammar) :

    grammar.multiterminal_dict = {  }
    grammar.keyword_dict = { }
    grammar.separator_dict = { }

    # multiterminals

    multiterminal_list = [  ]

    for name in grammar.multiterminals :
        symbol = Symbol ()
        symbol.text = ""
        symbol.ident = name
        symbol.alias = "<" + name + ">"
        symbol.multiterminal = True
        multiterminal_list.append (symbol)
        grammar.multiterminal_dict [name] = symbol

    # setup rule_dict, keyword_dict, separator_dict

    grammar.rule_dict = { }

    for rule in grammar.rules :
        if rule.name in grammar.rule_dict :
           grammar.error ("Rule " + rule.name + " already defined")
        grammar.rule_dict [rule.name] = rule

    for rule in grammar.rules :
        grammar.updatePosition (rule)
        symbolsFromExpression (grammar, rule.expr)

    # list of symbols

    grammar.symbol_cnt= 0
    grammar.symbols = [ ]

    symbol = Symbol ()
    symbol.text = ""
    symbol.ident = "eos";
    symbol.alias = "<end of source text>";
    addSymbol (grammar, symbol)

    for symbol in multiterminal_list :
        addSymbol (grammar, symbol)

    symbol = Symbol ()
    symbol.text = ""
    symbol.ident = "separator";
    symbol.alias = "<unknown separator>";
    addSymbol (grammar, symbol)

    symbol = Symbol ()
    symbol.text = ""
    symbol.ident = "end_of_line";
    symbol.alias = "<end of line>";
    addSymbol (grammar, symbol)

    for key in sorted (grammar.keyword_dict.keys()) :
        symbol = grammar.keyword_dict [key]
        addSymbol (grammar, symbol)

    for key in sorted (grammar.separator_dict.keys()) :
        symbol = grammar.separator_dict [key]
        addSymbol (grammar, symbol)

    if 0 :
       grammar.separator_dict["."].ident = "symbol_dot"
       grammar.separator_dict[","].ident = "symbol_comma"

# --------------------------------------------------------------------------

def symbolsFromExpression (grammar, expr) :
    for alt in expr.alternatives :
       symbolsFromAlternative (grammar, alt)

def symbolsFromAlternative (grammar, alt) :
    for item in alt.items :
        if isinstance (item, Terminal) :
           symbolsFromTerminal (grammar, item)
        elif isinstance (item, Nonterminal) :
           symbolsFromNonterminal (grammar, item)
        elif isinstance (item, Ebnf) :
           symbolsFromEbnf (grammar, item)
        else :
           grammar.error ("Unknown alternative item " + item.__class__.__name__)

def symbolsFromEbnf (grammar, ebnf) :
    symbolsFromExpression (grammar, ebnf.expr)

def symbolsFromNonterminal (grammar, item) :
    name = item.rule_name

    if name not in grammar.rule_dict:
       grammar.error ("Unknown rule: " + name)
    item.rule_ref = grammar.rule_dict [name]
    # print ("NONTERMINAL", name)

def symbolsFromTerminal (grammar, item) :
    grammar.updatePosition (item)
    if item.multiterminal_name != "" :
       name = item.multiterminal_name
       item.symbol_ref = grammar.multiterminal_dict [name]
       # print ("MULTI-TERMINAL", name)
    else :
       name = item.text
       if grammar.isLetter (name [0]) :
          if name in grammar.keyword_dict :
             symbol = grammar.keyword_dict [name]
          else :
             symbol = Symbol ()
             symbol.text = name
             symbol.ident = "keyword_" + name
             # symbol.alias = '"' + name + '"'
             symbol.alias = name
             symbol.keyword = True
             grammar.keyword_dict [name] = symbol
       else :
          if name in grammar.separator_dict :
             symbol = grammar.separator_dict [name]
          else :
             symbol = Symbol ()
             symbol.text = name
             symbol.ident = ""
             # symbol.alias = '"' + name + '"'
             symbol.alias = name
             symbol.separator = True
             grammar.separator_dict [name] = symbol
       item.symbol_ref = symbol
       # print ("TERMINAL", name)

# --------------------------------------------------------------------------

def nullableRules (grammar) :
    for rule in grammar.rules :
        rule.nullable = False

    grammar.nullableChanged = True
    while grammar.nullableChanged :
       grammar.nullableChanged = False
       for rule in grammar.rules :
           nullableRule (grammar, rule, complete = False)

    for rule in grammar.rules :
        nullableRule (grammar, rule, complete = True)
        # add nullable to all items

def nullableRule (grammar, rule, complete) :
    expr = rule.expr
    nullableExpression (grammar, expr, complete)
    if rule.nullable != expr.nullable :
       rule.nullable = expr.nullable
       grammar.nullableChanged = True

def nullableExpression (grammar, expr, complete) :
    # init
    expr.nullable = (len (expr.alternatives) == 0)

    for alt in expr.alternatives :
       nullableAlternative (grammar, alt, complete)

       # one alternative is nullable => expression is nullable
       if alt.nullable :
          expr.nullable = True
          if not complete :
             break

def nullableAlternative (grammar, alt, complete) :
    # init
    alt.nullable = True

    for item in alt.items :
        if isinstance (item, Terminal) :
           nullableTerminal (grammar, item)
        elif isinstance (item, Nonterminal) :
           nullableNonterminal (grammar, item)
        elif isinstance (item, Ebnf) :
           nullableEbnf (grammar, item, complete)
        else :
           grammar.error ("Unknown alternative item: " + item.__class__.__name__)

        # one item is not nullable => alternative is also not nullable
        if not item.nullable :
           alt.nullable = False
           if not complete :
              break

def nullableEbnf (grammar, ebnf, complete) :
    nullableExpression (grammar, ebnf.expr, complete)
    # if ebnf.impl != None :
    #    nullableAlternative (grammar, ebnf.impl)

    expr = ebnf.expr
    # set ebnf according to expression
    ebnf.nullable = expr.nullable
    # ( )? or ( )* => ebnf is nullable
    if ebnf.mark == '?' or ebnf.mark == '*' :
       ebnf.nullable = True

def nullableNonterminal (grammar, item) :
    rule = item.rule_ref
    item.nullable = rule.nullable

def nullableTerminal (grammar, item) :
    item.nullable = False

# --------------------------------------------------------------------------

def firstFromRules (grammar) :
    for rule in grammar.rules :
        rule.first = newArray (grammar)

    # calculate first sets
    grammar.firstChanged = True
    cnt = 0
    while grammar.firstChanged :
       grammar.firstChanged = False
       # print "first step"
       for rule in grammar.rules :
           firstFromRule (grammar, rule, complete = False)
       cnt = cnt + 1
       # print ("one step in firstFromRules")

    for rule in grammar.rules :
        firstFromRule (grammar, rule, complete = True)

    cnt = cnt + 1
    # print (cnt, "steps in firstFromRules")

def firstFromRule (grammar, rule, complete) :
    expr = rule.expr
    firstFromExpression (grammar, expr, complete) # !?

    equal = True
    for inx in range (grammar.symbol_cnt) :
        if rule.first [inx] != expr.first [inx] :
           equal = False

    if not equal :
       rule.first = expr.first
       grammar.firstChanged = True

def newArray (grammar) :
    return [False] * grammar.symbol_cnt

def copyArray (grammar, source) :
    result = newArray (grammar)
    for inx in range (grammar.symbol_cnt) :
        if source [inx] :
           result [inx] = True
    return result

def firstFromExpression (grammar, expr, complete) :
    # init
    expr.first = newArray (grammar)

    for alt in expr.alternatives :
       firstFromAlternative (grammar, alt, complete)

       # add symbols from alternative to expression
       for inx in range (grammar.symbol_cnt) :
           if alt.first [inx] :
              if expr.first [inx] :
                 pass # grammar.error ("Conflict between alternatives")
              expr.first [inx] = True

def firstFromAlternative (grammar, alt, complete) :
    # init
    alt.first = newArray (grammar)
    add = True

    for item in alt.items :
        if isinstance (item, Terminal) :
           firstFromTerminal (grammar, item)
        elif isinstance (item, Nonterminal) :
           firstFromNonterminal (grammar, item)
        elif isinstance (item, Ebnf) :
           firstFromEbnf (grammar, item, complete)
        else :
           grammar.error ("Unknown alternative item: " + item.__class__.__name__)

        if add :
           for inx in range (grammar.symbol_cnt) :
               if item.first [inx] :
                  alt.first [inx] = True
        # item is not nullable => stop adding symbols from items
        if not item.nullable :
           add = False
           if not complete :
              break

def firstFromEbnf (grammar, ebnf, complete) :
    firstFromExpression (grammar, ebnf.expr, complete)
    # if ebnf.impl != None :
    #    firstFromAlternative (grammar, ebnf.impl)

    expr = ebnf.expr
    # set ebnf according to expression
    ebnf.first = expr.first

def firstFromNonterminal (grammar, item) :
    rule = item.rule_ref
    item.first = rule.first

def firstFromTerminal (grammar, item) :
    # first set has one item
    item.first = newArray (grammar)
    inx = item.symbol_ref.inx
    item.first [inx] = True

# --------------------------------------------------------------------------

def followFromRules (grammar) :
    for rule in grammar.rules :
        rule.follow = newArray (grammar)

    for rule in grammar.rules :
        if rule.start :
           rule.follow [0] = True # index 0 ... eos

    cnt = 0
    grammar.followChanged = True
    while grammar.followChanged :
       grammar.followChanged = False
       for rule in grammar.rules :
           followFromRule (grammar, rule)
       cnt = cnt + 1
       # print ("one step in followFromRules")
    # print (cnt, "steps in followFromRules")

def followAsText (grammar, follow) :
    txt = ""
    for inx in range (grammar.symbol_cnt) :
        if follow [inx] :
           if len (txt) != 0 :
              txt = txt + " "
           txt = txt + grammar.symbols [inx].alias
    return txt

def followFromRule (grammar, rule) :
    # print ("followFromRule", rule.name, "begin", followAsText (grammar, rule.follow))
    followFromExpression (grammar, rule.expr, rule.follow)

def followFromExpression (grammar, expr, init) :
    expr.follow = copyArray (grammar, init)
    for alt in expr.alternatives :
        followFromAlternative (grammar, alt, init)

def followFromAlternative (grammar, alt, init_ref) :
    alt.follow = copyArray (grammar, init_ref)
    # copy init_ref to init
    init = copyArray (grammar, init_ref)
    # print ("followFromAlternative init_result", followAsText (grammar, init))

    cnt = len (alt.items)
    for item_inx in range (cnt) :
        item = alt.items [cnt-1-item_inx] # from last

        if isinstance (item, Nonterminal) : # update follow in nonterminal rule
           followFromNonterminal (grammar, item, init)

        if isinstance (item, Ebnf) : # update inner nonterminals
           followFromEbnf (grammar, item, init)

        if isinstance (item, Terminal) or isinstance (item, Nonterminal) or isinstance (item, Ebnf) :
           # item is not nullable => stop adding symbols
           if not item.nullable :
              for inx in range (grammar.symbol_cnt) :
                  init [inx] = False
              # print ("followFromAlternative init_clear")

           # add symbols from item
           for inx in range (grammar.symbol_cnt) :
               if item.first [inx] :
                  init [inx] = True
                  # print ("followFromAlternative add_to_init", grammar.symbols [inx].alias)

    # print ("followFromAlternative result", followAsText (grammar, init))

def followFromEbnf (grammar, ebnf, init_ref) :
    ebnf.follow = copyArray (grammar, init_ref)
    # copy init_ref to init
    init = copyArray (grammar, init_ref)

    expr = ebnf.expr
    if ebnf.mark == '*' or ebnf.mark == '+' :
       "add expr.first init"
       for inx in range (grammar.symbol_cnt) :
           if expr.first [inx] :
              init [inx] = True
              # print ("followFromEdnf add", grammar.symbols [inx].alias)
    followFromExpression (grammar, expr, init)

def followFromNonterminal (grammar, item, init) :
    item.follow = copyArray (grammar, init)
    rule = item.rule_ref
    for inx in range (grammar.symbol_cnt) :
        if init [inx] and not rule.follow [inx] :
           rule.follow [inx] = True
           grammar.followChanged = True
           # print ("followFromNonterminal", item.rule_name, "add", grammar.symbols [inx].alias)

# --------------------------------------------------------------------------

def checkRules (grammar) :
    for rule in grammar.rules :
       checkRule (grammar, rule)

def checkRule (grammar, rule) :
    grammar.updatePosition (rule)
    checkExpression (grammar, rule.expr)

def checkExpression (grammar, expr) :
    result = newArray (grammar)
    for alt in expr.alternatives :
       ok = True
       for inx in range (grammar.symbol_cnt) :
          if alt.first [inx] :
             if result [inx] :
                ok = False
             result [inx] = True
       if not ok :
          # grammar.warning_with_location (alt, "Conflict between alternatives")
          grammar.warning ("Conflict between alternatives")
       checkAlternative (grammar, alt)

def checkAlternative (grammar, alt) :
    grammar.updatePosition (alt)
    for item in alt.items :
        if isinstance (item, Ebnf) :
           checkEbnf (grammar, item)

        if isinstance (item, Nonterminal) or isinstance (item, Ebnf) :
           if item.nullable :
              ok = True
              for inx in range (grammar.symbol_cnt) :
                  if item.first [inx] and item.follow [inx] :
                     ok = False
              if not ok :
                 # grammar.warning_with_location (item, "Conflict between first and follow: " + item.rule_name)
                 grammar.warning ("Conflict between first and follow")

def checkEbnf (grammar, ebnf) :
    grammar.updatePosition (ebnf)
    checkExpression (grammar, ebnf.expr)

# --------------------------------------------------------------------------

def initSymbols (grammar) :
    print ("initSymbols")
    symbolsFromRules (grammar)
    print ("symbolsFromRules")
    nullableRules (grammar)
    print ("nullableRules")
    firstFromRules (grammar)
    print ("firstFromRules")
    # followFromRules (grammar)
    # print ("followFromRules")
    # checkRules (grammar)

# --------------------------------------------------------------------------

if __name__ == "__main__" :
    grammar = Grammar ()
    grammar.openFile ("./input/cecko.g")
    grammar.parseRules ()
    initSymbols (grammar)
    for rule in grammar.rules :
       print (rule.name, "starts with")
       sym_set = rule.first
       for inx in range (grammar.symbol_cnt) :
          if sym_set [inx] :
             sym = grammar.symbols [inx]
             print ("   ", sym.alias)
       print ()

# --------------------------------------------------------------------------

# kate: indent-width 1; show-tabs true; replace-tabs true; remove-trailing-spaces all
