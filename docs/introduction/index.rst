Installation
=============

.. code-block:: bash

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
    echo 'alias htb-vault="source $REPO_DIR/venv/bin/activate && $REPO_DIR/htv/__main__.py"' >> ~/.bashrc
    echo 'alias htv="htb-vault"' >> ~/.bashrc

Dependencies
-------------

`HTV` will check automatically for dependencies updates on start-up. To verify the dependencies automatically just run:

.. code-block:: bash

    htv -V

You can change this behaviour in the configuration file (`$REPO_DIR/conf.json`)

Usage
=======

Configuration
--------------

You can modify certain behaviours of the tool with the configuration file (`$REPO_DIR/conf.json`)

Basic
-------

.. code-block:: bash

    # With aliases created
    htv -h # or htb-toolkit -h

    # Without aliases
    source $REPO_DIR/venv/bin/activate
    python3 htv/__main__.py -h


Advanced
----------

.. code-block:: bash

    htv init         # Init a vault (default location $HOME/Documents/01-me/vaults/htb)
    htv add          # Add a new resource to the vault
    htv list         # List vault's resources
    htv rm 1 2 3     # Removes resources indexes 1, 2, 3
    htv open 4       # Open resource index 4
    htv vpn start 5  # Starts VPN index 5
    htv clean        # Clean-up temp files from the vault

