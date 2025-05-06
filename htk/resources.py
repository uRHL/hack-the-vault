import utils as _u
import subprocess
import shutil
import copy
import json
import tqdm
import os
import re

__all__ = [
    'load', 'HtbVault', 'VpnClient',
    'HtbModule', 'SkillPath', 'JobRolePath',
    'StartingPointMachine', 'LabMachine', 'ChallengeMachine', 'SherlockMachine',
    'MachineTrack', 'ProLabMachine', 'MachineFortress', 'MachineBattleground'
]

RES_BY_TYPE = {
        'mod': {'name': 'module', 'path': _u.CONF['VAULT_DIR'] / 'academy/modules'},
        'spt': {'name': 'skill-path',  'path': _u.CONF['VAULT_DIR'] /'academy/paths/skill-paths'},
        'jpt': {'name': 'job-role-path', 'path': _u.CONF['VAULT_DIR'] /'academy/paths/job-role-paths'},
        'stp': {'name': 'starting-point', 'path': _u.CONF['VAULT_DIR'] /'lab/starting-point'},
        'mch': {'name': 'machine', 'path': _u.CONF['VAULT_DIR'] /'lab/machines'},
        'chl': {'name': 'challenge', 'path': _u.CONF['VAULT_DIR'] /'lab/challenges'},
        'shr': {'name': 'sherlock', 'path': _u.CONF['VAULT_DIR'] /'lab/sherlocks'},
        'trk': {'name': 'track', 'path': _u.CONF['VAULT_DIR'] /'lab/tracks'},
        'lab': {'name': 'pro-lab', 'path': _u.CONF['VAULT_DIR'] /'lab/pro-labs'},
        'ftr': {'name': 'fortress', 'path': _u.CONF['VAULT_DIR'] /'lab/fortress'},
        'btg': {'name': 'battleground', 'path': _u.CONF['VAULT_DIR'] /'lab/battlegrounds'},
        'vpn': {'name': 'vpn', 'path': _u.CONF['VAULT_DIR'] / 'vpn'}
    }

#######  A U X   C L A S S E S  ####################

class About:
    def __init__(self):
        self.release_date = None
        self.rating = None
        self.academy_modules = None
        self.targets = list()

    def update(self, data):
        for key, value in data.items():
            if key == 'targets' and isinstance(value, list):
                for val in value:
                    if isinstance(val, dict):
                        m = LabMachine()
                        m.info.update(val.pop('info'))
                        # m.about.update(val.pop('about'))
                        self.targets.append(m)
            else:
                setattr(self, key, value)

    def to_dict(self) -> dict:
        return self.__dict__

class Info:
    def __init__(self):
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
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        self._name = _u.FsTools.secure_dirname(value)

    def update(self, data):
        for key, value in data.items():
            setattr(self, key, value)

    def to_dict(self) -> dict:
        dc = copy.deepcopy(self.__dict__)
        dc.pop('_name')
        dc['name'] = self.name
        return dc

class Task:
    def __init__(self, number: int = 1, text: str = None, answer: str = None, points: int = 0):
        self.number = int(number)
        self.text = f"Task {self.number}" if text is None else str(text)
        self.answer = 'ANSWER' if answer is None else str(answer)
        self.points = int(points)

    def to_markdown(self):
        return f"> T{self.number}. {f'[{self.points} pts] ' if self.points > 0 else ''}{self.text}\n> > **{self.answer}**"

    def to_dict(self):
        return self.__dict__

    @staticmethod
    def load(**kwargs):
        return Task(**kwargs)

class Section:
    def __init__(self, _type, title):
        self.type = str(_type)
        self.title = str(title).strip()
        self.name = _u.FsTools.secure_filename(self.title)


    def to_dict(self) -> dict:
        return dict(_type=self.type, title=self.title)

