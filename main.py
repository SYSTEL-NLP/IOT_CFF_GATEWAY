from sx1303 import SX1303, RxPacket
from time import sleep
from DecodedPayload import DecodedPayload
import csv
from requests import post

url = 'https://cff-lora.systel-sa.com/save/'

try:
    gateway = SX1303()
    gateway.configure_rx_rf_chains()
    gateway.configure_rx_channels()
    gateway.start()
except:
    gateway = SX1303(com_path = b"/dev/ttyACM1\0")
    gateway.configure_rx_rf_chains()
    gateway.configure_rx_channels()
    gateway.start()


while(True):
    try:
        nb_packets_received, packets_received = gateway.receive(10)
        if(nb_packets_received == 0):
            sleep(0.01)
        else:
            print(f"received {nb_packets_received} packets")
            for i in range(nb_packets_received):
                rx_packet: RxPacket = packets_received[i]
                """print(f"  count_us: {rx_packet.count_us}")
                print(f"  size:     {rx_packet.size}")
                print(f"  chan:     {rx_packet.if_chain}")
                print(f"  status:   {rx_packet.status}")
                print(f"  datr:     {rx_packet.datarate}")
                print(f"  codr:     {rx_packet.coderate}")
                print(f"  rf_chain  {rx_packet.rf_chain}")
                print(f"  freq_hz   {rx_packet.freq_hz}")
                print(f"  snr_avg:  {rx_packet.snr}")
                print(f"  rssi_chan:{rx_packet.rssic}")
                print(f"  rssi_sig :{rx_packet.rssis}")
                print(f"  crc:      {rx_packet.crc}")            
                print(rx_packet.payload) """
                if(rx_packet.size == 13 and rx_packet.payload[0]==0xE3):
                    decoded_payload = DecodedPayload(rx_packet.payload)
                    file_path=f"/home/rak/projects/IOT_CFF_GATEWAY/resultats/hops.csv"
                    row = [f"0X{'{:02X}'.format(decoded_payload.sensor)}", decoded_payload.date, decoded_payload.hops_count]
                    with open(file_path, 'a', encoding='UTF8') as file:
                        writer = csv.writer(file)
                        writer.writerow(row)

                    json_data = decoded_payload.get_json()
                    print(json_data)
                    result = post(url=url, data=json_data)
                    print(result)

    except Exception as e:
        print(e)
        pass