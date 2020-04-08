from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtWebEngineWidgets import *
from PyQt5.QtSql import QSqlDatabase, QSqlQuery

import os
import sys

from Ui_mainWindow import Ui_MainWindow
from Ui_dialog import Ui_Dialog

from custom_widget import  ListWidget

from Worker import Worker
from Web import Web


class Dialog(QDialog, Ui_Dialog):
    signal_value = pyqtSignal(int)

    def __init__(self, parent=None):
        super(Dialog, self).__init__()
        self.setupUi(self)
        self.pushButton.clicked.connect(self.pushButton_clicked)

    def pushButton_clicked(self):
        value = self.spinBox.value()
        self.signal_value.emit(value)
        self.close()


class MainWindow(QMainWindow, Ui_MainWindow):
    signal = pyqtSignal(list, str)  # 向网页显示页界面发送 网址列表，搜索文字 的信号 

    '''生成搜素首页'''
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.setupUi(self)
        self.set_out_widget_visible(False)  # out_widget 指导出时所显示的几个控件
        self.set_in_widget_visible(False)
        self.stackedWidget.removeWidget(self.page_2)    # 由于ui文件是在designer中生成的，stackedWidget最少有两个子分支，所以此处删除一个
        self.stackedWidget_2.removeWidget(self.page_4)

        self.web = web

        self.category = []  # 用于保存从数据库中读取的一级目录
        self.categoryi = [] # 用于保存从数据库中读取的二级目录(二维数组)
        self.index_to_sqlIndex_first_list = []   # 将一级目录的id按顺序记录下来，在更换数据顺序中会用到
        self.index_to_sqlIndex_second_listes = []    # 将二级目录的id按顺序记录下来（二维数组）
        self.id_category_first_max = 0  # 一级目录id的最大值
        self.id_category_second_max_list = []   # 各二级目录id最大值的列表
        self.id_webAddress_max = 0  # 网址id的最大值
        
        self.listWidget_category_list = []  # 将stackedWidget(即二阶目录)的每页的listWidget保存起来，后面会用到
        self.listWidget_webAddress_list = []    # 保存stackedWidget_2的每页的listWidget
        self.current_webAddress_list = []   # 当前stackedWidget_2页面上listWidget上的网址列表，方便直接发送给显示界面

        self.indexTuple_to_sqlIndexTuple = {} # 前面两个listWidget的序数所组成的index组合所对应其在数据库中的index组合
        self.sqlIndex_to_webAddress_listWidgetIndex = {}      # 其在数据库中的index组合所对应的webAddress ListWidget在stackedWidget的序数
        self.sqlIndexTuple_to_WebAddressIDLIST = {} #数据库index组合所对应的webAddressIDlist,如{'(1,1)':[2,3], '(1,2):[4,5,6,7]}
        self.sqlIndexTuple_to_webAddress = {}   # 数据库index组合所对应的webAddress，如{'(1,1)':['https://...','https://...'], '(1,2)':['','']}

        self.first_index = 1    # 一级目录的当前index
        self.second_index = 1   # 二级目录的当前index
        self.sign_out = 0   # 用于判断当前是否为导出状态

        self.path = './db'  # 数据库位置
        # 加载数据库数据， 加载stackedWidget的子分支界面
        self.load_Database()
        self.load_stackWidget1(self.category)
        self.load_stackWidget2(self.categoryi)

        self.listWidget_category_first.currentRowChanged.connect(self.category_widget_changed)
        self.listWidget_category_first.signal.connect(self.listWidget_category_first_drop)
        self.listWidget_category_first.doubleClicked.connect(self.listWidget_category_first_double)
        self.listWidget_category_first.customContextMenuRequested.connect(self.listWidget_category_first_context)
        self.lineEdit_search.returnPressed.connect(self.lineEdit_search_enterd)
        self.action_in.triggered.connect(self.file_in)
        self.action_out.triggered.connect(self.file_out)
        self.action_add_first.triggered.connect(self.action_add_first_triggerd)
        self.action_add_second.triggered.connect(self.action_add_second_triggerd)
        self.action_add_webAddress.triggered.connect(self.action_add_webAddress_triggerd)
        self.action_delete_first.triggered.connect(lambda _, Id=None: self.action_delete_first_triggerd(Id))
        self.action_delete_second.triggered.connect(lambda _, Id1=None, Id2=None: self.action_delete_second_triggerd(Id1, Id2))
        self.action_delete_webAddress.triggered.connect(self.action_delete_webAddress_triggerd)
        self.pushButton_out.clicked.connect(self.pushButton_out_clicked)
        self.pushButton_cancel.clicked.connect(self.pushButton_cancel_clicked)



    def action_add_first_triggerd(self):
        dialog = Dialog(self)
        dialog.signal_value.connect(self.add_first)
        dialog.exec()
    
    def add_first(self, value):
        db = QSqlDatabase.addDatabase('QSQLITE')
        db.setDatabaseName(self.path + '/multiWeb_Database.db')
        if db.open():
            query = QSqlQuery(db)
            for i in range(value):
                index = i + self.id_category_first_max + 1
                query.exec('insert into category values({}, "{}")'.format(index, 'xxx'))
                query.exec('create table category{}(id int, name vhar)'.format(index))
                query.exec('insert into category{} values(1, "{}")'.format(index, 'xxx'))
                query.exec('insert into webAddress values({}, "{}", "{}", {}, {})'.format(i + self.id_webAddress_max + 1, 'xxx', 'https://xxx', index, 1))
            db.close()
        self.data_update()

    def action_add_second_triggerd(self):
        dialog = Dialog(self)
        dialog.signal_value.connect(self.add_second)
        dialog.exec()

    def add_second(self, value):
        ID = self.index_to_sqlIndex_first_list[self.first_index-1]
        id_category_second_max = self.id_category_second_max_list[self.first_index-1]
        db = QSqlDatabase.addDatabase('QSQLITE')
        db.setDatabaseName(self.path + '/multiWeb_Database.db')
        if db.open():
            query = QSqlQuery(db)
            for i in range(value):
                query.exec('insert into category{} values({}, "{}")'.format(ID, i + id_category_second_max + 1, 'xxx'))
                query.exec('insert into webAddress values({}, "{}", "{}", {}, {})'.format(i + self.id_webAddress_max + 1, 'xxx', 'https://xxx', ID, index))
            db.close()
        self.data_update()

    def action_add_webAddress_triggerd(self):
        dialog = Dialog(self)
        dialog.signal_value.connect(self.add_webAddress)
        dialog.exec()
    
    def add_webAddress(self, value):
        ID1 = self.index_to_sqlIndex_first_list[self.first_index-1]
        ID2 = self.index_to_sqlIndex_second_listes[self.first_index-1][self.second_index-1]
        db = QSqlDatabase.addDatabase('QSQLITE')
        db.setDatabaseName(self.path + '/multiWeb_Database.db')
        if db.open():
            query = QSqlQuery(db)
            for i in range(value):
                query.exec('insert into webAddress values({}, "{}", "{}", {}, {})'.format(i + self.id_webAddress_max + 1, 'xxx', 'https://xxx', ID1, ID2))
            db.close()
        self.data_update()

    def action_delete_first_triggerd(self, ID=None):
        db = QSqlDatabase.addDatabase('QSQLITE')
        db.setDatabaseName(self.path + '/multiWeb_Database.db')
        if db.open():
            query = QSqlQuery(db)
        if ID == None:
            ID = self.index_to_sqlIndex_first_list[self.first_index-1]
            key = '({},{})'.format(self.first_index, self.second_index)
            key = self.indexTuple_to_sqlIndexTuple[key]
            index = self.sqlIndex_to_webAddress_listWidgetIndex[key]
            listWidget = self.listWidget_webAddress_list[index-1]
            webIDs = self.sqlIndexTuple_to_WebAddressIDLIST[key]
            sign = QMessageBox.information(self, '提醒', '此操作将会删除该目录下所有子目录\n确定删除吗', QMessageBox.Ok)
            if sign == 1024:
                if len(self.index_to_sqlIndex_first_list) != 1:
                    query.exec('delete from category where id={}'.format(ID))
                    query.exec('drop table if exists category{}'.format(ID))
                    for Id in webIDs:
                        query.exec('delete from webAddress where id={}'.format(Id))
                else:
                    query.exec('delete from category where id={}'.format(ID))
                    QMessageBox.critical(self, '错误', '当前主分类仅有一条，将自动创建一条', QMessageBox.Ok)
                    db.close()
                    os.remove(self.path + '/multiWeb_Database.db')
                    self.generate_origin_database()
                db.close()
                self.data_update()
        else:
            if len(self.index_to_sqlIndex_first_list) != 1:
                query.exec('delete from category where id={}'.format(ID))
            else:
                query.exec('delete from category where id={}'.format(ID))
                QMessageBox.critical(self, '错误', '当前所有分类仅有一条，将自动创建一条', QMessageBox.Ok)
                db.close()
                os.remove(self.path + '/multiWeb_Database.db')
                self.generate_origin_database()
                

    def action_delete_second_triggerd(self, ID1, ID2):
        db = QSqlDatabase.addDatabase('QSQLITE')
        db.setDatabaseName(self.path + '/multiWeb_Database.db')
        if db.open():
            query = QSqlQuery(db)
        if ID1 == None and ID2 == None:
            Id1s = self.index_to_sqlIndex_first_list
            IDs = self.index_to_sqlIndex_second_listes[self.first_index-1]
            key = '({},{})'.format(self.first_index, self.second_index)
            key = self.indexTuple_to_sqlIndexTuple[key]
            index = self.sqlIndex_to_webAddress_listWidgetIndex[key]
            listWidget = self.listWidget_webAddress_list[index-1]
            webIDs = self.sqlIndexTuple_to_WebAddressIDLIST[key]
            sign1 = 1
            sign2 = 0
            sign3 = QMessageBox.information(self, '提醒', '此操作将会删除该目录下的所有条目\n删除后将无法找回\n确定删除吗', QMessageBox.Ok, QMessageBox.Cancel)
            if sign3 == 1024:
                if len(IDs) == 1:
                    sign2 = QMessageBox.information(self, '提醒', '此目录下仅有此一条\n将会将此上级目录一并删除\n确定删除吗', QMessageBox.Ok, QMessageBox.Cancel)
                if sign2 == 4194304:
                    sign1 = 0
                if sign1 == 1:
                    ID1 = Id1s[self.first_index-1]
                    ID = IDs[self.second_index-1]
                    ID2 = self.index_to_sqlIndex_second_listes[self.first_index-1]
                    query.exec('delete from category{} where id={}'.format(ID1, ID))
                    for i in webIDs:
                        query.exec('delete from webAddress where id={}'.format(i))
                    if sign2 == 1024:
                        query.exec('drop table if exists category{}'.format(ID))
                        self.action_delete_first_triggerd(ID)
                db.close()
                self.data_update()
        else:
            query.exec('delete from category{} where id={}'.format(ID1, ID2))
            if len(self.index_to_sqlIndex_second_listes[self.first_index-1]) == 1:
                query.exec('drop table if exists category{}'.format(ID1))
                self.action_delete_first_triggerd(ID1)
                db.close()
        

    def action_delete_webAddress_triggerd(self):
        key = '({},{})'.format(self.first_index, self.second_index)
        key = self.indexTuple_to_sqlIndexTuple[key]
        index = self.sqlIndex_to_webAddress_listWidgetIndex[key]
        listWidget = self.listWidget_webAddress_list[index-1]
        row = listWidget.currentRow()
        webIDs = self.sqlIndexTuple_to_WebAddressIDLIST[key]
        sign1 = 1
        sign2 = 0
        sign3 = QMessageBox.information(self, '提醒', '此操作将删除该条目\n删除后将无法找回\n确定删除吗', QMessageBox.Ok, QMessageBox.Cancel)
        if sign3 == 1024:
            if len(webIDs) == 1:
                sign2 = QMessageBox.information(self, '提醒', '此目录下仅有此一条，将会将上级目录一并删除\n确定删除吗', QMessageBox.Ok, QMessageBox.Cancel)
            if sign2 == 4194304:
                sign1 =0
            if sign1 == 1:
                id_category_first = self.index_to_sqlIndex_first_list[self.first_index-1]
                id_category_second = self.index_to_sqlIndex_second_listes[self.first_index-1][self.second_index-1]
                webID = webIDs[row]
                db = QSqlDatabase.addDatabase('QSQLITE')
                db.setDatabaseName(self.path + '/multiWeb_Database.db')
                if db.open():
                    query = QSqlQuery(db)
                    query.exec('delete from webAddress where id={}'.format(webID))
                    if sign2 == 1024:
                        self.action_delete_second_triggerd(id_category_first, id_category_second)
                db.close()
                self.data_update()
        
    
    def listWidget_category_first_context(self, qpoint):
        x = qpoint.x()
        y = qpoint.y()
        item = self.listWidget_category_first.itemAt(x, y)
        if item:
            menu = QMenu()
            item1 = menu.addAction(self.action_add_first)
            item2 = menu.addAction(self.action_delete_first)
            menu.exec_(self.listWidget_category_first.mapToGlobal(qpoint))
        else:
            menu = QMenu()
            item = menu.addAction(self.action_add_first)
            menu.exec_(self.listWidget_category_first.mapToGlobal(qpoint))


    def listWidget_category_second_context(self, qpoint):
        x = qpoint.x()
        y = qpoint.y()
        listWidget = self.listWidget_category_list[self.first_index-1]
        item = listWidget.itemAt(x, y)
        if item:
            menu = QMenu()
            item1 = menu.addAction(self.action_add_second)
            item2 = menu.addAction(self.action_delete_second)
            action = menu.exec_(listWidget.mapToGlobal(qpoint))
        else:
            menu = QMenu()
            item = menu.addAction(self.action_add_second)
            menu.exec_(listWidget.mapToGlobal(qpoint))


    def listWidget_webAddress_context(self, qpoint):
        x = qpoint.x()
        y = qpoint.y()
        key = '({},{})'.format(self.first_index, self.second_index)
        key = self.indexTuple_to_sqlIndexTuple[key]
        index = self.sqlIndex_to_webAddress_listWidgetIndex[key]
        listWidget = self.listWidget_webAddress_list[index-1]
        item = listWidget.itemAt(x, y)
        if item:
            menu = QMenu()
            item1 = menu.addAction(self.action_add_webAddress)
            item2 = menu.addAction(self.action_delete_webAddress)
            action = menu.exec_(listWidget.mapToGlobal(qpoint))
        else:
            menu = QMenu()
            item = menu.addAction(self.action_add_webAddress)
            menu.exec_(listWidget.mapToGlobal(qpoint))

    def listWidget_category_first_drop(self, index1, index2):
        id1 = self.index_to_sqlIndex_first_list[index1]
        id2 = self.index_to_sqlIndex_first_list[index2]
        name1 = ''
        name2 = ''
        db = QSqlDatabase.addDatabase('QSQLITE')
        db.setDatabaseName(self.path + '/multiWeb_Database.db')
        if db.open():
            query = QSqlQuery(db)
            query.exec('select * from category where id={}'.format(id1))
            while query.next():
                name1 = query.value(1)
            query.exec('select * from category where id={}'.format(id2))
            while query.next():
                name2 = query.value(1)
            query.exec('update category set name="{}" where id={}'.format(name1, id2))
            query.exec('update category set name="{}" where id={}'.format(name2, id1))
            query.exec('update category set id=0 where id={}'.format(id1))
            query.exec('update category set id={} where id={}'.format(id1, id2))
            query.exec('update category set id={} where id=0'.format(id2))
        db.close()
        self.data_update()

    def listWidget_category_second_drop(self, index1, index2):
        id1 = self.index_to_sqlIndex_second_listes[self.first_index-1][index1]
        id2 = self.index_to_sqlIndex_second_listes[self.first_index-1][index2]
        index = self.index_to_sqlIndex_first_list[self.first_index-1]
        name1 = ''
        name2 = ''
        db = QSqlDatabase.addDatabase('QSQLITE')
        db.setDatabaseName(self.path + '/multiWeb_Database.db')
        if db.open():
            query = QSqlQuery(db)
            query.exec('select * from category{} where id={}'.format(index, id1))
            while query.next():
                name1 = query.value(1)
            query.exec('select * from category{} where id={}'.format(index, id2))
            while query.next():
                name2 = query.value(1)
            query.exec('update category{} set name="{}" where id={}'.format(index, name1, id2))
            query.exec('update category{} set name="{}" where id={}'.format(index, name2, id1))
            query.exec('update category{} set id=0 where id={}'.format(index, id1))
            query.exec('update category{} set id={} where id={}'.format(index, id1, id2))
            query.exec('update category{} set id={} where id=0'.format(index, id2))
        db.close()
        self.data_update()
        self.data_update()

    def listWidget_webAddress_drop(self, index1, index2):
        key = '({},{})'.format(self.first_index, self.second_index)
        key = self.indexTuple_to_sqlIndexTuple[key]
        webIDs = self.sqlIndexTuple_to_WebAddressIDLIST[key]
        id1 = webIDs[index1]
        id2 = webIDs[index2]
        name1 = ''
        name2 = ''
        url1 = ''
        url2 = ''
        db = QSqlDatabase.addDatabase('QSQLITE')
        db.setDatabaseName(self.path + '/multiWeb_Database.db')
        if db.open():
            query = QSqlQuery(db)
            query.exec('select name, url from webAddress where id={}'.format(id1))
            while query.next():
                name1 = query.value(0)
                url1 = query.value(1)
            query.exec('select name, url from webAddress where id={}'.format(id2))
            while query.next():
                name2 = query.value(0)
                url2 = query.value(1)
            query.exec('update webAddress set name="{}" where id={}'.format(name1, id2))
            query.exec('update webAddress set name="{}" where id={}'.format(name2, id1))
            query.exec('update webAddress set url="{}" where id={}'.format(url1, id2))
            query.exec('update webAddress set url="{}" where id={}'.format(url2, id1))
            query.exec('update webAddress set id=0 where id={}'.format(id1))
            query.exec('update webAddress set id={} where id={}'.format(id1, id2))
            query.exec('update webAddress set id={} where id=0'.format(id2))

        db.close()
        self.data_update()

    def textEdit_text_changed(self):
        QMessageBox.information(self, '提醒', '如果您需要手动更改下方文本框内容，请按正确格式，否则会发生意想不到的错误\n一级分类，二级分类，条目的"-"符号前依次为0,2,4个空格(只能是空格，请不要自动对齐)\n每行结尾无空格\n网站名称与网址之间用五个“-”连接', QMessageBox.Ok)
        self.textEdit.textChanged.disconnect(self.textEdit_text_changed)

    # 当搜索框回车激活的函数
    def lineEdit_search_enterd(self):
        self.setVisible(False)  # 搜索框回车后，弹出网页界面的显示，使首页面设置为不可见
        self.signal.emit(self.current_webAddress_list, self.lineEdit_search.text()) # 发送网站名网址，以及要搜索的文字

    # 当一级目录listWidget中的item被双击时
    def listWidget_category_first_double(self):
        def change_item(item):
            newItemName = item.text()
            if newItemName:
                db = QSqlDatabase.addDatabase('QSQLITE')
                db.setDatabaseName(self.path + '/multiWeb_Database.db')
                if db.open():
                    db.exec('update category set name="{}" where id={}'.format(newItemName, self.first_index))
                db.close()
            else:
                QMessageBox.critical(self, '错误', '输入不能为空', QMessageBox.Ok)
                self.listWidget_category_first.item(currentRow).setText(text)
        currentItem = self.listWidget_category_first.currentItem()
        currentRow = self.listWidget_category_first.currentRow()
        text = currentItem.text()
        currentItem.setFlags(currentItem.flags() | Qt.ItemIsEditable)
        self.listWidget_category_first.editItem(currentItem)
        self.listWidget_category_first.itemChanged.connect(lambda : change_item(self.listWidget_category_first.currentItem()))
    
    
    # 当二级目录listWidget中的item被双击时
    def listWidget_category_second_double(self):
        def change_item(currentItem):
            newItemName = currentItem.text()
            if newItemName:
                db = QSqlDatabase.addDatabase('QSQLITE')
                db.setDatabaseName(self.path + '/multiWeb_Database.db')
                if db.open():
                    db.exec('update category{} set name="{}" where id={}'.format(self.first_index, newItemName, self.second_index))
                db.close()
            else:
                QMessageBox.critical(self, '错误', '输入不能为空', QMessageBox.Ok)
                listWidget.item(currentRow).setText(text)
        listWidget = self.listWidget_category_list[self.first_index-1]
        currentItem = listWidget.currentItem()
        currentRow = listWidget.currentRow()
        text = currentItem.text()
        currentItem.setFlags(currentItem.flags() | Qt.ItemIsEditable)
        listWidget.editItem(currentItem)
        listWidget.itemChanged.connect(lambda : change_item(listWidget.currentItem()))

    # 当网址条目listWidget中的item被双击时
    def listWidget_webAddress_double(self):
        def change_item(currentItem):
            newItemName = currentItem.text()
            if newItemName:
                if len(newItemName.split('-----')) == 2:
                    name = newItemName.split('-----')[0]
                    url = newItemName.split('-----')[-1]
                    listWidget.closePersistentEditor(currentItem)
                    self.current_webAddress_list[currentRow] = name + '-----' + url
                    db = QSqlDatabase.addDatabase('QSQLITE')
                    db.setDatabaseName(self.path + '/multiWeb_Database.db')
                    if db.open():
                        db.exec('update webAddress set name="{}" where id={}'.format(name, id_index))
                        db.exec('update webAddress set url="{}" where id={}'.format(url, id_index))
                    db.close()
                else:
                    QMessageBox.critical(self, '错误', '网址名称与网址之间请用5个"-"连接', QMessageBox.Ok)
                    listWidget.item(currentRow).setText(txt)
            else:
                QMessageBox.critical(self, '错误', '输入不能为空', QMessageBox.Ok)
                listWidget.item(currentRow).setText(txt)

        QMessageBox.information(self, '提醒', '您正在进行编辑操作\n请按照示例的正确格式更改\n再次双击退出编辑', QMessageBox.Ok)
        key = '({},{})'.format(self.first_index, self.second_index)
        key = self.indexTuple_to_sqlIndexTuple[key]
        index = self.sqlIndex_to_webAddress_listWidgetIndex[key]
        listWidget = self.listWidget_webAddress_list[index-1]
        currentItem = listWidget.currentItem()
        txt = currentItem.text()
        currentRow = listWidget.currentRow()
        id_index = self.sqlIndexTuple_to_WebAddressIDLIST[key][currentRow]

        currentItem.setFlags(currentItem.flags() | Qt.ItemIsEditable)
        listWidget.editItem(currentItem)
        listWidget.itemChanged.connect(lambda : change_item(listWidget.currentItem()))


    # 当一级目录的item被切换时，切换到所对应的listWidget(二级目录)
    def category_widget_changed(self, i):
        i = i + 1       # 因为stackedWidget开始保留了一个原始的page，所以此处索引加1
        self.stackedWidget.setCurrentIndex(i)
        self.first_index = i
        self.second_index = 1
        if self.sign_out != 1:
            self.webAddress_widget_changed(self.second_index-1) # 切换一级目录时，自动选择二级目录的第一个item

    # 当二级目录的item被切换时，切换到所对应的listWidget(网址条目)
    def webAddress_widget_changed(self, i):
        i = i+ 1
        self.second_index = i
        key = '({},{})'.format(self.first_index, self.second_index)
        key = self.indexTuple_to_sqlIndexTuple[key]
        index = self.sqlIndex_to_webAddress_listWidgetIndex[key]
        self.current_webAddress_list = self.sqlIndexTuple_to_webAddress[key]
        self.stackedWidget_2.setCurrentIndex(index)
        if self.sign_out == 1:  # 如果此时是导出状态，执行写入文本框的操作
            self.add_to_textEdit()
    

    # 导出时，点击item，自动写入下方文本框的函数
    def add_to_textEdit(self):
        text = self.textEdit.toPlainText()
        categoryNmae_first = self.category[self.first_index-1]
        categoryNmae_second = self.categoryi[self.first_index-1][self.second_index-1]
        webAddress_list = self.current_webAddress_list
        text_add = '- {}\n  - {}\n'.format(categoryNmae_first, categoryNmae_second)
        for webAddress in webAddress_list:
            text_add += '    - {}\n'.format(webAddress)
        if not text_add in text:
            text += text_add
        self.textEdit.textChanged.disconnect(self.textEdit_text_changed)    # 不是手动更改时不提示
        self.textEdit.setText(text)
        self.textEdit.textChanged.connect(self.textEdit_text_changed)

    def generate_origin_database(self):
        db = QSqlDatabase.addDatabase('QSQLITE')
        db.setDatabaseName(self.path + '/multiWeb_Database.db')
        if db.open():
            query = QSqlQuery(db)
            query.exec('create table webAddress(id int primary key, name vhar, url vchar, category_first int, category_second int)')
            query.exec('create table category(id int primary key, name vhar)')
            query.exec('create table category1(id int primary key, name vhar)')
            query.exec('create table history(id int primary key, name vhar, url vhar)')
            query.exec('insert into webAddress values(1, "网址条目(搜狗搜索页)", "https://www.sogou.com/tx?query={}", 1, 1)')
            query.exec('insert into category values(1, "一级目录(示例)")')
            query.exec('insert into category1 values(1, "二级目录(示例)")')
        db.close()
    # 加载数据库函数
    def load_Database(self):
        sign = 0    # 用于判断db文件夹是否存在，一般第一次运行是没有的，则新建文件夹，并新建数据库
        if not os.path.exists(self.path):
            os.mkdir(self.path)
            sign = 1
        if not os.path.exists(self.path + '/multiWeb_Database.db'):
            sign = 1
        if sign:
            self.generate_origin_database()
        db = QSqlDatabase.addDatabase('QSQLITE')
        db.setDatabaseName(self.path + '/multiWeb_Database.db')
        if db.open():
            query = QSqlQuery(db)

            query.exec('select * from category')
            while query.next():
                index = query.value(0)
                s = query.value(1)
                self.listWidget_category_first.addItem(s)
                self.index_to_sqlIndex_first_list.append(index)
                self.category.append(s)
            self.id_category_first_max = max(self.index_to_sqlIndex_first_list)
                
            for j in self.index_to_sqlIndex_first_list:  # 遍历一级目录的id，因为数据库中二级目录的表名是根据一级目录id而来的
                l = []
                query.exec('select * from category'+str(j))
                categoryi = []
                while query.next():
                    index = query.value(0)
                    s = query.value(1)
                    categoryi.append(s)
                    l.append(index)
                self.index_to_sqlIndex_second_listes.append(l)
                self.id_category_second_max_list.append(max(l))
                self.categoryi.append(categoryi)
                if j > len(self.category):
                    break

            webAddress = []
            for i in range(5):
                query.exec('select * from webAddress')
                webs = []
                while query.next():
                    s = query.value(i)
                    webs.append(s)
                webAddress.append(webs)
            db.close()
            self.id_webAddress_max = max(webAddress[0])
            # 将数组转置，还原为数据库中的横向显示样式
            webAddress = [[row[i] for row in webAddress] for i in range(len(webAddress[0]))]
            # 创建Sql的indexTuple与name+网址的映射字典， 以及其与条目id的映射字典
            for row in webAddress:
                index = '({},{})'.format(row[3], row[4])
                if index not in self.sqlIndexTuple_to_webAddress.keys():
                    self.sqlIndexTuple_to_webAddress[index] = []
                    self.sqlIndexTuple_to_WebAddressIDLIST[index] = []
                self.sqlIndexTuple_to_webAddress[index].append(row[1] + '-----' + row[2])
                self.sqlIndexTuple_to_WebAddressIDLIST[index].append(row[0])
            # 创建listWidget的indexTuple与sql的indexTuple的映射字典
            for index, sqlIndex in enumerate(self.index_to_sqlIndex_first_list):
                index_to_sqlIndex_list = self.index_to_sqlIndex_second_listes[index]
                for ind, sqlInd in enumerate(index_to_sqlIndex_list):
                    self.indexTuple_to_sqlIndexTuple.update({'({},{})'.format(index+1, ind+1):'({},{})'.format(sqlIndex, sqlInd)})

    # 加载一级目录stackedWIdget，根据数据库的数据来确定其子分支的页数及内容
    def load_stackWidget1(self, category):
        for i in range(len(self.category)):
            listWidget = ListWidget()
            listWidget.addItems(self.categoryi[i])
            self.stackedWidget.addWidget(listWidget)
            listWidget.currentRowChanged.connect(self.webAddress_widget_changed)
            listWidget.doubleClicked.connect(self.listWidget_category_second_double)
            listWidget.signal.connect(self.listWidget_category_second_drop)
            listWidget.customContextMenuRequested.connect(self.listWidget_category_second_context)
            self.listWidget_category_list.append(listWidget)
        self.stackedWidget.setCurrentIndex(1)   # 将当前页设置为除了原始留的一页以外的第一页

    # 加载二级目录stackedWIdget_2，根据数据库的数据来确定其子分支的页数及内容
    def load_stackWidget2(self, categoryi):
        i = 1
        k = ''
        # 创建sqlIndexTuple对stackedWidget_2的序数
        for key in self.sqlIndexTuple_to_webAddress.keys():
            if k == '':
                k = key
            listWidget = ListWidget()
            listWidget.addItems(self.sqlIndexTuple_to_webAddress[key])
            listWidget.signal.connect(self.listWidget_webAddress_drop)
            listWidget.doubleClicked.connect(self.listWidget_webAddress_double)
            # listWidget.currentRowChanged.connect(self.webAddress_widget_row_changed)
            listWidget.customContextMenuRequested.connect(self.listWidget_webAddress_context)
            self.stackedWidget_2.addWidget(listWidget)
            self.listWidget_webAddress_list.append(listWidget)
            self.sqlIndex_to_webAddress_listWidgetIndex.update({key: i})
            i += 1
        key = '({},{})'.format(1, 1)
        key = self.indexTuple_to_sqlIndexTuple[key]
        index = self.sqlIndex_to_webAddress_listWidgetIndex[key]
        self.current_webAddress_list = self.sqlIndexTuple_to_webAddress[key]
        self.stackedWidget_2.setCurrentIndex(index)
        self.stackedWidget_2.setCurrentIndex(index)

    # 导入文本文件操作的函数
    def file_in(self):
        self.statusbar.showMessage('正在导入数据，请稍等.........')
        fileDialog = QFileDialog(self, filter="文本文件 (*.txt)")
        fileDialog.setWindowModality(Qt.WindowModal)
        fileDialog.exec_()
        if len(fileDialog.selectedFiles()) != 0:
            txtPath = fileDialog.selectedFiles()[0]
            self.set_in_widget_visible(True)
            self.thread = Worker(txtPath, self.path, self.id_category_first_max, self.id_webAddress_max, self)
            self.thread.signal_change_value.connect(lambda value: self.progressBar.setValue(value))
            self.thread.signal_update.connect(self.data_update)
            self.thread.signal_change_statusbar.connect(lambda message, time: self.statusbar.showMessage(message, time))
            self.thread.signal_set_in_widget_visiable.connect(self.set_in_widget_visible)
            self.thread.signal_critical.connect(lambda: QMessageBox.critical(self, '错误', '文本内容格式错误，请选择正确文件', QMessageBox.Ok))
            self.thread.start()
        else:
            self.statusbar.showMessage('')

    # 导出操作被点击的函数
    def file_out(self):
        self.set_out_widget_visible(True)
        self.textEdit.textChanged.connect(self.textEdit_text_changed)   # 更改文本框内容时会有善意提醒
        self.sign_out = 1   # 将导出信号改变
        self.listWidget_category_first.setCurrentRow(-1)  #将当前选中的listwidget条目给释放掉
        self.stackedWidget.setCurrentIndex(0)   # 将显示保留的原始页
        self.stackedWidget_2.setCurrentIndex(0)

    # 导出按钮被点击时，执行写入操作
    def pushButton_out_clicked(self):
        outPath = QFileDialog().getSaveFileName(self, 'save file', filter='(*.txt)')[0]
        if len(outPath) != 0:
            text = '###data###\n' + self.textEdit.toPlainText()
            with open(outPath, 'w', encoding='utf-8') as f:
                f.write(text)
            self.set_out_widget_visible(False)
            self.sign_out = 0
            self.statusbar.showMessage('导出完成', 5000)
        
    # 取消按钮被点击时
    def pushButton_cancel_clicked(self):
        self.textEdit.textChanged.disconnect(self.textEdit_text_changed)
        self.textEdit.clear()
        self.set_out_widget_visible(False)
        self.sign_out = 0
        self.listWidget_category_first.setCurrentRow(0)

    # 控制导出时显示的几个widget的显示与否
    def set_out_widget_visible(self, sign):
        self.textEdit.setVisible(sign)
        self.label_3.setVisible(sign)
        self.pushButton_out.setVisible(sign)
        self.pushButton_cancel.setVisible(sign)

    def set_in_widget_visible(self, sign):
        self.label_in.setVisible(sign)
        self.progressBar.setVisible(sign)


    # 将界面上显示的数据进行更新
    def data_update(self):
        # 先将所有的数据进行清除
        self.first_index = 1
        self.second_index = 1
        self.listWidget_category_first.currentRowChanged.disconnect(self.category_widget_changed)   # 由于clear()会触发函数，此处断开
        self.listWidget_category_first.clear()
        self.listWidget_category_first.currentRowChanged.connect(self.category_widget_changed)
        for widget in self.listWidget_category_list:
            self.stackedWidget.removeWidget(widget)
        self.listWidget_category_list.clear()
        for widget in self.listWidget_webAddress_list:
            self.stackedWidget_2.removeWidget(widget)
        self.listWidget_webAddress_list.clear()
        self.sqlIndexTuple_to_webAddress.clear()
        self.indexTuple_to_sqlIndexTuple.clear()
        self.sqlIndex_to_webAddress_listWidgetIndex.clear()
        self.category.clear()
        self.categoryi.clear()
        self.sqlIndexTuple_to_WebAddressIDLIST.clear()
        self.current_webAddress_list.clear()
        self.sign_out = 0
        self.index_to_sqlIndex_first_list.clear()
        self.index_to_sqlIndex_second_listes.clear()

        # 重新加载
        self.load_Database()
        self.load_stackWidget1(self.category)
        self.load_stackWidget2(self.categoryi)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    web = Web()
    web.setWindowTitle('网页')
    mainWindow = MainWindow()
    mainWindow.setWindowTitle('多网页搜索工具')

    mainWindow.signal.connect(web.add_new_tab)
    web.signal.connect(lambda : mainWindow.setVisible(True))

    web.show()
    web.setVisible(False)
    mainWindow.show()
    sys.exit(app.exec_())

