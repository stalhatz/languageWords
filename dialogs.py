from PyQt5 import QtCore, QtGui, QtWidgets
import unidecode
from controllers import TagController,ElementTagController
import os
#TODO: [DESIGN] Decide if the dialog should be recreated every time it needs to be shown or 
#TODO: Lookup for hunspell dictionaries in usual directories
#TODO: Implement dictionaries ListView. Show dictionary availability while typing the word.
# whether it should be hidden and shown thus constucted only once (responsiveness benefits?)
class WordDialog(QtWidgets.QDialog):
  class DictDialogListModel(QtCore.QAbstractListModel):
    def __init__(self,defModel):
      super(WordDialog.DictDialogListModel, self).__init__()
      self.dictNames = defModel.getDictNames()
    def rowCount(self, modelIndex):
      return len(self.dictNames)
    def data(self, index, role):
      if not index.isValid() or not (0<=index.row()<len(self.dictNames)):
        return QtCore.QVariant()
      if role==QtCore.Qt.DisplayRole:
        return self.dictNames[index.row()]
      if role==QtCore.Qt.DecorationRole:
        return QtGui.QIcon.fromTheme("edit-undo")
  
  CREATE_DIALOG = 0
  EDIT_DIALOG = 1

  def __init__(self, parent, wordDataModel,tagDataModel, defModel,dictionary,dialogType, existingWord = None , existingTags = None):
    super(WordDialog,self).__init__(parent)
    self.wordDataModel  = wordDataModel
    self.tagDataModel   = tagDataModel
    self.words          = [unidecode.unidecode(x.lower()) for x in self.wordDataModel.getWords()]
    self.dictionary           = dictionary
    self.wordSpelledCorrectly = False
    self.wordAlreadyExists    = False
    self.existingWord         = existingWord
    self.dialogType           = dialogType
    self.existingTags         = existingTags
    vLayout     = QtWidgets.QVBoxLayout(self)

    #vLayout
    hLowLayout  = QtWidgets.QHBoxLayout()
    hHighLayout = QtWidgets.QHBoxLayout()
    self.statusBar = QtWidgets.QStatusBar(self)
    vLayout.addLayout(hHighLayout)
    vLayout.addLayout(hLowLayout)
    vLayout.addWidget(self.statusBar)
    
    #hLowLayout
    self.okButton    = QtWidgets.QPushButton(self)
    self.okButton.setText("&OK")
    self.okButton.setEnabled(False)
    self.okButton.clicked.connect(self.accept)
    cancelButton = QtWidgets.QPushButton(self)
    cancelButton.setText("&Cancel")
    cancelButton.clicked.connect(self.reject)
    hLowLayout.addWidget(self.okButton)
    hLowLayout.addWidget(cancelButton)

    #hHighLayout
    vLeftLayout = QtWidgets.QVBoxLayout()
    vRightLayout = QtWidgets.QVBoxLayout()
    horizontalSpacer = QtWidgets.QSpacerItem(40, 40, QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Expanding) 
    hHighLayout.addLayout(vLeftLayout)
    hHighLayout.addItem(horizontalSpacer)
    hHighLayout.addLayout(vRightLayout)

    #vLeftLayout (hHighLayout)
    #verticalSpacer = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Expanding) 
    dictListView    = QtWidgets.QListView(self)
    dictController  = self.DictDialogListModel(defModel)
    dictListView.setModel(dictController)

    self.wLineEdit = QtWidgets.QLineEdit(self)
    self.wLineEdit.setMaximumSize(QtCore.QSize(400, 25))
    if self.dialogType == self.CREATE_DIALOG:
      self.wLineEdit.setPlaceholderText("Enter a new word")
    if self.dialogType == self.EDIT_DIALOG:
      self.wLineEdit.setPlaceholderText("Leave this blank to delete the word")
    self.wLineEdit.textChanged.connect(self.wordTextChanged)
    vLeftLayout.addStretch()
    vLeftLayout.addWidget(dictListView)
    vLeftLayout.addWidget(self.wLineEdit)
    
    #vRightLayout (hHighLayout) 
    self.tagView = QtWidgets.QListView(self)
    self.tagController = QtCore.QStringListModel()
    if self.dialogType == self.EDIT_DIALOG:
      self.tagController.setStringList(self.existingTags)
    self.tagView.setModel(self.tagController)    
    #self.tagView.setSelectionBehavior(QtWidgets.QAbstractItemView.)
    self.tLineEdit = QtWidgets.QLineEdit(self)
    self.tLineEdit.setMaximumSize(QtCore.QSize(400, 50))
    self.tLineEdit.setPlaceholderText("Enter a new tag linked to the word")
    self.tLineEdit.textChanged.connect(self.tagTextChanged)
    tagCompleter = QtWidgets.QCompleter(self.tagDataModel.getTags())
    tagCompleter.setCaseSensitivity(QtCore.Qt.CaseInsensitive)
    self.tLineEdit.setCompleter(tagCompleter)

    vRightLayout.addWidget(self.tagView)
    vRightLayout.addWidget(self.tLineEdit)
    tagHLayout = QtWidgets.QHBoxLayout()
    vRightLayout.addLayout(tagHLayout)
    
    #tagHLayout (vRightLayout (hHighLayout))
    self.addTagButton    = QtWidgets.QPushButton(self)
    self.addTagButton.setEnabled(False)
    self.addTagButton.setText("&Add Tag")
    self.addTagButton.clicked.connect(self.addTag)
    self.removeTagButton    = QtWidgets.QPushButton(self)
    self.removeTagButton.setText("&Remove Tag")
    self.removeTagButton.clicked.connect(self.removeTag)
    self.removeTagButton.setEnabled(False) #New word
    tagHLayout.addWidget(self.addTagButton)
    tagHLayout.addWidget(self.removeTagButton)
  
    if self.dialogType == self.EDIT_DIALOG:
      self.wLineEdit.setText(self.existingWord)

  def tagTextChanged(self,text):
    shouldEnable = False
    if text != "":
      if any(text == x for x in self.tagController.stringList()):
        shouldEnable = False
        self.statusBar.showMessage("Tag already added")
      else:
        shouldEnable = True
    if shouldEnable:
      self.addTagButton.setEnabled(True)
      self.statusBar.showMessage("")
    else:
      self.addTagButton.setEnabled(False)
      
  def enableOKButton(self):
    if (not self.wordSpelledCorrectly) or self.wordAlreadyExists or len(self.tagController.stringList()) == 0:
      self.okButton.setEnabled(False)
    else:
      self.okButton.setEnabled(True)
      self.statusBar.showMessage("")
    if self.wordAlreadyExists:
      self.statusBar.showMessage("Word already exists")
    elif not self.wordSpelledCorrectly:
      self.statusBar.showMessage("Please check your spelling")  
    elif len(self.tagController.stringList()) == 0:
      self.statusBar.showMessage("Need at least one tag to register word")  
    
    
  def wordTextChanged(self,text):
    if self.dialogType == self.EDIT_DIALOG and (text == self.existingWord or text == ""):
        self.wordSpelledCorrectly = True
        self.wordAlreadyExists = False
    else:
      self.wordSpelledCorrectly = False
      if text != "":
        self.wordSpelledCorrectly = True
        for word in text.split():
          if self.dictionary is not None:
            if not self.dictionary.spell(word):
              self.wordSpelledCorrectly = False
              break
      if self.wordSpelledCorrectly:   
        if any(unidecode.unidecode(text.lower()) == s for s in self.words):
          self.wordAlreadyExists = True
        else:
          self.wordAlreadyExists = False
    self.enableOKButton()

      
  def addTag(self,event):
    stringList = self.tagController.stringList()
    stringList.append(self.tLineEdit.text())
    self.tagController.setStringList(stringList)
    self.tLineEdit.clear()
    self.removeTagButton.setEnabled(True)
    self.enableOKButton()

  def removeTag(self,event):
    stringList = self.tagController.stringList()
    if len(stringList) > 0:
      index = self.tagView.currentIndex().row()
      del stringList[index]
      self.tagController.setStringList(stringList)
      if len(stringList) == 0:
        self.removeTagButton.setEnabled(False)
    self.enableOKButton()

  def getTags(self):
    return self.tagController.stringList()

  def getWord(self):
    return self.wLineEdit.text()

