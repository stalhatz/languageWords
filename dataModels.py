#We should create classes for offline and online dictionaries (subclasses of the same baseclass)
#For the time being it will just be functions
import unidecode
from bs4 import BeautifulSoup

from PyQt5.QtCore import (QObject,pyqtSignal,QUrl)
import pandas as pd
import pickle
from functools import partial
from requests_futures.sessions import FuturesSession
from concurrent.futures import ThreadPoolExecutor

def saveToPickle(a , filename):
  with open(filename, 'wb') as output:
    pickle.dump(a, output, pickle.HIGHEST_PROTOCOL)

def loadFromPickle(filename):
  with open(filename, 'rb') as _input:
    a = pickle.load(_input)
  return a
def splitWordsTable(table):
  tagTable = table.drop(["hyperlink"],axis="columns")
  wordTable = table.drop(["tag"], axis="columns")
  return wordTable, tagTable

class WordDataModel(QObject):
  def __init__(self, data):
    super(WordDataModel, self).__init__()
    self.wordTable  = data[0]
    self.tagTable   = data[1]

  @classmethod
  def fromFilename(cls,file):
    dictWords = loadFromPickle(file)
    wordTable, tagTable = splitWordsTable(dictWords)
    return cls([wordTable, tagTable])
    

class DefinitionDataModel(QObject):
  definitionsUpdated  = pyqtSignal(list)
  externalPageLoad    = pyqtSignal(QUrl)
  showMessage         = pyqtSignal(str)
  def __init__(self, dictionaryNames, dictionaryUrls, stripAccents):
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
      
