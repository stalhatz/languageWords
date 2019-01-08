import time
import os
import subprocess
import datetime as dt

import pickle
import argparse
import sys

from ui_mainwindow import Ui_MainWindow
from PyQt5.QtWidgets import (QApplication,QWidget,QMainWindow)
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
  ui.setupDataUi(dictWords)
  ui.dictSelect.insertItems(0,["wiktionary", "larousse"])

  window.show()
  app.exec_()