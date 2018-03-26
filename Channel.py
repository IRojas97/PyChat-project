
class Channel:
    def __init__(self, name, topic='No topic'):
        self.users = [] # A list of the users in this channel.
        self.channel_name = name
        self._topic = topic
        self.channel_modes = []
        self.channel_ops = []


    def welcome_user(self, user):
        all_users = self.get_all_users_in_channel()
        temp = user.nickname
        if user.usertype == 'admin':
            temp += "*"
        elif user.usertype == 'sysop':
            temp += "$"
        elif user in self.channel_ops:
            temp += "+"

        for _user in self.users:
            if _user.username is user.username:
                chatMessage = '\n\n> {0} have joined the channel {1}!\n|{2}'.format("You", self.channel_name, all_users).encode('utf8')
                _user.socket.sendall(chatMessage)
                chatMessage = '> Topic currently set to: {0}\n'.format(self._topic).encode('utf8')
                _user.socket.sendall(chatMessage)
            else:
                chatMessage = '\n> {0} has joined the channel {1}!\n\n|{2}'.format(temp, self.channel_name, all_users).encode('utf8')
                _user.socket.sendall(chatMessage)

    def broadcast_message_all(self, chatMessage):
        for user in self.users:
                user.socket.sendall("{0}".format(chatMessage).encode('utf8'))

    def broadcast_message(self, chatMessage, username=''):
        for user in self.users:
            if user.username is username:
                user.socket.sendall("You: {0}".format(chatMessage).encode('utf8'))
            else:
                user.socket.sendall("{0}: {1}".format(username, chatMessage).encode('utf8'))




    def get_all_users_in_channel(self):
        temp = ""
        if len(self.users) >= 1:
            for user in self.users:
                if user.usertype == 'admin':
                    temp += user.nickname
                    temp += "* "
                elif user.usertype == 'sysop':
                    temp += user.nickname
                    temp += "$ "
                elif user in self.channel_ops:
                    temp += user.nickname
                    temp += "+ "
                else:
                    temp += user.nickname
                    temp += " "
        else:
            temp += "NONE "
        return temp[:-1]


    def remove_user_from_channel(self, user):
        temp = user.nickname
        if user.usertype == 'admin':
            temp += "*"
        elif user.usertype == 'sysop':
            temp += "$"
        elif user in self.channel_ops:
            temp += "+"
        self.users.remove(user)
        leave_message = "\n> {0} has left the channel {1}\n".format(temp, self.channel_name)
        self.broadcast_message_all(leave_message)

    def set_topic(self, user, newtopic):
        if "t" not in self.channel_modes:
            self._topic = newtopic
            channelMessage = '\n> set topic for channel to: {0}\n'.format(self._topic)
            self.broadcast_message(channelMessage, user.username)
        elif user in self.channel_ops:
            self._topic = newtopic
            channelMessage = '\n> set topic for channel to: {0}\n'.format(self._topic)
            self.broadcast_message(channelMessage, user.username)
        else:
            chatMessage = '\n\n> You do not have permission to change topic\n'.encode('utf8')
            user.socket.sendall(chatMessage)

    def topic(self):
        return self._topic
