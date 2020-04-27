from PyQt5.QtWidgets import QListWidget, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QSplitter, QApplication, QMessageBox
from PyQt5.QtSql import QSqlDatabase, QSqlQuery
from PyQt5.QtCore import pyqtSignal, Qt, QUrl
from PyQt5.QtGui import QIcon
from PyQt5.QtWebEngineWidgets import QWebEngineView

import os
import sys

from Ui_showWeb import Ui_MainWindow as Ui_ShowWeb

from custom_widget import LineEdit
import back_to_first_page_image
import delete_history_image


class Web(QMainWindow, Ui_ShowWeb):
    signal_change_stackedWidget = pyqtSignal()

    '''生成批量浏览网页的界面 '''
    def __init__(self, parent=None):
        super(Web, self).__init__(parent)
        self.setupUi(self)
        self.tabWidget.removeTab(1)
        self.tabWidget.removeTab(0)
        if not os.path.exists('./asserts'):
            os.mkdir('./asserts')
            back_to_first_page_image.save('asserts/首页.png')
            delete_history_image.save('asserts/删除历史记录.png')
        self.action_back.setIcon(QIcon('asserts/首页.png'))
        self.action_delete_history.setIcon(QIcon('asserts/删除历史记录.png'))

        self.path = './db/multiWeb_Database.db'

        self.lineEdit_url_list = [] # 每一个tab的网址框
        self.browser_list = []  # 每一个tab的webEngineView
        self.listWidget_list = []   # 每一个tab的目录listWidget
        self.listWidget_history = QListWidget()
        self.webAddress_LIST = []   # 保存每次主程序发送来的网址数据
        self.webAddress_history_list = []
        
        self.tabWidget.tabCloseRequested.connect(self.tab_close)
        self.listWidget_history.currentRowChanged.connect(self.change_to_history)
        self.action_back.triggered.connect(self.action_back_triggerd)
        self.action_delete_history.triggered.connect(self.action_delete_history_triggerd)

    def action_back_triggerd(self):
        self.signal_change_stackedWidget.emit()

    def action_delete_history_triggerd(self):
        sign = QMessageBox.information(self, '删除历史记录', '是否删除所有历史记录\n删除后无法找回', QMessageBox.Ok)
        if sign:
            db = QSqlDatabase.addDatabase('QSQLITE')
            db.setDatabaseName(self.path)
            if db.open():
                query = QSqlQuery(db)
                query.exec('drop table if exists history')
                query.exec('create table history(id int primary key, name vhar, url vhar)')
                # for i in range(len(self.webAddress_history_list)):
                #     self.listWidget_history.takeItem(0)
                self.listWidget_history.clear()
                self.webAddress_history_list.clear()
            db.close()
        
    def url_changeed(self):
        index = self.tabWidget.currentIndex()
        i = self.listWidget_list[index].currentRow()
        if i == -1:
            i = 0
        url = self.lineEdit_url_list[index].text()
        self.webAddress_LIST[index][i] = url
        browser = self.browser_list[index]
        browser.setUrl(QUrl(url))

    def lineEdit_enterd(self):
        self.url_changeed()

    def setTabText_and_to_history(self, i, browser):
        title = browser.page().title()
        url = browser.url().toString()
        self.tabWidget.setTabText(i, title[0: 30])
        if url.strip() != '' and title.strip() != '':
            self.listWidget_history.addItem(title[0:50])
            self.webAddress_history_list.append(url)
            self.write_history_to_database(title[0:50], url)
    
    def write_history_to_database(self, name, url):
        db = QSqlDatabase.addDatabase('QSQLITE')
        db.setDatabaseName(self.path)
        if db.open():
            query = QSqlQuery(db)
            query.exec('insert into history values({}, "{}", "{}")'.format(len(self.webAddress_history_list), str(name), str(url)))
        db.close()

    def load_history_from_database(self):
        name_list = []
        url_list = []
        db = QSqlDatabase.addDatabase('QSQLITE')
        db.setDatabaseName(self.path)
        if db.open():
            query = QSqlQuery(db)
            query.exec('select name, url from history')
            while query.next():
                name_list.append(str(query.value(0)))
                url_list.append(str(query.value(1)))
        db.close()
        return name_list, url_list

    def change_to_history(self, i):
        index = self.tabWidget.currentIndex()
        url = self.webAddress_history_list[i]
        browser = self.browser_list[index]
        browser.setUrl(QUrl(url))

    def pushButton_copy_clicked(self):
        index = self.tabWidget.currentIndex()
        textEdit = self.lineEdit_url_list[index]
        clipboard = QApplication.clipboard()
        clipboard.setText(textEdit.text())
    
    def tab_close(self, i):
        self.tabWidget.removeTab(i)
        self.lineEdit_url_list.remove(self.lineEdit_url_list[i])
        self.browser_list.remove(self.browser_list[i])
        self.webAddress_LIST.remove(self.webAddress_LIST[i])
        self.listWidget_list.remove(self.listWidget_list[i])
        if self.tabWidget.count() < 1:
            self.signal_change_stackedWidget.emit()
        

    def add_new_tab(self, webAddress_name_list, text):
        self.setVisible(True)
        widget = QWidget()
        layout = QVBoxLayout()
        layout_h = QHBoxLayout()
        splitter = QSplitter()
        splitter.setOrientation(Qt.Horizontal)
        listWidget = QListWidget()
        listWidget.setCurrentRow(0)
        browser = QWebEngineView()
        lineEdit_url = LineEdit()
        pushButton_copy = QPushButton('复制网址')
        splitter.addWidget(listWidget)
        splitter.addWidget(browser)
        splitter.addWidget(self.listWidget_history)
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 8)
        splitter.setStretchFactor(2, 1)
        layout_h.addWidget(lineEdit_url)
        layout_h.addWidget(pushButton_copy)
        layout.addLayout(layout_h)
        layout.addWidget(splitter)
        widget.setLayout(layout)

        self.lineEdit_url_list.append(lineEdit_url)
        self.browser_list.append(browser)
        self.listWidget_list.append(listWidget)
        name_list, self.webAddress_history_list = self.load_history_from_database()
        self.listWidget_history.addItems(name_list)

        listWidget.currentRowChanged.connect(self.listWidget_changed)
        lineEdit_url.returnPressed.connect(self.lineEdit_enterd)
        pushButton_copy.clicked.connect(self.pushButton_copy_clicked)

        webAddress_list = [address.split('-----')[1].format(text) for address in webAddress_name_list]
        self.webAddress_LIST.append(webAddress_list)
        webName_list = [address.split('-----')[0] for address in webAddress_name_list]
        url = webAddress_list[0]
        listWidget.addItems(webName_list)
        browser.setUrl(QUrl(url))
        lineEdit_url.setText(url)
        i = self.tabWidget.addTab(widget, 'loading')
        browser.urlChanged.connect(lambda qurl, browser=browser:
                                   lineEdit_url.setText(qurl.toString()))
        browser.loadFinished.connect(lambda _, i=i, browser=browser:
                                     self.setTabText_and_to_history(i, browser))
        self.tabWidget.setCurrentIndex(i)
    

    def listWidget_changed(self, i):
        index = self.tabWidget.currentIndex()
        browser = self.browser_list[index]
        url = self.webAddress_LIST[index][i]
        browser.setUrl(QUrl(url))
        lineEdit = self.lineEdit_url_list[index]
        lineEdit.setText(url)

        