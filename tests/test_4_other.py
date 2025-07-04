from pprint import pprint
from pathlib import Path
import yaml

FIXTURES_DIR = Path(__file__).parent / 'fixtures'

def read(**kwargs) -> dict:
    if len(kwargs) == 0:
        with open(FIXTURES_DIR / 'sources.yml', 'r') as file:
            kwargs = yaml.safe_load(file)
    _flatten = dict()
    for k, v in kwargs.items():
        _parents = kwargs['parent_categories'] + f"/{k}" if 'parent_categories' in kwargs else k
        if k == 'parent_categories':
            continue
        if isinstance(v, dict): # recursive call
            _flatten.update(read(**v, parent_categories=_parents))
        elif isinstance(v, str): # final depth reached
            _flatten.update({f"{_parents.split('/')[0]}.{v}": _parents})
    return _flatten

def test_read_sources():
    pprint(read())
    assert read()
