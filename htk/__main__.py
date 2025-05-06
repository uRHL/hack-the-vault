#!/usr/bin/env python
# -*- coding: utf-8 -*-

import resources as _r
import utils as _u
import argparse


"""
HTB-toolkit is designed to create and manage an structured vault for your notes.
The vault can be opened with any text editor (Obsidian, VScode, ...) since it is just a directory with markdown files. 
"""


def init_mode(path: str | _u.Path, reset: bool = False) -> int:
    """

    :param path: Path for the vault
    :param reset: If True, and the vault already exists, the vault is deleted and reset to initial state
    :return: 0 if vault initialized successfully. 1 otherwise
    """
    return _r.HtbVault(path).makedirs(reset=reset)


def add_mode(res: _r.HtbResource | list[_r.HtbResource]) -> int:
    """

    :param res: HtbResource or list of them to be added.
    :return: 0 on success. 1 on error
    """
    return _r.HtbVault().add_resources(res)


def rm_mode(*args, confirm: bool = True) -> int:
    def confirm_prompt():
        while True:
            value = input('> Confirm deletion? [y/N] ').lower()
            if value in ['n', 'no', '']:
                print(f"[-] Deletion cancelled")
                return False
            elif value in ['y', 'yes']:
                print(f"[+] Deleting resources: {args}")
                return True
            else:
                print(f"> Please answer y/n")
    if confirm and not confirm_prompt(): # Operation cancelled
        return 0

    if 'VAULT' in args:
        print(f"[*] CAUTION: Deleting the entire vault")
        if confirm_prompt():
            return _r.HtbVault().removedirs()
            # shutil.rmtree(_u.CONF['VAULT_DIR'])
        return 0
    return _r.HtbVault().remove_resources(*args)


def list_mode(*args, name_regex: str = None) -> int:
    """

        :param args: resource types (short or long name)
        :param name_regex: regex applied on the resource name
        :return:
        """
    _r.HtbVault().list_resources(*args, name_regex=name_regex)
    return 0


def use_mode(*args) -> int:
    """

    :param args: Name(s) or ID(s), or list of them, indicating which resources should be opened
    :return: A HtbResource if the specified resource exists. Otherwise None
    """
    _r.HtbVault().use_resource(*args)
    return 0


def clean_mode() -> int:
    """
    Deletes hidden directories created by text editors, in addition to cached and temp files.
    `.gitignore` file and `.git` dir are always ignored
    :return: 0 on success. 1 if an error occurred
    """
    return _r.HtbVault().clean()


def vpn_mode(action: str, target: int | str = None) -> int:
    """

    :param action: action to be performed with the vpn: start, stop, status
    :param target: index-based id or vpn file name
    :return: 0 on success. 1 on error
    """
    if action == 'start':
        if isinstance(target, int | str):
            use_mode(target)  # Use the indicated file
        elif 'DEFAULT_VPN' in _u.CONF:  # Using default configuration
            # print(f"[*] Using default VPN configuration")
            use_mode(_u.CONF['DEFAULT_VPN'])
        else:
            try:  # get first match
                use_mode(_u.CONF['VAULT_DIR'].glob('**/*.ovpn')[0])
            except IndexError:
                print("[!] VPN configurations not found. Download them from HTB page and save into 'vpn/' dir")
                return 1
        return _u.CONF['_VPN'].start()
    elif '_VPN' not in _u.CONF:
        print(f"[-] VPN not running")
        return 1
    elif action == 'stop':
        return _u.CONF['_VPN'].stop()
    elif action == 'status':
        return _u.CONF['_VPN'].status()
    else:
        return 1 # Unknown action

################################################################################3

def _parse_args():
    parser = argparse.ArgumentParser(
        prog='htb-toolkit',
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
        help='Resource details, in JSON format. Obtained from htb-toolkit.js'
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
        help='Name(s) or ID(s) of the resource(s) to be removed. To get the ID use the command `htb-toolkit.py list`. Use the name `VAULT` to delete the entire vault'
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
        help='Name or ID of the resource to be opened. To get the ID use the command `htb-toolkit list`'
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
        help='Name or ID of the vpn conf to be opened. To get the ID use the command `htb-toolkit vpn list`. Defaults to value set in the configuration file'
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
    if ARGS.version:  # Print banner and version
        print(_u.FsTools.render_template('banner.txt'))
        print(f"v{_u._c.VERSION}")
    elif ARGS.mode == 'init':
        init_mode(ARGS.root_dir, reset=ARGS.reset)
    elif ARGS.mode == 'add':
        if ARGS.json_data is None:
            if ARGS.t is None:
                _u.FsTools.js_to_clipboard() # Js tools copied to clipboard
                _u.FileClipboard.set() # Copy object returned by js tools, save and exit
                add_mode(_r.load(_u.FileClipboard.get())) # Add resource, info from file
            else:
                # TODO: if data is not json but a type label, initialize empty resource
                pass
        else:  # Add resource from json data
            add_mode(_r.load(ARGS.json_data))
    elif ARGS.mode == 'rm':
        rm_mode(*ARGS.targets, confirm=ARGS.y)
    elif ARGS.mode == 'list':
        list_mode(*ARGS.categories, name_regex=ARGS.name)
    elif ARGS.mode == 'use':
        use_mode(*ARGS.target)
    elif ARGS.mode == 'clean':
        clean_mode()
    elif ARGS.mode == 'vpn':
        if ARGS.action == 'list':
            list_mode('vpn')
        else:
            vpn_mode(ARGS.action, ARGS.target.pop())
    else:
        print(f"[!] Mode not specified. Use '-h' option to show modes")

