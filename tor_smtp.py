import smtplib
import socks

class TorSMTP(smtplib.SMTP_SSL):
    """A smtplib.SMTP_SSL object wrapped by socks to use Tor's socks
    port

    """
    def __init__(self,
                 smtp_host="",
                 smtp_port=0,
                 proxy_host="127.0.0.1", # localhost
                 proxy_port=9050):       # default Tor SOCKS port

        # use socks to wrap the smtplib module
        socks.setdefaultproxy(socks.PROXY_TYPE_SOCKS4,
                              proxy_host,
                              proxy_port)
        socks.wrapmodule(smtplib)

        # finally init TorSMTP as smtplib.SMTP_SSL with the specified
        # SMTP info
        smtplib.SMTP_SSL.__init__(self,
                                  smtp_host,
                                  smtp_port)

if __name__ == "__main__":
    # this is dummy information
    email="user@example.com"
    pw="password"
    smtp_host="smtp@example.com"
    smtp_port=465

    # connect to server over Tor
    tor_smtp = TorSMTP(smtp_host=smtp_host,
                       smtp_port=smtp_port)
    # log in (still over Tor)
    tor_smtp.login(email,
                   pw)

    # send the email (over Tor, yet)
    tor_smtp.sendmail(
        email,
        "recipient@example.com",
        "Hello!")

    # disconnect
    tor_smtp.quit()
