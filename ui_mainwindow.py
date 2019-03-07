from PyQt5 import QtCore, QtGui, QtWidgets
from controllers import (DefinitionController, TagController, WordController,ElementTagController,SavedDefinitionsController)
from dialogs import WordDialog,DictionaryDialog,TagEditDialog,WelcomeDialog
from dataModels import WordDataModel,DefinitionDataModel,TagDataModel,OnlineDefinitionDataModel
import pickle
import os
from hunspell import HunSpell
import uiUtils
from functools import partial

# TODO : Setup keyboard shortcuts for easily navigating between ListViews/ListEdits etc.
#TODO : [UI] Move tabs to the right/left of QTabWidget with horizontal text. Calling setTabPosition(QtWidgets.QTabWidget.West) produces vertical text
#FIXME: Dialogs do not trigger a dirty program state
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

    self.actionSaveAs = QtWidgets.QAction(self.mainWindow)
    self.actionSaveAs.setObjectName("actionSave")
    self.actionSaveAs.triggered.connect(self.saveFileAs)
    self.actionSaveAs.setShortcut("Ctrl+Shift+S")

    self.actionSave = QtWidgets.QAction(self.mainWindow)
    self.actionSave.setObjectName("actionSave")
    self.actionSave.triggered.connect(self.saveFile)
    self.actionSave.setShortcut("Ctrl+S")
    #self.actionSave.setEnabled(False)

    self.removeWordAction = QtWidgets.QAction ("Remove Word", self.mainWindow)
    self.removeWordAction.setObjectName("removeWordAction")
    self.removeWordAction.triggered.connect(self.removeWord)

    self.addDefinitionAction = QtWidgets.QAction ("Add Custom Definition", self.mainWindow)
    self.addDefinitionAction.setObjectName("addDefinitionAction")
    self.addDefinitionAction.triggered.connect(self.addDefinition)

    self.removeDefinitionAction = QtWidgets.QAction ("Remove Definition", self.mainWindow)
    self.removeDefinitionAction.setObjectName("removeDefinitionAction")
    self.removeDefinitionAction.triggered.connect(self.removeDefinition)

    self.renameTagAction = QtWidgets.QAction ("Rename Tag", self.mainWindow)
    self.renameTagAction.setObjectName("renameTagAction")
    self.renameTagAction.triggered.connect(self.editSelectedTag)

    self.exitAppAction = QtWidgets.QAction ("Exit application", self.mainWindow)
    self.exitAppAction.setObjectName("exitAppAction")
    self.exitAppAction.triggered.connect(self.exitApplication)

    self.showPreferencesAction = QtWidgets.QAction ("Preferences", self.mainWindow)
    self.showPreferencesAction.setObjectName("showPreferencesAction")
    self.showPreferencesAction.triggered.connect(self.showPreferencesDialog)

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
    self.savedDefinitionsView.itemDelegate().commitData.connect(self.handleEditedDefinition)

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
    self.menuFile.addAction(self.actionSaveAs)
    self.menuFile.addSeparator()
    self.menuFile.addAction(self.exitAppAction)

    self.menuEdit = QtWidgets.QMenu(self.menubar)
    self.menuEdit.setObjectName("menuEdit")
    self.menuEdit.addAction(self.showPreferencesAction)

    self.menubar.addAction(self.menuFile.menuAction())
    self.menubar.addAction(self.menuEdit.menuAction())
    MainWindow.setMenuBar(self.menubar)
  def addStatusBar(self,MainWindow):
    self.statusBar = QtWidgets.QStatusBar(MainWindow)
    self.statusBar.setObjectName("statusbar")
    MainWindow.setStatusBar(self.statusBar)
  
  def setupDataModels(self,wordDataModel,tagDataModel,defDataModel,onlineDefDataModel):
    self.wordDataModel      = wordDataModel
    self.defDataModel       = defDataModel
    self.tagDataModel       = tagDataModel
    self.onlineDefDataModel = onlineDefDataModel
    #Instantiate controllers
    self.wordController     = WordController(wordDataModel,self.tagDataModel)
    self.wordview.setModel(self.wordController)
    self.wordview.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
    self.wordController.addView(self.wordview)
    self.tagController      = TagController(self.tagDataModel)
    self.tagview.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
    self.filterController   = QtCore.QSortFilterProxyModel()
    self.filterController.setSourceModel(self.tagController)
    self.filterController.setFilterCaseSensitivity(QtCore.Qt.CaseInsensitive)
    self.tagview.setModel(self.filterController)
    self.defController      = DefinitionController(self.onlineDefDataModel)
    self.defController.addView(self.definitionListView)
    self.definitionListView.setModel(self.defController)
    self.elementController  = ElementTagController(tagDataModel)
    self.elementTagview.setModel(self.elementController)
    self.savedDefController = SavedDefinitionsController(defDataModel)
    
    #Set signals/slots views to controllers
    self.elementTagview.selectionModel().currentChanged.connect(self.elementController.selected)
    #View->Ui signals
    self.definitionListView.doubleClicked.connect(self.saveDefinition)
    self.tagview.itemDelegate().commitData.connect(self.handleEditedTag)
    self.tagview.customContextMenuRequested.connect(self.tagViewMenuRequested)
    self.tagview.selectionModel().currentChanged.connect(self.selectedTagChanged)
    self.savedDefinitionsView.setModel(self.savedDefController)
    self.savedDefinitionsView.doubleClicked.connect(self.removeDefinition)
    self.wordview.customContextMenuRequested.connect(self.wordViewContextMenuRequested)
    self.wordview.selectionModel().currentChanged.connect(self.selectedWordChanged)
    self.savedDefinitionsView.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
    self.savedDefinitionsView.customContextMenuRequested.connect(self.savedDefViewContextMenuRequested)
    self.dictSelect.currentTextChanged.connect(self.updateOnlineDefinition)
    self.tabwidget.currentChanged.connect(self.updateOnlineDefinition)
    #Controller->Ui signals
    #self.wordController.clearSelection.connect(self.disableEditWordButton)
    
    #View->Controller signals
    self.tagFilter.textChanged.connect(self.filterController.setFilterFixedString)
    
    #Data models->Ui signals
    self.onlineDefDataModel.dictNamesUpdated.connect(self.updateDictNames)
    self.onlineDefDataModel.definitionsUpdated.connect(self._updateOnlineDefinition)
    self.onlineDefDataModel.showMessage.connect(self.statusBar.showMessage) #Not really needed...

    self.dictSelect.insertItems(0,self.onlineDefDataModel.getDictNames())

  def setupUi(self, MainWindow):
    MainWindow.setObjectName("MainWindow")
    MainWindow.resize(720, 1024)
    self.mainWindow = MainWindow
    self.version = 0.03
    self.language = "N/A"
    self.projectName = "Untitled"
    self.programName = "LanguageWords"
    self.sessionFile = "." + self.programName + "_" + "session" + ".pkl"
    self.autoSaveTimer = QtCore.QTimer()
    self.autoSaveTimer.timeout.connect(self.autoSave)
    self.autoSaveTimerInterval = 3000
    self.projectFile = None 
    self.unsavedChanges = False 
    self.tempProjectFile = None
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
    self.menuEdit.setTitle(_translate("MainWindow", "&Edit"))
    self.actionNew.setText(_translate("MainWindow", "New project"))
    self.actionOpen.setText(_translate("MainWindow", "Open..."))
    self.actionSaveAs.setText(_translate("MainWindow", "Save As..."))
    self.actionSave.setText(_translate("MainWindow", "Save"))
  
  def showPreferencesDialog(self):
    pass

  def showAddWordDialog(self,event):
    self.addWordDialog = WordDialog(self.centralwidget,self.wordDataModel,self.tagDataModel,self.onlineDefDataModel,self.dictionary,
                                    WordDialog.CREATE_DIALOG)
    dialogCode = self.addWordDialog.exec()
    if dialogCode == QtWidgets.QDialog.Accepted:
      newWord = self.addWordDialog.getWord()
      tags    = self.addWordDialog.getTags()
      self.tagDataModel.addTagging(newWord,tags)
      self.wordDataModel.addWord(newWord)
      self.tagController.updateTags()
      self.setDirtyState()
      self.tagFilter.setText("")
      tagIndex = self.tagController.getTagIndex(tags[0])
      tagIndex = self.filterController.mapFromSource(tagIndex)
      self.tagview.setCurrentIndex(tagIndex)
      self.wordview.setCurrentIndex(self.wordController.getWordIndex(newWord))
    elif dialogCode == QtWidgets.QDialog.Rejected:
      print('Rejected')

  def showEditWordDialog(self,event):
    wordIndex = self.wordview.currentIndex()
    word      = self.wordview.model().data(wordIndex,QtCore.Qt.DisplayRole)
    if isinstance(word,QtCore.QVariant):
      return
    tags      = self.tagDataModel.getTagsFromIndex(word)
    self.editWordDialog = WordDialog(self.centralwidget,self.wordDataModel,self.tagDataModel,self.onlineDefDataModel,self.dictionary,
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
    self.editDictsDialog = DictionaryDialog(self.centralwidget,self.onlineDefDataModel)
    dialogCode = self.editDictsDialog.exec()
    if dialogCode == QtWidgets.QDialog.Accepted:
      self.onlineDefDataModel.selectDictsFromNames(self.editDictsDialog.sController.getDictNames())
      
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
    tempCallback = None
    lastOpenedCallback = None
    if os.path.exists(self.sessionFile):
      with open(self.sessionFile, 'rb') as _input:
        version = pickle.load(_input)
        self.tempProjectFile  = pickle.load(_input)
        self.projectFile      = pickle.load(_input)
        self.unsavedChanges   = pickle.load(_input)
        if self.unsavedChanges:
          tempCallback          = partial(self.openFile,self.tempProjectFile,True)
        lastOpenedCallback    = partial(self.openFile,self.projectFile)

    availableLanguages = self.onlineDefDataModel.getAvailableLanguages()
    self.welcomeDialog = WelcomeDialog(self.centralwidget,self.actionOpen, self.actionNew , 
                                        self.programName , self.version , availableLanguages,
                                        lastOpenedCallback , tempCallback)
    dialogCode = self.welcomeDialog.exec()
    if dialogCode == QtWidgets.QDialog.Accepted:
      if not self.welcomeDialog.loadedFile: #New Project
        self.language     = self.welcomeDialog.languageComboBox.currentText()
        self.wordDataModel.language  = self.language
        self.defDataModel.language   = self.language
        self.projectName  = self.welcomeDialog.nameLineEdit.text()
        self.setWindowTitle()
        self.setDirtyState()
    elif dialogCode == QtWidgets.QDialog.Rejected:
      self.exitAppAction.trigger()
  # def disableEditWordButton(self):
  #   self.editWordButton.setEnabled(False)

  @classmethod
  def defaultInit(cls,app,window):
    wordDataModel   = WordDataModel()
    defDataModel    = DefinitionDataModel.getInstance()
    onlineDefModel  = OnlineDefinitionDataModel.getInstance()
    tagDataModel    = TagDataModel()

    obj = cls()
    obj.setupUi(window)
    obj.setupDataModels(wordDataModel,tagDataModel, defDataModel, onlineDefModel)
    obj.dictionary  = None
    obj.language    = None
    obj.app         = app
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
    if len(dicFile) == 0:
      print("Could not find corresponding hunspell .dic file for " + language + " language")
      return None,None
    if len(dicFile) == 0:
      print("Could not find corresponding hunspell .aff file for " + language + " language")
      return None,None
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
    print("Loading project file version " + str(version))
    if version > 0.01:
      projectName = pickle.load(_input)
    language = pickle.load(_input)
    if obj is None:
      obj = cls()
      if version > 0.02:
        wordDataModel = WordDataModel.fromFile(_input)
        tagDataModel = TagDataModel.fromFile(_input)
        onlineDefDataModel = OnlineDefinitionDataModel(_input)
        defDataModel = DefinitionDataModel.fromFile(_input)
      else:
        wordDataModel = WordDataModel.fromFile(_input)
        tagDataModel = TagDataModel.fromFile(_input)
        onlineDefDataModel = OnlineDefinitionDataModel.fromFile(_input)
        defDataModel = DefinitionDataModel.fromFile(_input , True)
      obj.setupUi(window)
      obj.setupDataModels(wordDataModel,tagDataModel,defDataModel)
    else:
      if version > 0.02:
        obj.wordDataModel._fromFile(_input)
        obj.tagDataModel._fromFile(_input)
        obj.onlineDefDataModel._fromFile(_input)
        obj.defDataModel._fromFile(_input)
      else:
        obj.wordDataModel._fromFile(_input)
        obj.tagDataModel._fromFile(_input)
        obj.onlineDefDataModel._fromFile(_input)
        obj.defDataModel._fromFile(_input, True)

    obj.wordDataModel.language  = language
    obj.defDataModel.language   = language
    obj.onlineDefDataModel.language = language
    obj.language                = language
    obj.projectName             = projectName
    obj.dictionary              = None
    obj.activeConnections       = []
    if language is not None:
      obj.dicPath       = "/usr/share/hunspell/"
      dicPath,affPath   = obj.findDictionary(obj.dicPath,obj.language)
      if (dicPath is not None) and (affPath is not None): 
        obj.dictionary    = obj.loadDictionary(dicPath, affPath)
    return obj
  
  def openFile(self,fileName = None, isTmpFile = False):
    if (fileName is None) | (fileName is False):
      fileName,fileType = QtWidgets.QFileDialog.getOpenFileName(self.centralwidget,"Open File", ".", "Pickle Files (*.pkl)")
    if fileName == "" or fileName is None:
      return
    else:
      Ui_MainWindow.fromFile(fileName,None,self)
      self.setWindowTitle()
      self.tagController.updateTags()
      if not isTmpFile:
        self.projectFile = fileName
      self.actionSave.setEnabled(True)
      if self.welcomeDialog.isVisible():
        self.welcomeDialog.loadedFile = True
        self.welcomeDialog.accept()
  def newProject(self):
    self.projectFile = None

  def setWindowTitle(self):
    self.mainWindow.setWindowTitle(self.projectName + " - " + "(" + str(self.language) + ")" + " - " + str(self.programName) )
  
  def saveFile(self):
    self.saveFileAs(False, self.projectFile)

  def saveFileAs(self , checked, fileName = None):
    if self._saveFileAs(checked, fileName):
      self.unsavedChanges = False
      self.autoSaveTimer.stop()
      self.writeSessionFile()

  def _saveFileAs(self , checked, fileName = None):
    if fileName is None:
      fileName,fileType = QtWidgets.QFileDialog.getSaveFileName(self.centralwidget,"Save File",".","Pickle Files (*.pkl)")
    if fileName == "" or fileName is None:
      return False
    else:
      fName = fileName
      with open(fName, 'wb') as output:
        pickle.dump(self.version, output, pickle.HIGHEST_PROTOCOL) #Version
        pickle.dump(self.projectName, output, pickle.HIGHEST_PROTOCOL) #ProjectName
        pickle.dump(self.language, output , pickle.HIGHEST_PROTOCOL) #Language
        self.wordDataModel.toFile(output)
        self.tagDataModel.toFile(output)
        self.onlineDefDataModel.toFile(output)
        self.defDataModel.toFile(output)
        self.statusBar.showMessage("Saved to "+ fileName , 2000)
        return True

  def updateDictNames(self,dictNames):
    self.dictSelect.clear()
    self.dictSelect.insertItems(0,dictNames)
    
  # def showEditWordDialog(self,event):
  #FIXME: When editing Enter key is not consumed in Delegate of TagView and is falsely propagated up to this filter. Reactivate filters when fixed.
  def eventFilter(self,_object, event):
    if _object == self.tagFilter:
      if event.type() == QtCore.QEvent.KeyPress:
        if (event.key() == QtCore.Qt.Key_Enter) or (event.key() == QtCore.Qt.Key_Return):
          #self.tagview.setFocus()
          return True
    if _object == self.tagview:
      if event.type() == QtCore.QEvent.KeyPress:
        if (event.key() == QtCore.Qt.Key_Enter) or (event.key() == QtCore.Qt.Key_Return):
          #self.wordview.setFocus()
          return True
    return False

  def requestWebPage(self,word,_dict,activeTab):
    if activeTab == 0:
      self.definitionListView.setEnabled(False)
      self.onlineDefDataModel.load(word,_dict)
    elif activeTab == 1:
      url = self.onlineDefDataModel.createUrl(word,_dict)
      self.webView.load(QtCore.QUrl(url))

  def updateOnlineDefinition(self,index):
    activeTab   = self.tabwidget.currentIndex()
    activeDict  = self.dictSelect.currentText()
    if activeDict == "":
      return
    selectedWord = self.getSelectedWord()
    if selectedWord is None:
      return
    self.requestWebPage(selectedWord,activeDict,activeTab)

  def _updateOnlineDefinition(self,definitionsList):
    self.defController.update(definitionsList)
    self.definitionListView.setEnabled(True)

  def selectedWordChanged(self,index):
    if index.isValid():
      self.editWordButton.setEnabled(True)
    else:
      self.editWordButton.setEnabled(False)
    selectedWord = self.getSelectedWord()
    self.elementController.updateOnWord(selectedWord)
    self.savedDefController.updateOnWord(selectedWord)
    self.updateOnlineDefinition(index)

  def selectedTagChanged(self,index):
    selectedTag = self.getSelectedTag()
    self.wordController.updateOnTag(selectedTag)

  def saveDefinition(self):
    definition  = self.getSelectedDefinition()
    word        = self.getSelectedWord()
    if not self.defDataModel.definitionExists(word,definition.definition):
      self._saveDefinition(definition.definition,definition.type,word)
    self.savedDefController.updateOnWord(word)

  def _saveDefinition(self,definitionText,definitionType,word):
    dictionary  = self.dictSelect.currentText()
    self.defDataModel.addDefinition(word,definitionText,dictionary,definitionType)
    self.setDirtyState()
  
  def _removeSelectedDefinition(self):
    definition  = self.getSelectedSavedDefinition().definition
    word        = self.getSelectedWord()
    self.defDataModel.removeDefinition(word,definition)
    self.setDirtyState()

  def removeDefinition(self):
    self._removeSelectedDefinition()
    self.savedDefController.updateOnWord(self.getSelectedWord())
  
  def handleEditedTag(self,widget):
    if (widget.isModified()):
      oldTag  = self.getSelectedTag()
      newTag = widget.text()
      self.tagDataModel.replaceTag(oldTag,newTag)
      self.tagController.updateTags()
      self.setDirtyState()

  def editSelectedTag(self):
    index = self.tagview.currentIndex()
    self.tagview.edit(index)
  
  def getSelectedWord(self):
    index = self.wordview.currentIndex()
    selectedWord  = self.wordController.data(index,QtCore.Qt.DisplayRole)
    if isinstance(selectedWord,str):
      return selectedWord    
    else:
      return None

  def getSelectedSavedDefinition(self):
    index = self.savedDefinitionsView.currentIndex()
    definition = self.savedDefController.getDefinition(index)
    return definition

  def getSelectedDefinition(self):
    index = self.definitionListView.currentIndex()
    definition = self.defController.getDefinition(index)
    return definition
  
  def getSelectedTag(self,viewIndex=None):
    if viewIndex is None:
      viewIndex = self.tagview.currentIndex()
    index = self.filterController.mapToSource(viewIndex)
    selectedTag = self.tagController.data(index,QtCore.Qt.EditRole)
    if isinstance(selectedTag,str):
      return selectedTag    
    else:
      return None

  def tagViewMenuRequested(self,point):
    if self.getSelectedTag() is not None:
      contextMenu = QtWidgets.QMenu ("Context menu", self.tagview)
      contextMenu.addAction(self.renameTagAction)
      contextMenu.exec(self.tagview.mapToGlobal(point))

  def savedDefViewContextMenuRequested(self,point):
    if self.getSelectedWord() is not None:
      index = self.savedDefinitionsView.indexAt(point).row()
      contextMenu = QtWidgets.QMenu ("Context menu", self.savedDefinitionsView)
      contextMenu.addAction(self.addDefinitionAction)
      if (index >= 0):
        contextMenu.addAction(self.removeDefinitionAction)
      contextMenu.exec(self.savedDefinitionsView.mapToGlobal(point))

  def wordViewContextMenuRequested(self,point):
    print("wordViewContextMenuRequested")
    index = self.wordview.indexAt(point).row()
    if (index >= 0):
      contextMenu = QtWidgets.QMenu ("Context menu", self.wordview)
      contextMenu.addAction(self.removeWordAction)
      contextMenu.exec(self.wordview.mapToGlobal(point))

  def _removeWord(self,word,tags):
    self.tagDataModel.removeTagging(word,tags)
    self.wordDataModel.removeWord(word)
    self.setDirtyState()

  def removeWord(self):
    word = self.getSelectedWord()
    tags = self.tagDataModel.getTagsFromIndex(word)
    self._removeWord(word,tags)
    self.wordController.updateOnTag(self.getSelectedTag())
    self.tagController.updateTags()
  
  def handleEditedDefinition(self,widget):
    definition  = self.getSelectedSavedDefinition()
    newDefinition = widget.text()
    word = self.getSelectedWord()
    if definition.type == "_newUserDefinition":  #Dont'replace, add to the model
      self._saveDefinition(newDefinition,"User Definition", word)
      self.savedDefController.deleteTmpDefinition()
    else:
      self.defDataModel.replaceDefinition(word,definition.definition,newDefinition)
      self.setDirtyState()
    self.savedDefController.updateOnWord(word)
  
  def addDefinition(self):
    index = self.savedDefController.addDefinition()
    self.savedDefinitionsView.setCurrentIndex(index)
    self.savedDefinitionsView.edit(index)

  def setDirtyState(self):
    if self.autoSaveTimer.isActive():
      return
    self.tempProjectFile = ".tmp_"+self.projectName+".pkl"
    self.unsavedChanges = True
    self.autoSaveTimer.start(self.autoSaveTimerInterval)

  def autoSave(self):
    self.autoSaveTimer.stop()
    self._saveFileAs(False,self.tempProjectFile)
    self.writeSessionFile()
  
  def writeSessionFile(self):
    with open(self.sessionFile, 'wb') as output:
      pickle.dump(self.version,output, pickle.HIGHEST_PROTOCOL)
      pickle.dump(self.tempProjectFile,output, pickle.HIGHEST_PROTOCOL)
      pickle.dump(self.projectFile,output, pickle.HIGHEST_PROTOCOL)
      pickle.dump(self.unsavedChanges,output, pickle.HIGHEST_PROTOCOL) #unsavedChanges
  def exitApplication(self):
    self.app.quit()

from PyQt5 import QtWebEngineWidgets 
