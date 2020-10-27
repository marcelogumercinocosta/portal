import datetime

import pytest
from mixer.backend.django import mixer

from xmlrpc.server import SimpleXMLRPCServer
import xmlrpc.client
from apps.monitoramento.utils import VDI, Vm, Host, Pool, XenInfo
from apps.infra.models import AmbienteVirtual, Servidor
from django.conf import settings
import errno
from XenAPI import Failure, Session


def test_vdi() -> None:
    vdi_input = {"name_label":"name", "uuid":"12312312dsfdfs", "virtual_size":( 32 * 1024 * 1024 *1024), "is_a_snapshot":"no", "type":"user"}
    sr_input = {"uuid":"123123123", "name_label":"LUN_VMS_X65_DMZ", "name_description":"LUN" }
    vdi = VDI(vdi_input,sr_input)
    assert vdi.get_virtual_size() == "32.00" 


def test_vm() -> None:
    vdi_input = {"name_label":"name", "uuid":"12312312dsfdfs", "virtual_size":( 32 * 1024 * 1024 *1024), "is_a_snapshot":"no", "type":"user"}
    sr_input = {"uuid":"123123123", "name_label":"LUN_VMS_X65_DMZ", "name_description":"LUN" }
    vdi = VDI(vdi_input,sr_input)

    vm_input = {"name_label":"server_name", "uuid":"asdf312dsfdfs", "name_description":"description" }
    metrics_input = {"VCPUs_number": 4, "memory_actual": 64 * 1024 * 1024 }
    vm = Vm(vm_input, metrics_input)
    guest_metric_input = { 'os_version':{}, 'networks': {'0/ip': '', '0/ipv6/0': ''},'last_updated': xmlrpc.client.DateTime('20200306T19:32:29Z')}
    vm.set_guest_metric(guest_metric_input)
    assert vm.software_version == ''

    guest_metric_input = { 'os_version': {'name': 'Ubuntu 16.04.4 LTS'},  'networks': {'0/ip': '192.168.0.1', '1/ip': '192.168.0.2', '0/ipv6/0': 'fe80::40f2:beff:fedd:7244'}, 'last_updated': xmlrpc.client.DateTime('20200306T19:32:29Z')}
    vm = Vm(vm_input, metrics_input)
    vm.set_guest_metric(guest_metric_input)
    assert vm.software_version == 'Ubuntu 16.04.4 LTS'

    vm.add_vdis(vdi) 
    assert len(vm.vdis) == 1

def test_host_pool() -> None:
    object_host_input = {"hostname":"server_host", "uuid": "00000003-00000001", "address": '192.168.0.1', "bios_strings":{"system-manufacturer":'HP',"system-product-name":'ProLiant DL380p Gen8'},"software_version": {'product_version': '7.2.0'},"cpu_info":{ "cpu_count":64,"modelname": 'Intel(R) Xeon(R) CPU E5-2660 0 @ 2.20GHz'}}
    metrics_input =  {'last_updated': xmlrpc.client.DateTime('20200306T19:32:29Z'),"memory_total":f'{ 256 * 1024 * 1024 * 1024}', "memory_free":f'{ 128 * 1024 * 1024 * 1024}'}
    host = Host(object_host_input, metrics_input)
    cpus = ['OpaqueRef:fc75bc2f-5e87-0a14-afcf-6fd8ed7cd987', 'OpaqueRef:f5918a5e-7f10-3e58-d29f-0181926b1bf2', 'OpaqueRef:e28ba667-3526-beac-68cb-a962c46fd8d3', 'OpaqueRef:e1e664e5-22c6-dc12-1cc1-8470f6762ea0']
    host.set_cpus(cpus) 

    assert host.get_memory() == 50
    assert host.get_memory_total() == '256.0'
    assert host.get_memory_used() == '128'
    assert host.cpus == 4

    vm_input = {"name_label":"server_name", "uuid":"asdf312dsfdfs", "name_description":"description" }
    metrics_input = {"VCPUs_number": 4, "memory_actual": 64 * 1024 * 1024 }
    vm = Vm(vm_input, metrics_input)

    host.add_vms(vm) 
    assert host.count_vms() == 1

    pool = Pool('virtual')
    pool.add_host(host)
    assert pool.count_host() == 1
    assert pool.count_vms() == 1
    assert int(pool.tempo()) <= 20 


@pytest.mark.django_db
def test_xeninfo_error_not_master() -> None:
    ambiente_virtual = mixer.blend(AmbienteVirtual, nome='LAN', virtualizador='XEN', versao='7.0' )
    settings.XEN_AUTH_USER = 'root'
    settings.XEN_AUTH_PASSWORD = '123456'
    servers = [mixer.blend(Servidor, nome='toropy'), mixer.blend(Servidor, nome='toropy')]
    xen = XenInfo(ambiente_virtual, servers)
    with pytest.raises(Failure) as excinfo:
        xen.login()


@pytest.mark.django_db
def test_xeninfo_error_not_servers() -> None:
    ambiente_virtual = mixer.blend(AmbienteVirtual, nome='LAN', virtualizador='XEN', versao='7.0' )
    settings.XEN_AUTH_USER = 'root'
    settings.XEN_AUTH_PASSWORD = '123456'
    servers = [mixer.blend(Servidor, nome='toropay'), mixer.blend(Servidor, nome='toroapy')]
    xen = XenInfo(ambiente_virtual, servers)
    with pytest.raises(OSError) as excinfo:
        xen.login()