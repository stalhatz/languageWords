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
    
#FIXME: Sequential loading for suggested tags. Should be moved to threaded requests.
class OnlineDefinitionDataModel(QObject):
  dictNamesUpdated    = pyqtSignal(list)
  tagsUpdated         = pyqtSignal(list)
  definitionsUpdated  = pyqtSignal(list)
  showMessage         = pyqtSignal(str)
  
  def __init__(self):
    super(OnlineDefinitionDataModel, self).__init__()
  @classmethod

  def getInstance(cls,modulePath = "./dictionaries"):
    obj = cls()
    obj.version      = 0.02
    obj.enableCaching= True
    if obj.enableCaching:
      obj.requestCache  = pd.DataFrame(columns = ["html" , "timestamp"])
    obj.session      = FuturesSession(max_workers=1)
    obj.lastRequest  = None
    obj.url          = None
    obj.findModules(modulePath)
    obj.selectedDicts = {}
    return obj

  def selectDictsFromNames(self,dictNames):
    #We will silently ignore all names not corresponding to available dictionaries
    self.selectedDicts = {}
    for name in dictNames:
      if name in self.availableDicts:
        self.selectedDicts[name] = self.availableDicts[name]
    self.updateDictNames()

  def findModules(self,directory= None,packageName = "dictionaries"):
    self.availableDicts = {}
    if directory is not None:
      sys.path.insert(0,str(directory))
    package  = importlib.import_module(packageName)
    prefix = package.__name__ + "."
    for importer, modname, ispkg in pkgutil.iter_modules(package.__path__, prefix):
      #print ("Found submodule %s (is a package: %s)" % (modname, ispkg))
      dictionary = import_module(modname)
      self.availableDicts[dictionary.name] = dictionary
    return self.availableDicts

  def getAvailableLanguages(self):
    return list ( set( [l for d in self.availableDicts.values() for l in d.languages] ) )

  def getAvailableDicts(self):
    return list(self.availableDicts.values())

  def getSelectedDicts(self):
    return list(self.selectedDicts.values())

  def getTagsFromHtml(self,dictName, html):
    tagList = []
    if hasattr(self.selectedDicts[dictName], 'getTagsFromHtml'):
      tagsList        = self.selectedDicts[dictName].getTagsFromHtml(html,self.language)
    return tagsList

  def getDefinitionsFromHtml(self,dictName, html):
    definitionsList = self.selectedDicts[dictName].getDefinitionsFromHtml(html,self.language)
    return definitionsList

  def updateDictNames(self):
    self.dictNamesUpdated.emit(list(self.selectedDicts.keys()))
  
  def getDictNames(self):
    return list(self.selectedDicts.keys())

  def createUrl(self,word,dictName):
    url = self.selectedDicts[dictName].createUrl(word,self.language)
    return url

  def loadDefinition(self,word,dictName):
    self.definitionsList = []
    self.load(self, word, dictName,isDefinition = True , _async = True)

  def loadTags(self, word):
    for dictName in self.selectedDicts:
      if hasattr(self.selectedDicts[dictName], 'getTagsFromHtml'):
        self.load(word,dictName,isDefinition = False , _async = False) 

  def load(self,word, dictName,isDefinition=False,_async= False):
    url       = self.createUrl(word,dictName)  
    if self.enableCaching:
      try:
        html = self.requestCache.loc[url,:].html
        self.showMessage.emit("Loaded " + url + " from cached copy")
        self.parseHtml(html,dictName,isDefinition)
        return
      except KeyError:
        pass
    if _async:
      self.loadAsync(url,dictName,isDefinition)
    else:
      self.loadSequential(url,dictName,isDefinition)

  def loadSequential(self, url,dictName,isDefinition=False):
    response  = requests.get(url)
    self.handleRequest(response,url,dictName,isDefinition)

  def loadAsync(self, url,dictName,isDefinition=True):
    self.url = url
    future = self.session.get(url)
    future.add_done_callback(partial(self._load,url,dictName,isDefinition))
    self.lastRequest = future
    self.showMessage.emit("Loading from " + url)
  
  #This is run by a thread other the main one. Though interpreter lock is in place, we should make sure there are no race conditions...
  def _load(self,url,dictName,isDefinition,future):
    if url != self.url:
      future.cancel() #Should cancel itself when issuing the next request as max_workers = 1
      return
    request = future.result()
    self.handleRequest(request,url,dictName,isDefinition)

  def handleRequest(self,request,url,dictName,isDefinition=True):
    if request.status_code > 200:
      self.showMessage.emit("Error while loading from " + url + " Code :: " + str(request.status_code))
    else:
      html =  request.text
      if self.enableCaching:
        try:
          html = self.requestCache.loc[url,:].html
        except KeyError:
          newRecord         = pd.Series({"html":html , "timestamp":pd.Timestamp.now()}, name = url)
          self.requestCache = self.requestCache.append(newRecord)
      self.showMessage.emit("Finished loading from " + url)
      self.parseHtml(html,dictName,isDefinition)
  
  def parseHtml(self,html,dictName,isDefinition):
    if isDefinition:
      self.definitionsList = self.getDefinitionsFromHtml(dictName, html)
      self.definitionsUpdated.emit(self.definitionsList)
    else: #Update tags
      self.tagsList = self.getTagsFromHtml(dictName,html)
      if self.tagsList:
        self.tagsUpdated.emit(self.tagsList)

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
    self.selectDictsFromNames(dictNames)
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

  @classmethod
  def getInstance(cls, columns = ["text" , "definition", "timestamp" , "dictionary","type"]):
    obj = cls()
    obj.version      = 0.04
    obj.savedDefinitionsTable = pd.DataFrame(columns = columns)
    return obj

  def definitionCondition(self,word,definition):
    return (self.savedDefinitionsTable.text == word) & (self.savedDefinitionsTable.definition == definition)
  def definitionExists(self,word,definition):
    return self.definitionCondition(word,definition).any()

  def addDefinition(self, word, definition, dictionary,_type):
    record = {"text" : word ,"definition":definition, "timestamp": pd.Timestamp.now() , "dictionary": dictionary , "type":_type}
    self.savedDefinitionsTable = self.savedDefinitionsTable.append(record, ignore_index = True)
  
  def getSavedDefinitions(self,word):
    return self.savedDefinitionsTable[ self.savedDefinitionsTable.text == word]
  
  def getSavedDefinition(self,word,definition):
    condition = self.definitionCondition(word,definition)
    return self.savedDefinitionsTable[condition]

  def replaceDefinition(self,word,oldDefinition,newDefinition):
    condition = self.definitionCondition(word,oldDefinition)
    self.savedDefinitionsTable.loc[condition,"definition"] = newDefinition
    print(self.savedDefinitionsTable[condition])

  def removeDefinition(self,word,definition):
    condition = self.definitionCondition(word,definition)
    index = self.savedDefinitionsTable[condition].index
    self.savedDefinitionsTable.drop(index, inplace = True)

  def saveData(self,output):
    saveToPickle(self.version, output)
    #version 0.04
    saveToPickle(self.savedDefinitionsTable, output)

  def loadData(self,_input,noVersion):
    #The version variable is only for backwards compatibility with the class version.
    #It should not be stores to the object
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
    if (version == 0.03):
      self.savedDefinitionsTable = loadFromPickle(_input)
    if (version == 0.04):
      self.savedDefinitionsTable = loadFromPickle(_input)

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

  def __init__(self , tagTable = None):
    self.version = 0.01
    self.tagNodes = {}
    if tagTable is None:
      self.tagTable   = pd.DataFrame(columns = ["text" , "tag"])
    else:
      self.tagTable   = tagTable

  def getTagsFromIndex(self,word):
    a =  self.tagTable[self.tagTable.text == word]
    a = list(a.tag)
    return a

  def getTags(self):
    tagIndex = pd.pivot_table(self.tagTable,values='text',index='tag',aggfunc=pd.Series.nunique).reset_index()
    return list(tagIndex['tag'])

  def replaceTag(self,oldTag,newTag):
    #Replace it as a metatag
    if oldTag in self.tagNodes:
      node = self.tagNodes[oldTag]
      node.tag = newTag
    #Replace it as a tagging to words
    condition = self.tagTable.tag == oldTag
    print (self.tagTable[condition])
    self.tagTable.loc[condition,"tag"] = newTag

  def addTagging(self,word,tags):
    if len(tags) > 0:
      tagTableList = []
      for tag in tags:
        tagTableList.append({"tag":tag , "text" : word})
      self.tagTable = self.tagTable.append(tagTableList, ignore_index = True)
      self.tagTable.drop_duplicates(inplace = True)

  def removeTagging(self,word,tags):
    if len(tags) > 0:
      tagTableList = []
      for tag in tags:
        tagTableList.append({"tag":tag , "text" : word})
      self.tagTable = self.tagTable.append(tagTableList, ignore_index = True)
      self.tagTable.drop_duplicates(keep=False, inplace = True)

  def getIndexesFromTagList(self,tagList):
    #print(tagList)
    tableList = []
    for tag in tagList:
      tableList.append(self.tagTable[self.tagTable.tag == tag])
    tagIndexTable = pd.concat(tableList, axis=0).drop(["tag"] , axis = "columns")
    tagIndexTable = tagIndexTable.drop_duplicates()
    return tagIndexTable

  def saveData(self,output):
    #version 0.01
    #saveToPickle(self.tagTable, output)
    #version 0.02
    saveToPickle(self.version, output)
    saveToPickle(self.tagTable, output)
    saveToPickle(self.tagNodes, output)


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
    def __init__(self,tag):
      self.predicatives  = []
      self.subjects = []
      self.tag = tag
    def __str__(self):
      return self.tag + " Pre: " + str(self.predicatives) + " | "
    def __repr__(self):
      return self.tag
  #This is not a symmetrical relation
  def tagToNode(self,tag):
    if tag in self.tagNodes:
      node = self.tagNodes[tag]
    else:
      node = TagDataModel.Node(tag)
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

  def addRelation(self,subject,pred):
    if subject == pred:
      #print("Can't relate a tag to itself")
      return
    subNode = self.tagToNode(subject)
    predNode = self.tagToNode(pred) 
    if self.connected(subNode,predNode):
      #print("Already connected!") 
      return
    #print("sNode :: " + str(subNode) + " pNode :: "+ str(predNode))  
    if self.checkForCycles(subNode,predNode):
      #print("Cycle found.")
      return
    #Given there are not cycles we can now add the new tagNodes to the graph
    if subject not in self.tagNodes:
      self.tagNodes[subject] = subNode
    if pred not in self.tagNodes:
      self.tagNodes[pred] = predNode
    subNode.predicatives.append(predNode)
    predNode.subjects.append(subNode)

  def removeRelation(self,subject,pred):
    subNode = self.tagNodes[subject]
    predNode = self.tagNodes[pred]
    subNode.predicatives.remove(predNode)
    predNode.subjects.remove(subNode)
