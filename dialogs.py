from hunspell import HunSpell
from PyQt5 import QtCore, QtGui, QtWidgets
#TODO: Decide if the dialog should be recreated every time it needs to be shown or 
#TODO: Lookup for hunspell dictionaries in usual directories
#TODO: Implement dictionaries ListView. Show dictionary availability while typing the word.
# whether it should be hidden and shown thus constucted only once (responsiveness benefits?)
class WordDialog(QtWidgets.QDialog):
  class DictDialogListModel(QtCore.QAbstractListModel):
    def __init__(self):
      super(WordDialog.DictDialogListModel, self).__init__()
      self.dictNames = ["wiktionary","larousse"]
    def rowCount(self, modelIndex):
      return len(self.dictNames)
    def data(self, index, role):
      if not index.isValid() or not (0<=index.row()<len(self.dictNames)):
        return QtCore.QVariant()
      if role==QtCore.Qt.DisplayRole:
        return self.dictNames[index.row()]
      if role==QtCore.Qt.DecorationRole:
        return QtGui.QIcon.fromTheme("edit-undo")
      

  def __init__(self ,parent , wordModel):
    super(WordDialog,self).__init__(parent)
    self.wordModel = wordModel
    self.dictionary = HunSpell("/usr/share/hunspell/fr.dic", "/usr/share/hunspell/fr.aff")


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
    dictModel     = self.DictDialogListModel()
    dictListView.setModel(dictModel)

    wLineEdit = QtWidgets.QLineEdit(self)
    wLineEdit.setMaximumSize(QtCore.QSize(400, 25))
    wLineEdit.setPlaceholderText("Enter a new word")
    wLineEdit.textChanged.connect(self.wordTextChanged)
    vLeftLayout.addStretch()
    vLeftLayout.addWidget(dictListView)
    vLeftLayout.addWidget(wLineEdit)
    
    #vRightLayout (hHighLayout) 
    self.tagView = QtWidgets.QListView(self)
    self.tagModel = QtCore.QStringListModel()
    self.tagView.setModel(self.tagModel)    
    #self.tagView.setSelectionBehavior(QtWidgets.QAbstractItemView.)
    self.tLineEdit = QtWidgets.QLineEdit(self)
    self.tLineEdit.setMaximumSize(QtCore.QSize(400, 50))
    self.tLineEdit.setPlaceholderText("Enter a new tag linked to the word")
    self.tLineEdit.textChanged.connect(self.tagTextChanged)
    tagCompleter = QtWidgets.QCompleter(wordModel.getTags())
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
    self.wLineEdit.text()
