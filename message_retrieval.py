from time import sleep
from datetime import datetime, timedelta
import email
import hashlib

from PyQt5.QtCore import QThread, pyqtSignal
from tor_nntp import TorNNTP

class MessageRetriever(QThread):
    """A tool to retrieve messages from alt.anonymous.messages via Tor and
    attempt to decrypt them.

    """
    
    retrieval_started = pyqtSignal(
        name="retrievalStarted")
    
    message_retrieved = pyqtSignal(
        [dict],
        name="messageRetrieved")

    progress_updated = pyqtSignal(
        int,
        int,
        name="progressUpdated")

    status_updated = pyqtSignal(
        str,
        name="statusUpdated")
    
    retrieval_finished = pyqtSignal(
        name="retrievalFinished")
    
    def __init__(self,
                 nntp_host,
                 nntp_port,
                 nntp_user,
                 nntp_password,
                 gpg,
                 last_retrieved,
                 passphrase):
        
        QThread.__init__(self)
        
        self.nntp_host = nntp_host
        self.nntp_port = nntp_port
        self.nntp_user = nntp_user
        self.nntp_password = nntp_password
        self.gpg = gpg
        self.last_retrieved = last_retrieved
        self.passphrase = passphrase
        
        self.nntp = None


    def parse_article(self, article):
        id, date, subject = None, None, None

        for line in article[1].lines:
            line = line.decode("utf-8")
            if line.startswith("Subject: "):
                subject = line[line.index(":")+1:].strip()
            elif line.startswith("Message-ID: "):
                id = line[line.index(":")+1:].strip()
            elif line.startswith("Date: "):
                date = line[line.index(":")+1:].strip()

        return id, date, subject

        
    def run(self):
        self.statusUpdated.emit("Connecting to server")

        self.nntp = TorNNTP(self.nntp_host,
                            self.nntp_port,
                            self.nntp_user,
                            self.nntp_password)

        self.statusUpdated.emit("Retrieving message counts")

        
        new_messages = self.nntp.newnews(
            "alt.anonymous.messages",
            datetime.today() - timedelta(weeks=3))
        
        if not new_messages[0].startswith("2"):
            
            self.statusUpdated.emit("<b>Error retrieving messages!</b>")
            return None
            
        else:
            
            message_ids = new_messages[1]
            cur = 0
            
            self.retrievalStarted.emit()

            for id in message_ids:

                article = self.nntp.article(id)

                encrypted = "\n".join(
                    map(lambda b: b.decode("utf-8"),
                        article[1].lines))
                
                crypt = self.gpg.decrypt(encrypted,
                                         passphrase=self.passphrase)
                
                if crypt.ok:
                    id, date, subject = self.parse_article(article)
                    self.messageRetrieved.emit({"id": id,
                                                "subject": subject,
                                                "post_date": date})
                else:
                    pass
                
                cur += 1
                
                self.progressUpdated.emit(len(message_ids), cur)
                
            self.retrievalFinished.emit()
