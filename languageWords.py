import time
import os
import subprocess

import argparse

from ui_mainwindow import Ui_MainWindow
from PyQt5.QtWidgets import (QApplication, QWidget, QMainWindow)

# def runCommand(command, args):
#   global useGUI
#   if useGUI:
#     a = subprocess.run([command] +  args, stdout=subprocess.PIPE)
#     b = a.stdout.decode('utf-8')
#     return b
  
# def createDFFromDict(dictWords):
#   words["text"] = []
#   words["hyperlink"] = []
#   for key in dictWords:
#     words["text"].append(key)
#     words["hyperlink"].append(dictWords[key][0])
#   tags["tag"] = []
#   tags["text"] = []
#   for key in dictWords:
#     words["tag"].append(dictWords[key][1])
#     words["text"].append(key)
#   return pd.DataFrame.from_dict(words),pd.DataFrame.from_dict(tags)
from dataModels import (WordDataModel, DefinitionDataModel)
if __name__ == "__main__":
  parser = argparse.ArgumentParser(description='Process some integers.')
  parser.add_argument('-l', nargs='?', const='dictWords.pd.pkl', default=None)
  parser.add_argument('-s', nargs='?', const='dictWords.pkl', default=None)
  args = parser.parse_args()
  
  if args.s is None and args.l is not None:
    args.s = args.l
  
  if args.l is not None:
    wordDataModel = WordDataModel.fromFilename(args.l)
  else:
    wordDataModel = WordDataModel(None)

  app = QApplication([])
  stylesheet="stylesheet1.css"
  with open(stylesheet,"r") as fh:
    app.setStyleSheet(fh.read())
  
  dictDataModel = DefinitionDataModel(["wiktionary", "larousse"],
                      ["https://fr.wiktionary.org/wiki/","https://www.larousse.fr/dictionnaires/francais/"],
                      [False,True])

  window = QMainWindow()
  ui = Ui_MainWindow()
  ui.setupUi(window)
  ui.setupDataModels(wordDataModel, dictDataModel)
  ui.dictSelect.insertItems(0,["wiktionary", "larousse"])

  window.show()
  app.exec_()