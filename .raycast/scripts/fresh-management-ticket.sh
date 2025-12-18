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
	set freshLine to "@freshservice \"group\":\"Management\", \"agent\":\"Jared Duquette\" @freshservice"
	set htmlBody to "<br><br><br><br>" & freshLine

	set newMessage to make new outgoing message with properties {subject:"", content:htmlBody}
	make new recipient at newMessage with properties {email address:{address:"information.solutions@padnos.com"}}

	open newMessage
	activate
end tell
EOF