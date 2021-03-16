""" Omq为一个进程间通信模块，基于Nanomsg开发

Omq封装了两种使用模式，一种为总线模式，另一种为问答模式，分别对应Bus类和Req、Rep类。
使用时，应按需使用不同的模式。
"""
import pickle
import threading

import nnpy


class Bus:
    """ 总线类

    通过该类，可以将消息发送至总线上，其他所有同一总线的节点都能收到消息，也可以订阅指定消息

    Attributes:
        on_message: 收到消息时的回调函数
    """

    def __init__(self, nano: bool = False, base_port: int = 50000):
        self.on_message = None
        self._topics = list()

        self._node = nnpy.Socket(nnpy.AF_SP, nnpy.BUS)
        port: int = base_port
        for port in range(base_port, 65535):
            try:
                self._node.bind(f'tcp://127.0.0.1:{port}')
                break
            except nnpy.errors.NNError:
                # 端口已被占用
                pass

        for target_port in range(base_port, port):
            self._node.connect(f'tcp://127.0.0.1:{target_port}')

        if nano is False:
            # 连接Nano
            self._node.connect('tcp://192.168.3.112:50000')

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self._node.close()

    def publish(self, topic: str, payload):
        """ 发送一条消息到总线上

        Args:
            topic: 消息主题
            payload: 消息内容，可以为任意Python内建类型
        """
        topic = topic.encode()
        self._node.send(topic + b';' + pickle.dumps(payload))

    def subscribe(self, topics: list):
        """ 订阅消息主题

        Args:
            topics: 消息主题列表，可以使用通配符#
        """
        self._topics = topics

    def close(self):
        """ 关闭节点"""
        self._node.close()

    def loop_start(self):
        """ 开始接收消息，非阻塞式 """
        threading.Thread(target=self._main_thread).start()

    def loop_forever(self):
        """ 开始接受消息，阻塞式 """
        self._main_thread()

    def _main_thread(self):
        while True:
            try:
                data = self._node.recv().split(b';')
                topic = data[0].decode()
                payload = pickle.loads(data[1])

                for t in self._topics:
                    if t.endswith('/#'):  # 通配符匹配
                        if topic.startswith(t[:-1]) and topic != t:
                            break
                    elif t in (topic, '#'):  # 完全匹配
                        break
                else:
                    continue  # 如果没有匹配，则不调回调函数

                if self.on_message:
                    self.on_message(topic, payload)
            except nnpy.errors.NNError:
                break


class Req:
    """ 请求类

    通过该类，可以向Rep（响应）类发起请求，并获取响应
    """

    def __init__(self, target_port: int, target_ip: str = '127.0.0.1'):
        self._node = nnpy.Socket(nnpy.AF_SP, nnpy.REQ)
        self._node.connect(f'tcp://{target_ip}:{target_port}')

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self._node.close()

    def req(self, data):
        """ 发起请求

        Args:
            data: 请求体，可以为任意Python内建类型

        Returns:
            响应体，为任意Python内建类型
        """
        self._node.send(pickle.dumps(data))
        res = self._node.recv()
        return pickle.loads(res)

    def close(self):
        """ 关闭节点 """
        self._node.close()


class Rep:
    """ 响应类

    通过该类，可以响应Req的请求
    """

    def __init__(self, port: int, handler):
        self._handler = handler
        self._node = nnpy.Socket(nnpy.AF_SP, nnpy.REP)
        self._node.bind(f'tcp://127.0.0.1:{port}')

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self._node.close()

    def _main_thread(self):
        while True:
            try:
                data = self._node.recv()
                data = pickle.loads(data)
                res = self._handler(data)
                self._node.send(pickle.dumps(res))
            except nnpy.errors.NNError:
                break

    def loop_start(self):
        """ 开始接收消息，非阻塞式 """
        threading.Thread(target=self._main_thread).start()

    def loop_forever(self):
        """ 开始接受消息，阻塞式 """
        self._main_thread()


if __name__ == '__main__':
    b = Bus()

    def on_message(topic, payload):
        print(topic, payload)

    b.on_message = on_message
    b.subscribe(['test/#'])
    b.loop_forever()
    b.close()
