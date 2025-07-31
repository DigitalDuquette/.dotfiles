#!/bin/bash

# Required parameters:
# @raycast.schemaVersion 1
# @raycast.title New Outlook Email
# @raycast.mode fullOutput

# Optional parameters:
# @raycast.icon ✉️

# Documentation:
# @raycast.description Creates a new outlook email
# @raycast.author DigitalDuquette
# @raycast.authorURL https://raycast.com/DigitalDuquette

#!/bin/bash
osascript <<EOF
tell application "Microsoft Outlook"
    set newMessage to make new outgoing message
    open newMessage
    activate
end tell
EOF
