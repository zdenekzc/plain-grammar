#!/usr/bin/env python

from __future__ import print_function

import os, sys, re, importlib

try :
   from PyQt4.QtCore import *
   from PyQt4.QtGui import *
except :
   from PyQt5.QtCore import *
   from PyQt5.QtGui import *
   from PyQt5.QtWidgets import *

from plain_lexer     import Lexer, LexerException
from plain_grammar   import Grammar, Rule, Expression, Alternative, Ebnf, Nonterminal, Terminal
from plain_symbols   import initSymbols
from plain_toparser  import ToParser
from plain_toproduct import ToProduct

# --------------------------------------------------------------------------

class Edit (QTextEdit) :
    def __init__ (self, parent=None) :
        super (Edit, self).__init__ (parent)
        self.setLineWrapMode (QTextEdit.NoWrap) # otherwise selectLine is not exact
        self.highlighter = Highlighter (self.document ())

    def selectLine (self, line) :
        cursor = self.textCursor ()
        cursor.movePosition (QTextCursor.Start)
        cursor.movePosition (QTextCursor.Down, QTextCursor.MoveAnchor, line-1)
        cursor.movePosition (QTextCursor.EndOfLine, QTextCursor.KeepAnchor)
        self.setTextCursor (cursor)

    def select (self, line, col, stop_line, stop_col):
        cursor = self.textCursor ()

        cursor.movePosition (QTextCursor.Start)
        cursor.movePosition (QTextCursor.Down, QTextCursor.MoveAnchor, line-1)
        cursor.movePosition (QTextCursor.Right, QTextCursor.MoveAnchor, col-1)

        if stop_line == line :
           cursor.movePosition (QTextCursor.Right, QTextCursor.KeepAnchor, stop_col-col)
        else :
           cursor.movePosition (QTextCursor.Down, QTextCursor.KeepAnchor, stop_line-line)
           cursor.movePosition (QTextCursor.StartOfLine, QTextCursor.KeepAnchor)
           cursor.movePosition (QTextCursor.Right, QTextCursor.KeepAnchor, stop_col)

        self.setTextCursor (cursor)

# --------------------------------------------------------------------------

def findIcon (icon_name) :
    return QIcon.fromTheme (icon_name)

class TreeItem (QTreeWidgetItem) :
    def __init__ (self, parent, text) :
        super (TreeItem, self).__init__ (parent)
        self.setText (0, text)

    def addIcon (self, icon_name) :
        self.setIcon (0, findIcon (icon_name))

class TreeView (QTreeWidget) :
    def __init__ (self, parent=None) :
        super (TreeView, self).__init__ (parent)
        self.setColumnCount (1)
        self.header ().hide ()
        self.setEditTriggers (QAbstractItemView.SelectedClicked)
        self.setIndentation (8)

# --------------------------------------------------------------------------

class Highlighter (QSyntaxHighlighter) :
    def __init__ (self, parent = None) :
        super (Highlighter, self).__init__ (parent)
        self.lexer = Lexer ()

        self.identifierFormat = QTextCharFormat ()
        self.identifierFormat.setForeground (Qt.darkRed)
        self.identifierFormat.setToolTip ("identifier")

        self.numberFormat = QTextCharFormat ()
        self.numberFormat.setForeground (QColor ("cornflowerblue"))

        self.realFormat = QTextCharFormat ()
        self.realFormat.setForeground (Qt.magenta)

        self.characterFormat = QTextCharFormat ()
        self.characterFormat.setForeground (QColor ("cornflowerblue"))

        self.stringFormat = QTextCharFormat ()
        self.stringFormat.setForeground (Qt.blue)

        self.separatorFormat = QTextCharFormat ()
        self.separatorFormat.setForeground (QColor ("orange"))

        self.commentFormat = QTextCharFormat ()
        self.commentFormat.setForeground (Qt.gray)

    def highlightBlock (self, text) :
        try :
           lexer = self.lexer
           lexer.openString (text)
           while not lexer.isEndOfSource () :
              index = lexer.tokenByteOfs - 1
              length = lexer.charByteOfs - lexer.tokenByteOfs
              if lexer.token == lexer.identifier :
                 self.setFormat (index, length, self.identifierFormat)
              elif lexer.token == lexer.number :
                 self.setFormat (index, length, self.numberFormat)
              elif lexer.token == lexer.real_number :
                 self.setFormat (index, length, self.realFormat)
              elif lexer.token == lexer.character_literal :
                 self.setFormat (index, length, self.characterFormat)
              elif lexer.token == lexer.string_literal :
                 self.setFormat (index, length, self.stringFormat)
              elif lexer.token == lexer.separator :
                 self.setFormat (index, length, self.separatorFormat)
              else : # !?
                 self.setFormat (index, length, self.commentFormat)
              lexer.nextToken ()
        except :
           pass

