from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtWebEngineWidgets import *
from PyQt5.QtSql import QSqlDatabase, QSqlQuery

class Worker(QThread):
    signal_change_value = pyqtSignal(int)
    signal_update = pyqtSignal()
    signal_change_statusbar = pyqtSignal(str, int)
    signal_set_in_widget_visiable = pyqtSignal(bool)
    signal_critical = pyqtSignal()

    def __init__(self, txtPath, self_path, self_id_category_first_max, self_id_webAddress_max, parent=None):
        super(Worker, self).__init__(parent)
        self.txtPath = txtPath
        self.path = self_path
        self.id_category_first_max = self_id_category_first_max
        self.id_webAddress_max = self_id_webAddress_max
        self.value = 0

    def run(self):
        self.file_in2()


    def file_in2(self):
        sign = 1
        text = ''
        with open(self.txtPath, 'r', encoding='utf-8') as f:
            count = len(f.readlines())*5
            f.seek(0)
            lineOne = f.readline()
            if lineOne != '###data###\n':
                self.signal_critical.emit()
                sign = 0
            if sign == 1:
                i = 0
                while True:
                    self.signal_change_value.emit(int((self.value)*100))
                    self.value = i/count
                    i += 1
                    t = f.readline()
                    if len(t.strip()) == 0: # 读到空行则跳出
                        break
                    text += t
        if text:
            sign = self.add_to_database(text)   # 将读取到的文本数据交给add_to_database函数处理
            self.signal_change_value.emit(100)
            # 根据处理的结果来显示状态栏的消息
            if sign:
                self.signal_change_statusbar.emit('导入完成', 5000)
                self.signal_update.emit()
            else:
                self.signal_change_statusbar.emit('写入数据库失败, 请重试', 5000)
            self.signal_set_in_widget_visiable.emit(False)
        else:
            self.signal_change_statusbar.emit('', 1)
            self.signal_set_in_widget_visiable.emit(False)


        # 导入时执行此操作, 先写入数据库，成功则返回TRUE，失败则返回FALSE
    def add_to_database(self, text):
        # 首先对text进行处理，方便写入数据库
        lines = text.split('\n')
        if '' in lines:
            lines.remove('')
        count = len(lines)*3
        category_first = []
        for line in lines:
            if line[0] == '-' and line[2:] not in category_first:
                category_first.append(line[2:])
        category_second = []
        webAddress_name_list =[]
        sign = 0
        j1 = 0
        j2 = 0
        for i, line in enumerate(lines):
            self.signal_change_value.emit(int((self.value+i/count)*100))
            diff1 = len(line) - len(line.strip())
            if sign == 0:
                if diff1 == 0:
                    sign = 1
                    j1 = category_first.index(line[2:])
                    continue
            if sign == 1:
                if diff1 == 2:
                    if len(category_second) > j1:
                        category_second[j1].append(line[4:])
                        j2 = len(category_second[j1]) - 1
                    else:
                        category_second.insert(j1, [line[4:]])
                        j2 = 0
                elif diff1 == 4:
                        name = line[6:].split('-----')[0]
                        webAddress = line[6:].split('-----')[1]
                        webAddress_name_list.append([name, webAddress, j1, j2])
                if i + 1 == len(lines):
                    break
                if len(lines[i+1]) - len(lines[i+1].strip()) == 0:
                    sign = 0  
    
        # 将整理好的数据依次写入数据库
        try:
            db = QSqlDatabase.addDatabase('QSQLITE')
            db.setDatabaseName(self.path + '/multiWeb_Database.db')
            if db.open():
                query = QSqlQuery(db)
                query.exec('select id from webAddress')
                webAddress_id_max = 0
                while query.next():
                    index = query.value(0)
                    if index > webAddress_id_max:
                        webAddress_id_max = index
                query.exec('select id from category')
                category_id_max = 0
                while query.next():
                    index = query.value(0)
                    if index > category_id_max:
                        category_id_max = index
                for i, item in enumerate(webAddress_name_list):
                    query.exec('insert into webAddress values({}, "{}", "{}", {}, {})'.format(
                        i + self.id_webAddress_max + 1, item[0], item[1], item[2] + self.id_category_first_max + 1, item[3] + 1
                    ))
                self.signal_change_value.emit(96)
                for i, item in enumerate(category_first):
                    index = i + self.id_category_first_max + 1
                    query.exec('insert into category values({}, "{}")'.format(index, item))
                    query.exec('create table category{}(id int primary key, name vhar)'.format(index))
                    for j, itm in enumerate(category_second[i]):
                        query.exec('insert into category{} values({}, "{}")'.format(index, j+1, itm))
                    
            db.close()

        except:
            return False
        else:
            return True
