try:
    from utils import CONF, FsTools, Path, open_browser_tab, Cache
    from constants import RES_TYPES
except ModuleNotFoundError:
    from .utils import CONF, FsTools, Path, open_browser_tab, Cache
    from .constants import RES_TYPES
finally:
    from tqdm import tqdm

    import subprocess
    import shutil
    import copy
    import json
    import os
    import re

__all__ = [
    'load', 'HtbVault', 'VpnClient',
    'HtbModule', 'HtbPath', 'SkillPath', 'JobRolePath',
    'HtbLabResource', 'StartingPointMachine', 'Machine', 'ChallengeMachine', 'SherlockMachine',
    'MachineTrack', 'ProLabMachine', 'MachineFortress', 'MachineBattleground'
]

__resources__ = dict()

#######  A U X   C L A S S E S  ####################

class About:
    """
    Dataclass that represents related information about a HtbResource

    :ivar release_date: [str] Release date
    :ivar rating: [float] rating [0, 5]
    :ivar academy_modules: [list] Related academy modules  # TODO: link to local modules
    :ivar targets: [list] List of targets, which are either strings or HtbMachine instances

    """
    def __init__(self):
        """Initialize an About instance"""
        self.release_date = None
        self.rating = None
        self.academy_modules = None
        self.targets = list()

    def update(self, data: dict) -> None:
        """Update the attributes of this instance

        :param data: Attributes to be updated
        :return: None
        """
        for key, value in data.items():
            if key == 'targets' and isinstance(value, list):
                for val in value:
                    if isinstance(val, dict):
                        m = Machine()
                        m.info.update(val.pop('info'))
                        # m.about.update(val.pop('about'))
                        self.targets.append(m)
            else:
                setattr(self, key, value)

    def to_dict(self) -> dict:
        """

        :return: dict representation of the object
        """
        return self.__dict__

class Info:
    """
    Dataclass that represents common information for all HtbResources

    :ivar url: [str] URL of the resource
    :ivar description: [str]  resource brief description
    :ivar difficulty: [str] resource difficulty (very easy, easy, medium, hard, very hard)
    :ivar status: [str] String containing information about our progress with the resource
    :ivar logo: [str] url to the logo resource (to include it later in the readme)
    :ivar os: [str] Operating System of the resource (Windows, Linux, None)
    :ivar authors: [list[str]] resource authors
    :ivar tags: [list[str]] resource's tags, categories and labels
    :ivar points: [int] points given upon completing the resource (default 0)

    """
    def __init__(self):
        """Initializes an Info instance"""
        self.url = None
        self._name = None
        self.description = None
        self.difficulty = None
        self.status = None
        self.logo = None
        self.os = None
        self.authors = list()
        self.tags = list()
        self.points = None

    @property
    def name(self) -> str:
        """Name of the resource

        The name is always secured using :func:`utils.FsTools.secure_dirname`

        :return: str
        """
        return self._name

    @name.setter
    def name(self, value):
        self._name = FsTools.secure_dirname(value)

    def update(self, data) -> None:
        """Update Info attributes

        :param data:  values to update Info
        :return: None
        """
        for key, value in data.items():
            setattr(self, key, value)

    def to_dict(self) -> dict:
        """

        :return: dict representation of the Info instance
        """
        dc = copy.deepcopy(self.__dict__)
        dc.pop('_name')
        dc['name'] = self.name
        return dc

class Task:
    """
    Dataclass representing a Task within a :class:`HtbResource`

    :ivar number: [int] Task number (default 1)
    :ivar text: [str] Task text, brief question or goal
    :ivar answer: [str] Task answer or solution (default None)
    :ivar points: [int] Points obtained when completing the task
    """
    def __init__(self, number: int = 1, text: str = None, answer: str = None, points: int = 0):
        """Initializes a Task instance

        :param number: Task number (default 1)
        :param text: Task text
        :param answer: Task answer
        :param points: Task points
        """
        self.number = int(number)
        self.text = f"Task {self.number}" if text is None else str(text)
        self.answer = 'ANSWER' if answer is None else str(answer)
        self.points = int(points)

    def to_markdown(self) -> str:
        """

        :return: string with the MarkDown representation of the Task
        """
        return f"> T{self.number}. {f'[{self.points} pts] ' if self.points > 0 else ''}{self.text}\n> > **{self.answer}**"

    def to_dict(self) -> dict:
        """

        :return:
        """
        return self.__dict__

    @staticmethod
    def load(**kwargs):
        """Initialize a Task from a dict

        :param kwargs: Task attributes to be updated
        :return: a Task instance initialized with provided kwargs
        """
        return Task(**kwargs)

