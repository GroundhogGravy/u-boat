import re
import gnupg
import os.path

class MessageEndecryptor(gnupg.GPG):
    def __init__(self, mail2news,
                 remailers,
                 gnupghome="~/.secure-messaging"):
        
        gnupg.GPG.__init__(
            self,
            gnupghome=os.path.abspath(
                os.path.expanduser(gnupghome)),
            options=["--throw-keyids",])  # hide all recipients
        
        self.mail2news = mail2news
        self.remailers = remailers
        self._email_rgx = re.compile(r'[\w\.-]+@[\w\.-]+')

    def recipients(self):
        keys = self.list_keys()
        return [{"uid": key["uids"][0],
                 "fingerprint": key["fingerprint"]}
                for key in keys]
        
    def _extract_email(self, s):
        """Attempts to extract an email address from `s` by regex.  Returns
        the email address if successful, None if not.

        """
        
        matches = self._email_rgx.findall(s)
        
        if len(matches) > 0:
            return matches[0]
        else:
            return None
    
    def _wrap_for_aam(self, msg):
        """Wrap a message with a remailer command directing it to a mail2news
        instance and from there to alt.anonymous.messages

        """
        
        cmd = """::
Anon-To: %s

Newsgroups: alt.anonymous.messages

%s"""
        return cmd % (self.mail2news,
                      msg)

    def _wrap_for_remailer(self, msg, prev_remailer):
        """Wrap a message in a remailer command to direct it to the next
        remailer in the chain"""
        
        cmd = """::
Anon-To: %s

%s"""
        return cmd % (self._extract_email(prev_remailer["uids"][0]),
                      msg)
    
    def encrypt_enchained(self, msg, recipient, remailers):
        """Encrypt a message, wrap it in commands for a mail2news instance,
        and encrypt it for each of a chain of remailers"""
        
        tmp_encrypted = str(self.encrypt(msg,
                                         recipient["fingerprint"]))
        
        prev_remailer = None
        
        for remailer in remailers:
            if prev_remailer:
                tmp_encrypted = self._wrap_for_remailer(tmp_encrypted,
                                                        prev_remailer)
            else:
                tmp_encrypted = self._wrap_for_aam(tmp_encrypted)

            tmp_encrypted = str(self.encrypt(tmp_encrypted,
                                             remailer["fingerprint"]))
            tmp_encrypted = "::\nEncrypted: PGP\n\n" + tmp_encrypted
            
            prev_remailer = remailer
            
        return tmp_encrypted


if __name__ == "__main__":

    encryptor = MessageEndecryptor("mail2news@dizum.com",
                          [])
    print(encryptor.recipients())