class HtbResource:

    def __init__(self, res_type: str = None):
        self._type = None
        self.type = res_type
        self.info = Info()
        self.about = About()


    @property
    def type(self):
        return self._type

    @type.setter
    def type(self, value):
        if value in RES_BY_TYPE:
            self._type = value
        else:
            raise ValueError(f"Unknown resource type '{value}'")

    @property
    def type_name(self):
        return RES_BY_TYPE[self.type]['name']

    @property
    def path(self):
        # PATHS(self.type) / self.info.name
        return RES_BY_TYPE[self.type]['path'] / self.info.name

    def __repr__(self):
        return f"{self.type_name}({self.info.name})"

    def to_dict(self):
        return {
            '_type': self.type_name, # convert to full-name string
            'info': self.info.to_dict(),
            'about': self.info.to_dict(),
        }

    def update(self, **kwargs):
        raise NotImplementedError

    def makedirs(self):
        raise NotImplementedError

    def open(self):
        _u.open_browser_tab(self.info.url)
        # TODO: open text editor, open VBox manager
        # IF text editor already opened, pass
        # If Vbox already opened, pass

class VpnClient:

    def __init__(self, path: str | _u.Path):
        self._proc = None
        self._log_path = _u.CONF['_LOG_PATH']
        self._path = None
        self.protocol = None  # (tcp, udp)
        self.port = None  # (tcp -> 443, udp -> 1337)
        self.remote = None

        if path.is_absolute():
            self.path = path
        else:
            self.path = _u.CONF['VAULT_DIR'] / f"vpn/{path}"

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
    def country(self):  # (EU, UE, SG, AU)
        return self.remote.split('.').pop().upper()

    @property
    def cat(self):
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
    def server_id(self):  # (1, 2, 3, 4, 5)
        return int(re.search('\d+', self.remote)[0])

    @property
    def path(self):
        return self._path

    @path.setter
    def path(self, value: _u.Path):
        if value.name.endswith(".ovpn") and value.exists():
            self._path = _u.Path(value)
        else:
            raise ValueError('Not a VPN configuration file or does not exist')

    @property
    def name(self):
        return self.__str__()

    def __str__(self):
        return f'{self.path.name} [{self.country} - {self.cat} {self.server_id} ({self.protocol}:{self.port})]'

    def open(self) -> int:
        """
        Updates the app runtime configuration with this VPN details
        :return: 0 on success
        """
        _u.CONF.update_values(_VPN=self)
        return 0

    def start(self) -> int:
        """

        :return: 0 on success. 1 on error
        """
        print(f'[*] Using VPN configuration from {self.path}')
        print(f'[*] Establishing connection...')
        # sudo openvpn <path> &> /tmp/htbtlk/.log &
        self._proc = subprocess.Popen(f"sudo openvpn {self.path} &> {self._log_path} &", shell=True)
        print("[+] Connected to VPN")
        return 0

    def stop(self):
        # Get process running in bg and kill it
        self._proc.kill()
        self._proc = None
        self._log_path.unlink()

    def status(self) -> int:
        if self._proc:
            print(f"[+] VPN active")
            # Print current contents of .log file
            # os.system(f"more {self.log_path}")
            with open(self._log_path, 'r') as file:
                # Open file in default text editor
                print(file.read())
            return 1
        else:
            print(f"[-] VPN stopped")
            return 0

    def to_json(self):
        # return path, _proc.id
        # TODO: save minum info so the bg process can be loged and killed
        return self._proc.pid

