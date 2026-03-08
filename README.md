# 🌀 Vortex CLI

##### CLI for managing the Vortex ecosystem!



---



## ✨ Features


- **Interactive REPL**: A full shell experience with a `vortex@host>` prompt.
- **Adaptive UI**: The banner and interface automatically scale for small or large terminal windows.
- **Smart SQL Completion**: Multi-level suggestions and real-time table name fetching.
- **Security First**: Zero-echo passwords and safe history (auth details are never saved).
- **Global Access**: Install once and use from any directory.



---



## 🚀 Installation (The Reliable Way)

We recommend using **pipx** to make `vortex` available globally without messing up your system Python.


### 1. Install repo


#### Download the repository by going to the appropriate folder.

```bash
git clone "https://github.com/incognito090fgxp/Vortex_CLI.git"
```


#### Then go to the Vortex_CLI folder.

```bash
cd Vortex_CLI
```



### 2. Creating a virtual environment:


#### Creating an environment.

```bash
python -m venv venv
```


#### Activation (Windows).

```bash
.\venv\Scripts\activate
```


#### Activation (Linux/macOS).

```bash
source venv/bin/activate
```



### 3. Setup:


#### Install.

```bash
pip install -e .
```


#### Be sure to exit venv.

```bash
deactivate
```



---



## ⚡ Quick Launch (Portable)

If you don't want to install the CLI globally, you can use these launchers. They automatically detect and use the `venv` in the project root:


- **Windows:** Run `.\vortex.bat` or just double-click it.
- **Linux / macOS / Termux / Git Bash:** Run `./vortex.run`.



---



## Core Commands:


| Command       | Description                                  |
| :------------ | :------------------------------------------- |
|               |                                              |
| `help`        | Show beautiful command overview.             |
| `check`       | Test connection and refresh table cache.     |
| `tables`      | List all tables in the `public` schema.      |
| `query <SQL>` | Run SQL (or just type SQL directly).         |
| `auth`        | Reconfigure database settings interactively. |
| `update`      | Manually check and apply updates via Git.    |
| `config`      | Manage global settings (e.g., auto-updates). |
| `clear`       | Clear terminal and update banner.            |
| `exit`        | Close session.                               |



---



## 🔄 Updates & Settings

##### Vortex CLI now supports automatic updates and local configuration:


- **Auto-Updates**: By default, the CLI checks for new versions on GitHub every time it starts. If an update is found, it will ask for your confirmation before pulling the changes.


- **Global Settings**: Use the `config` command to manage your preferences. These settings are stored locally in `.vortex_settings.json` and are not tracked by Git.
	- `config show`: View current settings.
	- `config auto_update off`: Disable the startup update check.



---



## 🐧 Linux / macOS Notes


1. Install system dependencies: `sudo apt install python3-dev libpq-dev` (Ubuntu) or `brew install postgresql` (macOS).


2. Follow the same `pipx` steps, but use `python3` instead of `py`.



---



## 🔐 Security Note

The `.env` and `.vortex_history` files are local to the project folder and ignored by Git. **Never commit your `.env` file!**