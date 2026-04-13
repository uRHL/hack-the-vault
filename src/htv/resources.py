## TEMPLATE START
import subprocess
from pathlib import Path
import sys

ROOT_PKG = Path(__file__).parents[1] # Points to install-dir/src/
sys.path.insert(0, str(ROOT_PKG))
## TEMPLATE END

from htv.utils import CONF, FsTools, Templater, open_browser_tab, Git, Cache, flatten
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
    'HtvVault', 'CustomResource', 'FileResource', 'HtvResource', 'HtvPath', 'HtvModule', 'HtvExercise', 'DataSources',
    'is_category', 'is_resource'
]

def is_category(path: str | Path) -> bool:
    # Ignore hidden directories
    if not Path(path).is_absolute():
        path = CONF['VAULT_DIR'] / path
    return not path.name.startswith('.') and (path / 'README.md').exists() and not (path / 'info.yml').exists()

def is_resource(path: str | Path) -> bool:
    if not Path(path).is_absolute():
        path = CONF['VAULT_DIR'] / path
    return (
            (  # Is a CustomResource
                    (path / 'README.md').exists() and
                    (path / 'info.yml').exists()
            ) or
            (  # Is a FileResource
                    path.is_file() and
                    path.name != 'README.md' and #  Exclude category README.md files
                    not path.name.startswith('.') and   # Exclude hidden files
                    not (path.parent / 'info.yml').exists()  # File does not belong to a resource
            )
    )


class Metadata:

    def __init__(self):
        """Basic metadata info"""
        self.title = None
        self.tags = list()
        self.url = '#'
        self.description = None
        self.difficulty = None
        self.status = None
        self.logo = '#'
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

    def hasattr(self, name):
        return hasattr(self, name)


