from htv.utils import FsTools, Cache, check_updates
from pathlib import Path
from htv import CONF


import htv.constants
import pytest

class TestConf:
    test_values = dict(k1=1, k2=2, k3=3)
    default_len = len(htv.constants.DEFAULT_CONF) + len(htv.constants.RUNTIME_CONF)
    def test_init(self):
        # By default 4 values are loaded: 3 default params, 1 runtime params
        assert len(CONF) == self.default_len

    def test_remove_non_existent(self):
        CONF.remove_values(*self.test_values.keys())
        assert len(CONF) == self.default_len

    def test_update_values(self):
        CONF.update_values(**self.test_values)
        assert len(CONF) == self.default_len + len(self.test_values)

    def test_remove_existent(self):
        CONF.remove_values(list(self.test_values.keys())[0])
        assert len(CONF) == self.default_len + len(self.test_values) - 1

    def test_reset(self):
        CONF.reset()
        assert len(CONF) == self.default_len

class TestCache:
    test_values = ['item1', 'item2', 'item3']


    def test_clear(self):
        Cache.clear()
        assert not Cache.__route__.exists()

    def test_get_none(self):
        assert Cache.get() is None

    def test_set(self):
        Cache.set(self.test_values)
        assert Cache.__route__.exists()

    @pytest.mark.parametrize("test_ind", list(range(0, len(test_values))))
    def test_get_one(self, test_ind):
        assert Cache.get(test_ind) == Path(self.test_values[test_ind])

    def test_get_all(self):
        assert Cache.get() == [Path(i) for i in self.test_values]

class TestFsTools:
    test_file = Path('dummy1')
    def test_dump_file(self):
        FsTools.dump_file(self.test_file, 'Lorem ipsum')
        assert self.test_file.exists()

    def test_dump_file_exists(self):
        with pytest.raises(FileExistsError):
            FsTools.dump_file(self.test_file, 'Lorem ipsum')
        assert self.test_file.exists()

    def test_dump_file_overwrite(self):
        self.test_file.unlink()
        FsTools.dump_file(self.test_file, 'Lorem ipsum', exists_ok=True)
        assert self.test_file.exists()
        self.test_file.unlink()

    # def test_js_to_clipboard(self):
    #     with pytest.raises(OSError):
    #         FsTools.js_to_clipboard()
    #     a = pyperclip.paste()
    #     assert a == FsTools.render_template('toolkit.js')

def test_check_updates():
    assert check_updates() == 0

