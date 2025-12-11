import pytest
from battery import Battery
from unittest.mock import Mock

@pytest.fixture
def fresh_battery():
    # Full charge at start
    return Battery(100)

@pytest.fixture
def partially_charged_battery():
    b = Battery(100)
    b.mCharge = 70
    return b

def describe_battery_core_behavior():

    def it_returns_capacity(fresh_battery):
        assert fresh_battery.getCapacity() == 100

    def it_returns_current_charge(fresh_battery):
        assert fresh_battery.getCharge() == 100

    # Recharge behavior (no monitor involvement assertions here)
    def it_recharge_increases_charge_until_capacity(partially_charged_battery):
        ok = partially_charged_battery.recharge(20)  # 70 + 20 = 90
        assert ok is True
        assert partially_charged_battery.getCharge() == 90

    def it_recharge_clamps_at_capacity(partially_charged_battery):
        ok = partially_charged_battery.recharge(50)  # 70 + 50 = 120 -> clamp to 100
        assert ok is True
        assert partially_charged_battery.getCharge() == 100

    def it_recharge_fails_when_amount_not_positive(fresh_battery):
        ok = fresh_battery.recharge(0)
        assert ok is False
        assert fresh_battery.getCharge() == 100

    def it_recharge_fails_when_already_full(fresh_battery):
        ok = fresh_battery.recharge(10)
        assert ok is False
        assert fresh_battery.getCharge() == 100

    # Drain behavior (state only)
    def it_drain_decreases_charge_until_zero(partially_charged_battery):
        ok = partially_charged_battery.drain(20)  # 70 - 20 = 50
        assert ok is True
        assert partially_charged_battery.getCharge() == 50

    def it_drain_clamps_at_zero(partially_charged_battery):
        ok = partially_charged_battery.drain(100)  # 70 - 100 = -30 -> clamp to 0
        assert ok is True
        assert partially_charged_battery.getCharge() == 0

    def it_drain_fails_when_amount_not_positive(partially_charged_battery):
        ok = partially_charged_battery.drain(0)
        assert ok is False
        assert partially_charged_battery.getCharge() == 70

    def it_drain_fails_when_empty():
        b = Battery(100)
        b.mCharge = 0
        ok = b.drain(10)
        assert ok is False
        assert b.getCharge() == 0

def describe_battery_external_monitor_interactions():

    def it_calls_monitor_on_recharge(partially_charged_battery):
        mock_monitor = Mock()
        partially_charged_battery.external_monitor = mock_monitor

        partially_charged_battery.recharge(20)  # 70 -> 90

        mock_monitor.notify_recharge.assert_called_once_with(90)

    def it_calls_monitor_on_drain(partially_charged_battery):
        mock_monitor = Mock()
        partially_charged_battery.external_monitor = mock_monitor

        partially_charged_battery.drain(30)  # 70 -> 40

        mock_monitor.notify_drain.assert_called_once_with(40)

    def it_does_not_call_monitor_when_recharge_fails(partially_charged_battery):
        mock_monitor = Mock()
        partially_charged_battery.external_monitor = mock_monitor

        partially_charged_battery.recharge(0)  # failure path

        mock_monitor.notify_recharge.assert_not_called()

    def it_does_not_call_monitor_when_drain_fails(partially_charged_battery):
        mock_monitor = Mock()
        partially_charged_battery.external_monitor = mock_monitor

        partially_charged_battery.drain(0)  # failure path

        mock_monitor.notify_drain.assert_not_called()

    def it_handles_no_monitor_safely_on_recharge(partially_charged_battery):
        partially_charged_battery.external_monitor = None
        ok = partially_charged_battery.recharge(10)  # 70 -> 80
        assert ok is True
        assert partially_charged_battery.getCharge() == 80  # no exception

    def it_handles_no_monitor_safely_on_drain(partially_charged_battery):
        partially_charged_battery.external_monitor = None
        ok = partially_charged_battery.drain(10)  # 70 -> 60
        assert ok is True
        assert partially_charged_battery.getCharge() == 60  # no exception

def describe_battery_with_stubbed_monitor_behavior():
    """
    Demonstrate a stub: define simple methods to accept calls without side effects.
    Useful if later Battery branches on monitor responses (e.g., returning booleans).
    """

    class StubMonitor:
        def __init__(self):
            self.recharge_calls = []
            self.drain_calls = []

        def notify_recharge(self, charge):
            # Pretend to do something; record the call
            self.recharge_calls.append(charge)
            return True  # forced outcome

        def notify_drain(self, charge):
            self.drain_calls.append(charge)
            return True  # forced outcome

    def it_works_with_stub_monitor_on_recharge(partially_charged_battery):
        stub = StubMonitor()
        partially_charged_battery.external_monitor = stub

        ok = partially_charged_battery.recharge(25)  # 70 -> 95
        assert ok is True
        assert partially_charged_battery.getCharge() == 95
        assert stub.recharge_calls == [95]

    def it_works_with_stub_monitor_on_drain(partially_charged_battery):
        stub = StubMonitor()
        partially_charged_battery.external_monitor = stub

        ok = partially_charged_battery.drain(35)  # 70 -> 35
        assert ok is True
        assert partially_charged_battery.getCharge() == 35
        assert stub.drain_calls == [35]

def test_drain_with_monitor_patch(mocker):
    # Create a mock monitor and patch its notify_drain method
    mock_monitor = mocker.Mock()
    b = Battery(100, external_monitor=mock_monitor)
    b.mCharge = 50

    # Patch the notify_drain method on this mock
    mock_monitor.notify_drain = mocker.Mock()

    b.drain(20)  # should call notify_drain with 30

    mock_monitor.notify_drain.assert_called_once_with(30)
