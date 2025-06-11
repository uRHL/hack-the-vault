from pathlib import Path
import sys

import yaml

ROOT_PKG = Path(__file__).parents[1] # Points to install-dir/src/
sys.path.insert(0, str(ROOT_PKG))

from htv.constants import ROOT_DIR, CONF_PATH, DEPENDENCIES, RUNTIME_CONF, DEFAULT_CONF
from collections.abc import Iterable
from datetime import datetime
from typing import TextIO, Any
from tqdm import tqdm

import webbrowser
import subprocess
import pyperclip
import time
import json
import os
import re

__all__ = [
    'CONF',
    'FsTools',
    'Conf',
    'Templater'
]

#####   C L A S S E S   #####

class Cache:
    """
    Implements a cache using a temp file.
    Cache contains a list of paths, which is overwritten everytime the method :class:`resources.HtbVault.list_resources` is called.
    """
    __route__ = Path('/tmp/.htbtlk.cc')

    @staticmethod
    def get(index: int = None) -> Path | list[Path] | None:
        """Get cache entries

        :param index: If None all the contents of the cache are returned
        :return: `Path` or a list of them. None if cache was empty or index provided out of bounds
        """
        try:  # load last list results (.tmp)
            with open(Cache.__route__, 'r') as file:
                _cc = [Path(i) for i in json.load(file)]
                return _cc if index is None else _cc.pop(index)
        except FileNotFoundError:
            print(f"[!] No cached results. Use option `list` to reload cache")
            return None

    @staticmethod
    def set(items: list) -> None:
        """Update cache with provided items"""
        with open(Cache.__route__, 'w') as file:
            json.dump([str(i) for i in items], file)

    @staticmethod
    def clear() -> None:
        """Clears cache"""
        if Cache.__route__.exists():
            Cache.__route__.unlink()


class Conf(dict):
    """
    Configuration class. Allows to have a callable runtime instance that read/write the changes to a file.
    """
    def __init__(self, runtime: dict, default: dict):
        """Initialize a Configuration instance

        :param runtime: runtime parameters
        :param default: default parameters. If not found in local file, they will be added again
        """
        super().__init__()
        self._default = default
        self._runtime = runtime
        self.load(**self._runtime)

    def _save(self) -> None:
        """Save current configuration

        Save current configuration parameters to disk.
        Runtime values (keys starting by `_`) are not dump into local file.
        If a parameter contained environment variables, they are shortened again

        :return: None
        """
        with open(CONF_PATH, 'w') as file:  # Save changes to disk
            _data = {}
            for k, v in self.items():
                if k.startswith('_'):  # Skip keys starting with '_', they are only used in execution time
                    continue
                if isinstance(v, int|float):
                    _data[k] = v
                elif hasattr(self, f'_{k.lower()}'):  # If vars were expanded, replace them
                    _data[k] = self.__getattribute__(f'_{k.lower()}')
                elif isinstance(v, dict|list):
                    _data[k] = v
                else:
                    _data[k] = str(v)  # cast any non-numeric value to str to avoid serialization problems
            yaml.dump(_data, file)

    def load(self, **kwargs) -> None:
        """Load configuration

        (Re)load configuration from local file. Then the provided kwargs are added.
        If local file does not exist it is created.
        The configured runtime parameters are added.
        Additionally, if any default parameter is missing it is added.

        :param kwargs: parameters to be added to the configuration
        :return: None
        """
        try:
            with open(CONF_PATH, 'r') as file:
                _data = yaml.safe_load(file)
            if len(_data) != len(self._default):  # Missing some default keys
                raise FileNotFoundError
        except FileNotFoundError:
            print(f"[!] Conf file not found or missing default configuration params")
            self.reset()  # reset to default config
            self.load()  # Load configuration
        else:
            self.update_values(**_data)  # Load saved configuration
        finally:
            self.update_values(**kwargs)  # Add custom parameters

    def update_values(self, **kwargs) -> None:
        """Update configuration parameters

        If a parameter contains environment variables, they are expanded again

        :param kwargs: Values to be updated in the configuration
        :return: None
        """
        for k, v in kwargs.items():
            if isinstance(v, str|Path) and str(v).find('$') != -1:  # String contains env variables
                self.__setattr__(f'_{k.lower()}', str(v))  # Save original value
                self[k.upper()] = Path(os.path.expandvars(v))  # Expand variables
            else:
                self[k.upper()] = v
        self._save()

    def remove_values(self, *args) -> None:
        """Remove configuration values

        Remove configuration values then save changes to disk

        :param args: Name(s) of the params to be removed from configuration
        :return: None
        """
        for v in args:
            if v.upper() in self.keys():
                self.pop(v.upper())
        self._save()

    def reset(self) -> None:
        """Resets the configuration to defaults parameters

        :return: None
        """
        print(f"[*] Resetting default config...")
        self.clear()
        self.update_values(**self._default)  # Default conf values
        self.update_values(**self._runtime)  # Add runtime parameters
        self._save()


