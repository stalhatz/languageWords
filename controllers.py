from PyQt5.QtGui import (QFont,QIcon)
from PyQt5.QtCore import (QVariant, Qt, pyqtSignal, QUrl,QItemSelectionModel)
from PyQt5.QtCore import (QAbstractListModel, QModelIndex, QStringListModel)
from PyQt5.QtNetwork import (QNetworkAccessManager, QNetworkRequest, QNetworkReply)

import pandas as pd

from dataModels import DefinitionDataModel
import unidecode
import textwrap
from collections import Counter
from operator import attrgetter
from collections import namedtuple

# TODO : [FEATURE] Animation while loading using QMovie
# TODO : [FEATURE] Enable help through tooltip messages
# (Racing condition? Is the server blocking us?).
# QNetworkAccessManager (which would be the easiest way to do this) not working due to QTBUG-68156
# Should use requests-futures

#FIXME: Find a more memory allocation/copies way of inserting multiple elements into a string
#FIXME: Optimize markup format so the intermediate representation will not be necessary
def htmlFromMarkups(text,markups):
  if markups is None : return text
  singleMarkups = []
  for markup in markups:
    if markup.tagType == "bold":
      tag = "b"
    initTag = "<" + tag + ">"    
    endTag = "</" + tag + ">"
    singleMarkups.append( (markup.start , initTag) )
    singleMarkups.append( (markup.stop , endTag) )
  
  sorted(singleMarkups, key = lambda x: x[0])

  icl = 0 #Inserted Characters Length
  for markup in singleMarkups:
    pos = markup[0] + icl
    text = text[:pos] + markup[1] + text[pos:]
    icl += len(markup[1])
  return text

#TODO: Merge with DefinitionController
class SavedDefinitionsController(QAbstractListModel):
  DataRole = Qt.UserRole + 1
  def __init__(self,defModel):
    super(SavedDefinitionsController,self).__init__()
    self.defModel = defModel
    self.definitionsList  = []

  def rowCount(self, modelIndex):
    return len(self.definitionsList)

  def getDefinition(self,index):
    if not index.isValid() or not (0<=index.row()<len(self.definitionsList)):  
      raise IndexError("Invalid index or index out of bounds")
    if isinstance(self.definitionsList[index.row()] , str):
      raise IndexError("Data in row " + str(index.row()) + " were requested but contained a label : " + self.definitionsList[index.row()])
    else:
      return self.definitionsList[index.row()]
      
  def data(self, index, role):
    if not index.isValid() or not (0<=index.row()<len(self.definitionsList)):  
      return QVariant()
    if role==Qt.DisplayRole:
      if isinstance(self.definitionsList[index.row()] , str):
        return self.definitionsList[index.row()].upper()
      else:
        return self.html[index.row()]
    if role==Qt.EditRole:
      if not isinstance(self.definitionsList[index.row()] , str):
        a  = self.definitionsList[index.row()].definition
        return a
    if role==Qt.ToolTipRole:
      if not isinstance(self.definitionsList[index.row()] , str):
        a  = self.definitionsList[index.row()]
        wrapper = textwrap.TextWrapper()
        wrapper.width = 80
        return wrapper.fill(str(a))
    if role==self.DataRole:
      if not isinstance(self.definitionsList[index.row()] , str):
        pandas = self.definitionsList[index.row()]
        return pandas

  def flags(self,index):
    flags = super(SavedDefinitionsController,self).flags(index)
    if not index.isValid() or not (0<=index.row()<len(self.definitionsList)):  
      return flags
    
    if isinstance(self.definitionsList[index.row()] , str):
      if flags & Qt.ItemIsEnabled != (flags & 0) : # If is enabled
        flags = flags ^ Qt.ItemIsEnabled
      if flags & Qt.ItemIsSelectable != (flags & 0): # If is selectable
        flags = flags ^ Qt.ItemIsSelectable
    else:
      if flags & Qt.ItemIsEditable == (flags & 0): # If is not editable
        flags = flags ^ Qt.ItemIsEditable
    return flags

  def updateOnWord(self,word):
    self.currentElement = word
    self.layoutAboutToBeChanged.emit()
    self.definitionsTable = self.defModel.getDefinitionsForWord(word).copy(True)
    self.html = []
    try:
      self.definitionsTable.type = self.definitionsTable.type.str.lower()
      self.definitionsTable.sort_values(by=["type"] , inplace = True)
    except (KeyError, AttributeError):
      self.layoutChanged.emit()
      return
    self.definitionsList  = [x for x in self.definitionsTable.itertuples()]
    self.sortDefList()
    for x in self.definitionsList:
      if isinstance(x , str):
        self.html.append(None)
      else:
        html = htmlFromMarkups(x.definition , x.markups[0])
        html = '<br />'.join(html.splitlines())
        self.html.append(html)
    self.layoutChanged.emit()

  def sortDefList(self):
    if len(self.definitionsList) == 0:
      return
    positions = []
    numTypes = 1
    positions.append((0,self.definitionsList[0].type))
    for i,element in enumerate(self.definitionsList):
      if i>0:
        if element.type.lower() != self.definitionsList[i-1].type.lower():
          positions.append((i+numTypes,element.type))
          numTypes+=1
    for position in positions:
      self.definitionsList.insert(position[0] , position[1])
  
  def addTmpDefinition(self):
    self.layoutAboutToBeChanged.emit()
    Definition = namedtuple('definition', ('definition', 'type'))
    self.definitionsList.append(Definition("","_newUserDefinition"))
    self.html.append("")
    #self.sortDefList()
    self.layoutChanged.emit()
    return self.createIndex(len(self.definitionsList) - 1,0)
  
  def deleteTmpDefinition(self):
    for d in self.definitionsList:
      if not isinstance(d , str):
        if d.type == "_newUserDefinition":
          self.definitionsList.remove(d)
          break


