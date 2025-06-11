# TEMPLATE
from pathlib import Path
import sys

ROOT_PKG = Path(__file__).parents[1] # Points to install-dir/src/
sys.path.insert(0, str(ROOT_PKG))

from htv.utils import CONF, FsTools, Templater, open_browser_tab, Git, Cache
from collections.abc import Iterable
from typing import TextIO
from htv import ROOT_DIR
from tqdm import tqdm

import importlib
import shutil
import yaml
import json
import os
import re

__all__ = [
    'HtvVault', 'CustomResource', 'HtvResource', 'HtvPath', 'HtvModule', 'HtvExercise', 'DataSources'
]
# todo info.name or metadata.name ==> metadata.title
class Metadata:

    def __init__(self):
        """Basic metadata info"""
        self.title = None
        self.tags = list()
        self.url = None
        self.description = None
        self.difficulty = None
        self.status = None
        self.logo = None
        self.authors = list()
        self.creation_date = Templater.now()
        self.completion_date = None

    def __repr__(self) -> str:
        return f"Metadata({', '.join(list(vars(self).keys())[:3])}, ...)"

    def update(self, **kwargs) -> None:
        """Update Info attributes

        :param kwargs:  Key:value pairs to be updated
        :return: None
        """
        for key, value in kwargs.items():
            setattr(self, key, value)

    def to_dict(self):
        return self.__dict__

class CustomResource:
    # Code reference
    __type__ = None  # :str E.g. htb.mod
    # File reference
    __resource_dir__ = None  # :str E.g. academy/module
    # Specific file extension associated to this resource
    __file_ext__ = None # str: eg. .ovpn

    def __init__(self):
        pass
        # self._name = None # File name

    @property
    def categories(self) -> list[str]:
        """Resource categorization

        Categories are extracted from the relative path of the resource (`self.__resource_dir__`)

        :returns : A list will the resource categories
        """
        return str(self.__resource_dir__).split('/')

    # @property
    # def backlink(self) -> str:
    #     _link_parts = [  # Base link, home + resource name
    #         f"[Home]({'../' * (len(self.categories) + 1)}README.md)", # Home link
    #         self.name
    #     ]
    #     for ind, _ in enumerate(reversed(self.categories), 1):  # Add parent categories links
    #         _link_parts.insert(1, f"[{_}]({'../' * ind}README.md)")
    #     return ' > '.join(_link_parts)

    # def front_matter(self):
    #     pass

    @property
    def name(self) -> str:
        """Secure file name (no spaces, no special chars, lowercased)"""
        # re.sub('[ ,&-/:]+', '-', str(self._name)).lower()
        if hasattr(self, 'metadata'):
            return FsTools.secure_dirname(self.metadata.title)
        else:
            return FsTools.secure_dirname(getattr(self, '_name'))

    @property
    def path(self) -> Path:
        """Absolute path of this resource"""
        return CONF['VAULT_DIR'] / self.__resource_dir__ / self.name

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f"{Templater.class_str(self)}({self.name})"

    def to_dict(self) -> dict:
        """

        :return: dict representation of this HtbResource
        """
        _data = dict(
            __type__=self.__type__,
            # __resource_dir__=self.__resource_dir__  # Ignore this attribute
        )
        for k, v in vars(self).items():
            if k.startswith('_'):  # Replace private attributes by their getter
                k = k.replace('_', '')
                v = self.__getattribute__(k)
            if isinstance(v, str | int | float | dict | None):
                _data[k] = v
            elif isinstance(v, CustomResource | Metadata):
                _data[k] = v.to_dict()
            elif isinstance(v, Iterable):  # sections
                _data[k] = list()
                for _ in iter(v):
                    if isinstance(_, str | int | float | dict | None):
                        _data[k].append(_)
                    elif isinstance(_, HtvResource | Metadata | HtvModule.Section | HtvExercise.Task):
                        _data[k].append(_.to_dict())
                    else:
                        raise TypeError(f"Unknown type ({type(k)}) for attribute '{k}' ({_})")
            else:
                print(f"[-] Unknown type for attribute '{k}' ({v})")
                _data[k] = v
        return _data

    def update(self, **kwargs):
        """Update the attributes of this resource

        :param kwargs: Attributes to be updated
        :return: None
        """
        for key, value in kwargs.items():
            if re.match(r"^[-+]?\d$", str(value)) is not None:
                value = int(value)
            elif re.match(r"^[-+]?\d*\.\d+$", str(value)) is not None:
                value = float(value)
            setattr(self, key, value)

    def list_resources(self, regex: str = None):
        """List resources of this type

        :param regex: Regex to be applied on the resource name to filter the results. Wildcards allowed. If None, no filtering
        :return: A list with the resources found in local vault
        """
        regex = '*' if regex is None else regex
        return DataSources.load(
            filter(lambda x: x.is_dir(), (CONF['VAULT_DIR'] / self.__resource_dir__).glob(regex))
        )

    def open(self):
        print(f"[*] Using resource '{self.name}' ...")
        pass

