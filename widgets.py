
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

    
  def contextMenuEvent(self, event):
    menu = QtWidgets.QMenu(self)
    for action in self.actions:
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
    except TypeError:
      pass
    return False