# --------------------------------------------------------------------------

class FindDialog (QDialog):

    def __init__ (self, parent, edit) :
        QDialog.__init__ (self, parent)
        self.edit = edit
        self.setWindowTitle ("Find")

        self.layout = QHBoxLayout ()
        self.setLayout (self.layout)

        self.line = QLineEdit ()
        self.layout.addWidget (self.line)

        self.findButton = QPushButton ()
        self.findButton.setText ("Find")
        self.layout.addWidget (self.findButton)

        self.cancelButton = QPushButton ()
        self.cancelButton.setText ("Cancel")
        self.layout.addWidget (self.cancelButton)

        self.line.returnPressed.connect (self.onReturnPressed)
        self.findButton.clicked.connect (self.onReturnPressed)
        self.cancelButton.clicked.connect (self.close)

        self.exec_ ()

    def onReturnPressed (self) :
        self.edit.find (self.line.text())

# --------------------------------------------------------------------------

class GoToLineDialog (QDialog):

    def __init__ (self, parent, edit) :
        QDialog.__init__ (self, parent)
        self.edit = edit
        self.setWindowTitle ("Go To Line")

        self.layout = QHBoxLayout ()
        self.setLayout (self.layout)

        self.spin = QSpinBox ()
        cursor = self.edit.textCursor ()
        document = self.edit.document ()
        self.spin.setMinimum (1)
        self.spin.setMaximum (document.blockCount ())
        self.spin.setValue (cursor.blockNumber () + 1) # line number
        self.layout.addWidget (self.spin)

        self.gotoButton = QPushButton ()
        self.gotoButton.setText ("Go to line")
        self.layout.addWidget (self.gotoButton)

        self.cancelButton = QPushButton ()
        self.cancelButton.setText ("Cancel")
        self.layout.addWidget (self.cancelButton)

        # self.spin.valueChanged.connect (self.onValueChanged)
        self.gotoButton.clicked.connect (self.onValueChanged)
        self.cancelButton.clicked.connect (self.close)

        self.show ()

    def onValueChanged (self) :
        self.edit.selectLine (self.spin.value ())

# --------------------------------------------------------------------------

