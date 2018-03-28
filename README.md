# PyChat-project
Project 1 for Net-Centric, Python GUI chat

Run ChatServer and Main with accounts.txt and channels.txt all in same folder. ChatServer initializes registered
accounts and channels with these txt files. open accounts.txt to find info for default admin and sysop users and
modify if desired. open channels.txt to find info on registered channels and modify if desired. Comments at top of each file show proper format.

In the chatServer you must register or login before sending messages.

    Register by typing /pass <password>.
Password is converted to all lowercase on submit. Then continue with /nick <nickname> and
/user <username> <real name>. If user and nick are available your account is registered and stored in
accounts.txt.

    Connect by typing /connect <nickname> <username> <password>.
If an offline account with all three matching fields is found the user is logged in and connected.


The following commands were implemented, and their usage shown. Same as help message in chat.
        /away [away_message]        - Set a new away message to [away_message] or remove away status.
        /die                        - Allows Ops to shutdown server
        /info                       - Returns relevant server information
        /ison <nicknames>           - See if space-separated list of nicks are online.
        /help                       - Show the list of commands
        /join [channel_name]        - To create or switch to a channel.
        /kick <user> [channel]      - Force a user to part from a channel, or your current channel if none.
        /kill <nickname>            - Force a client to quit the server, reserved for Ops
        /list [channels]            - Lists all, or the specified, channels and their topics.
        /nick [nickname]            - Set a new nickname if not already in use.
        /notice [msg] [nick]        - Same as Priv Msg except away auto replies are not sent as response.
        /oper <nick> <pass>         - Ops nick if supplied password is yours and you are currently Op
        /restart                    - Restarts the server. Closes all connections and reinits.
        /rules                      - Request server's rules
        /part [channel]             - Leaves channel provided, or current channel if none
        /ping                       - Used to request Pong from server, to check if connection is still live
        /pong                       - Replies with Ping
        /privmsg <nick> <message>   - Sends a private message to user
        /quit                       - Exits the program.
        /setname <new real name>    - Allows user to change real name after registration
        /time                       - Returns the local time from the server
        /topic <channel> [topic]    - To view/set a topic for a channel
        /userip <nickname>          - Returns ip address of user if online. Only callable by admins and sysops
        /userhost <nick names>      - Returns host info for up to 5 nicknames. Reserved for Ops only
        /users                      - List all users and their current status (Online, Away)
        /version                    - Returns current server version on one line
        /wallops <message>          - Sends message to all Ops online
        /who <channel>              - Returns list of all users in channel
        /whois <user>               - Returns information on specified user
    When possible RFC 1459 was followed for the implementation of the commands, minus the return of proper ERR codes.
    If it was not possible to follow RFC 1459, the commands were implemented to closely resemble the actual usage,
     return message, and params.

The following commands and features were not implemented.
        /invite
        /knock
        /mode
        /silence
    As a result some functionality is missing from the project. Setting and changing passwords for channels is not
    implemented, however can be given and changed manually in the channels.txt and then upon restart. Users are not
    able to be banned either. Due to personal impediments, the config, log, and test files for both the server and
    client were not implemented. As a result only one instance of the chatServer can run at a time successfully.
