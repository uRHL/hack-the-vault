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

    # __type__ = f"{__root_category__}.mod"
    # __resource_dir__ = f"{__root_category__}/module"

    def __init__(self):
        super().__init__(
            _type=f"{__root_category__}.mod",
            _resource_dir=f"{__root_category__}/module",
            **__default_metadata__
        )

class Dojo(HtvPath):

    # __type__ = f"{__root_category__}.dojo"
    # __resource_dir__ = f"{__root_category__}/dojo"

    def __init__(self):
        super().__init__(
            _type=f"{__root_category__}.dojo",
            _resource_dir=f"{__root_category__}/dojo",
            **__default_metadata__
        )


# Template
class Vault(HtvVault):
    __resources__ = [
        Module,
        Dojo
    ]

    def __init__(self):
        super().__init__(__root_category__)

    def __dir_struct__(self, *args) -> list:
        return super().__dir_struct__(
            # Custom files here
            *args
        )
