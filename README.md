# HTB Vault & toolkit

## Requirements

- `python3 python3-venv openvpn git nano`

## Installation

```bash
# 1. Select installation directory
TOOLS_DIR=$HOME/Documents/00-tools
REPO_DIR=$TOOLS_DIR"/htb-toolkit"

# 2. Clone the tool repo
git clone this.url $REPO_DIR
cd $REPO_DIR
# 3. Install dependencies
python3 -m venv venv                 # Create a virtual environment
source venv/bin/activate             # Activate the virtual env
pip install -r requirements          # Install dependencies
deactivate                           # Dependencies installed, venv may be deactivated now
chmod a+x $REPO_DIR/htk/__main__.py  # Grant execution permissions
# 4. Create aliases (shortcuts)
echo 'alias htb-toolkit="source $REPO_DIR/venv/bin/activate && $REPO_DIR/htk/__main__.py"' >> ~/.bashrc
echo 'alias htk="htb-toolkit"' >> ~/.bashrc
```

## Usage

```bash
# With aliases created
htk -h # or htb-toolkit -h

# Without aliases
source $REPO_DIR/venv/bin/activate
python3 htk/__main__.py -h
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
│   │   │   ├── 06_jailbreaks_i.md
│   │   │   ├── 07_jailbreaks_ii.md
│   │   │   ├── 08_tools_of_the_trade.md
│   │   │   ├── 09_traditional_mitigations.md
│   │   │   ├── 10_llm_based_mitigations.md
│   │   │   ├── 11_skills_assessment.md
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

## Scope

Right now HTK supports these parsers (JS and Python):

- Academy
  - [X] Module
  - [X] Path
- Lab
  - [X] Starting-point
  - [X] Machine
  - [X] Challenge
  - [X] Sherlock
  - [X] Track
  - [X] Pro-lab
  - [ ] Advanced-lab
      - [X] Fortress
      - [ ] Battlegrounds


## Auto CLI

```
my-cli: this is a command line
    mode1
        required_param
        --optional-param (y/N)
        param_list+ (default)
        param_list* (default)
    mode2
    mode3
    
modes = dict(
    init=init_mode,
    add=add_mode,
    rm=rm_mode,
    list=list_mode,
    use=use_mode,
    clean=clean_mode,
    vpn=vpn_mode
)
# modes[m](ARGS)

# Invert dict items keys <-> values
# inverted = {v: k for k, v in original.items()}
```

### TODOs

- Document all values, classes, and functions
  - [X] constants.py
  - [ ] __main__.py
  - [ ] resources.py
  - [ ] utils.py
- Remove debug traces, and shit prints
  - [X] constants.py
  - [ ] __main__.py
  - [ ] resources.py
  - [ ] utils.py
- Develop test suite to be run with pytest
  - Save a copy of each json type returned by js-toolkit

