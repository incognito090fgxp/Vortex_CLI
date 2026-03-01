# 🌀 Vortex CLI

CLI for managing the Vortex ecosystem!

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
py -m venv venv
```

#### Activation (Windows).
```bash
.\venv\Scripts\activate
```

#### Activation (Linux/macOS).
```bash
source venv/bin/activate
```

### 3. Setup and pipx (One-time only):

#### Install.
```bash
pip install -e .
```

#### Be sure to exit venv.
```bash
deactivate
```

#### Ensure paths are configured
```bash
py -m pipx ensurepath
```

**CRITICAL**: Close and reopen your terminal after running `ensurepath`.

### 4. Install Vortex
Navigate to the project folder and run:
```bash
pipx install -e .
```

---

## 🛠 Usage

Simply type the following in any terminal window:
```bash
vortex
```
## ⚙️ If you have moved the CLI folder, don't forget to do this:

### 1. Remove link.
```bash
pipx uninstall vortex-cli
```

### 2. Go to the folder with CLI (`...\Vortex_CLI`)

### 3. We write the command again.
```bash
pipx install -e .
```

### Core Commands:
| Command | Description |
| :--- | :--- |
| `help` | Show beautiful command overview. |
| `check` | Test connection and refresh table cache. |
| `tables` | List all tables in the `public` schema. |
| `query <SQL>`| Run SQL (or just type SQL directly). |
| `auth` | Reconfigure database settings interactively. |
| `clear` | Clear terminal and update banner. |
| `exit` | Close session. |

---

## 🐧 Linux / macOS Notes

1. Install system dependencies: `sudo apt install python3-dev libpq-dev` (Ubuntu) or `brew install postgresql` (macOS).
2. Follow the same `pipx` steps, but use `python3` instead of `py`.

---

## 🔐 Security Note
The `.env` and `.vortex_history` files are local to the project folder and ignored by Git. **Never commit your `.env` file!**
