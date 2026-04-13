#!/usr/bin/env python
# -*- coding: utf-8 -*-

# TEMPLATE
from pathlib import Path
import sys

ROOT_PKG = Path(__file__).parents[1] # Points to install-dir/src/
sys.path.insert(0, str(ROOT_PKG))

from htv.constants import VERSION, PROG_NAME, PROG_DESCRIPTION
from htv.utils import CONF, FsTools
from htv.resources import HtvVault
from importlib import import_module

import argparse



def init_mode(args) -> int:
    """Init and/or reset the vault

    :return: 0 if vault initialized successfully. 1 otherwise
    """
    _ = HtvVault(git_name=args.git_name, git_email=args.git_email)
    if args.source is not None:
        if not _.path.exists():
            _.makedirs(reset=args.reset)
        return _.import_vault(args.source)
        # return HtvVault(args.root_dir, args.git_name, args.git_email).makedirs(reset=args.reset)
    else:
        return _.makedirs(reset=args.reset)
        # return HtvVault(args.root_dir, args.git_name, args.git_email).makedirs(reset=args.reset)


def add_mode(args) -> int:
    """Add resource(s) to the vault

    :return: 0 on success. 1 on error
    """
    return HtvVault().add_resource(
        args.data[0] if len(args.data) > 0 else None,
        category=args.category,
        layout=args.layout,
    )


def rm_mode(args) -> int:
    """Remove resource(s) from the vault

    :return: 0 on success. 1 otherwise
    """
    def confirm_prompt():
        try:
            while True:
                value = input('>>> Confirm deletion? [y/N] ').lower()
                if value in ['n', 'no', '']:
                    print(f"[-] Deletion cancelled")
                    return False
                elif value in ['y', 'yes']:
                    return True
                else:
                    print(f">>> Please answer y/n")
        except (EOFError, KeyboardInterrupt, OSError):
            return False

    if not CONF['VAULT_DIR'].exists():
        print(f"[!] Vault not initialized. Run `htv init` to start")
        return 1

    if 'VAULT' in args.targets:
        print(f"[*] CAUTION: Deleting the entire vault")
        if not args.y and not confirm_prompt():  # Ir confirm requested but not accepted, cancel operation
            return 0
        else:
            return HtvVault().removedirs()
    else:
        try:
            print(f"[*] Selected resources contain a total of {sum([len(list(FsTools.get_resource_by_name_id(_).iterdir())) for _ in args.targets])} files/directories")
        except FileNotFoundError as e:
            print(f"[-] Resource not found:", Path(str(e).split("'")[1]).relative_to(CONF['VAULT_DIR']))
            return 0
        except AttributeError:  # get_resource_by_name_id returned None
            return 0
        if not args.y and not confirm_prompt():  # Ir confirm requested but not accepted, cancel operation
            return 0
        else:
            return HtvVault().remove_resources(*args.targets)



def list_mode(args) -> int:
    """List resource(s) from the vault

    :return: Number of listed elements [0, 256]
    """
    # TODO: if categories is None, list parent categories only
    _ = HtvVault().list_resources(
        *args.categories,
        regex=args.name if hasattr(args, 'name') else None
    )
    return 0 if _ is None else len(_)


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

################################################################################

def _parse_args(cmd = None):
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
    # vault_cli.add_argument(
    #     '-r', '--root-dir',
    #     help='Path were the vault will be created, defaults to $HOME/Documents/01-me/vaults'
    # )
    vault_cli.add_argument(
        '-R', '--reset',
        help='Resets an existing vault',
        action='store_true',
        default=False
    )
    vault_cli.add_argument(
        '--git-name',
        type=str,
        help='Name to be used in the commits'
    )
    vault_cli.add_argument(
        '--git-email',
        type=str,
        help='Email to be used in the commits'
    )
    vault_cli.add_argument(
        '-s', '--source',
        type=Path,
        default=None,
        help='Import the contents of the provided directory into the vault'
    )
    # ADD CLI
    add_cli =subparser.add_parser(
        name='add',
        help='Add new htb resources to your vault',
        description = 'Add new resources to your vault'
    )
    # add_cli_group = add_cli.add_mutually_exclusive_group()
    add_cli.add_argument(
        '-c', '--category',
        # choices=list(RES_TYPES),
        metavar='CAT',
        default=CONF['DEFAULT_CAT'],
        help="Category of the resource to be added. If will be created if does not exists",
    )
    add_cli.add_argument(
        '-l', '--layout',
        metavar='LAYOUT',
        choices=['module', 'path', 'exercise', 'file', 'custom'],
        default='custom',
        help="Resource layout. Defaults to 'custom', but it is deduced from json data if possible"
    )
    add_cli.add_argument(
        'data',
        nargs='*',
        type=str,
        metavar='NAME_DATA',
        help='Name, or details in JSON format, of the resource to be added. This JSON is returned by the corresponding datasource toolkit.js when executed in the correspondent page.'
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
        help='Name(s) or ID(s) of the resource/category to be removed. To get the ID use the command `htv list`. Use `htv rm VAULT` to delete the entire vault'
    )

    # LIST CLI
    list_cli = subparser.add_parser(
        name='list',
        description='Shows Vault resources (modules, exercises, ...). '
             f"Resource categories defined in src/datasources/sources.yml",
        help='Shows local resources (modules, machines, exercises, custom, ...)'
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
                print("[#]", e)
                continue
    return parser.parse_args(cmd)

def main(cmd = None):
    args = _parse_args(cmd)
    print('[#]', args)
    if args.version:
        args.mode = 'version'
    try:
        return globals()[f"{args.mode}_mode"](args)
    except KeyError:  # Using a custom mode defined in a datasource
        if hasattr(args, f"{args.mode}_mode"):
            return getattr(args, f"{args.mode}_mode")(args)
        else:
            print(f"[!] Mode not specified. Use '-h' option to show modes")
            return 1

if __name__ == '__main__':
    exit(main())