from jinja2 import Environment, FileSystemLoader
from pathlib import Path

__all__ = [
    'ROOT_DIR',
    'VERSION',
    'RES_TYPES'
]

#####   C O N S T A N T S   #####

"""App version"""
VERSION = '0.1'

"""All possible types of resource"""
RES_TYPES = ['mod', 'spt', 'jpt', 'stp', 'mch', 'chl', 'shr', 'trk', 'lab', 'ftr', 'btg', 'vpn']

"""Absolute path to repo"""
ROOT_DIR = Path(__file__).parents[2]

"""Required system pkg dependencies"""
DEPENDENCIES = ['python3', 'python3-venv', 'openvpn', 'git']  # Required system pkg dependencies

"""Default configuration. These keys will always be included"""
DEFAULT_CONF = dict(
        VAULT_DIR="$HOME/Documents/01-me/vaults/htb",
        CHECK_UPDATES=True
    )

"""Default configuration. These keys will only be included during runtime, but not saved to disk"""
RUNTIME_CONF = dict(
        _LOG_PATH=Path('/tmp/.htbtlk.log'),
        _CB_PATH=Path('/tmp/.auxclipboard'),
        _CACHE_PATH=Path('/tmp/.htbtlk.cc'),
        _JINJA_ENV=Environment(loader=FileSystemLoader(ROOT_DIR / "templates"))
    )