class Section:
    """
    Dataclass representing a Section of a :class:`HtbModule`

    :ivar type: [str] Type of section (interactive, document)
    :ivar title: [str] Section title used in the section template. May contain spaces
    :ivar name: [str] Secured file name (:func:`utils.FsTools.secure_filename`)

    """
    def __init__(self, _type, name):
        """Initializes a Section instance

        :param _type: Type of section (interactive, document)
        :param name: Section title, may contain spaces
        """
        self.type = str(_type)
        self.title = str(name).strip()
        self.name = FsTools.secure_filename(self.title)

    def to_dict(self) -> dict:
        """

        :return: dict representation of this Section
        """
        return dict(_type=self.type, name=self.title)

class HtbResource:
    """
    Dataclass representing a generic HtbResource.
    This class is the parent of all resource types that can be found in HTB

    :cvar __resource_dir__: [Path] Location for these resources within the vault (relative path)
    :ivar type: [str] Resource type ID (short-name). Possible values :func:`RES_BY_TYPE`
    :ivar info: [:class:`Info`]: Common resource information
    :ivar about: [:class:`About`]: Extra information about the resource
    """

    __resource_dir__ = Path()  # E.g. academy/modules

    def __init__(self, res_type: str = None):
        """Initializes a HtbResource instance

        :param res_type: Resource type. Possible values :attr:`HtbResource.type`
        """
        self._type = None
        self.type = res_type
        self.info = Info()
        self.about = About()


    @property
    def type(self) -> str:
        """Type of resource. Possible values :func:`RES_BY_TYPE`"""
        return self._type

    @type.setter
    def type(self, value):
        if value in RES_TYPES:
            self._type = value
        else:
            raise ValueError(f"Unknown resource type '{value}'")

    @property
    def type_name(self):
        """Resource type full-name"""
        return self.__resource_dir__.name

    @property
    def path(self) -> Path:
        """Absolute path of this resource"""
        return CONF['VAULT_DIR'] / self.__resource_dir__ / self.info.name

    def list_resources(self, regex: str = None) -> list:
        """List resources of this type

        :param regex: Regex to be applied on the resource name to filter the results. If None, no filtering
        :return: A list with the resources found in local vault
        """
        regex = '*' if regex is None else f"*{regex}*"
        return load(list((CONF['VAULT_DIR'] / self.__resource_dir__).glob(regex)))


    def __repr__(self) -> str:
        return re.sub("(<class '|'>)", '', str(self.__class__)) + f"({self.info.name})"

    def __str__(self) -> str:
        return self.info.name

    def to_dict(self) -> dict:
        """

        :return: dict representation of this HtbResource
        """
        return {
            '_type': self.type,
            'info': self.info.to_dict(),
            'about': self.info.to_dict(),
        }

    def update(self, **kwargs) -> None:
        """Update the attributes of this resource

        :param kwargs: Attributes to be updated
        :return: None
        :raises NotImplementedError:
        """
        raise NotImplementedError

    def makedirs(self) -> None:
        """Creates the resource dir structure in the local vault

        :return: None
        :raises NotImplementedError:
        """
        raise NotImplementedError

    def open(self) -> None:
        """Open the resource

        Open the resource in all the possible ways: opening the URL in a web browser,
        opening the Vault with your favorite editor (Obsidian, Code),
        and opening virtual-box to run your PwnBox or Kali instance.

        :return: None
        """
        open_browser_tab(self.info.url)
        # TODO: open text editor, open VBox manager
        # IF text editor already opened, pass
        # If Vbox already opened, pass

