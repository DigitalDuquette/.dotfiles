Generate a short git commit message from staged changes.

## Workflow

1. Run `git diff --staged` to see what is about to be committed
2. If there are no staged changes, tell the user and stop
3. Write a concise commit message (one line, under 72 characters)
   that summarizes the **why** not the **what**
4. Copy the message to the clipboard:
   ```
   pbcopy <<< "<commit message>"
   ```
5. Print the commit message and confirm it is on the clipboard