class HtvResource(CustomResource):
    """
        Dataclass representing a generic HtbResource.
        This class is the parent of all resource types that can be found in HTB

        :cvar __type__: [str] Resource type ID (short-name). Possible values `datasources/sources.yml`
        :cvar __resource_dir__: [str] Location for these resources within the vault (relative path)
        # :ivar _metadata: [:class:`Metadata`]: resource information
        """
    __file_ext__ = '.json'

    def __init__(self, **kwargs):
        """Initializes a HtvResource instance"""
        super().__init__()
        self._metadata = Metadata()
        self._metadata.update(**kwargs)

    @property
    def metadata(self):
        return self._metadata

    @metadata.setter
    def metadata(self, value: dict):
        self.metadata.update(**value)

    def read_stdin(self, _stdout: tqdm | TextIO = sys.stdout):
        if self.metadata.url is not None:
            _stdout.write(f"[*] Opening module URL and waiting for input\n")
            open_browser_tab(self.metadata.url, delay=3)
        else:
            _stdout.write("[-] Resource's URL not defined. Manual browsing required")
        self.copy_js_toolkit(_stdout=_stdout)

        while True:
            # Init module
            _user_input = input('>  json: ')
            if _user_input == 'skip':
                return None
            res = DataSources.load(_user_input)
            if res is not None:
                _stdout.write(f"[+] Module added\n")
                return res

    def __dir_struct__(self, *args) -> list:
        return list(args)

    def makedirs(self) -> None:
        """Dump serialized object to file

        Serializes and dumps this instance into a file (info.json).
        Additional arguments are tuples specifying other default files to be created,

        :return: None
        """
        # TODO: check if categories have README.md, if not create it

        if self.name in [None, '']:
            raise ValueError(f"Resource '{self.__repr__()}' has no name (HtvResource.name)")
        if os.path.exists(self.path / 'info.yml'):
            print(f"[-] Resource '{self.name}' already exists. Updating info.yml")
        # with open(self.path / 'info.json', 'w') as file:
        #     json.dump(self.__dict__, file)
        # FsTools.dump_files(args, root_dir=self.path)  # Add custom files
        FsTools.dump_files([
            ('info.yml', yaml.dump(self.to_dict(), default_flow_style=True)), # Flat lists and dicts
            # ('info.json', json.dumps(self.to_dict())),
            *self.__dir_struct__()
        ], root_dir=self.path, exists_ok=True)

        # Create parent categories if they do not exist
        for _ in range(1, len(self.categories) + 1):
            # if not os.path.exists(CONF['VAULT_DIR'] / f"{'/'.join(self.categories[:_])}/README.md"):
            FsTools.dump_file(
                CONF['VAULT_DIR'] / f"{'/'.join(self.categories[:_])}/README.md",
                't:category.md',
                exists_ok=True,
                resource=Path('/'.join(self.categories[:_])),
                VAULT_DIR=CONF['VAULT_DIR']
                # index=(CONF['VAULT_DIR']/Path('/'.join(self.categories[:_]))).glob('[a-z]*')
            )

    def open(self) -> None:
        """Open the resource

        Open the resource in all the possible ways: opening the URL in a web browser,
        opening the Vault with your favorite editor (Obsidian, Code),
        and opening virtual-box to run your PwnBox or Kali instance.

        :return: None
        """
        super().open()
        open_browser_tab(self.metadata.url)
        # TODO: open text editor, open VBox manager
        # IF text editor already opened, pass
        # If Vbox already opened, pass

    def copy_js_toolkit(self, _stdout: tqdm = None):
        FsTools.copy_js_toolkit(
            ROOT_DIR / f"src/htv/datasources/{self.categories[0]}/toolkit.js",
            _stdout=_stdout
        )