#FIXME: Set size of QWidgetTable elements
class DictionaryDialog(QtWidgets.QDialog):
  class DictionaryModel(QtCore.QAbstractTableModel):
    dataChanged = QtCore.pyqtSignal(QtCore.QModelIndex,QtCore.QModelIndex)
    def __init__(self,dictionaries,_id):
      super(DictionaryDialog.DictionaryModel,self).__init__()    
      self.dictionaries = dictionaries
      self.numCols =2
      self.currentIndex = 0
      self._id = _id
    def rowCount(self,index):
      #print(self._id +" :: " + str( len(self.dictionaries) ))
      return(len(self.dictionaries))
    def columnCount(self,index):
      return self.numCols
    def data(self,index,role):
      if not index.isValid() or not (0<=index.row()<len(self.dictionaries)) or not (0<=index.column()<self.numCols):
        return QtCore.QVariant()
      if role==QtCore.Qt.DisplayRole:
        if index.column() == 0:
          return self.dictionaries[index.row()].name
        if index.column() == 1:
          return str(self.dictionaries[index.row()].languages)
    def selected(self, index , prevIndex):
      self.currentIndex = index.row()
    def getSelectedDict(self):
      return self.dictionaries[self.currentIndex]
    def addDict(self,_dict):
      self.layoutAboutToBeChanged.emit()
      self.dictionaries.append(_dict)
      self.dataChanged.emit(self.createIndex(0,0) , self.createIndex(len(self.dictionaries) , self.numCols ))
      self.layoutChanged.emit()
    def removeSelectedDict(self):
      self.layoutAboutToBeChanged.emit()
      self.dictionaries.remove(self.dictionaries[self.currentIndex])
      self.dataChanged.emit(self.createIndex(0,0) , self.createIndex(len(self.dictionaries) , self.numCols ))
      self.layoutChanged.emit()
    def getDictNames(self):
      return [_dict.name for _dict in self.dictionaries]
  def __init__(self ,parent , defModel):
    super(DictionaryDialog,self).__init__(parent)

    vLayout     = QtWidgets.QVBoxLayout(self)

    #vLayout
    hHigherLayout   = QtWidgets.QHBoxLayout()
    hHighLayout     = QtWidgets.QHBoxLayout()
    hLowLayout      = QtWidgets.QHBoxLayout()
    self.statusBar  = QtWidgets.QStatusBar(self)
    
    vLayout.addLayout(hHigherLayout)
    vLayout.addLayout(hHighLayout)
    vLayout.addLayout(hLowLayout)
    vLayout.addWidget(self.statusBar)
    
    #hHigherLayout (vLayout)
    
    self.sDictTableView = QtWidgets.QTableView(self) #Selected
    self.aDictTableView = QtWidgets.QTableView(self) # Available
    self.sController         = DictionaryDialog.DictionaryModel( defModel.getSelectedDicts() , "s") 
    self.aController         = DictionaryDialog.DictionaryModel( defModel.getAvailableDicts(), "a" ) 
    self.sDictTableView.setModel(self.sController)
    self.aDictTableView.setModel(self.aController)
    self.sDictTableView.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows )
    self.aDictTableView.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows )
    self.sDictTableView.selectionModel().currentChanged.connect(self.sController.selected)
    self.aDictTableView.selectionModel().currentChanged.connect(self.aController.selected)
    self.aDictTableView.selectionModel().currentChanged.connect(self.validateSelection)
    self.sController.dataChanged.connect(self.sDictTableView.dataChanged)
    
    hHigherLayout.addWidget(self.sDictTableView)
    hHigherLayout.addWidget(self.aDictTableView)

    #hHighLayout (vLayout)
    self.addDictButton    = QtWidgets.QPushButton(self)
    self.addDictButton.setText("Add Dictionary")
    self.addDictButton.clicked.connect(self.addDictionary)
    # self.editDictButton = QtWidgets.QPushButton(self)
    # self.editDictButton.setText("Edit Dictionary")
    # self.editDictButton.clicked.connect(self.editDictionary)
    self.removeDictButton = QtWidgets.QPushButton(self)
    self.removeDictButton.setText("Remove Dictionary")
    self.removeDictButton.clicked.connect(self.removeDictionary)
    
    hHighLayout.addWidget(self.addDictButton)
    #hHighLayout.addWidget(self.editDictButton)
    hHighLayout.addWidget(self.removeDictButton)

    #hLowLayout (vLayout)
    self.okButton    = QtWidgets.QPushButton(self)
    self.okButton.setText("&OK")
    #self.okButton.setEnabled(False)
    self.okButton.clicked.connect(self.accept)
    cancelButton = QtWidgets.QPushButton(self)
    cancelButton.setText("&Cancel")
    cancelButton.clicked.connect(self.reject)
    hLowLayout.addWidget(self.okButton)
    hLowLayout.addWidget(cancelButton)
  def addDictionary(self,event):
    _dict = self.aController.getSelectedDict()
    self.sController.addDict(_dict)
    self.sDictTableView.reset()
    self.removeDictButton.setEnabled(True)
    self.addDictButton.setEnabled(False)
  def validateSelection(self, index , prevIndex):
    self._validateSelection(index.row())
  def _validateSelection(self, selectedID):
    self.selectedID = selectedID
    dictName = self.aController.dictionaries[selectedID].name
    if any(dictName == _dict.name for _dict in self.sController.dictionaries):
      self.addDictButton.setEnabled(False)
    else:
      self.addDictButton.setEnabled(True)
  def removeDictionary(self,event):
    self.sController.removeSelectedDict()
    if len(self.sController.dictionaries) == 0:
      self.removeDictButton.setEnabled(False)
    self._validateSelection(self.selectedID)

