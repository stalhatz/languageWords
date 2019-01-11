from PyQt5 import QtCore, QtGui, QtWidgets

from PyQt5.QtCore import (QUrl,QVariant,Qt,pyqtSignal)
from PyQt5.QtCore import (QAbstractListModel,QModelIndex,QStringListModel)
from PyQt5.QtNetwork import (QNetworkAccessManager,QNetworkRequest,QNetworkReply)
import requests

import pandas as pd
from requests_futures.sessions import FuturesSession
from concurrent.futures import ThreadPoolExecutor
import dictionaries as dictHandler
from functools import partial

# FIXME : Async requests. It's fast but it will not show the definitions sometimes 
# (Racing condition? Is the server blocking us?).
# QNetworkAccessManager (which would be the easiest way to do this) not working due to QTBUG-68156
# Should use requests-futures
class DictWebList(QAbstractListModel):
  dataChanged = pyqtSignal(QModelIndex,QModelIndex)
  showMessage = pyqtSignal(str)
  def __init__(self):
    super(DictWebList,self).__init__()
    self.definitionsList = []
    self.lastRequest = None
    self.session = FuturesSession(max_workers=1)
    self.url = None
  def load(self,url):
    self.url = url
    self.definitionsList = []
    future = self.session.get(url.toString())
    future.add_done_callback(partial(self._load,url))
    self.lastRequest = future
    self.showMessage.emit("Loading from " + url.toString() )
  def _load(self,url,future):
    if url != self.url:
      future.cancel() #Should cancel itself when issuing the next request as max_workers = 1
      return
    request = future.result()
    if request.status_code > 200:
      self.definitionsList.append("Could not load page. Code :: " + str(request.status_code))
    else:
      self.showMessage.emit("Finshed loading from " + url.toString())
      html =  request.text
      self.definitionsList = dictHandler.getDefinitionsFromHtml(url.toString() , html)
    self.dataChanged.emit(self.createIndex(0,0) , self.createIndex(len(self.definitionsList) , 0))
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
  def getCurrentTag():
    str(self.df.iloc[index.row(),0])

class PandasWordList(QAbstractListModel):
  dataChanged = pyqtSignal()
  pageLoad    = pyqtSignal(QUrl)
  def __init__(self, df ,webview):
    super(PandasWordList,self).__init__()
    self.df = df
    self.df_image = df
    self.webView = webview
    self.dict = "wiktionary"
    self.url = None
    self.currentIndex = -1
  def rowCount(self, modelIndex):
    return len(self.df_image)
  def data(self, index, role):
    if not index.isValid() or not (0<=index.row()<len(self.df_image)):
      return QVariant()
    if role==Qt.DisplayRole:
      return str(self.df_image.iloc[index.row(),0])
  def selected(self, index , prevIndex):
    self.url =  QUrl(dictHandler.createUrl(self.dict , str(self.df_image.iloc[index.row(),0])))
    self.currentIndex = index.row()
    self.pageLoad.emit(self.url)
  def reload(self):
    if self.url is not None:
      self.pageLoad.emit(self.url)
  def updateWords(self,tag):
    self.df_image = self.df[self.df['tag'] == tag]
    self.dataChanged.emit()
  def updateDict(self,dictName):
    self.dict = dictName
    if self.currentIndex > 0:
      self.selected(self.createIndex(self.currentIndex,0) , self.createIndex(0 , 0))
