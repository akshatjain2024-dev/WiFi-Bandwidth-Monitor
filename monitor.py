import csv
import os
import random
import threading
import time

import config
import dataset


class SimulatedMonitor:
    def __init__(self, path=None, start_minute=None):
        path = path or config.DATASET_FILE
        if not os.path.exists(path):
            dataset.generate(path)
        self.devices = []
        self.data = {}
        with open(path) as f:
            for row in csv.DictReader(f):
                mac = row["mac"]
                if mac not in self.data:
                    self.data[mac] = []
                    self.devices.append({"mac": mac, "ip": row["ip"], "name": row["name"], "type": row["type"]})
                self.data[mac].append(float(row["mbps"]))
        self.minute = config.START_MINUTE if start_minute is None else start_minute
        self.spikes = {}
        self.lock = threading.Lock()

    def sim_time(self):
        m = self.minute % 1440
        return "%02d:%02d" % (m // 60, m % 60)

    def add_spike(self, mac, level=None, seconds=40):
        if mac not in self.data:
            return False
        with self.lock:
            self.spikes[mac] = (time.time() + seconds, level or random.uniform(40, 65))
        return True

    def read(self, caps):
        readings = {}
        now = time.time()
        with self.lock:
            index = self.minute % 1440
            for d in self.devices:
                mac = d["mac"]
                value = self.data[mac][index]
                if mac in self.spikes:
                    end, level = self.spikes[mac]
                    if now < end:
                        value = level * random.uniform(0.9, 1.1)
                    else:
                        del self.spikes[mac]
                if mac in caps:
                    value = min(value, caps[mac] * random.uniform(0.9, 1.0))
                readings[mac] = round(value, 2)
            self.minute += 1
        return readings


class LiveMonitor:
    def __init__(self):
        from scapy.all import ARP, Ether, sniff, srp
        self.ARP = ARP
        self.Ether = Ether
        self.srp = srp
        self.sniff = sniff
        self.devices = []
        self.byte_count = {}
        self.last_read = time.time()
        self.lock = threading.Lock()
        self.scan()
        threading.Thread(target=self.capture, daemon=True).start()

    def scan(self):
        packet = self.Ether(dst="ff:ff:ff:ff:ff:ff") / self.ARP(pdst=config.SUBNET)
        answered, _ = self.srp(packet, timeout=2, iface=config.INTERFACE, verbose=False)
        for _, reply in answered:
            self.devices.append({"mac": reply.hwsrc.upper(), "ip": reply.psrc, "name": reply.psrc, "type": "device"})

    def capture(self):
        macs = {d["mac"] for d in self.devices}

        def count(pkt):
            if self.Ether in pkt:
                for mac in (pkt[self.Ether].src.upper(), pkt[self.Ether].dst.upper()):
                    if mac in macs:
                        with self.lock:
                            self.byte_count[mac] = self.byte_count.get(mac, 0) + len(pkt)

        self.sniff(iface=config.INTERFACE, prn=count, store=False)

    def sim_time(self):
        return time.strftime("%H:%M")

    def add_spike(self, mac, level=None, seconds=40):
        return False

    def read(self, caps):
        now = time.time()
        with self.lock:
            seconds = max(now - self.last_read, 0.001)
            readings = {d["mac"]: round(self.byte_count.get(d["mac"], 0) * 8 / seconds / 1000000, 2) for d in self.devices}
            self.byte_count = {}
            self.last_read = now
        return readings