class TagEditDialog(QtWidgets.QDialog):
  def __init__(self ,parent , wordDataModel , tagDataModel):
    super(TagEditDialog,self).__init__(parent)
    self.wordDataModel = wordDataModel
    self.tagDataModel  = tagDataModel

    vLayout     = QtWidgets.QVBoxLayout(self)
    #vLayout
    hHighLayout   = QtWidgets.QHBoxLayout()
    hMiddleLayout     = QtWidgets.QHBoxLayout()
    hLowLayout      = QtWidgets.QHBoxLayout()
    self.statusBar  = QtWidgets.QStatusBar(self)
    
    vLayout.addLayout(hHighLayout)
    vLayout.addLayout(hMiddleLayout)
    vLayout.addLayout(hLowLayout)
    vLayout.addWidget(self.statusBar)
    
    #hHighLayout (vLayout)
    vLeftLayout         = QtWidgets.QVBoxLayout()
    vRightLayout        = QtWidgets.QVBoxLayout()
    hHighLayout.addLayout(vLeftLayout)
    hHighLayout.addLayout(vRightLayout)
    
    #vLeftLayout ( hHighLayout (vLayout) )
    self.tagView        = QtWidgets.QListView(self) 
    self.tagController  = TagController(self.tagDataModel) 
    self.filterController = QtCore.QSortFilterProxyModel()
    self.filterController.setSourceModel(self.tagController)
    self.tagView.setModel(self.filterController)
    self.tagView.selectionModel().currentChanged.connect(self.tagController.selected)
    self.tagController.dataChanged.connect(self.tagView.dataChanged)
    
    self.tagFilter      = QtWidgets.QLineEdit(self)
    self.tagFilter.setObjectName("metaTagDialog.tagFilter")
    self.tagFilter.setPlaceholderText("Enter text to filter tags")
    self.tagFilter.setMaximumSize(QtCore.QSize(400, 30))
    self.tagFilter.installEventFilter(self) #Catch Enter
    self.tagFilter.textChanged.connect(self.filterController.setFilterFixedString)
    vLeftLayout.addWidget(self.tagView)
    vLeftLayout.addWidget(self.tagFilter)

    #vRightLayout ( hHighLayout (vLayout) )
    self.metaTagView        = QtWidgets.QListView(self) 
    self.metaTagController  = ElementTagController(self.tagDataModel)
    self.metaTagView.setModel(self.metaTagController)
    self.mtLineEdit         = QtWidgets.QLineEdit(self)
    self.mtLineEdit.setMaximumSize(QtCore.QSize(400, 50))
    self.mtLineEdit.setPlaceholderText("Enter metatag to be applied to selected tag")
    self.mtLineEdit.textChanged.connect(self.tagTextChanged)
    tagCompleter            = QtWidgets.QCompleter(self.tagDataModel.getTags())
    tagCompleter.setCaseSensitivity(QtCore.Qt.CaseInsensitive)
    self.mtLineEdit.setCompleter(tagCompleter)
    self.metaTagView.selectionModel().currentChanged.connect(self.metaTagSelected)
    vRightLayout.addWidget(self.metaTagView)
    vRightLayout.addWidget(self.mtLineEdit)

    self.tagController.tagChanged.connect(self.metaTagController.updateOnTag)
    #hMiddleLayout (vLayout)
    self.addMetaTagButton    = QtWidgets.QPushButton(self)
    self.addMetaTagButton.setText("Add MetaTag")
    self.addMetaTagButton.clicked.connect(self.addMetaTag)
    self.removeMetaTagButton = QtWidgets.QPushButton(self)
    self.removeMetaTagButton.setText("Remove MetaTag")
    self.removeMetaTagButton.clicked.connect(self.removeMetaTag)
    
    hMiddleLayout.addWidget(self.addMetaTagButton)
    hMiddleLayout.addWidget(self.removeMetaTagButton)

    #hLowLayout (vLayout)
    self.okButton = QtWidgets.QPushButton(self)
    self.okButton.setText("&OK")
    self.okButton.clicked.connect(self.accept)
    cancelButton  = QtWidgets.QPushButton(self)
    cancelButton.setText("&Cancel")
    cancelButton.clicked.connect(self.reject)
    hLowLayout.addWidget(self.okButton)
    hLowLayout.addWidget(cancelButton)
    
  def eventFilter(self,_object, event):
    if _object == self.tagFilter:
      if event.type() == QtCore.QEvent.KeyPress:
        if (event.key() == QtCore.Qt.Key_Enter) or (event.key() == QtCore.Qt.Key_Return):
          self.tagView.setFocus()
          return True
    return False

  def tagTextChanged(self,text):
    shouldEnable = False
    if text != "":
      if any(text == x for x in self.metaTagController.tagList):
        self.statusBar.showMessage("Tag already added")
      else:
        if (text == self.tagController.getSelectedTag()):
          self.statusBar.showMessage("A tag can't apply to itself")
        else:
          shouldEnable = True
    if shouldEnable:
      self.addMetaTagButton.setEnabled(True)
      self.statusBar.showMessage("")
    else:
      self.addMetaTagButton.setEnabled(False)
  
  def metaTagSelected(self):
    pass
  # def updateMetaTags(self):
  #   metaTags = self.metaTagController.stringList()
  #   selectedTag = self.tModel.getSelectedTag()
  #   for tag in metaTags:
      
  def addMetaTag(self,event):
    metaTag = self.mtLineEdit.text()
    selectedTag = self.tagController.getSelectedTag()
    self.metaTagController.tagModel.addRelation(selectedTag , metaTag)
    self.mtLineEdit.clear()
    self.metaTagController.update()
    self.removeMetaTagButton.setEnabled(True)
    #self.enableOKButton()
  
  def removeMetaTag(self, event):
    stringList = self.metaTagController.tagList
    if len(stringList) > 0:
      index = self.metaTagView.currentIndex().row()
      selectedTag = self.tagController.getSelectedTag()
      metaTag     = self.metaTagController.getSelectedTag()
      self.metaTagController.tagDataModel.removeRelation(selectedTag,metaTag)
      self.metaTagController.update()
      if len(metaTagController) == 0:
        self.removeMetaTagButton.setEnabled(False)
    #self.enableOKButton()

