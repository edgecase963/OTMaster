from distutils.log import error
from PyQt5 import QtCore, QtGui, QtWidgets
from MainWindow import Ui_MainWindow
import pickle
import datetime



def warning_message(title, message):
    msg = QtWidgets.QMessageBox()
    msg.setIcon(QtWidgets.QMessageBox.Warning)
    msg.setText(message)
    msg.setWindowTitle(title)
    msg.setStandardButtons(QtWidgets.QMessageBox.Ok)
    msg.exec_()

def error_message(title, message):
    msg = QtWidgets.QMessageBox()
    msg.setIcon(QtWidgets.QMessageBox.Critical)
    msg.setText(message)
    msg.setWindowTitle(title)
    msg.setStandardButtons(QtWidgets.QMessageBox.Ok)
    msg.exec_()


class Person():
    def __init__(self, name, group):
        self.name = name
        self.group = group
        self.hour_inputs = {}
        # {start_datetime: end_datetime, ...}
        self.allotted_hours = 0.0
        self.allotted_ot = 0.0
        self.same_hours_as_group = True
    
    def get_total_hours(self, date1=None, date2=None):
        total_hours = datetime.timedelta(hours=0)
        if date1 is None:
            # Get total hours for all time
            for start_time in self.hour_inputs:
                end_time = self.hour_inputs[start_time]
                total_hours += end_time - start_time
        elif date1 and not date2:
            # Get total hours for a single day
            for start_time in self.hour_inputs:
                end_time = self.hour_inputs[start_time]
                if start_time.date() == date1:
                    total_hours += end_time - start_time
                    if end_time.date() > date1:
                        # Subtract the hours that bled over
                        total_hours -= end_time.replace(hour=0, minute=0, second=0, microsecond=0) - start_time
        elif date1 and date2:
            # Get total hours for a range of days
            for start_time in self.hour_inputs:
                end_time = self.hour_inputs[start_time]
                if start_time.date() >= date1 and start_time.date() <= date2:
                    total_hours += end_time - start_time
                    if end_time.date() > date2:
                        # Subtract the hours that bled over
                        total_hours -= end_time - date2


class Group():
    def __init__(self, name):
        self.name = name
        self.persons = {}
        # {name: Person}
        self.allotted_hours = 0.0
        self.allotted_ot = 0.0
    
    def get_total_hours(self, date=None):
        if date is None:
            # Get total hours for all time
            total_hours = datetime.timedelta(hours=0)
            for name in self.persons:
                person = self.persons[name]
                total_hours += person.get_total_hours()
            return total_hours
        else:
            # Get total hours for a single date
            total_hours = datetime.timedelta(hours=0)
            for name in self.persons:
                person = self.persons[name]
                total_hours += person.get_total_hours(date)
            return total_hours