class VpnClient:
    """
    Dataclass representing a configuration for OpenVpn.

    :cvar __resource_dir__: [Path] Location for these resources within the vault (relative path)
    :ivar protocol: [str] Protocol configured in the vpn file (tcp or udp)
    :ivar port: [int] Port configured in vpn file. Normally 443 for tcp and 1337 for udp
    :ivar remote: [str] Full string of the remote server configured in the vpn file.

    """
    __resource_dir__ = Path('vpn')

    @staticmethod
    def list_resources(regex: str = None) -> list:
        """List VPN resources

        :param regex: Regex to be applied on the resource name to filter the results. If None, no filtering
        :return: A list with the resources found in local vault
        """
        regex = '*' if regex is None else f"*{regex}*"
        return [VpnClient(f) for f in (CONF['VAULT_DIR'] / VpnClient.__resource_dir__).glob(f"{regex}.ovpn")]


    def __init__(self, path: str | Path = None):
        """Initializes a VpnClient instance

        Initializes a VpnClient from a file. If path is not absolute,
        the file will be searched withing the vpn dir (htb-vault/vpn)
        If path is None, an instance with default values will be created

        :param path: path to vpn configuration file.

        """
        self._proc = None  # Process running the open-vpn client
        self._log_path = CONF['_LOG_PATH']  # Path to log file (Value read from `CONF`)
        self._path = None
        self.protocol = None  # (tcp, udp)
        self.port = None  # (tcp -> 443, udp -> 1337)
        self.remote = None

        if path is None:
            return # Do not initialize rest of values

        if path.is_absolute():
            self.path = path
        else:
            self.path = CONF['VAULT_DIR'] / f"vpn/{path}"

        with open(self.path, 'r') as conf_file:  # Read config file
            lines = conf_file.readlines()
        try:  # Parse info
            self.port = lines[3].split(' ')[2].strip()  # remote & port line 3
            self.remote = lines[3].split(' ')[1].strip()
            self.protocol = lines[2].strip()[-3:]  # protocol line 2
            if self.protocol not in ['tcp', 'udp']:
                print(f'[!] Error parsing the protocol ({self.path}:2)')
                raise ValueError
        except (IndexError, ValueError):
            raise ValueError(f"VPN file syntax not recognized '{path}'")

    @property
    def type_name(self):
        """Resource type full-name"""
        return self.__resource_dir__.name

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

    @property
    def path(self) -> Path:
        """Path to VPN configuration file"""
        return self._path

    @path.setter
    def path(self, value: Path):
        if value.name.endswith(".ovpn") and value.exists():
            self._path = Path(value)
        else:
            raise ValueError('Not a VPN configuration file or does not exist')

    @property
    def name(self) -> str:
        """Human-readable string representing the VpnClient (:func:`VpnClient.__str__`)"""
        return self.__str__()

    def __str__(self) -> str:
        return f'{self.path.name} [{self.country} - {self.cat} {self.server_id} ({self.protocol}:{self.port})]'

    def open(self) -> None:
        """Updates the app runtime configuration with this VPN details"""
        # TODO: update DEFAULT_VPN ?
        CONF.update_values(_VPN=self)

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
                self._log_path.unlink()
                CONF.remove_values('CURRENT_VPN')
            else:
                print("[-] A VPN is already running. Stop it to run a new one")
                return 1
        print(f'[*] Using VPN configuration from {self.path}')
        print(f'[*] Establishing connection...')
        self._proc = subprocess.Popen(f"sudo openvpn {self.path} &> {self._log_path} &", shell=True)
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
        self._log_path.unlink()
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
                os.system(f"more {self._log_path}")
            # with open(self._log_path, 'r') as file:
            #     # Open file in default text editor
            #     print(file.read())
            return 1
        else:
            print(f"[-] VPN stopped")
            return 0

