# TEMPLATE
from pathlib import Path
import sys

ROOT_PKG = Path(__file__).parents[3] # Points to install-dir/src/
sys.path.insert(0, str(ROOT_PKG))

from htv.resources import HtvModule, HtvPath, HtvExercise, HtvVault, CustomResource, DataSources
from htv.utils import CONF, FsTools, add_extensions
from htv.__main__ import use_mode, list_mode

import subprocess
import os
import re
# TEMPLATE
__root_category__ = 'htb'
# TEMPLATE: __all__ = []
__all__ = ['Vault', 'VpnClient', 'add_subparser',
           'AcademyModule', 'AcademySkillPath', 'AcademyJobRolePath',
           'LabStartingPoint', 'LabMachine', 'LabChallenge', 'LabSherlock',
           'LabTrack', 'LabProLab', 'LabFortress', 'LabBattleground', ]

__default_metadata__ = dict(os=None,
            points=None,
            rating=None,
            targets=list(),
            release_date=None,
            related_academy_modules=None)

__extensions__ = {
    '.ovpn': 'htb.vpn'
}

add_extensions(**__extensions__)

#######  B A S E   C L A S S E S  ####################

class VpnClient(CustomResource):
    """
    Dataclass representing a configuration for OpenVpn.

    :cvar __resource_dir__: [Path] Location for these resources within the vault (relative path)
    :ivar protocol: [str] Protocol configured in the vpn file (tcp or udp)
    :ivar port: [int] Port configured in vpn file. Normally 443 for tcp and 1337 for udp
    :ivar remote: [str] Full string of the remote server configured in the vpn file.

    """
    __type__ = f"{__root_category__}.vpn"
    __resource_dir__ = f"{__root_category__}/vpn"
    __file_ext__ = '.ovpn'

    # Custom class attribute
    __log_path__ = Path('/tmp/.htbtlk.log')  # CONF['_LOG_PATH']  # Path to log file (Value read from `CONF`)

    def __init__(self):
        super().__init__()
        self._proc = None  # Process running the open-vpn client
        self._path = None
        self.protocol = None  # (tcp, udp)
        self.port = None  # (tcp -> 443, udp -> 1337)
        self.remote = None

    @property
    def country(self) -> str:
        """Country configured for this VpnClient (EU, UE, SG, AU)"""
        return self.remote.split('.').pop().upper()

    @property
    def cat(self) -> str:
        """Category configured for this VpnClient (Free, VIP, VIP+)"""
        # Free, VIP, VIP+
        if self.remote.find('dedivip') != -1:
            return 'VIP+'
        elif self.remote.find('free') != -1:
            return 'FREE'
        elif self.remote.find('vip') != -1:
            return 'VIP'
        else:
            raise ValueError(f"Could not parse cat from remote '{self.remote}'")

    @property
    def server_id(self) -> int:
        """Server id provided by HTB"""
        return int(re.search(r'\d+', self.remote)[0])

    def __str__(self)-> str:
        return f'{self.path.name} [{self.country} - {self.cat} {self.server_id} ({self.protocol}:{self.port})]'

    def update(self, **kwargs) -> None:
        """
        Update Vpn attributes from a file. If path is not absolute,
        the file will be searched withing the vpn dir (VAULT_DIR/vpn)
        Param 'path' is expected.

        :param kwargs: Expects argument 'path' pointing to vpn configuration file.
        :raise ValueError: If path, or file content, is not valid
        TODO: template
        """
        if 'path' not in kwargs:
            print("[!] Missing path to file with the data to be updated")
            return
        path = Path(kwargs.pop('path'))
        if path.name.endswith(".ovpn") and path.exists():  # Init from file
            setattr(self, '_name', path.name)
            # self._name = path.name
            # self._path = path if path.is_absolute() else self._path = CONF['VAULT_DIR'] / f"vpn/{path}"
        else:  # path provided but invalid file
            raise ValueError("Not a VPN configuration file")
        # Config file provided. Parse it
        with open(self.path, 'r') as conf_file:
            lines = conf_file.readlines()
        try:  # Parse info
            self.port = lines[3].split(' ')[2].strip()  # remote & port line 3
            self.remote = lines[3].split(' ')[1].strip()
            self.protocol = lines[2].strip()[-3:]  # protocol line 2
            if self.protocol not in ['tcp', 'udp']:
                raise ValueError(f"Unknown protocol '{self.protocol}'. Expected: tcp, udp ({self.path}:2)")
        except (IndexError, ValueError): # Valid file name but invalid content
            raise ValueError(f"VPN file syntax not recognized '{path}'")

    def open(self) -> None:
        """Updates the app runtime configuration with this VPN details"""
        # TODO: update DEFAULT_VPN ?
        super().open()
        CONF.update_values(_VPN=self)

    # Custom methods
    def start(self, force: bool = False) -> int:
        """Starts the vpn using loaded configuration

        Starts an `openvpn` process in the background.
        If a vpn is already running and `force` is False, this VPN will not be started

        :param force: If True and a VPN is already running, it is stopped
        :return: 0 on success. 1 if a VPN is already running
        """
        if 'CURRENT_VPN' in CONF:
            if force:  # kill running VPN process
                print('[*] Stopping current VPN...')
                os.kill(CONF['CURRENT_VPN'], 9)
                self.__log_path__.unlink()
                CONF.remove_values('CURRENT_VPN')
            else:
                print("[-] A VPN is already running. Stop it to run a new one")
                return 1
        print(f'[*] Using VPN configuration from {self.path}')
        print(f'[*] Establishing connection...')
        self._proc = subprocess.Popen(f"sudo openvpn {self.path} &> {self.__log_path__} &", shell=True)
        CONF.update_values(CURRENT_VPN=self._proc.pid)
        print("[+] Connected to VPN")
        return 0

    def stop(self) -> int:
        """Stops this VpnClient, if it is running

        :return: 0 on success
        """
        # Get process running in bg and kill it
        self._proc.kill()
        self._proc = None
        self.__log_path__.unlink()
        CONF.remove_values('CURRENT_VPN')
        return 0

    def status(self, quiet: bool = False) -> int:
        """Check if this VPN is running

        :param quiet: If True, the VPN log is shown in the terminal
        :return: 0 if VPN is stopped. 1 if running
        """
        if self._proc:
            print(f"[+] VPN active")
            # Print current contents of .log file
            if not quiet:
                os.system(f"more {self.__log_path__}")
            # with open(self._log_path, 'r') as file:
            #     # Open file in default text editor
            #     print(file.read())
            return 1
        else:
            print(f"[-] VPN stopped")
            return 0

