from htv import StartingPointMachine, Machine, ChallengeMachine, SherlockMachine
from htv import MachineTrack, ProLabMachine, MachineFortress, MachineBattleground
from htv import HtbModule, SkillPath
from htv import CONF, load, HtbVault
from pathlib import Path

import pytest
import json
import os

TEST_VAULT_DIR = '$HOME/Documents/01-me/vaults/test-htv'

@pytest.fixture
def resource_fixtures():
    return {file.name: file for file in (Path(__file__).parent / 'fixtures').glob('*')}

class TestVault:
    vault = HtbVault(TEST_VAULT_DIR)

    def test_init(self):
        """Fresh init"""
        assert self.vault.makedirs() == 0

    def test_init_twice(self):
        """Vault already exists"""
        assert self.vault.makedirs() == 1

    def test_reset(self):
        """Reset an existing vault"""
        assert self.vault.makedirs(reset=True) == 0

    @pytest.mark.parametrize(
        'path,_class', [
            ('mod_1.json', HtbModule),
            ('mod_2.json', HtbModule),
            ('mod_3.json', HtbModule),
            ('skill_path.json', SkillPath),
            ('starting_point.json', StartingPointMachine),
            ('machine.json', Machine),
            ('challenge.json', ChallengeMachine),
            ('sherlock.json', SherlockMachine),
            ('track.json', MachineTrack),
            ('pro_lab.json', ProLabMachine),
            ('fortress.json', MachineFortress),
            # ('battleground.json', MachineBattleground)
        ])
    def test_add_resource(self, path, _class, resource_fixtures):
        if resource_fixtures[path].name == 'mod_1.json':
            res = load(resource_fixtures[path])  # test load from file
        elif resource_fixtures[path].name == 'mod_2.json':
            with open(resource_fixtures[path], 'r') as f:  # test load from json string
                res = load(f.read())
        elif resource_fixtures[path].name == 'mod_3.json':
            with open(resource_fixtures[path], 'r') as f:  # test load from dict
                res = load(json.load(f))
        else:
            res = load(resource_fixtures[path])
        assert isinstance(res, _class) or isinstance(res[0], _class)  # HtbPaths are parsed from lists
        self.vault.add_resources(res)
        if isinstance(res, list):
            assert res[0].path.exists()
        else:
            assert res.path.exists()
        # -------------------------------------------------

    def test_list_all(self):
        assert len(self.vault.list_resources('all')) == 11

    def test_list_no_results(self):
        assert self.vault.list_resources('vpn') is None

    def test_list_filtering_no_results(self):
        assert self.vault.list_resources('mod', name_regex='random') is None

    def test_list_filtering_one_results(self):
        assert len(self.vault.list_resources('mod', name_regex='javascript-deobfuscation')) == 1

    def test_list_filtering_many_results(self):
        assert len(self.vault.list_resources('all', name_regex='e')) == 7

    @pytest.mark.parametrize(
        'selector,expected', [
            (1, 'web-requests'),
            (3, 'getting-started'),
            ('solar', 'solar')
        ])
    def test_use_one_resource(self, selector, expected):
        assert self.vault.use_resource(selector).info.name == expected

    def test_use_many_resources(self):
        assert len(self.vault.use_resource(*range(1, len(self.vault.list_resources('all')) + 1))) == 11

    def test_clean(self):
        # create dummy files and folders in vault
        dummies = ['academy/modules/.dummy1', 'lab/tracks/_dummy2.123', 'vpn/__dummy3.txt', 'lab/machines/__dummy4__', 'academy/paths/skill-paths/.dummy5']
        for d in dummies[:3]:
            (self.vault.path / d).touch()
        for d in dummies[3:]:
            os.makedirs(self.vault.path / d)
        self.vault.clean()
        assert True not in [(self.vault.path / d).exists() for d in dummies]  # assert dummy files do not exist

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
        self.vault.removedirs()
        assert not Path(os.path.expandvars(TEST_VAULT_DIR)).exists()