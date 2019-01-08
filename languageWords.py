import time
import os
import subprocess
import datetime as dt
import pandas as pd
import pickle
import argparse
import sys

from PyQt5.QtWidgets import (QApplication,QWidget,QMainWindow)
from PyQt5.QtCore import (QUrl,QVariant,Qt,pyqtSignal)
from PyQt5.QtCore import (QAbstractListModel,QModelIndex,QStringListModel)

from ui_mainwindow import Ui_MainWindow

# class TextElement:
#   def __init__(self, text , hyperlink = None , tag = None):
#     self.text = text
#     self.link = "" 
#     self.date = dt.datetime.today()
#     self.tags = []
#     self.hyperlink = hyperlink
#     self.spellChecked = False
#   def __repr__(self):
#     return self.text
#   def __str__(self):
#     return self.text
    

# def runCommand(command, args):
#   global useGUI
#   if useGUI:
#     a = subprocess.run([command] +  args, stdout=subprocess.PIPE)
#     b = a.stdout.decode('utf-8')
#     return b
  

# def getQtTextInput(taskList, labelText):
#   app = QApplication([])
#   a = QInputDialog()
#   a.setInputMode(0)
#   a.setLabelText(labelText)
#   b = a.findChild(QLineEdit)
#   c = QCompleter(taskList)
#   print("Tasklist ::" + str(taskList))
#   c.setCompletionMode(QCompleter.UnfilteredPopupCompletion)
#   b.setCompleter(c)
#   ret = a.exec_()
#   if ret == 0:
#     return None
#   else:
#     return a.textValue()

# def showDialog(command, _title, taskList = None):
#   if command == "input":
#     return getQtTextInput(taskList, _title)
#   elif command == "notification":
#     title = ["--title" , _title]
#     text = [_title]
#     args =  title + ["--passivepopup"] + text
#     runCommand("kdialog", args)


# self.webView = QtWebEngineWidgets.QWebEngineView(self.centralwidget)
# from PyQt5 import QtWebEngineWidgets   

import requests
from bs4 import BeautifulSoup



def saveToPickle(a , filename):
  with open(filename, 'wb') as output:
    pickle.dump(a, output, pickle.HIGHEST_PROTOCOL)
  
def loadFromPickle(filename):
  with open(filename, 'rb') as input:
    a = pickle.load(input)
  return a

def createDFFromDict(dictWords):
  words["text"] = []
  words["hyperlink"] = []
  words["tag"] = []
  for key in dictWords:
    words["text"].append(key)
    words["hyperlink"].append(dictWords[key][0])
    words["tag"].append(dictWords[key][1])
  return pd.DataFrame.from_dict(words)

class DictWebList(QAbstractListModel):
  dataChanged = pyqtSignal()
  def __init__(self):
    super(DictWebList,self).__init__()
    self.definitionsList = []
  def load(self,url):
    self.definitionsList = []
    html =  requests.get(url.toString()).text
    s = BeautifulSoup(html,"html.parser")
    for element in s.select("ol > li"):
      self.definitionsList.append(element.text.split("\n")[0])
    print(self.definitionsList)
    self.dataChanged.emit()
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


class PandasWordList(QAbstractListModel):
  dataChanged = pyqtSignal()
  pageLoad    = pyqtSignal(QUrl)
  def __init__(self, df ,webview):
    super(PandasWordList,self).__init__()
    self.df = df
    self.df_image = df
    self.webView = webview
    self.dict = "wiktionary"
  def rowCount(self, modelIndex):
    return len(self.df_image)
  def data(self, index, role):
    if not index.isValid() or not (0<=index.row()<len(self.df_image)):
      return QVariant()
    if role==Qt.DisplayRole:
      return str(self.df_image.iloc[index.row(),0])
  def selected(self, index , prevIndex):
    if self.dict == "wiktionary":
      url = QUrl("https://fr.wiktionary.org/wiki/" + str(self.df_image.iloc[index.row(),0]) )
    elif self.dict == "larousse":
      url = QUrl("https://www.larousse.fr/dictionnaires/francais/" + str(self.df_image.iloc[index.row(),0]) )
    #self.webView.load(url) 
    self.pageLoad.emit(url)
  def updateWords(self,tag):
    self.df_image = self.df[self.df['tag'] == tag]
    self.dataChanged.emit()
  def updateDict(self,dictName):
    self.dict = dictName
words = {}

#def handleTabWidgetSignals():


if __name__ == "__main__":
  parser = argparse.ArgumentParser(description='Process some integers.')
  parser.add_argument('-l', nargs='?', const='dictWords.pd.pkl', default=None)
  parser.add_argument('-s', nargs='?', const='dictWords.pkl', default=None)
  args = parser.parse_args()
  
  dictWords = {}

  if args.s is None and args.l is not None:
    args.s = args.l
  
  if args.l is not None:
    try:
      dictWords = loadFromPickle(args.l)
    except:
      print("Could not load from file")
  app = QApplication([])
  
  window = QMainWindow()
  ui = Ui_MainWindow()
  ui.setupUi(window)
  ui.dictSelect.insertItems(0,["wiktionary", "larousse"])
  pwl = PandasWordList(dictWords,ui.webView)
  ptl = PandasTagList(dictWords)
  dwl = DictWebList()
  #Set signals/slots
  ui.dictListView.setModel(dwl)
  ui.tagview.setModel(ptl)
  ui.tagview.selectionModel().currentChanged.connect(ptl.selected)
  ui.wordview.setModel(pwl)
  ui.wordview.selectionModel().currentChanged.connect(pwl.selected)
  ui.dictSelect.currentTextChanged.connect(pwl.updateDict)

  ptl.tagChanged.connect(pwl.updateWords)
  pwl.dataChanged.connect(ui.wordview.reset)
  dwl.dataChanged.connect(ui.dictListView.reset)
  #Connect signals to web view
  pwl.pageLoad.connect(ui.webView.load)
  pwl.pageLoad.connect(dwl.load)
  #ui.tabwidget.currentChanged.connect()

  window.show()
  app.exec_()