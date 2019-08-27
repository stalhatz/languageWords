from importlib import import_module
import pkgutil
import os
import importlib
import sys
from PyQt5.QtCore import (QObject,pyqtSignal,QUrl)
import pandas as pd
import pickle
from functools import partial
from requests_futures.sessions import FuturesSession
import requests
from concurrent.futures import ThreadPoolExecutor
import copy
from collections import namedtuple

from wikipedia.exceptions import WikipediaException

def pandasCondition(dataFrame, query,fields):
  condition = None
  if len(fields) > 0:
    for f in fields:
      value = getattr(query,f)
      if value is None:
        raise ValueError("Not defined value in key")
      fieldCondition = (dataFrame[f] == value)
      if condition is not None:
        condition = fieldCondition & condition
      else:
        condition = fieldCondition
    return condition

  for value,field in zip(query,query._fields):
    if value is not None:
      fieldCondition = (dataFrame[field] == value)
      if condition is not None:
        condition = fieldCondition & condition
      else:
        condition = fieldCondition
  return condition

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

class WordDataModel():
  def __init__(self, wordTable = None):
    super(WordDataModel, self).__init__()
    self.version = 0.01
    if wordTable is None:
      self.wordTable  = pd.DataFrame(columns = ["text" , "timestamp"])
    else:
      self.wordTable  = wordTable

  def saveData(self,output):
    saveToPickle(self.version, output)
    #version 0.01
    saveToPickle(self.wordTable, output)
  
  def loadData(self,_input):
    #The version variable is only for backwards compatibility with the class version.
    #It should not be stores to the object
    version = loadFromPickle(_input)
    print("Loading WordDataModel version " + str(version))
    self.wordTable = loadFromPickle(_input)

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
  
  def getWords(self):
    words = self.wordTable.iloc[:,0]
    return list(words)
  
  def addWord(self,word):
    self.wordTable = self.wordTable.append({"text" : word , "timestamp": pd.Timestamp.now()}, ignore_index = True)

  def removeWord(self,word):
    self.wordTable.set_index("text",inplace = True)
    self.wordTable.drop(word , inplace = True)
    self.wordTable.reset_index(inplace = True)
  
  def renameWord(self,oldWord,newWord):
    condition = (self.wordTable.text == oldWord)
    self.wordTable.loc[condition,"text"] = newWord

