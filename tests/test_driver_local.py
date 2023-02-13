import gevent
import json
import logging
import pytest
import socket

from random import randint
from struct import pack, unpack

from volttron.client.known_identities import CONFIGURATION_STORE, PLATFORM_DRIVER
from volttron.utils import setup_logging
from volttrontesting.platformwrapper import PlatformWrapper

from volttron.driver.interfaces.modbus_tk.utils import helpers
from volttron.driver.interfaces.modbus_tk.utils.client import Client, Field
from volttron.driver.interfaces.modbus_tk.utils.server import Server

setup_logging()
logger = logging.getLogger(__name__)


def get_rand_ip_and_port():

    def is_port_open(ip, port):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex((ip, port))
        return result == 0

    def get_rand_port(ip=None, min_ip=5000, max_ip=6000):
        port = randint(min_ip, max_ip)
        if ip:
            while is_port_open(ip, port):
                port = randint(min_ip, max_ip)
        return port

    ip = "127.0.0.{}".format(randint(1, 254))
    port = get_rand_port(ip)
    return ip + ":{}".format(port)


IP, _port = get_rand_ip_and_port().split(":")
PORT = int(_port)

# Register values dictionary for testing set_point and get_point
REGISTERS_DICT = {
    "BigUShort": 2**16 - 1,
    "BigUInt": 2**32 - 1,
    "BigULong": 2**64 - 1,
    "BigShort": -(2**16) // 2,
    "BigInt": -(2**32) // 2,
    "BigFloat": -1234.0,
    "BigLong": -(2**64) // 2,
    "LittleUShort": 0,
    "LittleUInt": 0,
    "LittleULong": 0,
    "LittleShort": (2**16) // 2 - 1,
    "LittleInt": (2**32) // 2 - 1,
    "LittleFloat": 1.0,
    "LittleLong": (2**64) // 2 - 1
}

REGISTRY_CONFIG = [{"Volttron Point Name": "BigUShort", "Units": "PPM", "Modbus Register": ">H", "Writable": "TRUE",
                    "Point Address": "0"},
                   {"Volttron Point Name": "BigUInt", "Units": "PPM", "Modbus Register": ">I", "Writable": "TRUE",
                    "Point Address": "1"},
                   {"Volttron Point Name": "BigULong", "Units": "PPM", "Modbus Register": ">Q", "Writable": "TRUE",
                    "Point Address": "3"},
                   {"Volttron Point Name": "BigShort", "Units": "PPM", "Modbus Register": ">h", "Writable": "TRUE",
                    "Point Address": "7"},
                   {"Volttron Point Name": "BigInt", "Units": "PPM", "Modbus Register": ">i", "Writable": "TRUE",
                    "Point Address": "8"},
                   {"Volttron Point Name": "BigFloat", "Units": "PPM", "Modbus Register": ">f", "Writable": "TRUE",
                    "Point Address": "10"},
                   {"Volttron Point Name": "BigLong", "Units": "PPM", "Modbus Register": ">q", "Writable": "TRUE",
                    "Point Address": "12"},
                   {"Volttron Point Name": "LittleUShort", "Units": "PPM", "Modbus Register": "<H",
                    "Writable": "TRUE", "Point Address": "100"},
                   {"Volttron Point Name": "LittleUInt", "Units": "PPM", "Modbus Register": "<I",
                    "Writable": "TRUE", "Point Address": "101"},
                   {"Volttron Point Name": "LittleULong", "Units": "PPM", "Modbus Register": "<Q",
                    "Writable": "TRUE", "Point Address": "103"},
                   {"Volttron Point Name": "LittleShort", "Units": "PPM", "Modbus Register": "<h",
                    "Writable": "TRUE", "Point Address": "107"},
                   {"Volttron Point Name": "LittleInt", "Units": "PPM", "Modbus Register": "<i", "Writable": "TRUE",
                    "Point Address": "108"},
                   {"Volttron Point Name": "LittleFloat", "Units": "PPM", "Modbus Register": "<f",
                    "Writable": "TRUE", "Point Address": "110"},
                   {"Volttron Point Name": "LittleLong", "Units": "PPM", "Modbus Register": "<q",
                    "Writable": "TRUE", "Point Address": "112"}]

