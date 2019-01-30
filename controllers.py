from PyQt5.QtCore import (QVariant, Qt, pyqtSignal, QUrl)
from PyQt5.QtCore import (QAbstractListModel, QModelIndex, QStringListModel)
from PyQt5.QtNetwork import (QNetworkAccessManager, QNetworkRequest, QNetworkReply)

import pandas as pd

from dataModels import DefinitionDataModel
import unidecode
# FIXED : Async requests
# TODO : Animation while loading using QMovie
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

class TagController(QAbstractListModel):
  dataChanged = pyqtSignal(QModelIndex,QModelIndex)
  tagChanged = pyqtSignal(pd.DataFrame, name='tagChanged')
  def __init__(self, wordModel):
    super(TagController,self).__init__()
    self.wordModel = wordModel
    if self.wordModel.tagTable.empty:
      self.tagIndex  = pd.DataFrame(columns=["tag","text"])
    else:
      self.tagIndex = pd.pivot_table(self.wordModel.tagTable,values='text',index='tag',aggfunc=pd.Series.nunique).reset_index()
    self.selectedIndex = self.createIndex(0,0)
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
    wordTable = self.wordModel.tagTable[self.wordModel.tagTable['tag'] == selectedTag]
    self.tagChanged.emit(  wordTable )
  def getTag(self,index):
    return str(self.tagIndex.iloc[index.row(),0])
  def getTagCount(self,index):
    return self.tagIndex.iloc[index.row(),1]
  def updateTags(self):
    self.tagIndex = pd.pivot_table(self.wordModel.tagTable,values='text',index='tag',aggfunc=pd.Series.nunique).reset_index()
    self.dataChanged.emit(self.createIndex(0,0) , self.createIndex(len(self.tagIndex.index) , 0))
    selectedTag = self.getTag(self.selectedIndex)
    wordTable = self.wordModel.tagTable[self.wordModel.tagTable['tag'] == selectedTag]
    self.tagChanged.emit(  wordTable )
  # TODO: unidecode filter and pandas Series to match string with accents / no accents
  # TODO: use > = < filters to filter tags with certain number of corresponding words
  def filterTags(self,filter):
    transfomedFilter = unidecode.unidecode(filter).lower()
    self.tagIndex = pd.pivot_table(self.wordModel.tagTable,values='text',index='tag',aggfunc=pd.Series.nunique).reset_index()
    self.tagIndex = self.tagIndex[self.tagIndex.tag.str.lower().str.contains(transfomedFilter)]
    self.dataChanged.emit(self.createIndex(0,0) , self.createIndex(len(self.tagIndex.index) , 0))
    
#FIXME: Load word definition when shown on screen not only when selected
class WordController(QAbstractListModel):
  dataChanged = pyqtSignal(QModelIndex,QModelIndex)
  loadDefinition    = pyqtSignal(str, str, bool)
  def __init__(self, wordModel):
    super(WordController,self).__init__()
    self.wordModel = wordModel
    self.df_image = self.wordModel.wordTable
    self.dict = None
    self.url = None
    self.currentIndex = -1
    self.externalLoading = False
  def rowCount(self, modelIndex):
    return len(self.df_image.index)
  def data(self, index, role):
    if not index.isValid() or not (0<=index.row()<len(self.df_image.index)):
      return QVariant()
    if role==Qt.DisplayRole:
      return str(self.df_image.iloc[index.row(),0])
  def selected(self, index , prevIndex):
    self.currentIndex = index.row()
    if self.dict is None:
      pass  
    else:
      self.loadDefinition.emit(str(self.df_image.iloc[index.row(),0]),self.dict , self.externalLoading)
  def updateWords(self,wordList):
    self.df_image = pd.merge(self.wordModel.wordTable, wordList, on=['text','text'])
    self.dataChanged.emit(self.createIndex(0,0) , self.createIndex(len(self.df_image.index) , 0))
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