class HtbVault:
    """
    Dataclass representing the HtbVault.
    It allows to manage the vault, adding/removing/opening resources,
    listing them or initializing/deleting the entire vault

    :ivar _path: [`Path`] Path to the vault. May contain environment variables
    :param path [str|Path]: Path to the vault. If None, the default directory from conf will be used

    """
    @staticmethod
    def remove_resources(*args) -> int:
        """Remove resources from the vault

        :param args: resource(s) name or index
        :return: The number of resources deleted
        """
        if len(args) == 1:
            try:
                _t = FsTools.search_res_by_name_id(args[0])
                shutil.rmtree(_t)
                print(f"[*] Removing {_t.name}")
            except TypeError:
                print(f"[-] Unknown resource '{args[0]}'")
                return 0
            else:
                print(f"[+] Resource(s) removed successfully")
                return 1
        else:
            return sum([HtbVault.remove_resources(res) for res in args])


    def __init__(self, path: str | Path = None):
        if path is None:
            self._path = str(CONF['VAULT_DIR'])
        else:
            self._path = str(path)

    @property
    def path(self):
        return Path(os.path.expandvars(self._path))

    def makedirs(self, reset: bool = False) -> int:
        """Create vault dir structure

        :param reset: If True, and the vault already exists, the vault is deleted and reset to initial state
        :return: 0 if vault initialized successfully. 1 otherwise
        """
        print(f"[*] Initializing vault...")
        if self.path.exists():
            if reset:
                self.removedirs()
            else:
                print(f"[!] Vault already exists")
                return 1
        CONF.update_values(VAULT_DIR=self._path)  # Update conf to use this vault
        os.makedirs(self.path, exist_ok=True)  # Create base directory
        os.chdir(self.path)
        os.system('git init --initial-branch=main')  # Initialize repo
        for r in __resources__.values():  # Create separated directories for each resource type
            os.makedirs(r.__resource_dir__)
        os.makedirs(self.path / 'ctf')
        FsTools.dump_file(self.path / '.gitignore', 'vpns/\n.obsidian\n')
        FsTools.dump_file(
            self.path / 'vpn/README.txt',
            'Download VPN conf file (.ovpn extension) from HTB page \n'
        )
        os.system('git add .')  # Initialize repo
        # TODO: ensure git.config.username and git.config.email are configured
        os.system('git commit -am "Init vault"')  # Initialize repo
        print(f"[+] Vault initialized successfully")
        return 0

    def removedirs(self) -> int:
        """Removes the entire vault

        :return: 0 on success
        """
        print(f"[!] Deleting the entire vault")
        shutil.rmtree(self.path)
        CONF.reset()  # Reset configuration so VAULT_DIR points to default location again
        return 0

    def clean(self) -> int:
        """Clean-up vault

        Deletes hidden directories created by text editors, in addition to cached and temp files.
        These files/dirs usually start by '.' or '_'. `.gitignore` file and `.git` dir are always excluded.

        :return: 0 on success. 1 if an error occurred
        """
        print(f"[*] Cleaning the vault...")
        for p in [*self.path.glob('**/.*'), *self.path.glob('**/_*')]:
            if p.name not in ['.git', '.gitignore']:
                print(f"[*] Deleting {p}")
                if p.is_dir():
                    shutil.rmtree(p)
                else:
                    p.unlink()
        print(f"[+] Vault clean-up completed")
        return 0

    def add_resources(self, res: HtbResource | list[HtbResource], stdout: tqdm = None) -> int:
        """Add resource(s) to the vault

        :param res: :class:`HtbResource` or a list of them. If None, user will be prompt to input required Resource data
        :param stdout: Stdout to log information. Default to STDOUT
        :return: 0 on success. 1 on error
        """
        try:
            if res is None:
                FsTools.js_to_clipboard()  # Js tools copied to clipboard
                self.add_resources(load(input('>  json: ')))  # Add resource, info from stdin
            elif isinstance(res, list):
                bar = tqdm(res, unit='resource')
                for item in res:
                    self.add_resources(item, stdout=bar)
                    bar.update(1)
                print(f"[+] {len(res)} resource(s) added successfully")
            elif isinstance(res, HtbResource):
                stdout.write(f"[*] Adding resource {res}") if stdout else print(f"[*] Adding resource {res}")
                res.makedirs()
                stdout.write(f"[+] Resource added {res}") if stdout else print(f"[+] Resource added {res}")
            elif isinstance(res, str) and res in RES_TYPES:
                # TODO: if data is not json but a type label, initialize empty resource
                pass
        except ValueError:
            return 1
        else:
            return 0

    def list_resources(self, *args, name_regex: str = None) -> list[Path] | None:
        """List resources from the vault

        :param args: resource types :attr:`HtbResource.type`
        :param name_regex: regex applied on the resource name. If None, no filter is applied
        :return: A list with the resources found, or None if no match
        """

        def print_ordered(*items):
            _div = '-' * 30
            header = f"\n{__resources__[rtype]().type_name.upper()}"
            start = len(res_pool) + 1
            if len(items) > 0:
                print(f"{header}{'' if name_regex is None else f' (filter: {name_regex})'}\n{_div}")
                print(*[f"{f'{ind}. ' if ind <= 9 else f'{ind}.'} {item}" for ind, item in enumerate(items, start)],
                      _div, sep='\n')

        res_pool = list()

        if not self.path.exists():
            print(f"[!] Vault not found ({self.path}). Initialize the vault first")
            return None
        if len(args) == 0:
            args = ['all']

        for rtype in args:
            if rtype == 'all':  # Recursive call with all existing res types
                return self.list_resources(*RES_TYPES, name_regex=name_regex)
            elif rtype in RES_TYPES:  # Any other type of HtbResource
                results = __resources__[rtype]().list_resources(name_regex)
                print_ordered(*results)
                res_pool.extend([r.path for r in results])
            else:
                print(f"[-] Unknown resource type '{rtype}'")

        Cache.set(res_pool)
        if len(res_pool) == 0:
            print("[-] No search results")
            res_pool = None
        return res_pool

    def use_resource(self, *args) -> HtbResource | VpnClient | list[HtbResource] | None:
        """Opens resource(s)

        :param args: Name(s) and/or index(es) of the resources to be opened
        :return: A HtbResource, or a list of them. None if the resource could not be opened
        """
        if len(args) == 1:  # Select single resource, using index or name
            tg = FsTools.search_res_by_name_id(args[0])
            # Load the resource file
            if tg.is_file() and tg.name.endswith('.ovpn'):  # Init VpnClient
                tg = VpnClient(tg)
            elif tg.is_dir():  # Init HtbResource
                tg = load(tg / 'info.json')
            else:  # Path is not a HtbResource nor VpnClient
                print(f"[-] Unknown target '{tg}'")
                return None
            print(f"[*] Using resource '{tg.info.name}' ...")
            tg.open()  # Open the resource
            return tg
        else:
            return [self.use_resource(item) for item in args]  # Recursive call


