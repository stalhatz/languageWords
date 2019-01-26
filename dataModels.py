#TODO: Pickled object versioning: insert a version number to change whenever the serialized representation changes
import unidecode
from bs4 import BeautifulSoup

from PyQt5.QtCore import (QObject,pyqtSignal,QUrl)
import pandas as pd
import pickle
from functools import partial
from requests_futures.sessions import FuturesSession
from concurrent.futures import ThreadPoolExecutor

def saveToPickle(a , file):
  if isinstance(file,str):
    with open(file, 'wb') as output:
      pickle.dump(a, output, pickle.HIGHEST_PROTOCOL)
  else:
    pickle.dump(a, file, pickle.HIGHEST_PROTOCOL)

def loadFromPickle(file):
  if isinstance(file,str):
    with open(file, 'rb') as _input:
      a = pickle.load(_input)
  else:
    a = pickle.load(file)
  return a

def splitWordsTable(table):
  tagTable = table.drop(["hyperlink"],axis="columns")
  wordTable = table.drop(["tag"], axis="columns")
  return wordTable, tagTable

class WordDataModel(QObject):
  dataChanged         = pyqtSignal()
  def __init__(self, data = None):
    super(WordDataModel, self).__init__()
    if data is None:
      self.wordTable  = pd.DataFrame(columns = ["text" , "hyperlink"])
      self.tagTable   = pd.DataFrame(columns = ["text" , "tag"])
    else:
      self.wordTable  = data[0]
      self.tagTable   = data[1]

  def saveData(self,output):
    saveToPickle(self.wordTable, output)
    saveToPickle(self.tagTable, output)
  
  def loadData(self,_input):
    self.wordTable = loadFromPickle(_input)
    self.tagTable  = loadFromPickle(_input)

  def toFile(self,file):
    if isinstance(file,str):
      with open(file, 'wb') as output:
        self.saveData(self,output)
    else:
      self.saveData(self,output)

  def _fromFile(self,file):
    if isinstance(file,str):
      with open(file, 'rb') as _input: 
        self.loadData(_input)
    else:
      self.loadData(file)
  
  @classmethod
  def fromFile(cls,file):
    a = cls()
    a._fromFile(file)
    return a
  
  def getTags(self):
    tagIndex = pd.pivot_table(self.tagTable,values='text',index='tag',aggfunc=pd.Series.nunique).reset_index()
    return list(tagIndex['tag'])
  
  def getWords(self):
    words = self.wordTable.iloc[:,0]
    return list(words)
  
  def addWord(self,word,tags):
    self.wordTable = self.wordTable.append({"text" : word}, ignore_index = True)
    tagTableList = []
    for tag in tags:
      tagTableList.append({"tag":tag , "text" : word})
    self.tagTable = self.tagTable.append(tagTableList)
    self.dataChanged.emit()

  def updateData(self):
    self.dataChanged.emit()

class DefinitionDataModel(QObject):
  dictNamesUpdated    = pyqtSignal(list)
  definitionsUpdated  = pyqtSignal(list)
  externalPageLoad    = pyqtSignal(QUrl)
  showMessage         = pyqtSignal(str)
  def __init__(self, dictionaryNames = [], dictionaryUrls = [], stripAccents = False):
    super(DefinitionDataModel, self).__init__()
    self.dictNames    = dictionaryNames
    self.dictUrls     = dictionaryUrls
    self.stripAccents = stripAccents
    self.session = FuturesSession(max_workers=1)
    self.lastRequest = None
    self.url          = None
  @staticmethod
  def getDefinitionsFromHtml(url, html):
    definitionsList = []
    s = BeautifulSoup(html,"html.parser")
    if "wiktionary" in url:
    #Wiktionary
      for element in s.select("ol > li"):
        definitionsList.append(element.text.split("\n")[0])
    elif "larousse" in url:
      #Larousse
      for element in s.find_all("li",class_ = "DivisionDefinition"):
        definitionsList.append(str(element.find(text=True, recursive=False)))
        #print (self.definitionsList)
    return definitionsList

  def updateDictNames(self):
    self.dictNamesUpdated.emit(self.dictNames)

  def getDefinitions(self, dictName, word):
    url = self.createUrl(dictName,word)
    #self.getDefinitionsFromHtml(dictName, html)

  def createUrl(self, word, dictName):
    index = self.dictNames.index(dictName)
    url = self.dictUrls[index]
    if self.stripAccents[index]:
      word = unidecode.unidecode(word)
    return url + word
  
  def load(self, word, dictName, externalLoad):
    url = self.createUrl(word,dictName)
    self.url = url
    if externalLoad:
      self.externalPageLoad.emit(QUrl(url))
    else:
      self.definitionsList = []
      future = self.session.get(url)
      future.add_done_callback(partial(self._load,url))
      self.lastRequest = future
      self.showMessage.emit("Loading from " + url)

  def _load(self,url,future):
    if url != self.url:
      future.cancel() #Should cancel itself when issuing the next request as max_workers = 1
      return
    request = future.result()
    if request.status_code > 200:
      self.showMessage.emit("Error while loading from " + url + " Code :: " + str(request.status_code))
    else:
      self.showMessage.emit("Finished loading from " + url)
      html =  request.text
      self.definitionsList = self.getDefinitionsFromHtml(url, html)
      self.definitionsUpdated.emit(self.definitionsList)
  

  def saveData(self,output):
    saveToPickle(self.dictNames, output)
    saveToPickle(self.dictUrls, output)
    saveToPickle(self.stripAccents, output)

  def loadData(self,_input):
    self.dictNames = loadFromPickle(_input)
    self.dictUrls = loadFromPickle(_input)
    self.stripAccents = loadFromPickle(_input)


  def toFile(self,file):
    if isinstance(file,str):
      with open(file, 'wb') as output:
        self.saveData(output)
    else:
      self.saveData(file)

  def _fromFile(self,file):
    if isinstance(file,str):
      with open(file, 'rb') as _input: 
        self.loadData(_input)
    else:
      self.loadData(file)
  
  @classmethod
  def fromFile(cls,file):
    a = cls()
    a._fromFile(file)
    return a
