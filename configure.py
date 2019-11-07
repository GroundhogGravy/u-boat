import os as __os
import json as __json
import codecs as __codecs

_config_dir = "%s/.config/u-boat/" % __os.environ["HOME"]

def _configure():
    """If any of the essential configuration elements are not found, put
    them in place.
    
    """
    
    default_config = {
        "mail2news": "mail2news@dizum.com",
        "app-name": "U-Boat Secure Messenging",
    }

    path = "/"

    # make the config directory and all its parents, as needed
    for elem in _config_dir.split("/"):
        path = path + elem + "/"
        
        if not __os.path.exists(path):
            __os.mkdir(path)

    config_fn = __os.path.join(_config_dir, "rc")

    # ensure the config file exists
    if not __os.path.exists(config_fn):
        with __codecs.open(config_fn, "w", "utf-8") as f:
            __json.dump(default_config, f)

    config = _get_config()

    try:
        gpg_dir = config["gpg-dir"]
    except KeyError:
        config["gpg-dir"] = __os.path.join(_config_dir, "gpg")
        write_config(config)

    # make the gpg directory
    if not __os.path.exists(config["gpg-dir"]):
        __os.mkdir(config["gpg-dir"])

def _get_config():
    """Return a configuration dict."""
    
    with __codecs.open(__os.path.join(_config_dir, "rc"), "r", "utf-8") as f:
        return __json.load(f)

def get_config():
    """Return a configuration dict after making sure a configuration file
exists.

    """
    
    _configure()
    return _get_config()

    
def write_config(cfg):
    """Save configuration from `cfg`"""
    
    with __codecs.open(__os.path.join(_config_dir, "rc"), "w", "utf-8") as f:
        __json.dump(cfg, f)
    

if __name__ == "__main__":
    print(get_config())