#FIXME: Sequential loading for suggested tags. Should be moved to threaded requests.
class OnlineDefinitionDataModel(QObject):
  dictNamesUpdated    = pyqtSignal(list)
  tagsUpdated         = pyqtSignal(list)
  definitionsUpdated  = pyqtSignal(list)
  showMessage         = pyqtSignal(str)
  
  def __init__(self):
    super(OnlineDefinitionDataModel, self).__init__()
    self.enableCaching = False
    self.session      = FuturesSession(max_workers=1)
    self.executor     = ThreadPoolExecutor(max_workers=1)
    self.language     = None
  
  @classmethod
  def getInstance(cls,modulePath = "./dictionaries"):
    obj = cls()
    obj.version      = 0.02
    obj.enableCaching= True
    obj.cacheExpires = True
    obj.cacheExpirationPeriod = pd.Timedelta(weeks=1)
    if obj.enableCaching:
      obj.requestCache  = pd.DataFrame(columns = ["html" , "timestamp"])
    obj.session      = FuturesSession(max_workers=1)
    obj.lastRequest  = None
    obj.url          = None
    obj.findModules(modulePath)
    
    return obj

  def findModules(self,directory= None,packageName = "dictionaries"):
    self.availableDicts = {}
    if directory is not None:
      sys.path.insert(0,str(directory))
    package  = importlib.import_module(packageName)
    prefix = package.__name__ + "."
    for importer, modname, ispkg in pkgutil.iter_modules(package.__path__, prefix):
      #print ("Found submodule %s (is a package: %s)" % (modname, ispkg))
      dictionary = import_module(modname)
      try:
        self.availableDicts[dictionary.name] = dictionary
      except AttributeError:
        continue
    return self.availableDicts

  def getAvailableLanguages(self):
    return list ( set( [l for d in self.availableDicts.values() for l in d.languages] ) )

  def getDictNames(self):
    return list(self.availableDicts.keys())

  def getDictNamesProvidingLanguage(self , language):
    dictNames = [x for x in self.getDictNames() if self.canDictProvideLanguage(x,language)]
    return dictNames

  def getDictNamesProvidingUrls(self):
    dictNames = [x for x in self.getDictNames() if self.canDictProvideUrls(x)]
    return dictNames

  def getDictNamesProvidingDefinitions(self):
    dictNames = [x for x in self.getDictNames() if self.canDictProvideDefinitions(x)]
    return dictNames

  #TODO: Test for a dictionary without a languages attribute
  def canDictProvideLanguage(self,dictName , language):
    return (not hasattr(self.availableDicts[dictName], 'languages') ) \
      or any( x for x in self.availableDicts[dictName].languages if x == language)

  def canDictProvideUrls(self,dictName):
    return hasattr(self.availableDicts[dictName], 'createUrl')
  
  def canDictProvideDefinitions(self,dictName):
    return hasattr(self.availableDicts[dictName], 'getDefinitions')

  def canDictHandleDataLoading(self,dictName):
    return hasattr(self.availableDicts[dictName], 'loadData')
  
  def loadDataFromDict(self,dictName,url):
    return self.availableDicts[dictName].loadData(url)

  def getTagsFromDict(self,dictName, data):
    tagList = []
    if hasattr(self.availableDicts[dictName], 'getTags'):
      tagsList        = self.availableDicts[dictName].getTags(data,self.language)
    return tagsList

  def getDefinitionsFromDict(self,dictName, data):
    definitionsList = self.availableDicts[dictName].getDefinitions(data,self.language)
    return definitionsList

  def updateDictNames(self):
    self.dictNamesUpdated.emit(list(self.availableDicts.keys()))

  def createUrl(self,word,dictName):
    if (word is None) or (self.language is None) or (dictName is None):
      return None
    url = self.availableDicts[dictName].createUrl(word,self.language)
    return url

  def loadDefinition(self,word,dictName):
    self.load(word, dictName,isDefinition = True , _async = True)

  def loadTags(self, word , dictNames = None):
    for dictName in self.availableDicts:
      if hasattr(self.availableDicts[dictName], 'getTagsFromHtml'):
        self.load(word,dictName,isDefinition = False , _async = False) 
  
  def triggerEmptyUpdate(self, isDefinition):
    if isDefinition:
      self.definitionsUpdated.emit([])
    else:
      self.tagsUpdated.emit([])

  def load(self,word, dictName,isDefinition=False,_async= False):
    if (word is None) or (dictName is None):
      self.triggerEmptyUpdate(isDefinition)
      return
    url       = self.createUrl(word,dictName)  
    if url is None:
      self.triggerEmptyUpdate(isDefinition)
      return
    if self.enableCaching:
      try:
        cacheRecord = self.requestCache.loc[url,:]
        if self.cacheExpires:
          if self.cacheExpirationPeriod < pd.Timestamp.now() - cacheRecord.timestamp:
            self.requestCache.drop(url , inplace = True)
            raise KeyError("Cache expired")
        self.showMessage.emit("Loaded " + url + " from cached copy")
        self.parseOnlineData(cacheRecord.html,dictName,isDefinition)
        return
      except KeyError:
        pass
    if _async:
      self.loadAsync(url,dictName,isDefinition)
    else:
      self.loadSequential(url,dictName,isDefinition)

  def loadSequential(self, url,dictName,isDefinition=False):
    if canDictHandleDataLoading(dictName):
      try:
        response = loadDataFromDict(dictName,url)
      except ConnectionError as a:
        self.showMessage.emit("Connexion to " + str(url) + " failed. " + str(a))
        return
    else:
      try:
        response  = requests.get(url,timeout = 1)
      except requests.exceptions.RequestException as a:
        self.showMessage.emit("Connexion to " + str(url) + " failed. " + str(a))
        return
      if response.status_code > 200:
        self.showMessage.emit("Error while loading from " + url + " Code :: " + str(response.status_code))
        return
      response = response.text
    self.handleResponse(response,url,dictName,isDefinition)

  def loadAsync(self, url,dictName,isDefinition=True):
    if self.canDictHandleDataLoading(dictName):
      loadDataFunc = partial(self.loadDataFromDict,dictName,url)
      future = self.executor.submit(loadDataFunc)
      future.add_done_callback(partial(self._loadAsyncFromDictionary,url,dictName,isDefinition))
    else:
      self.url = url
      future = self.session.get(url,timeout = 1)
      future.add_done_callback(partial(self._loadAsyncHtml,url,dictName,isDefinition))
      self.lastRequest = future
      self.showMessage.emit("Loading from " + url)
  
  #This is run by a thread other the main one. Though interpreter lock is in place, we should make sure there are no race conditions...
  def _loadAsyncHtml(self,url,dictName,isDefinition,future):
    if url != self.url:
      future.cancel() #Should cancel itself when issuing the next request as max_workers = 1
      return
    try:
      response = future.result()
    except requests.exceptions.RequestException as e:
      self.showMessage.emit("Connexion to " + str(url) + " failed. " + str(e))
      return
    if response.status_code > 200:
      self.showMessage.emit("Error while loading from " + url + " Code :: " + str(response.status_code))
      return
    else:
      self.handleResponse(response.text,url,dictName,isDefinition)
  def _loadAsyncFromDictionary(self,url,dictName,isDefinition,future):
    try:
      response = future.result()
    except ConnectionError as e:
      self.showMessage.emit("Connexion to " + str(url) + " failed. " + str(e))
      return
    self.handleResponse(response,url,dictName,isDefinition)

  def handleResponse(self,data,url,dictName,isDefinition=True):
    if self.enableCaching:
      try:
        self.requestCache.drop(url , inplace = True)
      except KeyError:
        pass
      newRecord         = pd.Series({"html":data , "timestamp":pd.Timestamp.now()}, name = url)
      self.requestCache = self.requestCache.append(newRecord)
    self.showMessage.emit("Finished loading from " + url)
    self.parseOnlineData(data,dictName,isDefinition)
  
  def parseOnlineData(self,data,dictName,isDefinition):
    if isDefinition:
      definitionsList = self.getDefinitionsFromDict(dictName, data)
      self.definitionsUpdated.emit(definitionsList)
    else: #Update tags
      tagsList        = self.getTagsFromDict(dictName,data)
      if tagsList:
        self.tagsUpdated.emit(tagsList)

  def saveData(self,output):
    saveToPickle(self.version, output)
    #version 0.01
    saveToPickle(self.getDictNames(), output)
    #version 0.02
    saveToPickle(self.requestCache, output)

  def loadData(self,_input,noVersion):
    #The version variable is only for backwards compatibility with the class version.
    #It should not be stored to the object
    version = loadFromPickle(_input)
    print("Loading OnlineDefinitionDataModel version " + str(version))
    #version 0.01
    dictNames = loadFromPickle(_input)
    if version > 0.01:
      self.requestCache = loadFromPickle(_input)

  def toFile(self,file):
    if isinstance(file,str):
      with open(file, 'wb') as output:
        self.saveData(output)
    else:
      self.saveData(file)

  def _fromFile(self,file,noVersion = False):
    if isinstance(file,str):
      with open(file, 'rb') as _input: 
        self.loadData(_input,noVersion)
    else:
      self.loadData(file,noVersion)
  
  @classmethod
  def fromFile(cls,file,noVersion = False):
    a = cls.getInstance()
    a._fromFile(file,noVersion)
    return a