class AcademyModule(HtvModule):
    """Class representing an HTB Module

    :cvar TIER_COST: [dict] Mapping tier-cost
    :cvar COST_TIER: [dict] Mapping cost-tier

    :ivar duration: [str] Approximated time required to complete the module (days-hours)
    :ivar summary: [str] Brief summary of the module

    """

    __type__ = f"{__root_category__}.mod"
    __resource_dir__ = f"{__root_category__}/academy/module"

    TIER_COST = {
        '0': 10,
        'I': 50,
        'II': 100,
        'III': 500,
        'IV': 1000
    }
    COST_TIER = {v: k for k, v in TIER_COST.items()}

    def __init__(self):
        super().__init__(**__default_metadata__)
        self._tier = None
        self.duration = None
        self.summary = None


    @property
    def tier(self) -> str:
        """Module tier (0, I, II, III, IV)"""
        return self._tier

    @tier.setter
    def tier(self, value):
        if str(value) not in AcademyModule.TIER_COST:
            raise ValueError(f"Unknown tier '{value}'")
        else:
            self._tier = str(value)
            if self.tier == '0':
                self.metadata.points = 10
            else:  # 20% of the cost
                self.metadata.points = AcademyModule.TIER_COST[self.tier] * 0.2

    @property
    def cost(self) -> int:
        """Module cost (in cubes)"""
        return AcademyModule.TIER_COST[self.tier]

class AcademySkillPath(HtvPath):
    """**Abstract class** representing a Path in the HTB academy

    :ivar cost: [int]: Path total cost (in cubes)
    :ivar duration: [str] Approximated time to complete the path (days)

    """
    __type__ = f"{__root_category__}.spt"
    __resource_dir__ = f"{__root_category__}/academy/skill-path"

    def __init__(self):
        super().__init__(**__default_metadata__)
        self.cost = None
        self.duration = None

    @property
    def tier(self) -> str:
        """Aggregated tier, combining all tiers of this path's modules"""
        return '-'.join(set([m.tier for m in self.sections]))

class AcademyJobRolePath(HtvPath):
    """**Abstract class** representing a Path in the HTB academy

    :ivar cost: [int]: Path total cost (in cubes)
    :ivar duration: [str] Approximated time to complete the path (days)

    """

    __type__ = f"{__root_category__}.jpt"
    __resource_dir__ = f"{__root_category__}/academy/job-role-path"

    def __init__(self):
        super().__init__(**__default_metadata__)
        self.cost = None
        self.duration = None

    @property
    def tier(self) -> str:
        """Aggregated tier, combining all tiers of this path's modules"""
        return '-'.join(set([m.tier for m in self.sections]))

#######  H T B   L A B   C L A S S E S  ####################

class LabStartingPoint(HtvExercise):

    __type__ = f"{__root_category__}.stp"
    __resource_dir__ = f"{__root_category__}/lab/starting-point"

    def __init__(self):
        super().__init__(**__default_metadata__)


    def __dir_struct__(self, *args) -> list:
        # Add custom files here
        return super().__dir_struct__(
            ('sol_pdf.txt', f"Download the solution from the URL: {self.metadata.url}\n"),
            * args
        )

class LabMachine(HtvExercise):

    __type__ = f"{__root_category__}.mch"
    __resource_dir__ = f"{__root_category__}/lab/machine"

    def __init__(self):
        super().__init__(**__default_metadata__)

