from PyQt5 import QtCore
from PyQt5 import Qt
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from encryption import MessageEndecryptor
from message_retrieval import MessageRetriever

# TODO: Add app name to config file
app_name = "U-Boat Secure Messenging"
# TODO: Allow setting mail2news and remailer from UI
mail2news = "mail2news@dizum.com"

def get_password(caption):
    """Show a password dialog and return the password if one is
    entered.

    """
    
    text, ok = QInputDialog.getText(None,
                                    "Password Entry",
                                    caption,
                                    QLineEdit.Password)

    if ok:
        return text
    else:
        return None


class UBoatNewMessageWindow(QWidget):
    """A window for composing a new message"""
    
    def __init__(self, endecryptor, sender):
        QWidget.__init__(self)

        self.setMinimumSize(800, 480)
        self.setWindowTitle(app_name + ": New Message")

        self.endecryptor = endecryptor
        
        self.main_vbox = QVBoxLayout()
        
        self.setLayout(self.main_vbox)

        self.to_hbox = QHBoxLayout()
        
        self.to = QComboBox()

        # now that there's a combo for them, add the row values
        self.show_contacts()
        
        self.to_hbox.addWidget(QLabel("To: "), stretch=0.0)
        self.to_hbox.addWidget(self.to, stretch=1.0)

        self.main_vbox.addLayout(self.to_hbox)

        # the thing into which the message text is typed --- there is
        # no special formatting (links, etc.) allowed
        self.message_text = QTextEdit()

        self.main_vbox.addWidget(self.message_text)

        self.button_hbox = QHBoxLayout()

        self.send_btn = QPushButton("Send")

        # push the send button to the far right
        self.button_hbox.addStretch()
        self.button_hbox.addWidget(self.send_btn)

        self.main_vbox.addLayout(self.button_hbox)

    def show_contacts(self):
        """Add the contacts to the To: combobox"""
        
        self.contact_model = QStandardItemModel(self.to)

        # set up columns and headers
        self.contact_model.setColumnCount(1)

        # add messages to the model in order
        for contact in self.endecryptor.recipients():
            uid = QStandardItem(str(contact["uid"]))
            self.contact_model.appendRow([uid])

        self.to.setModel(self.contact_model)

        

    
