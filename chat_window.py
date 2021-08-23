import tkinter as tk
import tkinter.scrolledtext as st

other_username = 'user'
other_ip = '192.34.5.6'

wnd_chat = tk.Tk()
wnd_chat.title('MyChat')

wnd_chat.columnconfigure(0, minsize=400, weight=1)
wnd_chat.rowconfigure(0, weight=1)
wnd_chat.rowconfigure(1, weight=0)

text_area = st.ScrolledText(wnd_chat, bg='lightgray')
text_area.config(state='disabled')
text_area.grid(row=0, column=0, columnspan=2, sticky='NSEW')

ent_message = tk.Entry(wnd_chat)
ent_message.grid(row=1, column=0, sticky='EW')

btn_send = tk.Button(wnd_chat, text='Send!')
btn_send.grid(row=1, column=1, sticky='EW')

wnd_chat.mainloop()