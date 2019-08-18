from PyQt5 import QtCore, QtGui, QtWidgets
from controllers import (DefinitionController, TagController, WordController,ElementTagController,SavedDefinitionsController)
from dialogs import WordDialog,DictionaryDialog,TagEditDialog,WelcomeDialog,PreferencesDialog
from dataModels import WordDataModel,DefinitionDataModel,TagDataModel,OnlineDefinitionDataModel
from delegates import HTMLDelegate
from widgets import myWebViewer
import pickle
import os
from hunspell import HunSpell
import uiUtils
from functools import partial
from collections import namedtuple
from dictionaries import dict_types as dictT
from fuzzyPhraseMatch import matchphrases as mp
import pandas as pd
import re

#TODO : Setup keyboard shortcuts for easily navigating between ListViews/ListEdits etc.
#TODO : [UI] Move tabs to the right/left of QTabWidget with horizontal text. Calling setTabPosition(QtWidgets.QTabWidget.West) produces vertical text

#FIXME: Dialogs do not trigger a dirty program state
#FIXME: Renaming a word through the edit dialog does not update the UI
Markup = namedtuple('Markup', ('start', 'stop','tagType'))

class Ui_MainWindow(QtCore.QObject):

  @classmethod
  def defaultInit(cls,app=None,window=None):
    wordDataModel   = WordDataModel()
    defDataModel    = DefinitionDataModel.getInstance()
    onlineDefDataModel  = OnlineDefinitionDataModel.getInstance()
    tagDataModel    = TagDataModel()

    obj = cls()
    obj.init()
    obj.setupDataModels(wordDataModel,tagDataModel, defDataModel, onlineDefDataModel)
    if window is not None:
      obj.setupUi(window)
    obj.connectUIandDMs()
    
    obj.dictionary  = None
    obj.language    = None
    obj.app         = app
    return obj

  def init(self):
    self.mainWindow = None
    self.version = 0.03
    self.definitionName = "Textbite"
    self.language = "N/A"
    self.projectName = "Untitled"
    self.programName = "LanguageWords"
    self.definitionTypes = ["Definition" , "Quotation" , "Example"]
    # Filename of file that stores session details in case the program exits in an abrupt manner
    self.sessionFile = "." + self.programName + "_" + "session" + ".pkl" 
    # Timer to trigger autosave in presence of unsaved changes 
    self.autoSaveTimer = QtCore.QTimer() 
    self.autoSaveTimer.timeout.connect(self.autoSave) 
    #Interval in ms to trigger autosave in presence of unsaved changes
    self.autoSaveTimerInterval = 3000 
    # Perm file where the project is stored
    self.projectFile = None       
    # Are there changes that have not been written to the perm file?
    self.unsavedChanges = False   
    # Filename of temp file in case of unsaved changes
    self.tempProjectFile = None

  def setupUi(self, MainWindow):
    MainWindow.setObjectName("MainWindow")
    MainWindow.resize(720, 1024)
    self.mainWindow = MainWindow
    self.applyCss()
    self.setWindowTitle()
    self.defineActions()
    self.centralwidget = QtWidgets.QWidget(MainWindow)
    self.centralwidget.setObjectName("centralwidget")
    MainWindow.setCentralWidget(self.centralwidget)
    
    #outerVerticalLayout
    outerVerticalLayout = QtWidgets.QVBoxLayout(self.centralwidget)
    #buttonHorizontalLayout(outerVerticalLayout)
    buttonHorizontalLayout = QtWidgets.QHBoxLayout()
    self.addTopButtons(buttonHorizontalLayout,self.centralwidget)
    #horizontalLayout(outerVerticalLayout)
    self.horizontalLayout = QtWidgets.QHBoxLayout()
    self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
    self.horizontalLayout.setObjectName("horizontalLayout")  
    self.addListViews(self.horizontalLayout,self.centralwidget)
    outerVerticalLayout.addLayout(buttonHorizontalLayout)
    outerVerticalLayout.addLayout(self.horizontalLayout)

    self.addMenuBar(MainWindow)            
    self.addStatusBar(MainWindow)
    self.retranslateUi(MainWindow)
    QtCore.QMetaObject.connectSlotsByName(MainWindow)

  def defineActions(self):
    self.actionNew = QtWidgets.QAction(self.mainWindow)
    self.actionNew.setObjectName("actionNew")
    self.actionNew.triggered.connect(self.newProject)
    self.actionNew.setShortcut("Ctrl+N")

    self.actionOpen = QtWidgets.QAction(self.mainWindow)
    self.actionOpen.setObjectName("actionOpen")
    self.actionOpen.triggered.connect(self.loadProject_ui_noArg)
    self.actionOpen.setShortcut("Ctrl+O")

    self.actionSaveAs = QtWidgets.QAction(self.mainWindow)
    self.actionSaveAs.setObjectName("actionSave")
    self.actionSaveAs.triggered.connect(self.saveProject_ui_as)
    self.actionSaveAs.setShortcut("Ctrl+Shift+S")

    self.actionSave = QtWidgets.QAction(self.mainWindow)
    self.actionSave.setObjectName("actionSave")
    self.actionSave.triggered.connect(self.saveProject_ui_quick)
    self.actionSave.setShortcut("Ctrl+S")
    #self.actionSave.setEnabled(False)

    self.addWordAction = QtWidgets.QAction ("Add Word", self.mainWindow)
    self.addWordAction.setObjectName("addWordAction")
    self.addWordAction.triggered.connect(self.addWord_ui)
    self.addWordAction.setShortcut("Ctrl+Shift+A")
    self.addWordAction.setToolTip("Show a dialog to add a new word to the project")

    self.editTagsOfWordAction = QtWidgets.QAction ("Edit Tags", self.mainWindow)
    self.editTagsOfWordAction.setObjectName("editTagsOfWordAction")
    self.editTagsOfWordAction.triggered.connect(self.editTagsOfWord_dialog_ui)
    self.editTagsOfWordAction.setShortcut("Ctrl+Shift+E")
    self.editTagsOfWordAction.setEnabled(False)
    self.editTagsOfWordAction.setToolTip("Show a dialog to edit the selected word")

    self.removeWordAction = QtWidgets.QAction ("Remove Word", self.mainWindow)
    self.removeWordAction.setObjectName("removeWordAction")
    self.removeWordAction.triggered.connect(self.removeWord_ui)
    self.removeWordAction.setShortcut("Ctrl+Shift+R")
    self.removeWordAction.setEnabled(False)
    self.removeWordAction.setToolTip("Remove selected word from the project")
    
    self.renameWordAction = QtWidgets.QAction ("Rename Word", self.mainWindow)
    self.renameWordAction.setObjectName("renameWordAction")
    self.renameWordAction.triggered.connect(self.editSelectedWord)    
    self.removeWordAction.setEnabled(False)
    self.removeWordAction.setToolTip("Rename selected selected word")
    
    self.addDefinitionAction = QtWidgets.QAction ("Add Custom " + self.definitionName, self.mainWindow)
    self.addDefinitionAction.setObjectName("addDefinitionAction")
    self.addDefinitionAction.triggered.connect(self.addTmpDefinitionToEdit)

    self.addTagFromWebViewAction = QtWidgets.QAction ("Add Tag", self.mainWindow)
    self.addTagFromWebViewAction.setObjectName("addTagFromWebViewAction")
    self.addTagFromWebViewAction.triggered.connect(self.addTagFromWebView)

    self.addWordFromWebViewAction = QtWidgets.QAction ("Add Word...", self.mainWindow)
    self.addWordFromWebViewAction.setObjectName("addWorfFromWebViewAction")
    self.addWordFromWebViewAction.triggered.connect(self.addWordFromWebView)

    self.removeDefinitionAction = QtWidgets.QAction ("Remove Definition", self.mainWindow)
    self.removeDefinitionAction.setObjectName("removeDefinitionAction")
    self.removeDefinitionAction.triggered.connect(self.removeSelectedDefinition_ui)

    self.editDefinitionAction = QtWidgets.QAction ("Edit Definition", self.mainWindow)
    self.editDefinitionAction.setObjectName("editDefinitionAction")
    self.editDefinitionAction.triggered.connect(self.editDefinition)

    self.renameTagAction = QtWidgets.QAction ("Rename Tag", self.mainWindow)
    self.renameTagAction.setObjectName("renameTagAction")
    self.renameTagAction.triggered.connect(self.editSelectedTag)

    self.exitAppAction = QtWidgets.QAction ("Exit application", self.mainWindow)
    self.exitAppAction.setObjectName("exitAppAction")
    self.exitAppAction.triggered.connect(self.exitApplication)

    self.showPreferencesAction = QtWidgets.QAction ("Preferences", self.mainWindow)
    self.showPreferencesAction.setObjectName("showPreferencesAction")
    self.showPreferencesAction.triggered.connect(self.showPreferencesDialog)

    self.showSelectSearchEngineAction = QtWidgets.QAction ("Select search engine", self.mainWindow)
    self.showSelectSearchEngineAction.setObjectName("showSelectSearchEngineAction")
    self.showSelectSearchEngineAction.triggered.connect(self.showSelectSearchEngine)

    self.toggleSpellingAction = QtWidgets.QAction ("Enable spelling", self.mainWindow)
    self.toggleSpellingAction.setObjectName("toggleSpellingAction")
    self.toggleSpellingAction.setCheckable(True)
    self.toggleSpellingAction.setChecked(True)

    self.useExternalBrowserAction = QtWidgets.QAction ("Use external browser", self.mainWindow)
    self.useExternalBrowserAction.setObjectName("useExternalBrowserAction")
    self.useExternalBrowserAction.setCheckable(True)
    self.useExternalBrowserAction.setChecked(False)
    
    self.markupSavedDefinitionsAction = QtWidgets.QAction ("Markup saved " + self.definitionName + "s", self.mainWindow)
    self.markupSavedDefinitionsAction.setObjectName("useExternalBrowserAction")
    self.markupSavedDefinitionsAction.triggered.connect(self.reMarkupSDandRefreshView)

    self.followSavedDefinitionHyperlinkAction = QtWidgets.QAction ("Open in browser ", self.mainWindow)
    self.followSavedDefinitionHyperlinkAction.setObjectName("followSavedDefinitionHyperlinkAction")
    self.followSavedDefinitionHyperlinkAction.triggered.connect(partial(self.followSavedDefinitionHyperlink,None) )

    self.hideCentralPanelAction = QtWidgets.QAction ("Maximize content retrieval", self.mainWindow)
    self.hideCentralPanelAction.setObjectName("hideCentralPanelAction")
    self.hideCentralPanelAction.triggered.connect(self.hideCentralPanel)
    self.hideCentralPanelAction.setShortcut("F11")

    self.createAddDefFromWebViewActions()
    self.changeDefinitionTypeActions()
    
  def defineDictionaryActions(self):
    """ Define actions related to the dictionary modules we find"""
    self.createGetDefinitionsActions()
    self.selectDefinitionsProviderActions[0].trigger()
    self.createSearchForWordActions()
    self.selectEngineActions[0].trigger()
    self.searchForWordAction.setChecked(True)
    self.addDictionaryActionsToMenuBar()

  def createGetDefinitionsActions(self):
    self.selectDefinitionsProviderActions  = []
    defDicts = self.onlineDefDataModel.getDictNamesProvidingDefinitions()
    langDicts = self.onlineDefDataModel.getDictNamesProvidingLanguage(self.language)
    compatibleDicts = set(defDicts).intersection(langDicts) 
    for dictionary in compatibleDicts:
      selectDefinitionsProviderAction = QtWidgets.QAction (dictionary, self.mainWindow)
      selectDefinitionsProviderAction.setObjectName("GetDefinitions"+dictionary+"Action")
      selectDefinitionsProviderAction.triggered.connect( partial(self.selectDefinitionsProvider,dictionary , selectDefinitionsProviderAction) )
      selectDefinitionsProviderAction.setCheckable(True)
      selectDefinitionsProviderAction.setChecked(False)
      self.selectDefinitionsProviderActions.append(selectDefinitionsProviderAction)
  
  def selectDefinitionsProvider(self , dictionary , action):
    self.createGetDefinitionsAction_context(dictionary)
    self.selectedDefinitionsDict = dictionary
    for a in self.selectDefinitionsProviderActions:
      if a is not action:
        a.setChecked(False)

  def createSearchForWordActions(self):
    self.selectEngineActions  = []
    urlDicts = self.onlineDefDataModel.getDictNamesProvidingUrls()
    langDicts = self.onlineDefDataModel.getDictNamesProvidingLanguage(self.language)
    compatibleDicts = set(urlDicts).intersection(langDicts) 
    for dictionary in compatibleDicts:
      selectEngineAction = QtWidgets.QAction (dictionary, self.mainWindow)
      selectEngineAction.setObjectName("Select"+dictionary+"Action")
      selectEngineAction.triggered.connect(partial(self.selectSearchEngine,dictionary,selectEngineAction) )
      selectEngineAction.setCheckable(True)
      selectEngineAction.setChecked(False)
      self.selectEngineActions.append(selectEngineAction)

  def createAddDefFromWebViewActions(self):
    self.addDefFromWebViewMenu          = QtWidgets.QMenu("Add" + self.definitionName + " as...")
    self.addDefFromWebViewAction        = self.addDefFromWebViewMenu.menuAction()
    for definitionType in self.definitionTypes:
      addDefFromWebViewAction = QtWidgets.QAction (definitionType, self.mainWindow)
      addDefFromWebViewAction.setObjectName("addDefFromWebViewAction_"+definitionType)
      addDefFromWebViewAction.triggered.connect( partial(self.addDefFromWebView,definitionType) )
      self.addDefFromWebViewMenu.addAction(addDefFromWebViewAction)
  
  def changeDefinitionTypeActions(self):
    self.changeDefTypeMenu          = QtWidgets.QMenu("Change" + self.definitionName + " type")
    self.changeDefTypeAction        = self.changeDefTypeMenu.menuAction()
    for definitionType in self.definitionTypes:
      changeDefTypeAction = QtWidgets.QAction (definitionType, self.mainWindow)
      changeDefTypeAction.setObjectName("changeDefTypeAction_"+definitionType)
      changeDefTypeAction.triggered.connect( partial(self.changeDefinitionType,definitionType) )
      self.changeDefTypeMenu.addAction(changeDefTypeAction)

  def selectSearchEngine(self,dictionary,action):
    self.createSearchForWordAction_context(dictionary)
    self.selectedSearchDict = dictionary
    for a in self.selectEngineActions:
      if a is not action:
        a.setChecked(False)

  def followOnlineDefinitionHyperlink(self,index = None):
    definition = self.getSelectedOnlineDefinition()
    if definition.hyperlink is not None:
      self.openLinkInBrowser(definition.hyperlink)
    else:
      self.statusBar.showMessage("No hyperlink to follow ", 1000)
  
  def followSavedDefinitionHyperlink(self,index = None):
    definition = self.getSelectedSavedDefinition()
    if definition.hyperlink is not None:
      self.openLinkInBrowser(definition.hyperlink)
    else:
      self.statusBar.showMessage("No hyperlink to follow ", 1000)

  def openLinkInBrowser(self,link):
    if ( self.useExternalBrowserAction.isChecked() ):
      QtGui.QDesktopServices.openUrl(QtCore.QUrl(link))
    else:
      url = QtCore.QUrl.fromUserInput(link)
      self.tabwidget.setCurrentIndex(1)
      self.webView.load(url)
      self.statusBar.showMessage("Loading page from : " + str(url.toDisplayString() ))

  def requestOnlineDefinition(self,word,_dict):
    self.onlineDefDataModel.load(word,_dict,isDefinition=True,_async= True)

  def requestOnlineDefinition_ui(self,dictionary):
    self.dictionaryContentType  = "definitionList"
    self.selectedDict           = dictionary
    self.searchForWordAction.setChecked(False)
    self.getDefinitionsAction.setChecked(True)
    index = self.tabwidget.indexOf(self.onlineDefinitionsView)
    if index == -1:
      self.tabwidget.insertTab(0,self.onlineDefinitionsView , "List")
    self.tabwidget.setCurrentIndex(0)
    self.onlineDefinitionsView.setEnabled(False)
    self.requestOnlineDefinition(self.getSelectedWord(),self.selectedDefinitionsDict)

  def createGetDefinitionsAction_context(self,dictionary):
    try:
      prevAction                = self.getDefinitionsAction
    except AttributeError:
      prevAction = None
    self.getDefinitionsAction = QtWidgets.QAction ("Get Definitions from " + dictionary, self.mainWindow)
    self.getDefinitionsAction.setObjectName("getDefinitionsAction")
    self.getDefinitionsAction.triggered.connect(partial(self.requestOnlineDefinition_ui,dictionary) )
    self.getDefinitionsAction.setCheckable(True)
    if prevAction is not None:
      self.getDefinitionsAction.setChecked(prevAction.isChecked())
    self.dictionaryContentType  = "definitionList"
    self.selectedDict           = dictionary

  def createSearchForWordAction_context(self,engine):
    try:
      prevAction                = self.searchForWordAction
    except AttributeError:
      prevAction = None
    self.searchForWordAction = QtWidgets.QAction ("Search using "+ engine, self.mainWindow)
    self.searchForWordAction.setObjectName("searchForWordAction")
    self.searchForWordAction.triggered.connect(partial(self.searchForWordInBrowser,engine) )
    self.searchForWordAction.setCheckable(True)
    if prevAction is not None:
      self.searchForWordAction.setChecked(prevAction.isChecked())

    self.dictionaryContentType  = "urls"
    self.selectedDict           = engine
  
  def searchForWordInBrowser(self , engine):
    self.dictionaryContentType  = "urls"
    self.selectedDict           = engine
    self.searchForWordAction.setChecked(True)
    self.getDefinitionsAction.setChecked(False)
    url = self.onlineDefDataModel.createUrl(self.getSelectedWord(),self.selectedSearchDict)
    self.openLinkInBrowser(url)  

  def addTopButtons(self , layout ,parentWidget):
    self.addWordButton = QtWidgets.QToolButton(parentWidget)
    self.addWordButton.setObjectName("addWordButton")
    self.addWordButton.setMaximumSize(QtCore.QSize(100,50))
    self.addWordButton.setDefaultAction(self.addWordAction)
    
    self.editMetaTagsButton = QtWidgets.QPushButton(parentWidget)
    self.editMetaTagsButton.setObjectName("editMTButton")
    self.editMetaTagsButton.setMaximumSize(QtCore.QSize(150,50))
    self.editMetaTagsButton.setText("Edit &MetaTags")
    self.editMetaTagsButton.clicked.connect(self.showEditMetaTagsDialog)

    layout.addWidget(self.addWordButton)
    # layout.addWidget(self.editDictsButton)
    layout.addWidget(self.editMetaTagsButton)

  def addListViews(self,layout,parentWidget):
    #verticalLayout(layout)
    verticalLayout = QtWidgets.QVBoxLayout()

    self.wordview = QtWidgets.QListView(parentWidget)
    self.wordview.setMaximumSize(QtCore.QSize(400, 400))
    self.wordview.setObjectName("wordview")

    self.wordFilter = QtWidgets.QLineEdit(parentWidget)
    self.wordFilter.setObjectName("wordFilter")
    self.wordFilter.setPlaceholderText("Enter text to filter phrases")
    self.wordFilter.setMaximumSize(QtCore.QSize(400, 30))
    self.wordFilter.installEventFilter(self) #Catch Enter

    self.tagview = QtWidgets.QListView(parentWidget)
    self.tagview.setMaximumSize(QtCore.QSize(400, 400))
    self.tagview.setObjectName("tagview")
    self.tagview.installEventFilter(self)
    
    self.tagFilter = QtWidgets.QLineEdit(parentWidget)
    self.tagFilter.setObjectName("tagFilter")
    self.tagFilter.setPlaceholderText("Enter text to filter tags")
    self.tagFilter.setMaximumSize(QtCore.QSize(400, 30))
    self.tagFilter.installEventFilter(self) #Catch Enter

    self.elementTagview = QtWidgets.QListView(parentWidget)
    self.elementTagview.setMaximumSize(QtCore.QSize(400, 400))
    self.elementTagview.setObjectName("elementTagview")
    self.elementTagview.installEventFilter(self)

    uiUtils.addLabeledWidget("Tag List", self.tagview,verticalLayout)
    verticalLayout.addWidget(self.tagFilter)
    uiUtils.addLabeledWidget("Phrases by tag", self.wordview,verticalLayout)
    verticalLayout.addWidget(self.wordFilter)
    uiUtils.addLabeledWidget("Tags by Phrase", self.elementTagview,verticalLayout)
    
    self.savedDefinitionsView = QtWidgets.QListView(parentWidget)
    self.savedDefinitionsView.setObjectName("savedDefinitionListView")
    self.savedDefinitionsView.setItemDelegate(HTMLDelegate())
    self.savedDefinitionsView.setWordWrap(True)
    self.savedDefinitionsView.itemDelegate().commitData.connect(self.handleEditedDefinition)
    self.savedDefinitionsView.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
    self.savedDefinitionsView.setMaximumWidth(560)

    self.tabwidget = QtWidgets.QTabWidget(parentWidget)
    self.tabwidget.setTabPosition(QtWidgets.QTabWidget.South)
    self.tabwidget.setObjectName("tabwidget")
    
    self.onlineDefinitionsView = QtWidgets.QListView(self.tabwidget)
    self.onlineDefinitionsView.setObjectName("onlineDefinitionListView")
    self.onlineDefinitionsView.setItemDelegate(HTMLDelegate())
    self.onlineDefinitionsView.setWordWrap(True)
    self.tabwidget.addTab(self.onlineDefinitionsView , "List")

    self.webView = myWebViewer(self.tabwidget , [self.addDefFromWebViewAction,self.addTagFromWebViewAction,self.addWordFromWebViewAction])
    self.webView.setUrl(QtCore.QUrl("about:blank"))
    self.webView.setObjectName("webView")

    self.tabwidget.addTab(self.webView , "Web page")

    layout.addLayout(verticalLayout)
    self.savedDefLayout,self.savedDefLabel = uiUtils.addLabeledWidget("Saved " + self.definitionName + "s", self.savedDefinitionsView,layout)
    uiUtils.addLabeledWidget("Online" + self.definitionName + "s", self.tabwidget,layout)

    layout.setStretch(0,1)
    layout.setStretch(1,1)
    layout.setStretch(2,2)

  def addDictionaryActionsToMenuBar(self):
    try:
      self.menuEdit.removeAction(self.selectEngineMenu.menuAction())
      self.menuEdit.removeAction(self.selectDefProviderMenu.menuAction())
    except AttributeError:
      self.menuEdit.addSeparator()
    
    self.selectEngineMenu = self.menuEdit.addMenu("Search Engine")
    for action in self.selectEngineActions:
      self.selectEngineMenu.addAction(action)

    self.selectDefProviderMenu = self.menuEdit.addMenu(self.definitionName + " provider")
    for action in self.selectDefinitionsProviderActions:
      self.selectDefProviderMenu.addAction(action)

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

    self.menuWord = QtWidgets.QMenu(self.menubar)
    self.menuWord.setObjectName("menuWord")
    self.menuWord.addAction(self.addWordAction)
    self.menuWord.addAction(self.editTagsOfWordAction)
    self.menuWord.addAction(self.removeWordAction)

    self.menuEdit = QtWidgets.QMenu(self.menubar)
    self.menuEdit.setObjectName("menuEdit")
    self.menuEdit.addAction(self.showPreferencesAction)
    self.menuEdit.addAction(self.toggleSpellingAction)
    self.menuEdit.addAction(self.useExternalBrowserAction)
    self.menuEdit.addAction(self.markupSavedDefinitionsAction)

    self.menuView = QtWidgets.QMenu(self.menubar)
    self.menuView.setObjectName("menuView")
    self.menuView.addAction(self.hideCentralPanelAction)

    self.menubar.addAction(self.menuFile.menuAction())
    self.menubar.addAction(self.menuWord.menuAction())
    self.menubar.addAction(self.menuEdit.menuAction())
    self.menubar.addAction(self.menuView.menuAction())

    MainWindow.setMenuBar(self.menubar)
  def addStatusBar(self,MainWindow):
    self.statusBar = QtWidgets.QStatusBar(MainWindow)
    self.statusBar.setObjectName("statusbar")
    MainWindow.setStatusBar(self.statusBar)
  
  def setupDataModels(self,wordDataModel,tagDataModel,defDataModel,onlineDefDataModel):
    #Data Models
    self.wordDataModel      = wordDataModel
    self.defDataModel       = defDataModel
    self.tagDataModel       = tagDataModel
    self.onlineDefDataModel = onlineDefDataModel

  def connectUIandDMs(self):
    #Controllers
    self.wordController     = WordController(self.wordDataModel,self.tagDataModel)
    self.wordview.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
    self.wordFilterController   = QtCore.QSortFilterProxyModel()
    self.wordFilterController.setSourceModel(self.wordController)
    self.wordFilterController.setFilterCaseSensitivity(QtCore.Qt.CaseInsensitive)
    self.wordController.addView(self.wordview)
    self.wordview.setModel(self.wordFilterController)

    self.tagController      = TagController(self.tagDataModel)
    self.tagview.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
    self.tagFilterController   = QtCore.QSortFilterProxyModel()
    self.tagFilterController.setSourceModel(self.tagController)
    self.tagFilterController.setFilterCaseSensitivity(QtCore.Qt.CaseInsensitive)
    self.tagview.setModel(self.tagFilterController)
    
    self.onlineDefController      = DefinitionController(self.onlineDefDataModel)
    self.onlineDefController.addView(self.onlineDefinitionsView)
    self.onlineDefinitionsView.setModel(self.onlineDefController)
    self.elementController  = ElementTagController(self.tagDataModel)
    self.elementTagview.setModel(self.elementController)
    self.savedDefController = SavedDefinitionsController(self.defDataModel)
  
    #Set signals/slots views to controllers
    self.elementTagview.selectionModel().currentChanged.connect(self.elementController.selected)
    #View->Ui signals
    self.onlineDefinitionsView.doubleClicked.connect(self.saveDefinitionFromLV_ui)
    self.onlineDefinitionsView.clicked.connect(self.onlineDefinitionsView_clicked)     
    self.tagview.itemDelegate().commitData.connect(self.handleEditedTag)
    self.tagview.customContextMenuRequested.connect(self.tagViewMenuRequested)
    self.tagview.selectionModel().currentChanged.connect(self.selectedTagChanged)
    self.savedDefinitionsView.setModel(self.savedDefController)
    self.savedDefinitionsView.clicked.connect(self.savedDefinitionsView_clicked)     

    #self.savedDefinitionsView.doubleClicked.connect(self.removeDefinition)
    self.wordview.customContextMenuRequested.connect(self.wordViewContextMenuRequested)
    self.wordview.selectionModel().currentChanged.connect(self.selectedWordChanged)
    self.wordview.itemDelegate().commitData.connect(self.handleEditedWord)
    self.savedDefinitionsView.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
    self.savedDefinitionsView.customContextMenuRequested.connect(self.savedDefViewContextMenuRequested)
    # self.dictSelect.currentTextChanged.connect(self.requestOnlineDefinition_ui)
    #self.tabwidget.currentChanged.connect(self.requestOnlineDefinition_ui)
    #Controller->Ui signals
    #self.wordController.clearSelection.connect(self.disableEditWordButton)
    
    #View->Controller signals
    self.tagFilter.textChanged.connect(self.tagFilterController.setFilterFixedString)
    self.wordFilter.textChanged.connect(self.wordFilterController.setFilterFixedString)
    #Data models->Ui signals
    #self.onlineDefDataModel.dictNamesUpdated.connect(self.updateDictNames)
    self.onlineDefDataModel.definitionsUpdated.connect(self.updateOnlineDefinition_ui)
    self.onlineDefDataModel.showMessage.connect(self.statusBar.showMessage) #Not really needed...

    # self.dictSelect.insertItems(0,self.onlineDefDataModel.getDictNames())
      
  def retranslateUi(self, MainWindow):
    _translate = QtCore.QCoreApplication.translate
    self.menuFile.setTitle(_translate("MainWindow", "Fi&le"))
    self.menuWord.setTitle(_translate("MainWindow", "&Word"))
    self.menuEdit.setTitle(_translate("MainWindow", "&Edit"))
    self.menuView.setTitle(_translate("MainWindow", "&View"))
    self.actionNew.setText(_translate("MainWindow", "New project"))
    self.actionOpen.setText(_translate("MainWindow", "Open..."))
    self.actionSaveAs.setText(_translate("MainWindow", "Save As..."))
    self.actionSave.setText(_translate("MainWindow", "Save"))
  
  def showPreferencesDialog(self):
    self.preferencesDialog = PreferencesDialog(self.centralwidget , self, self.mainWindow , self.app, self.applyCss)
    dialogCode = self.preferencesDialog.exec()
    if dialogCode == QtWidgets.QDialog.Accepted:
      print("Accepted")
    else:
      print("Rejected")

  def showSelectSearchEngine(self):
    self.selectSearchEngineDialog = SelectSearchEngineDialog(self.centralwidget , self)
    dialogCode = self.selectSearchEngineDialog.exec()
    if dialogCode == QtWidgets.QDialog.Accepted:
      print("Accepted")
    else:
      print("Rejected")

  def addWord(self, newWord, tags):
    self.tagDataModel.addTagging(newWord,tags)
    self.wordDataModel.addWord(newWord)
    self.setDirtyState()

  def addWord_ui(self, word = None):
    if word is False:
      word = None
    dictionary = None
    if self.toggleSpellingAction.isChecked():
      dictionary = self.dictionary
    self.addWordDialog = WordDialog(self.centralwidget,self.wordDataModel,self.tagDataModel,self.onlineDefDataModel,dictionary,
                                    WordDialog.CREATE_DIALOG , word)
    dialogCode = self.addWordDialog.exec()
    if dialogCode == QtWidgets.QDialog.Accepted:
      newWord = self.addWordDialog.getWord()
      tags    = self.addWordDialog.getTags()
      self.addWord(newWord, tags)
      self.tagController.updateTags()   
      self.tagFilter.setText("")
      tagIndex = self.tagController.getTagIndex(tags[0])
      tagIndex = self.tagFilterController.mapFromSource(tagIndex)
      self.tagview.setCurrentIndex(tagIndex)
      #When the tag has not changed setCurrentIndex does not trigger a refresh of the word list
      if tagIndex == self.tagview.currentIndex():
        self.wordController.updateOnTag(tags[0])
      self.wordFilter.setText("")
      wordIndex = self.wordController.getWordIndex(newWord)
      viewIndex = self.wordFilterController.mapFromSource(wordIndex)
      self.wordview.setCurrentIndex(viewIndex)

    elif dialogCode == QtWidgets.QDialog.Rejected:
      print('Rejected')

  def replaceTagsOfWord(self, word,newTags):
    #Remove word and tags
    self.tagDataModel.replaceTagging(word,newTags)

  def replaceTagsOfWord_ui(self, word, newTags): 
    self.replaceTagsOfWord(word,newTags)
    self.tagController.updateTags()
    self.wordController.updateOnTag(self.getSelectedTag())
    wordIndex = self.wordController.getWordIndex(word)
    viewIndex = self.wordFilterController.mapFromSource(wordIndex)
    self.wordview.setCurrentIndex(viewIndex)

  def editTagsOfWord_dialog_ui(self,event):
    word = self.getSelectedWord()
    if isinstance(word,QtCore.QVariant):
      return
    tags      = self.tagDataModel.getTagsFromIndex(word)
    self.editWordDialog = WordDialog(self.centralwidget,self.wordDataModel,self.tagDataModel,self.onlineDefDataModel,self.dictionary,
                                      WordDialog.EDIT_DIALOG , word, tags)
    dialogCode = self.editWordDialog.exec()
    if dialogCode == QtWidgets.QDialog.Accepted:
      newTags    = self.editWordDialog.getTags()
      self.replaceTagsOfWord_ui(word,newTags)
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
    tempCallback,lastOpenedCallback = self.readSessionFile()
    availableLanguages = self.onlineDefDataModel.getAvailableLanguages()
    self.welcomeDialog = WelcomeDialog(self.centralwidget,self.actionOpen, self.actionNew , 
                                        self.programName , self.version , availableLanguages,
                                        lastOpenedCallback , tempCallback)
    dialogCode = self.welcomeDialog.exec()
    if dialogCode == QtWidgets.QDialog.Accepted:
      if not self.welcomeDialog.loadedFile: #New Project
        language     = self.welcomeDialog.languageComboBox.currentText()
        projectName  = self.welcomeDialog.nameLineEdit.text()
        self.newProject_ui(language,projectName)
    elif dialogCode == QtWidgets.QDialog.Rejected:
      self.exitAppAction.trigger()
  # def disableEditWordButton(self):
  #   self.editWordButton.setEnabled(False)
  @staticmethod
  def loadDictionary(obj,language):
    if language is not None:
      obj.dicPath       = "/usr/share/hunspell/"
      dicPath,affPath   = obj.findDictionary(obj.dicPath,obj.language)
      if (dicPath is not None) and (affPath is not None): 
        obj.dictionary    = obj._loadDictionary(dicPath, affPath)

  def _loadDictionary(self,dicFilename, affFilename):
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
      obj.setupDataModels(wordDataModel,tagDataModel,defDataModel)
      obj.setupUi(window)
      obj.connectUIandDMs()
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
    obj.loadDictionary(obj,obj.language)
    obj.defineDictionaryActions()
    return obj
  
  def openFile(self,fileName = None):
    if (fileName is None) | (fileName is False):
      fileName,fileType = QtWidgets.QFileDialog.getOpenFileName(self.centralwidget,"Open File", ".", "Pickle Files (*.pkl)")
    if fileName == "" or fileName is None:
      return None
    else:
      return fileName

  def loadProject_ui_noArg(self):
    self.loadProject_ui()

  def loadProject_ui(self, fileName=None, isTmpFile=False):
    if fileName is None:
      fileName = self.openFile(fileName)
      if fileName is None: return
    self.loadProject(fileName, isTmpFile)
    #Create html markups if they are not there
    self.markupSavedDefinitions(remarkup = False)
    self.setWindowTitle()
    self.tagController.updateTags()
    self.statusBar.showMessage("Loaded from "+ fileName , 2000)
    if self.welcomeDialog.isVisible():
      self.welcomeDialog.loadedFile = True
      self.welcomeDialog.accept()

  def loadProject(self,fileName,isTmpFile):
    Ui_MainWindow.fromFile(fileName,None,self)
    if not isTmpFile:
      self.projectFile = fileName
      self.writeSessionFile()
    self.actionSave.setEnabled(True)
  
  def newProject_ui(self , language , projectName):
    self.newProject(language,projectName)
    self.setWindowTitle()
    self.defineDictionaryActions()
    
  def newProject(self,language,projectName):
    self.language                 = language
    self.wordDataModel.language   = language
    self.defDataModel.language    = language
    self.onlineDefDataModel.language  = language
    self.loadDictionary(self,self.language)
    self.projectName = projectName
    self.projectFile = None
    self.setDirtyState()

  def setWindowTitle(self):
    self.mainWindow.setWindowTitle(self.projectName + " - " + "(" + str(self.language) + ")" + " - " + str(self.programName) )
  

  def saveFileAs(self , extension = None):
    if extension is None:
      fileName,fileType = QtWidgets.QFileDialog.getSaveFileName(self.centralwidget,"Save File",".")
    else:
      fileName,fileType = QtWidgets.QFileDialog.getSaveFileName(self.centralwidget,"Save File",".","(*" +extension +")")
    if fileName is not None:
      if fileType is not None: 
        if not fileName.endswith(extension):
          fileName += extension
    if fileName == "" or fileName is None:
      return None
    else:
      return fileName

  def filify(self,s):
    """ Method copied from https://stackoverflow.com/questions/1007481/how-do-i-replace-whitespaces-with-underscore-and-vice-versa"""
    # Remove all non-word characters (everything except numbers and letters)
    s = re.sub(r"[^\w\s]", '', s)
    # Replace all runs of whitespace with a single dash
    s = re.sub(r"\s+", '_', s)
    return s

  def saveProject_ui_quick(self):
    if self.projectFile is None:
      self.projectFile = self.filify(self.projectName) + ".pkl"
    self.saveProject_ui(self.projectFile)

  def saveProject_ui_as(self):
    self.saveProject_ui(None)

  def saveProject_ui(self , fileName = None ,isTmpFile = False):
    if fileName is None:
      fileName = self.saveFileAs(".pkl")
      if fileName is None : return
    self.saveProject(fileName , isTmpFile)
    self.statusBar.showMessage("Saved to "+ fileName , 2000)

  def saveProject(self, fName , isTmpFile = False):
    with open(fName, 'wb') as output:
      pickle.dump(self.version, output, pickle.HIGHEST_PROTOCOL) #Version
      pickle.dump(self.projectName, output, pickle.HIGHEST_PROTOCOL) #ProjectName
      pickle.dump(self.language, output , pickle.HIGHEST_PROTOCOL) #Language
      self.wordDataModel.toFile(output)
      self.tagDataModel.toFile(output)
      self.onlineDefDataModel.toFile(output)
      self.defDataModel.toFile(output)
    if not isTmpFile:
      self.unsavedChanges = False
      self.projectFile = fName
    self.autoSaveTimer.stop()
    self.writeSessionFile()     

  # def updateDictNames(self,dictNames):
  #   self.dictSelect.clear()
  #   self.dictSelect.insertItems(0,dictNames)
  #   if len(dictNames) == 0:
  #     self.dictSelect.setVisible(False)
  #     self.tabwidget.setCurrentIndex(1)
  #     self.tabwidget.removeTab(0)
  #   else:
  #     self.dictSelect.setVisible(True)
  #     if self.tabwidget.count() == 1:
  #       self.tabwidget.insertTab(0,self.onlineDefinitionsView , "List")


  def onlineDefinitionsView_clicked(self,index):
    if int( QtGui.QGuiApplication.instance().queryKeyboardModifiers() & QtCore.Qt.ControlModifier) != 0:
      self.followOnlineDefinitionHyperlink(index)        

  def savedDefinitionsView_clicked(self,index):
    if int( QtGui.QGuiApplication.instance().queryKeyboardModifiers() & QtCore.Qt.ControlModifier) != 0:
      self.followSavedDefinitionHyperlinkAction.trigger()
  # def showEditWordDialog(self,event):
  #FIXME: When editing Enter key is not consumed in Delegate of TagView and is falsely propagated up to this filter. Reactivate filters when fixed.
  def eventFilter(self,_object, event):
    if _object == self.tagFilter:
      if event.type() == QtCore.QEvent.KeyPress:
        if (event.key() == QtCore.Qt.Key_Enter) or (event.key() == QtCore.Qt.Key_Return):
          #self.tagview.setFocus()
          return True
    elif _object == self.tagview:
      if event.type() == QtCore.QEvent.KeyPress:
        if (event.key()  == QtCore.Qt.Key_Enter) or (event.key() == QtCore.Qt.Key_Return):
          #self.wordview.setFocus()
          return True
    return False



  def updateOnlineDefinition_ui(self,onlineDefinitionsList):
    word = self.getSelectedWord()
    # if word is None: return
    for i,d in enumerate(onlineDefinitionsList):
      markups = self.markupWordInText(word,d.definition)
      onlineDefinitionsList[i] = dictT.Definition(d.definition , d.type , markups , d.hyperlink )
    self.onlineDefController.update(onlineDefinitionsList)
    self.onlineDefinitionsView.scrollToTop()
    self.onlineDefinitionsView.setEnabled(True)

  def selectedWordChanged(self,index):
    if index.isValid():
      self.editTagsOfWordAction.setEnabled(True)
      self.removeWordAction.setEnabled(True)
    else:
      self.editTagsOfWordAction.setEnabled(False)
      self.removeWordAction.setEnabled(False)
    selectedWord = self.getSelectedWord()
    self.elementController.updateOnWord(selectedWord)
    self.savedDefController.updateOnWord(selectedWord)
    if self.getDefinitionsAction.isChecked():
      self.getDefinitionsAction.trigger()
    elif self.searchForWordAction.isChecked():
      self.searchForWordAction.trigger()
    else:
      raise KeyError( "No content type selected")

  def selectedTagChanged(self,index):
    oldIndex = self.wordview.currentIndex()
    selectedTag = self.getSelectedTag()
    self.wordController.updateOnTag(selectedTag)
    index = self.wordview.currentIndex()
    if index.isValid():
      self.wordview.selectionModel().setCurrentIndex(QtCore.QModelIndex(),QtCore.QItemSelectionModel.Deselect)
      self.wordview.selectionModel().setCurrentIndex(QtCore.QModelIndex(),QtCore.QItemSelectionModel.Clear)
    else:
      if oldIndex.isValid():
        self.selectedWordChanged(index)

