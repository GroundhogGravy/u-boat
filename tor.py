import subprocess
import os
import requests
from uuid import uuid4
from stem import Signal
from stem.control import Controller
import json
from threading import Thread

class IpAddrError(Exception):
    """An exception indicating that something went wrong finding an IP
    address

    """
    pass

class NoTorException(Exception):
    """An exception indicating Tor is not running"""
    pass


class Tor(object):
    """Provides a simple but limited interface to the Tor anonymity
    tool

    """
    def __init__(self,
                 control_password,
                 socks_port=9050,
                 control_port=9051):

        self._control_password = control_password
        self._socks_port=socks_port
        self._control_port=control_port
        self.tor_process = None
        self._started = False

    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_value, traceback):
        if self.tor_process:
            self.tor_process.terminate()

    @property
    def started(self):
        return self._started

    def _confirm_started(self):
        if not self.started:
            raise NoTorException("Tor is not started.")

    def _hash_password(self):
        proc = subprocess.Popen(
            ["tor",
             "--hash-password",
             self._control_password],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)

        proc.wait()
        
        stdout, stderr = proc.communicate()

        return stdout.decode("ascii").strip()
        

    def start(self):
        torrc = """SOCKSPort %(socks_port)s
Log notice syslog
DataDirectory %(data_dir)s
ControlPort %(control_port)s
HashedControlPassword %(hashed_pw)s
"""

        # TODO: make this configurable? not nonsense? something?
        data_dir = "/tmp/tor_data"

        tmp_fn = "/tmp/%s" % uuid4()

        with open(tmp_fn, "w") as f:
            f.write(
                torrc % {"socks_port": self._socks_port,
                         "data_dir": data_dir,
                         "control_port": self._control_port,
                         "hashed_pw": self._hash_password()})

        def run_tor():
            self.tor_process = subprocess.Popen(
                ["tor",
                 "-f",
                 tmp_fn],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE)

            output = []

            self._started = False

            output = []
            
            while not self.started and self.tor_process.returncode == None:
                lines = self.tor_process.stdout.readlines(3)
                output += lines
                
                for line in lines:
                    if "Opened Control listener" in line.decode("utf-8"):
                        self._started = True

            self.tor_process.wait()

        t = Thread(target=run_tor)
        t.start()

    def tor_session(self):
        """Returns a requests.session using tor's socks port

This is straight-up copied from StackOverflow:
https://stackoverflow.com/questions/30286293/make-requests-using-python-over-tor

Probably we need to confirm it's actually Tor we're going through, and
not some other artfully-crafted proxy using port 9050.

        """
        
        self._confirm_started()

        session = requests.session()
        session.proxies = {
            'http':  'socks5://127.0.0.1:%s' % self._socks_port,
            'https': 'socks5://127.0.0.1:%s' % self._socks_port
        }
        return session
    
    def reroute_connection(self):
        """Sends a signal to Tor's control port asking for a new connection
(NEWNYM)

        """

        self._confirm_started()
        
        with Controller.from_port(port=9051) as controller:
            controller.authenticate(password=self._control_password)
            controller.signal(Signal.NEWNYM)

    def tor_ip_address(self):
        """Returns the IP address of the Tor endpoint"""

        self._confirm_started()
        
        session = self.tor_session()
        resp = session.get("http://httpbin.org/ip")

        if resp.status_code != 200:
            raise IpAddrError(
                "HTTP Error %s contacting httpbin.org using Tor" %
                resp.status_code)

        resp_obj = json.loads(resp.text)
        return resp_obj["origin"].split(",")[0]

    def non_tor_ip_address(self):
        """Returns the IP address of the local connection"""

        self._confirm_started()
        
        resp = requests.get("http://httpbin.org/ip")

        if resp.status_code != 200:
            raise IpAddrError(
                "HTTP Error %s contacting httpbin.org (non-Tor)" %
                resp.status_code)

        resp_obj = json.loads(resp.text)
        return resp_obj["origin"].split(",")[0]

    def ensure_reroute_connection(self):
        """Keeps rerouting Tor until it has a new endpoint address (sometimes
        Tor reroutes to the same exit node, which is probably fine,
        but still.)

        """

        self._confirm_started()
        
        orig_ip = self.tor_ip_address()

        self.reroute_connection()

        while self.tor_ip_address() == orig_ip:
            sleep(2) # let's not overload httpbin with automated
                     # requests — it's not as though the secure
                     # messaging tool we're writing this for is fast
                     # anyway
            self.reroute_connection()

    def is_working(self):
        """Is Tor working? If the IP address over Tor is different than the
        local connection's IP address, we'll say it's working.

        """

        self._confirm_started()

        return self.tor_ip_address() != self.non_tor_ip_address()

if __name__ == "__main__":
    import time
    from random_pw import random_pw
    
    tor_password = random_pw(100) # input("Tor control password> ")
    
    # run commands that use all the methods of the Tor() object
    with Tor(tor_password, socks_port=9150) as tor:

        print("Starting Tor")
        tor.start()

        while not tor.tor_process:
            pass

        try:
            while  not tor.started:
                print("Waiting for Tor to start")
                time.sleep(1)
        except KeyboardInterrupt:
            tor.tor_process.terminate()
            exit()

        print("Checking if Tor is working")

        if tor.is_working():
            print("Tor is working")
        else:
            print("Tor IP address is same as local")

        t = tor.tor_session().get("http://start.duckduckgo.com").text

        print(t.encode("utf-8"))
        print("Old Tor IP address: %s" % tor.tor_ip_address())

        tor.ensure_reroute_connection()

        print("New Tor IP address: %s" % tor.tor_ip_address())
