from tor import Tor

class IndexParseError(Exception):
    pass


class KeyFetcher(Tor):
    """Fetches keys from a keyserver over Tor"""
    
    def __init__(self, server="pool.sks-keyservers.net"):
        Tor.__init__(self)
        
        self.server = server
        
        self.get_url_pattern = 'http://%s:11371/pks/lookup?op=get&search=%s&options=mr&fingerprint=on'
        self.index_url_pattern = 'http://%s:11371/pks/lookup?op=index&search=%s&options=mr&fingerprint=on'

    def _do_req(self, url):
        resp = self.tor_session().get(url)
        
        if resp.status_code == 200:
            return resp.text
        else:
            return None
        
    def get(self, q):
        return self._do_req(self.get_url_pattern %
                            (self.server, q))
    
    def _parse_index(self, idx):
        lines = idx.split("\n")

        if lines[0].startswith("info"):
            version, keycount = map(int, lines[0].split(":")[1:])
        else:
            raise IndexParseError("Invalid starting line")

        keys = []
        key=None

        for line in lines[1:]:
            if line.startswith("pub"):
                if key:
                    keys.append(key)

                vals = line.split(":")[1:]

                key = {"keyid": vals[0],
                       "algo": int(vals[1]),
                       "keylen": int(vals[2]),
                       "creationdate": vals[3],
                       "expirationdate": vals[4],
                       "flags": vals[5],
                       "uids": []}
            elif line.startswith("uid"):
                vals = line.split(":")[1:]

                key["uids"].append({"uid": vals[0],
                                    "creationdate": vals[1],
                                    "expirationdate": vals[2],
                                    "flags": vals[3]})

        keys.append(key)

        return keys
    
    def index(self, q):
        index = self._do_req(self.index_url_pattern %
                             (self.server, q))
        return self._parse_index(index)
        
            
if __name__ == "__main__":
    kf = KeyFetcher() #"pgp.mit.edu")
    idx = kf.index(input("Search string: "))
    if idx:
        for i in range(len(idx)):
            if len(idx[i]["uids"]) > 0:
                print("%s: %s" %
                      (i+1,
                       idx[i]["uids"][0]["uid"]))

        i = int(input("> ")) - 1

        print(kf.get(idx[i]["uids"][0]["uid"]))
    else:
        print("No keys found.")