class DefinitionController(QAbstractListModel):
  DataRole = Qt.UserRole
  def __init__(self,defModel):
    super(DefinitionController,self).__init__()
    self.definitionsList  = []
    self.views            = []
  def update(self,definitionsList):
    self.layoutAboutToBeChanged.emit()
    self.definitionsList = definitionsList
    self.sortDefList()
    self.layoutChanged.emit()
  def rowCount(self, modelIndex):
    return len(self.definitionsList)
  def data(self, index, role):
    if not index.isValid() or not (0<=index.row()<len(self.definitionsList)):  return QVariant()
    if role==Qt.DisplayRole:
      if isinstance(self.definitionsList[index.row()] , str):
        return self.definitionsList[index.row()].upper()
      else:
        html = htmlFromMarkups( self.definitionsList[index.row()].definition, self.definitionsList[index.row()].markups) 
        html = '<br />'.join(html.splitlines())
        return html
    if role==self.DataRole:
      return self.definitionsList[index.row()]

  def getDefinition(self,index):
    if not index.isValid() or not (0<=index.row()<len(self.definitionsList)):  
      raise IndexError("Invalid index or index out of range")
    if isinstance(self.definitionsList[index.row()] , str):
      raise IndexError("Data where requested for a decorative index")
    else:
      return self.definitionsList[index.row()]
  def flags(self,index):
    flags = super(DefinitionController,self).flags(index)
    if not index.isValid() or not (0<=index.row()<len(self.definitionsList)):  
      return flags
    if isinstance(self.definitionsList[index.row()] , str):
      if flags & Qt.ItemIsEnabled != 0: # If is enabled
        flags = flags ^ Qt.ItemIsEnabled
      if flags & Qt.ItemIsSelectable != 0: # If is selectable
        flags = flags ^ Qt.ItemIsSelectable
    return flags
  def sortDefList(self):
    if len(self.definitionsList) > 0: 
      self.definitionsList.sort(key=attrgetter('type'))
      positions = []
      numTypes = 1
      positions.append((0,self.definitionsList[0].type))
      for i,element in enumerate(self.definitionsList):
        if i>0:
          if element.type != self.definitionsList[i-1].type:
            positions.append((i+numTypes,element.type))
            numTypes+=1
      for position in positions:
        self.definitionsList.insert(position[0] , position[1])
  def addView(self,view):
    self.views.append(view)
    

