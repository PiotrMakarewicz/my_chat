import socket
import threading
import requests
import tkinter as tk

TCP_IP_LOCAL = socket.gethostbyname(socket.gethostname())
try:
    TCP_IP_PUBLIC = requests.get('https://api.ipify.org').text
except:
    TCP_IP_PUBLIC = 'unknown'
TCP_PORT = 3485
MSG_LEN_SIZE = 8
MSG_TOTAL_SIZE = 256

# TODO: wątek pingujący i rozłączający
# TODO: odpowiadanie na pingi 


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
    msg_text = data[MSG_LEN_SIZE:(MSG_LEN_SIZE + msg_len)]
    return msg_text


def handle_incoming_messages(s, sender):
    while True:
        message = receive_message(s)
        print(f'[{sender}]', message)


def handle_user_input(s):
    print('Now you may send messages')
    while (True):
        msg = input()
        send_message(s, msg)
        # print('Received user input:', msg)


def do_listen():
    print(
        f'Listening under public IP {TCP_IP_PUBLIC} and local IP {TCP_IP_LOCAL}'
    )
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((TCP_IP_LOCAL, TCP_PORT))
        s.listen(1)
        conn, addr = s.accept()
        addr = f'{addr[0]}:{addr[1]}'
        print(addr, 'has connected')
        incoming_messages_thread = threading.Thread(
            target=handle_incoming_messages, args=(conn, addr))
        incoming_messages_thread.start()
        handle_user_input(conn)


def do_connect(ip, *args):
    print(ip, *args)
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    except:
        raise Exception(f'Failed to connect to {ip}')
    try:
        s.connect((ip, TCP_PORT))
        addr = ':'.join((ip, str(TCP_PORT)))
        print('Connected to', addr)
        incoming_messages_thread = threading.Thread(
            target=handle_incoming_messages, args=(s, addr))
        incoming_messages_thread.start()
        handle_user_input(s)
    finally:
        s.close()


def get_data_from_connection_dialog():
    connection_dialog = tk.Tk()

    connection_dialog.title('MyChat | Connection dialog')
    connection_dialog.rowconfigure([6, 7], pad=20)

    localip_desc = 'Your local IP address:'
    lbl_localip_desc = tk.Label(connection_dialog, text=localip_desc)
    lbl_localip_desc.grid(row=0, column=0, sticky='NESW')
    lbl_localip = tk.Label(connection_dialog, text=TCP_IP_LOCAL)
    lbl_localip.grid(row=0, column=1, sticky='NESW')

    publicip_desc = 'Your public IP address:'
    lbl_publicip_desc = tk.Label(connection_dialog, text=publicip_desc)
    lbl_publicip_desc.grid(row=1, column=0, sticky='NESW')
    lbl_publicip = tk.Label(connection_dialog, text=TCP_IP_PUBLIC)
    lbl_publicip.grid(row=1, column=1, sticky='NESW')

    displayed_name_desc = 'Your displayed name:'
    lbl_displayed_name_desc = tk.Label(connection_dialog, text=displayed_name_desc)
    lbl_displayed_name_desc.grid(row=2, column=0, sticky='NESW')
    ent_displayed_name = tk.Entry(connection_dialog, justify=tk.RIGHT)
    ent_displayed_name.insert(tk.END, 'user')
    ent_displayed_name.grid(row=2, column=1, sticky='EW')

    connection_dialog.rowconfigure(3, minsize=30)

    option = tk.StringVar()

    ent_address = tk.Entry(connection_dialog, state='disabled', justify=tk.RIGHT)
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
        data = option.get(), str(ent_address.get())
        connection_dialog.destroy()

    btn_start = tk.Button(connection_dialog,
                          text='Start!',
                          command=get_data_and_destroy_window)
    btn_start.grid(row=7, column=1)
    connection_dialog.mainloop()
    return data


mode, ip = get_data_from_connection_dialog()
if mode == 'wait':
    socket_thread = threading.Thread(target=do_listen)
elif mode == 'connect':
    socket_thread = threading.Thread(target=do_connect, args=[ip])

socket_thread.run()
# with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
#     s.bind((TCP_IP, TCP_PORT))
#     s.listen()