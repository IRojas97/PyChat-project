import socket
import sys
import threading
import Channel
import User
import Util
from datetime import datetime


class Server:
    SERVER_CONFIG = {"MAX_CONNECTIONS": 15}

    HELP_MESSAGE = """\n> The list of commands available are:

/help                   - Show the instructions
/join [channel_name]    - To create or switch to a channel.
/quit                   - Exits the program.
/list                   - Lists all available channels.
/nick [nickname]        - Set a new nickname if not already in use.
/away [away_message]    - Set a new away message or remove away status.
/time                   - Returns the local time from the server \n\n""".encode('utf8')

    WELCOME_MESSAGE = "\n> Welcome to our chat app!!! What is your name?\n".encode('utf8')

    def __init__(self, host=socket.gethostbyname('localhost'), port=50000, allowReuseAddress=True, timeout=3):
        self.address = (host, port)
        self.channels = {} # Channel Name -> Channel
        self.users_channels_map = {} # User Name -> Channel Name
        self.client_thread_list = [] # A list of all threads that are either running or have finished their task.
        self.users = [] # A list of all the users who are connected to the server.
        self.exit_signal = threading.Event()

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
        username = Util.generate_username(user.socket.recv(size).decode('utf8')).lower()

        while not username:
            user.socket.sendall("\n> Please enter your full name(first and last. middle optional).\n".encode('utf8'))
            username = Util.generate_username(user.socket.recv(size).decode('utf8')).lower()

        user.username = username

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
                self.list_all_channels(user)
            elif '/help' in chatMessage:
                self.help(user)
            elif '/join' in chatMessage:
                self.join(user, chatMessage)
            elif 'nick' in chatMessage:
                self.nick(user,chatMessage)
            elif '/away' in chatMessage:
                self.away(user, chatMessage)
            elif '/time' in chatMessage:
                self.get_time(user, chatMessage)
            else:
                self.send_message(user, chatMessage + '\n')

        if self.exit_signal.is_set():
            user.socket.sendall('/squit'.encode('utf8'))

        user.socket.close()

    def quit(self, user):
        user.socket.sendall('/quit'.encode('utf8'))
        self.remove_user(user)

    def list_all_channels(self, user):
        if len(self.channels) == 0:
            chatMessage = "\n> No rooms available. Create your own by typing /join [channel_name]\n".encode('utf8')
            user.socket.sendall(chatMessage)
        else:
            chatMessage = '\n\n> Current channels available are: \n'
            for channel in self.channels:
                chatMessage += "    \n" + channel + ": " + str(len(self.channels[channel].users)) + " user(s)"
            chatMessage += "\n"
            user.socket.sendall(chatMessage.encode('utf8'))

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

                self.channels[channelName].users.append(user)
                self.channels[channelName].welcome_user(user.username)
                self.users_channels_map[user.username] = channelName
        else:
            self.help(clientSocket)

    def nick(self, user, chatMessage):
        isNickNameTaken = False

        if len(chatMessage.split()) >= 2:
            NickName = chatMessage.split()[1]

            if user in self.users:
                if user.nickname == NickName:  # see if user already has this nickname
                    user.socket.sendall("\n> You already have this nickname: {0}".format(NickName).encode('utf8'))
                    isNickNameTaken = True
                else:  # see if this nickname is taken
                    for users in self.users:
                        if users.nickname == NickName:
                            user.socket.sendall(
                                "\n> Nickname already in use: {0}".format(NickName).encode('utf8'))
                            isNickNameTaken = True

            if not isNickNameTaken:
                user.nickname = NickName
                user.socket.sendall(
                    "\n> Successfully updated nickname: {0}".format(user.nickname).encode('utf8'))

        else:
            self.help(clientSocket)

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
            self.help(clientSocket)

    def get_time(self,user, chatMessage):
        user.socket.sendall(
            "\n> Current local time from server is: {0}".format(str(datetime.now())).encode('utf8'))


    def send_message(self, user, chatMessage):
        if user.username in self.users_channels_map:
            self.channels[self.users_channels_map[user.username]].broadcast_message(chatMessage, "{0}: ".format(user.username))
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
