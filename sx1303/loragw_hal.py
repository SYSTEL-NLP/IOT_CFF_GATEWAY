from ctypes import *
from os import path
from enum import Enum

# Get the path
dir_path = path.dirname(path.realpath(__file__))
lib_name = "libloragw.so"

# Load the shared library
libloragw = cdll.LoadLibrary(path.join(dir_path, lib_name))

# Commmunication type
class CommunicationTypes(Enum):
    LGW_COM_SPI = 0
    LGW_COM_USB = 1
    LGW_COM_UNKNOWN = 2

# Radio Type
class RadioTypes(Enum):
    LGW_RADIO_TYPE_NONE = 0
    LGW_RADIO_TYPE_SX1255 = 1
    LGW_RADIO_TYPE_SX1257 = 2
    LGW_RADIO_TYPE_SX1272 = 3
    LGW_RADIO_TYPE_SX1276 = 4
    LGW_RADIO_TYPE_SX1250 = 5

# Data Rates
class DataRates(Enum):
    DR_UNDEFINED = 0
    DR_LORA_SF5  = 5
    DR_LORA_SF6  = 6
    DR_LORA_SF7  = 7
    DR_LORA_SF8  = 8
    DR_LORA_SF9  = 9
    DR_LORA_SF10 = 10
    DR_LORA_SF11 = 11
    DR_LORA_SF12 = 12

# Bandwidths
class Bendwidths(Enum):
    BW_UNDEFINED = 0
    BW_500KHZ    = 0x06
    BW_250KHZ    = 0x05
    BW_125KHZ    = 0x04

# Modulation types
class ModulationTypes(Enum):
    MOD_UNDEFINED = 0
    MOD_CW        = 0x08
    MOD_LORA      = 0x10
    MOD_FSK       = 0x20

# Clock Sources
class ClockSources(Enum):
    CLK_SOURCE_RF_CHAIN_0 = 0
    CLK_SOURCE_RF_CHAIN_1 = 1

# Return values
LGW_HAL_SUCCESS     = 0
LGW_HAL_ERROR       = -1
LGW_LBT_NOT_ALLOWED = 1

class lgw_conf_board_s(Structure):
    _fields_ = [("lorawan_public", c_bool),
                ("clksrc", c_uint8),
                ("full_duplex", c_bool),
                ("com_type", c_int),
                ("com_path", c_char * 64)]


class lgw_rssi_tcomp_s(Structure):
    _fields_ = [("coeff_a", c_float),
                ("coeff_b", c_float),
                ("coeff_c", c_float),
                ("coeff_d", c_float),
                ("coeff_e", c_float)]


class lgw_conf_rxrf_s(Structure):
    _fields_ = [("enable", c_bool),
                ("freq_hz", c_uint32),
                ("rssi_offset", c_float),
                ("rssi_tcomp", lgw_rssi_tcomp_s),
                ("type", c_uint8),
                ("tx_enable", c_bool),
                ("single_input_mode", c_bool)]

class lgw_conf_rxif_s(Structure):
    _fields_ = [("enable", c_bool),
                ("rf_chain", c_uint8),
                ("freq_hz", c_int32),
                ("bandwidth", c_uint8),
                ("datarate", c_uint32),
                ("sync_word_size", c_uint8),
                ("sync_word", c_uint64),
                ("implicit_hdr", c_bool),
                ("implicit_payload_length", c_uint8),
                ("implicit_crc_en", c_bool),
                ("implicit_coderate", c_uint8)]

class lgw_pkt_rx_s(Structure):
    _fields_ = [("freq_hz", c_uint32),
                ("freq_offset", c_int32),
                ("if_chain", c_uint8),
                ("status", c_uint8),
                ("count_us", c_uint32),
                ("rf_chain", c_uint8),
                ("modem_id", c_uint8),
                ("modulation", c_uint8),
                ("bandwidth", c_uint8),
                ("datarate", c_uint32),
                ("coderate", c_uint8),
                ("rssic", c_float),
                ("rssis", c_float),
                ("snr", c_float),
                ("snr_min", c_float),
                ("snr_max", c_float),
                ("crc", c_uint16),
                ("size", c_uint16),
                ("payload", c_uint8 * 256),
                ("ftime_received", c_bool),
                ("ftime", c_uint32)]



"""
@brief Configure the gateway board
@param conf structure containing the configuration parameters
@return LGW_HAL_ERROR id the operation failed, LGW_HAL_SUCCESS else
*/
"""
lgw_board_setconf = libloragw.lgw_board_setconf
lgw_board_setconf.argtypes = [POINTER(lgw_conf_board_s)]
lgw_board_setconf.restype = c_int

"""
@brief Configure an RF chain (must configure before start)
@param rf_chain number of the RF chain to configure [0, LGW_RF_CHAIN_NB - 1]
@param conf structure containing the configuration parameters
@return LGW_HAL_ERROR id the operation failed, LGW_HAL_SUCCESS else
"""
lgw_rxrf_setconf = libloragw.lgw_rxrf_setconf
lgw_rxrf_setconf.argtypes = [c_uint8, POINTER(lgw_conf_rxrf_s)]
lgw_rxrf_setconf.restype = c_int

"""
@brief Configure an IF chain + modem (must configure before start)
@param if_chain number of the IF chain + modem to configure [0, LGW_IF_CHAIN_NB - 1]
@param conf structure containing the configuration parameters
@return LGW_HAL_ERROR id the operation failed, LGW_HAL_SUCCESS else
"""
lgw_rxif_setconf = libloragw.lgw_rxif_setconf
lgw_rxif_setconf.argtypes = [c_uint8, POINTER(lgw_conf_rxif_s)]
lgw_rxif_setconf.restype = c_int

"""
@brief Connect to the LoRa concentrator, reset it and configure it according to previously set parameters
@return LGW_HAL_ERROR id the operation failed, LGW_HAL_SUCCESS else
"""
lgw_start = libloragw.lgw_start
lgw_start.argtypes = []
lgw_start.restype = c_int

"""
@brief Stop the LoRa concentrator and disconnect it
@return LGW_HAL_ERROR id the operation failed, LGW_HAL_SUCCESS else
"""
lgw_stop = libloragw.lgw_stop
lgw_stop.argtypes = []
lgw_stop.restype = c_int

"""
@brief A non-blocking function that will fetch up to 'max_pkt' packets from the LoRa concentrator FIFO and data buffer
@param max_pkt maximum number of packet that must be retrieved (equal to the size of the array of struct)
@param pkt_data pointer to an array of struct that will receive the packet metadata and payload pointers
@return LGW_HAL_ERROR id the operation failed, else the number of packets retrieved
"""
lgw_receive = libloragw.lgw_receive
lgw_receive.argtypes = [c_uint8, POINTER(lgw_pkt_rx_s)]
lgw_stop.restype = c_int
