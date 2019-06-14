import argparse
from ui_mainwindow import Ui_MainWindow
from PyQt5.QtWidgets import (QApplication, QMainWindow)
from PyQt5.QtCore import QTimer
# Connectivity:
#TODO: [FEATURE_2] Request asynchronously more than one web page
#TODO: [FEATURE_1] Dictionaries can return more results when user scrolls
#TODO: [FEATURE_3] Add user options for Enabling caching / Cache expiration period
#Documentation:
#TODO: [FEATURE_0] Write README.md
#Machine Learning:
#TODO: [FEATURE_0] Use word embeddings to propose new words given a tag
#TODO: [FEATURE_0] Use word embeddings to propose tags for new words
#Interface:
#TODO: [FEATURE_0] Use a QStackedLayout to show alternative layouts for manipulating/viewing/experimenting with data
#TODO: [FEATURE_1] Sort ListViews by interacting with their corresponding Label
#TODO: [FEATURE_2] Translate interface
#TODO: [FEATURE_3] Implement rename word action
#TODO: [FEATURE_3] Show in bold the matching part of the elements of a list view relating to the filter being applied
#TODO: [FEATURE_3] Extend bold algorithm to full-words.
#TODO: [FEATURE_3] Option to add quotation marks in query to Online Dictionary
#FIXME: Calibrate the stepping of the scrollbar
#FIXME: When switching dictionaries the scrollbar should return to the start
#FIXME: Erase custom tag from textbox after 'Add tag' button has been clicked
#FIXME: Ctrl+s works sometimes as Save As...
#FIXME: Bold algorithm takes too long for long phrases
#Data Model:
#TODO: [FEATURE_2] Enable Online definitions to return markups and preserve them during automatic marking up
#TODO: [FEATURE_2] Create table to hold markup per definition. Add field to distinguish between automatically created and markups provided by online definitions.
#Miscellaneous:
#TODO: [FEATURE_0] Training mode where a category is selected and examples are shown for the user to fill the gaps.
#TODO: [FEATURE_1] Drag and Drop support between list views
#TODO: [FEATURE_1] Customize generic css styles by modifying styles in-code (Is it really needed?)
#TODO: [FEATURE_2] Auto tags: Example: When a phrase has no examples added to saved definitions add it automatically to the tag #noExamples
#TODO: [FEATURE_2] Change saved information category / Add user example category.
#TODO: [FEATURE_3] Have a default metatag "All" applied to all words. Should not be renamable or deletable.
#Testing

#TODO: [FEATURE_2] Create an interactive CLI.





if __name__ == "__main__":
  parser = argparse.ArgumentParser(description='Process some integers.')
  parser.add_argument('-l', nargs='?', const='french_test_5.pkl', default=None)
  parser.add_argument('-s', nargs='?', const='dictWords.pkl', default=None)
  args = parser.parse_args()
  
  app = QApplication([])
  window = QMainWindow()
  
  if args.s is None and args.l is not None:
    args.s = args.l
  
  # if args.l is not None:
  #    ui = Ui_MainWindow.fromFile(args.l, window)
  # else:
  ui = Ui_MainWindow.defaultInit(app,window)
  QTimer.singleShot(0,ui.showWelcomeDialog)

  window.show()
  app.exec_()