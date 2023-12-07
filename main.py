from PyQt5.QtWidgets import QApplication, QPushButton, QFileDialog, QVBoxLayout, QWidget, QTableView, QComboBox, QLineEdit, QMessageBox, QLabel, QHBoxLayout
from PyQt5.QtSql import QSqlDatabase, QSqlQuery, QSqlTableModel, QSqlError
from PyQt5.QtCore import QSortFilterProxyModel, Qt
from PyQt5.QtGui import QIcon
import csv
import sys

db = None
model = None

def open_database():
    global db
    file_name, _ = QFileDialog.getOpenFileName(None, "Open SQLite file", "", "SQLite files (*.db *.sqlite *.db3 *.sdb)")
    if file_name:
        db = QSqlDatabase.addDatabase("QSQLITE")
        db.setDatabaseName(file_name)
        if not db.open():
            error = db.lastError()
            if error.type() != QSqlError.NoError:
                print("Error opening database: ", error.text())
            return
        query = QSqlQuery("SELECT name FROM sqlite_master WHERE type='table';")
        if not query.isActive():
            error = query.lastError()
            if error.type() != QSqlError.NoError:
                print("Error executing query: ", error.text())
            return
        table_selector.clear()
        while query.next():
            table_name = query.value(0)
            table_selector.addItem(table_name)
            filter_column_selector.clear()
            filter_column_selector.addItems([model.headerData(i, Qt.Horizontal) for i in range(model.columnCount())])


def close_database():
    global db
    if db is not None and db.isOpen():
        db.close()
        QSqlDatabase.removeDatabase(db.connectionName())
        db = None

def display_table(table_name):
    global model
    model = QSqlTableModel(db=db)
    model.setTable(table_name)
    model.select()
    proxy_model.setSourceModel(model)
    filter_column_selector.clear()
    filter_column_selector.addItems([model.headerData(i, Qt.Horizontal) for i in range(model.columnCount())])

def set_filter():
    filter_text = filter_edit.text()
    filter_column = filter_column_selector.currentIndex()
    proxy_model.setFilterKeyColumn(filter_column)
    proxy_model.setFilterRegExp(filter_text)

def delete_record():
    selection_model = table_view.selectionModel()
    if selection_model.hasSelection():
        selected_rows = selection_model.selectedRows()
        if selected_rows:
            selected_row = proxy_model.mapToSource(selected_rows[0]).row()
            model.removeRow(selected_row)
            model.submitAll()
        else:
            QMessageBox.information(None, "No selection", "No row is selected.")
    else:
        QMessageBox.information(None, "No selection", "No row is selected.")

def save_changes():
    if model is not None:
        model.submitAll()
    else:
        QMessageBox.information(None, "No model", "No model is available.")

def export_to_csv():
    file_name, _ = QFileDialog.getSaveFileName(None, "Save CSV", "", "CSV files (*.csv)")
    if file_name:
        with open(file_name, 'w', newline='') as file:
            writer = csv.writer(file)
            query = QSqlQuery(db)
            query.exec_("SELECT * FROM " + model.tableName())
            writer.writerow([query.record().fieldName(i) for i in range(query.record().count())])
            while query.next():
                writer.writerow([query.value(i) for i in range(query.record().count())])


app = QApplication(sys.argv)
app.setWindowIcon(QIcon('./icon.ico'))

button = QPushButton("Open SQLite file")
button.clicked.connect(open_database)

table_selector = QComboBox()
table_selector.currentTextChanged.connect(display_table)

table_selector_label = QLabel("Select Table:")

hlayout = QHBoxLayout()
hlayout.addWidget(table_selector_label)
hlayout.addWidget(table_selector)

filter_edit = QLineEdit()
filter_edit.textChanged.connect(set_filter)

filter_column_selector = QComboBox()

filter_label = QLabel("Filter:")

filter_layout = QHBoxLayout()
filter_layout.addWidget(filter_label)
filter_layout.addWidget(filter_edit)
filter_layout.addWidget(filter_column_selector)

delete_button = QPushButton("Delete Record")
delete_button.clicked.connect(delete_record)

save_button = QPushButton("Save Changes")
save_button.clicked.connect(save_changes)

export_button = QPushButton("Export to CSV")
export_button.clicked.connect(export_to_csv)

proxy_model = QSortFilterProxyModel()
table_view = QTableView()
table_view.setModel(proxy_model)
table_view.setSortingEnabled(True)

layout = QVBoxLayout()
layout.addWidget(button)
layout.addLayout(hlayout)
layout.addLayout(filter_layout)
layout.addWidget(table_view)
layout.addWidget(delete_button)
layout.addWidget(save_button)
layout.addWidget(export_button)


window = QWidget()
window.setLayout(layout)
window.resize(1000, 750)
window.setWindowTitle("🐍 SQL Browser 📑")
window.setWindowIcon(QIcon('./icon.ico'))
window.show()

app.exec_()

close_database()

sys.exit()