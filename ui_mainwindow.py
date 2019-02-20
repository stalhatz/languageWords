from PyQt5 import QtCore, QtGui, QtWidgets
from controllers import (DefinitionController, TagController, WordController,ElementTagController,SavedDefinitionsController)
from dialogs import WordDialog,DictionaryDialog,TagEditDialog,WelcomeDialog
from dataModels import WordDataModel,DefinitionDataModel,TagDataModel
import pickle
import os
from hunspell import HunSpell
import uiUtils
# TODO : Setup keyboard shortcuts for easily navigating between ListViews/ListEdits etc.
#TODO : [FEATURE] TagWordView showing tags corresponding to a word. Optimally it should be done without introducing an extra Controller, just by filtering TagController
#TODO : [FEATURE] Store information (definitions / examples) provided in the definitionsModel: Copy items from definitions to a per word structure. In this way we can better contextualize each word with definitions that seem pertinant to the user.
#TODO : [UI] Move tabs to the right/left of QTabWidget with horizontal text. Calling setTabPosition(QtWidgets.QTabWidget.West) produces vertical text
class Ui_MainWindow(QtCore.QObject):
  def defineActions(self):
    self.actionNew = QtWidgets.QAction(self.mainWindow)
    self.actionNew.setObjectName("actionNew")
    self.actionNew.triggered.connect(self.newProject)
    self.actionNew.setShortcut("Ctrl+N")

    self.actionOpen = QtWidgets.QAction(self.mainWindow)
    self.actionOpen.setObjectName("actionOpen")
    self.actionOpen.triggered.connect(self.openFile)
    self.actionOpen.setShortcut("Ctrl+O")

    self.actionSave = QtWidgets.QAction(self.mainWindow)
    self.actionSave.setObjectName("actionSave")
    self.actionSave.triggered.connect(self.saveFile)
    self.actionSave.setShortcut("Ctrl+S")

    self.removeWordAction = QtWidgets.QAction ("Remove Word", self.mainWindow)
    self.removeWordAction.setObjectName("removeWordAction")
    self.removeWordAction.triggered.connect(self.removeWord)

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
    self.editWordButton.setEnabled(False)
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
    self.wordview.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
    
    self.tagview = QtWidgets.QListView(self.centralwidget)
    self.tagview.setMaximumSize(QtCore.QSize(400, 400))
    self.tagview.setObjectName("tagview")
    self.tagview.installEventFilter(self)
    self.tagFilter = QtWidgets.QLineEdit(self.centralwidget)
    self.tagFilter.setObjectName("tagFilter")
    self.tagFilter.setPlaceholderText("Enter text to filter tags")
    self.tagFilter.setMaximumSize(QtCore.QSize(400, 30))
    self.tagFilter.installEventFilter(self) #Catch Enter
    self.elementTagview = QtWidgets.QListView(self.centralwidget)
    self.elementTagview.setMaximumSize(QtCore.QSize(400, 400))
    self.elementTagview.setObjectName("elementTagview")
    self.elementTagview.installEventFilter(self)

    self.verticalLayout.addWidget(self.dictSelect)
    uiUtils.addLabeledWidget("Tag List", self.tagview,self.verticalLayout)
    self.verticalLayout.addWidget(self.tagFilter)
    uiUtils.addLabeledWidget("Phrases by tag", self.wordview,self.verticalLayout)
    
    uiUtils.addLabeledWidget("Tags by Phrase", self.elementTagview,self.verticalLayout)
    
    self.savedDefinitionsView = QtWidgets.QListView(self.centralwidget)
    self.savedDefinitionsView.setObjectName("savedDefinitionsView")
    self.savedDefinitionsView.setWordWrap(True)
    self.savedDefinitionsView.setEditTriggers(QtWidgets.QAbstractItemView.SelectedClicked)
    self.savedDefinitionsView.itemDelegate().commitData.connect(self.replaceSavedDefinition)

    uiUtils.addLabeledWidget("Saved Definitions", self.savedDefinitionsView,self.horizontalLayout)

    self.tabwidget = QtWidgets.QTabWidget(self.centralwidget)
    self.tabwidget.setTabPosition(QtWidgets.QTabWidget.South)
    self.tabwidget.setObjectName("tabwidget")
    uiUtils.addLabeledWidget("Online Definitions", self.tabwidget,self.horizontalLayout)
    
    self.definitionListView = QtWidgets.QListView(self.tabwidget)
    self.definitionListView.setObjectName("definitionListView")
    self.definitionListView.setWordWrap(True)
    self.tabwidget.addTab(self.definitionListView , "List")

    self.webView = QtWebEngineWidgets.QWebEngineView(self.tabwidget)
    self.webView.setUrl(QtCore.QUrl("about:blank"))
    self.webView.setObjectName("webView")
    self.tabwidget.addTab(self.webView , "Web page")

  def addMenuBar(self,MainWindow):
    self.menubar = QtWidgets.QMenuBar(MainWindow)
    self.menubar.setGeometry(QtCore.QRect(0, 0, 728, 30))
    self.menubar.setObjectName("menubar")
    self.menuFile = QtWidgets.QMenu(self.menubar)
    self.menuFile.setObjectName("menuFile")
    self.menuFile.addAction(self.actionNew)
    self.menuFile.addAction(self.actionOpen)
    self.menuFile.addAction(self.actionSave)
    self.menubar.addAction(self.menuFile.menuAction())
    MainWindow.setMenuBar(self.menubar)
  def addStatusBar(self,MainWindow):
    self.statusBar = QtWidgets.QStatusBar(MainWindow)
    self.statusBar.setObjectName("statusbar")
    MainWindow.setStatusBar(self.statusBar)
  
  def setupDataModels(self,wordDataModel,tagDataModel,defDataModel):
    self.wordDataModel      = wordDataModel
    self.defDataModel       = defDataModel
    self.tagDataModel       = tagDataModel
    self.wordController     = WordController(wordDataModel,self.tagDataModel)
    self.tagController      = TagController(self.tagDataModel)
    self.filterController   = QtCore.QSortFilterProxyModel()
    self.defController      = DefinitionController()
    self.elementController  = ElementTagController(tagDataModel)
    self.savedDefController = SavedDefinitionsController(defDataModel)
    #Set signals/slots views to controllers
    self.filterController.setSourceModel(self.tagController)
    self.filterController.setFilterCaseSensitivity(QtCore.Qt.CaseInsensitive)
    self.savedDefinitionsView.setModel(self.savedDefController)
    self.savedDefinitionsView.doubleClicked.connect(self.removeDefinition)
    self.savedDefinitionsView.selectionModel().currentChanged.connect(self.savedDefController.selected)
    self.elementTagview.setModel(self.elementController)
    self.elementTagview.selectionModel().currentChanged.connect(self.elementController.selected)
    self.definitionListView.setModel(self.defController)
    self.definitionListView.doubleClicked.connect(self.saveDefinition)
    self.definitionListView.selectionModel().currentChanged.connect(self.defController.selected)
    self.tagview.setModel(self.filterController)
    self.tagview.selectionModel().currentChanged.connect(self.tagController.selected)
    self.wordview.setModel(self.wordController)
    self.wordController.addView(self.wordview)
    
    #View->Ui signals
    self.wordview.customContextMenuRequested.connect(self.contextMenuRequested)
    self.wordview.selectionModel().currentChanged.connect(self.enableEditWordButton)
    
    #Controller->Ui signals
    self.wordController.clearSelection.connect(self.disableEditWordButton)
    
    #View->Controller signals
    self.wordview.selectionModel().currentChanged.connect(self.wordController.selected)
    self.wordController.currentChanged.connect(self.elementController.updateOnWord)
    self.wordController.currentChanged.connect(self.savedDefController.updateOnWord)
    self.dictSelect.currentTextChanged.connect(self.wordController.updateDict)
    self.tagFilter.textChanged.connect(self.filterController.setFilterFixedString)
    self.tabwidget.currentChanged.connect(self.wordController.setDefinitionLoadingSource)

    #Controller->Controller signals
    self.tagController.tagChanged.connect(self.wordController.updateOnTag)

    #Controller->View signals
    self.defController.dataChanged.connect(self.definitionListView.dataChanged)
    self.tagController.dataChanged.connect(self.tagview.dataChanged)
    self.defController.setEnabledView.connect(self.definitionListView.setEnabled)

    #Connect signals to data models
    self.defDataModel.dictNamesUpdated.connect(self.updateDictNames)
    self.wordController.loadDefinition.connect(self.defDataModel.load)
    self.wordController.loadDefinition.connect(self.defController.loadingInitiated)
    self.defDataModel.definitionsUpdated.connect(self.defController.updateDefinition)
    self.defDataModel.externalPageLoad.connect(self.webView.load)
    self.defDataModel.showMessage.connect(self.statusBar.showMessage)

    self.dictSelect.insertItems(0,defDataModel.getDictNames())

  def setupUi(self, MainWindow):
    MainWindow.setObjectName("MainWindow")
    MainWindow.resize(720, 1024)
    self.mainWindow = MainWindow
    self.version = 0.02
    self.language = "N/A"
    self.projectName = "Untitled"
    self.programName = "LanguageWords"
    self.setWindowTitle()
    self.centralwidget = QtWidgets.QWidget(MainWindow)
    self.centralwidget.setObjectName("centralwidget")
    self.outerVerticalLayout = QtWidgets.QVBoxLayout(self.centralwidget)
    self.outerVerticalLayout.setObjectName("outerVerticalLayout")
    self.defineActions()
    self.addTopButtons()
    self.addListViews()
    MainWindow.setCentralWidget(self.centralwidget)
    self.addMenuBar(MainWindow)            
    self.addStatusBar(MainWindow)
    self.retranslateUi(MainWindow)
    QtCore.QMetaObject.connectSlotsByName(MainWindow)
      
  def retranslateUi(self, MainWindow):
    _translate = QtCore.QCoreApplication.translate
    self.menuFile.setTitle(_translate("MainWindow", "Fi&le"))
    self.actionNew.setText(_translate("MainWindow", "New project"))
    self.actionOpen.setText(_translate("MainWindow", "Open..."))
    self.actionSave.setText(_translate("MainWindow", "Save..."))
  
  def showAddWordDialog(self,event):
    self.addWordDialog = WordDialog(self.centralwidget,self.wordDataModel,self.tagDataModel,self.defDataModel,self.dictionary,
                                    WordDialog.CREATE_DIALOG)
    dialogCode = self.addWordDialog.exec()
    if dialogCode == QtWidgets.QDialog.Accepted:
      newWord = self.addWordDialog.getWord()
      tags    = self.addWordDialog.getTags()
      self.tagDataModel.addTagging(newWord,tags)
      self.wordDataModel.addWord(newWord)
      self.tagController.updateTags()
      print('Accepted. New Word:' + newWord)
      print("Tags: " + str(tags))
    elif dialogCode == QtWidgets.QDialog.Rejected:
      print('Rejected')

  def showEditWordDialog(self,event):
    wordIndex = self.wordview.currentIndex()
    word      = self.wordview.model().data(wordIndex,QtCore.Qt.DisplayRole)
    if isinstance(word,QtCore.QVariant):
      return
    tags      = self.tagDataModel.getTagsFromIndex(word)
    self.editWordDialog = WordDialog(self.centralwidget,self.wordDataModel,self.tagDataModel,self.defDataModel,self.dictionary,
                                      WordDialog.EDIT_DIALOG , word, tags)
    dialogCode = self.editWordDialog.exec()
    if dialogCode == QtWidgets.QDialog.Accepted:
      #Remove word and tags
      self._removeWord(word,tags)
      #Add new word and tags
      editedWord = self.editWordDialog.getWord()
      if editedWord != "":
        newTags    = self.editWordDialog.getTags()
        self.tagDataModel.addTagging(editedWord,newTags)
        self.wordDataModel.addWord(editedWord)
        print('Accepted. Existing word:' + editedWord)
        print("Tags: " + str(newTags))
      else:
        print('Accepted. Deleted word')
      self.tagController.updateTags()
    elif dialogCode == QtWidgets.QDialog.Rejected:
      print('Rejected')

  def showEditDictsDialog(self,event):
    self.editDictsDialog = DictionaryDialog(self.centralwidget,self.defDataModel)
    dialogCode = self.editDictsDialog.exec()
    if dialogCode == QtWidgets.QDialog.Accepted:
      self.defDataModel.selectDictsFromNames(self.editDictsDialog.sController.getDictNames())
      
    elif dialogCode == QtWidgets.QDialog.Rejected:
      print('Rejected')
  
  def showEditMetaTagsDialog(self,event):
    self.editMetaTagsDialog = TagEditDialog(self.centralwidget,self.wordDataModel,self.tagDataModel)
    dialogCode = self.editMetaTagsDialog.exec()
    if dialogCode == QtWidgets.QDialog.Accepted:
      self.tagController.updateTags()
    elif dialogCode == QtWidgets.QDialog.Rejected:
      print('Rejected')
  
  def showWelcomeDialog(self):
    availableLanguages = self.defDataModel.getAvailableLanguages()
    self.welcomeDialog = WelcomeDialog(self.centralwidget,self.actionOpen, self.actionNew , 
                                        self.programName , self.version , availableLanguages)
    dialogCode = self.welcomeDialog.exec()
    if dialogCode == QtWidgets.QDialog.Accepted:
      if not self.welcomeDialog.loadedFile: #New Project
        self.language     = self.welcomeDialog.languageComboBox.currentText()
        self.wordDataModel.language  = self.language
        self.defDataModel.language   = self.language
        self.projectName  = self.welcomeDialog.nameLineEdit.text()
        self.setWindowTitle()
      print('Accepted')
    elif dialogCode == QtWidgets.QDialog.Rejected:
      print('Rejected')

  def disableEditWordButton(self):
    self.editWordButton.setEnabled(False)
  def enableEditWordButton(self, wordIndex,*_):
    if wordIndex.isValid():
      self.editWordButton.setEnabled(True)

  @classmethod
  def defaultInit(cls,window):
    wordDataModel = WordDataModel()
    defDataModel = DefinitionDataModel.getInstance()
    tagDataModel = TagDataModel()
    obj = cls()
    obj.setupUi(window)
    obj.setupDataModels(wordDataModel,tagDataModel, defDataModel)
    obj.dictionary  = None
    obj.language    = None
    #self.activeConnections = []
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
  def fromFile(cls, file, window=None , obj = None):
    if isinstance(file,str):
      with open(file, 'rb') as _input:
        obj = cls._fromFile(_input, window , obj)
    else:
      obj = cls._fromFile(file, window , obj)
    return obj


  @classmethod 
  def _fromFile(cls, _input, window=None,obj=None):
    projectName = "Untitled"
    version = pickle.load(_input)
    if version > 0.01:
      projectName = pickle.load(_input)
    language = pickle.load(_input)
    if obj is None:
      obj = cls()
      wordDataModel = WordDataModel.fromFile(_input)
      tagDataModel = TagDataModel.fromFile(_input)
      defDataModel = DefinitionDataModel.fromFile(_input)
      obj.setupUi(window)
      obj.setupDataModels(wordDataModel,tagDataModel,defDataModel)
    else:
      obj.wordDataModel._fromFile(_input)
      obj.tagDataModel._fromFile(_input)
      obj.defDataModel._fromFile(_input)
    
    obj.wordDataModel.language  = language
    obj.defDataModel.language   = language
    obj.language                = language
    obj.projectName             = projectName
    obj.dictionary              = None
    obj.activeConnections       = []
    if language is not None:
      obj.dicPath       = "/usr/share/hunspell/"
      dicPath,affPath   = obj.findDictionary(obj.dicPath,obj.language)
      obj.dictionary    = obj.loadDictionary(dicPath, affPath)
    return obj
  
  def openFile(self):
    fileName,fileType = QtWidgets.QFileDialog.getOpenFileName(self.centralwidget,"Open File", ".", "Pickle Files (*.pkl)")
    if fileName == "" or fileName is None:
      return
    else:
      Ui_MainWindow.fromFile(fileName,None,self)
      self.setWindowTitle()
      self.tagController.updateTags()
      if self.welcomeDialog.isVisible():
        self.welcomeDialog.loadedFile = True
        self.welcomeDialog.accept()
  def newProject(self):
    pass

  def setWindowTitle(self):
    self.mainWindow.setWindowTitle(self.projectName + " - " + "(" + str(self.language) + ")" + " - " + str(self.programName) )

  def saveFile(self):
    fileName,fileType = QtWidgets.QFileDialog.getSaveFileName(self.centralwidget,"Save File",".","Pickle Files (*.pkl)")
    if fileName == "":
      return
    else:
      with open(fileName, 'wb') as output:
        pickle.dump(self.version, output, pickle.HIGHEST_PROTOCOL) #Version
        pickle.dump(self.projectName, output, pickle.HIGHEST_PROTOCOL) #ProjectName
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

  def saveDefinition(self):
    definition  = self.defController.getSelectedDefinition()
    self._saveDefinition(definition)

  def _saveDefinition(self,definition):
    word        = self.wordController.getSelectedWord()
    if not self.defDataModel.definitionExists(word,definition.text):
      dictionary  = self.dictSelect.currentText()
      self.defDataModel.addDefinition(word,definition.text,dictionary,definition.type)
      self.savedDefController.update()

  
  def _removeSelectedDefinition(self):
    definition  = self.savedDefController.getSelectedDefinition()
    word        = self.wordController.getSelectedWord()
    self.defDataModel.removeDefinition(word,definition)

  def removeDefinition(self):
    self._removeSelectedDefinition()
    self.savedDefController.update()
  
  def contextMenuRequested(self,point):
    index = self.wordview.indexAt(point).row()
    print(index)
    if (index >= 0):
      contextMenu = QtWidgets.QMenu ("Context menu", self.wordview)
      contextMenu.addAction(self.removeWordAction)
      contextMenu.exec(self.wordview.mapToGlobal(point))

  def _removeWord(self,word,tags):
    self.tagDataModel.removeTagging(word,tags)
    self.wordDataModel.removeWord(word)

  def removeWord(self):
    word = self.wordController.getSelectedWord()
    tags = self.tagDataModel.getTagsFromIndex(word)
    self._removeWord(word,tags)
    self.wordController.updateOnTag(self.tagController.getSelectedTag())
    self.tagController.updateTags()
  
  def replaceSavedDefinition(self,widget):
    newDefinition = widget.text()
    word = self.wordController.getSelectedWord()
    definition  = self.savedDefController.getSelectedDefinition()
    self.defDataModel.replaceDefinition(word,definition,newDefinition)
    self.savedDefController.update()

from PyQt5 import QtWebEngineWidgets 
