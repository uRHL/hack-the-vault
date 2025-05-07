# HTB-Vault 

![Static Badge](https://img.shields.io/badge/HTB-black?logo=hackthebox)
![Static Badge](https://img.shields.io/badge/Hack_the_Vault-black)
![Static Badge](https://img.shields.io/badge/pwn_records-black)

![Static Badge](https://img.shields.io/badge/test_coverage-84%25-blue)




**HTB-Vault**, abbreviated (**HTV**), is tool to manage your vault of write-ups and notes efficiently.

#### The _goodbook_

As you progress in your path as a hacker, you will learn more and more techniques, technologies, scenarios, ... 
Knowledge is power, and since human memory sometimes fails, a good _notebook_ can save you tons of time and headaches. HTV helps you to keep this notebook structured and organized so you can get most benefit from it.

#### Save your progress

If you know HTB you should already know Git. Your vault is also a repository, so you can track down changes and save your progress using git. To save the repository in the cloud, just [update the remote repository](#annex-a-updating-remote-repository).


#### Sharing knowledge

With this tool you can share your discoveries and achievements by setting up a blog in few minutes using [GitHub pages](https://pages.github.com/). Check out the [tutorial](#annex-b-setting-up-github-pages).

## Index 

1. [About](#the-_goodbook_)
2. [Installation](#installation)
3. [Usage](#usage)
4. [Configuration](#configuration)
5. [Vault structure](#vault-structure)
6. [Tests](#tests)
7. [Annex A: Updating remote repository](#annex-a-updating-remote-repository)
8. [Annex B: Setting up GitHub pages](#annex-b-setting-up-github-pages)



## Installation

> HTV will automatically install the package dependencies with the command `htv -V`. You can also install the dependencies manually: `python3 python3-venv openvpn git`

```bash
# 1. Select installation directory
TOOLS_DIR=$HOME/Documents/00-tools
REPO_DIR=$TOOLS_DIR"/htb-vault"

# 2. Clone the tool repo
git clone this.url $REPO_DIR
cd $REPO_DIR
# 3. Install dependencies
python3 -m venv venv                 # Create a virtual environment
source venv/bin/activate             # Activate the virtual env
pip install -r requirements          # Install dependencies
deactivate                           # Dependencies installed, venv may be deactivated now
chmod a+x $REPO_DIR/htv/__main__.py  # Grant execution permissions
# 4. Create aliases (shortcuts)
echo 'alias htb-vault="source $REPO_DIR/venv/bin/activate && $REPO_DIR/htv/__main__.py"' >> ~/.bashrc
echo 'alias htv="htb-vault"' >> ~/.bashrc
```


## Usage

```bash
# With aliases created
htv -h # or htb-vault -h

# Without aliases
source $REPO_DIR/venv/bin/activate
python3 htv/__main__.py -h
```


## Configuration

Configuration file (`$REPO_DIR/conf.json`) contain some configuration parameters like the vault directory or the automatic check of dependencies update. You can change this configuration at any time.


## Vault structure
HTB vault has the following structure

```
htb
├── academy
│   ├── modules
│   │   ├── prompt-injection-attacks  # Module name
│   │   │   ├── 01_introduction_to_prompt_engineering.md  # Section name
│   │   │   ├── 02_introduction_to_prompt_injection.md
│   │   │   ├── 03_direct_prompt_injection.md
│   │   │   ├── 04_indirect_prompt_injection.md
│   │   │   ├── 05_introduction_to_jailbreaking.md
│   │   │   ├── index.md
│   │   │   ├── info.json
│   │   │   └── resources  # Images, videos, files or other resources relevant for the module
│   └── paths  # Soft-links to modules
│       ├── job-role-paths
│       │   └── ai-red-teamer
│       │       ├── index.md
│       │       └── info.json
│       └── skill-paths
│           └── cracking-into-hack-the-box
│               ├── index.md
│               └── info.json
├── ctf
├── lab
│   ├── battlegrounds
│   ├── challenges
│   │   └── flag-command
│   │       ├── evidences  # Screenshots, files, strings and any other relevant evidence
│   │       │   └── screenshots
│   │       ├── info.json  # metadata
│   │       ├── sol.pdf  # Official solution
│   │       └── writeup.md  # My writeup, built from template and info.json
│   ├── fortress
│   │   └── jet
│   │       ├── evidences
│   │       │   └── screenshots
│   │       ├── info.json
│   │       ├── sol.pdf
│   │       └── writeup.md
│   ├── machines
│   │   └── eureka
│   │       ├── evidences
│   │       │   └── screenshots
│   │       ├── info.json
│   │       ├── sol.pdf
│   │       └── writeup.md
│   ├── pro-labs
│   │   └── solar
│   │       ├── index.md
│   │       ├── info.json
│   │       └── targets  # Each of the machines of the pro-lab
│   │           ├── solar-inner
│   │           │   ├── evidences
│   │           │   │   └── screenshots
│   │           │   └── writeup.md
│   │           ├── solar-outer
│   │           │   ├── evidences
│   │           │   │   └── screenshots
│   │           │   └── writeup.md
│   │           └── solar-sun
│   │               ├── evidences
│   │               │   └── screenshots
│   │               └── writeup.md
│   ├── sherlocks
│   │   └── dream-job-1
│   │       ├── evidences
│   │       │   └── screenshots
│   │       ├── info.json
│   │       ├── sol.pdf
│   │       └── writeup.md
│   ├── starting-point
│   │   └── responder
│   │       ├── evidences
│   │       │   └── screenshots
│   │       ├── info.json
│   │       ├── sol.pdf
│   │       └── writeup.md
│   └── tracks  # Soft-links to machines and challenges
│       └── ics-and-scada-exploitation
│           ├── index.md
│           └── info.json
└── vpn  # Vpn configuration files
    ├── vpn1.ovpn
    └── vpn2.ovpn

```


## Tests

To run test and generate coverage report run the following command from the installation dir

```bash
pytest --cov --cov-report=html:tests/coverage-report
```

---

## Annex A: Updating remote repository
TODO: tutorial here

## Annex B: Setting-up GitHub pages
TODO: tutorial here

---

## TODOs

- [~] Remove debug traces, and shit prints (REVIEW)
- [ ] Complete pyproject.toml
- [ ] Clean docs
  - [ ] Draw import sequence diagram
  - [ ] Complete Class diagram
  - [ ] Complete class comparison 
- [ ] Review docs (python and README)
  - [ ] Add section 'Importing/Exporting a vault'
  - [ ] Add section 'Setup remote repository'
  - [ ] Add section 'Setup GitHub pages'
  - [ ] Add section 'Generating docs: how to re-generate docs'
- [ ] Generate single-file documentation, clean the rest
- [ ] Create remote repo or use existing one

Right now HTK supports these parsers (JS and Python).

- Implemented
  - Academy: Module, Path
  - Lab: Starting-point, Machine, Challenge, Sherlock, Track, Pro-lab, Fortress
- Not implemented
  - Lab: Battlegrounds