class CustomResource:
    """
    :cvar __type__: [str] Resource type ID. Syntax: <mod_name>.<class_name>`
    :cvar __resource_dir__: [str] Location for these resources within the vault (relative path)
    :ivar _metadata: [:class:`Metadata`]: resource information
    """
    # Code reference
    __type__ = None  # :str E.g. htb.AcademyModule
    # File reference
    __resource_dir__ = None  # :str E.g. academy/module


    def __init__(self, category: str | Path | tuple = None, _type: str = None, **kwargs):
        """
        :param category: Path or tuple(path, description) indicating the category of the resource
        :param _type: Type of resource. The type must match an existing class
        :param kwargs: Additional arguments used to update the resource's metadata
        """
        self.__type__ = 'custom' if _type is None else str(_type)
        if category is None:
            self.__resource_dir__ = CONF['DEFAULT_CAT']
        elif isinstance(category, tuple):
            self.__resource_dir__ = str(category[0]).strip('/')
            HtvVault().add_categories(self.__resource_dir__, category[1])
        else:
            self.__resource_dir__ = str(category).strip('/')
        self._metadata = Metadata()
        self._metadata.update(**kwargs)

    @property
    def metadata(self):
        return self._metadata

    @metadata.setter
    def metadata(self, value: dict):
        self.metadata.update(**value)

    @property
    def categories(self) -> list[str]:
        """Resource categorization

        Categories are extracted from the relative path of the resource (`self.__resource_dir__`)

        :returns : A list will the resource categories
        """
        # Strip trailing '/' from the string. This should be a local path
        return str(self.__resource_dir__).strip('/').split('/')

    @property
    def main_categories(self) -> list[str]:
        if len(self.categories) >= 2:
            return [self.categories[0], self.categories[-1]]
        else:
            return [self.categories[0]]

    @property
    def name(self) -> str:
        """Secure file name (no spaces, no special chars, lowercased)"""
        # re.sub('[ ,&-/:]+', '-', str(self._name)).lower()
        if hasattr(self, 'metadata'):
            return FsTools.secure_dirname(self.metadata.title)
        elif hasattr(self, '_name'):
            return FsTools.secure_dirname(getattr(self, '_name'))
        else:
            print("[#] Resource has no name:", self.to_dict(include_private=False))
            return ''

    @property
    def path(self) -> Path:
        """Absolute path of this resource"""
        return CONF['VAULT_DIR'] / self.__resource_dir__ / self.name

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        try:
            return f"{Templater.class_str(self)}({self.name})"
        except TypeError:
            return f"{Templater.class_str(self)}()"

    def __lt__(self, other):
        if not isinstance(other, CustomResource):
            return False
        return self.name < other.name

    def __eq__(self, other):
        if not isinstance(other, CustomResource):
            return False
        return (
            self.path == other.path
        )

    def __hash__(self):
        return hash(self.path)


    def to_dict(self, include_private: bool = True) -> dict:
        """
        :param include_private: If True, private attributes (starting with '_') are also serialized
        :return: dict representation of this HtbResource
        """
        _data = dict[str:str|dict|list](
            __type__=self.__type__,
            # __resource_dir__=self.__resource_dir__  # Ignore this attribute
        )
        for k, v in vars(self).items():
            if k.startswith('__'):
                continue # Always skip static attributes
            elif k.startswith('_') :  # Replace private attributes by their getter
                if include_private:
                    k = k.replace('_', '')
                    v = self.__getattribute__(k)
                else:
                    continue # Skipping private attributes
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
            try:
                setattr(self, key, value)
            except AttributeError: # Property has no setter
                if hasattr(self, f"_{key}"):  # Try to update a private property with the same name
                    setattr(self, f"_{key}", value)

    def list_resources(self, regex: str = None):
        """List resources of this type

        :param regex: Regex to be applied on the resource name to filter the results. Wildcards allowed. If None, no filtering
        :return: A list with the resources found in local vault
        """
        regex = '*' if regex in [None, ''] else regex
        _ret = DataSources.load(
            list(filter(lambda x: x.is_dir(), (CONF['VAULT_DIR'] / self.__resource_dir__).glob(regex)))
        )
        return _ret


    def open(self):
        """Open the resource

        Open the resource in all the possible ways: opening the URL in a web browser,
        opening the Vault with your favorite editor (Obsidian, Code),
        and opening virtual-box to run your PwnBox or Kali instance.

        :return: None
        """
        print(f"[*] Using resource '{self.name}' ...")
        if self.metadata.url is not None:
            open_browser_tab(self.metadata.url)
        # TODO: open text editor, open VBox manager
        # IF text editor already opened, pass
        # If Vbox already opened, pass

    def __dir_struct__(self, *args) -> list:
        return [
            ('README.md', 't:custom.md', dict(resource=self)),
            ('info.yml', yaml.dump(self.to_dict())),
            *args
        ]

    def makedirs(self, *args, exists_ok: bool = False):
        """Dump serialized object to file

        Serializes and dumps this instance into a file (info.json).
        Additional arguments are tuples specifying other default files to be created,

        :return: None
        """
        if not exists_ok and self.path.exists():
            print(f"[-] Resource '{self.name}' already exists")
        else:
            print(f"[*] Adding resource {self.__repr__()}")
            FsTools.dump_files([
                *self.__dir_struct__(),
                *args
            ], root_dir=self.path, exists_ok=True)



class FileResource(CustomResource):

    # Specific file extension associated to this resource
    __file_ext__ = ''  # str: eg. .ovpn

    def __init__(self, title: str, extension: str = None, **kwargs):
        if extension in [None, '']:
            self.__file_ext__ = ''
        elif str(extension).startswith('.'):
            self.__file_ext__ = str(extension)
        else:
            _ = f"_file_ext must start with '.' ({extension})"
            raise ValueError(_)

        self._name = None
        self.name = title
        super().__init__(
            _type=kwargs.get('_type', 'file'),
            category=kwargs.get('category', None),
            title=title
        )


    @property
    def name(self):
        return f"{self._name}{self.__file_ext__}"

    @name.setter
    def name(self, value: str):
        if self.__file_ext__ in [None, '']:
            self._name, self.__file_ext__ = os.path.splitext(value)
        elif os.path.splitext(value)[1] in ['', self.__file_ext__]:
            self._name = FsTools.secure_filename(value.replace(self.__file_ext__, ''))
        else:
            _ = f"Expected '{self.__file_ext__}' extension, found '{os.path.splitext(value)[1]}'"
            raise ValueError(_)

    @property
    def main_categories(self) -> list[str]:
        if len(self.categories) >= 2:
            return [self.categories[0], self.categories[-1]]
        else:
            return [self.categories[0]]

    def __dir_struct__(self, *args) -> list:
        raise NotImplemented("FileResources are only files, no directories")

    def makedirs(self, *args, exists_ok: bool = False):
        try:
            FsTools.dump_file(self.path, b'', exists_ok=exists_ok)
        except FileExistsError:
            print(f"[-] Resource already exists: {self.path.name}")


