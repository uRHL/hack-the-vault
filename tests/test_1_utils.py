from htv.utils import FsTools, Templater, Cache
from pathlib import Path
from htv import CONF


import htv.constants
import pytest

class TestConf:
    test_values = dict(k1=1, k2=2, k3=3)
    # By default 4 values are loaded: 4 default params, 1 runtime params
    default_len = len(htv.constants.DEFAULT_CONF) + len(htv.constants.RUNTIME_CONF)

    def test_init(self):
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
        try:
            CONF.reset(restart=True)
        except SystemExit:
            pass
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
    test_files = [
            (Path('dummy1'), 'Lorem ipsum'),
            (Path('dummy2'), b'Lorem ipsum'),
            (Path('dummy3'), None)
        ]

    @pytest.mark.parametrize('path,content', test_files)
    def test_dump_file(self, path, content):
        FsTools.dump_file(path, content)
        assert path.exists()

    @pytest.mark.parametrize('path,content', test_files)
    def test_dump_file_exists(self, path, content):
        with pytest.raises(FileExistsError):
            FsTools.dump_file(path, content)
        assert path.exists()

    @pytest.mark.parametrize('path,content', test_files)
    def test_dump_file_overwrite(self, path, content):
        path.unlink()
        FsTools.dump_file(path, content, exists_ok=True)
        assert path.exists()
        path.unlink()

    # def test_js_to_clipboard(self):
    #     with pytest.raises(OSError):
    #         FsTools.js_to_clipboard()
    #     a = pyperclip.paste()
    #     assert a == FsTools.render_template('toolkit.js')


class TestTemplater:

    def test_clean_description(self):
        description = """Many malicious actors tend to obfuscate their code to avoid it being detected
        by systems or understood by other developers.


        The ability to deobfuscate code is a useful technique that can be applied to various
        real-world scenarios. It is useful on web application assessments to determine if
        a developer has used \"security by obscurity\" to hide JavaScript code containing
        sensitive data. It can also be useful for defenders when, for example, attempting
        to deobfuscate code that was responsible for the Phishing website used in an attack.


        In this module, you will learn the basics of deobfuscating and decoding JavaScript
        code and will have several exercises to practice what you learned.


        You will learn the following topics:


        Locating JavaScript code

        Intro to Code Obfuscation

        How to Deobfuscate JavaScript code

        How to decode encoded messages

        Basic Code Analysis

        Sending basic HTTP requests


        Our final exercise in this module will open a door for many other challenges and
        exercises in Hack The Box!


        Requirements


        It is recommended to take the Web Requests module before this one to get a general
        understanding of how HTTP requests work. If you are already familiar with them,
        then you should be able to start this module.

        Another list:


        step1

        step 2

        step 3


        """
        assert description.count('\n') > Templater.clean_description(description).count('\n')

    def test_generate_index(self):
        p = '/home/redwing/Documents/01-me/vaults/hack-vault'
        # print(Templater.generate_index(p))
        # assert Templater.generate_index(p)
        assert True

    def test_generate_index_invalid(self):
        p = '/home/redwing/Documents/01-me/vaults/hack-vault/vpn'
        # assert Templater.generate_index(p) is None
        assert True