#======Definitions=======================================================
  def saveDefinitionFromLV_ui(self , event):
    'Save selected definition from the onlineDefinitions ListView widget'
    definition  = self.getSelectedOnlineDefinition()
    self.saveDefinition_ui(definition.definition, definition.type ,definition.hyperlink, definition.markups)

  def saveDefinition_ui(self , definitionText, definitionType, hyperlink = None , markups = None):    
    word        = self.getSelectedWord()
    query = self.getDefDMQuery(word,definitionText)
    if not self.defDataModel.definitionExists(query):
      if markups is None: 
        markups  = self.markupWordInText(word,definitionText)
      dictionary  = self.selectedDefinitionsDict
      self.saveDefinition(word,definitionText,dictionary,definitionType,markups,hyperlink)
    self.savedDefController.updateOnWord(word)

  def saveDefinition(self,word,definitionText,dictionary,definitionType,markups,hyperlink=None):
    #Try to check every element of the query before adding the definition
    defTuple = DefinitionDataModel.Definition(word,definitionText,None,dictionary,definitionType,[markups],hyperlink)
    self.defDataModel.addDefinition(defTuple)
    self.setDirtyState()
  
  def removeDefinition(self,word,definition):
    query = self.getDefDMQuery(word,definition)
    self.defDataModel.removeDefinition(query)
    self.setDirtyState()

  def removeSelectedDefinition_ui(self):
    selectedDefinition  = self.getSelectedSavedDefinition().definition
    word                = self.getSelectedWord()
    self.removeDefinition(word,selectedDefinition)
    self.savedDefController.updateOnWord(self.getSelectedWord())
  
  def editDefinition(self):
    index = self.savedDefinitionsView.currentIndex()
    self.savedDefinitionsView.edit(index)
  
  def changeDefinitionType(self, newDefinitionType):
    oldDefinition = self.getSelectedSavedDefinition()
    self.replaceDefinition_ui(oldDefinition,type = newDefinitionType)

  def replaceDefinition(self,oldDefinition,**kwargs):
    newDefinition = oldDefinition._replace(**kwargs)
    if (hasattr(oldDefinition,"Index") ):
      self.defDataModel.replaceDefinition(newDefinition)
    else:
      self.defDataModel.replaceDefinition(newDefinition , oldDefinition)
    self.setDirtyState()

  def replaceDefinition_ui(self,oldDefinition,**kwargs):
    self.replaceDefinition(oldDefinition,**kwargs)
    self.savedDefController.updateOnWord(self.getSelectedWord())

  def handleEditedDefinition(self,widget):
    oldDefinition  = self.getSelectedSavedDefinition()
    newDefinitionText = widget.text()
    word = self.getSelectedWord()
    if oldDefinition.type == "_newUserDefinition":  #Dont'replace, add to the model
      _type = "User " + self.definitionName
      self.saveDefinition_ui(newDefinitionText,_type)
      self.savedDefController.deleteTmpDefinition()
    else:
      markups  = self.markupWordInText(word,newDefinitionText)
      self.replaceDefinition_ui(oldDefinition, markups = [markups], definition = newDefinitionText)
    
