# boss-battles
A Micro:bit based coding challenge game

## Development
### Clone the repo
- https: https://github.com/MrGallo/boss-battles.git
- ssh: git@github.com:MrGallo/boss-battles.git
- [GitHub CLI](https://cli.github.com/): gh repo clone MrGallo/boss-battles

### Install poetry package manager
- Install poetry: `$ curl -sSL https://install.python-poetry.org | python3 -`
    - Once done, you should be able to check the version with `$ poetry --version`.
    - If not, follow these steps:
        - Add poetry to pah: `$ echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc`
        - Refresh termitnal: `source ~/.bashrc`
        - `$ poetry --version` should work now. 

## Daily Operating Procedure

This guide provides a simple daily process for contributing to a Python project using Git and Poetry via the terminal. It's designed for people new to Git and Poetry.

### 1. Start Your Day: Sync with Remote

Before starting any work, make sure your local copy of the project is up-to-date.

```bash
# Navigate to your project directory
cd /path/to/your/project

# Ensure you're on the correct branch (usually 'main' or 'develop')
git checkout main

# Fetch the latest changes from the remote repository
git fetch origin

# Merge any changes that have been made to the remote branch into your local copy
git pull origin main
```

### 2. Install dependancies
#### Running on windows
```bash
# Install the dependencies listed in the pyproject.toml file
poetry install --extras "windows"
```
#### Running on linux
```bash
# Install the dependencies listed in the pyproject.toml file
poetry install
```


### 3. Create a new branch to develop on
```bash
# Create and switch to a new branch
git checkout -b your-branch-name
```

### 4. If you already have an active branch...
```bash
# Switch to the main branch
git checkout main

# Fetch and pull any new changes
git fetch origin
git pull origin main

# Rebase your feature branch with the latest changes
git checkout your-branch-name
git rebase main

# If there are conflicts, resolve them, then continue the rebase
# After resolving conflicts:
git add .
git rebase --continue
```

### 5. Actually starting to code
```bash
# activate the poetry shell (virtual environment) to get working
poetry shell

# do some work, then run tests with
pytest

# Run the module
python -m boss_battles
```

### 6. Stage your changes
```bash
# Stage all changes
git add .

# OR stage specific files
git add file1 file2
```

### 7. Commit your changes
```bash
# Commit with a message
git commit -m "Description of what you changed"

# If you get an error you need to add your GitHub username and email
git config --global user.email "you@example.com"
git config --global user.name "Your Name"
```

### 8. Push your changes
```bash
# Push the branch to the remote repository
git push origin your-branch-name
```


## The Game
### Running the radio server
```python
from microbit import *
import radio


radio.on()
radio.config(group=255)

while True:
    message = radio.receive()
    if message:
        uart.write(message + '\n')
    
    if button_b.was_pressed():
        uart.write("done")

```
### Running the Game server
- Connect the microbit radio server to the computer via USB.
- Check which port the Microbit is connected to
    - Device manager
    - Ports
    - Take note of the port. On windows its usually COM3
- Run the Boss Battles package
    - python -m boss_battles --port=COM3

#### USB Connection over WSL
- Download the latest usbipd-win release from the GitHub page.
- Install it by running the installer.
- Open PowerShell (as Admin) and run:
    - `dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart`
- Restart your computer after enabling the feature.
- In PowerShell (Admin), check for attached USB devices: `usbipd list`
- Identify the busid for your micr from the usbipd list output.
- Use this command to bind the device: `usbipd bind --busid <busid>`
- Use this command to attach the device: `usbipd attach --busid <busid> --wsl`
- Open WSL and run: `dmesg | grep tty`
    - This will show something like /dev/ttyUSB0 or /dev/ttyACM0
- Grant Permissions to the Serial Port: `sudo chmod 666 /dev/ttyACM0  # Replace with your actual port if different`


### Registering as a player
```python
from microbit import *

USERNAME = "user1"

radio.config(group=255)
radio.on()

while True:
    if button_b.was_pressed():
        radio.send(USERNAME + "/register")
        break

# The rest of your game code will go down here...
```
