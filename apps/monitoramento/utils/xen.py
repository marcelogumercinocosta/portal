import configparser
import time
from datetime import datetime
from django.conf import settings
from XenAPI import Failure, Session


class Pool:
    hosts = []
    total_vms = 0

    def __init__(self, name):
        self.hosts = []
        self.name = name
        self.inicio = time.time()
        self.update = datetime.now()

    def add_host(self, host):
        self.total_vms += host.count_vms()
        self.hosts.append(host)

    def tempo(self):
        return time.time() - self.inicio

    def count_host(self):
        return len(self.hosts)

    def count_vms(self):
        return self.total_vms


class Host:
    vms = []

    def __init__(self, object_host, metric):
        self.vms = []
        self.nome = object_host["hostname"]
        self.uid = object_host["uuid"]
        self.address = object_host["address"]
        self.system_manufacturer = object_host["bios_strings"]["system-manufacturer"]
        self.system_product_name = object_host["bios_strings"]["system-product-name"]
        self.software_version = object_host["software_version"]
        self.cpu_count = object_host["cpu_info"]["cpu_count"]
        self.modelname = object_host["cpu_info"]["modelname"]
        self.start_time = datetime.fromtimestamp(int(object_host["other_config"]["boot_time"].replace('.', '')))
        self.memory_total = int(metric["memory_total"])
        self.memory_free = int(metric["memory_free"])
        self.load = 0
        self.cpus = 0


    def get_memory(self):
        return int(100 - (self.memory_free * 100) / self.memory_total)

    def get_memory_total(self):
        return str(self.memory_total / 1024 / 1024 / 1024)

    def get_memory_used(self):
        return str(int((self.memory_total - self.memory_free) / 1024 / 1024 / 1024))

    def add_vms(self, vm):
        self.vms.append(vm)

    def set_cpus(self, cpu):
        self.cpus = len(cpu)

    def count_vms(self):
        return len(self.vms)
    
    def get_uptime(self):
        return (datetime.now() - self.start_time).days


class Vm:
    vdis = []

    def __init__(self, object_data, metrics):
        self.vdis = []
        self.nome = object_data["name_label"]
        self.uid = object_data["uuid"]
        self.name_description = object_data["name_description"]
        self.VCPUs_number = metrics["VCPUs_number"]
        self.memory_total = float(metrics["memory_actual"])
        self.start_time = datetime.strptime(metrics["start_time"].value, "%Y%m%dT%H:%M:%SZ")
        self.networks = ""
        self.software_version = None
        self.memory_free = 0
        self.load = 0
        self.vmNetOut = 0
        self.vmNetIn = 0
        self.vmWrite = 0
        self.vmRead = 0

    def set_guest_metric(self, guest_metric):
        if guest_metric["os_version"]:
            self.software_version = guest_metric["os_version"]["name"]
        else:
            self.software_version = ""

        for key in guest_metric["networks"]:
            if "/" in key[-3]:
                if self.networks == "":
                    self.networks = guest_metric["networks"][key]
                else:
                    self.networks = self.networks + " / " + guest_metric["networks"][key]
    
    def get_uptime(self):
        return (datetime.now() - self.start_time).days

    def add_vdis(self, vdi):
        self.vdis.append(vdi)


class VDI:
    def __init__(self, vdi, sr):
        self.nome = vdi["name_label"]
        self.uuid = vdi["uuid"]
        self.virtual_size = float(vdi["virtual_size"]) 
        self.is_a_snapshot = vdi["is_a_snapshot"]
        self.type = vdi["type"]
        self.sr_uuid = sr["uuid"]
        self.sr_nome = sr["name_label"]
        self.sr_name_description = sr["name_description"]


class XenInfo:
    def __init__(self, ambiente, servidores):
        self.pool = Pool(ambiente)
        self.servers = servidores
        self.server = self.servers[0]
        self.user = settings.XEN_AUTH_USER
        self.password = settings.XEN_AUTH_PASSWORD
        self.session = None

    # Login
    def login(self):
        try:
            self.session = Session(f"http://{self.server}.cptec.inpe.br")
            self.session.xenapi.login_with_password(self.user, self.password)
        except Failure as err:
            id_server = int(self.servers.index(self.server)) + 1
            if id_server < len(self.servers):
                if err.details[0] == "HOST_IS_SLAVE":
                    self.session = Session("http://" + err.details[1])
                    self.server = self.servers[id_server ]
                    self.login()
            else:
                raise Failure( f"Failure error: {err}")
        except OSError as err:
            raise OSError(1, f"OS error: {err}")

    # Obtendo informacoes sobre o Pool
    def set_pool(self):
        pool = self.session.xenapi.pool.get_all()[0]
        master = self.session.xenapi.pool.get_master(pool)
        self.pool.nome = self.session.xenapi.pool.get_name_label(pool)
        self.pool.uid = self.session.xenapi.pool.get_uuid(pool)[0]

    # Obtendo informacoes sobre os Hipervisor e VMs
    def set_gerar(self):
        # Consulta todos os Hosts
        for host in self.session.xenapi.host.get_all():
            # Consulta Metricas do Host
            metric_host = self.session.xenapi.host_metrics.get_record(self.session.xenapi.host.get_metrics(host))
            # Instancia Host
            new_host = Host(self.session.xenapi.host.get_record(host), metric_host)
            # Processa rrd_updates do host
            new_host.set_cpus(self.session.xenapi.host.get_host_CPUs(host))
            # consulta as VMs do Host
            for VM in self.session.xenapi.host.get_resident_VMs(host):
                # Consulta Metricas da VM
                metric_vm = self.session.xenapi.VM_metrics.get_record(self.session.xenapi.VM.get_metrics(VM))
                # Instancia a VM
                new_vm = Vm(self.session.xenapi.VM.get_record(VM), metric_vm)
                # retira o Control domain on host
                if "Control domain on host" not in new_vm.nome:
                    # Consulta Metricas do Guest VM
                    guest_metric_vm = self.session.xenapi.VM_guest_metrics.get_record(self.session.xenapi.VM.get_guest_metrics(VM))
                    new_vm.set_guest_metric(guest_metric_vm)
                    # Consulta VBD,VDI e SR
                    for VBD in self.session.xenapi.VM.get_VBDs(VM):
                        vdi = self.session.xenapi.VBD.get_VDI(VBD)
                        if vdi != "OpaqueRef:NULL":
                            new_vdi = VDI(self.session.xenapi.VDI.get_record(vdi), self.session.xenapi.SR.get_record(self.session.xenapi.VDI.get_SR(vdi)))
                            new_vm.add_vdis(new_vdi)
                    new_host.add_vms(new_vm)
            self.pool.add_host(new_host)
        self.session.xenapi.logout()

    def carregar(self):
        self.login()
        self.set_pool()
        self.set_gerar()
        return self.pool
