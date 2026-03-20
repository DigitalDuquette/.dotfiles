# Linux Remote

Go-bag for remote Linux boxes. Copy the directory and run
`bootstrap.sh` to provision a new remote system. All scripts are
idempotent — safe to re-run.

---

## Usage

```sh
scp -r ~/.config/linux-remote jjduqu@remote:/tmp/linux-remote
ssh jjduqu@remote "bash /tmp/linux-remote/bootstrap.sh"
```

Or run a single step:

```sh
ssh jjduqu@remote "bash /tmp/linux-remote/setup/10_gh.sh"
```

---

## Scripts

Scripts run in numerical order via `bootstrap.sh`.

### 00_ghostty.sh

Configures Ghostty terminal support (`TERM=xterm-256color`).

### 10_gh.sh

Installs the GitHub CLI (`gh`).

- Detects distro (RHEL/Fedora via `dnf`, Debian/Ubuntu via `apt`)
- Adds the official GitHub CLI repo before installing

After install, authenticate:

```sh
gh auth login
```

> On a headless server with no browser, choose **token** auth when
> prompted. Generate a token at GitHub → Settings → Developer
> settings → Personal access tokens. Scope needed: `repo`,
> `read:org`.

### 20_ble.sh

Installs `ble.sh` — bash-native as-you-type syntax highlighting.
No shell switch required, stays on bash.

- Downloads release tarball from GitHub
- Installs to `~/.local/share/blesh/`
- Adds source line to `~/.bashrc`

### 30_colorls.sh

Installs `colorls` with icons and color output. Aliases `ls` to
`colorls --group-directories-first` in your shell config.

- Detects distro (Debian/Ubuntu via `apt`, RHEL/Fedora via `dnf`)
- Downloads and installs FiraCode Nerd Font
- Works on bash and zsh

### 40_tmux.sh

Pulls `.tmux.conf` from `digitalduquette/.dotfiles` via `gh` CLI.
Requires `gh` to be installed and authenticated (see `10_gh.sh`).