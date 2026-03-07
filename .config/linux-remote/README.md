# Linux Remote

Go-bag for remote Linux boxes. Copy and run these bootstrap scripts when
setting up a new remote system.

---

## Usage

```sh
scp ~/.config/linux-remote/<script>.sh jjduqu@remote:/tmp/
ssh jjduqu@remote "bash /tmp/<script>.sh"
```

---

## Scripts

### bootstrap_colorls.sh

Installs `colorls` with icons and color output. Aliases `ls` to
`colorls --group-directories-first` in your shell config.

- Detects distro (Debian/Ubuntu via `apt`, RHEL/Fedora via `dnf`)
- Downloads and installs FiraCode Nerd Font
- Works on bash and zsh

### bootstrap_ble.sh

Installs `ble.sh` — bash-native as-you-type syntax highlighting.
No shell switch required, stays on bash.

- Downloads release tarball from GitHub
- Installs to `~/.local/share/ble.sh/`
- Adds source line to `~/.bashrc`

---

## Windows

Mount or copy the script to the machine, then from WSL:

```sh
chmod +x /path/to/script.sh
bash /path/to/script.sh
```
