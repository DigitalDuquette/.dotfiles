# Homebrew PATH (must be before pyenv so brew-installed Python takes priority)
# export PATH="/opt/homebrew/bin:$PATH"
eval "$(/opt/homebrew/bin/brew shellenv)"
# Prefer Homebrew Ruby over macOS system Ruby
export PATH="/opt/homebrew/opt/ruby/bin:/usr/local/opt/ruby/bin:$PATH"
export PATH="$HOME/.local/bin:$PATH"
# Homebrew's gem bindir is version-pinned (e.g. .../gems/4.0.0/bin) and the
# version segment moves on `brew upgrade ruby`, so it can't be hardcoded.
# Glob instead of shelling out to Ruby: (Nn[-1]) = nullglob, numeric sort,
# newest match only. Numeric sort matters -- lexically 4.9.0 > 4.10.0.
gembin=(/opt/homebrew/lib/ruby/gems/*/bin(Nn[-1]))
(( $#gembin )) && export PATH="$gembin[1]:$PATH"
unset gembin

eval "$(starship init zsh)"


# Aliases
alias ls="colorls --group-directories-first"
alias lls="/bin/ls"
alias dotfiles='/usr/bin/git --git-dir=$HOME/.dotfiles/ --work-tree=$HOME'
alias external-ip="curl checkip.amazonaws.com"
alias ff="fastfetch"
alias batt='pmset -g batt && system_profiler SPPowerDataType | grep -E "Amperage|Voltage|Wattage"'
alias ccgc='claude -p "/gc" --model haiku --allowedTools "Bash(git diff:*)" "Bash(pbcopy:*)"'

# pyenv initialization
export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"
# `pyenv init -` emits everything `pyenv init --path` emits and more, so
# running both ran the whole init twice -- including `pyenv rehash` twice
# at ~75-113ms a call. Dropping --path leaves PATH byte-for-byte identical.
eval "$(pyenv init -)"


# Auto completion 
if type brew &>/dev/null; then
    # $HOMEBREW_PREFIX is already exported by `brew shellenv` above -- no
    # need to fork `brew --prefix` again here or below.
    FPATH=$HOMEBREW_PREFIX/share/zsh-completions:$FPATH

    autoload -Uz compinit
    if [[ -n ~/.zcompdump(#qN.mh-24) ]]; then
        compinit -C   # dump is <24h old: trust it, skip the security audit
    else
        compinit      # audit and rebuild at most once a day
    fi
fi
# Auto suggestions
source "$HOMEBREW_PREFIX/share/zsh-autosuggestions/zsh-autosuggestions.zsh"
# Syntax highlighting
source "$HOMEBREW_PREFIX/opt/zsh-fast-syntax-highlighting/share/zsh-fast-syntax-highlighting/fast-syntax-highlighting.plugin.zsh"
