import array
import utime
import micropython
from machine import Pin
from micropython import const

class InvalidChecksum(Exception):
    pass

class InvalidPulseCount(Exception):
    pass

MAX_UNCHANGED = const(100)
HIGH_LEVEL = const(50)
EXPECTED_PULSES = const(84)
MIN_INTERVAL_US = const(200000)

class Sensor:
    def __init__(self, pin):
        self.temperature = 0.0
        self.humidity = 0.0
        self.pin = pin
        self.lastMeasure = utime.ticks_us()
        
    def InitSignal(self):
        self.pin.init(Pin.OUT, Pin.PULL_DOWN)
        self.pin.value(1)
        utime.sleep_ms(50)
        self.pin.value(0)
        utime.sleep_ms(18)
     
    def CapturePulses(self):
        #pin = self.pin
        self.pin.init(Pin.IN, Pin.PULL_UP)
        
        value = 1
        index = 0
        transitions = bytearray(EXPECTED_PULSES)
        unchanged = 0
        timestamp = utime.ticks_us()
        
        while unchanged < MAX_UNCHANGED:
            if value != self.pin.value():
                if index >= EXPECTED_PULSES:
                    raise InvalidPulseCount("Got more than {} pulses".format(EXPECTED_PULSES))
                now = utime.ticks_us()
                transitions[index] = now - timestamp
                timestamp = now
                index += 1
                
                value = 1 - value
                unchanged = 0
            else:
                unchanged += 1
                
        self.pin.init(Pin.OUT, Pin.PULL_DOWN)
        if index != EXPECTED_PULSES:
            raise InvalidPulseCount("Expected {} but got {} pulses".format(EXPECTED_PULSES, index))
        return transitions[4:]
    
    def PulsesToBuffer(self, pulses):
        binary = 0
        #print(pulses)
        
        for idx in range (0, len(pulses), 2):
            binary = binary << 1 | int(pulses[idx] > HIGH_LEVEL)
            
        #print("{0:b}".format(binary))
            
        buffer = array.array("B")
        for shift in range(4, -1, -1):
            buffer.append(binary >> shift * 8 & 0xFF)
            #print("{0:b}".format(buffer[len(buffer) - 1]))
            
        return buffer
    
    def VerifyChecksum(self, buffer):
        checksum = 0
        for index in buffer [0:4]:
            checksum += index
        if checksum & 0xFF != buffer[4]:
            raise InvalidChecksum()
            
    def MeasureTemperatureAndHumidity(self):
        currentTicks = utime.ticks_us()
        if utime.ticks_diff(currentTicks, self.lastMeasure) < MIN_INTERVAL_US and (self.temperature > -1 or self.humidity > -1):
            return
        
        self.InitSignal()
        pulses = self.CapturePulses()
        buffer = self.PulsesToBuffer(pulses)
        self.VerifyChecksum(buffer)
        
        self.humidity = buffer [0]
        self.humidityDecimal = buffer[1]
        self.temperature = buffer [2]
        self.temperatureDecimal = buffer[3]
        self.lastMeasure = utime.ticks_us()
        
