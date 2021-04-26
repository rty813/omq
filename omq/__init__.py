from typing import Any

from .omq import Bus, Rep, SuperNode, SlaveNode, req

class Addr:
    """ 地址常量 """
    NANO = ('192.168.3.112', 51000)
    MAIN = ('192.168.3.11', 51000)
    COMMUNICATION = ('192.168.3.11', 51001)
    RADAR = ('192.168.3.11', 51002)
    PLAN = ('192.168.3.11', 51003)
    CONTROL = ('192.168.3.11', 51004)
