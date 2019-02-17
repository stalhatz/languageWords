from PyQt5 import  QtWidgets

def addLabeledWidget(label , widget , layout):
  qLabel = QtWidgets.QLabel(widget)
  qLabel.setObjectName("widgetLabel")
  qLabel.setText(label)
  verticalLayout = QtWidgets.QVBoxLayout()
  verticalLayout.setObjectName("labelLayout")
  verticalLayout.addWidget(qLabel)
  verticalLayout.addWidget(widget)
  verticalLayout.setSpacing(0)
  layout.addLayout(verticalLayout)