import atexit
import socket
import threading
import tkinter as tk
import tkinter.scrolledtext
import requests
import time
import sys

from queue import Queue


def close_all_sockets():
    if g.socket:
        g.socket.close()
    if g.waiting_socket:
        g.waiting_socket.close()


atexit.register(close_all_sockets)
atexit.register(print, '[MyChat] Closing...')

class GlobalVars:
    def __init__(self):
        self.TCP_IP_LOCAL = socket.gethostbyname(socket.gethostname())
        try:
            self.TCP_IP_PUBLIC = requests.get('https://api.ipify.org').text
        except:
            self.TCP_IP_PUBLIC = 'unknown'
        self.TCP_PORT = 1250
        self.MSG_LEN_SIZE = 8
        self.MSG_TOTAL_SIZE = 256
        self.USERNAME = 'You'
        self.OTHER_USERNAME = 'The connected user'
        self.RUNNING = True
        self.socket = None
        self.waiting_socket = None
        self.wnd_chat = None


g = GlobalVars()

def on_disconnect():
    g.RUNNING = False
    g.wnd_chat.disable_sending()
    if g.socket:
        g.socket.close()
    if g.waiting_socket:
        g.waiting_socket.close()
        g.wnd_chat.display_application_message(
            f'Disconnected. You may now close the window.')
    g.wnd_chat.destroy()


def send_message(msg):
    len_str = str(len(msg)).ljust(g.MSG_LEN_SIZE)
    content_str = msg
    data = (len_str + content_str).encode()
    data = data + bytes(g.MSG_TOTAL_SIZE - len(data))
    total_sent_bytes = 0
    while total_sent_bytes < g.MSG_TOTAL_SIZE:
        sent_bytes = g.socket.send(data[total_sent_bytes:])
        if sent_bytes == 0:
            on_disconnect()
            break
        total_sent_bytes += sent_bytes


def receive_message():
    chunks = []
    bytes_received = 0
    while bytes_received < g.MSG_TOTAL_SIZE:
        chunk = g.socket.recv(min(g.MSG_TOTAL_SIZE - bytes_received, 2048))
        if chunk == b'':
            on_disconnect()
            break
        chunks.append(chunk)
        bytes_received += len(chunk)
    data = b''.join(chunks).decode()
    msg_len = int(data[:g.MSG_LEN_SIZE].strip())
    msg_text = data[g.MSG_LEN_SIZE:(g.MSG_LEN_SIZE + msg_len)]
    return msg_text


def get_data_from_connection_dialog(g):
    connection_dialog = tk.Tk()

    connection_dialog.protocol('WM_DELETE_WINDOW', sys.exit)
    connection_dialog.title('MyChat')
    connection_dialog.rowconfigure([6, 7], pad=20)

    localip_desc = 'Your local IP address:'
    lbl_localip_desc = tk.Label(connection_dialog, text=localip_desc)
    lbl_localip_desc.grid(row=0, column=0, sticky='NESW')
    lbl_localip = tk.Label(connection_dialog, text=g.TCP_IP_LOCAL)
    lbl_localip.grid(row=0, column=1, sticky='NESW')

    publicip_desc = 'Your public IP address:'
    lbl_publicip_desc = tk.Label(connection_dialog, text=publicip_desc)
    lbl_publicip_desc.grid(row=1, column=0, sticky='NESW')
    lbl_publicip = tk.Label(connection_dialog, text=g.TCP_IP_PUBLIC)
    lbl_publicip.grid(row=1, column=1, sticky='NESW')

    displayed_name_desc = 'Your displayed name:'
    lbl_displayed_name_desc = tk.Label(connection_dialog,
                                       text=displayed_name_desc)
    lbl_displayed_name_desc.grid(row=2, column=0, sticky='NESW')
    ent_displayed_name = tk.Entry(connection_dialog, justify=tk.RIGHT)
    ent_displayed_name.insert(tk.END, 'user')
    ent_displayed_name.grid(row=2, column=1, sticky='EW')

    connection_dialog.rowconfigure(3, minsize=30)

    option = tk.StringVar()

    ent_address = tk.Entry(connection_dialog,
                           state='disabled',
                           justify=tk.RIGHT)
    ent_address.grid(row=6, column=1, sticky='EW')

    def update_ent_address_state():
        if option.get() == 'connect':
            ent_address.config(state='normal')
        else:
            ent_address.delete(0, tk.END)
            ent_address.config(state='disabled')

    radio_wait = tk.Radiobutton(connection_dialog,
                                text='Wait for another user to connect',
                                indicator=0,
                                justify=tk.LEFT,
                                variable=option,
                                value='wait',
                                command=update_ent_address_state)
    radio_wait.grid(row=4, column=0, sticky='NESW')
    radio_wait.select()

    radio_connect = tk.Radiobutton(connection_dialog,
                                   text='Connect another user',
                                   indicator=0,
                                   justify=tk.LEFT,
                                   variable=option,
                                   value='connect',
                                   command=update_ent_address_state)
    radio_connect.grid(row=5, column=0, sticky='NESW')
    lbl_address = tk.Label(connection_dialog,
                           text='Address to connect:',
                           justify=tk.RIGHT)
    lbl_address.grid(row=6, column=0, sticky='NESW')

    data = None

    def get_data_and_destroy_window():
        nonlocal data
        g.USERNAME = ent_displayed_name.get()
        data = option.get(), str(ent_address.get())
        connection_dialog.destroy()

    btn_start = tk.Button(connection_dialog,
                          text='Start!',
                          command=get_data_and_destroy_window)
    btn_start.grid(row=7, column=1)
    connection_dialog.mainloop()
    return data