class FsTools:
    """
    Static class to interact with files
    """
    @staticmethod
    def dump_file(path, content: str = None, exists_ok: bool = False, **kwargs) -> None:
        """Dump content into file

        Dump the provided content into a file.
        If it does not exist, or any of the intermediate directories, they will be created
        To render a template set 'content' to 't:<template_name>'. Instead of  dumping content as plain text, it will dump the rendered template.

        :param path: Path of the output file.
        :param content: Content to be dumped into the file. Use 't:<template_name>' to use a template.
        :param exists_ok: If False and file already exists, raise FileExistError
        :param kwargs: Additional arguments required to the render the template
        :raise FileExistsError: If file already exists and param `exists_ok` is False
        :return: None
        """
        if not path.parent.exists():  # Create directory if it does not exist
            os.makedirs(path.parent)
        if os.path.exists(path) and not exists_ok:  # If file exists
            raise FileExistsError(f"File {path} already exists and it's not empty")
        if content is None:
            content = ''
        if content.startswith('t:'):  # Render template
            content = FsTools.render_template(content.split(':').pop(), path, **kwargs)
        with open(path, 'w') as file:  # Dump content to file
            file.write(content)


    @staticmethod
    def dump_files(files: Iterable, root_dir: str | Path = None, exists_ok: bool = False):
        """Dump a list of files.

        See also :func:`FsTools.dump_file`

        :param files: list of tuples (path:str, content:str, kwargs:dict)
        :param root_dir: Root dir for the files. If None, files' path will be equal to the name provided
        :param exists_ok: If False and file already exists, raise FileExistError

        >>> _files = [
        >>>    'any/other/dir',
        >>>    ('.file1', 'lorem ipsum'),
        >>>    ('file2.md', 't:readme.md'),
        >>>    ('file3.md', 't:readme.md', dict(param1="value1", param2="value2"))
        >>> ]
        """
        for f in iter(files):  # (name, content, dict())
            if isinstance(f, Path | str): # Just one arg provided
                name = f
                content = None
                kwargs = dict()
            else:  # Many arguments (tuple)
                name = f[0]
                content = f[1] if len(f) >= 2 else ''
                kwargs = f[2] if len(f) == 3 else dict()

            if root_dir is not None:  # Name is relative to root_dir
                name = Path(root_dir) / name

            if content is None: # Name points to directory
                os.makedirs(name)
            else: # Name points to file
                # try:
                FsTools.dump_file(name, content=content, exists_ok=exists_ok, **kwargs)
                # except TypeError:
                #     print("\n\nDEBUG", name, content, kwargs)
                #     raise TypeError


    @staticmethod
    def set_clipboard(value: str | Path):
        """
        :param value: Text or path to file to be copied in the clipboard
        """
        if Path(value).is_file():
            with open(value, 'r') as file:
                pyperclip.copy(file.read())
        else:
            pyperclip.copy(str(value))

    @staticmethod
    def copy_js_toolkit(path: str | Path, _stdout: TextIO | tqdm = None):
        _prompt = '[*] Use the script in the dev-tools console (F12). Then copy the returned value into the terminal.'
        FsTools.set_clipboard(path)
        if _stdout is None:
            sys.stdout.write('[+] JavaScript tools copied to the clipboard\n')
            sys.stdout.write(f"{_prompt}\n")
        else:
            _stdout.write('[+] JavaScript tools copied to the clipboard')
            _stdout.write(f"{_prompt}")


    @staticmethod
    def render_template(template: str, out: str | Path = None, **kwargs) -> str:
        """Render a template

        Renders a template from the template directory (`CONF['_JINJA_ENV']`)
        If out is provided, saves the rendered template into that file

        :param template: template to be used from /templates
        :param out: output file to write the template. If None, just returns the rendered template
        :param kwargs: Additional arguments for the render
        :return: The rendered template
        """
        kwargs.update({'templater': Templater})
        _render = CONF['_JINJA_ENV'].get_template(template).render(kwargs)
        if out is not None:
            FsTools.dump_file(out, _render, exists_ok=True)
        return _render

    @staticmethod
    def secure_filename(name) -> str:
        """Returns a secure filename:

        Returns a secure filename: lowercased, not containing special characters and
        with all spaces replaced by underscores (`_`)

        :return: Secured filename
        """
        return re.sub('[ ,&-/:]+', '_', str(name)).lower()

    @staticmethod
    def secure_dirname(name) -> str:
        """Returns a secure dir name:

        Returns a secure dir name: lowercased, not containing special characters and
        with all spaces replaced by dashes (`-`)

        :return: Secured dir name
        """

        return re.sub('[ ,&-/:?]+', '-', str(name)).lower()


    @staticmethod
    def search_res_by_name_id(selector: int | str) -> Path | None:
        """Search resources by name or index

        Search among cached entries and/or the entire vault for a resource.
        If found, its absolute path is returned.
        Index is between [1, N], where N is the number of cached resources

        :param selector: Resource name or cache index
        :return: Path to the resource if found, None otherwise
        """

        try:  # Try cache
            if isinstance(selector, int) and selector < 1:  # Index provided but out of bounds
                raise IndexError
            else:
                return Cache.get(int(selector) - 1)
        except IndexError:  # Index provided, but out of bounds
            print(f"[-] Index {selector} does not exist. Run command `list` again.")
            return None
        except ValueError:  # Not an index, try string search
            _tgs = list(CONF['VAULT_DIR'].glob(f"**/{str(selector).lower()}"))
            if len(_tgs) == 1:
                return _tgs[0]
            else:
                print(f"[-] Not a perfect match, {len(_tgs)} results")
                return None


