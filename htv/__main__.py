#!/usr/bin/env python
# -*- coding: utf-8 -*-

import resources as _r
import utils as _u
import argparse


def init_mode() -> int:
    """Init and/or reset the vault

    :return: 0 if vault initialized successfully. 1 otherwise
    """
    return _r.HtbVault(ARGS.root_dir).makedirs(reset=ARGS.reset)


def add_mode() -> int:
    """Add resource(s) to the vault

    :return: 0 on success. 1 on error
    """
    if ARGS.json_data is None:
        return _r.HtbVault().add_resources(ARGS.t)
    else:  # Add resource from json data
        return _r.HtbVault().add_resources(_r.load(ARGS.json_data))


def rm_mode() -> int:
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
                print(f"[+] Deleting resources: {ARGS.targets}")
                return True
            else:
                print(f"> Please answer y/n")
    if ARGS.y and not confirm_prompt(): # Ir confirm requested but not accepted, cancel operation
        return 0

    if 'VAULT' in ARGS.targets:
        print(f"[*] CAUTION: Deleting the entire vault")
        if confirm_prompt():
            return _r.HtbVault().removedirs()
            # shutil.rmtree(_u.CONF['VAULT_DIR'])
        return 0
    return _r.HtbVault().remove_resources(*ARGS.targets)


def list_mode() -> int:
    """List resource(s) from the vault

    :return: 0 on success. 1 otherwise
    """
    _r.HtbVault().list_resources(*ARGS.categories, name_regex=ARGS.name)
    return 0


def use_mode() -> int:
    """Open resource(s) from the vault

    :return: 0 on success. 1 on error (resource not found)
    """
    if _r.HtbVault().use_resource(*ARGS.target) is None:
        return 1
    else:
        return 0


def clean_mode() -> int:
    """Clean-up the vault

    :func:`resources.HtbVault.clean`

    :return: 0 on success. 1 if an error occurred
    """
    return _r.HtbVault().clean()


def vpn_mode() -> int:
    """Manage the VPN connection with HTB lab

    :return: 0 on success. 1 on error
    """
    if ARGS.action == 'list':
        ARGS.categories = ['vpn']
        return list_mode()
    elif ARGS.action == 'start':
        if isinstance(ARGS.target, list):
            ARGS.target = ARGS.target.pop()  # Use the indicated file
        elif ARGS.target is None or len(ARGS.target) == 0:  # VPN not specified, get first match
            try:
                ARGS.target = _u.CONF['VAULT_DIR'].glob('**/*.ovpn')[0]
            except IndexError:
                print("[!] VPN configurations not found. Download them from HTB page and save into 'vpn/' dir")
                return 1
        elif 'DEFAULT_VPN' in _u.CONF:  # Using default configuration
            # print(f"[*] Using default VPN configuration")
            ARGS.target = _u.CONF['DEFAULT_VPN']
        use_mode()  # Use selected VPN
        return _u.CONF['_VPN'].start()  # Start selected VPN
    elif '_VPN' not in _u.CONF:
        print(f"[-] VPN not running")
        return 1
    elif ARGS.action == 'stop':
        return _u.CONF['_VPN'].stop()
    elif ARGS.action == 'status':
        return _u.CONF['_VPN'].status()
    else:
        return 1 # Unknown action


def version_mode() -> int:
    """Print banner and version

    :return: 0 on success
    """
    print(_u.FsTools.render_template('banner.txt'))
    print(f"v{_u._c.VERSION}")
    return 0

################################################################################3

def _parse_args():
    """Command-line interface configuration"""
    parser = argparse.ArgumentParser(
        prog='htb-vault',
        description='A simple CLI tool to manage your HTB vault for note taking',
    )
    # Init CLI
    subparser = parser.add_subparsers(title='mode', dest='mode')
    vault_cli = subparser.add_parser(
        name='init',
        help='Initialize a new vault or resets an existing one',
        description='Initialize a new vault. To reset an existing vault use option -R'
    )
    vault_cli.add_argument(
        '--root-dir',
        help='Path were the vault will be created, defaults to $HOME/Documents/vaults/htb'
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
        choices=list(_r.RES_BY_TYPE.keys()),
        help="Type of resources to be added. If not specified it will be deduced from json data",
    )
    add_cli_group.add_argument(
        '--json-data',
        help='Resource details, in JSON format. Obtained from htb-vault.js'
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
        help='Name(s) or ID(s) of the resource(s) to be removed. To get the ID use the command `htb-vault.py list`. Use the name `VAULT` to delete the entire vault'
    )

    # LIST CLI
    list_cli = subparser.add_parser(
        name='list',
        description='Shows local HTB resources (modules, machines, VPNs). '
             f"Resource categories: {', '.join(_r.RES_BY_TYPE.keys())}",
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
        # choices=[*_r.BY_TYPE.keys(), 'all'],
        help="Type of resources to be listed. Use 'all' to list everything (default)",
        default=['all']
    )

    # Use CLI
    use_cli = subparser.add_parser(
        name='use',
        help='Uses the specified resource (Open file or enable VPN',
        description='Opens the specified with your favorite text editor (Obsidian, Code, ...)'
    )
    use_cli.add_argument(
        'target',
        metavar='NAME_ID',
        nargs='+',
        help='Name or ID of the resource to be opened. To get the ID use the command `htb-vault list`'
    )

    # Clean CLI
    subparser.add_parser(
        name='clean',
        help='Removes temp files and cache data',
        description='Removes hidden directories, temp files and cache data created by text editors. '
             'We do not want them in the repo'
    )
    # VPN CLI
    vpn_cli = subparser.add_parser(
        name='vpn',
        help='Manage your VPN connections to HTB',
        description='Manage your VPN connections to HTB'
    )
    vpn_cli.add_argument(
        'action',
        choices=['start', 'stop', 'status', 'list'],
        default='list',
        help='Action to be performed. Starts the VPN in the background. Stops the VPN, if it is running. '
             'Prints the status of the vpn (active or not, logs, ...). List available VPNs (default).'
    )
    vpn_cli.add_argument(
        'target',
        metavar='NAME_ID',
        # default=None,
        nargs='*',
        help='Name or ID of the vpn conf to be opened. To get the ID use the command `htb-vault vpn list`. Defaults to value set in the configuration file'
    )
    parser.add_argument(
        '-V', '--version',
        help='Print version and exits',
        action='store_true',
        default=False
    )
    return parser.parse_args()


if __name__ == '__main__':
    ARGS = _parse_args()
    if _u.CONF['CHECK_UPDATES']:  # Check that dependencies are installed and updated
        _u.check_updates()
    if ARGS.version:
        exit(version_mode())
    try:
        exit(eval(f"{ARGS.mode}_mode()"))
    except NameError:
        print(f"[!] Mode not specified. Use '-h' option to show modes")
        exit(1)