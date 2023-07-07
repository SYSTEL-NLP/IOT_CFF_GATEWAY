from .loragw_hal import *
from enum import Enum
from time import sleep

DEFAULT_FREQ_HZ = 868500000
DEFAULT_COM_PATH = b"/dev/ttyACM0\0"
DEFAULT_CHANNEL_MODE = 0
DEFAULT_CLOCK_SOURCE = ClockSources.CLK_SOURCE_RF_CHAIN_0
DEFAULT_COM_TYPE = CommunicationTypes.LGW_COM_USB
DEFAULT_DATA_RATE = DataRates.DR_LORA_SF7
DEFAULT_BANDWIDTH = Bendwidths.BW_125KHZ
DEFAULT_RADIO_TYPE = RadioTypes.LGW_RADIO_TYPE_SX1250

CHANNEL_IF_MODE_0 = [
    -400000,
    -200000,
    0,
    -400000,
    -200000,
    0,
    200000,
    400000,
    -200000
]

CHANNEL_IF_MODE_1 = [
    -400000,
    -400000,
    -400000,
    -400000,
    -400000,
    -400000,
    -400000,
    -400000,
    -400000
]

CHANNEL_RFCHAIN_MODE_0 = [1, 1, 1, 0, 0, 0, 0, 0, 1]

CHANNEL_RFCHAIN_MODE_1 = [0, 0, 0, 0, 0, 0, 0, 0, 0]


class RxPacket():
    def __init__(self, freq_hz=0, freq_offset=0, if_chain=0, status=0, count_us=0,
                 rf_chain=0, modem_id=0, modulation=0, bandwidth=0, datarate=0,
                 coderate=0, rssic=0, rssis=0, snr=0, snr_min=0, snr_max=0, crc=0,
                 size=0, payload=0, ftime_received=0, ftime=0):
        self.freq_hz = freq_hz
        self.freq_offset = freq_offset
        self.if_chain = if_chain
        self.status = status
        self.count_us = count_us
        self.rf_chain = rf_chain
        self.modem_id = modem_id
        self.modulation = modulation
        self.bandwidth = bandwidth
        self.datarate = datarate
        self.coderate = coderate
        self.rssic = rssic
        self.rssis = rssis
        self.snr = snr
        self.snr_min = snr_min
        self.snr_max = snr_max
        self.crc = crc
        self.size = size
        self.payload = payload
        self.ftime_received = ftime_received
        self.ftime = ftime
        self.payload = [payload[j] for j in range(size)]


class SX1303:
    def __init__(self, lorawan_public: bool = True, com_path: bytes = DEFAULT_COM_PATH,
                 clock_source: ClockSources = DEFAULT_CLOCK_SOURCE,
                 com_type: CommunicationTypes = DEFAULT_COM_TYPE) -> None:
        self.board_conf = lgw_conf_board_s(com_path=com_path, lorawan_public=lorawan_public,
                                           clksrc=clock_source.value, com_type=com_type.value)
        self.rx_rf_conf = None
        self.rx_if_conf = None

        # Configure board
        if lgw_board_setconf(byref(self.board_conf)) != LGW_HAL_SUCCESS:
            raise Exception("Can't initialize board, check com type and path")

    def configure_rx_rf_chains(self, enable: bool = True, freq_hz: int = DEFAULT_FREQ_HZ,
                               type: RadioTypes = DEFAULT_RADIO_TYPE, rssi_offset: float = 0,
                               single_input_mode: bool = False, tx_enable: bool = False):
        self.rx_rf_conf = lgw_conf_rxrf_s(enable=enable, freq_hz=freq_hz,
                                          type=type.value, rssi_offset=rssi_offset,
                                          single_input_mode=single_input_mode, tx_enable=tx_enable)
        if lgw_rxrf_setconf(0, byref(self.rx_rf_conf)) != LGW_HAL_SUCCESS:
            raise Exception("Can't set RF chain 0, please check parameters")
        if lgw_rxrf_setconf(1, byref(self.rx_rf_conf)) != LGW_HAL_SUCCESS:
            raise Exception("Can't set RF chain 1, please check parameters")

    def configure_rx_channels(self, datarate: DataRates = DEFAULT_DATA_RATE,
                              bandwidth=DEFAULT_BANDWIDTH):
        for i in range(0, 8):
            channel_mode = DEFAULT_CHANNEL_MODE
            freq_hz = CHANNEL_IF_MODE_0[i] if channel_mode == 0 else CHANNEL_IF_MODE_1[i]
            rf_chain = CHANNEL_RFCHAIN_MODE_0[i] if channel_mode == 0 else CHANNEL_RFCHAIN_MODE_1[i]
            self.rx_if_conf = lgw_conf_rxif_s(enable=True, rf_chain=rf_chain,
                                              freq_hz=freq_hz, datarate=datarate.value)
            if lgw_rxif_setconf(i, byref(self.rx_if_conf)) != LGW_HAL_SUCCESS:
                raise Exception(
                    f"Can't configure channel {i}, please check parameters")

        freq_hz = CHANNEL_IF_MODE_0[8]
        rf_chain = CHANNEL_RFCHAIN_MODE_0[8]
        self.rx_if_conf = lgw_conf_rxif_s(enable=True, rf_chain=rf_chain, freq_hz=freq_hz,
                                          datarate=datarate.value, bandwidth=bandwidth.value)
        if lgw_rxif_setconf(i, byref(self.rx_if_conf)) != LGW_HAL_SUCCESS:
            raise Exception(
                "Can't configure channel 8, please check parameters")

    def start(self):
        if self.rx_if_conf == None or self.rx_rf_conf == None:
            raise Exception("RF Interface and chains aren't yet configured")

        if lgw_start() != LGW_HAL_SUCCESS:
            raise Exception("Can't start gateway, please check configuration")

    def stop(self):
        if lgw_stop() != LGW_HAL_SUCCESS:
            raise Exception("Can't stop gateway, check communication")

    def receive(self, max_packets: int) -> tuple:
        received_packet_array = (lgw_pkt_rx_s * max_packets)()
        nb_packets_received = lgw_receive(
            max_packets, byref(received_packet_array[0]))

        rx_packets = []
        for i in range(nb_packets_received):
            rx_packets.append(RxPacket(freq_hz=received_packet_array[i].freq_hz, freq_offset=received_packet_array[i].freq_offset, if_chain=received_packet_array[i].if_chain, status=received_packet_array[i].status, count_us=received_packet_array[i].count_us,
                                       rf_chain=received_packet_array[i].rf_chain, modem_id=received_packet_array[i].modem_id, modulation=received_packet_array[
                                           i].modulation, bandwidth=received_packet_array[i].bandwidth, datarate=received_packet_array[i].datarate,
                                       coderate=received_packet_array[i].coderate, rssic=received_packet_array[i].rssic, rssis=received_packet_array[i].rssis, snr=received_packet_array[
                                           i].snr, snr_min=received_packet_array[i].snr_min, snr_max=received_packet_array[i].snr_max, crc=received_packet_array[i].crc,
                                       size=received_packet_array[i].size, payload=received_packet_array[i].payload, ftime_received=received_packet_array[i].ftime_received, ftime=received_packet_array[i].ftime))
        return nb_packets_received, rx_packets
