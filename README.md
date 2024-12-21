# .dotfiles in Source Control

Used to source key dot files to source control. Files must be added to be tracked. Idea sourced from [https://www.anand-iyer.com/blog/2018/a-simpler-way-to-manage-your-dotfiles/](https://www.anand-iyer.com/blog/2018/a-simpler-way-to-manage-your-dotfiles/)

## Dotfiles - Configuration Management

This repository manages and tracks dotfiles across different machines using a bare Git repository. It enables you to version control configuration files without cluttering your $HOME directory.

## Setup on a New Computer

Follow these steps to set up your dotfiles on a new machine.

1. Clone the Bare Repository

    ```sh
    git clone --bare https://github.com/DigitalDuquette/.dotfiles.git $HOME/.dotfiles
    ```

2. Create an Alias for Easy Management

    ```sh
    alias dotfiles='/usr/bin/git --git-dir=$HOME/.dotfiles/ --work-tree=$HOME'
    ```

    This alias allows you to interact with the bare repo as if it were a regular Git repository.

3. Prevent Untracked Files from Showing Up

    ```sh
    dotfiles config --local status.showUntrackedFiles no
    ```

4. Checkout the Tracked Files

    ```sh
    dotfiles checkout
    ```

    Note: If you encounter errors due to existing files, back them up or remove them:

    ```sh
    mkdir -p .dotfiles-backup
    dotfiles checkout 2>&1 | grep -E "^\s+" | awk '{print $1}' | xargs -I{} mv {} .dotfiles-backup/{}
    dotfiles checkout
    ```

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

    ```
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
