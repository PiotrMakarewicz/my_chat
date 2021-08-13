import socket
import threading

HOST = '127.0.0.1'
PORT = 63428

# TODO: wątek pingujący i rozłączający
# TODO: wątek odpowiadający na pingi

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((HOST, PORT))
    s.listen()