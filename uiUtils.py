from PyQt5 import QtCore, QtGui , QtWidgets

def addLabeledWidget(label , widget , layout , actions = None):
  qLabel = QtWidgets.QLabel(widget)
  qLabel.setObjectName("widgetLabel")
  qLabel.setText(label)
  if actions is not None:
    qLabel.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)
    for action in actions:
      qLabel.insertAction(action)
  verticalLayout = QtWidgets.QVBoxLayout()
  verticalLayout.setObjectName(widget.objectName() + "_layout")
  verticalLayout.addWidget(qLabel)
  verticalLayout.addWidget(widget)
  verticalLayout.setSpacing(0)
  layout.addLayout(verticalLayout)
  return (verticalLayout,qLabel)