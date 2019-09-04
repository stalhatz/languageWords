
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5 import QtWebEngineWidgets 

class myWebViewer(QtWebEngineWidgets.QWebEngineView): 
  def __init__(self,parent,actions=None):
    super(myWebViewer,self).__init__(parent)
    if actions == None:
      self.actions = []
    else:
      self.actions = actions
    self.setMinimumWidth(100)
    self.actionBack = QtWidgets.QAction("Back", self)
    self.actionBack.setObjectName("myWebViewer.actionBack")
    self.actionBack.triggered.connect(self.back)
    QtWidgets.QApplication.instance().installEventFilter(self)
    self.setFocusProxy(self)
    self.searchText = ""

  #Override
  def load(self,url,text = ""):
    if text is None:
      text = ""
    self.page().findText(text)
    self.searchText = text
    super(myWebViewer,self).load(url)

  def contextMenuEvent(self, event):
    menu = QtWidgets.QMenu(self)
    if len(self.selectedText()) > 0:
      for action in self.actions:
        if action.isEnabled():
          menu.addAction(action)
    menu.addAction(self.actionBack)
    menu.exec_(event.globalPos())
  
  def eventFilter(self,object,event):
    try:
      if object.parent() == self:
        if isinstance(event,QtGui.QKeyEvent):
          if event.type() == QtGui.QKeyEvent.KeyPress:
            if int( QtGui.QGuiApplication.instance().queryKeyboardModifiers() & QtCore.Qt.AltModifier) != 0:
              if (event.key() == QtCore.Qt.Key_Left):
                self.back()
                return True
              elif (event.key() == QtCore.Qt.Key_Right):
                self.forward()
                return True
            elif int( QtGui.QGuiApplication.instance().queryKeyboardModifiers() & QtCore.Qt.ControlModifier) != 0:
              if (event.key() == QtCore.Qt.Key_F):
                text = self.showFindTextDialog()
                if text is not None and (not text == ""):
                  self.page().findText(text )
                  self.searchText = text
            elif (event.key() == QtCore.Qt.Key_F3):
              if self.searchText != "":
                self.page().findText(self.searchText)

    except TypeError:
      pass
    return False

  def showFindTextDialog(self):
    ok = False
    text,ok = QtWidgets.QInputDialog.getText(self, "Find text in page",
                                          "Text to find", QtWidgets.QLineEdit.Normal)
    if ok and len(text) > 0:
      return text
    else:
      return None