class LabChallenge(HtvExercise):
    """Class representing a Challenge in the HTB lab

    :cvar info.logo: [str] 'https://app.hackthebox.com/images/logos/htb_ic2.svg'
    """
    __type__ = f"{__root_category__}.chl"
    __resource_dir__ = f"{__root_category__}/lab/challenge"

    def __init__(self):
        super().__init__(**__default_metadata__)
        self.metadata.logo = 'https://app.hackthebox.com/images/logos/htb_ic2.svg'

class LabSherlock(HtvExercise):

    __type__ = f"{__root_category__}.shr"
    __resource_dir__ = f"{__root_category__}/lab/sherlock"

    def __init__(self):
        super().__init__(**__default_metadata__)

class LabTrack(HtvPath):
    """Class representing a Track in the HTB lab

    :ivar _sections: [list[:class:`HtvExercise`]] List of machines (lab machines and challenges) associated to the track
    """

    __type__ = f"{__root_category__}.trk"
    __resource_dir__ = f"{__root_category__}/lab/track"

    def __init__(self):
        super().__init__(**__default_metadata__)

class LabProLab(HtvExercise):

    __type__ = f"{__root_category__}.lab"
    __resource_dir__ = f"{__root_category__}/lab/pro-lab"

    def __init__(self):
        super().__init__(**__default_metadata__)
        self.entry_point = None
        self._targets = list()

    @property
    def targets(self):
        return self._targets

    @targets.setter
    def targets(self, value: list[dict]):
        self._targets.clear()
        for item in value: # Sections are Modules/Exercises
            m = DataSources.get(item.pop('__type__'))
            m.update(**item)
            self._targets.append(m)

    def __dir_struct__(self, *args) -> list:
        # Add custom files here
        return super().__dir_struct__(
            ('README.md', 't:prolab.md', dict(resource=self)),
            *args
        )

    def makedirs(self) -> None:
        """Creates the dir structure for this ProLabMachine within the configured vault

        :return: None
        """
        super().makedirs()
        for m in self.targets:
            FsTools.dump_files([
                Path('evidences/screenshots'),
                ('README.md', 't:exercise.md', dict(resource=m))
            ], root_dir=self.path / f'targets/{m.name}')

class LabFortress(HtvExercise):

    __type__ = f"{__root_category__}.ftr"
    __resource_dir__ = f"{__root_category__}/lab/fortress"

    def __init__(self):
        super().__init__(**__default_metadata__)

class LabBattleground(HtvExercise):
    """Class representing a Battleground in the HTB lab

    :raise NotImplementedError
    """

    __type__ = f"{__root_category__}.btg"
    __resource_dir__ = f"{__root_category__}/lab/battleground"

    def __init__(self):
        super().__init__(**__default_metadata__)
        # TODO: parser not implemented

#######  D S   V A U L T  ####################

# Template
class Vault(HtvVault):
    __resources__ = [
        AcademyModule, AcademySkillPath, AcademyJobRolePath,
        LabStartingPoint, LabMachine, LabChallenge, LabSherlock,
        LabTrack, LabProLab, LabFortress, LabBattleground, VpnClient
    ]

    def __init__(self):
        super().__init__(__root_category__)

    def __dir_struct__(self) -> list:
        return [
            # ('README.txt', 'Description of this vault\n'),
            ('vpn/README.txt', 'Download VPN conf file (.ovpn extension) from HTB page \n'),
            (self.path / 'ctf')
        ]

#######  C L I   P A R S E R S  ####################

def add_subparser(subparsers):

    vpn_cli = subparsers.add_parser(
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
        nargs='*',
        help='Name or ID of the vpn conf to be opened. To get the ID use the command `htv vpn list`. Defaults to value set in the configuration file'
    )
    vpn_cli.set_defaults(vpn_mode=handle_args)

def handle_args(args) -> int:
    """Manage the VPN connection with HTB lab

    :return: 0 on success. 1 on error
    """
    if args.action == 'list':
        args.categories = ['vpn']
        return list_mode(args)
    elif args.action == 'start':
        if isinstance(args.target, list):
            args.target = args.target.pop()  # Use the indicated file
        elif args.target is None or len(args.target) == 0:  # VPN not specified, get first match
            try:
                args.target = CONF['VAULT_DIR'].glob('**/*.ovpn')[0]
            except IndexError:
                print("[!] VPN configurations not found. Download them from HTB page and save into 'vpn/' dir")
                return 1
        elif 'DEFAULT_VPN' in CONF:  # Using default configuration
            # print(f"[*] Using default VPN configuration")
            args.target = CONF['DEFAULT_VPN']
        use_mode(args)  # Use selected VPN
        return CONF['_VPN'].start()  # Start selected VPN
    elif '_VPN' not in CONF:
        print(f"[-] VPN not running")
        return 1
    elif args.action == 'stop':
        return CONF['_VPN'].stop()
    elif args.action == 'status':
        return CONF['_VPN'].status()
    else:
        return 1  # Unknown action