class HtvModule(HtvResource):
    """
    Modules represent some knowledge that is related together around a topic.
    It includes Sections, which are single pages focused on a single subtopic.

    Modules can be aggregated in a :class:`HtvPath`

    :ivar _sections: list[str] Module sections (:class:`Section`)

    """

    __type__ = 'mod'  # E.g. htb.mod
    __resource_dir__ = 'personal/module'  # E.g. academy/module

    class Section:
        """
        Sections are like data-pills. A post, not long, focused on a single topic

        Dataclass representing a Section of a :class:`HtbModule`

        :ivar __type__: [str] Type of section (interactive, document)
        :ivar title: [str] Section title used in the section template. May contain spaces
        :ivar name: [str] Secured file name (:func:`utils.FsTools.secure_filename`)

        :param __type__: Type of section (interactive, document)
        :param title: Section title, may contain spaces

        """

        def __init__(self, __type__: str = None, title: str = None, number: int = 1):
            self.__type__ = 'undefined' if __type__ is None else str(__type__)
            self.title = 'undefined' if __type__ is None else str(title).strip()
            self.name = FsTools.secure_filename(self.title)
            self.number = int(number)

        def __lt__(self, other):
            return self.number < other.number

        @property
        def __file_name__(self):
            return f"{f'0{self.number}' if self.number < 10 else self.number}_{self.name}.md"

        def to_dict(self) -> dict:
            return dict(__type__=self.__type__, title=self.title)


    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._sections = list()

    @property
    def sections(self) -> int | list[Section]:
        return self._sections

    @sections.setter
    def sections(self, value: int | list[dict]) -> None:
        if isinstance(value, list):
            self._sections = sorted([HtvModule.Section(**item, number=ind) for ind, item in enumerate(value, 1)])
        else:
            self._sections = [HtvModule.Section()] * value

    # @property
    # def markdown_index(self) -> str:
    #     _index = ['## Index\n', '\n']
    #     for ind, _ in enumerate(self.sections, 1):
    #         _index.insert(1, f"{ind}. [{_.title}](./{_.__file_name__})")
    #     return '\n'.join(_index)

    def __dir_struct__(self, *args) -> list:
        # Add custom files here
        # TODO: generate sections
        # self.sections.index()
        return super().__dir_struct__(
            ('README.md', 't:module.md', dict(resource=self)),
            self.path / 'resources/img',
            *[(_.__file_name__, 't:mod_section.md', dict(resource=self, section=_)) for _ in self.sections],
            # *[section.to_file() for section in self.sections],
            * args
        )

    def add_section(self, __type__: str, name: str) -> Section:
        """Adds a new section to this module

        :param __type__: Type of section (interactive / document)
        :param name: Title of the section. May contain spaces
        :return: the new :class:`Section` added
        """
        self.sections.append(HtvModule.Section(__type__, name))
        return self.sections[-1]

    def remove_section(self, index: int) -> Section:
        """Removes a section from this module

        :param index: Index of the section to be removed
        :return: the removed :class:`Section`
        """
        return self.sections.pop(index)

