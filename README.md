# Hack the Vault 

![Static Badge](https://img.shields.io/badge/HTV-black)
![Static Badge](https://img.shields.io/badge/pwn_records-black)

![Static Badge](https://img.shields.io/badge/test_coverage-83%25-blue)



**Hack the Vault**, abbreviated (**HTV**), is tool to efficiently manage your hacking write-ups and notes. Initially HTV was designed for [Hack The Box (HTB)](https://www.hackthebox.com/), for that reason the vault has that directory structure. Nevertheless, you can use it for any type of write-up or hacking project.

> [CLI and library documentation](https://urhl.github.io/hack-the-vault/)

#### The _cookbook_

As you progress in your path as a hacker, you will learn more and more techniques, technologies, scenarios, ... 
Knowledge is power, and since human memory sometimes fails, a good _notebook_ can save you tons of time and headaches. HTV helps you to keep this notebook structured and organized so you can get most benefit from it.

#### Save your progress

If you do not know Git it's the perfect moment to start with it. Your vault is also a repository, so you can track down changes and save your progress using git. To save the repository in the cloud, just [update the remote repository](#annex-a-updating-remote-repository).


#### Sharing knowledge

Share your discoveries and achievements by setting up a blog in few minutes, directly from your vault, using [GitHub pages](https://pages.github.com/). Check out the [tutorial](#annex-b-setting-up-github-pages).

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
REPO_DIR=$TOOLS_DIR"/hack-the-vault"
mkdir -p $TOOLS_DIR

# 2. Clone the tool repo
git clone https://github.com/uRHL/hack-the-vault.git $REPO_DIR && cd $REPO_DIR

# 3. Install dependencies
python3 -m venv venv                     # Create a virtual environment
source venv/bin/activate                 # Activate the virtual env
pip install -r requirements.txt          # Install dependencies
deactivate                               # Dependencies installed, venv may be deactivated now
chmod a+x $REPO_DIR/src/htv/__main__.py  # Grant execution permissions

# 4. Create aliases (shortcuts)
echo -e '\n# Hack-the-vault' >> ~/.bashrc
echo 'alias hack-the-vault="source '$REPO_DIR'/venv/bin/activate && '$REPO_DIR'/src/htv/__main__.py"' >> ~/.bashrc
echo 'alias htv="hack-the-vault"' >> ~/.bashrc

# 5. Reload session
source ~/.bashrc
```


## Usage

```bash
# With aliases created
htv -h # or hack-the-vault -h

# Without aliases
source $REPO_DIR/venv/bin/activate
python3 htv/__main__.py -h
```

## Configuration

Configuration file (`$REPO_DIR/conf.yml`) contain some configuration parameters like the vault directory or the automatic check of dependencies update. You can change this configuration at any time.

To disable the automatic check for updates modify the configuration file (`$REPO_DIR/conf.yml`)


## Vault structure
The vault has the following structure

```
vault
├── category-1
│   ├──sub-cat-1
│   │  ├── resource-1
│   │  │   ├── info.yml
│   │  │   ├── README.md
│   │  │   ├── custom_file.txt
│   │  │   └── ...
│   │  ├── resource-2
│   │  └── ...
│   ├──sub-cat-2
│   └── ...
├── category-2
└── ...
```

## Tests

To run test and generate coverage report run the following command from the installation dir

```bash
pytest --cov --cov-report=html:tests/coverage-report
```

---

## Annex A: Updating remote repository

> Remember that the repository name is used by GitHub pages to create the URL to the blog. 
> Give it a useful name, like `hack-vault` 

> Recommended: Use a col quote for the repository description

Create a **private empty repository**, no template, no .gitignore, no README, no license.
Then update the vault's git configuration to add the remote and push the changes.

> You will be requested to authenticate yourself in GitHub. SSH keys are the safe way. 
> Check the [tutorial](#set-up-git-ssh)  

```bash
cd <VAULT_DIR>
git remote add origin <REPO_URL>
git push -u origin main  # Set upstream for git pull/status 
```

## Annex B: Setting-up GitHub pages

Your GitHub repositories should look like this:
```
username
  hacks-vault
  hacks-vault-private
    @hacks-vault (submodule)
```

1. Install htv
2. Login into your [GitHub account](https://github.com/login)
3. Create a new empty private repository. It will be your private vault. Name it `hacks-vault-private`
4. Init local repo with htv: `htv init`
5. Pair remote and local: 

```bash
cd $VAULT_DIR
git remote add origin git@github.com:user/hacks-vault-private.git
git branch -M main
git push -u origin main
```

If you want to use the web blog version (either for you or to share it), first of all, select a Jekyll theme. There are plenty, choose your favorite. I have created my own ([hacks-vault-theme](https://github.com/uRHL/hacks-vault-theme)).

> Works better with themes that support classification by tags and categories, like [Chirpy theme](https://github.com/cotes2020/jekyll-theme-chirpy).

Once you have found your theme, go to its repository. There are 2 ways of "downloading" the theme, depending on your needs on the repository visibility (public or private).

#### Option A: Fork the theme (public site)

This is the recommended option if you are going to deploy your site using GitHub Pages. Free accounts cannot create pages from private repositories thus you will need a public repository to host the content of your site. Additionally, by **forking** the repository you will be able to get theme updates from the original repository.

1. Login into your [GitHub account](https://github.com/login)
2. Fork the theme repository. Give it a cool name. It will appear in your site URL.
3. Clone the forked repository locally: `git clone https://github.com/user/forked.git`

#### Option B: Clone the theme (private site or self-hosted)

If you want to keep your site private, or if you want to host it yourself instead of using GitHub Pages, then use this option. By **cloning** the theme, the fork linkage is broken so you will not receive theme updates. If you change your mind and decide to deploy the site with GitHub Pages, just change the repository visibility to `public` and configure GitHub Actions.

1. Login into your [GitHub account](https://github.com/login)
2. Create an empty private repository
3. Clone the theme you want to use
4. Change the remote URL to point to your private repository
5. Push the changes in the repository configuration
6. Remove the local repository

```bash
git clone https://github.com/user/public-repo.git .blog && cd .blog # step 3
git remote set-url origin https://github.com/your-username/private-repo.git  # Step 4
git push -u origin main  # Step 5
cd .. && rm -fr public-repo  # Step 6

```
Finally, to pair your private and public vaults, add the public one as a submodule of the private vault. The submodule is the public version of hacks-vault.

```bash
# Add the submodule
cd $VAULT_DIR
git submodule add https://github.com/uRHL/hacks-vault.git .blog
git add . && git commit -am "feat: add jekyll site submodule"
git push
```

Now that you have "downloaded" a copy of the theme, you can start with the customization and configuration.
1. Complete the installation steps indicated in the theme repository. 
2. Configura the site name, author, ..., tabs, url, ...
3. Configure GitHub Actions to automatically build and deploy your site whenever changes are pushed to the remote repository.

To push changes in the blog:

```bash
# Update the submodule repository
cd $VAULT_DIR/.blog
git add . && git commit -am "Commit message"
git push
# Now update the submodule reference in the main repository
cd ..
git add . && git commit -am "fix: update submodule ref"
git push
```

### Configuring GitHub Actions


## Creating add-ons

To create a new add-on create a new directory `hack-the-vault/src/datasources/your-add-on` with the following structure:

```
src/datasources/my-add-on/
├── __init__.py  # Python module declaration
├── ds.py        # Add-on source code (classes and functions)
├── toolkit.js   # Web scrapper
├── README.md    # Add-on description and useful information
├── tests        # Tests
└── _layouts     # Custom templates used by the add-on
```

## Set up Git SSH

SSH keys are the recommended way to authenticate you against GitHub from command line applications like Git. Furthermore, you will need them to pull/push from any private repository you own. Configure them in just a couple of minutes and get benefited from the protection of good cryptography.

> It is recommended to use a passphrase to protect the private key

`ssh-keygen` will generate 2 files `gh` (private key) and `gh.pub` (public key). In order to be authenticated on GitHub we need to share our public key with them. Go to User > Settings > SSH and PGP keys > New SSH key. Now paste the contents of `gh.pub` and save the key.

Finally, Git needs to know which key should be used to authenticate you in GitHub. We will configure ssh to do so. We will configure SSH to do the authentication of user git (who does the request behind the scenes) against host `github.com` using the key we just generated. Open (or create) ssh config file (`~/.ssh/config`) to add the following lines:

```
Host github.com
  User git
  IdentityFile ~/.ssh/gh
```

```bash
# Generate SSH key pair
ssh-keygen -f ~/.ssh/gh -t ed25519 -C "your_email@example.com"
# Configure SSH to use that key for GitHub 
echo -e 'Host github.com\n\tUser git\n\tIdentityFile ~/.ssh/gh' >> ~/.ssh/config
```


## Importing and exporting

The vault is a collection of files so it may be exported as a regular folder, copied into an usb memory, zipped, ... Nevertheless, the recommended option is to use git and a hosting service of your choice.

The vault itself is a repository so you just need to [set up the remote](#annex-a-updating-remote-repository) and push the changes to **_export_** your vault.
To **_import_** a vault, just go to your vault directory and clone the repository were you are synchronizing the changes.

```bash
# Importing a vault
VAULT_DIR=$HOME/Documents/01-me/vaults  # recommended location 
mkdir -p $VAULT_DIR; cd $VAULT_DIR
git clone https://github.com/username/your-vault.git  # Clone from the remote
```

## DEV: Updating the documentation

```bash
cd docs/
# Build docs auto-refreshing changes
sphinx-autobuild ./ _build/
# Generate single file doc
sphinx-build -b singlehtml . ../single-doc

# Prepare docs. Params are empty since they are read from constants.py
sphinx-quickstart --sep -l en -p '' -a '' -r '' -v '' --no-batchfile ./docs
```

```python
import sys
import os
sys.path.insert(0, os.path.abspath('../../src'))  # Add our project to the path
import htv

project = htv.constants.DOCS['PROJECT_NAME']
author = htv.constants.DOCS['AUTHOR']
copyright = f'2025, {author}'
release = htv.constants.VERSION
extensions = htv.constants.DOCS['EXTENSIONS']
```

Now, to generate the docs in html format:
```bash
# Interactive docs, refreshing on changes
sphinx-autobuild -b 'html' docs/source docs/build/
# Generate final documentation
sphinx-build -b 'html' docs/source docs/build/
```

---
0x7231
ra-moon

## TODOs

- [~] Remove debug traces, and shit prints (REVIEW)
- [ ] Complete pyproject.toml
- [ ] DOCS (sphinx and README)
  - [ ] Add section 'Setup GitHub pages'
- [ ] Templater.front_matter() => metadata + custom args. Categories are `[categories[0], categories[-1]]`
- [ ] Simulate vault creation and population with my vaults
- [ ] Add submodule (test if by cloning the main repo the secondary is cloned)
- [X] `htv add CAT`. Category is `HTB` returns the corresponding toolkit.js. If no toolkit, create empty resource in the path.
- [X] Fix basic resources so that default-empty resources can be created (e.g. new exercise)
- [ ] Update category/README.md#index whenever resources are added/deleted
- [X] When creating a custom resource are created in __resource_dir__ instead of custom categories
- [~] Fix `list` CLI. Custom resources are not listed since they are not loaded as resources
list htb


```
HtvResource
  name: str
  cat: str
  type: str -> subclass implementation
  tags: list[str] 

mod: htb/academy/modules
path: htb/academy/paths
mch: htb/lab/machines
cat:
  name:
```

Vault resources are organized in categories. Each category has its own README.md
