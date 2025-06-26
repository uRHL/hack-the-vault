from jinja2 import Environment, FileSystemLoader
from pathlib import Path

__all__ = [
    'ROOT_DIR',
    'VERSION',
]

#####   C O N S T A N T S   #####

"""Absolute path to repo"""
ROOT_DIR = Path(__file__).parents[2]

"""CLI configuration"""
PROG_NAME = 'htv'
PROG_DESCRIPTION = 'Keep your hacking notes safe and organized in a vault'

DOCS = {
    'PROJECT_NAME': 'Hack the Vault',
    'AUTHOR': '@uRHL',
    'EXTENSIONS': [
        'sphinx.ext.autodoc',         # enable autodoc extension
        'sphinx.ext.doctest',         # enable doctest extension
        # 'sphinx.ext.intersphinx',   # enable intersphinx extension
        'sphinx.ext.todo',            # enable todos extension
        'sphinx.ext.coverage',        # enable coverage extension
        # 'sphinx.ext.imgmath',       # enable imgmath extension
        # 'sphinx.ext.mathjax',       # enable mathjax extension
        # 'sphinx.ext.ifconfig',      # enable ifconfig extension
        'sphinx.ext.viewcode',        # enable viewcode extension
        'sphinx.ext.githubpages',     # enable githubpages extension
        'sphinx_autodoc_typehints',   # Optional: type hints
    ]
}

"""App version"""
VERSION = '1.0'

"""Required system pkg dependencies"""
DEPENDENCIES = ['python3', 'python3-venv', 'openvpn', 'git']  # Required system pkg dependencies

CONF_PATH = ROOT_DIR / 'conf.yml'

"""Default configuration. These keys will always be included"""
DEFAULT_CONF = dict(
        VAULT_DIR="$HOME/Documents/01-me/vaults/hacks-vault",
        CHECK_UPDATES=False,
        EXTENSIONS=dict(),
        DEFAULT_CAT='personal'
    )

"""Default configuration. These keys will only be included during runtime, but not saved to disk"""
RUNTIME_CONF = dict(
        _JINJA_ENV=Environment(loader=FileSystemLoader([
            *(ROOT_DIR / 'src/datasources/').glob('**/_layouts'),
            ROOT_DIR / "src/_layouts",
        ]))
)