DRIVER_CONFIG = {
    "driver_config": {
        "device_address": IP,
        "port": PORT,
        "slave_id": 1
    },
    "driver_type": "modbus_tk",
    "registry_config": "config://modbus.csv",
    "interval": 120,
    "timezone": "UTC"
}


@pytest.fixture(scope="module")
def publish_agent(volttron_instance: PlatformWrapper):
    assert volttron_instance.is_running()
    vi = volttron_instance
    assert vi is not None
    assert vi.is_running()

    # install platform driver
    config = {
        "driver_scrape_interval": 0.05,
        "publish_breadth_first_all": "false",
        "publish_depth_first": "false",
        "publish_breadth_first": "false"
    }
    puid = vi.install_agent(agent_dir="volttron-platform-driver",
                            config_file=config,
                            start=False,
                            vip_identity=PLATFORM_DRIVER)
    assert puid is not None
    gevent.sleep(1)
    assert vi.start_agent(puid)
    assert vi.is_agent_running(puid)

    # create the publish agent
    publish_agent = volttron_instance.build_agent()
    assert publish_agent.core.identity
    gevent.sleep(1)

    capabilities = {"edit_config_store": {"identity": PLATFORM_DRIVER}}
    volttron_instance.add_capabilities(publish_agent.core.publickey, capabilities)
    gevent.sleep(1)

    # Add Modbus Driver to Platform Driver
    # This registry configuration contains only required fields
    publish_agent.vip.rpc.call(CONFIGURATION_STORE,
                               "manage_store",
                               PLATFORM_DRIVER,
                               "modbus.csv",
                               json.dumps(REGISTRY_CONFIG),
                               config_type="json").get(timeout=10)

    publish_agent.vip.rpc.call(CONFIGURATION_STORE,
                               "manage_store",
                               PLATFORM_DRIVER,
                               "devices/modbus",
                               json.dumps(DRIVER_CONFIG),
                               config_type='json').get(timeout=10)

    yield publish_agent

    volttron_instance.stop_agent(puid)
    publish_agent.core.stop()


class PPSPi32Client(Client):
    """
    Define some registers to PPSPi32Client
    """

    def __init__(self, *args, **kwargs):
        super(PPSPi32Client, self).__init__(*args, **kwargs)

    byte_order = helpers.BIG_ENDIAN
    addressing = helpers.ADDRESS_OFFSET

    BigUShort = Field("BigUShort", 0, helpers.USHORT, 'PPM', 2, helpers.no_op,
                      helpers.REGISTER_READ_WRITE, helpers.OP_MODE_READ_WRITE)
    BigUInt = Field("BigUInt", 1, helpers.UINT, 'PPM', 2, helpers.no_op,
                    helpers.REGISTER_READ_WRITE, helpers.OP_MODE_READ_WRITE)
    BigULong = Field("BigULong", 3, helpers.UINT64, 'PPM', 2, helpers.no_op,
                     helpers.REGISTER_READ_WRITE, helpers.OP_MODE_READ_WRITE)
    BigShort = Field("BigShort", 7, helpers.SHORT, 'PPM', 2, helpers.no_op,
                     helpers.REGISTER_READ_WRITE, helpers.OP_MODE_READ_WRITE)
    BigInt = Field("BigInt", 8, helpers.INT, 'PPM', 2, helpers.no_op, helpers.REGISTER_READ_WRITE,
                   helpers.OP_MODE_READ_WRITE)
    BigFloat = Field("BigFloat", 10, helpers.FLOAT, 'PPM', 2, helpers.no_op,
                     helpers.REGISTER_READ_WRITE, helpers.OP_MODE_READ_WRITE)
    BigLong = Field("BigLong", 12, helpers.INT64, 'PPM', 2, helpers.no_op,
                    helpers.REGISTER_READ_WRITE, helpers.OP_MODE_READ_WRITE)
    LittleUShort = Field("LittleUShort", 100, helpers.USHORT, 'PPM', 2, helpers.no_op,
                         helpers.REGISTER_READ_WRITE, helpers.OP_MODE_READ_WRITE)
    LittleUInt = Field("LittleUInt", 101, helpers.UINT, 'PPM', 2, helpers.no_op,
                       helpers.REGISTER_READ_WRITE, helpers.OP_MODE_READ_WRITE)
    LittleULong = Field("LittleULong", 103, helpers.UINT64, 'PPM', 2, helpers.no_op,
                        helpers.REGISTER_READ_WRITE, helpers.OP_MODE_READ_WRITE)
    LittleShort = Field("LittleShort", 107, helpers.SHORT, 'PPM', 2, helpers.no_op,
                        helpers.REGISTER_READ_WRITE, helpers.OP_MODE_READ_WRITE)
    LittleInt = Field("LittleInt", 108, helpers.INT, 'PPM', 2, helpers.no_op,
                      helpers.REGISTER_READ_WRITE, helpers.OP_MODE_READ_WRITE)
    LittleFloat = Field("LittleFloat", 110, helpers.FLOAT, 'PPM', 2, helpers.no_op,
                        helpers.REGISTER_READ_WRITE, helpers.OP_MODE_READ_WRITE)
    LittleLong = Field("LittleLong", 112, helpers.INT64, 'PPM', 2, helpers.no_op,
                       helpers.REGISTER_READ_WRITE, helpers.OP_MODE_READ_WRITE)


