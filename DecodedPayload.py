import json
from time import time
from datetime import datetime
DATA_LIMITS_PRESSURE_MIN = 900

class DecodedPayload():
    payload = []

    def __init__(self, payload: list) -> None:
        self.payload = payload
        self.decode_payload()
        pass

    def decode_payload(self):
        self.sensor = 0
        for i in range(4):
            self.sensor += self.payload[9+i] << (8 * i)
        self.alarm = self.payload[8] & 0x3
        self.topic = (self.payload[8] & 0x1C) >> 2
        self.hops_count = self.payload[8] >> 5
        self.temp = self.payload[7]
        self.hum = self.payload[6]
        self.press = self.payload[5] + DATA_LIMITS_PRESSURE_MIN
        self.co2 = (self.payload[4] << 4) + (self.payload[3] >> 4)
        self.bvoc = ((self.payload[3] & 0xF) << 6) + (self.payload[2] >> 2)
        self.gaz = ((self.payload[2] & 0x3) << 8) + self.payload[1]
        self.date = datetime.now()
    
    def __str__(self) -> str:
        return (f"A payload from 0X{'{:02X}'.format(self.sensor)} at {self.date}\n\
        |_ Temperature (°C): {self.temp}\n\
        |_ Humidity (%): {self.hum}\n\
        |_ Pressure (hPa): {self.press}\n\
        |_ CO2 (ppm): {self.co2}\n\
        |_ bVOC (ppm): {self.bvoc}\n\
        |_ Gas Resistance (kOhm): {self.gaz}\n\
        |_ Hops Count: {self.hops_count}\n\
        |_ Alarm: {self.alarm}")
    
    def get_json(self):
        dict_payload = self.__dict__
        dict_payload.pop('payload')
        dict_payload.pop('hops_count')
        dict_payload = {'json_payload': json.dumps(dict_payload, default=str)}
        return dict_payload