class HtvPath(HtvResource):
    """**Abstract class** representing a Path in the HTB academy

    :ivar _sections: [list] Collection of modules and/or exercises

    """
    __type__ = 'path'
    __resource_dir__ = 'personal/path'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._sections = list() # Collection of modules and/or exercises
        self._progress = 0.0

    # TODO: status = completed_mods / total_mods (completed)
    @property
    def progress(self) -> str:
        """Completion status string"""
        return f"{self._progress * 100} % completed"
        # return f"TODO: 0 % completed"

    @property
    def sections(self):
        """Collection of modules and/or exercises"""
        return self._sections

    @sections.setter
    def sections(self, value: list[dict]):
        for item in value: # Sections are Modules/Exercises
            m = DataSources.get(item.pop('__type__'))
            m.update(**item)
            self._sections.append(m)


    def __dir_struct__(self, *args) -> list:
        # Add custom files here
        return super().__dir_struct__(
            ('README.md', 't:path.md', dict(resource=self)),
            *args
        )

    def makedirs(self, *args, missing_ok: bool = False) -> None:
        """Create the directory structure of the path, including the corresponding modules/exercises

        :param missing_ok: If True, user will not be prompted to add the missing modules
        :return: None
        """
        super().makedirs()

        # TODO: Should I create soft link files?
        # os.symlink(f"../../modules/{st.name}", st.name, target_is_directory=True)

        bar = tqdm(self.sections, unit='section')
        for st in self.sections:  # TODO Create soft-links to modules
            if not (missing_ok or st.path.exists()):
                bar.write(f"[-] Path section not found in local vault ({st.__repr__()})")
                # If module not found locally, request the user to get the info from the web
                st = st.read_stdin(_stdout=bar)
                if isinstance(st, HtvModule | HtvExercise):
                    st.makedirs()
            bar.update(1)