# TODO: [FEATURE] [LOW PRIORITY] unidecode filter and pandas Series to match string with accents / no accents
# TODO: [FEATURE] [LOW PRIORITY] use > = < filters to filter tags with certain number of corresponding words
class TagController(QAbstractListModel):
  DataRole = Qt.UserRole
  def __init__(self,tagModel,isAutoTag,stripAutoTag):
    super(TagController,self).__init__()
    self.tagModel = tagModel
    self.isAutoTag    = isAutoTag
    self.stripAutoTag = stripAutoTag
    if self.tagModel.tagTable.empty:
      self.tagIndex  = pd.DataFrame(columns=["tag","text"])
    else:
      self.updateTags()
  def rowCount(self, modelIndex):
    return len(self.tagIndex.index)
  def data(self, index, role):
    if not index.isValid() or not (0<=index.row()<len(self.tagIndex.index)):  
      return QVariant()
    if role== Qt.DecorationRole:
      tagName = self.getTag(index)
      if (self.isAutoTag(tagName)):
        return QIcon("sample.svg")
    if role == Qt.FontRole:
      tagName = self.getTag(index)
      if (self.isAutoTag(tagName)):
        font = QFont();
        font.setBold(True);
        return font;
    if role==Qt.DisplayRole: 
      tagName = self.getTag(index)
      if (self.isAutoTag(tagName)):
        tagName = self.stripAutoTag(tagName)
      return (tagName + " ("+str(self.getTagCount(index))+")").capitalize()
    if role==Qt.EditRole:
      return self.getTag(index)
    if role==self.DataRole:
      return self.getTag(index)
    if role==Qt.ToolTipRole:
      a  = self.tagIndex.iloc[index.row(),:]
      wrapper = textwrap.TextWrapper()
      wrapper.width = 80
      return wrapper.fill(str(a))

  def getTag(self,index):
    if isinstance(index,int):
      ind = index  
    else:
      ind = index.row()
    return str(self.tagIndex.iloc[ind,0])  
  def getTagCount(self,index):
    return self.tagIndex.iloc[index.row(),1]

  def updateTags(self):
    self.layoutAboutToBeChanged.emit()
    self.tagIndex = pd.pivot_table(self.tagModel.tagTable,values='text',index='tag',aggfunc=pd.Series.nunique).reset_index()
    self.tagIndex.rename(columns={"text":"indexCount"},inplace = True)
    newTagsList = []
    for tag in self.tagModel.tagNodes:
      tagList = self.tagModel.getAllChildTags(tag)
      if len(tagList) > 0:
        tagList.append(tag)
        indCount = len( self.tagModel.getIndexesFromTagList(tagList).index )
        newTagsList.append({"tag":tag,"indexCount":indCount})
    if len(newTagsList) > 0:
      self.tagIndex = self.tagIndex.append(newTagsList,ignore_index = True)
    self.layoutChanged.emit()

  def getTagIndex(self,tag):
    condition = self.tagIndex.tag == tag
    result    = self.tagIndex[condition]
    if result.empty:
      return QModelIndex()
    else:
      index =  int( result.index.values[0] )
      return self.createIndex(index,0)
  
  def flags(self,index):
    flags = super(TagController,self).flags(index)
    if index.row() < len(self.tagIndex.index):
      if flags & Qt.ItemIsEditable == (flags & 0): # If is not editable
        flags = flags ^ Qt.ItemIsEditable
    return flags
