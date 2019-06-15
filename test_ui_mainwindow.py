import random
from ui_mainwindow import Ui_MainWindow
import pytest
import io



@pytest.fixture(scope="session")
def initDefMainWindow():
  a = Ui_MainWindow.defaultInit()
  a.newProject("French" , "TestProj1")
  a.addWord("bonjour" , ["tag1", "tag2", "tag3"])
  a.addWord("tard"    , ["tag4", "tag2", "tag3"])
  a.addWord("bonne"   , ["tag5", "tag6", "tag3"])
  a.saveDefinition("def1","example","bonjour",None,"Custom")
  a.saveDefinition("def2","example","bonjour",None,"Custom")
  a.saveDefinition("def3","example","bonjour",None,"Custom")
  a.saveDefinition("def4","example","tard",None,"Custom")
  a.saveDefinition("def5","example","tard",None,"Custom")
  a.saveDefinition("def6","example","bonne",None,"Custom")
  return a

def test_getters(initDefMainWindow):
  a = initDefMainWindow
  assert ( set(a.wordDataModel.getWords()) == set(["bonjour","tard","bonne"]))
  assert ( set(a.defDataModel.getDefinitionsForWord("bonjour").definition)  == set( ["def1" , "def2" , "def3"] ) )
  assert ( set(a.tagDataModel.getTags()) == set(["tag1","tag2","tag3","tag4","tag5","tag6"]))
  #memoryFile = io.BytesIO()
  #model.saveData(memoryFile)

