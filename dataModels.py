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

class WordDataModel(QObject):
  def __init__(self, wordTable = None):
    super(WordDataModel, self).__init__()
    self.version = 0.01
    if wordTable is None:
      self.wordTable  = pd.DataFrame(columns = ["text" , "hyperlink"])
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
    self.wordTable = self.wordTable.append({"text" : word}, ignore_index = True)

  def removeWord(self,word):
    self.wordTable.set_index("text",inplace = True)
    self.wordTable.drop(word , inplace = True)
    self.wordTable.reset_index(inplace = True)
    

class DefinitionDataModel(QObject):
  dictNamesUpdated    = pyqtSignal(list)
  definitionsUpdated  = pyqtSignal(list)
  externalPageLoad    = pyqtSignal(QUrl)
  showMessage         = pyqtSignal(str)
  def __init__(self, dictNames = []):
    super(DefinitionDataModel, self).__init__()
    self.version      = 0.02
    self.session      = FuturesSession(max_workers=1)
    self.lastRequest  = None
    self.url          = None
    self.availableDicts = self.findModules("./dictionaries")
    self.selectDictsFromNames(dictNames)

  def selectDictsFromNames(self,dictNames):
    #We will silently ignore all names not corresponding to available dictionaries
    self.selectedDicts = {}
    for name in dictNames:
      if name in self.availableDicts:
        self.selectedDicts[name] = self.availableDicts[name]
    self.updateDictNames()

  def findModules(self,directory):
    availableDicts = {}
    package = dictionaries
    prefix = package.__name__ + "."
    for importer, modname, ispkg in pkgutil.iter_modules(package.__path__, prefix):
      #print ("Found submodule %s (is a package: %s)" % (modname, ispkg))
      dictionary = import_module(modname)
      availableDicts[dictionary.name] = dictionary
    return availableDicts

  def getAvailableLanguages(self):
    return list ( set( [l for d in self.availableDicts.values() for l in d.languages] ) )

  def getAvailableDicts(self):
    return list(self.availableDicts.values())

  def getSelectedDicts(self):
    return list(self.selectedDicts.values())

  def getDefinitionsFromHtml(self,dictName, html):
    definitionsList = self.selectedDicts[dictName].getDefinitionsFromHtml(html)
    return definitionsList

  def updateDictNames(self):
    self.dictNamesUpdated.emit(list(self.selectedDicts.keys()))
  
  def getDictNames(self):
    return list(self.selectedDicts.keys())

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
    saveToPickle(self.getDictNames(), output)
    

  def loadData(self,_input):
    #The version variable is only for backwards compatibility with the class version.
    #It should not be stores to the object
    version = loadFromPickle(_input)
    print("DefinitionsVersion :: " + str(version))
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

  def addTagging(self,word,tags):
    if len(tags) > 0:
      tagTableList = []
      for tag in tags:
        tagTableList.append({"tag":tag , "text" : word})
      self.tagTable = self.tagTable.append(tagTableList, ignore_index = True)

  def removeTagging(self,word,tags):
    if len(tags) > 0:
      tagTableList = []
      for tag in tags:
        tagTableList.append({"tag":tag , "text" : word})
      self.tagTable = self.tagTable.append(tagTableList, ignore_index = True)
      self.tagTable.drop_duplicates(keep=False, inplace = True)

  def getIndexesFromTagList(self,tagList):
    print(tagList)
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
  
  def getAllChildTags(self,tag):
    node = self.tagToNode(tag)
    preds = self.getAllSubjects(node)
    metaTags = [n.tag for n in preds]
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

import random
#Test TagDataModel
if __name__ == "__main__":
  random.seed(1)
  aModel = TagDataModel()
  #tags = list("azertyuiopqsdfghjklmwxcvbn")
  tags = list("abcdefg")
  for i in range(10):
    a = random.randint(0,len(tags)-1)
    b = random.randint(0,len(tags)-1)
    aTag = tags[a]
    bTag = tags[b]
    print("Adding relation :: " + bTag +" -> " + aTag )
    aModel.addRelation(aTag,bTag)
    print(i)
  for n in aModel.tagNodes:
    print (aModel.tagNodes[n])