class DefinitionDataModel():
  def __init__(self):
    super(DefinitionDataModel, self).__init__()


  Definition = namedtuple('Definition',['text' , 'definition', 'timestamp' , 'dictionary','type','markups','hyperlink'])
  Definition.__new__.__defaults__ = (None,) * len(Definition._fields)

  @classmethod
  def getInstance(cls):
    obj = cls()
    obj.version      = 0.05
    obj.savedDefinitionsTable = pd.DataFrame()
    return obj

  def definitionCondition(self,d,*fields):
    return pandasCondition(self.savedDefinitionsTable,d,fields)

  def definitionExists(self,d):
    try:
      return self.definitionCondition(d).any()
    except KeyError:
      return False
    

  def addDefinition(self, record):
    if type(record) != DefinitionDataModel.Definition:
      raise ValueError('Expected' + str(Definition) + " ,got " + str(record.type))
    rSeries = pd.Series(record,record._fields)
    if record.timestamp is None:
      rSeries.timestamp = pd.Timestamp.now()
    self.savedDefinitionsTable = self.savedDefinitionsTable.append(rSeries, ignore_index = True)
  
  def getDefinitionsForWord(self,word):
    try:
      return self.savedDefinitionsTable[ self.savedDefinitionsTable.text == word]
    except AttributeError as err:
      if self.savedDefinitionsTable.empty:
        return self.savedDefinitionsTable
      else:
        raise err

    
  
  def getDefinition(self,query):
    condition = self.definitionCondition(query)
    return self.savedDefinitionsTable[condition]
  
  def replaceWord(self,oldWord,newWord):
    """ Replaces all instances of a word"""
    try:
      condition = (self.savedDefinitionsTable.text == oldWord)
    except AttributeError:
      return
    else:
      self.savedDefinitionsTable.loc[condition,"text"] = newWord

  def replaceDefinition(self,newDefinition , oldDefinition = None):
    if oldDefinition == None:
      self.savedDefinitionsTable.iloc[newDefinition.Index] = newDefinition[1:]
    else:
      condition = self.definitionCondition(oldDefinition , "text", "definition")
      self.savedDefinitionsTable.loc[condition] = newDefinition

  def removeDefinition(self,query):
    condition = self.definitionCondition(query)
    index = self.savedDefinitionsTable[condition].index
    self.savedDefinitionsTable.drop(index, inplace = True)

  def saveData(self,output):
    saveToPickle(self.version, output)
    #version 0.04
    saveToPickle(self.savedDefinitionsTable, output)

  def loadData(self,_input,noVersion):
    #The version variable is only for backwards compatibility with the class version.
    #It should not be stored to the object
    if not noVersion:
      version = loadFromPickle(_input)
      print("Loading DefinitionDataModel version " + str(version))
    else:
      version = 0.03
    #print("DefinitionsVersion :: " + str(version))
    #version 0.01
    if (version == 0.01):
      dictNames = loadFromPickle(_input)
      self.selectDictsFromNames(dictNames)
      dictUrls = loadFromPickle(_input)
      stripAccents = loadFromPickle(_input)
    #version 0.02
    if (version == 0.02):
      dictNames = loadFromPickle(_input)
      self.selectDictsFromNames(dictNames)
    if (version > 0.03):
      self.savedDefinitionsTable = loadFromPickle(_input)
    if (version <= 0.04):
      self.savedDefinitionsTable["markups"] = None
      self.savedDefinitionsTable["markups"] = self.savedDefinitionsTable["markups"].astype(object)

  def toFile(self,file):
    if isinstance(file,str):
      with open(file, 'wb') as output:
        self.saveData(output)
    else:
      self.saveData(file)

  def _fromFile(self,file,nv= False):
    if isinstance(file,str):
      with open(file, 'rb') as _input: 
        self.loadData(_input,nv)
    else:
      self.loadData(file,nv)
  
  @classmethod
  def fromFile(cls,file,nv = False):
    a = cls.getInstance()
    a._fromFile(file,nv)
    return a