class HtvResource(CustomResource):
    """
    Dataclass representing a generic HtbResource.
    This class is the parent of all resource types that can be found in HTB
    """

    def __init__(self, **kwargs):
        """Initializes a HtvResource instance"""
        super().__init__(**kwargs)


    def read_stdin(self, _stdout: tqdm | TextIO = sys.stdout):
        if self.metadata.url is not None:
            _stdout.write(f"[*] Opening module URL and waiting for input\n")
            open_browser_tab(self.metadata.url, delay=3)
        else:
            _stdout.write("[-] Resource's URL not defined. Manual browsing required")
        self.copy_js_toolkit(_stdout=_stdout)

        while True:
            # Init module
            _user_input = input('>>> json: ')
            if _user_input == 'skip':
                return None
            res = DataSources.load(_user_input)
            if res is not None:
                _stdout.write(f"[+] Module added\n")
                return res

    def __dir_struct__(self, *args) -> list:
        return [
            ('info.yml', yaml.dump(self.to_dict())),
            *args
        ]

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
        return super().__dir_struct__(
            ('README.md', 't:module.md', dict(resource=self)),
            self.path / 'resources/img',
            *[(_.__file_name__, 't:mod_section.md', dict(resource=self, section=_)) for _ in self.sections],
            * args
            # Add custom files here
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
        # Extract linked resources (images, files, etc.)
        # add linked resources to VAULT_DIR/docs/assets
        pass


class HtvVault:
    """
    Dataclass representing the HtbVault.
    It allows to manage the vault, adding/removing/opening resources,
    listing them or initializing/deleting the entire vault

    :ivar _path: [`Path`] Path to the vault. May contain environment variables
    :cvar __resources__ [list[class]: List with all the existing resource types of this Vault
    :param path [str|Path]: Path to the vault. If None, the default directory from conf will be used

    """
    __resources__ = None # list

    @staticmethod
    def clean() -> int:
        """Clean-up vault

        Deletes hidden directories created by text editors, in addition to cached and temp files.
        These files/dirs usually start by '.' or '_'. `.gitignore` file and `.git` dir are always excluded.

        :return: 0 on success. 1 if an error occurred
        """
        __excluded__ = ['.git', '.gitignore', '.gitmodules', '.private', '.blog']
        if not CONF['VAULT_DIR'].exists():
            print(f"[!] Vault not initialized. Run `htv init` to start")
            return 1
        print(f"[*] Cleaning the vault...")
        for p in [*CONF['VAULT_DIR'].glob('**/[._]*')]:
            if p.name not in __excluded__:
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
        if not CONF['VAULT_DIR'].exists():
            print(f"[!] Vault not initialized. Run `htv init` to start")
            return 1
        if len(args) == 1:
            try:
                _ = FsTools.get_resource_by_name_id(args[0])
                print(f"[*] Removing '{_.relative_to(CONF['VAULT_DIR'])}'")
                shutil.rmtree(_)
                return 1
            except (TypeError, FileNotFoundError):
                print(f"[-] Unknown resource '{args[0]}'")
                return 0
            except AttributeError:  # FsTools.get_resource_by_name_id returned None (no search results)
                return 0
        else:
            _ = sum([HtvVault.remove_resources(res) for res in args])
            print(f"[+] Resource(s) removed successfully")
            return _


    def __init__(self, *args, path: str | Path = None, git_name: str = None, git_email: str = None):
        if path is None:  # Main vault initialized
            self._path = str(CONF['VAULT_DIR'])
        elif os.path.isabs(os.path.expandvars(path)):
            CONF.update_values(VAULT_DIR=path)
            self._path = str(path)
        else:  # Path relative to vault
            self._path = CONF['VAULT_DIR'] / FsTools.secure_dirname(path)
        self._git = (git_name, git_email)
        self.__resources__ = list(args)

    @property
    def path(self):
        return Path(os.path.expandvars(self._path))

    @property
    def categories(self):
        return ['vault']

    @property
    def main_categories(self) -> list[str]:
        if len(self.categories) >= 2:
            return [self.categories[0], self.categories[-1]]
        else:
            return [self.categories[0]]

    def __str__(self) -> str:
        return self.path.name

    def __repr__(self) -> str:
        return f"{Templater.class_str(self)}({self.path.name})"

    def __dir_struct__(self, *args) -> list:
        return [
            ('.gitignore', 't:gitignore.txt'),
            ('README.md', 't:vault.md'),
            *args
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
        if self.__resources__ is None or len(self.__resources__) == 0: # If is the main vault calling
            print(f"[*] Initializing vault...")
            FsTools.dump_files(self.__dir_struct__(), root_dir=self.path)
            for ds in DataSources.get('all'):  # Get resources associated to this Vault category
                ds.makedirs()
            self.add_categories(
                'personal',
                'Store here all the files you are not sure how to categorize'
            )
            print(f"[+] Vault initialized successfully")
            if not (CONF['VAULT_DIR'] / '.git').exists():  # Initialize repo
                try:
                    Git.init()
                    Git.config_git_user(*self._git)
                    Git.commit('Init vault', quiet=True)
                except (KeyboardInterrupt, EOFError, OSError):  # If initialization fails, remove vault
                    self.removedirs()
                    return 1
        else:
            for _ in self.__resources__:  # 1 dir for each sub-category
                # TODO: find a more elegant way to do this...
                HtvVault().add_categories(_().__resource_dir__) # Instantiate the resource to get __resource_dir__
        return 0

    def removedirs(self, reset: bool = False) -> int:
        """Removes the entire vault

        :return: 0 on success
        """
        if not CONF['VAULT_DIR'].exists():
            print(f"[!] Vault not initialized. Run `htv init` to start")
            return 1
        print(f"[!] Deleting the entire vault")
        shutil.rmtree(self.path)
        if reset:
            CONF.reset()  # Reset configuration so VAULT_DIR points to default location again
        print(f"[+] Vault deleted")
        return 0

    def add_resource(self, data: str | CustomResource, category: str = None, layout: str = None, _stdout: tqdm | TextIO = sys.stdout):
        """Add a resource to the vault

        :param data: Resource data. It may be a name, a json-serialized resource, or a HtvResource object
        :param category: Resource categories
        :param layout: Template name.
        :param _stdout: Output stream
        :return: 0 on success, 1 on error
        """
        # TODO: create an empty resource with name 'name', in the category 'personal', using template 'custom'
        layout = 'custom' if layout is None else layout
        category = CONF['DEFAULT_CAT'] if category is None else category

        if not self.path.exists():
            print(f"[!] Vault not initialized. Run `htv init -h` for more information")
            return 1

        if data is None:
            # If JS toolkit exists so resource can be parsed from web page
            # Use only parent category name to lookup for the JS toolkit
            if (ROOT_PKG / f"datasources/{category.split('/')[0]}/toolkit.js").exists():
                FsTools.copy_js_toolkit(ROOT_PKG / f"datasources/{category.split('/')[0]}/toolkit.js")
                try:
                    self.add_categories(category)
                    self.add_resources(DataSources.load(input('>>> json: ')))  # Add resource, info from stdin
                except KeyboardInterrupt:
                    _stdout.write(f"\n[-] Operation cancelled\n")
                    return 0
            else:
                _stdout.write(f"[!] Resource not created. Missing resource data\n")
                return 1
        elif isinstance(data, CustomResource):
            self.add_categories('/'.join(data.categories))  # Create categories if needed
            data.makedirs()
            return 1
        else:  # Data is a string, either a name, or a json-serialized resource
            self.add_categories(category)  # Create categories if needed
            try:
                return self.add_resource(DataSources.load(data))  # Try to load serialized object
            except ValueError:  # Not a serialized object, then it is the name of the resource
                __layouts__ = {
                    'file': FileResource,
                    'custom': CustomResource,
                    'module': HtvModule,
                    'path': HtvPath,
                    'exercise': HtvExercise
                }
                if layout not in __layouts__:
                    print(f"[-] Unknown layout '{layout}'")
                    return 1
                else:
                    return self.add_resource(
                        __layouts__[layout](categories=category, title=data)
                    )

    def add_resources(self, res: CustomResource | list[CustomResource], _stdout: tqdm | TextIO = sys.stdout) -> int:
        """Add resource(s) to the vault

        :param res: :class:`HtbResource` or a list of them. If None, user will be prompt to input required Resource data
        :param _stdout: Stdout to log information. Default to STDOUT
        :return: number of resources added successfully
        """
        _ret = 0
        if isinstance(res, HtvResource):
            _ret += 1 if self.add_resource(res, _stdout=_stdout) == 0 else 0
        elif isinstance(res, list):
            bar = tqdm(res, unit='resource')
            for item in res:
                _ret += self.add_resources(item, _stdout=bar)
                bar.update(1)
            print(f"[+] {len(res)} resource(s) added successfully")
        else:
            print(f"[-] Not a HtvResource ({type(res)})")
            _ret = 0
        return _ret

    def add_categories(self, path: str, description: str = None):
        """Add new categories to the vault

        Creates a new directory and README for the provided categories.
        Parent categories will be created if they do not exist.

        :param path: Category path. For example: 'cat/sub-cat/sub-sub-cat'
        :param description: Description of the category. It replaces the template placeholder description
        """
        path = Path(FsTools.secure_dirname(path))
        _parent = ''
        for _ in path.parts:
            (self.path / f"{_parent}{_}").mkdir(exist_ok=True)
            try:
                FsTools.dump_file(
                    self.path / f"{_parent}{_}/README.md",
                    't:category.md',
                    resource=Path(f"{_parent}{_}"),
                    VAULT_DIR=self.path,
                    # Add the description only to the final category, not the middle ones
                    description=description if f"{_parent}{_}" == path else None
                )
                print(f"[+] New category added: {_parent}{_}")
            except FileExistsError:  # Category README already exists
                continue
            finally:
                _parent += f"{_}/"


    def list_resources(self, path: str | Path = None, regex: str = None) -> list[Path] | None:
        """List resources from the vault

        :param path: List the contents found in this path
        :param regex: regex applied on the resource name. If None, no filter is applied
        :return: A list with the resources found, or None if no match
        """

        def print_ordered(*items) -> None | list[str]:
            items = list(set(items))  # Remove duplicates
            _div = '-' * 30
            path_pool = list()
            last_idx = 1
            print(f"[*] Listing: {path} {'' if regex in ['', None] else f'(regex: {regex})'}")
            if len(items) <= 0:
                print(
                    _div,
                    f"[-] No resources found matching that criteria",
                    f"[*] Tip: Add a new resource with `htv add`",
                    sep='\n'
                )
                return None
            for v in group_by_cat(*items).values():
                if len(v) <= 0:
                    continue
                print(
                    f"\n{' - '.join(v[0].main_categories).upper()}",  # Header
                    _div,
                    # Pad index depending on how many items will be listed
                    *[f"{Templater.pad_num(ind, len(str(len(items))))}. {item}" for ind, item in enumerate(v, last_idx)],
                    _div,
                    sep='\n'
                )
                last_idx += len(v)
                path_pool.extend([_.path for _ in v])
            Cache.set(path_pool)
            return path_pool

        def group_by_cat(*args) -> dict[str:list[CustomResource]]:
            # TODO: if key has empty list, delete that key
            _grp = dict()
            for _res in filter(lambda x: x is not None, set(args)):
                _key = '/'.join(_res.main_categories)
                if _key in _grp:
                    # Add the resource keeping alphabetical order
                    _grp.update({_key: sorted(_grp[_key] + [_res])})
                else:
                    _grp[_key] = [_res]
            return dict(sorted(_grp.items()))  # Order the keys (categories) alphabetically

        def list_path(_path, _regex):
            if _regex is None:
                _regex = '*'
            elif _regex.find('*') == -1:  # If wildcards not included in the regex
                _regex = f"**/*{_regex}*"  # Search all categories and subcategories
            if _path in ['', None, 'all']:  # List Root vault only
                _regex = f"[!.]*/{_regex}" # Expand regex to exclude hidden directories
                return [list_path(f, _regex) for f in sorted(self.path.glob(_regex)) if is_category(f) or is_resource(f)]
            elif is_category(_path):  # Recursive call to list contained categories/resources
                return [list_path(f, _regex) for f in sorted((self.path / _path).glob(_regex)) if is_category(f) or is_resource(f)]
            elif is_resource(_path) or Path(_path).is_file():
                return DataSources.load(_path)  # Load HtvResource, CustomResource, or FileResource
            else:
                print(f"[-] Unknown category or resource '{_path}'. ")
                return None
        if self.path.exists():
            return print_ordered(*list(flatten(list_path(path, regex))))
        else:
            print(f"[!] Vault not initialized. Run `htv init` to start")
            return list()


    def use_resource(self, *args) -> HtvResource | list[HtvResource] | None:
        """Opens resource(s)

        :param args: Name(s) and/or index(es) of the resources to be opened
        :return: A HtbResource, or a list of them. None if the resource could not be opened
        """
        if not self.path.exists():
            print(f"[!] Vault not initialized. Run `htv init` to start")
            return None

        if len(args) == 1:  # Select single resource, using index or name
            tg = FsTools.get_resource_by_name_id(args[0])
            # TODO: Load the resource file
            if tg is not None:
                tg = DataSources.load(tg)  # Load from path
                tg.open()  # Open the resource
            return tg
        else:
            return [self.use_resource(item) for item in args]  # Recursive call

    @staticmethod
    def post_resources(resources: list):
        for r in resources:
            r.post()

    def import_vault(self, source: str | Path) -> int:
        if not self.path.exists():
            print(f"[!] Vault not initialized. Run `htv init` to start")
            return 1
        print(f"[*] Importing resources from '{source}' ...")
        Git.freeze_virtual_environments(source)
        return subprocess.run(f"cp -r {source}/* {self.path}", shell=True).returncode



class DataSources:
    @staticmethod
    def get(category: str) -> CustomResource | HtvVault | list[HtvVault] | None:
        __types__ = {
            'module': HtvModule(),
            'path': HtvPath(),
            'exercise': HtvExercise(),
            'file': FileResource(''),
            'custom': CustomResource()
        }
        if category == 'all':
            return [
                getattr(importlib.import_module(f"datasources.{_.parent.name}"), 'Vault')
                for _ in (ROOT_PKG / 'datasources').glob('**/ds.py')
            ]
        elif category in __types__:
            return __types__[category]
        else:  # Category points to a class defined in a datasource
            if category.find('.') == -1:
                try:
                    return getattr(importlib.import_module(f"datasources.{category}"), 'Vault')
                except ModuleNotFoundError as e:
                    print(f"[-] {e}")
                    return None
            else:
                _mod, _class = category.split('.', maxsplit=1)
                try:
                    return getattr(importlib.import_module(f"datasources.{_mod}"), _class)()
                except KeyError as e:
                    print(f"[!] Unknown (sub-)category '{e.args[0]}' ({category})")
                    return None
                except (AttributeError, ModuleNotFoundError) as e:
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
        if data is None:
            print(f"[-] Missing parameter 'data'")
            return None
        elif isinstance(data, dict):  # load from dict
            resource = DataSources.get(data.pop('__type__'))
            # If CustomResource use path as resource_dir
            if Templater.class_str(resource) == 'resources.CustomResource':
                resource.__resource_dir__ = data.pop('__path__', CONF['DEFAULT_CAT'])
            resource.update(**data)
        elif isinstance(data, Iterable) and not isinstance(data, str):  # Load several HtbResources
            return [DataSources.load(item) for item in iter(data)]
        elif isinstance(data, str):  # Load serialized data from JSON/YML string
            if FsTools.is_json(data):
                resource = DataSources.load(json.loads(data))
            elif FsTools.is_yaml(data):
                resource = DataSources.load(yaml.safe_load(data))
            else:
                raise ValueError("Invalid data. Expected a serialized object string or path")
        elif Path(data).exists():  # Load data from path
            if Path(data).is_dir():  # Get info.yml in that dir
                data = Path(data) / 'info.yml'
            if FsTools.is_json(data):
                with open(data, 'r') as file:
                    resource = DataSources.load(json.load(file))
            elif FsTools.is_yaml(data):
                with open(data, 'r') as file:
                    _ = yaml.safe_load(file)
                    # Path relative to vault dir
                    _.update({'__path__': str(data.parents[1]).split(f"{CONF['VAULT_DIR'].name}/")[1]})
                    resource = DataSources.load(_)
            else:  # Not a serialized object. Try other files associations
                _match = False
                for ext, class_name in CONF['EXTENSIONS'].items():
                    if data.name.endswith(ext):
                        resource = DataSources.get(class_name)
                        resource.update(path=data)
                        _match = True
                        break
                # If no match, create FileResource
                if not _match: # data is a path that points to any other type of file
                    resource = FileResource(
                        data.name,
                        extension=data.suffix,
                        category='/'.join(data.relative_to(CONF['VAULT_DIR']).parts[:-1])
                    )
        return resource

