from pathlib import Path

import pytest
import json
import htv
import os


TEST_VAULT_DIR = '$HOME/Documents/01-me/vaults/test-htv'

class TestDataSources:

    def test_get_none(self):
        assert htv.DataSources.get('none-category') is None

    def test_get_all(self):
        assert len(htv.DataSources.get('all')) == 3

    def test_get_category(self):
        assert isinstance(htv.DataSources.get('htb'), htv.HtvVault)

    def test_get_resource(self):
        assert isinstance(htv.DataSources.get('htb.mod'), htv.HtvResource)

    @pytest.mark.parametrize('path', sorted((Path(__file__).parent / 'fixtures').glob('[0-9]*')))
    def test_load(self, path):
        # Dynamic modification of load parameters to test more cases
        # if path.name.startswith('1_mod'):  # test load from json string
        #     with open(path, 'r') as f:
        #         res = htv.DataSources.load(f.read())
        # elif path.name.startswith('2_mod'):  # test load from dict
        #     with open(path, 'r') as f:
        #         res = htv.DataSources.load(json.load(f))
        # else:  # test load from file
        #     res = htv.DataSources.load(path)
        with open(path, 'r') as file:
            res = htv.DataSources.load(file.read())
        if isinstance(res, list):
            for _ in res:
                assert isinstance(_, htv.HtvResource)
        else:
            assert isinstance(res, htv.HtvResource)

class TestVault:
    vault = htv.HtvVault(TEST_VAULT_DIR)
    # vault.add_resources()
    # vault.add('htb')


    def test_init(self):
        """Fresh init"""
        assert self.vault.makedirs() == 0

    def test_init_twice(self):
        """Vault already exists"""
        assert self.vault.makedirs() == 1

    def test_reset(self):
        """Reset an existing vault"""
        assert self.vault.makedirs(reset=True) == 0

    @pytest.mark.parametrize('path', sorted((Path(__file__).parent / 'fixtures').glob('[0-9]*')))
    def test_add_resource(self, path):
        with open(path, 'r') as file:
            res = htv.DataSources.load(file.read())  # Deserialize resource
        self.vault.add_resources(res) # Add resources to the vault
        if isinstance(res, htv.HtvResource):
            assert res.path.exists()
        else:  # HtbPaths are parsed from lists
            for _ in res:
                assert isinstance(_, htv.HtvResource) and _.path.exists()

    def test_list_all(self):
        assert len(self.vault.list_resources('all')) == 3

    def test_list_no_results(self):
        assert len(self.vault.list_resources('none')) == 0

    def test_list_filtering_no_results(self):
        assert len(self.vault.list_resources('htb.mod', regex='random')) == 0

    def test_list_filtering_one_results(self):
        assert len(self.vault.list_resources('htb.mod', regex='javascript-deobfuscation')) == 1

    def test_list_filtering_many_results(self):
        assert len(self.vault.list_resources('all', regex='e')) == 2

    def test_list_by_category(self):
        # Run this test after all other list_resources() test. Cache needs to be set up for next test
        assert len(self.vault.list_resources('htb.mod')) == 3

    @pytest.mark.parametrize(
        'selector,expected', [
            (1, 'web-requests'),
            (3, 'getting-started'),
            ('solar', 'solar')
        ])
    def test_use_one_resource(self, selector, expected):
        assert self.vault.use_resource(selector).name == expected
#
#     # def test_use_many_resources(self):
#     #     assert len(self.vault.use_resource(*range(1, len(self.vault.list_resources('all')) + 1))) == 11
#     #
    def test_clean(self):
        # create dummy files and folders in vault
        dummies = [
            'htb/academy/module/.dummy1',
            'htb/lab/track/_dummy2.123',
            'htb/vpn/__dummy3.txt',
            'personal/machine/__dummy4__',
            'personal/exercise/.dummy5'
        ]
        for d in dummies[:3]:  # Temp files
            (self.vault.path / d).touch()
        for d in dummies[3:]:  # Temp Directories
            os.makedirs(self.vault.path / d)
        self.vault.clean()
        assert True not in [(self.vault.path / d).exists() for d in dummies]  # assert dummy files do not exist
#
    def test_rm_res_by_name(self):
        assert self.vault.remove_resources('web-requests') == 1

    def test_rm_res_by_index(self):
        # javaScript-deobfuscation module
        assert self.vault.remove_resources(2) == 1

    def test_rm_res_unknown_index(self):
        assert self.vault.remove_resources(-1) == 0

    def test_rm_res_unknown_name(self):
        assert self.vault.remove_resources('random-res') == 0

    def test_removedirs(self):
        input("Press enter to finish")
        self.vault.removedirs()
        assert not Path(os.path.expandvars(TEST_VAULT_DIR)).exists()