class HtvExercise(HtvResource):
    """**Abstract class** representing a resource from HTB lab

    :ivar _tasks: [list[:class:`Task`]] List of tasks associated to this resource

    """
    __type__ = 'exr'  # E.g. htb.mod
    __resource_dir__ = 'personal/exercise'  # E.g. academy/module

    class Task:
        """
        Dataclass representing a Task within a :class:`HtbResource`

        :ivar number: [int] Task number (default 1)
        :ivar text: [str] Task text, brief question or goal
        :ivar answer: [str] Task answer or solution (default None)
        :ivar points: [int] Points obtained when completing the task
        """

        def __init__(self, text: str = None, answer: str = None, points: int = None, number: int = None):
            """Initializes a Task instance

            :param text: Task text
            :param answer: Task answer
            :param points: Task points
            :param number: Task number (default 1)
            """
            try:
                self.number = int(number)
            except (ValueError, TypeError):
                self.number = 1
            self.text = f"Task {self.number}" if text is None else str(text)
            self.answer = 'ANSWER' if answer is None else str(answer)
            try:
                self.points = int(points)
            except (ValueError, TypeError):
                self.points = 0

        def __lt__(self, other):
            return self.number < other.number

        def to_dict(self) -> dict:
            return dict(text=self.text, answer=self.answer, points=self.points)

        def to_markdown(self) -> str:
            """

            :return: string with the MarkDown representation of the Task
            """
            return f"> T{self.number}. {f'[{self.points} pts] ' if self.points > 0 else ''}{self.text}\n> > **{self.answer}**"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._tasks = list()

    @property
    def tasks(self) -> list[Task]:
        return self._tasks

    @tasks.setter
    def tasks(self, value: list[dict]) -> None:
        self._tasks = sorted([HtvExercise.Task(**_, number=ind) for ind, _ in enumerate(value, 1)])


    def __dir_struct__(self, *args) -> list:
        # Add custom files here
        return super().__dir_struct__(
            (self.path / 'evidences/screenshots'),
            ('README.md', 't:exercise.md', dict(resource=self)),
            *args
        )

    def add_task(self, text: str = None, answer: str = None, points: int = 0, index: int = None) -> Task:
        """Adds a new :class:`Task` to this machine

        :param text: Text of the task
        :param answer: Answer of the task
        :param points: Points of the task
        :param index: Index of the task. Defaults to None (auto-increment)
        :return: the added :class:`Task`
        """
        self.tasks.append(HtvExercise.Task(
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

    def post(self, include_tasks: bool = False):
        # try commit and push current work on main.
        #
        #
        #
        # n branch
        # Switch to gh-pages branch

        # Add front matter
        # Extract linked resources (images, files, etc)
        # add linked resources to VAULT_DIR/docs/assets
        pass

class HtvVault:
    """
        Dataclass representing the HtbVault.
        It allows to manage the vault, adding/removing/opening resources,
        listing them or initializing/deleting the entire vault

        :ivar _path: [`Path`] Path to the vault. May contain environment variables
        :param path [str|Path]: Path to the vault. If None, the default directory from conf will be used

        """
    """List with all the existing resource types of this Vault"""
    __resources__ = None # list

    @staticmethod
    def clean() -> int:
        """Clean-up vault

        Deletes hidden directories created by text editors, in addition to cached and temp files.
        These files/dirs usually start by '.' or '_'. `.gitignore` file and `.git` dir are always excluded.

        :return: 0 on success. 1 if an error occurred
        """
        print(f"[*] Cleaning the vault...")
        for p in [*CONF['VAULT_DIR'].glob('**/[._]*')]:
            if p.name not in ['.git', '.gitignore']:
                print(f"[*] Deleting {p}")
                if p.is_dir():
                    shutil.rmtree(p)
                else:
                    p.unlink()
        print(f"[+] Vault clean-up completed")
        return 0

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
            return sum([HtvVault.remove_resources(res) for res in args])


    def __init__(self, path: str | Path = None):

        # si tu me das un path
        # VAULT_DIR / path
        if path is None:  # Main vault initialized
            self._path = str(CONF['VAULT_DIR'])
        elif os.path.isabs(os.path.expandvars(path)):
            CONF.update_values(VAULT_DIR=path)
            self._path = str(path)
        else:  # Path relative to vault
            self._path = CONF['VAULT_DIR'] / path
        # self.sub_vaults = list()
        # for _ in self.path.glob('[a-z0-9]*'):
        #     self.add_subvaults(_.name)

    @property
    def path(self):
        return Path(os.path.expandvars(self._path))

    @property
    def categories(self):
        return ['vault']

    def __str__(self) -> str:
        return self.path.name

    def __repr__(self) -> str:
        return f"{Templater.class_str(self)}({self.path.name})"

    def __dir_struct__(self) -> list:
        return [
            ('.gitignore', 'vpn/\n.obsidian\n'),
            ('README.md', 't:vault.md'),
        ]

    def makedirs(self, reset: bool = False) -> int:
        """Create vault dir structure

        :param reset: If True, and the vault already exists, the vault is deleted and reset to initial state
        :return: 0 if vault initialized successfully. 1 otherwise
        """
        if self.path.exists():
            if reset:
                self.removedirs()
            else:
                print(f"[!] Directory already exists ({self.path})")
                return 1
        # CONF.update_values(VAULT_DIR=self._path)  # Update conf to use this vault
        if self.__resources__ is None:
            print(f"[*] Initializing vault...")
            FsTools.dump_files(self.__dir_struct__(), root_dir=self.path)
            for ds in DataSources.get('all'):  # Get resources associated to this Vault category
                print(f"  [*] Adding category '{ds.path.name}'")
                ds.makedirs(reset=reset)
            print(f"[+] Vault initialized successfully")
            if not (CONF['VAULT_DIR'] / '.git').exists():  # Initialize repo
                Git.init()
                Git.config_git_user()
                Git.commit('Init vault')
        else:
            for _ in self.__resources__:
                # TODO: category.makedirs()
                os.makedirs(CONF['VAULT_DIR'] / _.__resource_dir__)  # 1 dir for each sub-category
        return 0

    def removedirs(self) -> int:
        """Removes the entire vault

        :return: 0 on success
        """
        print(f"[!] Deleting the entire vault")
        shutil.rmtree(self.path)
        # CONF.reset()  # Reset configuration so VAULT_DIR points to default location again
        return 0

    def add_resources(self, res: HtvResource | list[HtvResource], _stdout: tqdm | TextIO = sys.stdout) -> int:
        """Add resource(s) to the vault

        :param res: :class:`HtbResource` or a list of them. If None, user will be prompt to input required Resource data
        :param _stdout: Stdout to log information. Default to STDOUT
        :return: number of resources added successfully
        """
        # try:
        _ret = 0
        if res is None:  # Try to load Resource from json
            self.copy_js_toolkit()  # Js tools copied to clipboard
            _ret += self.add_resources(DataSources.load(input('>  json: ')))  # Add resource, info from stdin
        elif isinstance(res, HtvResource):
            _stdout.write(f"[*] Adding resource {res.__repr__()}\n")
            # print(f"[*] Adding resource {res}")
            res.makedirs()
            # print(f"[+] Resource added {res}")
            # _stdout.write(f"[+] Resource added {res}\n")
            _ret = 1
            # TODO: create base class BasicResource
            # which represents a custom object in the vault
            # This resource does not have makedirs, and some other methods, which are only included in HtvResource
        elif isinstance(res, list):
            bar = tqdm(res, unit='resource')
            for item in res:
                _ret += self.add_resources(item)#, stdout=bar)
                bar.update(1)
            print(f"[+] {len(res)} resource(s) added successfully")
        else:
            print(f"[-] Not a HtvResource ({type(res)})")
            _ret = 0
        return _ret
        # except ValueError:
        #     return 1
        # else:
        #     return 0

    def list_resources(self, *args, regex: str = None) -> list[Path]:
        """List resources from the vault

        :param args: resource types :attr:`HtbResource.type`
        :param regex: regex applied on the resource name. If None, no filter is applied
        :return: A list with the resources found, or None if no match
        """

        def print_ordered(*items, start_idx: int = 0):
            if len(items) > 0:
                _div = '-' * 30
                header = f"\n{items[0].categories[-1].upper()}"
                # start = len(res_pool) + 1
                print(f"{header}{'' if regex is None else f' (filter: {regex})'}\n{_div}")
                print(*[f"{f'{ind}. ' if ind <= 9 else f'{ind}.'} {item}" for ind, item in enumerate(items, start_idx)],
                      _div, sep='\n')

        res_pool = list()

        if not self.path.exists():
            print(f"[!] Vault not found ({self.path}). Initialize the vault first")
            return res_pool
        elif len(args) == 0 or 'all' in args:
            # TODO: iterate Datasources.get('all')
            if regex is None:
                regex = ''
            res = list(filter(
                lambda x: re.search(regex, x.path.name, re.I) is not None,
                DataSources.get('all')
            ))
            print_ordered(*res, start_idx=1)
            res_pool.extend([_.path for _ in res])
        else:  # Get specific category
            for rtype in args:
                res = DataSources.get(rtype)
                if res is not None:  # Call subclass implementation
                    res_items = res.list_resources(regex=regex)
                    print_ordered(*res_items, start_idx=len(res_pool) + 1)
                    res_pool.extend([_.path for _ in res_items])
        Cache.set(res_pool)
        if len(res_pool) == 0:
            print(f"[-] No search results for [{args} regex: {regex}]")
        return res_pool

    def use_resource(self, *args) -> HtvResource | list[HtvResource] | None:
        """Opens resource(s)

        :param args: Name(s) and/or index(es) of the resources to be opened
        :return: A HtbResource, or a list of them. None if the resource could not be opened
        """
        if len(args) == 1:  # Select single resource, using index or name
            tg = FsTools.search_res_by_name_id(args[0])
            # TODO:
            # Load the resource file

            # if tg.is_file() and tg.name.endswith('.ovpn'):  # Init VpnClient
            #     tg = VpnClient(tg)
            # elif tg.is_dir():  # Init HtbResource
            #     tg = load(tg / 'info.json')
            # else:  # Path is not a HtbResource nor VpnClient
            #     print(f"[-] Unknown target '{tg}' ")
            #     return None
            tg = DataSources.load(tg)  # Load from path
            print(f"[*] Using resource '{tg.name}' ...")
            tg.open()  # Open the resource
            return tg
        else:
            return [self.use_resource(item) for item in args]  # Recursive call

    @staticmethod
    def post_resources(resources: list):
        for r in resources:
            r.post()

    # def add_subvaults(self, name: str, default_files: Iterable = None):
    #     """TODO: add initialize new category
    #
    #     :param name: Name for the category
    #     :param default_files: Default files to be created with the category
    #     """
    #     """
    #     cat-name/
    #         info.json (vault.json)? with readme is really necessary?
    #     """
    #     # If subvault is defined in datasources/sources.yml get it from there
    #     if DataSources.get(name) is not None:
    #         self.sub_vaults.append(DataSources.get(name))
    #         DataSources.get(name).makedirs()
    #     else: # Create sub-vault from scratch
    #         os.makedirs(name)
    #         if default_files is not None:
    #             FsTools.dump_files(default_files, root_dir=self.path / name)

    def copy_js_toolkit(self) -> None:
        FsTools.copy_js_toolkit(ROOT_DIR / f"src/htv/datasources/{self.path.name}/toolkit.js")

class DataSources:

    @staticmethod
    def get(category: str) -> HtvModule | HtvPath | HtvExercise | HtvVault | list[HtvVault] | None:
        with open(Path(__file__).parents[1] / 'datasources/sources.yml', 'r') as file:
            ds = yaml.safe_load(file)  # Dict with {cat_id: path} pairs
        if category == 'all':  # Return top-level categories
            # TODO: iterate ds keys, (parent-keys only)
            return [DataSources.get(cat) for cat in ds.keys()]
        elif category in ['mod', 'personal.mod']:
            return HtvModule()
        elif category in ['path', 'personal.path']:
            return HtvPath()
        elif category in ['exr', 'personal.exr']:
            return HtvExercise()

        parent_cat = Templater.camel_case(category.split('.').pop(0), sep='-', lower_first=True)

        if category.find('.') == -1:
            try:
                return getattr(
                    importlib.import_module(f"datasources.{parent_cat}"),
                    'Vault')()
            except ModuleNotFoundError as e:
                print(f"[-] {e}")
                return None
        try:
            cat_path = None

            for _ in category.split('.'):
                if cat_path is None:
                    cat_path = ds[_]
                else:
                    cat_path = cat_path[_]
            return getattr(
                importlib.import_module(f"datasources.{parent_cat}"),
                Templater.camel_case(cat_path.replace('-', '/'), sep='/')
            )()
        except KeyError as e:
            print(f"[!] Unknown (sub-)category '{e.args[0]}' ({category})")
            return None
        except ModuleNotFoundError as e:
            print(f"[-] {e}")
            return None
        except ImportError as e:
            print(e)
            print(f"[!] Module '{category}' cannot be imported")
            return None


    @staticmethod
    def load(data: str | dict | Path | Iterable) -> HtvResource | list[HtvResource] | None:
        """Load serialized Resources

        :param data: Serialized data. It may be a JSON string/file, a serialized HtbResource (dict) or a list of them (llist[dict])
        :return: the deserialized HtbResource or list of them
        """
        resource = None
        if isinstance(data, dict):  # load from dict
            resource = DataSources.get(data.pop('__type__'))
            if isinstance(resource, HtvResource):
                resource.update(**data)
        elif isinstance(data, Iterable) and not isinstance(data, str):  # Load several HtbResources
            return [DataSources.load(item) for item in iter(data)]
        elif Path(data).exists():  # Load data from YAML file
            if Path(data).is_dir():  # Get info.yml in that dir
                data = Path(data) / 'info.yml'
            if data.name.endswith('info.yml'):
                try:
                    with open(data, 'r') as file:
                        resource = DataSources.load(yaml.safe_load(file))
                except FileNotFoundError:
                    print(f"[-] Not a HtvResource. Missing info.yml ({data})")
            else:  # Not a json. Try other saves files associations
                for ext, class_name in CONF['EXTENSIONS'].items():
                    if data.name.endswith(ext):
                        resource = DataSources.get(class_name)
                        resource.update(path=data)
                # return None
        elif isinstance(data, str):  # Load data from JSON string
            resource = DataSources.load(json.loads(data))
        return resource

