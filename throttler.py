import subprocess

import config


def class_id(ip):
    return 10 + int(ip.split(".")[-1])


def limit_commands(ip, speed):
    dev = config.INTERFACE
    cid = class_id(ip)
    return [
        "tc class replace dev %s parent 1: classid 1:%d htb rate %smbit ceil %smbit" % (dev, cid, speed, speed),
        "tc filter replace dev %s parent 1: protocol ip prio 1 u32 match ip dst %s/32 flowid 1:%d" % (dev, ip, cid),
    ]


def remove_commands(ip):
    dev = config.INTERFACE
    return [
        "tc filter del dev %s parent 1: protocol ip prio 1 u32 match ip dst %s/32" % (dev, ip),
        "tc class del dev %s classid 1:%d" % (dev, class_id(ip)),
    ]


class Throttler:
    def __init__(self, live=False):
        self.live = live
        self.caps = {}
        self.history = []
        if live:
            dev = config.INTERFACE
            self.run("tc qdisc del dev %s root" % dev)
            self.run("tc qdisc add dev %s root handle 1: htb default 1" % dev)
            self.run("tc class add dev %s parent 1: classid 1:1 htb rate 1000mbit" % dev)

    def run(self, command):
        self.history.append(command)
        self.history = self.history[-20:]
        if self.live:
            subprocess.run(command.split(), capture_output=True)

    def limit(self, mac, ip, speed):
        for c in limit_commands(ip, speed):
            self.run(c)
        self.caps[mac] = speed

    def release(self, mac, ip):
        for c in remove_commands(ip):
            self.run(c)
        self.caps.pop(mac, None)
