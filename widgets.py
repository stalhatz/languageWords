
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

    
  def contextMenuEvent(self, event):
    menu = QtWidgets.QMenu(self)
    for action in self.actions:
      menu.addAction(action)
    menu.addAction(self.actionBack)
    menu.exec_(event.globalPos())