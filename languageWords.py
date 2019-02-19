import argparse
from ui_mainwindow import Ui_MainWindow
from PyQt5.QtWidgets import (QApplication, QMainWindow)
from PyQt5.QtCore import QTimer

#TODO: [FEATURE_2] Add custom (user provided) examples
#TODO: [FEATURE_1] Add context menus(right click) to fluidify navigation and control
#TODO: [FEATURE_2] Show word in bold when found in example (impossible currently without implementing the paint function of a delegate)
#TODO: [FEATURE_0] Training mode where a category is selected and examples are shown for the user to fill the gaps.
#TODO: [FEATURE_0] Use word embeddings to propose new words given a tag
#TODO: [FEATURE_0] Use word embeddings to propose tags for new words

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
  ui = Ui_MainWindow.defaultInit(window)
  QTimer.singleShot(0,ui.showWelcomeDialog)


  stylesheet="stylesheet1.css"
  with open(stylesheet,"r") as fh:
    app.setStyleSheet(fh.read())
  
  window.show()
  app.exec_()