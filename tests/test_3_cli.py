import re

from htv.__main__ import main
import subprocess
import pytest
import htv


def __run__(cmd: str | None, ret: int = 0) -> None:
    try:
        if cmd is None:  # No params provided
            main()
        else:  # Params provided. Split by space, excluding quoted values
            for _ in re.findall(r"\"[\w ]+\"", cmd):  # Iterate quoted params found
                cmd = cmd.replace(_, str(_).replace(' ', '_'))
            main(list(map(lambda x: x.replace('_', ' '), cmd.split(' '))))
    except SystemExit as e:
        assert e.code == ret

def test_cli_process():
    exe = f"python3 {htv.ROOT_DIR / 'src/htv/__main__.py'}"
    _ = subprocess.run(exe, shell=True)
    assert _.returncode == 1

def test_help():
    __run__('-h')

def test_no_mode():
    __run__(None, 2)

def test_version_mode():
    __run__('-V', 0)

def test_bad_init_mode():
    __run__('init --git-email "me@me.com"', 1)

def test_init_mode():
    __run__('init --git-name "me me" --git-email "me@me.com"', 0)

@pytest.mark.parametrize('res', ['res1', '"Res 2"', 'rEs3'])
def test_add_mode(res):
    __run__(f'add {res}', 1)

@pytest.mark.parametrize('res,ret', [('all', 3), ('htb', 0), ('personal', 3)])
def test_list_mode(res, ret):
    __run__(f'list {res}', ret)  # existing resources are listed

@pytest.mark.parametrize('res,ret', [('random', 1), ('1', 0), ('res-2', 0)])
def test_use_mode(res, ret):
    __run__(f'use {res}', ret)  # returned resource is not none

def test_clean_mode():
    __run__('clean', 0)

@pytest.mark.parametrize('res,ret', [('random', 0), ('-y 1', 1), ('-y res3', 1), ('-y VAULT', 0)])
def test_rm_mode(res, ret):
    __run__(f'rm {res}', ret)