from PyQt5 import QtCore, QtGui, QtWidgets
from controllers import (DefinitionController, TagController, WordController)
from dialogs import WordDialog,DictionaryDialog,TagEditDialog
from dataModels import WordDataModel,DefinitionDataModel,TagDataModel
import pickle
import os
from hunspell import HunSpell
# TODO : Setup keyboard shortcuts for easily navigating between ListViews/ListEdits etc.
class Ui_MainWindow(QtCore.QObject):
  def addTopButtons(self):
    self.buttonHorizontalLayout = QtWidgets.QHBoxLayout()
    self.buttonHorizontalLayout.setObjectName("buttonHorizontalLayout")
    self.addWordButton = QtWidgets.QPushButton(self.centralwidget)
    self.addWordButton.setObjectName("addWordButton")
    self.addWordButton.setMaximumSize(QtCore.QSize(100,50))
    self.addWordButton.setText("&Add Word")
    self.addWordButton.clicked.connect(self.showAddWordDialog)
    self.editWordButton = QtWidgets.QPushButton(self.centralwidget)
    self.editWordButton.setObjectName("editWordButton")
    self.editWordButton.setMaximumSize(QtCore.QSize(100,50))
    self.editWordButton.setText("&Edit Word")
    self.editWordButton.clicked.connect(self.showEditWordDialog)
    self.editDictsButton = QtWidgets.QPushButton(self.centralwidget)
    self.editDictsButton.setObjectName("editDictButton")
    self.editDictsButton.setMaximumSize(QtCore.QSize(150,50))
    self.editDictsButton.setText("Edit &Dictionaries")
    self.editDictsButton.clicked.connect(self.showEditDictsDialog)
    self.editMetaTagsButton = QtWidgets.QPushButton(self.centralwidget)
    self.editMetaTagsButton.setObjectName("editMTButton")
    self.editMetaTagsButton.setMaximumSize(QtCore.QSize(150,50))
    self.editMetaTagsButton.setText("Edit &MetaTags")
    self.editMetaTagsButton.clicked.connect(self.showEditMetaTagsDialog)

    self.buttonHorizontalLayout.addWidget(self.addWordButton)
    self.buttonHorizontalLayout.addWidget(self.editWordButton)
    self.buttonHorizontalLayout.addWidget(self.editDictsButton)
    self.buttonHorizontalLayout.addWidget(self.editMetaTagsButton)
  def addListViews(self):
    #outerVerticalLayout
    self.horizontalLayout = QtWidgets.QHBoxLayout()
    self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
    self.horizontalLayout.setObjectName("horizontalLayout")  
    #self.statusBar = QtWidgets.QStatusBar(self.centralwidget)
    #self.statusBar.setObjectName("statusBar")
    self.outerVerticalLayout.addLayout(self.buttonHorizontalLayout)
    self.outerVerticalLayout.addLayout(self.horizontalLayout)
    #self.outerVerticalLayout.addWidget(self.statusBar)

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
    self.tagview.installEventFilter(self)
    self.tagFilter = QtWidgets.QLineEdit(self.centralwidget)
    self.tagFilter.setObjectName("tagFilter")
    self.tagFilter.setPlaceholderText("Enter text to filter tags")
    self.tagFilter.setMaximumSize(QtCore.QSize(400, 30))
    self.tagFilter.installEventFilter(self) #Catch Enter
    self.verticalLayout.addWidget(self.dictSelect)
    self.verticalLayout.addWidget(self.tagview)
    self.verticalLayout.addWidget(self.tagFilter)
    self.verticalLayout.addWidget(self.wordview)
    
    

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
  def adefDataModelenuBar(self,MainWindow):
    self.menubar = QtWidgets.QMenuBar(MainWindow)
    self.menubar.setGeometry(QtCore.QRect(0, 0, 728, 30))
    self.menubar.setObjectName("menubar")
    self.menuFile = QtWidgets.QMenu(self.menubar)
    self.menuFile.setObjectName("menuFile")
    self.actionOpen = QtWidgets.QAction(MainWindow)
    self.actionOpen.setObjectName("actionOpen")
    self.menuFile.addAction(self.actionOpen)
    self.actionOpen.triggered.connect(self.openFile)

    self.actionSave = QtWidgets.QAction(MainWindow)
    self.actionSave.setObjectName("actionSave")
    self.menuFile.addAction(self.actionSave)
    self.actionSave.triggered.connect(self.saveFile)

    self.menubar.addAction(self.menuFile.menuAction())
    MainWindow.setMenuBar(self.menubar)
  def addStatusBar(self,MainWindow):
    self.statusBar = QtWidgets.QStatusBar(MainWindow)
    self.statusBar.setObjectName("statusbar")
    MainWindow.setStatusBar(self.statusBar)
  
  def setupDataModels(self,wordDataModel,tagDataModel,defDataModel):
    self.wordDataModel = wordDataModel
    self.defDataModel = defDataModel
    self.tagDataModel = tagDataModel
    self.wordController = WordController(wordDataModel,self.tagDataModel)
    self.tagController = TagController(self.tagDataModel)
    self.defController = DefinitionController()
    #Set signals/slots views to controllers
    self.definitionListView.setModel(self.defController)
    self.tagview.setModel(self.tagController)
    self.tagview.selectionModel().currentChanged.connect(self.tagController.selected)
    self.wordview.setModel(self.wordController)
    self.wordview.selectionModel().currentChanged.connect(self.wordController.selected)
    self.dictSelect.currentTextChanged.connect(self.wordController.updateDict)
    self.tagFilter.textChanged.connect(self.tagController.filterTags)
    #InterController signals
    self.tagController.tagChanged.connect(self.wordController.updateOnTag)
    #Connect signals to tab views
    self.wordController.dataChanged.connect(self.wordview.dataChanged)
    self.defController.dataChanged.connect(self.definitionListView.dataChanged)
    self.tagController.dataChanged.connect(self.tagview.dataChanged)
    self.defController.setEnabledView.connect(self.definitionListView.setEnabled)
    self.tabwidget.currentChanged.connect(self.wordController.setDefinitionLoadingSource)
    #Connect signals to data models
    self.defDataModel.dictNamesUpdated.connect(self.updateDictNames)
    self.wordDataModel.dataChanged.connect(self.tagController.updateTags)
    self.wordController.loadDefinition.connect(defDataModel.load)
    self.wordController.loadDefinition.connect(self.defController.loadingInitiated)
    defDataModel.definitionsUpdated.connect(self.defController.updateDefinition)
    defDataModel.externalPageLoad.connect(self.webView.load)
    defDataModel.showMessage.connect(self.statusBar.showMessage)

    self.dictSelect.insertItems(0,defDataModel.getDictNames())

  def setupUi(self, MainWindow):
    MainWindow.setObjectName("MainWindow")
    MainWindow.resize(728, 521)
    self.version = 0.01

    self.centralwidget = QtWidgets.QWidget(MainWindow)
    self.centralwidget.setObjectName("centralwidget")
    self.outerVerticalLayout = QtWidgets.QVBoxLayout(self.centralwidget)
    self.outerVerticalLayout.setObjectName("outerVerticalLayout")
    self.addTopButtons()
    self.addListViews()
    MainWindow.setCentralWidget(self.centralwidget)
    self.adefDataModelenuBar(MainWindow)            
    self.addStatusBar(MainWindow)
    self.retranslateUi(MainWindow)
    QtCore.QMetaObject.connectSlotsByName(MainWindow)
      
  def retranslateUi(self, MainWindow):
    _translate = QtCore.QCoreApplication.translate
    MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
    self.menuFile.setTitle(_translate("MainWindow", "Fi&le"))
    self.actionOpen.setText(_translate("MainWindow", "Open..."))
    self.actionSave.setText(_translate("MainWindow", "Save..."))
  
  def showAddWordDialog(self,event):
    self.addWordDialog = WordDialog(self.centralwidget,self.wordDataModel,self.tagDataModel,self.defDataModel,self.dictionary)
    dialogCode = self.addWordDialog.exec()
    if dialogCode == QtWidgets.QDialog.Accepted:
      newWord = self.addWordDialog.getWord()
      tags    = self.addWordDialog.getTags()
      self.wordDataModel.addWord(newWord,tags)
      self.tagDataModel.addTagging(newWord,tags)
      self.tagController.updateTags()
      print('Accepted. New Word:' + newWord)
      print("Tags: " + str(tags))
    elif dialogCode == QtWidgets.QDialog.Rejected:
      print('Rejected')
  def showEditWordDialog(self,event):
    pass
  def showEditDictsDialog(self,event):
    self.editDictsDialog = DictionaryDialog(self.centralwidget,self.defDataModel)
    dialogCode = self.editDictsDialog.exec()
    if dialogCode == QtWidgets.QDialog.Accepted:
      self.defDataModel.selectDictsFromNames(self.editDictsDialog.sModel.getDictNames())
      
    elif dialogCode == QtWidgets.QDialog.Rejected:
      print('Rejected')
  
  def showEditMetaTagsDialog(self,event):
    self.editMetaTagsDialog = TagEditDialog(self.centralwidget,self.wordDataModel,self.tagDataModel)
    dialogCode = self.editMetaTagsDialog.exec()
    if dialogCode == QtWidgets.QDialog.Accepted:
      self.tagController.updateTags()
    elif dialogCode == QtWidgets.QDialog.Rejected:
      print('Rejected')
  
  
  @classmethod
  def defaultInit(cls,window):
    wordDataModel = WordDataModel()
    defDataModel = DefinitionDataModel()
    obj = cls()
    obj.setupUi(window)
    obj.setupDataModels(wordDataModel, defDataModel)
    return obj

  def loadDictionary(self,dicFilename, affFilename):
    dictionary = HunSpell(dicFilename,affFilename)
    return dictionary
    
  def findDictionary(self,dicPath,language):
    codes = {"French":"fr_fr","English":"en_us"}
    files = os.listdir(dicPath)
    dicFiles = [f for f in files if f.endswith(".dic")]
    affFiles = [f for f in files if f.endswith(".aff")]
    code = codes[language]
    dicFile = [f for f in dicFiles if code.lower() in f.lower()]
    affFile = [f for f in affFiles if code.lower() in f.lower()]
    return os.path.join(dicPath,dicFile[0]), os.path.join(dicPath,affFile[0])

  @classmethod 
  def fromFile(cls, file, window):
    with open(file , "rb") as _input:
      version = pickle.load(_input)
      language = pickle.load(_input)
      wordDataModel = WordDataModel.fromFile(_input)
      tagDataModel = TagDataModel.fromFile(_input)
      defDataModel = DefinitionDataModel.fromFile(_input)
      wordDataModel.language = language
      defDataModel.language = language
      obj = cls()
      obj.setupUi(window)
      obj.setupDataModels(wordDataModel,tagDataModel,defDataModel)
      obj.language = language
      obj.dicPath       = "/usr/share/hunspell/"
      dicPath,affPath   = obj.findDictionary(obj.dicPath,obj.language)
      obj.dictionary    = obj.loadDictionary(dicPath, affPath)
      return obj
  
  def openFile(self):
    fileName,fileType = QtWidgets.QFileDialog.getOpenFileName(self.centralwidget,"Open File", ".", "Pickle Files (*.pkl)")
    if fileName == "":
      return
    else:
      with open(fileName, 'rb') as _input:
        version = pickle.load(_input)
        self.language = pickle.load(_input)
        self.wordDataModel.language = self.language
        self.defDataModel.language = self.language
        self.wordDataModel._fromFile(_input)
        self.tagDataModel._fromFile(_input)
        self.defDataModel._fromFile(_input)
        self.wordDataModel.updateData()
        self.defDataModel.updateDictNames()
        self.dicPath    = "/usr/share/hunspell/"
        dicPath,affPath = self.findDictionary(obj.dicPath,obj.language)
        self.dictionary = self.loadDictionary(dicPath, affPath)

  def saveFile(self):
    fileName,fileType = QtWidgets.QFileDialog.getSaveFileName(self.centralwidget,"Save File",".","Pickle Files (*.pkl)")
    if fileName == "":
      return
    else:
      with open(fileName, 'wb') as output:
        pickle.dump(self.version, output, pickle.HIGHEST_PROTOCOL) #Version
        pickle.dump(self.language, output , pickle.HIGHEST_PROTOCOL) #Language
        self.wordDataModel.toFile(output)
        self.tagDataModel.toFile(output)
        self.defDataModel.toFile(output)

  def updateDictNames(self,dictNames):
    self.dictSelect.clear()
    self.dictSelect.insertItems(0,dictNames)
  # def showEditWordDialog(self,event):

  def eventFilter(self,_object, event):
    if _object == self.tagFilter:
      if event.type() == QtCore.QEvent.KeyPress:
        if (event.key() == QtCore.Qt.Key_Enter) or (event.key() == QtCore.Qt.Key_Return):
          self.tagview.setFocus()
          return True
    if _object == self.tagview:
      if event.type() == QtCore.QEvent.KeyPress:
        if (event.key() == QtCore.Qt.Key_Enter) or (event.key() == QtCore.Qt.Key_Return):
          self.wordview.setFocus()
          return True
    return False

from PyQt5 import QtWebEngineWidgets 