class HtbVault:
    @staticmethod
    def remove_resources(*args) -> int:
        for res in args:
            try:
                _t = _u.FsTools.search_res_by_name_id(res)
                shutil.rmtree(_t)
                print(f"[*] Removing {_t.name}")
            except TypeError:
                print(f"[-] Unknown resource '{res}'")
                continue
        print(f"[+] Resource(s) removed successfully")
        return 0

    def __init__(self, path: str | _u.Path = None):
        if path is None:
            self.path = _u.CONF['VAULT_DIR']
        else:
            self.path = _u.Path(path)

    def makedirs(self, reset: bool = False):
        """

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
        _u.CONF.update_values(VAULT_DIR=self.path)
        os.makedirs(self.path, exist_ok=True)
        os.chdir(self.path)
        os.system('git init --initial-branch=main')  # Initialize repo
        for t in RES_BY_TYPE.values():  # Create separated directories for each resource type
            os.makedirs(t['path'])
        os.makedirs(self.path / 'ctf')
        _u.FsTools.dump_file(self.path / 'vpn/vpn1.ovpn', 'Download VPN conf file from HTB page\n')
        _u.FsTools.dump_file(self.path / '.gitignore', 'vpns/\n.obsidian\n')
        os.system('git add .')  # Initialize repo
        # TODO: ensure git.config.username and git.config.email are configured
        os.system('git commit -am "Init vault"')  # Initialize repo
        print(f"[+] Vault initialized successfully")
        return 0

    def removedirs(self) -> int:
        """
        Removes the entire vault
        :return: 0 on success
        """
        print(f"[!] Deleting the entire vault")
        shutil.rmtree(self.path)
        return 0

    def clean(self):
        """
            Deletes hidden directories created by text editors, in addition to cached and temp files.
            `.gitignore` file and `.git` dir are always ignored
            :return: 0 on success. 1 if an error occurred
            """
        print(f"[*] Cleaning the vault...")
        for p in self.path.glob('**/.*'):
            if p.name not in ['.git', '.gitignore']:
                print(f"[*] Deleting {p}")
                shutil.rmtree(p)
        print(f"[+] Vault clean-up completed")
        return 0

    def add_resources(self, res: HtbResource | list[HtbResource], stdout=None):
        """

        :param res: HtbResource or list of them to be added.
        :param stdout: Stdout to log information
        :return: 0 on success. 1 on error
        """
        try:
            if isinstance(res, HtbResource):
                stdout.write(f"[*] Adding resource {res}") if stdout else print(f"[*] Adding resource {res}")
                res.makedirs()
                stdout.write(f"[+] Resource added {res}") if stdout else print(f"[+] Resource added {res}")
            else:
                bar = tqdm.tqdm(res, unit='resource')
                for item in res:
                    self.add_resources(item, stdout=bar)
                    bar.update(1)
                print(f"[+] {len(res)} resource(s) added successfully")
        except ValueError:
            return 1
        else:
            return 0

    def list_resources(self, *args, name_regex: str = None) -> list[_u.Path] | None:
        """

            :param args: resource types (short or long name)
            :param name_regex: regex applied on the resource name
            :return:
            """
        def filter_by_name():
            # cast to list to avoid exhausting the generator
            return list(filter(lambda p: re.search(name_regex, p.name) is not None, results))

        def print_ordered(*items):
            _div = '-' * 30
            header = f"\n{RES_BY_TYPE[rtype]['name'].upper()}"
            start = len(res_pool) + 1
            if len(items) > 0:
                print(f"{header}{'' if name_regex is None else f' (filter: {name_regex})'}\n{_div}")
                print(*[f"{f'{ind}. ' if ind <= 9 else f'{ind}.'} {item}" for ind, item in enumerate(items, start)],
                      _div, sep='\n')

        res_pool = list()
        for rtype in args:
            if rtype == 'all':  # Recursive call with all existing res types
                return self.list_resources(*RES_BY_TYPE.keys(), name_regex=name_regex)
            elif rtype == 'vpn':  # Special case VpnClient
                results = [VpnClient(f) for f in RES_BY_TYPE[rtype]['path'].glob('*.ovpn')]
                if name_regex is not None:
                    results = filter_by_name()
                print_ordered(*results)
                res_pool.extend([vpn.path for vpn in results])
            elif rtype in RES_BY_TYPE:  # Any other type of HtbResource
                results = list(RES_BY_TYPE[rtype]['path'].glob('*'))  # cast to list to avoid exhausting the generator
                if name_regex is not None:
                    results = filter_by_name()
                print_ordered(*[p.name for p in results])
                res_pool.extend(results)
            else:
                print(f"[-] Unknown resource type '{rtype}'")

        _u.Cache.set(res_pool)
        if len(res_pool) == 0:
            print("[-] No search results")
        return res_pool

    def use_resource(self, *args) -> HtbResource | VpnClient | list[HtbResource] | None:
        """

        :param args: Name(s) or ID(s), or list of them, indicating which resources should be opened
        :return: A HtbResource if the specified resource exists. Otherwise None
        """
        if len(args) == 1:  # Select single resource, using index or name
            tg = _u.FsTools.search_res_by_name_id(args[0])
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
    TIER_COST = {
        '0': 10,
        'I': 50,
        'II': 100,
        'III': 500,
        'IV': 1000
    }
    COST_TIER = {v: k for k, v in TIER_COST.items()}
    # COST_TIER = { 10: '0', 50: 'I', 100: 'II', 500: 'III', 1000: 'IV' }

    def __init__(self):
        super().__init__(res_type='mod')
        self._tier = None
        self.cost = None
        self.duration = None
        self.summary = None
        self.sections = []


    @property
    def tier(self):
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
    def total_sections(self):
        if isinstance(self.sections, list):
            return len(self.sections)
        else:
            return self.sections

    def __repr__(self):
        return f"HtbModule({self.type}, {self.info.name})"

    def to_dict(self):
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

    def update(self, **kwargs):
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

    def makedirs(self):
        try:
            _u.FsTools.dump_file(self.path / 'info.json', json.dumps(self.to_dict()), exist_ok=False)
        except FileExistsError:
            print(f"[!] Resource '{self.info.name}' already exists. Only info.json will be updated")
            _u.FsTools.dump_file(self.path / 'info.json', json.dumps(self.to_dict()), exist_ok=True)
        else:
            os.makedirs(self.path / 'resources')
            _u.FsTools.render_template('module_index.md', self.path / 'index.md', mod=self)
            for ind, section in enumerate(self.sections, 1):  # Create one file per each section
                _u.FsTools.render_template(
                    'mod_section.md',
                    self.path / f"{f'0{ind}' if ind < 10 else ind}_{section.name}.md",
                    section=section
                )

    def add_section(self, _type, title) -> Section:
        self.sections.append(Section(_type, title))
        return self.sections[-1]

    def remove_section(self, index: int) -> Section:
        return self.sections.pop(index)

class HtbPath(HtbResource):
    def __init__(self, res_type :str =None):
        super().__init__(res_type=res_type)
        self._progress = 0.0
        self.cost = None
        self.duration = None
        self.sections = None # int
        self.modules = []

    @property
    def tier(self):
        """
        Iterates the modules creating a set with all the different tiers

        :return: list containing all the different tiers
        """
        return list(set([m.tier for m in self.modules]))


    # TODO: completed = completed_mods / total_mods
    @property
    def status(self):
        # return f"{self._completed * 100} %"
        return f"{self._progress * 100} % completed"

    def to_dict(self):
        json_data = super().to_dict()
        # Tier not added since it is always deduced from self.modules
        json_data['cost'] = self.cost
        json_data['duration'] = self.duration
        json_data['sections'] = self.sections
        json_data['modules'] = [mod.to_dict() for mod in self.modules]

        return json_data

    def update(self, **kwargs):
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

    def makedirs(self, missing_ok: bool = False):
        try:
            _u.FsTools.dump_file(self.path / 'info.json', json.dumps(self.to_dict()), exist_ok=False)
        except FileExistsError:
            print(f"[!] Resource '{self.info.name}' already exists. Only info.json will be updated")
            _u.FsTools.dump_file(self.path / 'info.json', json.dumps(self.to_dict()), exist_ok=True)
        else:
            _u.FsTools.render_template('path_index.md', self.path / 'index.md', path=self)
            # TODO: Should I create soft link files?
            # os.symlink(f"../../modules/{mod.name}", mod.name, target_is_directory=True)
            bar = _u.tqdm(self.modules, unit='mod')
            for mod in self.modules:  # Create soft-links to modules
                bar.write(f"[*] Adding mod: {mod.info.name}")
                if not (missing_ok or mod.path.exists()):
                    bar.write(f"  [-] Module not found in local vault")
                    # If module not found locally, request the user to get the info from the web
                    _u.FsTools.js_to_clipboard(bar)
                    bar.write(f"  [*] Opening module URL and waiting for input")
                    _u.open_browser_tab(mod.info.url, delay=3)
                    while True:
                        try:
                            _u.FsTools.js_to_clipboard(bar)
                            _u.FileClipboard.set()  # Paste clipboard into file, save and exit
                            # add_one(load(ut.FileClipboard.get()).makedirs())  # Init module
                            load(_u.FileClipboard.get()).makedirs()  # Init module
                            bar.write(f"  [+] Module added")
                            break
                        # TODO: catch rest of exceptions to exit gracefully
                        except json.decoder.JSONDecodeError:
                            bar.write("   > Not a valid JSON")
                bar.update(1)

class SkillPath(HtbPath):
    def __init__(self):
        super().__init__(res_type='spt')

class JobRolePath(HtbPath):
    def __init__(self):
        super().__init__(res_type='jpt')

#######  H T B   L A B   C L A S S E S  ####################

class HtbMachine(HtbResource):
    def __init__(self, res_type :str =None):
        super().__init__(res_type=res_type)
        self.tasks = list()

    def to_dict(self, path: str | _u.Path = None):
        json_data = super().to_dict()
        # Add tasks
        json_data['tasks'] = [tsk.to_dict() for tsk in self.tasks]
        if path is not None:
            if path.is_dir():
                with open(path / 'info.json', 'w') as file:
                    json.dump(json_data, file)
            elif path is not None:
                with open(path, 'w') as file:
                    json.dump(json_data, file)
        return json_data

    def update(self, **kwargs):
        self.info.update(kwargs.pop('info'))
        self.about.update(kwargs.pop('about'))
        self.tasks = [Task(**item) for item in kwargs.pop('tasks')]

        # Add custom attributes
        for key, value in kwargs.items():
            setattr(self, key, value)

    def makedirs(self):
        try:
            _u.FsTools.dump_file(self.path / 'info.json', json.dumps(self.to_dict()), exist_ok=False)
        except FileExistsError:
            print(f"[!] Resource '{self.info.name}' already exists. Only info.json will be updated")
            _u.FsTools.dump_file(self.path / 'info.json', json.dumps(self.to_dict()), exist_ok=True)
        else:
            os.makedirs(self.path / 'evidences/screenshots', exist_ok=True)
            _u.FsTools.dump_file(
                self.path / 'sol_pdf.txt',
                f"Download the solution from the URL: {self.info.url}\n"
            )
            _u.FsTools.render_template(
                'writeup.md',
                self.path / 'writeup.md',
                resource=self
            )

    def add_task(self, text: str = None, answer: str = None, points: int = 0, index: int = None) -> Task:
        self.tasks.append(Task(
            number=len(self.tasks) + 1 if index is None else index,
            text=text,
            answer=answer,
            points=points
        ))
        return self.tasks[-1]

    def remove_task(self, index: int) -> Task:
        return self.tasks.pop(index)

class StartingPointMachine(HtbMachine):
    def __init__(self):
        super().__init__(res_type='stp')

class LabMachine(HtbMachine):
    def __init__(self):
        super().__init__(res_type='mch')

class ChallengeMachine(HtbMachine):
    def __init__(self):
        super().__init__(res_type='chl')
        self.info.logo = 'https://app.hackthebox.com/images/logos/htb_ic2.svg'

class SherlockMachine(HtbMachine):
    def __init__(self):
        super().__init__(res_type='shr')

class MachineTrack(HtbMachine):
    def __init__(self):
        super().__init__(res_type='trk')
        self.tasks = list[HtbMachine]

    def update(self, **kwargs):
        self.info.update(kwargs.pop('info'))
        self.about.update(kwargs.pop('about'))
        self.tasks = load(kwargs.pop('tasks'))

            # Add custom attributes
        for key, value in kwargs.items():
            setattr(self, key, value)

    def makedirs(self):
        try:
            _u.FsTools.dump_file(self.path / 'info.json', json.dumps(self.to_dict()), exist_ok=False)
        except FileExistsError:
            print(f"[!] Resource '{self.info.name}' already exists. Only info.json will be updated")
            _u.FsTools.dump_file(self.path / 'info.json', json.dumps(self.to_dict()), exist_ok=True)
        else:
            _u.FsTools.render_template('track_index.md', self.path / 'index.md', track=self)

class ProLabMachine(HtbMachine):
    def __init__(self):
        super().__init__(res_type='lab')
        self.entry_point = None

    def update(self, **kwargs):
        self.info.update(kwargs.pop('info'))
        self.about.update(kwargs.pop('about'))

        self.entry_point = kwargs.pop('entry_point')
        self.tasks = [Task(**item) for item in kwargs.pop('tasks')]
        # Add custom attributes
        # for key, value in kwargs.items():
        #     setattr(self, key, value)

    def makedirs(self):
        try:
            _u.FsTools.dump_file(self.path / 'info.json', json.dumps(self.to_dict()), exist_ok=False)
        except FileExistsError:
            print(f"[!] Resource '{self.info.name}' already exists. Only info.json will be updated")
            _u.FsTools.dump_file(self.path / 'info.json', json.dumps(self.to_dict()), exist_ok=True)
        else:
            _u.FsTools.render_template('prolab_index.md', self.path / 'index.md', lab=self)
            for m in self.about.targets:
                _tg_path = self.path / f'targets/{m.info.name}'
                os.makedirs(_tg_path / 'evidences/screenshots', exist_ok=True)
                _u.FsTools.render_template('basic_writeup.md', _tg_path / 'writeup.md', resource=m)

class MachineFortress(HtbMachine):
    def __init__(self):
        super().__init__(res_type='ftr')

    def makedirs(self):
        try:
            _u.FsTools.dump_file(self.path / 'info.json', json.dumps(self.to_dict()), exist_ok=False)
        except FileExistsError:
            print(f"[!] Resource '{self.info.name}' already exists. Only info.json will be updated")
            _u.FsTools.dump_file(self.path / 'info.json', json.dumps(self.to_dict()), exist_ok=True)
        else:
            os.makedirs(self.path / 'evidences/screenshots', exist_ok=True)
            _u.FsTools.render_template(
                'writeup.md',
                self.path / 'writeup.md',
                resourece=self
            )

class MachineBattleground(HtbMachine):
    def __init__(self):
        super().__init__(res_type='btg')
        raise NotImplementedError

############################################################################

def load(data :str | _u.Path | list | dict) -> HtbResource | list[HtbResource] | None:
    """Parses JSON data returned by toolkit.js

    :param data: Serialized data. It may be a JSON string/file, a serialized HtbResource or a list of them
    :return: the deserialized HtbResource or list of them
    """
    _builder = {
        'module': HtbModule,
        'skill-path': SkillPath,
        'job-role-path': JobRolePath,
        'starting-point': StartingPointMachine,
        'machine': LabMachine,
        'challenge': ChallengeMachine,
        'sherlock': SherlockMachine,
        'track': MachineTrack,
        'pro-lab': ProLabMachine,
        'fortress': MachineFortress,
        'battleground': MachineBattleground
    }
    if isinstance(data, dict):  # Base case, load a HtbResource from a json
        try:
            htb_resource = _builder[data.pop('_type')]()
        except KeyError as e:
            print(f"[!] Unknown resource type. {e}")
            return None
        else:
            htb_resource.update(**data)
            return htb_resource
    elif isinstance(data, list):  # Load several HtbResources
        return [load(item) for item in data]
    elif isinstance(data, _u.Path) or _u.Path(data).exists():  # Load data from JSON file
        try:
            with open(data, 'r') as file:
                return load(json.load(file))
        except FileNotFoundError:
            print(f"[-] Not a HtbResource")
            return None
    else:  # Load data from JSON string
        return load(json.loads(data))
