from PyQt5.QtCore import (QVariant, Qt, pyqtSignal, QUrl)
from PyQt5.QtCore import (QAbstractListModel, QModelIndex, QStringListModel)
from PyQt5.QtNetwork import (QNetworkAccessManager, QNetworkRequest, QNetworkReply)

import pandas as pd

from dataModels import DefinitionDataModel
import unidecode

# TODO : [FEATURE] Animation while loading using QMovie
# TODO : [FEATURE] Enable help through tooltip messages
# (Racing condition? Is the server blocking us?).
# QNetworkAccessManager (which would be the easiest way to do this) not working due to QTBUG-68156
# Should use requests-futures
class DefinitionController(QAbstractListModel):
  dataChanged = pyqtSignal(QModelIndex,QModelIndex)
  setEnabledView = pyqtSignal(bool)
  def __init__(self):
    super(DefinitionController,self).__init__()
    self.definitionsList = []
  def loadingInitiated(self, dict, word, external):
    if not external:
      self.setEnabledView.emit(False)
  def updateDefinition(self,definitionsList):
    self.definitionsList = definitionsList
    self.setEnabledView.emit(True)
    self.dataChanged.emit(self.createIndex(0,0) , self.createIndex(len(self.definitionsList) , 0))
  def rowCount(self, modelIndex):
    return len(self.definitionsList)
  def data(self, index, role):
    if not index.isValid() or not (0<=index.row()<len(self.definitionsList)):  return QVariant()
    if role==Qt.DisplayRole:      return self.definitionsList[index.row()]

# TODO: [FEATURE] [LOW PRIORITY] unidecode filter and pandas Series to match string with accents / no accents
# TODO: [FEATURE] [LOW PRIORITY] use > = < filters to filter tags with certain number of corresponding words
class TagController(QAbstractListModel):
  dataChanged = pyqtSignal(QModelIndex,QModelIndex)
  tagChanged = pyqtSignal(str, name='tagChanged')
  def __init__(self,tagModel):
    super(TagController,self).__init__()
    self.tagModel = tagModel
    if self.tagModel.tagTable.empty:
      self.tagIndex  = pd.DataFrame(columns=["tag","text"])
    else:
      self.updateTagIndexFromModel()
    self.selectedIndex = self.createIndex(0,0)
    self.currentFilter = ""
  def rowCount(self, modelIndex):
    return len(self.tagIndex.index)
  def data(self, index, role):
    if not index.isValid() or not (0<=index.row()<len(self.tagIndex.index)):  
      return QVariant()
    if role==Qt.DisplayRole:      
      return self.getTag(index) + " ("+str(self.getTagCount(index))+")"
  def selected(self, index , prevIndex):
    self.selectedIndex = index
    selectedTag = self.getTag(index)
    self.tagChanged.emit(  selectedTag )
  def getTag(self,index):
    if isinstance(index,int):
      return str(self.tagIndex.iloc[index,0])  
    else:
      return str(self.tagIndex.iloc[index.row(),0])
  def getTagCount(self,index):
    return self.tagIndex.iloc[index.row(),1]
  def getSelectedTag(self):
    return self.getTag(self.selectedIndex)
  def updateTagIndexFromModel(self):
    self.layoutAboutToBeChanged.emit()
    self.tagIndex = pd.pivot_table(self.tagModel.tagTable,values='text',index='tag',aggfunc=pd.Series.nunique).reset_index()
    self.tagIndex.rename(columns={"text":"indexCount"},inplace = True)
    newTagsList = []
    for tag in self.tagModel.tagNodes:
      tagList = self.tagModel.getAllChildTags(tag)
      if len(tagList) > 0:
        tagList.append(tag)
        indCount = len( self.tagModel.getIndexesFromTagList(tagList).index )
        newTagsList.append({"tag":tag,"indexCount":indCount})
    if len(newTagsList) > 0:
      self.tagIndex = self.tagIndex.append(newTagsList,ignore_index = True)
    self.layoutChanged.emit()
    
  def updateTags(self):
    self.updateTagIndexFromModel()
    #self.dataChanged.emit(self.createIndex(0,0) , self.createIndex(len(self.tagIndex.index) , 0))
    selectedTag = self.getTag(self.selectedIndex)
    self.tagChanged.emit(  selectedTag )
    
