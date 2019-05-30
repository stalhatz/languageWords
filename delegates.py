
#from PyQt5.QtCore import QRect,QSize
#from PyQt5.QtGui import QTextDocument,QAbstractTextDocumentLayout,QPalette
#from PyQt5.QtWidgets import QStyleOptionViewItem,QStyledItemDelegate,QApplication,QStyle

from PyQt5 import QtCore, QtGui , QtWidgets

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