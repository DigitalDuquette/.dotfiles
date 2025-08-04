# .dotfiles in Source Control

Stop the pain jumping to a new dev machine: track core `.files` in source control. While there are [many dotfile repos](https://github.com/webpro/awesome-dotfiles?tab=readme-ov-file), this one is mine. Uses a headless git repo in `~/.dotfiles/` - while this isn't the most simplistic of storage options, it has two key advantages:

1. No symlinks are required. Files are exactly where they need to be.
2. GitHub desktop does not work with headless git repos - this forces me to use git commands so I'm not googling on remote machines.

NOTE: Files must be added to be tracked. Hardest muscle memory to learn. Have a new file you wanna add to this repo? Better `dotfiles add file_name.sh`.

Original inspiration from [Anand Iyer's blog](https://www.anand-iyer.com/blog/2018/a-simpler-way-to-manage-your-dotfiles/).

## Dotfiles - Configuration Management

This repository manages and tracks dotfiles across different machines using a bare Git repository. It enables you to version control configuration files without cluttering your $HOME directory.

## Setup on a New Computer

1. Run the setup script to install dotfiles:

```sh
curl -fsSL https://raw.githubusercontent.com/DigitalDuquette/.dotfiles/main/dotfiles_setup.sh | zsh
```

2. Open a new terminal, then run the bootstrap sequence:

```sh
chmod +x ~/.bootstrap/bootstrap.sh && ~/.bootstrap/bootstrap.sh
```

The setup script installs Xcode Command Line Tools and clones your dotfiles. The bootstrap script handles application installation and system configuration.

## Adding New Files

1. Add the File to Git:

    ```sh
    dotfiles add ~/.zshrc
    ```

    (Replace .zshrc with the file you wish to track.)

2. Commit the Changes:

    ```sh
    dotfiles commit -m "Track zshrc"
    ```

3. Push to GitHub:

    ```sh
    dotfiles push
    ```

## Adding a README or Project Files

To add files to the .dotfiles repository directory (not $HOME):

1. Navigate to .dotfiles:

    ```sh
    cd $HOME/.dotfiles
    ```

2. Add and commit files normally:

    ```sh
    touch README.md
    git add README.md
    git commit -m "Add README.md"
    git push
    ```

### Useful Commands

* Check Status: `dotfiles status`
* List Tracked Files: `dotfiles ls-tree --name-only -r HEAD`
* Untrack a File: `dotfiles rm --cached ~/.vimrc`

## Backup and Restore

To back up conflicting files during a checkout:

```sh
mkdir -p .dotfiles-backup
dotfiles checkout 2>&1 | grep -E "^\s+" | awk '{print $1}' | xargs -I{} mv {} .dotfiles-backup/{}
```

## Bootstrap

Bootstrap scripts for setting up a fresh macOS environment are located in `~/.bootstrap/*`.

To run all bootstrap steps in sequence:

```sh
chmod +x ~/.bootstrap/bootstrap.sh
```
