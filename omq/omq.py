""" Omq为一个进程间通信模块，基于Nanomsg开发

Omq封装了三种使用模式：总线模式、问答模式、主从模式，分别对应Bus类；Req、Rep类；SuperNode、SlaveNode类。
总线模式适合多对多通信，采用类似于MQTT式的发布订阅模型。
问答模式适合提供服务的类型，类似于HTTP请求。
主从模式适合一对多通信，一个主机和多个从机建立单独的通信。
使用时，应按需使用不同的模式。
"""
from typing import Any, List
import pickle
import threading

import nnpy

from . import Addr


class Bus:
    """ 总线类

    通过该类，可以将消息发送至总线上，其他所有同一总线的节点都能收到消息，也可以订阅指定消息

    """
    def __init__(self, nano: bool = False, base_port: int = 50000) -> None:
        self._on_message = None
        self._topics = list()

        self._node = nnpy.Socket(nnpy.AF_SP, nnpy.BUS)
        port: int = base_port
        for port in range(base_port, 65535):
            try:
                self._node.bind(f'tcp://0.0.0.0:{port}')
                break
            except nnpy.errors.NNError:
                # 端口已被占用
                pass

        for target_port in range(base_port, port):
            self._node.connect(f'tcp://127.0.0.1:{target_port}')

        if nano is False:
            # 连接Nano
            self._node.connect('tcp://192.168.3.112:50000')

    @property
    def on_message(self):
        return self._on_message

    @on_message.setter
    def on_message(self, func):
        """ 设置回调函数，接收参数为topic和payload """
        self._on_message = func

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self._node.close()

    def publish(self, topic: str, payload: Any) -> None:
        """ 发送一条消息到总线上

        Args:
            topic: 消息主题
            payload: 消息内容，可以为任意Python内建类型
        """
        topic = topic.encode()
        self._node.send(topic + b'^&*;' + pickle.dumps(payload))

    def subscribe(self, topics: List) -> None:
        """ 订阅消息主题

        Args:
            topics: 消息主题列表，可以使用通配符#
        """
        self._topics = topics

    def close(self) -> None:
        """ 关闭节点"""
        self._node.close()

    def loop_start(self) -> None:
        """ 开始接收消息，非阻塞式 """
        threading.Thread(target=self._main_thread).start()

    def loop_forever(self) -> None:
        """ 开始接受消息，阻塞式 """
        self._main_thread()

    def _main_thread(self):
        while True:
            try:
                data = self._node.recv().split(b'^&*;')
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
            except KeyboardInterrupt:
                self.close()
                break


class SuperNode(Bus):
    """ 中心节点

    该类为中心节点类，被动连接，收发消息。

    Attributes:
        on_message: 收到消息时的回调函数，参数为slave_id和payload
    """
    def __init__(self, port: int = 40000) -> None:  # pylint: disable=super-init-not-called
        self.on_message = None
        self._node = nnpy.Socket(nnpy.AF_SP, nnpy.BUS)
        self._node.bind(f'tcp://0.0.0.0:{port}')

    def publish(self, slave_id: str, payload: Any) -> None:
        """ 给子节点发消息

        Args:
            slave_id: 子节点ID
            payload: 消息内容，可以为任意Python内建类型
        """
        topic = ('M2S/' + slave_id).encode()
        self._node.send(topic + b'^&*;' + pickle.dumps(payload))

    def _main_thread(self) -> None:
        while True:
            try:
                data = self._node.recv().split(b'^&*;')
                topic = data[0].decode()
                payload = pickle.loads(data[1])

                if not topic.startswith('S2M/'):
                    continue

                slave_id = topic[4:]  # 去掉开头的"S2M/"

                if self.on_message:
                    self.on_message(slave_id, payload)
            except nnpy.errors.NNError:
                break


class SlaveNode(Bus):
    """ 子节点

    该类为子节点类，可以与中心节点建立一对一通信。需要填写中心节点的ip和port。

    Attributes:
        on_message: 收到消息时的回调函数，参数为payload
    """
    def __init__(self, slave_id: str, super_node_ip: str, super_node_port: int = 40000) -> None:
        self.on_message = None
        self._slave_id = slave_id
        self._node = nnpy.Socket(nnpy.AF_SP, nnpy.BUS)
        self._node.connect(f'tcp://{super_node_ip}:{super_node_port}')

    def publish(self, payload: Any) -> None:
        """ 给中心节点发消息

        Args:
            payload: 消息内容，可以为任意Python内建类型
        """
        topic = ('S2M/' + self._slave_id).encode()
        self._node.send(topic + b'^&*;' + pickle.dumps(payload))

    def _main_thread(self) -> None:
        while True:
            try:
                data = self._node.recv().split(b'^&*;')
                topic = data[0].decode()
                payload = pickle.loads(data[1])

                if not topic == f'M2S/{self._slave_id}':
                    continue

                if self.on_message:
                    self.on_message(payload)
            except nnpy.errors.NNError:
                break


def req(target: Addr, topic: str, payload: Any, timeout: int = 0) -> Any:
    """ 发起req请求

    Args:
        target: 目标地址
        topic: 主题
        payload: 消息
        timeout: 发送超时时间（毫秒）。默认为0，即非阻塞。若为-1，则将一直等待。
    """

    node = nnpy.Socket(nnpy.AF_SP, nnpy.REQ)
    node.connect(f'tcp://{target[1]}:{target[0]}')
    node.setsockopt(nnpy.SOL_SOCKET, nnpy.RCVTIMEO, timeout)

    node.send(topic.encode() + b'^&*;' + pickle.dumps(payload))
    try:
        res = node.recv()
    except nnpy.errors.NNError:
        res = None

    node.close()
    return pickle.loads(res)


class Rep:
    """ 响应类

    通过该类，可以响应Req的请求
    """
    def __init__(self, port: int, handler) -> None:
        self._handler = handler
        self._node = nnpy.Socket(nnpy.AF_SP, nnpy.REP)
        self._node.bind(f'tcp://0.0.0.0:{port}')

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self._node.close()

    def _main_thread(self) -> None:
        while True:
            try:
                data = self._node.recv().split(b'^&*;')
                topic = data[0].decode()
                payload = pickle.loads(data[1])

                res = self._handler(topic, payload)
                self._node.send(pickle.dumps(res))
            except nnpy.errors.NNError:
                break

    def loop_start(self) -> None:
        """ 开始接收消息，非阻塞式 """
        threading.Thread(target=self._main_thread).start()

    def loop_forever(self) -> None:
        """ 开始接受消息，阻塞式 """
        self._main_thread()

    def close(self) -> None:
        """ 关闭节点 """
        self._node.close()
