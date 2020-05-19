import socket
import pickle

class Network:
    def __init__(self):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server = "127.0.0.1"
        self.port = 7777
        self.addr = (self.server, self.port)
        self.connect()


    def connect(self):
        try:
            self.client.connect(self.addr)
        except Exception as e:
            raise e

    def send(self, data):
        try:
            send_msg(self.client, data)
            got = self.listen()
            print('got:', got)
            return got
        except socket.error as e:
            print(e)

    def only_send(self, data):
        try:
            send_msg(self.client, data)

        except socket.error as e:
            print(e)

    def listen(self, blocking=True):
        try:
            got = recv(self.client, blocking)
            return got

        except BlockingIOError:
            pass
        except socket.error as e:
            print(e)

    def close(self):
        self.client.close()


def get_len(msg):
    return str(len(msg)).ljust(20)

def send_msg(conn, msg):
    msg_b = pickle.dumps(msg)
    len_msg = get_len(msg_b).encode('utf-8')
    conn.sendall(len_msg + msg_b)

def recv(conn, blocking=True):
    try:
        conn.setblocking(blocking)
        msg_len = int(conn.recv(20))
        recved = b""
        while len(recved) < msg_len:
            recved = recved + conn.recv(msg_len-len(recved))
        ret = pickle.loads(recved)
        conn.setblocking(True)
        return ret
    except BlockingIOError:
        conn.setblocking(True)
        return None
    except Exception as e:
        raise e