#######  H T B   A C A D E M Y   C L A S S E S  ####################

class HtbModule(HtbResource):
    """Class representing an HTB Module

    :cvar TIER_COST: [dict] Mapping tier-cost
    :cvar COST_TIER: [dict] Mapping cost-tier

    :ivar _type: [str] mod
    :ivar cost: [int] Module cost (in cubes)
    :ivar duration: [str] Approximated time required to complete the module (days-hours)
    :ivar summary: [str] Brief summary of the module
    :ivar sections: [str] Module sections (:class:`Section`)

    """
    TIER_COST = {
        '0': 10,
        'I': 50,
        'II': 100,
        'III': 500,
        'IV': 1000
    }
    COST_TIER = {v: k for k, v in TIER_COST.items()}

    __resource_dir__ = Path('academy/modules')

    def __init__(self):
        super().__init__(res_type='mod')
        self._tier = None
        self.cost = None
        self.duration = None
        self.summary = None
        self.sections = []


    @property
    def tier(self) -> str:
        """Module tier (0, I, II, III, IV)"""
        return self._tier

    @tier.setter
    def tier(self, value):
        if value not in HtbModule.TIER_COST:
            raise ValueError(f"Unknown tier '{value}'")
        else:
            self._tier = value
            self.cost = HtbModule.TIER_COST[self.tier]
            if self.tier == '0':
                self.info.points = 10
            else:  # 20% of the cost
                self.info.points = HtbModule.TIER_COST[self.tier] * 0.2

    @property
    def total_sections(self) -> int:
        """Return the total number of sections included in this module"""
        if isinstance(self.sections, int):
            return self.sections
        else:
            return len(self.sections)

    def __repr__(self) -> str:
        return f"HtbModule({self.type}, {self.info.name})"

    def to_dict(self) -> dict:
        """

        :return: Dict representation of this Module
        """
        json_data = super().to_dict()
        json_data['tier'] = self.tier
        json_data['cost'] = self.cost
        json_data['duration'] = self.duration
        json_data['summary'] = self.summary
        if isinstance(self.sections, list):
            json_data['sections'] = [st.to_dict() for st in self.sections]
        else:
            json_data['sections'] = self.sections
        return json_data

    def update(self, **kwargs) -> None:
        """Update the module attributes

        :param kwargs: Module attributes to be updated
        :return: None
        """
        self.info.update(kwargs.pop('info'))
        self.about.update(kwargs.pop('about'))
        self.tier = str(kwargs.pop('tier'))
        self.duration = str(kwargs.pop('duration'))
        self.summary = str(kwargs.pop('summary'))
        if isinstance(kwargs['sections'], list):
            self.sections = [Section(**item) for item in kwargs.pop('sections')]
        else:
            self.sections = int(kwargs['sections'])

        # Add custom attributes
        for key, value in kwargs.items():
            setattr(self, key, value)

    def makedirs(self) -> None:
        """Create dir structure for this Module in the configured vault

        :return: None
        """
        try:
            FsTools.dump_file(self.path / 'info.json', json.dumps(self.to_dict()), exist_ok=False)
        except FileExistsError:
            print(f"[!] Resource '{self.info.name}' already exists. Only info.json will be updated")
            FsTools.dump_file(self.path / 'info.json', json.dumps(self.to_dict()), exist_ok=True)
        else:
            os.makedirs(self.path / 'resources')
            FsTools.render_template('module_index.md', self.path / 'index.md', mod=self)
            for ind, section in enumerate(self.sections, 1):  # Create one file per each section
                FsTools.render_template(
                    'mod_section.md',
                    self.path / f"{f'0{ind}' if ind < 10 else ind}_{section.name}.md",
                    section=section
                )

    def add_section(self, _type: str, name: str) -> Section:
        """Adds a new section to this module

        :param _type: Type of section (interactive / document)
        :param name: Title of the section. May contain spaces
        :return: the new :class:`Section` added
        """
        self.sections.append(Section(_type, name))
        return self.sections[-1]

    def remove_section(self, index: int) -> Section:
        """Removes a section from this module

        :param index: Index of the section to be removed
        :return: the removed :class:`Section`
        """
        return self.sections.pop(index)

