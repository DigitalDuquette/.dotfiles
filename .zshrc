# Homebrew PATH (must be before pyenv so brew-installed Python takes priority)
export PATH="/opt/homebrew/bin:$PATH"
# Prefer Homebrew Ruby over macOS system Ruby
export PATH="/opt/homebrew/opt/ruby/bin:/usr/local/opt/ruby/bin:$PATH"
export PATH="$HOME/.local/bin:$PATH"

eval "$(starship init zsh)"
eval "$(/opt/homebrew/bin/brew shellenv)"

# Aliases
alias ls="colorls --group-directories-first --sort=none"
alias lslegacy="ls"
alias dotfiles='/usr/bin/git --git-dir=$HOME/.dotfiles/ --work-tree=$HOME'
alias externalip="curl checkip.amazonaws.com"
alias ff="fastfetch"

# pyenv initialization
export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init --path)"
eval "$(pyenv init -)"


# Auto completion 
if type brew &>/dev/null; then
    FPATH=$(brew --prefix)/share/zsh-completions:$FPATH

    autoload -Uz compinit
    compinit
fi
# Auto suggestions
source "$(brew --prefix)/share/zsh-autosuggestions/zsh-autosuggestions.zsh"
# Syntax highlighting
source "$(brew --prefix)/opt/zsh-fast-syntax-highlighting/share/zsh-fast-syntax-highlighting/fast-syntax-highlighting.plugin.zsh"