#FIXME: Decorrelate the use of the word "Words" to mean indexes in tagTable (They don't have to be words, they could be imageIDs)
class TagDataModel():
  """ TagDataModel separates between taggings which refers to tags attributed to indexes and relations which refers
  to tags attributed to tags. Through the transitive property tags related to other tags also apply to indexes but there is no way to
  directly remove a tag related transitively to an index because by design this information is not captured"""

  Tag = namedtuple('Tag',['text' , 'tag', 'timestamp' , 'isAutoTag'])
  Tag.__new__.__defaults__ = (None,) * len(Tag._fields)
  

  def __init__(self , tagTable = None):  
    self.version = 0.01
    self.tagNodes = {}
    if tagTable is None:
      self.tagTable   = pd.DataFrame()
    else:
      self.tagTable   = tagTable

  def condition(self,t,*fields):
    return pandasCondition(self.tagTable,t,fields)

  def getTagsFromIndex(self,word):
    a =  self.tagTable[self.tagTable.text == word]
    a = list(a.tag)
    return a

  def getTags(self , includeAutoTags = True):
    # tagIndex = pd.pivot_table(self.tagTable,values='isAutoTag',index='tag',aggfunc=pd.Series.nunique).reset_index()
    table = self.tagTable
    if not includeAutoTags:
      table = table[table.isAutoTag != True]
    uniqueTagColumn = table.tag.unique()
    return list(uniqueTagColumn)

  def replaceTag(self,oldTag,newTag):
    #Replace it as a metatag
    if oldTag in self.tagNodes:
      node = self.tagNodes[oldTag]
      node.tag = newTag
    #Replace it as a tagging to words
    condition = self.tagTable.tag == oldTag
    print (self.tagTable[condition])
    self.tagTable.loc[condition,"tag"] = newTag

  def replaceWord(self,oldWord,newWord):
    condition = self.tagTable.text == oldWord
    self.tagTable.loc[condition,"text"] = newWord

  def addTagging(self,word,tags,autoTags=None):
    if len(tags) > 0:
      tagTableList = []
      ts = pd.Timestamp.now()
      for i,tag in enumerate(tags):
        if autoTags is not None and autoTags[i]:
          tagTableList.append({"tag":tag , "text" : word ,"timestamp":ts, "isAutoTag" : True})
        else:
          tagTableList.append({"tag":tag , "text" : word ,"timestamp":ts, "isAutoTag" : False})
      self.tagTable = self.tagTable.append(tagTableList, ignore_index = True)
      self.tagTable.drop_duplicates(inplace = True)

  def removeTagging(self,word,tags):
    if len(tags) > 0:
      tagTableList = []
      for tag in tags:
        self.removeSingleTagging(word,tag)

  def removeSingleTagging(self,word,tag):
    query = TagDataModel.Tag(text = word , tag = tag)
    condition = self.condition( query )
    index = self.tagTable[condition].index
    self.tagTable.drop(index, inplace = True)

  def replaceTagging(self,word,newTags,autoTags=None):
    oldTags = self.getTagsFromIndex(word)
    self.removeTagging(word,oldTags)
    self.addTagging(word,newTags,autoTags)

  def getIndexesFromTagList(self,tagList):
    #print(tagList)
    tableList = []
    for tag in tagList:
      tableList.append(self.tagTable[self.tagTable.tag == tag])
    tagIndexTable = pd.concat(tableList, axis=0).drop(["tag"] , axis = "columns")
    tagIndexTable = tagIndexTable.drop_duplicates()
    return tagIndexTable

  def deleteAutoTags(self):
    #delete auto meta tags
    metaTagsToBeRemoved = []
    for tag in self.tagNodes:
      if self.tagNodes[tag].isAutoTag:
        metaTagsToBeRemoved.append(tag)
    for tag in metaTagsToBeRemoved:
      self.removeMetaTag(tag)

    #delete auto tags
    condition = self.condition(TagDataModel.Tag(isAutoTag = True))
    index = self.tagTable[condition].index
    self.tagTable.drop(index, inplace = True)
  
  def saveData(self,output):
    #version 0.01
    #saveToPickle(self.tagTable, output)
    #version 0.02
    aCopy = copy.deepcopy(self)
    aCopy.deleteAutoTags()
    saveToPickle(aCopy.version, output)
    saveToPickle(aCopy.tagTable, output)
    saveToPickle(aCopy.tagNodes, output)


  def loadData(self,_input):
    #The version variable is only for backwards compatibility with the class version.
    #It should not be stores to the object
    #version 0.02
    version = loadFromPickle(_input)
    print("Loading TagDataModel version " + str(version))
    if version == 0.01:
      self.tagTable = loadFromPickle(_input)  
      self.tagNodes = loadFromPickle(_input)
    #self.tagTable = loadFromPickle(_input)

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

  class Node():
    #The tag works as a subject for its predicatives and as a predicative for its subjects
    def __init__(self,tag,isAutoTag=False):
      self.predicatives  = []
      self.subjects = []
      self.tag = tag
      self.isAutoTag = isAutoTag
    def __str__(self):
      return self.tag + " Pre: " + str(self.predicatives) + " | "
    def __repr__(self):
      return self.tag
  #This is not a symmetrical relation
  def tagToNode(self,tag , isAutoTag = False):
    if tag in self.tagNodes:
      node = self.tagNodes[tag]
    else:
      node = TagDataModel.Node(tag , isAutoTag)
    return node

  def getDirectParentTags(self,tag):
    node = self.tagToNode(tag)
    preds = node.predicatives
    metaTags = [n.tag for n in preds]
    return metaTags
  
  def getDirectChildTags(self,tag):
    node = self.tagToNode(tag)
    subjects = node.subjects
    metaTags = [n.tag for n in subjects]
    return metaTags

  def getAllParentTags(self,tag):
    node = self.tagToNode(tag)
    preds = self.getAllPredicatives(node)
    metaTags = [n.tag for n in preds]
    metaTags = list(set(metaTags))
    return metaTags

  def getAllChildTags(self,tag):
    node = self.tagToNode(tag)
    subjects = self.getAllSubjects(node)
    metaTags = [n.tag for n in subjects]
    metaTags = list(set(metaTags))
    return metaTags

  def getAllSubjects(self,node):
    subjectList = [] + node.subjects
    for n in node.subjects:
      if len(n.subjects) > 0:
        _subjectList = self.getAllSubjects(n)
        subjectList += _subjectList
    return subjectList

  def getAllPredicatives(self,node):
    predList = [] + node.predicatives
    for n in node.predicatives:
      if len(n.predicatives) > 0:
        _predList = self.getAllPredicatives(n)
        #print(_predList)
        predList += _predList
    return predList

  def checkForCycles(self,subNode, predNode):
    preds = self.getAllPredicatives(predNode)
    #print("sub :: " +str(subNode)+ " preds :: " + str(preds) )
    return subNode in preds
  def connected(self, subNode, predNode):
    return predNode in subNode.predicatives

  def addRelation(self,subject,pred, isAutoTag=False):
    if subject == pred:
      #print("Can't relate a tag to itself")
      return
    subNode = self.tagToNode(subject,isAutoTag)
    predNode = self.tagToNode(pred,isAutoTag)
    self.addNodeRelation(subNode,predNode)
      

  def addNodeRelation(self,subNode, predNode):
    if self.connected(subNode,predNode):
      #print("Already connected!") 
      return False
    #print("sNode :: " + str(subNode) + " pNode :: "+ str(predNode))  
    if self.checkForCycles(subNode,predNode):
      #print("Cycle found.")
      return False
    #Given there are not cycles we can now add the new tagNodes to the graph
    if subNode.tag not in self.tagNodes:
      self.tagNodes[subNode.tag] = subNode
    if predNode.tag not in self.tagNodes:
      self.tagNodes[predNode.tag] = predNode
    subNode.predicatives.append(predNode)
    predNode.subjects.append(subNode)
    return True

  def removeNodeRelation(self,subNode,predNode):
    subNode.predicatives.remove(predNode)
    predNode.subjects.remove(subNode)


  def removeMetaTag(self,tag):
    try:
      node = self.tagNodes[tag]
    except KeyError:
      return
    preds = node.predicatives.copy()
    for n in preds:
      self.removeNodeRelation(node,n)
    subjects = node.subjects.copy()
    for n in subjects:
      self.removeNodeRelation(n,node)
    del self.tagNodes[tag]