class Git:
    """
    Static class to interact with the repository
    """
    @staticmethod
    def init() -> None:
        """Initialize Vault repository"""
        subprocess.run('git init --initial-branch=main', shell=True, check=True, cwd=CONF['VAULT_DIR'])

    @staticmethod
    def add_ssh(email: str = None) -> None:
        """Create SSh keys to authenticate on GitHub

        :param email: Email associated to your GitHub account
        """
        _key_name = 'gh'
        email_input = None
        while email_input in [None, '']:
            email_input = input('>> email: ')
            if re.match(r'.+@\w+\.\w{2,}', email_input) is None:
                email_input = None
        print("[*] Generating keys...")
        subprocess.run(f'ssh-keygen -f ~/.ssh/{_key_name} -t ed25519 -C "{email}"', shell=True, check=True)
        print("[*] Updating SSH configuration for github.com")
        subprocess.run(f"echo 'Host github.com\n\tUser git\n\tIdentityFile ~/.ssh/{_key_name}' >> ~/.ssh/config", shell=True)
        print(f"[+] Done\n[*] To complete the setup upload your public key (~/.ssh/{_key_name}.pub) to your GitHub account")
        print(f"[*] Public key: {subprocess.run('cat ~/.ssh/gh.pub', shell=True, capture_output=True, text=True).stdout}")

    @staticmethod
    def config_git_user() -> None:
        """
        Prompts user to input name and email to be used for commits.
        """
        print('[*] Git Name and email must be configured to push into the repository')
        print('[*] Who is in charge of this vault?')
        name_input = None
        email_input = None
        while name_input in [None, '']:
            name_input = input('>> name: ')
        while email_input in [None, '']:
            email_input = input('>> email: ')
            if re.match(r'.+@\w+\.\w{2,}', email_input) is None:
                email_input = None
        print(f"[+] Git user configured {name_input} ({email_input})")
        subprocess.run(f'git config user.name "{name_input}"', shell=True, check=True, cwd=CONF['VAULT_DIR'])
        subprocess.run(f'git config user.email "{email_input}"', shell=True, check=True, cwd=CONF['VAULT_DIR'])

    @staticmethod
    def commit(msg: str) -> None:
        """Commit all changes

        :param msg: Message associated to the commit
        """
        subprocess.run('git add .', shell=True, check=True, cwd=CONF['VAULT_DIR'])
        subprocess.run(f'git commit -am "{msg}"', shell=True, check=True, cwd=CONF['VAULT_DIR'])

    @staticmethod
    def push() -> None:
        """Push changes to remote"""
        _proc = subprocess.run('git branch -vv', shell=True, capture_output=True, text=True, cwd=CONF['VAULT_DIR'])
        if _proc.stdout.find('[origin/main]'):  # Upstream configured
            subprocess.run('git push', shell=True, cwd=CONF['VAULT_DIR'])
        else:  # Set upstream for main branch, then push
            subprocess.run('git push -u origin main', shell=True, cwd=CONF['VAULT_DIR'])


