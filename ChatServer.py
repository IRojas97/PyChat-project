import socket
import sys
import threading
import Channel
import User
import Account
import Util
from datetime import datetime


class Server:
    SERVER_CONFIG = {"MAX_CONNECTIONS": 15}

    HELP_MESSAGE = """\n> The list of commands available are:

/away [away_message]        - Set a new away message or remove away status.
/ison <nicknames>           - See if space-separated list of nicks are online.
/help                       - Show the instructions
/join [channel_name]        - To create or switch to a channel.
/kick <user> [channel]      - Force part a user from a channel, or current channel if none
/list [channels]            - Lists all, or the specified, channels and their topics.
/nick [nickname]            - Set a new nickname if not already in use.
/part [channel]             - Leaves channel provided, or current channel if none
/ping                       - Used to request Pong from server, to check if connection is still live
/pong                       - Replies with Ping
/privmsg <nick> <message>   - Sends a private message to user
/quit                       - Exits the program.
/time                       - Returns the local time from the server 
/topic <channel> [topic]    - To view/set a topic for a channel
/users                      - List all users and their current status (Online, Away)
/who <channel>              - Returns list of all users in channel
/whois <user>               - Returns information on specified user
\n\n""".encode('utf8')

    WELCOME_MESSAGE = "\n> Welcome to our chat app!!!\n".encode('utf8')

    def __init__(self, host=socket.gethostbyname('localhost'), port=50000, allowReuseAddress=True, timeout=3):
        self.address = (host, port)
        self.channels = {} # Channel Name -> Channel
        self.users_channels_map = {} # User Name -> Channel Name
        self.client_thread_list = [] # A list of all threads that are either running or have finished their task.
        self.users = [] # A list of all the users who are connected to the server.
        self.accounts = {}  # username -> accounts
        self.exit_signal = threading.Event()
        self.accounts['admin'] = Account.Account('admin', 'admin', 'password', 'admin', 'Ivan Rojas')
        self.accounts['sysop'] = Account.Account('sysop', 'sysop', 'password', 'sysop', 'Ivan Rojas')

        try:
            self.serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        except socket.error as errorMessage:
            sys.stderr.write("Failed to initialize the server. Error - {0}".format(errorMessage))
            raise

        self.serverSocket.settimeout(timeout)

        if allowReuseAddress:
            self.serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        try:
            self.serverSocket.bind(self.address)
        except socket.error as errorMessage:
            sys.stderr.write('Failed to bind to address {0} on port {1}. Error - {2}'.format(self.address[0], self.address[1], errorMessage))
            raise

    def start_listening(self, defaultGreeting="\n> Welcome to our chat app!!! What is your full name?\n"):
        self.serverSocket.listen(Server.SERVER_CONFIG["MAX_CONNECTIONS"])

        try:
            while not self.exit_signal.is_set():
                try:
                    print("Waiting for a client to establish a connection\n")
                    clientSocket, clientAddress = self.serverSocket.accept()
                    print("Connection established with IP address {0} and port {1}\n".format(clientAddress[0], clientAddress[1]))
                    user = User.User(clientSocket)
                    self.users.append(user)
                    self.welcome_user(user)
                    clientThread = threading.Thread(target=self.client_thread, args=(user,))
                    clientThread.start()
                    self.client_thread_list.append(clientThread)
                except socket.timeout:
                    pass
        except KeyboardInterrupt:
            self.exit_signal.set()

        for client in self.client_thread_list:
            if client.is_alive():
                client.join()

    def welcome_user(self, user):
        user.socket.sendall(Server.WELCOME_MESSAGE)

    def client_thread(self, user, size=4096):
        password = user.password


        while not user.password or not user.nickname or not user.username:
            user.password = "@"
            user.socket.sendall("\n> Please enter /pass <password> to begin registration or /connect <nickname> <username> <password> to login into an existing account .\n".encode('utf8'))
            passMessage = (user.socket.recv(size).decode('utf8')).split()
            if ('/pass' in passMessage) and len(passMessage) == 2:
                self.handle_register(user, passMessage, size)
            if ('/connect' in passMessage) and len(passMessage) >= 3:
                self.handle_connect(user, passMessage)




        welcomeMessage = '\n> Welcome {0}, type /help for a list of helpful commands.\n\n'.format(user.username).encode('utf8')
        user.socket.sendall(welcomeMessage)

        while True:
            chatMessage = user.socket.recv(size).decode('utf8').lower()

            if self.exit_signal.is_set():
                break

            if not chatMessage:
                break

            if '/quit' in chatMessage:
                self.quit(user)
                break
            elif '/list' in chatMessage:
                self.handle_list(user, chatMessage)
            elif '/help' in chatMessage:
                self.help(user)
            elif '/join' in chatMessage:
                self.join(user, chatMessage)
            elif 'nick' in chatMessage:
                self.nick(user, chatMessage)
            elif '/away' in chatMessage:
                self.away(user, chatMessage)
            elif '/time' in chatMessage:
                self.get_time(user, chatMessage)
            elif '/topic' in chatMessage:
                self.handle_topic(user, chatMessage)
            elif '/part' in chatMessage:
                self.part(user, chatMessage)
            elif '/kick' in chatMessage:
                self.kick(user, chatMessage)
            elif '/users' == chatMessage.split()[0]:
                self.list_all_users(user)
            elif '/ping' in chatMessage:
                user.socket.sendall("\n> Pong\n".encode('utf8'))
            elif '/pong' in chatMessage:
                user.socket.sendall("\n> Ping\n".encode('utf8'))
            elif '/ison' in chatMessage:
                self.handle_ison(user, chatMessage)
            elif '/whois' in chatMessage:
                self.handle_whois(user, chatMessage)
            elif '/who' in chatMessage:
                self.handle_who(user, chatMessage)
            elif 'privmsg' in chatMessage:
                self.handle_pm(user, chatMessage)
            else:
                self.send_message(user, chatMessage + '\n')

        if self.exit_signal.is_set():
            user.socket.sendall('/squit'.encode('utf8'))

        user.socket.close()

    def quit(self, user):
        user.socket.sendall('/quit'.encode('utf8'))
        self.remove_user(user)

    def handle_register(self, user, regMessage, size):
        password = regMessage[1]
        user.password = password
        account = Account.Account(password=user.password)
        while not user.username:
            regMessage = ''

            while not regMessage:
                user.socket.sendall(
                    "\n> Please enter /nick <nickname> (Nick must not be in use)\n".encode('utf8'))

                regMessage = user.socket.recv(size).decode('utf8').lower()
                if '/nick ' not in regMessage:
                    regMessage = ''
                elif '+' in regMessage or '$' in regMessage or '*' in regMessage:
                    regMessage = ''
                    user.socket.sendall(
                        "\n> Use of symbols '+' or '$' or '*' not allowed\n".encode('utf8'))

            regMessage += " "
            userMessage = ''
            while not userMessage:
                user.socket.sendall(
                    "\n> Please enter /user <username> <real name> (User must not be in use)\n".encode(
                        'utf8'))

                userMessage = user.socket.recv(size).decode('utf8').lower()

                if '/user ' not in userMessage:
                    userMessage = ''

                elif '+' in userMessage or '$' in userMessage or '*' in userMessage:
                    userMessage = ''
                    user.socket.sendall(
                        "\n> Use of symbols '+' or '$' or '*' not allowed\n".encode('utf8'))
                else:
                    regMessage += userMessage

            regMessage = regMessage.split(' ', 4)


            if len(regMessage) == 5 and regMessage[0] == '/nick' and regMessage[2] == '/user':
                nickname = regMessage[1]
                username = regMessage[3]
                realname = regMessage[4]
                inUse = False


                for users in self.users:
                    if users.nickname == nickname:
                        user.socket.sendall(
                            "\n> Nickname already in use: {0}\n".format(nickname).encode('utf8'))
                        inUse = True
                    if users.username == username:
                        user.socket.sendall(
                            "\n> Username already in use: {0}\n".format(username).encode('utf8'))
                        inUse = True
                if not inUse:
                    user.nickname = nickname
                    user.username = username
                    user.realname = realname
                    account.nickname = nickname
                    account.username = username
                    account.realname = realname
                    self.accounts[account.username] = account




    def handle_connect(self,user, connMessage):
        inUse = False
        username = connMessage[2]
        nickname = connMessage[1]
        if len(connMessage) == 4:
            password = connMessage[3]
        else:
            password = '@'
        if username in self.accounts:
            if self.accounts[username].nickname == nickname and self.accounts[username].password == password:
                for users in self.users:
                    if users.username == username:
                        user.socket.sendall(
                            "\n> Username already Online: {0}".format(username).encode('utf8'))
                        inUse = True
                    if users.nickname == self.accounts[username].nickname:
                        user.socket.sendall(
                            "\n> Nickname already Online: {0}".format(self.accounts[username].nickname).encode('utf8'))
                        inUse = True
                if not inUse:
                    user.username = self.accounts[username].username
                    user.nickname = self.accounts[username].nickname
                    user.password = self.accounts[username].password
                    user.usertype = self.accounts[username].usertype
                    user.realname = self.accounts[username].realname

    def list_all_channels(self, user):
        if len(self.channels) == 0:
            chatMessage = "\n> No rooms available. Create your own by typing /join [channel_name]\n".encode('utf8')
            user.socket.sendall(chatMessage)
        else:
            chatMessage = '\n\n> Current channels available are: \n'
            for channel in self.channels:
                chatMessage += "    \n" + channel + ", topic currently: " + self.channels[channel].topic()
            chatMessage += "\n"
            user.socket.sendall(chatMessage.encode('utf8'))

    def handle_list(self,user, chatMessage):
        split_message = chatMessage.split(' ', 1)
        if len(split_message) >= 2:
            channel_list = split_message[1].split()
            chatMessage = '\n\n> Current topics for queried channels: \n'
            for channel in channel_list:
                if channel in self.channels:
                    chatMessage += "    \n" + channel + ",\t topic currently: " + self.channels[channel].topic()
                else:
                    chatMessage += "    \n" + channel + "\t does not exist!"

            chatMessage += "\n"
            user.socket.sendall(chatMessage.encode('utf8'))

        else:
            self.list_all_channels(user)

    def help(self, user):
        user.socket.sendall(Server.HELP_MESSAGE)

    def join(self, user, chatMessage):
        isInSameRoom = False

        if len(chatMessage.split()) >= 2:
            channelName = chatMessage.split()[1]

            if user.username in self.users_channels_map: # Here we are switching to a new channel.
                if self.users_channels_map[user.username] == channelName:
                    user.socket.sendall("\n> You are already in channel: {0}".format(channelName).encode('utf8'))
                    isInSameRoom = True
                else: # switch to a new channel
                    oldChannelName = self.users_channels_map[user.username]
                    self.channels[oldChannelName].remove_user_from_channel(user) # remove them from the previous channel

            if not isInSameRoom:
                if not channelName in self.channels:
                    newChannel = Channel.Channel(channelName)
                    self.channels[channelName] = newChannel
                    self.channels[channelName].channel_ops.append(user)

                self.channels[channelName].users.append(user)
                self.channels[channelName].welcome_user(user.username)
                self.users_channels_map[user.username] = channelName
        else:
            user.socket.sendall("\n> /join [channel_name]  To create or switch to a channel.".encode('utf8'))

    def nick(self, user, chatMessage):
        isNickNameTaken = False

        if len(chatMessage.split()) >= 2:
            NickName = chatMessage.split()[1]

            if user in self.users:
                if user.nickname == NickName:  # see if user already has this nickname
                    user.socket.sendall("\n> You already have this nickname: {0}".format(NickName).encode('utf8'))
                    isNickNameTaken = True
                else:  # see if this nickname is taken
                    for acc in self.accounts:
                        if self.accounts[acc].nickname == NickName:
                            user.socket.sendall(
                                "\n> Nickname already in use: {0}".format(NickName).encode('utf8'))
                            isNickNameTaken = True
            if not isNickNameTaken:
                user.nickname = NickName
                self.accounts[user.username].nickname = NickName
                user.socket.sendall(
                    "\n> Successfully updated nickname: {0}\n".format(user.nickname).encode('utf8'))

        else:
            self.help(user)

    def user(self, user, chatMessage):
        isUserNameTaken = False
        splitMess = chatMessage.split(' ', 2)
        if len(splitMess) >= 3:
            UserName = splitMess[1]
            RealName = splitMess[2]

            if user in self.users:
                if user.username == UserName:  # see if user already has this username
                    user.socket.sendall("\n> You already have this username: {0}".format(UserName).encode('utf8'))
                    isUserNameTaken = True
                else:  # see if this username is taken
                    for users in self.users:
                        if users.username == UserName:
                            user.socket.sendall(
                                "\n> Username already in use: {0}".format(UserName).encode('utf8'))
                            isUserNameTaken = True

            if not isUserNameTaken and not user.username and not user.realname:
                user.username = UserName
                user.realname = RealName
                user.socket.sendall(
                    "\n> Successfully updated username: {0}\n".format(user.username).encode('utf8'))


        elif len(splitMess) == 1:  # no user given
            user.socket.sendall(
                "\n> Type /user <username> <realname> to to set username and real name\n".format(
                    user.username).encode('utf8'))

    def away(self, user, chatMessage):
        if len(chatMessage.split()) >= 2:  #set away status
            awaymsg = chatMessage.split(' ', 1)[1]
            if user.status == "Online":
                user.status = awaymsg
                user.socket.sendall(
                    "\n> Away message set to: {0}".format(user.status).encode('utf8'))
            else:
                user.socket.sendall(
                    "\n> Away message was set to: {0}\n>    Away message now set to: {1}".format(user.status,awaymsg).encode('utf8'))
                user.status = awaymsg

        elif len(chatMessage.split()) == 1:
            if user.status != "Online":
                user.status = "Online"
                user.socket.sendall(
                    "\n> Away message removed. Status set to: {0}".format(user.status).encode('utf8'))
            else:
                user.socket.sendall(
                    "\n> User status already {0}. Use /away [away_message] to set an away message.".format(user.status).encode('utf8'))

        else:
            self.help(user)

    def get_time(self,user, chatMessage):
        user.socket.sendall(
            "\n> Current local time from server is: {0}\n".format(str(datetime.now())).encode('utf8'))

    def handle_topic(self, user, chatMessage):
        if len(chatMessage.split()) > 2:   # give a channel  topic
            channelName = chatMessage.split(' ', 2)[1]
            if channelName in self.channels:
                new_topic = chatMessage.split(' ', 2)[2]
                self.channels[channelName].set_topic(user, new_topic)
                if self.users_channels_map[user.username] != channelName:
                    user.socket.sendall(
                        "\n> You have set the topic for \"{0}\" to: {1}\n".format(channelName, new_topic).encode('utf8'))
            else:
                user.socket.sendall(
                    "\n> Channel \"{0}\" was not found.\n".format(channelName).encode('utf8'))

        elif len(chatMessage.split()) == 2:   #view current topic of channel
            channelName = chatMessage.split()[1]
            if channelName in self.channels:
                current_topic = self.channels[channelName]._topic
                user.socket.sendall(
                    "\n> Current topic for channel \"{0}\" is set to: {1}\n".format(channelName, current_topic).encode('utf8'))
            else:
                user.socket.sendall(
                    "\n> Channel \"{0}\" was not found.\n".format(channelName).encode('utf8'))

        elif len(chatMessage.split()) == 1:
            user.socket.sendall(
                "\n> Type /topic <channel_name> [topic] to view or set a topic for a channel\n".format(user.status).encode('utf8'))
        else:
            self.help(user)

    def part(self, user, chatMessage):
        if len(chatMessage.split()) >= 2:   #leave channel provided
            channelName = chatMessage.split()[1]
            if user.username in self.users_channels_map:
                if self.users_channels_map[user.username] == channelName:
                    self.channels[self.users_channels_map[user.username]].remove_user_from_channel(user)
                    del self.users_channels_map[user.username]
                    user.socket.sendall(
                        "\n> You have parted from the channel: {0}\n".format(channelName).encode('utf8'))
                else:
                    user.socket.sendall(
                        "\n> User not in channel: {0}\n".format(channelName).encode('utf8'))
            else:
                user.socket.sendall(
                    "\n> User not in any channel.\n".encode('utf8'))
        elif len(chatMessage.split()) == 1:  #leave current channel
            if user.username in self.users_channels_map:
                channelName = self.users_channels_map[user.username]
                self.channels[self.users_channels_map[user.username]].remove_user_from_channel(user)
                del self.users_channels_map[user.username]
                user.socket.sendall(
                "\n> You have parted from the channel: {0}\n".format(channelName).encode('utf8'))
            else:
                user.socket.sendall(
                    "\n> User not in channel.\n".encode('utf8'))
        else:
            self.help(user)

    def kick(self, user, chatMessage):
        if len(chatMessage.split()) >= 2:
            _user = chatMessage.split()[1]
            found = False;
            for users in self.users:
                if users.username == _user:
                    found = True;
                    kicked_user = users
                    if kicked_user != user:
                        if len(chatMessage.split()) >= 3:
                            channel_name = chatMessage.split()[2]
                            if user in self.channels[channel_name].channel_ops:
                                if channel_name == self.users_channels_map[kicked_user.username]:
                                    self.part(kicked_user, channel_name)
                                    user.socket.sendall(
                                        "\n> You have kicked {0} from channel {1}.\n".format(_user, channel_name).encode('utf8'))
                                else:
                                    user.socket.sendall(
                                        "\n> User is not in that channel.\n".encode('utf8'))
                            else:
                                user.socket.sendall(
                                    "\n> You do not have permission to kick on this channel.\n".encode('utf8'))

                        else:   #no channel provided, use users current channel
                            if user.username in self.users_channels_map:
                                 channel_name = self.users_channels_map[user.username]
                                 if user in self.channels[channel_name].channel_ops:
                                     if channel_name == self.users_channels_map[kicked_user.username]:
                                         self.part(kicked_user, channel_name)
                                     else:
                                         user.socket.sendall(
                                             "\n> User is not in your channel.\n".encode('utf8'))
                                 else:
                                     user.socket.sendall(
                                         "\n> You do not have permission to kick on this channel.\n".encode('utf8'))
                            else:
                                user.socket.sendall(
                                    "\n> Please provide the user's channel, or enter their channel, to kick them\n".encode('utf8'))
                    else:
                        user.socket.sendall(
                            "\n> Use /part to remove yourself from a channel\n".encode('utf8'))
            if not found:
                user.socket.sendall(
                    "\n> User not found on server: {0}\n".format(_user).encode('utf8'))

        elif len(chatMessage.split()) == 1:  #no user given
                user.socket.sendall(
                "\n> Type /kick <user> [channel] to kick user from designated or current channel\n".format(user.username).encode('utf8'))


    def list_all_users(self, _user):
        if len(self.users) == 0:
            chatMessage = "\n> No Users connected.\n".encode('utf8')
            _user.socket.sendall(chatMessage)
        else:
            chatMessage = '\n\n> Current users connected: \n'
            for user in self.users:
                chatMessage += "    \n" + user.username + ": "
                if user.status != "Online":
                    chatMessage += "Away - "
                chatMessage += user.status
            chatMessage += "\n"
            _user.socket.sendall(chatMessage.encode('utf8'))

    def handle_ison(self, user, chatMessage):
        split_message = chatMessage.split(' ',1)
        if(len(split_message) == 2):
            user_list = split_message[1].split()
            replyMessage = "\n\n > From queried nicks:\n"
            userMessage = ""
            for _user in self.users:
                if _user.nickname in user_list:
                    userMessage += _user.nickname + "\n"
            if userMessage == "":
                userMessage = "NONE "
            replyMessage += userMessage
            replyMessage += "are connected."
            user.socket.sendall(replyMessage.encode('utf8'))
        else:
            user.socket.sendall(
                "\n> Type /ison <users> to see if space-separated list of users are online\n".format(
                    user.username).encode('utf8'))

    def handle_whois(self, user, chatMessage):
        if len(chatMessage.split()) >= 2:
            request_user = chatMessage.split()[1]
            replyMessage = ""
            for _user in self.users:
                if _user.username == request_user:
                    replyMessage += "\n> "
                    replyMessage += _user.to_string()
            user.socket.sendall(replyMessage.encode('utf8'))
        else:
            user.socket.sendall(
                "\n> Type /whois <user> to see information about a user\n".format(
                    user.username).encode('utf8'))

    def handle_who(self, user, chatMessage):
        if len(chatMessage.split()) >= 2:
            request_channel = chatMessage.split()[1]
            replyMessage = "\n\n> " + request_channel + " has users:\n"
            if request_channel in self.channels:
                replyMessage += self.channels[request_channel].get_all_users_in_channel()
            else:
                replyMessage = "\n\n> Channel not found.\n"
            user.socket.sendall(replyMessage.encode('utf8'))
        else:
            user.socket.sendall(
                "\n> Type /who <channel> to see information about a channel\n".format(
                    user.username).encode('utf8'))

    def handle_pm(self, user, chatMessage):
        split_message = chatMessage.split(' ', 2)
        if len(split_message) >= 3:
            sent = False
            to_user = split_message[1]
            privMessage = split_message[2]
            for _user in self.users:
                if _user.nickname == to_user:
                    _user.socket.sendall(
                        "\nFrom> {0}: {1}".format(user.nickname, privMessage).encode('utf8'))
                    user.socket.sendall(
                        "\nTo> {0}: {1}".format(_user.nickname, privMessage).encode('utf8'))
                    sent = True
                    if _user.status != "Online":
                        user.socket.sendall(
                            "\n\n> {0} is currently away: {1}".format(_user.nickname, _user.status).encode('utf8'))

            if not sent:
                user.socket.sendall(
                    "\n> Error with privmsg.\n> Type /privmsg <nick> <message> to send private message to user\n".encode('utf8'))
        else:
            user.socket.sendall(
                "\n> Type /privmsg <nick> <message> to send private message to user\n".encode('utf8'))

    def send_message(self, user, chatMessage):
        if user.username in self.users_channels_map:
            self.channels[self.users_channels_map[user.username]].broadcast_message(chatMessage, user.username)
        else:
            chatMessage = """\n> You are currently not in any channels:

Use /list to see a list of available channels.
Use /join [channel name] to join a channel.\n\n""".encode('utf8')

            user.socket.sendall(chatMessage)

    def remove_user(self, user):
        if user.username in self.users_channels_map:
            self.channels[self.users_channels_map[user.username]].remove_user_from_channel(user)
            del self.users_channels_map[user.username]

        self.users.remove(user)
        print("Client: {0} has left\n".format(user.username))

    def server_shutdown(self):
        print("Shutting down chat server.\n")
        self.serverSocket.close()

def main():
    chatServer = Server()

    print("\nListening on port {0}".format(chatServer.address[1]))
    print("Waiting for connections...\n")

    chatServer.start_listening()
    chatServer.server_shutdown()

if __name__ == "__main__":
    main()