class HtbPath(HtbResource):
    """**Abstract class** representing a Path in the HTB academy

    :ivar _progress: [float] Completion progress
    :ivar cost: [int]: Path total cost (in cubes)
    :ivar duration: [str] Approximated time to complete the path (days)
    :ivar sections: [int] Total number of sections included in the path
    :ivar modules: [list[:class:`HtbModule`]] List of modules included in the path

    """

    def __init__(self, res_type :str =None):
        super().__init__(res_type=res_type)
        self._progress = 0.0
        self.cost = None
        self.duration = None
        self.sections = None # int
        self.modules = []

    @property
    def tier(self) -> str:
        """Aggregated tier, combining all tiers of this path's modules"""
        return '-'.join(set([m.tier for m in self.modules]))


    # TODO: completed = completed_mods / total_mods
    @property
    def status(self) -> str:
        """Completion status string"""
        # return f"{self._completed * 100} %"
        return f"{self._progress * 100} % completed"

    def to_dict(self) -> dict:
        """

        :return: dict representation of this path
        """
        json_data = super().to_dict()
        # Tier not added since it is always deduced from self.modules
        json_data['cost'] = self.cost
        json_data['duration'] = self.duration
        json_data['sections'] = self.sections
        json_data['_progress'] = self._progress
        json_data['modules'] = [mod.to_dict() for mod in self.modules]
        return json_data

    def update(self, **kwargs) -> None:
        """Update this path attributes

        :param kwargs: Path attributes to be updated
        :return: None
        """
        self.info.update(kwargs.pop('info'))
        self.cost = int(kwargs.pop('cost'))
        self.duration = str(kwargs.pop('duration'))
        self.sections = int(kwargs.pop('sections'))
        # These modules only include info.name, info.url
        self._progress = kwargs.pop('_progress')
        for item in kwargs.pop('modules'):
            m = HtbModule()
            item.pop('_type') # Pop _type as it is already known
            m.update(**item)
            self.modules.append(m)
        # Add custom attributes
        for key, value in kwargs.items():
            setattr(self, key, value)

    def makedirs(self, missing_ok: bool = False) -> None:
        """Create the directory structure of the path, including the corresponding modules

        :param missing_ok: If True, user will not be prompted to add the missing modules
        :return: None
        """
        try:
            FsTools.dump_file(self.path / 'info.json', json.dumps(self.to_dict()), exist_ok=False)
        except FileExistsError:
            print(f"[!] Resource '{self.info.name}' already exists. Only info.json will be updated")
            FsTools.dump_file(self.path / 'info.json', json.dumps(self.to_dict()), exist_ok=True)
        else:
            FsTools.render_template('path_index.md', self.path / 'index.md', path=self)
            # TODO: Should I create soft link files?
            # os.symlink(f"../../modules/{mod.name}", mod.name, target_is_directory=True)
            bar = tqdm(self.modules, unit='mod')
            for mod in self.modules:  # Create soft-links to modules
                bar.write(f"[*] Adding mod: {mod.info.name}")
                if not (missing_ok or mod.path.exists()):
                    bar.write(f"  [-] Module not found in local vault")
                    # If module not found locally, request the user to get the info from the web
                    FsTools.js_to_clipboard(bar)
                    bar.write(f"  [*] Opening module URL and waiting for input")
                    open_browser_tab(mod.info.url, delay=3)
                    while True:
                        try:
                            FsTools.js_to_clipboard(bar)
                            # _u.FileClipboard.set()  # Paste clipboard into file, save and exit
                            # load(_u.FileClipboard.get()).makedirs()  # Init module
                            load(input('>  json: ')).makedirs()  # Init module
                            bar.write(f"  [+] Module added")
                            break
                        # TODO: catch rest of exceptions to exit gracefully
                        except json.decoder.JSONDecodeError:
                            bar.write("   > Not a valid JSON")
                bar.update(1)

class SkillPath(HtbPath):

    __resource_dir__ = Path('academy/paths/skill-paths')

    def __init__(self):
        super().__init__(res_type='spt')

class JobRolePath(HtbPath):

    __resource_dir__ = Path('academy/paths/job-role-paths')

    def __init__(self):
        super().__init__(res_type='jpt')

#######  H T B   L A B   C L A S S E S  ####################

