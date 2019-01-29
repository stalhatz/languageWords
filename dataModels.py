#TODO: Pickled object versioning: insert a version number to change whenever the serialized representation changes
from importlib import import_module
import pkgutil
import dictionaries
import os

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

#TODO: Store and load language from the project file
#TODO: Add tags for tags. Transitive effect when applying a certain tag to a word.
class WordDataModel(QObject):
  dataChanged         = pyqtSignal()
  def __init__(self, data = None):
    super(WordDataModel, self).__init__()
    self.version = 0.01
    if data is None:
      self.wordTable  = pd.DataFrame(columns = ["text" , "hyperlink"])
      self.tagTable   = pd.DataFrame(columns = ["text" , "tag"])
    else:
      self.wordTable  = data[0]
      self.tagTable   = data[1]

  def saveData(self,output):
    saveToPickle(self.version, output)
    #version 0.01
    saveToPickle(self.wordTable, output)
    saveToPickle(self.tagTable, output)
  
  def loadData(self,_input):
    #The version variable is only for backwards compatibility with the class version.
    #It should not be stores to the object
    version = loadFromPickle(_input)
    self.wordTable = loadFromPickle(_input)
    self.tagTable  = loadFromPickle(_input)

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
  def __init__(self, dictionaryNames = [], dictionaryUrls = []):
    super(DefinitionDataModel, self).__init__()
    self.version      = 0.02
    self.session      = FuturesSession(max_workers=1)
    self.lastRequest  = None
    self.url          = None
    self.availableDicts = self.findModules("./dictionaries")

  def findModules(self,directory):
    availableDicts = {}
    package = dictionaries
    prefix = package.__name__ + "."
    for importer, modname, ispkg in pkgutil.iter_modules(package.__path__, prefix):
      print ("Found submodule %s (is a package: %s)" % (modname, ispkg))
      dictionary = import_module(modname)
      availableDicts[dictionary.name] = dictionary
    return availableDicts

  def getDefinitionsFromHtml(self,dictName, html):
    definitionsList = self.availableDicts[dictName].getDefinitionsFromHtml(html)
    return definitionsList

  def updateDictNames(self):
    self.dictNamesUpdated.emit(getDictNames())
  
  def getDictNames(self):
    return list(self.availableDicts.keys())

  def load(self, word, dictName, externalLoad):
    url = self.availableDicts[dictName].createUrl(word,self.language)
    self.url = url
    if externalLoad:
      self.externalPageLoad.emit(QUrl(url))
    else:
      self.definitionsList = []
      future = self.session.get(url)
      future.add_done_callback(partial(self._load,url,dictName))
      self.lastRequest = future
      self.showMessage.emit("Loading from " + url)

  def _load(self,url,dictName,future):
    if url != self.url:
      future.cancel() #Should cancel itself when issuing the next request as max_workers = 1
      return
    request = future.result()
    if request.status_code > 200:
      self.showMessage.emit("Error while loading from " + url + " Code :: " + str(request.status_code))
    else:
      self.showMessage.emit("Finished loading from " + url)
      html =  request.text
      self.definitionsList = self.getDefinitionsFromHtml(dictName, html)
      self.definitionsUpdated.emit(self.definitionsList)
  

  def saveData(self,output):
    saveToPickle(self.version, output)
    #version 0.02

    

  def loadData(self,_input):
    #The version variable is only for backwards compatibility with the class version.
    #It should not be stores to the object
    version = loadFromPickle(_input)
    print("DefinitionsVersion :: " + str(version))
    #version 0.01
    if (version == 0.01):
      dictNames = loadFromPickle(_input)
      dictUrls = loadFromPickle(_input)
      stripAccents = loadFromPickle(_input)
    #version 0.02


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