class ChatWindow(tk.Tk):
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.title('MyChat')

        self.columnconfigure(0, minsize=400, weight=1)
        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=0)

        self.text_area = tkinter.scrolledtext.ScrolledText(self,
                                                           bg='lightgray')
        self.text_area.config(state='disabled')
        self.text_area.grid(row=0, column=0, columnspan=2, sticky='NSEW')

        self.ent_message = tk.Entry(self, state='disabled')
        self.ent_message.grid(row=1, column=0, sticky='EW')
        self.ent_message.bind('<Return>', self.on_return_press)

        self.btn_send = tk.Button(self,
                                  text='Send!',
                                  command=self.__on_send_button_click,
                                  state='disabled')
        self.btn_send.grid(row=1, column=1, sticky='EW')

        self.bind('<<Message>>', self.__handle_message)
        self.bind('<<Enable>>', self.__handle_enable)
        self.bind('<<Disable>>', self.__handle_disable)

        self.message_queue = Queue()

    def write_line_in_text_area(self, str):
        self.text_area.config(state='normal')
        print(str)
        self.text_area.insert(tk.END, f'{str}\n')
        self.text_area.config(state='disabled')

    def display_application_message(self, str):
        self.display_message(f'[MyChat] {str}')

    def display_message(self, str):
        self.message_queue.put(str)
        self.event_generate('<<Message>>')

    def display_user_message(self, str):
        self.display_message(f'[{self.config.USERNAME}] {str}')

    def display_other_user_message(self, str):
        self.display_message(f'[{self.config.OTHER_USERNAME}] {str}')

    def enable_sending(self):
        self.event_generate('<<Enable>>')

    def __handle_enable(self, event):
        self.ent_message.config(state='normal')
        self.btn_send.config(state='normal')

    def disable_sending(self):
        self.event_generate('<<Disable>>')
    
    def __handle_disable(self, event):
        self.ent_message.config(state='disabled')
        self.btn_send.config(state='disabled')

    def __handle_message(self, event):
        message = self.message_queue.get()
        self.write_line_in_text_area(message)
    
    def on_return_press(self, event):
        self.__on_send_button_click()

    def __on_send_button_click(self):
        message = self.ent_message.get()
        if message == '':
            return
        self.ent_message.delete(0, tk.END)
        send_message(message)
        if message.startswith('!username '):
            new_username = message[len('!username '):]
            g.wnd_chat.display_application_message(f'You have set your username to `{new_username}`')
            g.USERNAME = new_username
        elif message:
            self.display_user_message(message)

    def mainloop(self):
        super().mainloop()
        self.config.RUNNING = False


def handle_incoming_messages(s):
    g.wnd_chat.enable_sending()
    g.socket = s
    send_message(f'!username {g.USERNAME}')
    while g.RUNNING:
        message = receive_message()
        if not message:
            continue
        if message.startswith('!username '):
            new_username = message[len('!username '):]
            g.wnd_chat.display_application_message(f'{g.OTHER_USERNAME} has set their username to `{new_username}`')
            g.OTHER_USERNAME = new_username
        else:
            g.wnd_chat.display_other_user_message(message)
    if s:
        s.close()
        g.socket = None


def do_listen():
    g.wnd_chat.display_application_message(
        f'Listening under public IP {g.TCP_IP_PUBLIC} and local IP {g.TCP_IP_LOCAL}'
    )
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        g.waiting_socket = s
        s.bind((g.TCP_IP_LOCAL, g.TCP_PORT))
        s.listen(1)
        conn, addr = s.accept()
        addr = f'{addr[0]}:{addr[1]}'
        g.wnd_chat.display_application_message(f'User at {addr} has connected.')
        handle_incoming_messages(conn)


def do_connect(ip):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect((ip, g.TCP_PORT))
    except:
        g.wnd_chat.display_application_message(f'Failed to connect to {ip}')
        on_disconnect()
    addr = ':'.join((ip, str(g.TCP_PORT)))
    g.wnd_chat.display_application_message(f'Successfully connected to {addr}.')
    handle_incoming_messages(s)


def setup_sockets(ip):
    if mode == 'wait':
        g.wnd_chat.display_application_message(
            'Waiting for another user to connect...')
        do_listen()
    elif mode == 'connect':
        g.wnd_chat.display_application_message(f'Connecting to {ip}...')
        do_connect(ip)

mode, ip = get_data_from_connection_dialog(g)
g.wnd_chat = ChatWindow(g)

socket_thread = threading.Thread(target=setup_sockets,
                                 args=(ip, ),
                                 name='SocketThread',
                                 daemon=True)
socket_thread.start()
g.wnd_chat.mainloop()

sys.exit(0)