class WelcomeDialog(QtWidgets.QDialog):
  def __init__(self ,parent, loadAction , newAction , programName, version ,languages):
    super(WelcomeDialog,self).__init__(parent)
    self.loadAction = loadAction
    self.newAction  = newAction
    self.loadedFile = False
    vLayout     = QtWidgets.QVBoxLayout(self)
    #vLayout
    hHighLayout   = QtWidgets.QHBoxLayout()
    hMiddleLayout     = QtWidgets.QHBoxLayout()
    hLowLayout      = QtWidgets.QHBoxLayout()
    
    welcomeMessageLabel = QtWidgets.QLabel(self)
    welcomeMessage = "Welcome to " + programName + " version " + str(version)
    welcomeMessageLabel.setText(welcomeMessage)

    vLayout.addWidget(welcomeMessageLabel)
    vLayout.addLayout(hHighLayout)
    vLayout.addLayout(hMiddleLayout)
    vLayout.addLayout(hLowLayout)
        
    #hMiddleLayout (vLayout)
    self.newProjectButton      = QtWidgets.QPushButton(self)
    self.newProjectButton.setText("New project")
    self.newProjectButton.setObjectName("welcomeDialog.newProjectButton")
    self.newProjectButton.setMinimumSize(QtCore.QSize(100, 50))
    self.newProjectButton.clicked.connect(self.accept)
    self.newProjectButton.setEnabled(False)

    self.loadProjectButton      = QtWidgets.QPushButton(self)
    self.loadProjectButton.setText("Load existing project...")
    self.loadProjectButton.setObjectName("welcomeDialog.loadProjectButton")
    self.loadProjectButton.setMinimumSize(QtCore.QSize(100, 50))
    self.loadProjectButton.clicked.connect(self.loadAction.trigger)

    hMiddleLayout.addWidget(self.newProjectButton)
    hMiddleLayout.addWidget(self.loadProjectButton)
    

    #hLowLayout (vLayout)
    self.nameLineEdit     = QtWidgets.QLineEdit(self)
    self.nameLineEdit.setObjectName("welcomeDialog.nameLineEdit")
    self.nameLineEdit.setPlaceholderText("Enter name for new project")
    self.nameLineEdit.setMinimumSize(QtCore.QSize(100, 20))
    #self.nameLineEdit.installEventFilter(self) #Catch Enter
    self.nameLineEdit.textChanged.connect(self.nameTextChanged)

    self.languageComboBox = QtWidgets.QComboBox(self)
    self.languageComboBox.insertItems(0,languages)
    self.languageComboBox.setMaximumSize(QtCore.QSize(100, 20))

    hLowLayout.addWidget(self.nameLineEdit)
    hLowLayout.addWidget(self.languageComboBox)
    
  def eventFilter(self,_object, event):
    pass
    
  def nameTextChanged(self,text):
    shouldEnable = False
    if len(text) > 3:
      self.newProjectButton.setEnabled(True)
    else:
      self.newProjectButton.setEnabled(False)
