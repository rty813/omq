# import zmq
# import time
# import sys
# import pickle
# import threading
# context = zmq.Context()
# socket = context.socket(zmq.REQ)
# socket.connect("tcp://localhost:5556")

# def recv():
#     socket_r = zmq.Context().socket(zmq.SUB)
#     socket_r.connect('tcp://localhost:5555')
#     socket_r.setsockopt(zmq.SUBSCRIBE, b'basic')
#     while True:
#         topic, msg = socket_r.recv_multipart()
#         print(f'{topic=}, {msg=}')

# threading.Thread(target=recv).start()
# while True:
#     msg = input("请输入要发布的信息：").strip()
#     if msg == 'b':
#         sys.exit()
#     socket.send_multipart([b'basic', msg.encode()])
#     socket.recv()
#     socket.send_multipart([b'test', pickle.dumps({'hello': msg})])
#     socket.recv()
#     time.sleep(1)

import omq
import time
s = omq.Socket()
i = 0
while True:
    try:
        s.publish('nihao', i)
        s.publish('test', i)
    except:
        print('send error')
        import traceback
        traceback.print_exc()
    print(i)
    i += 1
    time.sleep(1)

# import zmq
# socket = zmq.Context().socket(zmq.REQ)
# socket.connect('tcp://localhost:52002')
# socket.send(b'hello world')
# msg = socket.recv()
# print(msg)