words = {}
# TODO: Breakup ui setup in functions
class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
      MainWindow.setObjectName("MainWindow")
      MainWindow.resize(728, 521)
      self.centralwidget = QtWidgets.QWidget(MainWindow)
      self.centralwidget.setObjectName("centralwidget")
      
      self.outerVerticalLayout = QtWidgets.QVBoxLayout(self.centralwidget)
      self.outerVerticalLayout.setObjectName("outerVerticalLayout")
      self.buttonHorizontalLayout = QtWidgets.QHBoxLayout()
      self.buttonHorizontalLayout.setObjectName("buttonHorizontalLayout")

      self.addWordButton = QtWidgets.QPushButton(self.centralwidget)
      self.addWordButton.setObjectName("addWordButton")
      self.addWordButton.setMaximumSize(QtCore.QSize(100,100))
      self.addWordButton.setText("Add Word")
      self.editWordButton = QtWidgets.QPushButton(self.centralwidget)
      self.editWordButton.setObjectName("editWordButton")
      self.editWordButton.setMaximumSize(QtCore.QSize(100,100))
      self.editWordButton.setText("Edit Word")

      self.buttonHorizontalLayout.addWidget(self.addWordButton)
      self.buttonHorizontalLayout.addWidget(self.editWordButton)

      self.horizontalLayout = QtWidgets.QHBoxLayout()
      self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
      self.horizontalLayout.setObjectName("horizontalLayout")
      
      self.statusBar = QtWidgets.QStatusBar(self.centralwidget)
      self.statusBar.setObjectName("statusBar")
      self.statusBar.showMessage("Hello World")

      self.outerVerticalLayout.addLayout(self.buttonHorizontalLayout)
      self.outerVerticalLayout.addLayout(self.horizontalLayout)
      self.outerVerticalLayout.addWidget(self.statusBar)

      self.verticalLayout = QtWidgets.QVBoxLayout()
      self.verticalLayout.setObjectName("verticalLayout")
      self.dictSelect = QtWidgets.QComboBox(self.centralwidget)
      self.dictSelect.setMaximumSize(QtCore.QSize(300, 50))
      self.dictSelect.setObjectName("dictSelect")
      self.verticalLayout.addWidget(self.dictSelect)
      self.wordview = QtWidgets.QListView(self.centralwidget)
      self.wordview.setMaximumSize(QtCore.QSize(400, 400))
      self.wordview.setObjectName("wordview")
      self.verticalLayout.addWidget(self.wordview)
      self.tagview = QtWidgets.QListView(self.centralwidget)
      self.tagview.setMaximumSize(QtCore.QSize(400, 400))
      self.tagview.setObjectName("tagview")
      self.verticalLayout.addWidget(self.tagview)
      self.horizontalLayout.addLayout(self.verticalLayout)

      self.tabwidget = QtWidgets.QTabWidget(self.centralwidget)
      self.tabwidget.setObjectName("tabwidget")
      self.horizontalLayout.addWidget(self.tabwidget)

      self.dictListView = QtWidgets.QListView(self.tabwidget)
      self.dictListView.setObjectName("dictView")
      self.dictListView.setWordWrap(True)
      self.tabwidget.addTab(self.dictListView , "Custom view")

      self.webView = QtWebEngineWidgets.QWebEngineView(self.tabwidget)
      self.webView.setUrl(QtCore.QUrl("about:blank"))
      self.webView.setObjectName("webView")
      self.tabwidget.addTab(self.webView , "Webview")
      #self.horizontalLayout.addWidget(self.webView)
      
      MainWindow.setCentralWidget(self.centralwidget)
      self.menubar = QtWidgets.QMenuBar(MainWindow)
      self.menubar.setGeometry(QtCore.QRect(0, 0, 728, 30))
      self.menubar.setObjectName("menubar")
      self.menuFile = QtWidgets.QMenu(self.menubar)
      self.menuFile.setObjectName("menuFile")
      MainWindow.setMenuBar(self.menubar)
      self.statusbar = QtWidgets.QStatusBar(MainWindow)
      self.statusbar.setObjectName("statusbar")
      MainWindow.setStatusBar(self.statusbar)
      self.actionOpen = QtWidgets.QAction(MainWindow)
      self.actionOpen.setObjectName("actionOpen")
      self.menuFile.addAction(self.actionOpen)
      self.menubar.addAction(self.menuFile.menuAction())

      self.retranslateUi(MainWindow)
      QtCore.QMetaObject.connectSlotsByName(MainWindow)
    
    def setupDataUi(self, dictWords):
      self.pwl = PandasWordList(dictWords,self.webView)
      self.ptl = PandasTagList(dictWords)
      self.dwl = DictWebList()
      #Set signals/slots
      self.dictListView.setModel(self.dwl)
      self.tagview.setModel(self.ptl)
      self.tagview.selectionModel().currentChanged.connect(self.ptl.selected)
      self.wordview.setModel(self.pwl)
      self.wordview.selectionModel().currentChanged.connect(self.pwl.selected)
      self.dictSelect.currentTextChanged.connect(self.pwl.updateDict)

      self.ptl.tagChanged.connect(self.pwl.updateWords)
      #Connect signals to tab views
      self.pwl.dataChanged.connect(self.wordview.reset)
      self.dwl.dataChanged.connect(self.dictListView.dataChanged)
      self.dwl.showMessage.connect(self.statusBar.showMessage)
      
      self.tabConnected = -1
      self.connectTabSlots(self.tabwidget.currentIndex())

      self.tabwidget.currentChanged.connect(self.connectTabSlots)

    def connectTabSlots(self,current):
      if current == 1:
        if self.tabConnected == 0:
          self.pwl.pageLoad.disconnect(self.dwl.load)
        self.pwl.pageLoad.connect(self.webView.load)
        self.pwl.reload()
        self.tabConnected = 1
      if current == 0:
        if self.tabConnected == 1:
          self.pwl.pageLoad.disconnect(self.webView.load)
        self.pwl.pageLoad.connect(self.dwl.load)
        self.pwl.reload()
        self.tabConnected = 0
        
    def retranslateUi(self, MainWindow):
      _translate = QtCore.QCoreApplication.translate
      MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
      self.menuFile.setTitle(_translate("MainWindow", "Fi&le"))
      self.actionOpen.setText(_translate("MainWindow", "Open..."))
    
    # TODO: Show dialogs for adding/editing words.
    # def showAddWordDialog(self,event):
    #   currentTag = self.ptl.getCurrentTag()
    #   self.addWordDialog = QtWidgets.QDialog(self.centralwidget)
    #   hLayout = QtWidgets.QHBoxLayout(self.addWordDialog)
    #   vLeftLayout = QtWidgets.QVBoxLayout(self.addWordDialog)
    #   vRightLayout = QtWidgets.QVBoxLayout(self.addWordDialog)
    #   hLayout.addLayout(vLeftLayout)
    #   hLayout.addLayout(vRightLayout)

    #   label = 

    # def showEditWordDialog(self,event):

from PyQt5 import QtWebEngineWidgets 
