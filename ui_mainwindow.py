from PyQt5 import QtCore, QtGui, QtWidgets
from controllers import (DefinitionController, TagController, WordController)
from dialogs import WordDialog
# TODO : Setup keyboard shortcuts for easily navigating between ListViews/ListEdits etc.
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

      #outerVerticalLayout
      self.horizontalLayout = QtWidgets.QHBoxLayout()
      self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
      self.horizontalLayout.setObjectName("horizontalLayout")  
      self.statusBar = QtWidgets.QStatusBar(self.centralwidget)
      self.statusBar.setObjectName("statusBar")
      self.outerVerticalLayout.addLayout(self.buttonHorizontalLayout)
      self.outerVerticalLayout.addLayout(self.horizontalLayout)
      self.outerVerticalLayout.addWidget(self.statusBar)

      #horizontalLayout (outerVerticalLayout)
      self.verticalLayout = QtWidgets.QVBoxLayout()
      self.verticalLayout.setObjectName("verticalLayout")
      self.horizontalLayout.addLayout(self.verticalLayout)
      #verticalLayout (horizontalLayout (outerVerticalLayout))
      self.dictSelect = QtWidgets.QComboBox(self.centralwidget)
      self.dictSelect.setMaximumSize(QtCore.QSize(300, 30))
      self.dictSelect.setObjectName("dictSelect")
      self.wordview = QtWidgets.QListView(self.centralwidget)
      self.wordview.setMaximumSize(QtCore.QSize(400, 400))
      self.wordview.setObjectName("wordview")
      self.tagview = QtWidgets.QListView(self.centralwidget)
      self.tagview.setMaximumSize(QtCore.QSize(400, 400))
      self.tagview.setObjectName("tagview")
      self.tagFilter = QtWidgets.QLineEdit(self.centralwidget)
      self.tagFilter.setObjectName("tagFilter")
      self.tagFilter.setPlaceholderText("Enter text to filter tags")
      self.tagFilter.setMaximumSize(QtCore.QSize(400, 30))
      self.verticalLayout.addWidget(self.dictSelect)
      self.verticalLayout.addWidget(self.wordview)
      self.verticalLayout.addWidget(self.tagview)
      self.verticalLayout.addWidget(self.tagFilter)
      
      

      self.tabwidget = QtWidgets.QTabWidget(self.centralwidget)
      self.tabwidget.setObjectName("tabwidget")
      self.horizontalLayout.addWidget(self.tabwidget)

      self.definitionListView = QtWidgets.QListView(self.tabwidget)
      self.definitionListView.setObjectName("definitionListView")
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
      self.wc = WordController(wordDataModel.wordTable)
      self.tc = TagController(wordDataModel.tagTable)
      self.dc = DefinitionController()
      #Set signals/slots views to controllers
      self.definitionListView.setModel(self.dc)
      self.tagview.setModel(self.tc)
      self.tagview.selectionModel().currentChanged.connect(self.tc.selected)
      self.wordview.setModel(self.wc)
      self.wordview.selectionModel().currentChanged.connect(self.wc.selected)
      self.dictSelect.currentTextChanged.connect(self.wc.updateDict)
      self.tagFilter.textChanged.connect(self.tc.filterTags)
      #InterController signals
      self.tc.tagChanged.connect(self.wc.updateWords)
      #Connect signals to tab views
      self.wc.dataChanged.connect(self.wordview.dataChanged)
      self.dc.dataChanged.connect(self.definitionListView.dataChanged)
      self.tc.dataChanged.connect(self.tagview.dataChanged)
      self.dc.setEnabledView.connect(self.definitionListView.setEnabled)
      self.tabwidget.currentChanged.connect(self.wc.setDefinitionLoadingSource)
      #Connect signals to data models
      self.wc.loadDefinition.connect(defDataModel.load)
      self.wc.loadDefinition.connect(self.dc.loadingInitiated)
      defDataModel.definitionsUpdated.connect(self.dc.updateDefinition)
      defDataModel.externalPageLoad.connect(self.webView.load)
      defDataModel.showMessage.connect(self.statusBar.showMessage)

      self.dictSelect.insertItems(0,defDataModel.dictNames)

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
      self.addWordDialog = WordDialog(self.centralwidget)
      dialogCode = self.addWordDialog.exec()
      if dialogCode == QtWidgets.QDialog.Accepted:
        print('Accepted')
      elif dialogCode == QtWidgets.QDialog.Rejected:
        print('Rejected')




    # def showEditWordDialog(self,event):

from PyQt5 import QtWebEngineWidgets 