class Templater:

    @staticmethod
    def clean_description(text) -> str:
        while re.search(r":\n{3}(.+\n{2})*", text) is not None:
            start, end = re.search(r":\n{3}(.+\n{2})*", text).span()
            list_text = text[start:end].strip()
            list_text = re.sub(r":\n{3}", ':\n- ', list_text)
            list_text = re.sub(r"\n\n", "\n- ", list_text)
            text = text[:start] + f"{list_text}\n" + text[end:]
        return text

    @staticmethod
    def front_matter(resource):
        """Generates front-matter
        :param resource: HtvResource whose front-matter will be generated
        """
        # layout: page  # 'page' for JeKyll pages, 'post' for post pages, ...
        # title: About
        # date: 2022-02-02  # Overwrite file name date
        # categories: [cat1, cat2]
        # permalink: /:categories /: year /:mont /: day /:title.whatever
        # filename: YYYY-MM-DD-TITLE.md
        return yaml.dump(dict(
            title=resource,
            date=Templater.now(),
            categories=[resource.categories[0], resource.categories[-1]],  # [parent_cat, resource_type]
            tags=[*resource.metadata.tags, *resource.categories],  # TAG names should always be lowercase
            # description=resource.metadata.description,
            #permalink='/:categories /: year /:mont /: day /:title.whatever'
        ))

    @staticmethod
    def backlink(resource: str | Path | Any) -> str | None:
        """

        :param resource: HtvResource or path pointing to a category
        :return : Link chain from Home to resource, in Markdown format
        """

        if isinstance(resource, str | Path): # Generate from path: htb/academy/module -> module, academy, htb
            _link_parts = [f"[Home]({'../' * len(Path(resource).parents)}README.md)"]
            for ind, _ in enumerate(reversed(resource.__str__().split('/'))):
                _link_parts.insert(1, f"[{_}]({'../' * ind if ind > 0 else './'}README.md)")
            return ' > '.join(_link_parts)
        else:
            try: # Generate from HtvResource: htb/academy/module -> htb, academy, module
                _link_parts = [f"[Home]({'../' * (len(resource.categories) + 1)}README.md)", resource.metadata.title]
                for ind, _ in enumerate(reversed(resource.categories), 1):  # Add parent categories links
                    _link_parts.insert(1, f"[{_}]({'../' * ind}README.md)")
                return ' > '.join(_link_parts)
            except AttributeError:
                print(f"[-] Cannot generate backlink of resource '{resource}'")
                return None

    @staticmethod
    def pagination(resource, section) -> str:
        """Generates pagination link

        :param resource: HtvResource instance owning the section
        :param section: HtvModule.Section whose pagination links will be generated
        """
        _nav_menu_md = ['---\n']
        ind = resource.sections.index(section)
        if ind < len(resource.sections) - 1:
            _nav_menu_md.append(
                f"[Next: {resource.sections[ind + 1].title}]"
                f"(./{resource.sections[ind + 1].__file_name__})"
                f"< br >")
        elif ind > 0:
            _nav_menu_md.append(
                f"[Previous: {resource.sections[ind - 1].title}]"
                f"(./{resource.sections[ind - 1].__file_name__})"
                f"< br >")
        return '\n'.join(_nav_menu_md)

    @staticmethod
    def now() -> str:
        """
        :return : Timezone timestamp
        """
        return datetime.now().astimezone().strftime('%Y-%m-%d %H:%M:%S %z')

    @staticmethod
    def class_str(obj) -> str:
        return re.sub(r"(<class '\w+\.|'>)", '', str(obj.__class__))

    @staticmethod
    def camel_case(text: str, sep: str = ' ', lower_first: bool = False):
        _cased = ''
        for ind, w in enumerate(text.split(sep)):
            _cased += w if (ind == 0 and lower_first) else w[0].upper() + w[1:]
        return  _cased


#####   F U N C T I O N S   #####

def open_browser_tab(url, quiet: bool = True, delay: int = 0) -> None:
    """Open url in a new tab

    :param url: URL to be opened
    :param quiet: If True runs the command in the background. Else runs in foreground
    :param delay: Seconds to wait before and after opening the page
    :return: None
    """
    time.sleep(delay)
    if quiet:
        subprocess.run(
            'python3 -c "import webbrowser;webbrowser.open_new_tab(\'' + url + '\')" &',
            shell=True,
            capture_output=True
        )
    else:
        webbrowser.open_new_tab(url)
    time.sleep(delay)

def check_updates() -> int:
    """Check for dependencies updates

    Check for updates of the required dependencies which are listed in constants.DEPENDENCIES

    :return: 0 if dependencies are updated successfully. 1 if update failed. 2 if operation canceled
    """
    # TODO: run pip install -U -r requirements.txt
    print(f"[*] Checking for updates...")
    try:
        subprocess.run('sudo apt update', capture_output=True, shell=True, check=True)
        subprocess.run(f"sudo apt upgrade {' '.join(DEPENDENCIES)}", shell=True, check=True)
    except KeyboardInterrupt:
        print("[!] Update cancelled")
        return 2
    except subprocess.CalledProcessError:
        print("[!] Error updating dependencies")
        return 1
    else:
        print(f"[+] Dependencies updated successfully")
        return 0

#####   D Y N A M I C   V A L U E S   #####

"""Dynamic configuration"""
CONF = Conf(runtime=RUNTIME_CONF,default=DEFAULT_CONF)