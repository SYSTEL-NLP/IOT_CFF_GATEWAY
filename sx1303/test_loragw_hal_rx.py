from loragw_hal import *
from time import sleep

DEFAULT_FREQ_HZ = 868500000
DEFAULT_COM_PATH = b"/dev/ttyACM0\0"
DEFAULT_CHANNEL_MODE = 0
DEFAULT_COM_TYPE = CommunicationTypes.LGW_COM_USB.value
DEFAULT_DATA_RATE = DataRates.DR_LORA_SF7.value
DEFAULT_BANDWIDTH = Bendwidths.BW_125KHZ.value
DEFAULT_RADIO_TYPE = RadioTypes.LGW_RADIO_TYPE_SX1250.value
MAX_POLLED_PACKETS = 10

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

# Configure the gateway
boardconf = lgw_conf_board_s(com_path=DEFAULT_COM_PATH, lorawan_public=True,
                             clksrc=0, com_type=DEFAULT_COM_TYPE)
print("lgw_board_setconf: " +
      ("Success" if lgw_board_setconf(byref(boardconf)) == 0 else "Failed"))

# Set configuration for RF chains
rfconf = lgw_conf_rxrf_s(enable=True, freq_hz=DEFAULT_FREQ_HZ,
                         type=DEFAULT_RADIO_TYPE, rssi_offset=0,
                         single_input_mode=False, tx_enable=False)
print("lgw_rxrf_setconf 0: " +
      ("Success" if lgw_rxrf_setconf(0, byref(rfconf)) == 0 else "Failed"))
print("lgw_rxrf_setconf 1: " +
      ("Success" if lgw_rxrf_setconf(1, byref(rfconf)) == 0 else "Failed"))


# Set configuration for LoRa multi-SF channels (bandwidth cannot be set)
for i in range(0, 8):
    channel_mode = DEFAULT_CHANNEL_MODE
    freq_hz = CHANNEL_IF_MODE_0[i] if channel_mode == 0 else CHANNEL_IF_MODE_1[i]
    rf_chain = CHANNEL_RFCHAIN_MODE_0[i] if channel_mode == 0 else CHANNEL_RFCHAIN_MODE_1[i]
    datarate = DEFAULT_DATA_RATE
    ifconf = lgw_conf_rxif_s(enable=True, rf_chain=rf_chain,
                             freq_hz=freq_hz, datarate=datarate)
    print(f"lgw_rxif_setconf {i}: " +
          ("Success" if lgw_rxif_setconf(i, byref(ifconf)) == 0 else "Failed"))

# Set configuration for LoRa Service channel
channel_mode = DEFAULT_CHANNEL_MODE
freq_hz = CHANNEL_IF_MODE_0[8]
rf_chain = CHANNEL_RFCHAIN_MODE_0[8]
datarate = DEFAULT_DATA_RATE
bandwidth = DEFAULT_BANDWIDTH
ifconf = lgw_conf_rxif_s(enable=True, rf_chain=rf_chain, freq_hz=freq_hz,
                         datarate=datarate, bandwidth=bandwidth)
print("lgw_rxif_setconf 8: " +
      ("Success" if lgw_rxif_setconf(8, byref(ifconf)) == 0 else "Failed"))

print("lgw_start: " +
      ("Success" if lgw_start() == 0 else "Failed"))

print("Waiting for packets...")
nb_packets_received = 0

received_packet_array = (lgw_pkt_rx_s * MAX_POLLED_PACKETS)()

while (nb_packets_received < 6):
    nb_pkt = lgw_receive(MAX_POLLED_PACKETS, byref(received_packet_array[0]))
    if (nb_pkt == 0):
        sleep(0.01)
    else:
        print(f"received {nb_pkt} packets")
        for i in range(nb_pkt):
            print(
                f"----- {'LoRa' if (received_packet_array[i].modulation == ModulationTypes.MOD_LORA.value) else 'FSK'} packet -----")
            print(f"  count_us: {received_packet_array[i].count_us}")
            print(f"  size:     {received_packet_array[i].size}")
            print(f"  chan:     {received_packet_array[i].if_chain}")
            print(f"  status:   {received_packet_array[i].status}")
            print(f"  datr:     {received_packet_array[i].datarate}")
            print(f"  codr:     {received_packet_array[i].coderate}")
            print(f"  rf_chain  {received_packet_array[i].rf_chain}")
            print(f"  freq_hz   {received_packet_array[i].freq_hz}")
            print(f"  snr_avg:  {received_packet_array[i].snr}")
            print(f"  rssi_chan:{received_packet_array[i].rssic}")
            print(f"  rssi_sig :{received_packet_array[i].rssis}")
            print(f"  crc:      {received_packet_array[i].crc}")
            payload = [received_packet_array[i].payload[j]
                       for j in range(received_packet_array[i].size)]
            print(payload)
        nb_packets_received += nb_pkt

print(f"received {nb_packets_received} packets, loop stopped")
print("lgw_stop: " +
      ("Success" if lgw_stop() == 0 else "Failed"))
