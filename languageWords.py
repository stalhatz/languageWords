import time
import os
import subprocess
import datetime as dt
import pandas as pd
import pickle

class TextElement:
  def __init__(self, text , hyperlink = None , tag = None):
    self.text = text
    self.link = "" 
    self.date = dt.datetime.today()
    self.tags = []
    self.hyperlink = hyperlink
    self.spellChecked = False
  def __repr__(self):
    return self.text
  def __str__(self):
    return self.text
    

# def runCommand(command, args):
#   global useGUI
#   if useGUI:
#     a = subprocess.run([command] +  args, stdout=subprocess.PIPE)
#     b = a.stdout.decode('utf-8')
#     return b
  
from PyQt5.QtWidgets import (QApplication,QInputDialog, QLineEdit,QCompleter)
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

import pandas as pd
# def saveToPandas(tasks, taskName):
#   global pandasTasks
#   global pandasWindows
#   tasksDict = {}
#   windowsDict = {}
#   j = 0
#   k=0
#   for task in tasks.values():
#     if len(task.subTasks) > 0:
#       pandasTasks[taskName],pandasWindows[taskName] = saveToPandas(task.subTasks,str(task))
    
    
# #    print(str(task) + " : Startdates :: " + str(len(task.startDates)) )
# #    print(str(task) + " : Durations :: " + str(len(task.durations)) )
#     for i,date in enumerate(task.startDates):
#       taskDict = {}
#       taskDict["taskName"] = str(task)
#       taskDict["date"] = date
#       taskDict["duration"] = task.durations[i]
#       tasksDict[j] = taskDict
#       j+=1
      
#     for i,processName in enumerate(task.processNames):
#       windowDict= {}
#       windowDict["taskName"] = str(task)
#       windowDict["processName"] = processName
#       windowDict["windowName"] = task.windowNames[i]
#       windowDict["windowDate"] = task.windowDates[i]
#       windowDict["windowDuration"] = task.windowDurations[i]
#       windowsDict[k] = windowDict
#       k+=1
#   taskTable = pd.DataFrame(tasksDict).T
#   windowTable = pd.DataFrame(windowsDict).T
#   return taskTable,windowTable
      
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

import argparse

words = {}
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
  print(dictWords)  