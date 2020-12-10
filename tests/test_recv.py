# import zmq
# import pickle
# import time

# context = zmq.Context()
# socket = context.socket(zmq.SUB)
# socket.connect("tcp://localhost:5555")
# # socket.send_multipart([b'basic', b'hello world'])
# # time.sleep(1)
# socket.setsockopt(zmq.SUBSCRIBE, b'test')  # 接收所有消息
# while True:
#     topic, msg = socket.recv_multipart()
#     msg = pickle.loads(msg)
#     print(f'{topic=}', f'{msg=}')
#     # response = pickle.loads(msg)
#     # print(f"{response=}, {topic=}")
#     # print(response['extend']['CPU_Usage'])

import omq
import time

def on_message(topic, msg):
    print(topic, msg)


s = omq.Socket(host='172.29.4.253')
s.on_message = on_message
s.subscribe('test')
s.loop_forever()

# import zmq

# socket = zmq.Context().socket(zmq.REP)
# socket.bind('tcp://0.0.0.0:52002')
# msg = socket.recv()
# print(msg)
# socket.send(b'o=h')
