from PyQt5.QtCore import (QVariant, Qt, pyqtSignal, QUrl)
from PyQt5.QtCore import (QAbstractListModel, QModelIndex, QStringListModel)
from PyQt5.QtNetwork import (QNetworkAccessManager, QNetworkRequest, QNetworkReply)

import pandas as pd
from requests_futures.sessions import FuturesSession
from concurrent.futures import ThreadPoolExecutor
from functools import partial

import dictionaries as dictHandler
# FIXED : Async requests
# TODO : Animation while loading using QMovie
# (Racing condition? Is the server blocking us?).
# QNetworkAccessManager (which would be the easiest way to do this) not working due to QTBUG-68156
# Should use requests-futures
class DictWebList(QAbstractListModel):
  dataChanged = pyqtSignal(QModelIndex,QModelIndex)
  showMessage = pyqtSignal(str)
  setEnabledView = pyqtSignal(bool)
  def __init__(self):
    super(DictWebList,self).__init__()
    self.definitionsList = []
    self.lastRequest = None
    self.session = FuturesSession(max_workers=1)
    self.url = None
  def load(self,url):
    self.url = url
    self.definitionsList = []
    future = self.session.get(url.toString())
    future.add_done_callback(partial(self._load,url))
    self.lastRequest = future
    self.showMessage.emit("Loading from " + url.toString() )
    self.setEnabledView.emit(False)
  def _load(self,url,future):
    if url != self.url:
      future.cancel() #Should cancel itself when issuing the next request as max_workers = 1
      return
    request = future.result()
    if request.status_code > 200:
      self.showMessage.emit("Error while loading from " + url.toString() + " Code :: " + str(request.status_code))
    else:
      self.showMessage.emit("Finished loading from " + url.toString())
      html =  request.text
      self.definitionsList = dictHandler.getDefinitionsFromHtml(url.toString() , html)
      self.setEnabledView.emit(True)
      self.dataChanged.emit(self.createIndex(0,0) , self.createIndex(len(self.definitionsList) , 0))
  def rowCount(self, modelIndex):
    return len(self.definitionsList)
  def data(self, index, role):
    if not index.isValid() or not (0<=index.row()<len(self.definitionsList)):  return QVariant()
    if role==Qt.DisplayRole:      return self.definitionsList[index.row()]

class PandasTagList(QAbstractListModel):
  tagChanged = pyqtSignal(str, name='tagChanged')
  def __init__(self, df):
    super(PandasTagList,self).__init__()
    self.df = pd.pivot_table(df,values='text',index='tag',aggfunc=pd.Series.nunique).reset_index()
    self.selectedIndex = 0
  def rowCount(self, modelIndex):
    #print("Rowcount() :: " + str(len(self.df)))
    return len(self.df)
  def data(self, index, role):
    if not index.isValid() or not (0<=index.row()<len(self.df)):  return QVariant()
    if role==Qt.DisplayRole:      return str(self.df.iloc[index.row(),0])
  def selected(self, index , prevIndex):
    self.selectedIndex = index.row()
    self.tagChanged.emit( str(self.df.iloc[index.row(),0]) )
  def getCurrentTag():
    str(self.df.iloc[index.row(),0])

class PandasWordList(QAbstractListModel):
  dataChanged = pyqtSignal()
  pageLoad    = pyqtSignal(QUrl)
  def __init__(self, df ,webview):
    super(PandasWordList,self).__init__()
    self.df = df
    self.df_image = df
    self.webView = webview
    self.dict = "wiktionary"
    self.url = None
    self.currentIndex = -1
  def rowCount(self, modelIndex):
    return len(self.df_image)
  def data(self, index, role):
    if not index.isValid() or not (0<=index.row()<len(self.df_image)):
      return QVariant()
    if role==Qt.DisplayRole:
      return str(self.df_image.iloc[index.row(),0])
  def selected(self, index , prevIndex):
    self.url =  QUrl(dictHandler.createUrl(self.dict , str(self.df_image.iloc[index.row(),0])))
    self.currentIndex = index.row()
    self.pageLoad.emit(self.url)
  def reload(self):
    if self.url is not None:
      self.pageLoad.emit(self.url)
  def updateWords(self,tag):
    self.df_image = self.df[self.df['tag'] == tag]
    self.dataChanged.emit()
  def updateDict(self,dictName):
    self.dict = dictName
    if self.currentIndex > 0:
      self.selected(self.createIndex(self.currentIndex,0) , self.createIndex(0 , 0))
  #def addWord(self, word):
