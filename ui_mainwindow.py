from PyQt5 import QtCore, QtGui, QtWidgets
from dataModels import (DictWebList, PandasTagList, PandasWordList)
#import requests

# TODO: Breakup ui setup in functions
class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
      MainWindow.setObjectName("MainWindow")
      MainWindow.resize(728, 521)
      self.centralwidget = QtWidgets.QWidget(MainWindow)
      self.centralwidget.setObjectName("centralwidget")
      
      self.outerVerticalLayout = QtWidgets.QVBoxLayout(self.centralwidget)
      self.outerVerticalLayout.setObjectName("outerVerticalLayout")
      self.buttonHorizontalLayout = QtWidgets.QHBoxLayout()
      self.buttonHorizontalLayout.setObjectName("buttonHorizontalLayout")

      self.addWordButton = QtWidgets.QPushButton(self.centralwidget)
      self.addWordButton.setObjectName("addWordButton")
      self.addWordButton.setMaximumSize(QtCore.QSize(100,100))
      self.addWordButton.setText("Add Word")
      self.editWordButton = QtWidgets.QPushButton(self.centralwidget)
      self.editWordButton.setObjectName("editWordButton")
      self.editWordButton.setMaximumSize(QtCore.QSize(100,100))
      self.editWordButton.setText("Edit Word")

      self.buttonHorizontalLayout.addWidget(self.addWordButton)
      self.buttonHorizontalLayout.addWidget(self.editWordButton)

      self.horizontalLayout = QtWidgets.QHBoxLayout()
      self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
      self.horizontalLayout.setObjectName("horizontalLayout")
      
      self.statusBar = QtWidgets.QStatusBar(self.centralwidget)
      self.statusBar.setObjectName("statusBar")
      self.statusBar.showMessage("Hello World")

      self.outerVerticalLayout.addLayout(self.buttonHorizontalLayout)
      self.outerVerticalLayout.addLayout(self.horizontalLayout)
      self.outerVerticalLayout.addWidget(self.statusBar)

      self.verticalLayout = QtWidgets.QVBoxLayout()
      self.verticalLayout.setObjectName("verticalLayout")
      self.dictSelect = QtWidgets.QComboBox(self.centralwidget)
      self.dictSelect.setMaximumSize(QtCore.QSize(300, 50))
      self.dictSelect.setObjectName("dictSelect")
      self.verticalLayout.addWidget(self.dictSelect)
      self.wordview = QtWidgets.QListView(self.centralwidget)
      self.wordview.setMaximumSize(QtCore.QSize(400, 400))
      self.wordview.setObjectName("wordview")
      self.verticalLayout.addWidget(self.wordview)
      self.tagview = QtWidgets.QListView(self.centralwidget)
      self.tagview.setMaximumSize(QtCore.QSize(400, 400))
      self.tagview.setObjectName("tagview")
      self.verticalLayout.addWidget(self.tagview)
      self.horizontalLayout.addLayout(self.verticalLayout)

      self.tabwidget = QtWidgets.QTabWidget(self.centralwidget)
      self.tabwidget.setObjectName("tabwidget")
      self.horizontalLayout.addWidget(self.tabwidget)

      self.dictListView = QtWidgets.QListView(self.tabwidget)
      self.dictListView.setObjectName("dictView")
      self.dictListView.setWordWrap(True)
      self.tabwidget.addTab(self.dictListView , "Custom view")

      self.webView = QtWebEngineWidgets.QWebEngineView(self.tabwidget)
      self.webView.setUrl(QtCore.QUrl("about:blank"))
      self.webView.setObjectName("webView")
      self.tabwidget.addTab(self.webView , "Webview")
      #self.horizontalLayout.addWidget(self.webView)
      
      MainWindow.setCentralWidget(self.centralwidget)
      self.menubar = QtWidgets.QMenuBar(MainWindow)
      self.menubar.setGeometry(QtCore.QRect(0, 0, 728, 30))
      self.menubar.setObjectName("menubar")
      self.menuFile = QtWidgets.QMenu(self.menubar)
      self.menuFile.setObjectName("menuFile")
      MainWindow.setMenuBar(self.menubar)
      self.statusbar = QtWidgets.QStatusBar(MainWindow)
      self.statusbar.setObjectName("statusbar")
      MainWindow.setStatusBar(self.statusbar)
      self.actionOpen = QtWidgets.QAction(MainWindow)
      self.actionOpen.setObjectName("actionOpen")
      self.menuFile.addAction(self.actionOpen)
      self.menubar.addAction(self.menuFile.menuAction())

      self.retranslateUi(MainWindow)
      QtCore.QMetaObject.connectSlotsByName(MainWindow)
    
    def setupDataUi(self, dictWords):
      self.pwl = PandasWordList(dictWords,self.webView)
      self.ptl = PandasTagList(dictWords)
      self.dwl = DictWebList()
      #Set signals/slots
      self.dictListView.setModel(self.dwl)
      self.tagview.setModel(self.ptl)
      self.tagview.selectionModel().currentChanged.connect(self.ptl.selected)
      self.wordview.setModel(self.pwl)
      self.wordview.selectionModel().currentChanged.connect(self.pwl.selected)
      self.dictSelect.currentTextChanged.connect(self.pwl.updateDict)

      self.ptl.tagChanged.connect(self.pwl.updateWords)
      #Connect signals to tab views
      self.pwl.dataChanged.connect(self.wordview.reset)
      self.dwl.dataChanged.connect(self.dictListView.dataChanged)
      self.dwl.showMessage.connect(self.statusBar.showMessage)
      self.dwl.setEnabledView.connect(self.dictListView.setEnabled)
      self.tabConnected = -1
      self.connectTabSlots(self.tabwidget.currentIndex())

      self.tabwidget.currentChanged.connect(self.connectTabSlots)

    def connectTabSlots(self,current):
      if current == 1:
        if self.tabConnected == 0:
          self.pwl.pageLoad.disconnect(self.dwl.load)
        self.pwl.pageLoad.connect(self.webView.load)
        self.pwl.reload()
        self.tabConnected = 1
      if current == 0:
        if self.tabConnected == 1:
          self.pwl.pageLoad.disconnect(self.webView.load)
        self.pwl.pageLoad.connect(self.dwl.load)
        self.pwl.reload()
        self.tabConnected = 0
        
    def retranslateUi(self, MainWindow):
      _translate = QtCore.QCoreApplication.translate
      MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
      self.menuFile.setTitle(_translate("MainWindow", "Fi&le"))
      self.actionOpen.setText(_translate("MainWindow", "Open..."))
    
    # TODO: Show dialogs for adding/editing words.
    # def showAddWordDialog(self,event):
    #   currentTag = self.ptl.getCurrentTag()
    #   self.addWordDialog = QtWidgets.QDialog(self.centralwidget)
    #   hLayout = QtWidgets.QHBoxLayout(self.addWordDialog)
    #   vLeftLayout = QtWidgets.QVBoxLayout(self.addWordDialog)
    #   vRightLayout = QtWidgets.QVBoxLayout(self.addWordDialog)
    #   hLayout.addLayout(vLeftLayout)
    #   hLayout.addLayout(vRightLayout)

    #   label = 

    # def showEditWordDialog(self,event):

from PyQt5 import QtWebEngineWidgets 
