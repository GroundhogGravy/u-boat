import nntplib
import socks

class TorNNTP(nntplib.NNTP):
    """A nntlib.NNTP object wrapped by socks to use Tor's socks
    port

    """
    def __init__(self,
                 nntp_host,
                 nntp_port,
                 nntp_user=None,
                 nntp_password=None,
                 proxy_host="127.0.0.1", # localhost
                 proxy_port=9050):       # default Tor SOCKS port

        # use socks to wrap the smtplib module
        socks.setdefaultproxy(socks.PROXY_TYPE_SOCKS4,
                              proxy_host,
                              proxy_port)
        socks.wrapmodule(nntplib)

        # finally init TorNNTP as nntplib.NNTP with the specified
        # NNTP info
        if nntp_user and nntp_password:
            return nntplib.NNTP.__init__(self,
                                         nntp_host,
                                         user=nntp_user,
                                         password=nntp_password,
                                         port=nntp_port)
        else:
            return nntplib.NNTP.__init__(self,
                                         nntp_host,
                                         port=nntp_port)


if __name__ == "__main__":
    # Albasani's anonymous read-only account
    nntp = TorNNTP(nntp_host="news.albasani.net",
                   nntp_port=119,
                   nntp_user="readonly",
                   nntp_password="readonly")

    resp, count, first, last, name = nntp.group(
        'alt.anonymous.messages')

    print('Group', name, 'has', count, 'articles, range', first, 'to', last)

    resp, overviews = nntp.over((last - 9, last))
    for id, over in overviews:
        print(id,
              nntplib.decode_header(over['subject']),
              nntplib.decode_header(over['from']))    