class MainWin (QMainWindow) :

    def __init__ (self, parent=None) :
        super (MainWin, self).__init__ (parent)
        self.setupUI ()
        self.setupMenus ()
        ver = sys.version_info
        inf = str (ver[0]) + "." + str (ver[1]) + "." + str (ver[2])
        self.statusBar().showMessage ("Python " + inf + ", Qt " + qVersion())

        work_dir = sys.path [0]
        self.output_dir = os.path.join (work_dir, "_output")

    def setupUI (self) :

        self.split = QSplitter ()
        self.setCentralWidget (self.split)

        self.tree = TreeView ()
        self.split.addWidget (self.tree)

        self.tree.itemActivated.connect (self.onItemActivated)

        self.tabWidget = QTabWidget ()
        self.split.addWidget (self.tabWidget)

        self.split.setStretchFactor (0, 1)
        self.split.setStretchFactor (1, 2)

        self.resize (640, 480)

    def setupMenus (self) :

        fileMenu = self.menuBar().addMenu ("&File")

        act = QAction ("&Open...", self)
        act.setShortcut ("Ctrl+O")
        act.triggered.connect (self.openFile)
        fileMenu.addAction (act)

        act = QAction ("&Save...", self)
        act.setShortcut ("Ctrl+S")
        act.triggered.connect (self.saveFile)
        fileMenu.addAction (act)


        act = QAction ("&Quit", self)
        act.setShortcut ("Ctrl+Q")
        act.triggered.connect (self.close)
        fileMenu.addAction (act)

        editMenu = self.menuBar().addMenu ("&Edit")

        act =  QAction ("&Find", self)
        act.setShortcut ("Ctrl+F")
        act.triggered.connect (self.find)
        editMenu.addAction (act)

        act =  QAction ("&Go to line", self)
        act.setShortcut ("Ctrl+G")
        act.triggered.connect (self.goToLine)
        editMenu.addAction (act)

        runMenu = self.menuBar().addMenu ("&Run")

        act = QAction ("&Create parser", self)
        act.setShortcut ("Ctrl+E")
        act.triggered.connect (self.createParser)
        runMenu.addAction (act)

        act = QAction ("&Run parser", self)
        act.setShortcut ("Ctrl+R")
        act.triggered.connect (self.runParser)
        runMenu.addAction (act)

    def onItemActivated (self, item, column) :
        if hasattr (item, "src_tab") :
           inx = item.src_tab
           edit = self.tabWidget.widget (inx)
           self.tabWidget.setCurrentIndex (inx)
           if hasattr (item, "src_line") :
              edit.selectLine (item.src_line)


    def getEditor (self) :
        e = self.tabWidget.currentWidget ()
        if isinstance (e, Edit) :
           return e
        else :
           return None

    def readFile (self, edit, fileName) :
        f = open (fileName)
        text = f.read ()

        if edit == None :
           edit = Edit ()
           title = os.path.basename (fileName)
           self.tabWidget.addTab (edit, title)

        edit.setPlainText (text)
        return edit

    def writeFile (self, edit, fileName) :
        f = open (fileName)
        text =  edit.toPlainText ()
        f.write (text)

    def openFile (self) :
        edit = self.getEditor ()
        if edit != None :
           fileName = QFileDialog.getOpenFileName (self, "Open File") [0]
           if fileName :
              self.readFile (None, str (fileName))

    def saveFile (self):
        edit = self.getEditor ()
        if edit != None :
           fileName = QFileDialog.getSaveFileName (self, "Save File") [0]
           if fileName :
              self.writeFile (edit, fileName)

    def find (self) :
        edit = self.getEditor ()
        if edit != None :
           FindDialog (self, edit)

    def goToLine (self) :
        edit = self.getEditor ()
        if edit != None :
           GoToLineDialog (self, edit)

    # ----------------------------------------------------------------------

    def loadModule (self, fileName) :
        module = None
        try :
           fileName = os.path.abspath (fileName)
           sys.path.insert (0, os.path.dirname (fileName))
           name, ext = os.path.splitext (os.path.basename (fileName))
           if name in sys.modules :
              if sys.version_info >= (3,) :
                 importlib.reload (sys.modules [name])
              else :
                 reload (sys.modules [name])
           module = importlib.import_module (name)
        finally :
           del sys.path [0]
        return module

    def createDir (self, fileName) :
        dirName = os.path.dirname (fileName)
        if not os.path.isdir (dirName) :
           os.makedirs (dirName)

    def outputFileName (self, fileName) :
        fileName = os.path.join (self.output_dir, fileName)
        self.createDir (fileName)
        return fileName

    # ----------------------------------------------------------------------

    def calculateSymbols (self) :
        # self.tree.clear ()
        edit = self.getEditor ()
        if edit != None :
           source = edit.toPlainText ()

           grammar = Grammar ()
           grammar.openString (source)

           grammar.parseRules ()
           initSymbols (grammar)

           self.grammarTree (grammar, edit)

    def createParser (self) :
        # self.tree.clear ()
        edit = self.getEditor ()
        if edit != None :
           source = edit.toPlainText ()

           grammar = Grammar ()
           grammar.openString (source)

           grammar.parseRules ()
           initSymbols (grammar)

           self.parserFileName = self.outputFileName ("parser.py")
           self.productFileName = self.outputFileName ("product.py")

           to_parser = ToParser ()
           to_parser.open (self.parserFileName)
           to_parser.parserFromGrammar (grammar)
           to_parser.close ()
           print ("parser O.K.")
           e1 = self.readFile (None, self.parserFileName)

           to_product = ToProduct ()
           to_product.open (self.productFileName)
           to_product.productFromGrammar (grammar)
           to_product.close ()
           print ("product O.K.")
           e2 = self.readFile (None, self.productFileName)

           self.grammarTree (grammar, edit)
           self.pythonTree (e1, "parser")
           self.pythonTree (e2, "product")

    def runParser (self) :
        edit = self.getEditor ()
        if edit != None :
           try :
              source = edit.toPlainText ()

              parser_module = self.loadModule (self.parserFileName)
              product_module = self.loadModule (self.productFileName)

              parser = parser_module.Parser ()
              parser.openString (source)
              data = parser.parse_program ();
              parser.close ()

              print (data)
              self.syntaxTree (data)

              product = product_module.Product ()
              product.openString ()
              product.send_program (data);
              output = product.closeString ()

              widget = Edit ()
              widget.setPlainText (output)
              self.tabWidget.addTab (widget, "output")
              self.tabWidget.setCurrentWidget (widget)

           except LexerException as e :
              edit.selectLine (e.lineNum)
              raise e

    # ----------------------------------------------------------------------

    def grammarTree (self, grammar, edit) :
        tab_inx = self.tabWidget.indexOf (edit)
        top = TreeItem (self.tree, "grammar")
        top.addIcon ("folder")
        top.src_tab = tab_inx
        self.addSymbols (top, grammar)
        for rule in grammar.rules :
           self.addBranch (top, rule, grammar, tab_inx)

    def addSymbols (self, above, grammar) :
        branch = TreeItem (above, "symbols")
        for symbol in grammar.symbols :
            TreeItem (branch, str (symbol.inx) + " " + symbol.alias)

    def addBranch (self, above, node, grammar, tab_inx) :

        txt = ""
        if isinstance (node, Rule) :
           txt = node.name
        elif isinstance (node, Expression) :
           txt = "expression"
        elif isinstance (node, Alternative) :
           txt = "alternative"
        elif isinstance (node, Ebnf) :
           txt = "ebnf " + node.mark
        elif isinstance (node, Nonterminal) :
           txt = "nonterminal "
           txt = txt + node.rule_name
        elif isinstance (node, Terminal) :
           txt = "terminal " + node.text
        else:
           txt = node.__class__.__name__

        item = TreeItem (above, txt)

        if hasattr (node, "src_line") :
           item.src_tab = tab_inx
           item.src_line = node.src_line

        if isinstance (node, Rule) :
           item.addIcon ("code-class")
        if isinstance (node, Nonterminal) :
           item.addIcon ("code-function")
        if isinstance (node, Terminal) :
           item.addIcon ("code-variable")
        if isinstance (node, Ebnf) :
           item.addIcon ("code-block")

        if isinstance (node, Rule) :
           if hasattr (node, "first") :
              n = 0
              for inx in range (len (node.first)) :
                  if node.first [inx] :
                     n = n + 1
              if n > 1 :
                 item.setForeground (0, QBrush (Qt.green))

        if hasattr (node, "nullable") :
           if node.nullable :
              item.setForeground (0, QBrush (Qt.red))

        if isinstance (node, Rule) :
           self.addInfo (item, node, grammar)
           self.addBranch (item, node.expr, grammar, tab_inx)
        elif isinstance (node, Expression) :
           for t in node.alternatives :
              self.addBranch (item, t, grammar, tab_inx)
        elif isinstance (node, Alternative) :
           for t in node.items :
              self.addBranch (item, t, grammar, tab_inx)
        elif isinstance (node, Ebnf) :
           self.addBranch (item, node.expr, grammar, tab_inx)

    def addInfo (self, above, rule, grammar) :
        if hasattr (rule, "first") :
           branch = TreeItem (above, "first")
           branch.addIcon ("info")
           branch.setForeground (0, QBrush (Qt.blue))
           if hasattr (rule, "nullable") and rule.nullable :
              item = TreeItem (branch, "<empty>")
              item.setForeground (0, QBrush (Qt.red))
           for inx in range (len (rule.first)) :
               if rule.first [inx] :
                  name = grammar.symbols [inx].alias
                  item = TreeItem (branch, name)
                  item.setForeground (0, QBrush (Qt.blue))

    # ----------------------------------------------------------------------

    def syntaxTree (self, data) :
        top = TreeItem (self.tree, "syntax tree")
        top.addIcon ("folder")
        self.addSyntaxBranch (top, data)

    def addSyntaxBranch (self, above, data) :
        name = data [0]
        branch = TreeItem (above, name)
        inx = 1
        cnt = len (data)
        while inx < cnt :
           val = data [inx]
           if isinstance (val, bool) :
              node = TreeItem (branch, str (val))
              if val :
                 node.setForeground (0, QBrush (Qt.green))
              else :
                 node.setForeground (0, QBrush (Qt.red))
           elif isinstance (val, int) :
              node = TreeItem (branch, str (val))
              node.setForeground (0, QBrush (Qt.blue))
           elif isinstance (val, list) :
              self.addSyntaxBranch (branch, val)
           else :
              node = TreeItem (branch, str (val))
              node.setForeground (0, QColor ("orange"))
           inx = inx + 1

    # ----------------------------------------------------------------------

    def pythonTree (self, edit, title) :
        tab_inx = self.tabWidget.indexOf (edit)
        source = edit.toPlainText ()

        top = TreeItem (self.tree, title)
        top.addIcon ("folder")
        top.src_tab = tab_inx

        line_inx = 0
        cls_branch = None
        for line in source.split ("\n") :
           line_inx = line_inx + 1
           pattern = "(\s*)(class|def)\s\s*(\w*)"
           m = re.match (pattern, line)
           if m :
              target = top
              if m.group (1) != "" and cls_branch != None : # identation and existing class
                 target = cls_branch

              is_class = m.group (2) == "class"

              name = m.group (3)
              if is_class :
                 name = "class " + name

              node = TreeItem (target, name)
              node.src_tab = tab_inx
              node.src_line = line_inx

              if is_class :
                 node.addIcon ("class")
              else :
                 node.addIcon ("code-function")

              if is_class :
                 cls_branch = node

# --------------------------------------------------------------------------

app = QApplication (sys.argv)
QIcon.setThemeName ("oxygen")
# print (QStyleFactory.keys())
# app.setStyle ("windows")
win = MainWin ()
# win.setFont (QFont ("Sans Serif", 16))
# win.setFont (QFont ("Sans Serif", 24))
win.show ()

# win.readFile (None, "./input/nullable.g")
# win.calculateSymbols ()
win.readFile (None, "./input/cecko.g")
win.createParser ()
e = win.readFile (None, "./input/c1.cc")
win.tabWidget.setCurrentWidget (e)
# win.runParser ()

app.exec_ ()

# --------------------------------------------------------------------------

# kate: indent-width 1; show-tabs true; replace-tabs true; remove-trailing-spaces all