@pytest.fixture
def modbus_server():
    modbus_server = Server(address=IP, port=PORT)
    modbus_server.define_slave(1, PPSPi32Client, unsigned=True)

    # Set values for registers from server as the default values
    modbus_server.set_values(1, PPSPi32Client().field_by_name("BigUShort"), 0)
    modbus_server.set_values(1, PPSPi32Client().field_by_name("BigUInt"), 0)
    modbus_server.set_values(1, PPSPi32Client().field_by_name("BigULong"), 0)
    modbus_server.set_values(1, PPSPi32Client().field_by_name("BigShort"), 0)
    modbus_server.set_values(1, PPSPi32Client().field_by_name("BigInt"), 0)
    modbus_server.set_values(1, PPSPi32Client().field_by_name("BigFloat"), 0)
    modbus_server.set_values(1, PPSPi32Client().field_by_name("BigLong"), 0)
    modbus_server.set_values(1,
                             PPSPi32Client().field_by_name("LittleUShort"),
                             unpack('<H', pack('>H', 0)))
    modbus_server.set_values(1,
                             PPSPi32Client().field_by_name("LittleUInt"),
                             unpack('<HH', pack('>I', 0)))
    modbus_server.set_values(1,
                             PPSPi32Client().field_by_name("LittleULong"),
                             unpack('<HHHH', pack('>Q', 0)))
    modbus_server.set_values(1,
                             PPSPi32Client().field_by_name("LittleShort"),
                             unpack('<H', pack('>h', 0)))
    modbus_server.set_values(1,
                             PPSPi32Client().field_by_name("LittleInt"),
                             unpack('<HH', pack('>i', 0)))
    modbus_server.set_values(1,
                             PPSPi32Client().field_by_name("LittleFloat"),
                             unpack('<HH', pack('>f', 0)))
    modbus_server.set_values(1,
                             PPSPi32Client().field_by_name("LittleLong"),
                             unpack('<HHHH', pack('>q', 0)))

    modbus_server.start()
    gevent.sleep(10)
    yield modbus_server
    modbus_server.stop()


def test_default_values(modbus_server, publish_agent):
    """
    By default server setting, all registers values are 0
    """
    default_values = publish_agent.vip.rpc.call(PLATFORM_DRIVER, 'scrape_all',
                                                'modbus').get(timeout=10)
    assert type(default_values) is dict

    for key in default_values.keys():
        assert default_values[key] == 0 or 0.0


def test_set_point(modbus_server, publish_agent):
    for key in REGISTERS_DICT.keys():
        publish_agent.vip.rpc.call(PLATFORM_DRIVER, 'set_point', 'modbus', key,
                                   REGISTERS_DICT[key]).get(timeout=20)
        gevent.sleep(5)
        assert publish_agent.vip.rpc.call(PLATFORM_DRIVER, 'get_point', 'modbus',
                                   key).get(timeout=20) == REGISTERS_DICT[key]
        gevent.sleep(5)

    assert publish_agent.vip.rpc.call(PLATFORM_DRIVER, 'scrape_all',
                                      'modbus').get(timeout=20) == REGISTERS_DICT
