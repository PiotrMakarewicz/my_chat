import socket
import threading

TCP_IP = socket.gethostbyname(socket.gethostname())
TCP_PORT = 3485
MSG_LEN_SIZE = 8
MSG_TOTAL_SIZE = 256
DISCONNECT_MSG = '%$$*^@(#*&#($&*^*(%$%#&*%&*%^%$*&%!!!!%$%$%$%$*$%*^#*@^&@%^&@%&&@'

# TODO: wątek pingujący i rozłączający
# TODO: wątek odpowiadający na pingi
# możliwe problemy: firewall => na początek łączymy sockety lokalnie, potem zobaczymy
# przy uruchomieniu wybór - czekaj na połączenie vs. połącz się z...

def send_message(s, msg):
    len_str = str(len(msg)).ljust(MSG_LEN_SIZE)
    content_str = msg
    data = (len_str + content_str).encode()
    data = data + bytes(MSG_TOTAL_SIZE - len(data))
    total_sent_bytes = 0
    while total_sent_bytes < MSG_TOTAL_SIZE:
        sent_bytes = s.send(data[total_sent_bytes:])
        #print(f'Sent {sent_bytes} bytes')
        if sent_bytes == 0:
            raise RuntimeError("socket connection broken")
        total_sent_bytes += sent_bytes


def receive_message(s):
    chunks = []
    bytes_received = 0
    while bytes_received < MSG_TOTAL_SIZE:
        chunk = s.recv(min(MSG_TOTAL_SIZE - bytes_received, 2048))
        if chunk == b'':
            raise RuntimeError("socket connection broken")
        chunks.append(chunk)
        bytes_received += len(chunk)
        # print(f'Received {bytes_received} bytes')
    data = b''.join(chunks).decode()
    msg_len = int(data[:MSG_LEN_SIZE].strip())
    msg_text = data[MSG_LEN_SIZE:(MSG_LEN_SIZE+msg_len)]
    return msg_text

def handle_incoming_messages(s, sender):
    while True:
        message = receive_message(s)
        if message == DISCONNECT_MSG:
            print(f'{sender} has disconnected. Closing...')
            break
        else:
            print(f'[{sender}]', message)
            
def handle_user_input(s):
    print('Now you may send messages')
    while (True):
        msg = input()
        send_message(s, msg)
        # print('Received user input:', msg)

def do_listen():
    print('Listening...')
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((TCP_IP, TCP_PORT))
        s.listen(1)
        conn, addr = s.accept()
        addr = f'{addr[0]}:{addr[1]}'
        print(addr, 'has connected')
        incoming_messages_thread = threading.Thread(
            target=handle_incoming_messages, args=(conn, addr))
        incoming_messages_thread.start()
        handle_user_input(conn)     
        

def do_connect():
    ip = input('What IP do you want to connect to?')
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((ip, TCP_PORT))
        addr = ':'.join((ip, str(TCP_PORT)))
        print('Connected to', addr)
        incoming_messages_thread = threading.Thread(
            target=handle_incoming_messages, args=(s, addr))
        incoming_messages_thread.start()
        handle_user_input(s)  


while True:
    ans = input('Do you want to listen (L) or connect (C)?')
    if ans.upper() == 'L':
        socket_thread = threading.Thread(target=do_listen)
        break
    elif ans.upper() == 'C': 
        socket_thread = threading.Thread(target=do_connect)
        break

socket_thread.run()
# with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
#     s.bind((TCP_IP, TCP_PORT))
#     s.listen()