#======Definitions (End)=======================================================

  def handleEditedTag(self,widget):
    if (widget.isModified()):
      oldTag  = self.getSelectedTag()
      newTag = widget.text()
      self.tagDataModel.replaceTag(oldTag,newTag)
      self.tagController.updateTags()
      self.setDirtyState()

  def handleEditedWord(self,widget):
    if (widget.isModified()):
      oldWord  = self.getSelectedWord()
      newWord = widget.text()
      self.renameWord(oldWord,newWord)
      self.wordController.updateOnTag(self.getSelectedTag())
      sourceIndex = self.wordController.getWordIndex(newWord)
      viewIndex = self.wordFilterController.mapFromSource(sourceIndex)
      #Trigger a refresh of the part of the UI depending on the selected word
      self.selectedWordChanged(viewIndex)

  def editSelectedTag(self):
    index = self.tagview.currentIndex()
    self.tagview.edit(index)
  
  def editSelectedWord(self):
    index = self.wordview.currentIndex()
    self.wordview.edit(index)

  def getSelectedWord(self):
    viewIndex = self.wordview.currentIndex()
    index = self.wordFilterController.mapToSource(viewIndex)
    selectedWord  = self.wordController.data(index,WordController.DataRole)
    if isinstance(selectedWord,str):
      return selectedWord
    else:
      return None

  def getSelectedSavedDefinition(self):
    index = self.savedDefinitionsView.currentIndex()
    definition = self.savedDefController.getDefinition(index)
    return definition

  def getSelectedOnlineDefinition(self):
    index = self.onlineDefinitionsView.currentIndex()
    definition = self.onlineDefController.getDefinition(index)
    return definition
  
  def getSelectedTag(self,viewIndex=None):
    if viewIndex is None:
      viewIndex = self.tagview.currentIndex()
    index = self.tagFilterController.mapToSource(viewIndex)
    selectedTag = self.tagController.data(index,TagController.DataRole)
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
      index = self.savedDefinitionsView.indexAt(point)
      contextMenu = QtWidgets.QMenu ("Context menu", self.savedDefinitionsView)
      contextMenu.addAction(self.addDefinitionAction)
      if int(self.savedDefController.flags(index) & QtCore.Qt.ItemIsSelectable) != 0:
        contextMenu.addAction(self.removeDefinitionAction)
        contextMenu.addAction(self.followSavedDefinitionHyperlinkAction)
        contextMenu.addAction(self.changeDefTypeAction)
      if int(self.savedDefController.flags(index) & QtCore.Qt.ItemIsEditable) != 0:
        contextMenu.addAction(self.editDefinitionAction)
      contextMenu.exec(self.savedDefinitionsView.mapToGlobal(point))

  def wordViewContextMenuRequested(self,point):
    index = self.wordview.indexAt(point).row()
    contextMenu = QtWidgets.QMenu ("Context menu", self.wordview)
    contextMenu.addAction(self.addWordAction)
    if (index >= 0):
      contextMenu.addAction(self.editTagsOfWordAction)
      contextMenu.addAction(self.removeWordAction)
      contextMenu.addAction(self.renameWordAction)
      contextMenu.addSeparator()
      contextMenu.addAction(self.searchForWordAction)
      contextMenu.addAction(self.getDefinitionsAction)
    contextMenu.exec(self.wordview.mapToGlobal(point))

  def removeWord(self,word,tags):
    self.tagDataModel.removeTagging(word,tags)
    self.wordDataModel.removeWord(word)
    self.setDirtyState()

  def removeWord_ui(self):
    word = self.getSelectedWord()
    tags = self.tagDataModel.getTagsFromIndex(word)
    self.removeWord(word,tags)
    self.wordController.updateOnTag(self.getSelectedTag())
    self.tagController.updateTags()
  
  def renameWord(self,oldWord,word):
    self.wordDataModel.renameWord(oldWord,word)
    self.tagDataModel.replaceWord(oldWord,word)
    self.defDataModel.replaceWord(oldWord,word)
    self.setDirtyState()

  @staticmethod
  def getDefDMQuery(word = None , _def = None):
    return DefinitionDataModel.Definition(text = word, definition = _def)
  
  def addTmpDefinitionToEdit(self):
    index = self.savedDefController.addTmpDefinition()
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
    self.saveProject_ui(self.tempProjectFile , True)
    self.writeSessionFile()
  
  def readSessionFile(self):
    tempCallback = None
    lastOpenedCallback = None
    if os.path.exists(self.sessionFile):
      with open(self.sessionFile, 'rb') as _input:
        version = pickle.load(_input)
        self.tempProjectFile  = pickle.load(_input)
        self.projectFile      = pickle.load(_input)
        self.unsavedChanges   = pickle.load(_input)
        try:
          self.cssFileName      = pickle.load(_input)
          self.applyCss(self.cssFileName)
        except EOFError:
          pass
        if self.unsavedChanges:
          tempCallback          = partial(self.loadProject_ui,self.tempProjectFile,True)
        lastOpenedCallback    = partial(self.loadProject_ui,self.projectFile)
    return tempCallback,lastOpenedCallback

  def writeSessionFile(self):
    with open(self.sessionFile, 'wb') as output:
      pickle.dump(self.version,output, pickle.HIGHEST_PROTOCOL)
      pickle.dump(self.tempProjectFile,output, pickle.HIGHEST_PROTOCOL)
      pickle.dump(self.projectFile,output, pickle.HIGHEST_PROTOCOL)
      pickle.dump(self.unsavedChanges,output, pickle.HIGHEST_PROTOCOL)
      pickle.dump(self.cssFileName,output, pickle.HIGHEST_PROTOCOL)
  def exitApplication(self):
    self.app.quit()

  def applyCss(self,cssFileName = None):
    if cssFileName is not None:
      self.cssFileName = cssFileName
      with open(cssFileName,"r") as fh:
        self.app.setStyleSheet(fh.read())
    
    stylesheet="stylesheet_compl.css"
    with open(stylesheet,"r") as fh:
      self.mainWindow.setStyleSheet(fh.read())

  def reMarkupSDandRefreshView(self):    
    self.markupSavedDefinitions(True)
    self.savedDefController.updateOnWord(self.getSelectedWord())
  
  def markupSavedDefinitions(self, remarkup = False):
    df = self.defDataModel.savedDefinitionsTable
    for row in df.itertuples(index=True, name='Pandas'):
      if row.markups is None or remarkup:
        markups = self.markupWordInText(row.text,row.definition)
        self.replaceDefinition(row,markups = markups)

  def markupWordInText(self,word , text):
    maxDist = min( int(len(word) / 3) , 4 )
    #matches = fnm(phrase.lower(),text.lower(),max_l_dist = maxDist)
    matches = mp(word.lower(),text.lower(),0.25)
    if len(matches) == 0:
      return None
    else:
      markups = []
      for match in matches:
        markup = Markup(match.start,match.end,"bold")
        markups.append(markup)
      return markups

  def addDefFromWebView(self , _type):
    selectedText  = self.webView.selectedText()
    self.saveDefinition_ui(selectedText,_type,self.webView.url().toString())

  def addTagFromWebView(self):
    newTag = self.webView.selectedText()
    word = self.getSelectedWord()
    tags = self.tagDataModel.getTagsFromIndex(word)
    alreadyExists = any( tag for tag in tags if tag.lower() == newTag.lower() )
    if not alreadyExists:
      tags.append(newTag)
      self.replaceTagsOfWord_ui(word,tags)
  
  def addWordFromWebView(self):
    newWord = self.webView.selectedText()
    self.addWord_ui(newWord)
    
  def hideCentralPanel(self):
    if self.horizontalLayout.count() == 3:
      self.horizontalLayout.removeItem(self.savedDefLayout)
      self.savedDefinitionsView.setVisible(False)
      self.savedDefLabel.setVisible(False)
    else:
      self.horizontalLayout.insertItem(1,self.savedDefLayout)
      self.horizontalLayout.setStretch(1,1)
      self.savedDefinitionsView.setVisible(True)
      self.savedDefLabel.setVisible(True)
