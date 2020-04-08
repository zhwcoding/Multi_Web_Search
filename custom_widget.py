from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

# 自定义LineEdit，在web显示页用到，拖拽网址到网址框自动跳转
class LineEdit(QLineEdit):
    def __init__(self, parent=None):
        super(LineEdit, self).__init__(parent)
        self.setAcceptDrops(True)

    def dragEnter(self, e):
        text = e.mimeData().text()
        if "http" in text:
            e.accept()
        else:
            e.ignore()
    

    def dropEvent(self, e):
        self.setText(e.mimeData().text())
        self.returnPressed.emit()

# 自定义ListWidget，拖拽换序
class ListWidget(QListWidget):
    signal = pyqtSignal(int, int)

    def __init__(self, parent=None):
        super(ListWidget, self).__init__(parent)
        self.setDragDropMode(self.InternalMove)
        self.setEditTriggers(self.DoubleClicked)
        self.setContextMenuPolicy(Qt.CustomContextMenu)

    def dropEvent(self, e):
        index1 = self.currentRow()
        super(ListWidget, self).dropEvent(e)
        index2 = self.currentRow()
        self.signal.emit(index1, index2)

# class ListWidget2(QListWidget):
#     signal = pyqtSignal(int, int)

#     def __init__(self, parent=None):
#         super(ListWidget2, self).__init__(parent)
#         self.setDragDropMode(self.InternalMove)
#         self.setEditTriggers(self.DoubleClicked)
#         self.setContextMenuPolicy(Qt.CustomContextMenu)

#     def dropEvent(self, e):
#         index1 = self.currentRow()
#         super(ListWidget2, self).dropEvent(e)
#         index2 = self.currentRow()
#         self.signal.emit(index1, index2)

# class ListWidget3(QListWidget):
#     signal = pyqtSignal(int, int)

#     def __init__(self, parent=None):
#         super(ListWidget3, self).__init__(parent)
#         self.setDragDropMode(self.InternalMove)
#         self.setEditTriggers(self.DoubleClicked)
#         self.setContextMenuPolicy(Qt.CustomContextMenu)

#     def dropEvent(self, e):
#         index1 = self.currentRow()
#         super(ListWidget3, self).dropEvent(e)
#         index2 = self.currentRow()
#         self.signal.emit(index1, index2)






        