#FIXME: Load word definition when shown on screen not only when selected
class WordController(QAbstractListModel):
  dataChanged       = pyqtSignal(QModelIndex,QModelIndex)
  loadDefinition    = pyqtSignal(str, str, bool)
  clearSelection    = pyqtSignal()
  currentChanged    = pyqtSignal(str)
  def __init__(self, wordModel ,tagModel):
    super(WordController,self).__init__()
    self.wordModel = wordModel
    self.tagModel = tagModel
    self.df_image = self.wordModel.wordTable
    self.dict = None
    self.url = None
    self.currentIndex = -1
    self.externalLoading = False
    self.viewList = []

  def addView(self,view):
    self.viewList.append(view)
  def rowCount(self, modelIndex):
    return len(self.df_image.index)
  def data(self, index, role):
    if not index.isValid() or not (0<=index.row()<len(self.df_image.index)):
      return QVariant()
    if role==Qt.DisplayRole:
      return str(self.df_image.iloc[index.row(),0])
  def selected(self, index , prevIndex):
    self.currentIndex = index.row()
    word = str(self.df_image.iloc[index.row(),0])
    self.currentChanged.emit(word)
    if self.dict is None:
      pass  
    else:
      self.loadDefinition.emit(word,self.dict , self.externalLoading)
  def updateOnTag(self,tag):
    tagList = self.tagModel.getAllChildTags(tag)
    tagList.append(tag)
    tagIndexTable = self.tagModel.getIndexesFromTagList(tagList)
    self.currentIndex = -1
    self.clearSelection.emit()
    for view in self.viewList:
      view.clearSelection()
      view.setCurrentIndex(QModelIndex())
    self.df_image = pd.merge(self.wordModel.wordTable, tagIndexTable, on=['text','text'])
    for view in self.viewList:
      view.dataChanged(self.createIndex(0,0) , self.createIndex(len(self.df_image.index) , 0))
    #self.dataChanged.emit(self.createIndex(0,0) , self.createIndex(len(self.df_image.index) , 0))
  def updateDict(self,dictName):
    self.dict = dictName
    if self.currentIndex > 0:
      self.selected(self.createIndex(self.currentIndex, 0) , self.createIndex(0 , 0))
  def setDefinitionLoadingSource(self,widgetID):
    if widgetID == 1:
      self.externalLoading = True
    else:
      self.externalLoading = False
    if self.currentIndex >= 0:
      self.loadDefinition.emit(str(self.df_image.iloc[self.currentIndex,0]),self.dict , self.externalLoading)

class ElementTagController(QAbstractListModel):
  dataChanged       = pyqtSignal(QModelIndex,QModelIndex)
  def __init__(self,tagModel):
    super(ElementTagController,self).__init__()
    self.tagModel = tagModel
    self.currentIndex = -1
    self.tagList  = []
    self.directTagList = []
    self.currentElement = None
    self.spliterText = "------------Inherited Tags-----------"
  def rowCount(self, modelIndex):
    return self.dataSize()
  def dataSize(self):
    if len(self.tagList) - len(self.directTagList) > 0:
      return len(self.tagList) + 1 # + spliterText
    else:
      return len(self.tagList)

  def data(self, index, role):
    if not index.isValid() or not (0<=index.row()<self.dataSize()):
      return QVariant()
    if role==Qt.DisplayRole:
      print (index.row())
      if index.row() < len(self.directTagList):
        return str(self.tagList[index.row()])
      elif index.row() == len(self.directTagList):
        return self.spliterText
      else:
        return str(self.tagList[index.row() - 1])
      
  def selected(self, index , prevIndex):
    self.currentIndex = index.row()

  def updateOnTag(self,tag):
    self.updatesOnTag = True
    self.currentElement = tag
    self.layoutAboutToBeChanged.emit()
    self.tagList = self.tagModel.getAllParentTags(tag)
    self.directTagList = self.tagModel.getDirectParentTags(tag)
    self.orderTagLists()
    self.layoutChanged.emit()
    
  def updateOnWord(self,word):
    self.updatesOnTag = False
    self.currentElement = word
    self.layoutAboutToBeChanged.emit()
    self.directTagList = self.tagModel.getTagsFromIndex(word)
    self.tagList = []
    for tag in self.directTagList:
      self.tagList += self.tagModel.getAllParentTags(tag)
    self.tagList = list(set(self.tagList))
    self.orderTagLists()
    self.layoutChanged.emit()



  def update(self):
    if self.updatesOnTag:
      self.updateOnTag(self.currentElement)
    else:
      self.updateOnWord(self.currentElement)

  def orderTagLists(self):
    self.tagList = [x for x in self.tagList if x not in self.directTagList]
    self.tagList = self.directTagList + self.tagList

  def flags(self,index):
    flags = super(ElementTagController,self).flags(index)
    if index.row() >= len(self.directTagList):
      if flags & Qt.ItemIsEnabled != 0: # If is enabled
        flags = flags ^ Qt.ItemIsEnabled
      if flags & Qt.ItemIsSelectable != 0: # If is selectable
        flags = flags ^ Qt.ItemIsSelectable
    return flags
  
  def __len__(self):
    return len(self.tagList)