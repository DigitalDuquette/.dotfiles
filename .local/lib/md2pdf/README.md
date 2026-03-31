# md2pdf

Markdown → PDF CLI tool styled after the
[Border](https://github.com/Akifyss/obsidian-border) Obsidian theme.

Uses [md-to-pdf](https://github.com/simonhaenisch/md-to-pdf) via `npx` —
no global npm install required.

## Prerequisites

- Node.js (any recent version — installed via Homebrew is fine)

That's it. `npx` handles downloading md-to-pdf on first run.

## Files

```
~/.local/bin/md2pdf              # wrapper script (in PATH)
~/.local/lib/md2pdf/
├── README.md                    # this file
├── border-print.css             # Border theme adapted for print
└── config.js                    # md-to-pdf configuration
```

## Usage

```bash
md2pdf document.md               # outputs document.pdf in same dir
md2pdf file1.md file2.md         # batch convert
```

First run downloads md-to-pdf (~30s). Subsequent runs use the npx cache.

## What it looks like

The Border theme's signature features, adapted for PDF:

- **Colored heading indicators** — 3px left bars (red h1 → purple h6)
- **Bold** text in red, **italic** in orange, `inline code` in pink
- **Code blocks** with dashed borders and syntax highlighting
- **Blockquotes** with accent-colored left bar and dot-pattern background
- **Tables** full-width with styled headers
- Light theme only — optimized for print

## Customization

Edit `border-print.css` to change colors, fonts, or spacing. The CSS
variables at the top of the file control most of the theme:

```css
:root {
    --color-red: rgb(221, 44, 56);
    --font-text: -apple-system, BlinkMacSystemFont, ...;
    /* etc. */
}
```

Edit `config.js` to change PDF options (margins, paper size).

## Adding to dotfiles

```bash
dotfiles add ~/.local/bin/md2pdf
dotfiles add ~/.local/lib/md2pdf/
dotfiles commit -m "Add md2pdf: markdown to PDF with Border theme"
dotfiles push
```
