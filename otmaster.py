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
        self.allotted_hours = 0.0
        self.allotted_ot = 0.0
        self.same_hours_as_group = True
        # {date: [[datetime_start, datetime_end], [datetime_start, datetime_end], ...]}
    
    def get_total_hours(self, date1=None, date2=None):
        total_hours = datetime.timedelta(hours=0)
        if date1 is None:
            # Get total hours for all time
            for date, hours in self.hour_inputs.items():
                for hour in hours:
                    total_hours += datetime.datetime.combine(date, hour[1]) - datetime.datetime.combine(date, hour[0])
        elif date1 and not date2:
            # Get total hours for a single date
            if date1 in self.hour_inputs:
                for hour in self.hour_inputs[date1]:
                    total_hours += datetime.datetime.combine(date1, hour[1]) - datetime.datetime.combine(date1, hour[0])
        elif date1 and date2:
            # Get total hours for a range of dates
            for date, hours in self.hour_inputs.items():
                if date >= date1 and date <= date2:
                    for hour in hours:
                        total_hours += datetime.datetime.combine(date, hour[1]) - datetime.datetime.combine(date, hour[0])
        
        return total_hours


class Group():
    def __init__(self, name):
        self.name = name
        self.persons = []
        self.allotted_hours = 0.0
        self.allotted_ot = 0.0
        # [Person]
    
    def get_total_hours(self, date=None):
        if date is None:
            # Get total hours for all time
            total_hours = datetime.timedelta(hours=0)
            for person in self.persons:
                total_hours += person.get_total_hours()
            return total_hours
        else:
            # Get total hours for a single date
            total_hours = datetime.timedelta(hours=0)
            for person in self.persons:
                total_hours += person.get_total_hours(date)
            return total_hours


class OTMaster(QtWidgets.QMainWindow):
    def __init__(self):
        super(OTMaster, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.groups = {}
        # {groupobject: [personobject1, personobject2, ...]}
        
        self.current_group = None
        self.current_user = None

        self.setup_triggers()
    
    def setup_triggers(self):
        self.ui.add_timeclock_btn.clicked.connect(self.add_timeclock)
    
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
    
    def add_timeclock_to_db(self, date, start_time, end_time):
        if self.current_user is None:
            error_message("Error", "No user is currently selected")
            return
        self.person.hour_inputs[date] = [start_time, end_time]
    
    def submit_timeclock(self, dialog, date_enter, start_time_enter, end_time_enter):
        date = date_enter.date().toPyDate()
        start_time = start_time_enter.time().toPyTime()
        end_time = end_time_enter.time().toPyTime()
        dialog.close()
        # convert total time worked to timedelta
        time_worked = datetime.datetime.combine(date, end_time) - datetime.datetime.combine(date, start_time)
        self.add_timeclock_to_db(date, start_time, end_time)
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
        date_enter = QtWidgets.QDateEdit(dialog)
        start_time_enter = QtWidgets.QTimeEdit(dialog)
        end_time_enter = QtWidgets.QTimeEdit(dialog)
        date_enter.setDate(datetime.datetime.now().date())
        start_time_enter.setTime(datetime.datetime.now().time())
        end_time_enter.setTime(datetime.datetime.now().time())
        date_enter.setCalendarPopup(True)
        start_time_enter.setCalendarPopup(True)
        end_time_enter.setCalendarPopup(True)
        date_enter.setDisplayFormat("MM/dd/yyyy")
        start_time_enter.setDisplayFormat("HH:mm")
        end_time_enter.setDisplayFormat("HH:mm")
        date_enter.setGeometry(QtCore.QRect(10, 10, 200, 30))
        start_time_enter.setGeometry(QtCore.QRect(10, 50, 200, 30))
        end_time_enter.setGeometry(QtCore.QRect(10, 90, 200, 30))
        submit_btn = QtWidgets.QPushButton(dialog)
        submit_btn.setText("Submit")
        submit_btn.setGeometry(QtCore.QRect(10, 130, 200, 30))
        submit_btn.clicked.connect(lambda: self.submit_timeclock(dialog, date_enter, start_time_enter, end_time_enter))
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
