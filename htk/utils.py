from pathlib import Path
from tqdm import tqdm

import constants as _c
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
]

#####   C L A S S E S   #####

class Cache:
    @staticmethod
    def get(index: int = None) -> Path | list[Path] | None:
        try:  # load last list results (.tmp)
            with open(CONF['_CACHE_PATH'], 'r') as file:
                _cc = [Path(i) for i in json.load(file)]
                return _cc if index is None else _cc[index]
        except FileNotFoundError:
            print(f"[!] No cached results. Use option `list` to reload cache")
            return None

    @staticmethod
    def set(items: list) -> None:
        # TODO: save items in a tmp file
        with open(CONF['_CACHE_PATH'], 'w') as file:
            json.dump([str(i) for i in items], file)

class Conf(dict):
    def __init__(self, runtime: dict, default: dict):
        super().__init__()
        self._default = default
        self.load(**runtime)

    def _save(self) -> None:  # Save changes to disk
        with open(_c.ROOT_DIR / 'conf.json', 'w') as file:
            _data = {}
            for k, v in self.items():
                if k.startswith('_'):  # Skip keys starting with '_', they are only used in execution time
                    continue
                if isinstance(v, int|float):
                    _data[k] = v
                elif hasattr(self, f'_{k.lower()}'):  # If vars were expanded, replace them
                    _data[k] = self.__getattribute__(f'_{k.lower()}')
                else:
                    _data[k] = str(v)  # cast any non-numeric value to str to avoid serialization problems
            json.dump(_data, file, indent=2)

    def load(self, **kwargs) -> None:
        try:
            with open(_c.ROOT_DIR / 'conf.json', 'r') as file:
                _data = json.load(file)
            if len(_data) != len(self._default):  # Missing some default keys
                raise FileNotFoundError
        except FileNotFoundError:
            print(f"[!] Conf file not found or missing default configuration params")
            self.reset()  # reset to default config
            self.load()  # Load configuration
        else:
            self.update_values(**_data)  # Load saved configuration
        finally:
            self.update_values(**kwargs)  # Add runtime values

    def update_values(self, **kwargs) -> None:
        for k, v in kwargs.items():
            if isinstance(v, str) and v.find('$') != -1:  # String contains env variables
                self.__setattr__(f'_{k.lower()}', v)  # Save original value
                self[k.upper()] = Path(os.path.expandvars(v))  # Expand variables
            else:
                self[k.upper()] = v
        self._save()

    def remove_values(self, *args) -> None:
        for v in args:
            if v.upper() in self.keys():
                self.pop(v.upper())
        self._save()

    def reset(self):
        print(f"[*] Resetting default config...")
        self.clear()
        self.update(self._default)  # Default conf values
        self._save()

class FileClipboard:
    @staticmethod
    def set():
        CONF['_CB_PATH'].unlink(missing_ok=True) # Reset clipboard file
        subprocess.run(['nano', CONF['_CB_PATH']])

    @staticmethod
    def get():
        try:
            with open(CONF['_CB_PATH'], 'r') as file:
                content = file.read()
        except FileNotFoundError:
            return None
        else:
            return content

class FsTools:
    @staticmethod
    def dump_file(path, content, exist_ok: bool = False) -> None:
        if not path.parent.exists():  # Create directory if it does not exist
            os.makedirs(path.parent)
        if os.path.exists(path) and not exist_ok:  # If file exists
            raise FileExistsError(f"File {path} already exists and it's not empty")
        with open(path, 'w') as file:  # Create new files or overwrite an existing one
            file.write(content)

    @staticmethod
    def js_to_clipboard(stdout: tqdm = None) -> None:
        _prompt = '[*] Use the script in the dev-tools console (F12). Then copy the returned value into the terminal. [Press ENTER to continue]'
        if stdout:
            stdout.write('  [+] JavaScript tools copied to the clipboard')
            stdout.write(f"  {_prompt}")
        else:
            print('[+] JavaScript tools copied to the clipboard')
            input(_prompt)
        pyperclip.copy(FsTools.render_template('toolkit.js'))


    @staticmethod
    def render_template(template: str, out: str | Path = None, **kwargs) -> str:
        """

        :param template: template to be used from /templates
        :param out: output file to write the template. If None, just returns the rendered template
        :param kwargs: Additional arguments for the render
        :return: The rendered template
        """
        def taggify(data):
            if isinstance(data, str | int | float):
                return f"`{data}`"
            elif isinstance(data, list):
                return [f"`{i}`" for i in data]
            elif data is None:
                return ''
            else:
                return str(data)

        kwargs.update(taggify=taggify) # aux function to render markdown
        _render = CONF['_JINJA_ENV'].get_template(template).render(kwargs)
        if out is not None:
            FsTools.dump_file(out, _render)
        return _render

    @staticmethod
    def secure_filename(name) -> str:
        return re.sub('[ ,&-/:]+', '_', str(name)).lower()

    @staticmethod
    def secure_dirname(name) -> str:
        return re.sub('[ ,&-/:]+', '-', str(name)).lower()

    @staticmethod
    def search_res_by_name_id(selector: int | str) -> Path | None:
        try:  # Try cache
            return Cache.get(int(selector) - 1)
        except IndexError:  # Index provided, but out of bounds
            print(f"[-] Index {selector} does not exist. Run command `list` again.")
            return None
        except TypeError:  # Not an index, try string search
            _tgs = list(CONF['VAULT_DIR'].glob(f"**/{str(selector).lower()}"))
            if len(_tgs) == 1:
                return _tgs[0]
            else:
                print(f"[-] Not a perfect match, {len(_tgs)} results")
                return None

#####   F U N C T I O N S   #####

def open_browser_tab(url, quiet: bool = True, delay: int = 0):
    """

    :param url: URL to be opened
    :param quiet: If True runs the command in the bg. Else runs in fg
    :param delay: Seconds to wait before and after opening the page
    :return: None
    """
    time.sleep(delay)
    if quiet:
        os.system('python3 -c "import webbrowser;webbrowser.open_new_tab(\'' + url + '\')" > /dev/null &')
    else:
        webbrowser.open_new_tab(url)
    time.sleep(delay)

def check_updates():
    # TODO: run pip install -U -r requirements.txt
    print(f"[*] Checking for updates...")
    try:
        subprocess.run('sudo apt update', capture_output=True, shell=True, check=True)
        subprocess.run(f"sudo apt upgrade {' '.join(_c.DEPENDENCIES)}", shell=True, check=True)
    except KeyboardInterrupt:
        print("[!] Update cancelled")
    except subprocess.CalledProcessError:
        print("[!] Error updating dependencies")
    else:
        print(f"[+] Dependencies updated successfully")

#####   D Y N A M I C   V A L U E S   #####

CONF = Conf(runtime=_c.RUNTIME_CONF,default=_c.DEFAULT_CONF)