class OTMaster(QtWidgets.QMainWindow):
    def __init__(self):
        super(OTMaster, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.groups = {}
        # {group_name: Group}
        
        self.timeclock_view = {}
        # Parameters in this dictionary are set when the user decides to view timeclocks
        # They are temporary
        
        self.current_group = None
        self.current_user = None

        self.setup_triggers()
    
    def setup_triggers(self):
        self.ui.add_timeclock_btn.clicked.connect(self.add_timeclock)
        self.ui.view_timeclocks_btn.clicked.connect(self.view_timeclocks)

        self.ui.add_group_btn.clicked.connect(self.add_group)
        self.ui.group_input.returnPressed.connect(self.add_group)

        self.ui.add_person_btn.clicked.connect(self.add_person)
        self.ui.name_input.returnPressed.connect(self.add_person)
        
        self.ui.group_list.clicked.connect(lambda: self.select_group())
        self.ui.name_list.clicked.connect(lambda: self.select_person())
    
    def select_group(self, group_name=None):
        if group_name is None:
            group_name = self.ui.group_list.currentItem().text()
        
        self.current_group = self.groups[group_name]
        self.ui.name_list.clear()
        for name in self.current_group.persons:
            person = self.current_group.persons[name]
            self.ui.name_list.addItem(person.name)
        self.ui.name_list.sortItems()
        self.ui.name_list.setCurrentRow(0)

        self.ui.allotted_group_hours.setValue(self.current_group.allotted_hours)
        self.ui.allotted_group_ot.setValue(self.current_group.allotted_ot)
        self.ui.group_name_val.setText(group_name)
        
        self.current_user = None
    
    def select_person(self, person_name=None):
        if person_name is None:
            person_name = self.ui.name_list.currentItem().text()
        
        self.current_user = self.current_group.persons[person_name]
        self.ui.person_name_val.setText(person_name)

        # Set selection box to the first option
        self.ui.hours_used_combo_box.setCurrentIndex(0)

        total_hours, total_ot = self.current_user.get_total_hours()
        self.ui.hours_used_val.setText(str(total_hours))
        self.ui.total_ot_used_val.setText(str(total_ot))
    
    def add_group(self):
        group_name = self.ui.group_input.text()
        # Clear input field
        self.ui.group_input.setText("")
        if group_name == "":
            return
        
        new_group = Group(group_name)
        self.groups[group_name] = new_group
        self.ui.group_list.addItem(group_name)
        # sort the list
        self.ui.group_list.sortItems()

        # Select the new group
        self.select_group(group_name)
    
    def add_person(self):
        person_name = self.ui.name_input.text()
        if person_name == "":
            return
        
        if not self.current_group:
            error_message("Error", "No group is currently selected")
            return

        # Clear input field
        self.ui.name_input.setText("")
        
        new_person = Person(person_name, self.current_group)
        self.current_group.persons[person_name] = new_person
        self.ui.name_list.addItem(person_name)

        # sort the list
        self.ui.name_list.sortItems()
        
        self.select_person(person_name)
    
    def view_timeclocks(self):
        # Create new dialog containing a list of all timeclocks for the selected person
        if not self.current_user:
            error_message("Error", "No employee is currently selected")
            return
        
        dialog = QtWidgets.QDialog()
        dialog.setWindowTitle("Timeclocks for " + self.current_user.name)
        dialog.setFixedSize(400, 400)
        dialog.setLayout(QtWidgets.QVBoxLayout())
        listWidget = QtWidgets.QListWidget()
        dialog.layout().addWidget(listWidget)
        
        for dt in self.current_user.hour_inputs:
            listWidget.addItem(str(dt))
            self.timeclock_view[str(dt)] = dt
        
        # Create a right click menu for the list
        listWidget.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        timeclocks_menu = QtWidgets.QMenu()
        timeclocks_menu.addAction("Delete", lambda: self.delete_timeclock(listWidget.currentItem()))
        listWidget.customContextMenuRequested.connect(lambda pos: timeclocks_menu.exec_(listWidget.mapToGlobal(pos)))
        
        dialog.exec_()
    
    def delete_timeclock(self, item):
        if not item:
            return
        
        if not item.text() in self.timeclock_view:
            error_message("Error", "Unable to delete timeclock")
            return
        dt = self.timeclock_view[item.text()]
        self.current_user.hour_inputs.pop(dt)
        item.setHidden(True)
    
    def save_db(self):
        # Prompt user for file location
        def open_file(self):
            file_name = QtWidgets.QFileDialog.getSaveFileName(self, "Save Database", "", "Pickle Files (*.pkl)")
            if file_name[0]:
                with open(file_name[0], "wb") as f:
                    pickle.dump(self.groups, f)
                print("Saved database to " + file_name[0])

        open_file(self)
    
    def update_gui(self):
        if self.current_group is not None:
            self.ui.group_name_val.setText(self.current_group.name)
            self.ui.allotted_group_hours.setValue(self.current_group.allotted_hours)
            self.ui.allotted_group_ot.setValue(self.current_group.allotted_ot)
        else:
            self.ui.group_name_val.setText("No group selected")
            self.ui.allotted_group_hours.setValue(0.0)
    
    def add_timeclock_to_db(self, start_time, end_time):
        if self.current_user is None:
            error_message("Error", "No user is currently selected")
            return
        self.current_user.hour_inputs[start_time] = end_time
    
    def submit_timeclock(self, dialog, start_time_entry, end_time_entry):
        start_time = start_time_entry.dateTime().toPyDateTime()
        end_time = end_time_entry.dateTime().toPyDateTime()

        dialog.close()
        # convert total time worked to timedelta
        total_shift_time = end_time - start_time
        print("Total time worked: " + str(total_shift_time))
        self.add_timeclock_to_db(start_time, end_time)
        self.update_gui()
    
    def add_timeclock(self):
        # Prompt user with a date and time for the user
        # Also prompt user for when the person clocked in and out
        dialog = QtWidgets.QDialog()
        dialog.setWindowTitle("Add Timeclock")
        dialog.setFixedSize(300, 200)
        dialog.setWindowFlags(QtCore.Qt.WindowCloseButtonHint)
        dialog.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        dialog.setWindowFlags(QtCore.Qt.WindowSystemMenuHint)
        dialog.setWindowFlags(QtCore.Qt.WindowTitleHint)
        dialog.setWindowFlags(QtCore.Qt.WindowType_Mask)
        dialog.setWindowFlags(QtCore.Qt.Window)
        # Set the layout of the dialog
        dialog.setLayout(QtWidgets.QVBoxLayout())
        
        # Add start time label
        start_time_label = QtWidgets.QLabel("Start Time")
        dialog.layout().addWidget(start_time_label)
        
        # Add a date/time entry
        start_time_entry = QtWidgets.QDateTimeEdit(dialog)
        start_time_entry.setDisplayFormat("MM/dd/yyyy hh:mm:ss")
        dialog.layout().addWidget(start_time_entry)
        start_time_entry.setCalendarPopup(True)
        start_time_entry.setDateTime(QtCore.QDateTime.currentDateTime())
        
        # Add end time label
        end_time_label = QtWidgets.QLabel("End Time")
        dialog.layout().addWidget(end_time_label)
        
        # Add a date/time entry
        end_time_entry = QtWidgets.QDateTimeEdit(dialog)
        end_time_entry.setDisplayFormat("MM/dd/yyyy hh:mm:ss")
        dialog.layout().addWidget(end_time_entry)
        end_time_entry.setCalendarPopup(True)
        end_time_entry.setDateTime(QtCore.QDateTime.currentDateTime())
        
        # Add a button to submit the timeclock
        submit_button = QtWidgets.QPushButton("Submit", dialog)
        submit_button.clicked.connect(
            lambda: self.submit_timeclock(dialog, start_time_entry, end_time_entry))
        dialog.layout().addWidget(submit_button)
        dialog.exec_()
    
    def start(self):
        self.show()
        self.raise_()
        self.activateWindow()



if __name__ == "__main__":
    app = QtWidgets.QApplication([])
    window = OTMaster()
    window.start()
    app.exec_()