class HtbLabResource(HtbResource):
    """**Abstract class** representing a resource from HTB lab

    :ivar tasks: [list[:class:`Task`]] List of tasks associated to this resource

    """
    def __init__(self, res_type :str =None):
        super().__init__(res_type=res_type)
        self.tasks = list()

    def to_dict(self, *args, path: str | Path = None) -> dict:
        """

        :param path: If provided, write dumps the returned dict into this path
        :return: dict representation of this resource
        """
        json_data = super().to_dict() # Initialize json data
        json_data['tasks'] = [tsk.to_dict() for tsk in self.tasks]  # Add tasks
        for a in args:  # Add any other custom attribute
            if hasattr(self, a):
                json_data[a] = self.__getattribute__(a)
        if path is not None:
            if path.is_dir():
                with open(path / 'info.json', 'w') as file:
                    json.dump(json_data, file)
            elif path is not None:
                with open(path, 'w') as file:
                    json.dump(json_data, file)
        return json_data

    def update(self, **kwargs) -> None:
        """Update machine attributes

        :param kwargs: Machine Attributes to be updated
        :return: None
        """
        self.info.update(kwargs.pop('info'))
        self.about.update(kwargs.pop('about'))
        self.tasks = [Task(**item) for item in kwargs.pop('tasks')]

        # Add custom attributes
        for key, value in kwargs.items():
            setattr(self, key, value)

    def makedirs(self) -> None:
        """Create dir structure for this resource within the configured vault

        If the resource already exists in the local vault, only its info.json file will be updated

        :return: None
        """
        if self.info.name in [None, '']:
            print(f"f[!] Resource has no name ({self.__repr__()})")
            self.info.name = 'unknown'
        try:
            FsTools.dump_file(self.path / 'info.json', json.dumps(self.to_dict()), exist_ok=False)
        except FileExistsError:
            print(f"[!] Resource '{self.info.name}' already exists. Only info.json will be updated")
            FsTools.dump_file(self.path / 'info.json', json.dumps(self.to_dict()), exist_ok=True)
        else:
            os.makedirs(self.path / 'evidences/screenshots', exist_ok=True)
            FsTools.dump_file(
                self.path / 'sol_pdf.txt',
                f"Download the solution from the URL: {self.info.url}\n"
            )
            FsTools.render_template(
                'writeup.md',
                self.path / 'writeup.md',
                resource=self
            )

    def add_task(self, text: str = None, answer: str = None, points: int = 0, index: int = None) -> Task:
        """Adds a new :class:`Task` to this machine

        :param text: Text of the task
        :param answer: Answer of the task
        :param points: Points of the task
        :param index: Index of the task. Defaults to None (auto-increment)
        :return: the added :class:`Task`
        """
        self.tasks.append(Task(
            number=len(self.tasks) + 1 if index is None else index,
            text=text,
            answer=answer,
            points=points
        ))
        return self.tasks[-1]

    def remove_task(self, index: int) -> Task:
        """Removes a :class:`Task` from this machine

        :param index: Index of the Task to be removed
        :return: the removed :class:`Task`
        """
        return self.tasks.pop(index)

class StartingPointMachine(HtbLabResource):

    __resource_dir__ = Path('lab/starting-point')

    def __init__(self):
        super().__init__(res_type='stp')

class Machine(HtbLabResource):

    __resource_dir__ = Path('lab/machines')

    def __init__(self):
        super().__init__(res_type='mch')

class ChallengeMachine(HtbLabResource):
    """Class representing a Challenge in the HTB lab

    :cvar info.logo: [str] 'https://app.hackthebox.com/images/logos/htb_ic2.svg'
    """

    __resource_dir__ = Path('lab/challenges')

    def __init__(self):
        super().__init__(res_type='chl')
        self.info.logo = 'https://app.hackthebox.com/images/logos/htb_ic2.svg'

class SherlockMachine(HtbLabResource):

    __resource_dir__ = Path('lab/sherlocks')

    def __init__(self):
        super().__init__(res_type='shr')

class MachineTrack(HtbLabResource):
    """Class representing a Track in the HTB lab

    :ivar tasks: [list[:class:`HtbMachine`]] List of machines (lab machines and challenges) associated to the track
    """

    __resource_dir__ = Path('lab/tracks')

    def __init__(self):
        super().__init__(res_type='trk')
        self.tasks = list[HtbLabResource]

    def update(self, **kwargs) -> None:
        """Update this MachineTrack attributes

        :param kwargs: Attributes to be updated
        :return: None
        """
        self.info.update(kwargs.pop('info'))
        self.about.update(kwargs.pop('about'))
        self.tasks = load(kwargs.pop('tasks'))

        # Add custom attributes
        for key, value in kwargs.items():
            setattr(self, key, value)

    def makedirs(self) -> None:
        """Creates the dir structure for this track within the configured vault

        :return: None
        """
        try:
            FsTools.dump_file(self.path / 'info.json', json.dumps(self.to_dict()), exist_ok=False)
        except FileExistsError:
            print(f"[!] Resource '{self.info.name}' already exists. Only info.json will be updated")
            FsTools.dump_file(self.path / 'info.json', json.dumps(self.to_dict()), exist_ok=True)
        else:
            FsTools.render_template('track_index.md', self.path / 'index.md', track=self)

