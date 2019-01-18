from PyQt5 import QtCore, QtGui, QtWidgets
from controllers import (DefinitionController, TagController, WordController)

class Ui_MainWindow(object):
    def addTopButtons(self):
      self.buttonHorizontalLayout = QtWidgets.QHBoxLayout()
      self.buttonHorizontalLayout.setObjectName("buttonHorizontalLayout")
      self.addWordButton = QtWidgets.QPushButton(self.centralwidget)
      self.addWordButton.setObjectName("addWordButton")
      self.addWordButton.setMaximumSize(QtCore.QSize(100,100))
      self.addWordButton.setText("Add Word")
      self.addWordButton.clicked.connect(self.showAddWordDialog)
      self.editWordButton = QtWidgets.QPushButton(self.centralwidget)
      self.editWordButton.setObjectName("editWordButton")
      self.editWordButton.setMaximumSize(QtCore.QSize(100,100))
      self.editWordButton.setText("Edit Word")
      self.buttonHorizontalLayout.addWidget(self.addWordButton)
      self.buttonHorizontalLayout.addWidget(self.editWordButton)
    def addListViews(self):
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

      self.definitionListView = QtWidgets.QListView(self.tabwidget)
      self.definitionListView.setObjectName("dictView")
      self.definitionListView.setWordWrap(True)
      self.tabwidget.addTab(self.definitionListView , "Custom view")

      self.webView = QtWebEngineWidgets.QWebEngineView(self.tabwidget)
      self.webView.setUrl(QtCore.QUrl("about:blank"))
      self.webView.setObjectName("webView")
      self.tabwidget.addTab(self.webView , "Webview")

      #self.horizontalLayout.addWidget(self.webView)
    def addMenuBar(self,MainWindow):
      self.menubar = QtWidgets.QMenuBar(MainWindow)
      self.menubar.setGeometry(QtCore.QRect(0, 0, 728, 30))
      self.menubar.setObjectName("menubar")
      self.menuFile = QtWidgets.QMenu(self.menubar)
      self.menuFile.setObjectName("menuFile")
      self.actionOpen = QtWidgets.QAction(MainWindow)
      self.actionOpen.setObjectName("actionOpen")
      self.menuFile.addAction(self.actionOpen)
      self.menubar.addAction(self.menuFile.menuAction())
      MainWindow.setMenuBar(self.menubar)
    def addStatusBar(self,MainWindow):
      self.statusbar = QtWidgets.QStatusBar(MainWindow)
      self.statusbar.setObjectName("statusbar")
      MainWindow.setStatusBar(self.statusbar)
    
    def setupDataModels(self,wordDataModel,defDataModel):
      self.wc = WordController(wordDataModel)
      self.tc = TagController(wordDataModel.tagTable)
      self.dc = DefinitionController()
      #Set signals/slots
      self.definitionListView.setModel(self.dc)
      self.tagview.setModel(self.tc)
      self.tagview.selectionModel().currentChanged.connect(self.tc.selected)
      self.wordview.setModel(self.wc)
      self.wordview.selectionModel().currentChanged.connect(self.wc.selected)
      self.dictSelect.currentTextChanged.connect(self.wc.updateDict)
      #InterController signals
      self.tc.tagChanged.connect(self.wc.updateWords)
      #Connect signals to tab views
      self.wc.dataChanged.connect(self.wordview.reset)
      self.dc.dataChanged.connect(self.definitionListView.dataChanged)
      self.dc.setEnabledView.connect(self.definitionListView.setEnabled)
      self.tabwidget.currentChanged.connect(self.wc.setDefinitionLoadingSource)
      #Connect signals to data models
      self.wc.loadDefinition.connect(defDataModel.load)
      self.wc.loadDefinition.connect(self.dc.loadingInitiated)
      defDataModel.definitionsUpdated.connect(self.dc.updateDefinition)
      defDataModel.externalPageLoad.connect(self.webView.load)
      defDataModel.showMessage.connect(self.statusBar.showMessage)

    def setupUi(self, MainWindow):
      MainWindow.setObjectName("MainWindow")
      MainWindow.resize(728, 521)
      self.centralwidget = QtWidgets.QWidget(MainWindow)
      self.centralwidget.setObjectName("centralwidget")
      self.outerVerticalLayout = QtWidgets.QVBoxLayout(self.centralwidget)
      self.outerVerticalLayout.setObjectName("outerVerticalLayout")
      self.addTopButtons()
      self.addListViews()
      MainWindow.setCentralWidget(self.centralwidget)
      self.addMenuBar(MainWindow)            
      self.addStatusBar(MainWindow)
      self.retranslateUi(MainWindow)
      QtCore.QMetaObject.connectSlotsByName(MainWindow)
        
    def retranslateUi(self, MainWindow):
      _translate = QtCore.QCoreApplication.translate
      MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
      self.menuFile.setTitle(_translate("MainWindow", "Fi&le"))
      self.actionOpen.setText(_translate("MainWindow", "Open..."))
    
    # TODO: Show dialogs for adding/editing words.
    def showAddWordDialog(self,event):
      #currentTag = self.tc.getCurrentTag()
      self.addWordDialog = QtWidgets.QDialog(self.centralwidget)
      
      vLayout     = QtWidgets.QVBoxLayout(self.addWordDialog)
      hLowLayout  = QtWidgets.QHBoxLayout(self.addWordDialog)
      okButton    = QtWidgets.QPushButton(self.addWordDialog)
      okButton.setText("OK")
      okButton.clicked.connect(self.addWordDialog.accept)
      cancelButton = QtWidgets.QPushButton(self.addWordDialog)
      cancelButton.setText("Cancel")
      cancelButton.clicked.connect(self.addWordDialog.reject)
      hHighLayout = QtWidgets.QHBoxLayout(self.addWordDialog)
      hLowLayout.addWidget(okButton)
      hLowLayout.addWidget(cancelButton)
      vLayout.addLayout(hHighLayout)
      vLayout.addLayout(hLowLayout)
      vLeftLayout = QtWidgets.QVBoxLayout(self.addWordDialog)
      vRightLayout = QtWidgets.QVBoxLayout(self.addWordDialog)
      hHighLayout.addLayout(vLeftLayout)
      hHighLayout.addLayout(vRightLayout)
      textLabel = QtWidgets.QLabel(self.addWordDialog)
      textLabel.setText("Please enter a new word")
      textLabel.setMaximumSize(QtCore.QSize(300, 50))
      lineEdit = QtWidgets.QLineEdit(self.addWordDialog)
      lineEdit.setMaximumSize(QtCore.QSize(400, 50))
      vLeftLayout.addWidget(textLabel)
      vLeftLayout.addWidget(lineEdit)
      dialogCode = self.addWordDialog.exec()
      if dialogCode == QtWidgets.QDialog.Accepted:
        print('Accepted')
        print("New word is ::" + lineEdit.text())
        self.wc
      elif dialogCode == QtWidgets.QDialog.Rejected:
        print('Rejected')
      else:
        print('Neither Acc or Rej')



    # def showEditWordDialog(self,event):

from PyQt5 import QtWebEngineWidgets 
