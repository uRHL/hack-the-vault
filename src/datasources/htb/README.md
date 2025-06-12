# HTB add-on

Datasource to work with [HTB](https://www.hackthebox.com/) resources, from both [academy](https://academy.hackthebox.com/dashboard) and [labs](https://app.hackthebox.com/home).

Right now HTK supports these parsers (JS and Python).
- Implemented
  - Academy: Module, Path
  - Lab: Starting-point, Machine, Challenge, Sherlock, Track, Pro-lab, Fortress
- Not implemented
  - Lab: Battlegrounds

## Vault structure

```
vault
└── htb
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

## Select your VPN

If it is the first time you are using HTB, check out their tutorial: Introduction to lab access. They will tell you how to select and download the VPN configuration file from your HTB profile page.

Once you have downloaded your VPN configuration file, save it in your vault in the directory `vpn`.
