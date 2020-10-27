# -*- coding: utf-8 -*-
import datetime


class SupercomputadorRack:
    nos = []
    rack = None

    def __init__(self, rack):
        self.nos = []
        self.rack = rack

    def add_no(self, nos_novo):
        self.nos.append(nos_novo)

    def __str__(self):
        return self.rack


class SupercomputadorNode:
    status = tempo = chassis = size = slot = 0
    usuario = posicao = comando = rack = None
    classe_html = {
        "-": "free_batch",
        "--": "free_batch",
        "S": "service",
        "SS": "service",
        ";": "free_batch",
        ";;": "free_batch",
        "A": "allocated_interactive",
        "AA": "allocated_interactive",
        "W": "waiting",
        "WW": "waiting",
        "X": "down",
        "XX": "down",
        "Y": "down",
        "YY": "down",
        "?": "suspect",
        "??": "suspect",
        "Z": "service",
        "ZZ": "service",
        " ": "noexist",
        "  ": "noexist",
    }

    def get_classe_html(self):
        if str(self.status) in self.classe_html:
            return self.classe_html[self.status]
        return "processing"

    def __init__(self, dict_data):
        for key, value in dict_data.items():
            setattr(self, key, value)

    def __str__(self):
        return f"{str(self.chassis)}:{str(self.slot)}:{str(self.posicao)}"


class SupercomputadorHistorico:

    update = jobs = service = free_batch = admindown = waiting = free = down = running = suspect = noexist = allocated_interactive = 0

    def get_services(self):
        return self.service + self.admindown + self.suspect

    def get_downs(self):
        return self.down

    def get_used(self):
        return self.running + self.allocated_interactive + self.waiting + self.service

    def get_frees(self):
        return self.free + self.free_batch

    def get_total(self):
        return self.get_services() + self.get_downs() + self.get_used() + self.get_frees()

    def get_used_percent(self):
        if self.get_total() == 0:
            return 0
        return (self.get_used() * 100) / self.get_total()

    def get_down_percent(self):
        if self.get_total() == 0:
            return 0
        return (self.get_downs() * 100) / self.get_total()

    def get_last(self):
        return datetime.datetime.fromtimestamp(self.update).strftime("%d/%m %H:%M")

    def get_alerta(self):
        comand_erro = self.jobs + self.service + self.free_batch + self.admindown + self.waiting + self.free + self.down + self.running + self.suspect + self.noexist + self.allocated_interactive
        if (self.get_downs()) > 0 or (comand_erro == 0):
            return ["lighten-3", "grey", "red"]
        return ["darken-4", "", "brown"]

    def get_alerta_time(self):
        limit_time = datetime.datetime.now() - datetime.timedelta(minutes=10)
        if datetime.datetime.fromtimestamp(self.update) < limit_time:
            return "alert_time red"
        return "blue"

    def get_ok(self):
        limit_time = datetime.datetime.now() - datetime.timedelta(minutes=10)
        comand_erro = self.jobs + self.service + self.free_batch + self.admindown + self.waiting + self.free + self.down + self.running + self.suspect + self.noexist + self.allocated_interactive
        if (comand_erro == 0) or (datetime.datetime.fromtimestamp(self.update) < limit_time):
            return False
        else:
            return True

    def __init__(self, dict_data):
        for key, value in dict_data.items():
            setattr(self, key, value)
