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
  def __init__(self, tagTable):
    super(TagController,self).__init__()
    self.tagTable = tagTable
    self.tagIndex = pd.pivot_table(tagTable,values='text',index='tag',aggfunc=pd.Series.nunique).reset_index()
    self.selectedIndex = 0
  def rowCount(self, modelIndex):
    return len(self.tagIndex)
  def data(self, index, role):
    if not index.isValid() or not (0<=index.row()<len(self.tagIndex)):  
      return QVariant()
    if role==Qt.DisplayRole:      
      return self.getTag(index) + " ("+str(self.getTagCount(index))+")"
  def selected(self, index , prevIndex):
    self.selectedIndex = index.row()
    selectedTag = self.getTag(index)
    wordTable = self.tagTable[self.tagTable['tag'] == selectedTag]
    self.tagChanged.emit(  wordTable )
  def getTag(self,index):
    return str(self.tagIndex.iloc[index.row(),0])
  def getTagCount(self,index):
    return self.tagIndex.iloc[index.row(),1]
  # TODO: unidecode filter and pandas Series to match string with accents / no accents
  # TODO: use > = < filters to filter tags with certain number of corresponding words
  def filterTags(self,filter):
    transfomedFilter = unidecode.unidecode(filter).lower()
    self.tagIndex = pd.pivot_table(self.tagTable,values='text',index='tag',aggfunc=pd.Series.nunique).reset_index()
    self.tagIndex = self.tagIndex[self.tagIndex.tag.str.lower().str.contains(transfomedFilter)]
    self.dataChanged.emit(self.createIndex(0,0) , self.createIndex(len(self.tagIndex) , 0))

class WordController(QAbstractListModel):
  dataChanged = pyqtSignal(QModelIndex,QModelIndex)
  loadDefinition    = pyqtSignal(str, str, bool)
  def __init__(self, wordTable):
    super(WordController,self).__init__()
    self.wordTable = wordTable
    self.df_image = wordTable
    self.dict = "wiktionary"
    self.url = None
    self.currentIndex = -1
    self.externalLoading = False
  def rowCount(self, modelIndex):
    return len(self.df_image)
  def data(self, index, role):
    if not index.isValid() or not (0<=index.row()<len(self.df_image)):
      return QVariant()
    if role==Qt.DisplayRole:
      return str(self.df_image.iloc[index.row(),0])
  def selected(self, index , prevIndex):
    self.currentIndex = index.row()
    self.loadDefinition.emit(str(self.df_image.iloc[index.row(),0]),self.dict , self.externalLoading)
  def updateWords(self,wordList):
    self.df_image = pd.merge(self.wordTable, wordList, on=['text','text'])
    self.dataChanged.emit(self.createIndex(0,0) , self.createIndex(len(self.df_image) , 0))
  def updateDict(self,dictName):
    self.dict = dictName
    if self.currentIndex > 0:
      self.selected(self.createIndex(self.currentIndex, 0) , self.createIndex(0 , 0))
  def setDefinitionLoadingSource(self,widgetID):
    if widgetID == 1:
      self.externalLoading = True
    else:
      self.externalLoading = False
    if self.currentIndex > 0:
      self.selected(self.createIndex(self.currentIndex, 0) , self.createIndex(0 , 0))

