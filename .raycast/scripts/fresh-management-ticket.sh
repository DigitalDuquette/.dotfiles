#!/bin/bash

# Required parameters:
# @raycast.schemaVersion 1
# @raycast.title Open Fresh Management Ticket
# @raycast.mode fullOutput

# Optional parameters:
# @raycast.icon ✉️

# Documentation:
# @raycast.description Creates a new outlook email with @fresh handler for Management
# @raycast.author DigitalDuquette
# @raycast.authorURL https://raycast.com/DigitalDuquette

#!/bin/bash
osascript <<'EOF'
tell application "Microsoft Outlook"
	set newMessage to make new outgoing message with properties {subject:"", content:"@freshservice \"group\":\"Management\", \"agent\":\"Jared Duquette\" @freshservice"}
	open newMessage
	activate
end tell
EOF