class ProLabMachine(HtbLabResource):

    __resource_dir__ = Path('lab/pro-labs')

    def __init__(self):
        super().__init__(res_type='lab')
        self.entry_point = None

    def update(self, **kwargs) -> None:
        """Update this ProLabMachine attributes

        :param kwargs: Attributes to be updated
        :return: None
        """
        self.info.update(kwargs.pop('info'))
        self.about.update(kwargs.pop('about'))

        self.entry_point = kwargs.pop('entry_point')
        self.tasks = [Task(**item) for item in kwargs.pop('tasks')]
        # Add custom attributes
        # for key, value in kwargs.items():
        #     setattr(self, key, value)

    def makedirs(self) -> None:
        """Creates the dir structure for this ProLabMachine within the configured vault

        :return: None
        """
        try:
            FsTools.dump_file(self.path / 'info.json', json.dumps(self.to_dict()), exist_ok=False)
        except FileExistsError:
            print(f"[!] Resource '{self.info.name}' already exists. Only info.json will be updated")
            FsTools.dump_file(self.path / 'info.json', json.dumps(self.to_dict()), exist_ok=True)
        else:
            FsTools.render_template('prolab_index.md', self.path / 'index.md', lab=self)
            for m in self.about.targets:
                _tg_path = self.path / f'targets/{m.info.name}'
                os.makedirs(_tg_path / 'evidences/screenshots', exist_ok=True)
                FsTools.render_template('basic_writeup.md', _tg_path / 'writeup.md', resource=m)

    def to_dict(self, *args, path: str | Path = None) -> dict:
        return super().to_dict('entry_point', path=path)

class MachineFortress(HtbLabResource):

    __resource_dir__ = Path('lab/fortresses')

    def __init__(self):
        super().__init__(res_type='ftr')

    def makedirs(self) -> None:
        """Creates the dir structure for this MachineFortress within the configured vault

        :return: None
        """
        try:
            FsTools.dump_file(self.path / 'info.json', json.dumps(self.to_dict()), exist_ok=False)
        except FileExistsError:
            print(f"[!] Resource '{self.info.name}' already exists. Only info.json will be updated")
            FsTools.dump_file(self.path / 'info.json', json.dumps(self.to_dict()), exist_ok=True)
        else:
            os.makedirs(self.path / 'evidences/screenshots', exist_ok=True)
            FsTools.render_template(
                'writeup.md',
                self.path / 'writeup.md',
                resource=self
            )

class MachineBattleground(HtbLabResource):
    """Class representing a Battleground in the HTB lab

    :raise NotImplementedError
    """

    __resource_dir__ = Path('lab/battlegrounds')

    def __init__(self):
        super().__init__(res_type='btg')
        # TODO: parser not implemented

############################################################################

# Resource types, full-names and default paths
__resources__.update({
        'mod': HtbModule,
        'spt': SkillPath,
        'jpt': JobRolePath,
        'stp': StartingPointMachine,
        'mch': Machine,
        'chl': ChallengeMachine,
        'shr': SherlockMachine,
        'trk': MachineTrack,
        'lab': ProLabMachine,
        'ftr': MachineFortress,
        'btg': MachineBattleground,
        'vpn': VpnClient
    })

def load(data :str | Path | list | dict) -> HtbResource | list[HtbResource] | None:
    """Parses JSON data returned by toolkit.js

    :param data: Serialized data. It may be a JSON string/file, a serialized HtbResource (dict) or a list of them (llist[dict])
    :return: the deserialized HtbResource or list of them
    """
    if isinstance(data, dict):  # Base case, load a HtbResource from a json
        try:
            htb_resource = __resources__[data.pop('_type')]()
        except KeyError as e:
            print(f"[!] Unknown resource type. {e}")
            return None
        else:
            htb_resource.update(**data)
            return htb_resource
    elif isinstance(data, list):  # Load several HtbResources
        return [load(item) for item in data]
    elif isinstance(data, Path) or Path(data).exists():  # Load data from JSON file
        if Path(data).is_dir():  # If it is a directory append info.json
            data = Path(data) / 'info.json'
        try:
            with open(data, 'r') as file:
                return load(json.load(file))
        except FileNotFoundError:
            print(f"[-] Not a HtbResource ({data})")
            return None
    else:  # Load data from JSON string
        return load(json.loads(data))
