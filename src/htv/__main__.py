#!/usr/bin/env python
# -*- coding: utf-8 -*-

# TEMPLATE
from pathlib import Path
import sys

ROOT_PKG = Path(__file__).parents[1] # Points to install-dir/src/
sys.path.insert(0, str(ROOT_PKG))

from htv.constants import VERSION, PROG_NAME, PROG_DESCRIPTION
from htv.utils import CONF, FsTools, check_updates
from htv.resources import HtvVault, DataSources
from importlib import import_module

import argparse



def init_mode(args) -> int:
    """Init and/or reset the vault

    :return: 0 if vault initialized successfully. 1 otherwise
    """
    return HtvVault(args.root_dir).makedirs(reset=args.reset)


def add_mode(args) -> int:
    """Add resource(s) to the vault

    :return: 0 on success. 1 on error
    """
    if args.json_data is None:
        return HtvVault().add_resources(args.t)
    else:  # Add resource from json data
        return HtvVault().add_resources(DataSources.load(args.json_data))


def rm_mode(args) -> int:
    """Remove resource(s) from the vault

    :return: 0 on success. 1 otherwise
    """
    def confirm_prompt():
        while True:
            value = input('> Confirm deletion? [y/N] ').lower()
            if value in ['n', 'no', '']:
                print(f"[-] Deletion cancelled")
                return False
            elif value in ['y', 'yes']:
                print(f"[+] Deleting resources: {args.targets}")
                return True
            else:
                print(f"> Please answer y/n")
    if args.y and not confirm_prompt(): # Ir confirm requested but not accepted, cancel operation
        return 0

    if 'VAULT' in args.targets:
        print(f"[*] CAUTION: Deleting the entire vault")
        if confirm_prompt():
            return HtvVault().removedirs()
            # shutil.rmtree(CONF['VAULT_DIR'])
        return 0
    return HtvVault().remove_resources(*args.targets)


def list_mode(args) -> int:
    """List resource(s) from the vault

    :return: 0 on success. 1 otherwise
    """
    # TODO: if categories is None, list parent categories only
    HtvVault().list_resources(
        *args.categories,
        regex=args.name if hasattr(args, 'name') else None
    )
    return 0


def use_mode(args) -> int:
    """Open resource(s) from the vault

    :return: 0 on success. 1 on error (resource not found)
    """
    if HtvVault().use_resource(*args.target) is None:
        return 1
    else:
        return 0


def clean_mode(args) -> int:
    """Clean-up the vault

    :func:`resources.HtvVault.clean`

    :return: 0 on success. 1 if an error occurred
    """
    return HtvVault.clean()


def version_mode(args) -> int:
    """Print banner and version

    :return: 0 on success
    """
    print(FsTools.render_template('banner.txt'))
    print(f"v{VERSION}")
    return 0

################################################################################3

def _parse_args():
    """Command-line interface configuration"""
    parser = argparse.ArgumentParser(prog=PROG_NAME, description=PROG_DESCRIPTION)
    parser.add_argument(
        '-V', '--version',
        help='Print version and exits',
        action='store_true',
        default=False
    )

    # init vault CLI
    subparser = parser.add_subparsers(title='mode', dest='mode')
    vault_cli = subparser.add_parser(
        name='init',
        help='Initialize a new vault or resets an existing one',
        description='Initialize a new vault. To reset an existing vault use option -R'
    )
    vault_cli.add_argument(
        '--root-dir',
        help='Path were the vault will be created, defaults to $HOME/Documents/01-me/vaults'
    )
    vault_cli.add_argument(
        '-R', '--reset',
        help='Resets an existing vault',
        action='store_true',
        default=False
    )
    # ADD CLI
    add_cli =subparser.add_parser(
        name='add',
        help='Add new htb resources to your vault',
        description = 'Add new HTB resources to your vault'
    )
    add_cli_group = add_cli.add_mutually_exclusive_group()
    add_cli_group.add_argument(
        '-t',
        # choices=list(RES_TYPES),
        help="Type of resources to be added. If not specified it will be deduced from json data",
    )
    add_cli_group.add_argument(
        '--json-data',
        help='Resource details. This JSON is returned by toolkit.js when executed in a HTB resource page'
    )
    # Remove CLI
    remove_cli = subparser.add_parser(
        name='rm',
        help='Remove an existing resource from your vault',
        description='Remove an existing resource from your vault'
    )
    remove_cli.add_argument(
        '-y',
        help='Disable confirmation prompt',
        action='store_true',
        default=False
    )
    remove_cli.add_argument(
        'targets',
        metavar='NAME_ID',
        nargs='+',
        help='Name(s) or ID(s) of the resource(s) to be removed. To get the ID use the command `htv list`. Use the name `VAULT` to delete the entire vault'
    )

    # LIST CLI
    list_cli = subparser.add_parser(
        name='list',
        description='Shows Vault resources (modules, exercises, ...). '
             f"Resource categories defined in htv/datasources/sources.yml",
        help='Shows local HTB resources (modules, machines, VPNs)'
    )
    list_cli.add_argument(
        '-n', '--name',
        type=str,
        help='Name regex to filter the results'
    )
    list_cli.add_argument(
        'categories',
        metavar='CAT',
        nargs='*',
        # choices=[*RES_BY_TYPE.keys(), 'all'],
        help="Type of resources to be listed. Use 'all' to list everything (default)",
        default=['all']
    )

    # Use CLI
    use_cli = subparser.add_parser(
        name='use',
        help='Open the specified resource',
        description='Opens the specified with your favorite text editor (Obsidian, Code, ...)'
    )
    use_cli.add_argument(
        'target',
        metavar='NAME_ID',
        nargs='+',
        help='Name or ID of the resource to be opened. To get the ID use the command `htv list`'
    )

    # Clean CLI
    subparser.add_parser(
        name='clean',
        help='Removes temp files and cache data',
        description='Removes hidden directories, temp files and cache data created by text editors. '
             'We do not want them in the repo'
    )

    # Add add-on parsers
    for _ in (ROOT_PKG / 'datasources').iterdir():
        if _.is_dir() and (_ / '__init__.py').exists():
            try:
                _ = import_module(f"datasources.{_.name}")
                if hasattr(_, 'add_subparser'):
                    _.add_subparser(subparser)
            except (ImportError, ModuleNotFoundError) as e:
                print("[DEBUG]", e)
                continue
    return parser.parse_args()


if __name__ == '__main__':
    ARGS = _parse_args()
    if CONF['CHECK_UPDATES']:  # Check that dependencies are installed and updated
        check_updates()
    if ARGS.version:
        ARGS.mode = 'version'
    try:
        globals()[f"{ARGS.mode}_mode"](ARGS)
        exit(0)
        # exit(eval(f"{ARGS.mode}_mode({ARGS})"))
    except KeyError:
        if hasattr(ARGS, f"{ARGS.mode}_mode"):
            getattr(ARGS, f"{ARGS.mode}_mode")(ARGS)
            exit(0)
        else:
            print(f"[!] Mode not specified. Use '-h' option to show modes")
            exit(1)