# volttron-lib-modbustk-driver

![Passing?](https://github.com/VOLTTRON/volttron-lib-modbustk-driver/actions/workflows/run-tests.yml/badge.svg)
[![pypi version](https://img.shields.io/pypi/v/volttron-lib-modbustk-driver.svg)](https://pypi.org/project/volttron-lib-modbustk-driver/)

VOLTTRON’s Modbus-TK driver, built on the Python Modbus-TK library, is an alternative to the original VOLTTRON modbus driver. Unlike the original modbus driver, the Modbus-TK driver supports Modbus RTU as well as Modbus over TCP/IP.

# Prerequisites

* Python 3.8

# Installation

1. Create and activate a virtual environment.

    ```shell
    python -m venv env
    source env/bin/activate
    ```

1. Install volttron and start the platform.

    ```shell
    pip install volttron

    # Start platform with output going to volttron.log
    volttron -vv -l volttron.log &
    ```

1. Install the volttron platform driver:

    ```shell
    vctl install volttron-platform-driver --vip-identity platform.driver --start
    ```

1. Install the volttron-lib-modbustk-driver library.

    ```shell
    pip install volttron-lib-modbustk-driver
    ```

1. Install the driver onto the Platform Driver.

    Installing a driver in the Platform Driver Agent requires adding copies of the device configuration and registry configuration files to the Platform Driver’s configuration store.

    Create a config directory and navigate to it:

    ```shell
    mkdir config
    cd config
    ```

1. Add driver configurations to the Platform Driver.

   The Modbus-TK driver is mostly backward-compatible with the parameter definitions in the original Modbus driver’s configuration (.config and .csv files). If the config file’s parameter names use the Modbus driver’s name conventions, they are translated to the Modbus-TK name conventions, e.g. a Modbus CSV file’s Point Address is interpreted as a Modbus-TK “Address”. Backward-compatibility exceptions are:

        * If the config file has no port, the default is 0, not 502.

        * If the config file has no slave_id, the default is 1, not 0.

    The driver_config section of a Modbus-TK device configuration file supports a variety of parameter definitions, but only *device_address* is required:

    * device_address (Required):  IP Address of the device.

    * name (Optional) - Name of the device. Defaults to “UNKNOWN”.

    * device_type (Optional) - Name of the device type. Defaults to “UNKNOWN”.

    * port (Optional) - Port the device is listening on. Defaults to 0 (no port). Use port 0 for RTU transport.

    * slave_id (Optional) - Slave ID of the device. Defaults to 1. Use ID 0 for no slave.

    * baudrate (Optional) - Serial (RTU) baud rate. Defaults to 9600.

    * bytesize (Optional) - Serial (RTU) byte size: 5, 6, 7, or 8. Defaults to 8.

    * parity (Optional) - Serial (RTU) parity: none, even, odd, mark, or space. Defaults to None.

    * stopbits (Optional) - Serial (RTU) stop bits: 1, 1.5, or 2. Defaults to 1.

    * xonxoff (Optional) - Serial (RTU) flow control: 0 or 1. Defaults to 0.

    * addressing (Optional) - Data address table: offset, offset_plus, or address. Defaults to offset.

      * address: The exact value of the address without any offset value.

      * offset: The value of the address plus the offset value.

      * offset_plus: The value of the address plus the offset value plus one.

      * : If an offset value is to be added, it is determined based on a point’s properties in the CSV file:

        * Type=bool, Writable=TRUE: 0

        * Type=bool, Writable=FALSE: 10000

        * Type!=bool, Writable=TRUE: 30000

        * Type!=bool, Writable=FALSE: 40000

    * endian (Optional) - Byte order: big or little. Defaults to big.

    * write_multiple_registers (Optional) - Write multiple coils or registers at a time. Defaults to true.

      * If write_multiple_registers is set to false, only register types unsigned short (uint16) and boolean (bool) are supported. The exception raised during the configure process.

    * register_map (Optional) - Register map csv of unchanged register variables. Defaults to registry_config csv.

    This repo provides an example configuration in the file "modbus_tk_example.config".

    Here is an example device configuration file:

    ```json
        {
        "driver_config": {
            "device_address": "10.1.1.2",
            "port": "5020",
            "register_map": "config://modbus_tk_test_map.csv"
        },
        "driver_type": "modbus_tk",
        "registry_config": "config://modbus_tk_test.csv",
        "interval": 60,
        "timezone": "UTC",
        "heart_beat_point": "heartbeat"
        }
    ```

    After creating a driver configuration file named "modbus_tk_example.config", add it to the Configuration Store:

    ```shell
    vctl config store platform.driver devices/modbustk modbus_tk_example.config
    ```

1. Add a Modbus-TK Register Map CSV File to the Platform Driver.

    Modbus TK requires an additional registry configuration file compared to the paradigm of most other drivers. The registry map file is an analogue to the typical registry configuration file. The registry configuration file is a simple file which maps device point names to user specified point names.

    This repo provides an example configuration in the file "modbus_tk_test_map.csv".

    The registry map file is a CSV file. Each row configures a register definition on the device.

    Register Name (Required) - The field name in the modbus client. This field is distinct and unchangeable.

    Address (Required) - The point’s modbus address. The addressing option in the driver configuration controls whether this is interpreted as an exact address or an offset.

    Type (Required) - The point’s data type: bool, string[length], float, int16, int32, int64, uint16, uint32, or uint64.

    Units (Optional) - Used for metadata when creating point information on a historian. Default is an empty string.

    Writable (Optional) - TRUE/FALSE. Only points for which Writable=TRUE can be updated by a VOLTTRON agent. Default is FALSE.

    Default Value (Optional) - The point’s default value. If it is reverted by an agent, it changes back to this value. If this value is missing, it will revert to the last known value not set by an agent.

    Transform (Optional) - Scaling algorithm: scale(multiplier), scale_int(multiplier), scale_reg(register_name), scale_reg_power10(register_name), scale_decimal_int_signed(multiplier), mod10k(reverse), mod10k64(reverse), mod10k48(reveres) or none. Default is an empty string.

    Table (Optional) - Standard modbus table name defining how information is stored in slave device. There are 4 different tables:

    discrete_output_coils: read/write coil numbers 1-9999

    discrete_input_contacts: read only coil numbers 10001-19999

    analog_input_registers: read only register numbers 30001-39999

    analog_output_holding_registers: read/write register numbers 40001-49999

    If this field is empty, the modbus table will be defined by type and writable fields. By that, when user sets read only for read/write coils/registers or sets read/write for read only coils/registers, it will select wrong table, and therefore raise exception.

    Mixed Endian (Optional) - TRUE/FALSE. If Mixed Endian is set to TRUE, the order of the Modbus registers will be reversed before parsing the value or writing it out to the device. By setting mixed endian, transform must be None (no op). Defaults to FALSE.

    Description (Optional) - Additional information about the point. Default is an empty string.

    Here is a sample Modbus-TK registry map:

    ```csv
    Register Name,Address,Type,Units,Writable,Default Value,Transform,Table
    unsigned_short,0,uint16,None,TRUE,0,scale(10),analog_output_holding_registers
    unsigned_int,1,uint32,None,TRUE,0,scale(10),analog_output_holding_registers
    unsigned_long,3,uint64,None,TRUE,0,scale(10),analog_output_holding_registers
    sample_short,7,int16,None,TRUE,0,scale(10),analog_output_holding_registers
    sample_int,8,int32,None,TRUE,0,scale(10),analog_output_holding_registers
    sample_float,10,float,None,TRUE,0.0,scale(10),analog_output_holding_registers
    sample_long,12,int64,None,TRUE,0,scale(10),analog_output_holding_registers
    sample_bool,16,bool,None,TRUE,False,,analog_output_holding_registers
    sample_str,17,string[12],None,TRUE,hello world!,,analog_output_holding_registers
    ```

    After creating a registry map named "modbus_tk_test_map.csv", add it to the Configuration Store:

    ```shell
    vctl config store platform.driver modbus_tk_test_map.csv modbus_tk_test_map.csv --csv
    ```

1. Add a registry configuration to the PlatformDriver.

    The registry configuration file is a CSV file. Each row configures a point on the device.

        Volttron Point Name (Required) - The name by which the platform and agents refer to the point. For instance, if the Volttron Point Name is HeatCall1, then an agent would use my_campus/building2/hvac1/HeatCall1 to refer to the point when using the RPC interface of the actuator agent.

        Register Name (Required) - The field name in the modbus client. It must be matched with the field name from register_map.

    Any additional columns will override the existed fields from register_map.

    Here is a sample Modbus-TK registry configuration with defined register_map:

    ```csv
    Volttron Point Name,Register Name
    unsigned short,unsigned_short
    unsigned int,unsigned_int
    unsigned long,unsigned_long
    sample short,sample_short
    sample int,sample_int
    sample float,sample_float
    sample long,sample_long
    sample bool,sample_bool
    sample str,sample_str
    ```

    After creating a registry map named "modbus_tk_test.csv", add it to the Configuration Store:

    ```shell
    vctl config store platform.driver modbus_tk_test.csv modbus_tk_test.csv --csv
    ```

1. Observe Data

    To see data being published to the bus, install a [Listener Agent](https://pypi.org/project/volttron-listener/):

    ```
    vctl install volttron-listener --start
    ```

    Once installed, you should see the data being published by viewing the Volttron logs file that was created in step 2.
    To watch the logs, open a separate terminal and run the following command:

    ```
    tail -f <path to folder containing volttron.log>/volttron.log
    ```

# Modbus-TK Config Command Tool

`config_cmd.py` is a command-line tool for creating and maintaining VOLTTRON driver configurations. The tool runs from the command line:

config_cmd.py supports the following commands:

* help - List all commands.

* quit - Quit the command-line tool.

* list_directories - List all setup directories, with an option to edit their paths.


By default, all directories are in this repo at the following folder: volttron/driver/interfaces/modbus_tk/utils/maps.

It is important to use the correct directories when adding/editing device types and driver configs, and when loading configurations into VOLTTRON.

* map_dir: directory in which maps.yaml is stored.

* config_dir: directory in which driver config files are stored.

* csv_dir: directory in which registry config CSV files are stored.

* edit_directories - Add/Edit map directory, driver config directory, and/or CSV config directory. Press <Enter> if no change is needed. Exits if the directory does not exist.

* list_device_type_description - List all device type descriptions in maps.yaml. Option to edit device type descriptions.

* list_all_device_types - List all device type information in maps.yaml. Option to add more device types.

* device_type - List information for a selected device type. Option to select another device type.

* add_device_type - Add a device type to maps.yaml. Option to add more than one device type. Each device type includes its name, CSV file, description, addressing, and endian, as explained in MODBUS-TK Driver Maps. If an invalid value is entered for addressing or endian, the default value is used instead.

*edit_device_type - Edit an existing device type. If an invalid value is entered for addressing or endian, the previous value is left unchanged.

* list_drivers - List all driver config names in config_dir.

* driver_config <driver_name> - Get a driver config from config_dir. Option to select the driver if no driver is found with that name.

* add_driver_config <driver_name> - Add/Edit <config_dir>/<driver name>.config. Option to select the driver if no driver is found with that name. Press <Enter> to exit.

* load_volttron - Load a driver config and CSV into VOLTTRON. Option to add the config or CSV file to config_dir or to csv_dir. VOLTTRON must be running when this command is used.

* delete_volttron_config - Delete a driver config from VOLTTRON. VOLTTRON must be running when this command is used.

* delete_volttron_csv - Delete a registry csv config from VOLTTRON. VOLTTRON must be running when this command is used.

# Development

Please see the following for contributing guidelines [contributing](https://github.com/eclipse-volttron/volttron-core/blob/develop/CONTRIBUTING.md).

Please see the following helpful guide about [developing modular VOLTTRON agents](https://github.com/eclipse-volttron/volttron-core/blob/develop/DEVELOPING_ON_MODULAR.md)


# Disclaimer Notice

This material was prepared as an account of work sponsored by an agency of the
United States Government.  Neither the United States Government nor the United
States Department of Energy, nor Battelle, nor any of their employees, nor any
jurisdiction or organization that has cooperated in the development of these
materials, makes any warranty, express or implied, or assumes any legal
liability or responsibility for the accuracy, completeness, or usefulness or any
information, apparatus, product, software, or process disclosed, or represents
that its use would not infringe privately owned rights.

Reference herein to any specific commercial product, process, or service by
trade name, trademark, manufacturer, or otherwise does not necessarily
constitute or imply its endorsement, recommendation, or favoring by the United
States Government or any agency thereof, or Battelle Memorial Institute. The
views and opinions of authors expressed herein do not necessarily state or
reflect those of the United States Government or any agency thereof.
