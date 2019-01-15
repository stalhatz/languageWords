#We should create classes for offline and online dictionaries (subclasses of the same baseclass)
#For the time being it will just be functions
import unidecode
from bs4 import BeautifulSoup

from PyQt5.QtCore import (QObject)
import pandas as pd
import pickle

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
  def __init__(self, dictionaryNames, dictionaryUrls, stripAccents):
    super(DefinitionDataModel, self).__init__()
    self.dictNames    = dictionaryNames
    self.dictUrls     = dictionaryUrls
    self.stripAccents = stripAccents

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
  def createUrl(self, dictName, word):
    index = self.dictNames.index(dictName)
    url = self.dictUrls[index]
    if self.stripAccents[index]:
      word = unidecode.unidecode(word)
    return url + word