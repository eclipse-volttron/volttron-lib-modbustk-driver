"""Unit tests for volttron-lib-modbustk-driver."""

from volttron.driver.interfaces.modbustk.modbustk import BaseInterface, ModbusTK


def test_driver():
    driver = ModbusTK()
    assert isinstance(driver, BaseInterface)