class UBoatMainWindow(QMainWindow):
    """The main window of the U-Boat application."""

    # signals emitted on UI events
    message_view_signal =  QtCore.pyqtSignal(
        [dict],
        name="messageViewRequested")
    
    compose_signal = QtCore.pyqtSignal(name="composeClicked")
    contacts_signal = QtCore.pyqtSignal(name="contactsViewClicked")
    settings_signal = QtCore.pyqtSignal(name="settingsClicked")
    check_messages_signal = QtCore.pyqtSignal(name="checkMessagesClicked")

    @QtCore.pyqtSlot(dict)
    def handleMessage(self, message_dict):
        """Accepts a message dict with keys id, subject, and post_date, and
        displays it in the list of incoming messages

        """
        self.messages = [message_dict,] + self.messages
        self.show_messages()
    
    def __init__(self):
        QMainWindow.__init__(self)

        self.setMinimumSize(800, 480)
        self.setWindowTitle(app_name)
        
        self.set_up_controls()

        # start with no messages
        self.messages = []
        
        self.show_messages()

    def set_up_controls(self):
        """Add controls to the main window"""
        
        # rough layout items
        self.main_wid = QWidget()
        self.main_hbox = QHBoxLayout()
        self.button_vbox = QVBoxLayout()
        self.message_vbox = QVBoxLayout()

        # L.H. side buttons to launch other forms
        self.compose_btn = QPushButton("New &message", self)
        self.contacts_btn = QPushButton("&Contacts", self)
        self.options_btn = QPushButton("Sending &options", self)

        # make the left-panel buttons emit top-level signals
        self.compose_btn.clicked.connect(
            lambda b: self.composeClicked.emit())
        self.contacts_btn.clicked.connect(
            lambda b: self.contactsViewClicked.emit())
        self.options_btn.clicked.connect(
            lambda b: self.settingsClicked.emit())
        
        # it puts the buttons in its box
        self.button_vbox.addWidget(self.compose_btn)
        self.button_vbox.addWidget(self.contacts_btn)
        self.button_vbox.addWidget(self.options_btn)
        
        # push them to the top
        self.button_vbox.addStretch()
        
        self.main_hbox.addLayout(self.button_vbox)

        # a horizontal layout with controls to launch and show progress
        # in message retrieval
        self.message_ctl_hbox = QHBoxLayout()
        
        self.incoming_lbl = QLabel("Incoming messages:")
        self.message_ctl_hbox.addWidget(self.incoming_lbl)
        
        self.incoming_progress = QProgressBar(self)
        self.incoming_progress.hide()
        self.message_ctl_hbox.addWidget(self.incoming_progress)

        self.message_ctl_hbox.addStretch()
        
        self.check_incoming_btn = QPushButton("Check messages")
        self.check_incoming_btn.clicked.connect(self.fetch_messages)
        self.message_ctl_hbox.addWidget(self.check_incoming_btn)
        
        self.message_vbox.addLayout(self.message_ctl_hbox)

        # list of incoming messages
        self.message_list = QTableView(self)

        # don't show the table grid as that seems to visually imply
        # editability
        self.message_list.setShowGrid(False)

        # we don't need to select individual cells
        self.message_list.setSelectionBehavior(QAbstractItemView.SelectRows)
        
        self.message_list.horizontalHeader().setStretchLastSection(True)
        self.message_list.verticalHeader().setVisible(False)
        self.message_list.horizontalHeader().setVisible(True)

        # this is not an editable list — it just launches the viewer
        self.message_list.setEditTriggers(QTableView.NoEditTriggers)

        # when a list item is doubleclicked, retrieve message info and
        # emit messageViewRequested signal
        self.message_list.doubleClicked.connect(self.double_clicked)
        
        self.message_vbox.addWidget(self.message_list)
        
        self.main_hbox.addLayout(self.message_vbox)
        
        self.main_wid.setLayout(self.main_hbox)
        self.setCentralWidget(self.main_wid)

                
        
    def show_messages(self):
        """Load messages and add them to the visible list's model"""
        
        self.message_model = QStandardItemModel(self.message_list)

        # set up columns and headers
        self.message_model.setColumnCount(3)
        self.message_model.setHorizontalHeaderLabels(["ID",
                                                      "Subject",
                                                      "Post date"])

        # add messages to the model in order
        for message in self.messages:
            id, subject, post_date = (QStandardItem(str(message["id"])),
                                      QStandardItem(message["subject"]),
                                      QStandardItem(message["post_date"]))

            self.message_model.appendRow([id, subject, post_date])

        self.message_list.setModel(self.message_model)


    def double_clicked(self):
        """Retrieve the message info and emit a signal carrying that data"""

        row = self.message_list.selectedIndexes()[0].row()
        self.messageViewRequested.emit(self.messages[row])

    def on_retrieval_started(self):
        """Respond to the start of message retrieval"""

        self.incoming_progress.setValue(0)
        self.incoming_progress.show()
        self.incoming_lbl.setText("Retrieving messages…")

    def on_message_retrieved(self, msg_dict):
        """Display the message represented by msg_dict"""

        self.messages = [msg_dict,] + self.messages
        self.show_messages()

    def on_progress_updated(self, max_val, cur):
        """Display the progress percent 100 * cur / max_val"""
        
        self.incoming_progress.setValue(100 * float(cur) / float(max_val))

    def on_status_updated(self, msg):
        """Display a message-retrieval status messages"""

        self.incoming_lbl.setText(msg + "…")

    def on_retrieval_finished(self):
        """Handle completion of message retrieval"""
        
        self.incoming_progress.hide()
        self.incoming_lbl.setText("Incoming messages:")

    def fetch_messages(self):
        """Launch message retrieval in a separate thread"""
        
        # TODO: set mail2news and NNTP stuff from UI settings
        e = MessageEndecryptor("mail2news@dizum.com",
                               [])

        pw = get_password("Decryption password:")

        if pw:
            # even though it's only used locally, it needs to survive
            # outside this method so its thread can continue
            self.mr = MessageRetriever("news.albasani.net",
                                       119,
                                       "readonly",
                                       "readonly",
                                       e,
                                       None,
                                       pw)

            self.mr.retrievalStarted.connect(self.on_retrieval_started)
            self.mr.messageRetrieved.connect(self.on_message_retrieved)
            self.mr.progressUpdated.connect(self.on_progress_updated)
            self.mr.status_updated.connect(self.on_status_updated)
            self.mr.retrieval_finished.connect(self.on_retrieval_finished)
            self.mr.start()

        else:
            # password dialog cancelled
            pass
        
if __name__ == "__main__":

    import sys
    from encryption import MessageEndecryptor
    from tor_smtp import TorSMTP
    
    endecryptor = MessageEndecryptor("mail2news",
                                     [],
                                     gnupghome="~/.gnupg")
                          
    app = QApplication(sys.argv)
    sender = TorSMTP("smtp.fastmail.com",
                     465,
                     proxy_port=9150)
                     
    # mw = UBoatMainWindow()
    # mw.messageViewRequested.connect(lambda m: print(m))
    # mw.showMaximized()
    nm = UBoatNewMessageWindow(endecryptor, sender)
    nm.show()
    sys.exit(app.exec_())