#FIXME: Load word definition when shown on screen not only when selected
class WordController(QAbstractListModel):
  loadDefinition    = pyqtSignal(str, str, bool)
  DataRole = Qt.UserRole
  def __init__(self, wordModel ,tagModel):
    super(WordController,self).__init__()
    self.wordModel = wordModel
    self.tagModel = tagModel
    self.df_image = self.wordModel.wordTable
    self.dict = None
    self.url = None
    self.externalLoading = False
    self.viewList = []

  def addView(self,view):
    self.viewList.append(view)
  def rowCount(self, modelIndex):
    return len(self.df_image.index)
  def data(self, index, role):
    if not index.isValid() or not (0<=index.row()<len(self.df_image.index)):
      return QVariant()
    if role==Qt.DisplayRole:
      return str(self.df_image.iloc[index.row(),0]).capitalize()
    if role==Qt.EditRole:
      return str(self.df_image.iloc[index.row(),0])
    if role==self.DataRole:
      return str(self.df_image.iloc[index.row(),0])
    if role==Qt.ToolTipRole:
      a  = self.df_image.iloc[index.row()]
      wrapper = textwrap.TextWrapper()
      wrapper.width = 80
      return wrapper.fill(str(a))
  def updateOnTag(self,tag):
    self.layoutAboutToBeChanged.emit()
    if tag == None:
      self.df_image = self.wordModel.wordTable
    else:
      tagList = self.tagModel.getAllChildTags(tag)
      tagList.append(tag)
      tagIndexTable = self.tagModel.getIndexesFromTagList(tagList)
      self.df_image = pd.merge(self.wordModel.wordTable, tagIndexTable[["text"]], on=['text','text'])
    self.layoutChanged.emit()

  def getWordIndex(self,word):
    condition = self.df_image.text == word
    result    = self.df_image[condition]
    if result.empty:
      return QModelIndex()
    else:
      index =  int( result.index.values[0] )
      return self.createIndex(index,0)

  def flags(self,index):
    flags = super(WordController,self).flags(index)
    if index.row() <     len(self.df_image.index):
      if flags & Qt.ItemIsEditable == (flags & 0): # If is not editable
        flags = flags ^ Qt.ItemIsEditable
    return flags


#TODO: Augment internal list with non-selectable elements ("INHERITED TAGS") to simplify indexing
class ElementTagController(QAbstractListModel):
  dataChanged       = pyqtSignal(QModelIndex,QModelIndex)
  def __init__(self,tagModel):
    super(ElementTagController,self).__init__()
    self.tagModel = tagModel
    self.currentIndex = -1
    self.tagList  = []
    self.directTagList = []
    self.currentElement = None
    self.spliterText = " INHERITED TAGS"
  def rowCount(self, modelIndex):
    return self.dataSize()
  def dataSize(self):
    if len(self.tagList) - len(self.directTagList) > 0:
      return len(self.tagList) + 1 # + spliterText
    else:
      return len(self.tagList)

  def data(self, index, role):
    if not index.isValid() or not (0<=index.row()<self.dataSize()):
      return QVariant()
    if role==Qt.DisplayRole:
      if index.row() < len(self.directTagList):
        return str(self.tagList[index.row()])
      elif index.row() == len(self.directTagList):
        return self.spliterText
      else:
        return str(self.tagList[index.row() - 1])
      
  def selected(self, index , prevIndex):
    self.currentIndex = index.row()

  def updateOnTag(self,tag):
    self.updatesOnTag = True
    self.currentElement = tag
    self.layoutAboutToBeChanged.emit()
    if tag is None:
      self.tagList = []
      self.directTagList = []
    else:
      self.tagList = self.tagModel.getAllParentTags(tag)
      self.directTagList = self.tagModel.getDirectParentTags(tag)
      self.orderTagLists()
    self.layoutChanged.emit()
    
  def updateOnWord(self,word):
    self.updatesOnTag = False
    self.currentElement = word
    self.layoutAboutToBeChanged.emit()
    if word is None:
      self.tagList = []
      self.directTagList = []
    else:
      self.directTagList = self.tagModel.getTagsFromIndex(word)
      self.tagList = []
      for tag in self.directTagList:
        self.tagList += self.tagModel.getAllParentTags(tag)
      self.tagList = list(set(self.tagList))
      self.orderTagLists()
    self.layoutChanged.emit()
  def clear(self):
    self.layoutAboutToBeChanged.emit()
    self.tagList = []
    self.layoutChanged.emit()

  def update(self):
    if self.updatesOnTag:
      self.updateOnTag(self.currentElement)
    else:
      self.updateOnWord(self.currentElement)

  def orderTagLists(self):
    self.tagList = [x for x in self.tagList if x not in self.directTagList]
    self.tagList = self.directTagList + self.tagList

  def flags(self,index):
    flags = super(ElementTagController,self).flags(index)
    if index.row() >= len(self.directTagList):
      if flags & Qt.ItemIsEnabled != 0: # If is enabled
        flags = flags ^ Qt.ItemIsEnabled
      if flags & Qt.ItemIsSelectable != 0: # If is selectable
        flags = flags ^ Qt.ItemIsSelectable
    return flags
  
  def __len__(self):
    return len(self.tagList)

