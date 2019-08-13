
#from PyQt5.QtCore import QRect,QSize
#from PyQt5.QtGui import QTextDocument,QAbstractTextDocumentLayout,QPalette
#from PyQt5.QtWidgets import QStyleOptionViewItem,QStyledItemDelegate,QApplication,QStyle

from PyQt5 import QtCore, QtGui , QtWidgets
import re

def cleanhtml(raw_html):
  """ Taken from : https://stackoverflow.com/questions/9662346/python-code-to-remove-html-tags-from-a-string """
  cleanr = re.compile('<.*?>')
  cleantext = re.sub(cleanr, '', raw_html)
  return cleantext

class HTMLDelegate(QtWidgets.QStyledItemDelegate):
  def __init__(self, parent=None):
    super(HTMLDelegate, self).__init__(parent)
    self.doc = QtGui.QTextDocument(self)

  def copyStyleProperties(self,option,ctx):
    ctx.palette.setColor(QtGui.QPalette.Text, option.palette.color(QtGui.QPalette.Active, QtGui.QPalette.Text))
     
  def paint(self, painter, option, index):
    substring = index.data(QtCore.Qt.UserRole)
    painter.save()
    options = QtWidgets.QStyleOptionViewItem(option)
    self.initStyleOption(options, index)
    self.doc.setHtml(options.text)
    self.doc.setTextWidth(options.widget.viewport().size().width())
    self.doc.setDefaultFont(options.widget.font())
    options.text = ""
    style = QtWidgets.QApplication.style() if options.widget is None \
        else options.widget.style()
    style.drawControl(QtWidgets.QStyle.CE_ItemViewItem, options, painter,options.widget)

    ctx = QtGui.QAbstractTextDocumentLayout.PaintContext()
    self.copyStyleProperties(option,ctx)

    textRect = style.subElementRect(QtWidgets.QStyle.SE_ItemViewItemText, options , options.widget)
    painter.translate(textRect.topLeft())
    painter.setClipRect(textRect.translated(-textRect.topLeft()))
    self.doc.documentLayout().draw(painter, ctx)

    painter.restore()


  def sizeHint(self, option, index):
    options = QtWidgets.QStyleOptionViewItem(option)
    self.initStyleOption(options,index)

    self.doc.setHtml(options.text)
    self.doc.setTextWidth(options.widget.size().width())
    self.doc.setDefaultFont(options.widget.font())
    
    return QtCore.QSize(self.doc.idealWidth(), self.doc.size().height())

  def createEditor(self, parent, option, index):
    if (type(index.data()) == type("")):
      editor = TextEdit(parent)
      editor.editingFinished.connect(self.commitAndCloseEditor)
      return editor
    else:
      return super(HTMLDelegate, self).createEditor(parent,option,index)

  def setEditorData(self, editor,index):
    editor.setText(index.data())
  
  def setModelData(self, editor,model,index):
    text = cleanhtml( editor.toPlainText())
    model.setData(index, text )
    # it = editor.document().begin().begin()
    # while not it.atEnd():
    #   fragment = it.fragment()
    #   if fragment.isValid():
    #     print(fragment.text())
    #     print(fragment.charFormat().fontWeight())
    #   it += 1


  def commitAndCloseEditor(self):
    editor = self.sender()
    self.commitData.emit(editor)
    editor._changed = False
    self.closeEditor.emit(editor)


#Copied from https://gist.github.com/hahastudio/4345418
class TextEdit(QtWidgets.QTextEdit):
    """
    A TextEdit editor that sends editingFinished events 
    when the text was changed and focus is lost.
    """

    editingFinished = QtCore.pyqtSignal()
    receivedFocus = QtCore.pyqtSignal()
    
    def __init__(self, parent=None):
      super(TextEdit, self).__init__(parent)
      self._changed = False
      self.setTabChangesFocus( True )
      self.textChanged.connect( self._handle_text_changed )
      self.setMinimumHeight(50)

    def keyPressEvent(self , event):
      if (event.key() == QtCore.Qt.Key_Enter) or (event.key() == QtCore.Qt.Key_Return):
        if int( QtGui.QGuiApplication.instance().queryKeyboardModifiers() & QtCore.Qt.ControlModifier) != 0:
          #Simulate an Return press
          enterEvent = QtGui.QKeyEvent( QtCore.QEvent.KeyPress, QtCore.Qt.Key_Return, QtCore.Qt.NoModifier)
          super(TextEdit, self).keyPressEvent( enterEvent )  
        else:
          self.editingFinished.emit()
      else:
        super(TextEdit, self).keyPressEvent( event )

    def focusInEvent(self, event):
      super(TextEdit, self).focusInEvent( event )
      self.receivedFocus.emit()

    # def focusOutEvent(self, event):
    #   if self._changed:
    #       self.editingFinished.emit()
    #   super(TextEdit, self).focusOutEvent( event )

    def _handle_text_changed(self):
      self._changed = True

    def setTextChanged(self, state=True):
      self._changed = state

    def setHtml(self, html):
      QtGui.QTextEdit.setHtml(self, html)
      self._changed = False  
    
    def text(self):
      return cleanhtml(self.toPlainText())