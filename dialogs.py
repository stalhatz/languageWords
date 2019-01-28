from hunspell import HunSpell
from PyQt5 import QtCore, QtGui, QtWidgets
import unidecode
#TODO: Decide if the dialog should be recreated every time it needs to be shown or 
#TODO: Lookup for hunspell dictionaries in usual directories
#TODO: Implement dictionaries ListView. Show dictionary availability while typing the word.
#TODO: Edit Dialog
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
      

  def __init__(self, parent, wordModel, defModel):
    super(WordDialog,self).__init__(parent)
    self.wordModel = wordModel
    self.dictionary = HunSpell("/usr/share/hunspell/fr.dic", "/usr/share/hunspell/fr.aff")
    self.words = [unidecode.unidecode(x.lower()) for x in self.wordModel.getWords()]

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
    dictListView  = QtWidgets.QListView(self)
    dictModel     = self.DictDialogListModel(defModel)
    dictListView.setModel(dictModel)

    self.wLineEdit = QtWidgets.QLineEdit(self)
    self.wLineEdit.setMaximumSize(QtCore.QSize(400, 25))
    self.wLineEdit.setPlaceholderText("Enter a new word")
    self.wLineEdit.textChanged.connect(self.wordTextChanged)
    vLeftLayout.addStretch()
    vLeftLayout.addWidget(dictListView)
    vLeftLayout.addWidget(self.wLineEdit)
    
    #vRightLayout (hHighLayout) 
    self.tagView = QtWidgets.QListView(self)
    self.tagModel = QtCore.QStringListModel()
    self.tagView.setModel(self.tagModel)    
    #self.tagView.setSelectionBehavior(QtWidgets.QAbstractItemView.)
    self.tLineEdit = QtWidgets.QLineEdit(self)
    self.tLineEdit.setMaximumSize(QtCore.QSize(400, 50))
    self.tLineEdit.setPlaceholderText("Enter a new tag linked to the word")
    self.tLineEdit.textChanged.connect(self.tagTextChanged)
    tagCompleter = QtWidgets.QCompleter(self.wordModel.getTags())
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
  
  def tagTextChanged(self,text):
    shouldEnable = False
    if text != "":
      if any(text == x for x in self.tagModel.stringList()):
        shouldEnable = False
        self.statusBar.showMessage("Tag already added")
      else:
        shouldEnable = True
    if shouldEnable:
      self.addTagButton.setEnabled(True)
      self.statusBar.showMessage("")
    else:
      self.addTagButton.setEnabled(False)
      

  def wordTextChanged(self,text):
    correctlySpelled = False
    if text != "":
      correctlySpelled = True
      for word in text.split():
        if not self.dictionary.spell(word):
          correctlySpelled = False
          break
    if correctlySpelled:
      if any(unidecode.unidecode(text.lower()) == s for s in self.words):
        self.okButton.setEnabled(False)
        self.statusBar.showMessage("Word already exists")
      else:
        self.okButton.setEnabled(True)
        self.statusBar.showMessage("")
    else:
      self.okButton.setEnabled(False)
      self.statusBar.showMessage("Please check your spelling")
      
  def addTag(self,event):
    stringList = self.tagModel.stringList()
    stringList.append(self.tLineEdit.text())
    self.tagModel.setStringList(stringList)
    self.tLineEdit.clear()
    self.removeTagButton.setEnabled(True)

  def removeTag(self,event):
    stringList = self.tagModel.stringList()
    if len(stringList) > 0:
      index = self.tagView.currentIndex().row()
      del stringList[index]
      self.tagModel.setStringList(stringList)
      if len(stringList) == 0:
        self.removeTagButton.setEnabled(False)

  def getTags(self):
    return self.tagModel.stringList()

  def getWord(self):
    return self.wLineEdit.text()

#FIXME: Set size of QWidgetTable elements
class DictionaryDialog(QtWidgets.QDialog):
    
  def __init__(self ,parent , defModel):
    super(DictionaryDialog,self).__init__(parent)

    vLayout     = QtWidgets.QVBoxLayout(self)

    #vLayout
    self.dictTable  = QtWidgets.QTableWidget(self)
    #self.dictTable.setMinimumSize(QtCore.QSize(500, 300))
    self.dictTable.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows )
    self.dictTable.setRowCount(len(defModel.getDictNames()))
    self.dictTable.setColumnCount(3)
    for i,dictName in enumerate(defModel.getDictNames()):
      item = QtWidgets.QTableWidgetItem(dictName)
      self.dictTable.setItem(i,0,item)
    for i,dictUrl in enumerate(defModel.dictUrls):
      item = QtWidgets.QTableWidgetItem(dictUrl)
      #Does not work...
      #item.setSizeHint(QtCore.QSize(150,30))
      self.dictTable.setItem(i,1,item)
    for i,stripAccents in enumerate(defModel.stripAccents):
      item = QtWidgets.QTableWidgetItem(str(stripAccents))
      self.dictTable.setItem(i,2,item)
    self.dictTable.selectRow(0)

    hHighLayout     = QtWidgets.QHBoxLayout()
    hLowLayout      = QtWidgets.QHBoxLayout()
    self.statusBar  = QtWidgets.QStatusBar(self)
    
    vLayout.addWidget(self.dictTable)
    vLayout.addLayout(hHighLayout)
    vLayout.addLayout(hLowLayout)
    vLayout.addWidget(self.statusBar)
    
    #hHighLayout (vLayout)
    self.addDictButton    = QtWidgets.QPushButton(self)
    self.addDictButton.setText("Add Dictionary")
    self.addDictButton.clicked.connect(self.addDictionary)
    self.editDictButton = QtWidgets.QPushButton(self)
    self.editDictButton.setText("Edit Dictionary")
    self.editDictButton.clicked.connect(self.editDictionary)
    self.removeDictButton = QtWidgets.QPushButton(self)
    self.removeDictButton.setText("Remove Dictionary")
    self.removeDictButton.clicked.connect(self.removeDictionary)
    
    hHighLayout.addWidget(self.addDictButton)
    hHighLayout.addWidget(self.editDictButton)
    hHighLayout.addWidget(self.removeDictButton)

    #hLowLayout (vLayout)
    self.okButton    = QtWidgets.QPushButton(self)
    self.okButton.setText("&OK")
    self.okButton.setEnabled(False)
    self.okButton.clicked.connect(self.accept)
    cancelButton = QtWidgets.QPushButton(self)
    cancelButton.setText("&Cancel")
    cancelButton.clicked.connect(self.reject)
    hLowLayout.addWidget(self.okButton)
    hLowLayout.addWidget(cancelButton)
  def addDictionary():
    pass
  def editDictionary():
    pass
  def removeDictionary():
    pass