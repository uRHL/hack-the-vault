# TEMPLATE
from pathlib import Path
import sys

ROOT_PKG = Path(__file__).parents[3] # Points to install-dir/src/
sys.path.insert(0, str(ROOT_PKG))

from htv.resources import HtvModule, HtvPath, HtvVault


__root_category__ = 'pwn-college'
# TEMPLATE: __all__ = []
__all__ = [
    'Vault',
    'Module',
    'Dojo'
]

__default_metadata__ = dict()

class Module(HtvModule):

    def __init__(self):
        super().__init__(
            _type=f"{__root_category__}.Module",
            category=f"{__root_category__}/module",
            **__default_metadata__
        )

class Dojo(HtvPath):


    def __init__(self):
        super().__init__(
            _type=f"{__root_category__}.Dojo",
            category=f"{__root_category__}/dojo",
            **__default_metadata__
        )


# Template
Vault = HtvVault(
    Module, Dojo,
    path=__root_category__
)
