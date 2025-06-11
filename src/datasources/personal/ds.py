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

    __type__ = f"{__root_category__}.mod"
    __resource_dir__ = f"{__root_category__}/module"

    def __init__(self):
        super().__init__(**__default_metadata__)

class Path(HtvPath):

    __type__ = f"{__root_category__}.path"
    __resource_dir__ = f"{__root_category__}/path"

    def __init__(self):
        super().__init__(**__default_metadata__)

class Exercise(HtvExercise):

    __type__ = f"{__root_category__}.exr"
    __resource_dir__ = f"{__root_category__}/exercise"

    def __init__(self):
        super().__init__(**__default_metadata__)

# Template
class Vault(HtvVault):
    __resources__ = [
        Module,
        Path,
        Exercise
    ]

    def __init__(self):
        super().__init__(__root_category__)

