# TEMPLATE
from pathlib import Path
import sys

ROOT_PKG = Path(__file__).parents[3] # Points to install-dir/src/
sys.path.insert(0, str(ROOT_PKG))

from htv import HtvModule, HtvPath, HtvVault, HtvExercise


__root_category__ = 'personal'
# TEMPLATE: __all__ = []
__all__ = [
    'Vault',
    'Module',
    'Path',
    'Exercise'
]

__default_metadata__ = dict()

class Module(HtvModule):

    def __init__(self):
        super().__init__(
            _type=f"{__root_category__}.mod",
            categories=f"{__root_category__}/module",
            **__default_metadata__
        )

class Path(HtvPath):

    def __init__(self):
        super().__init__(
            _type=f"{__root_category__}.path",
            categories=f"{__root_category__}/path",
            **__default_metadata__
        )

class Exercise(HtvExercise):

    def __init__(self):
        super().__init__(
            _type=f"{__root_category__}.exr",
            categories=f"{__root_category__}/exercise",
            **__default_metadata__
        )

# Template
class Vault(HtvVault):
    __resources__ = [
        Module,
        Path,
        Exercise
        # TODO: add support to custom resources
    ]

    def __init__(self):
        super().__init__(__root_category__)

