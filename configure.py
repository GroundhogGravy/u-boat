import os as __os
import json as __json
import codecs as __codecs

_config_dir = "%s/.config/u-boat/" % __os.environ["HOME"]

def configure():
    """If any of the essential configuration elements are not found, put
    them in place.
    
    """
    
    default_config = {
        "mail2news": "mail2news@dizum.com",
        "app-name": "U-Boat Secure Messenging",
    }

    path = "/"
    
    for elem in _config_dir.split("/"):
        path = path + elem + "/"
        
        if not __os.path.exists(path):
            __os.mkdir(path)

    config_fn = __os.path.join(_config_dir, "rc")
    
    if not __os.path.exists(config_fn):
        with __codecs.open(config_fn, "w", "utf-8") as f:
            __json.dump(default_config, f)

def get_config():
    """Return a configuration dict."""
    
    configure()
    
    with __codecs.open(__os.path.join(_config_dir, "rc"), "r", "utf-8") as f:
        return __json.load(f)
    

if __name__ == "__main__":
    configure()
    print(get_config())
