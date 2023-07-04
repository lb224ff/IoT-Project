from machine import Pin #I2C
import utime as time
from dht import Sensor

import network
import usocket

pin = Pin(16, Pin.OUT, Pin.PULL_DOWN)
sensor = Sensor(pin)


print('Starting sensor')
sta_if = network.WLAN(network.STA_IF)
sta_if.active(True)
print("connecting...")
sta_if.connect("ssid", "Password")

connected = sta_if.isconnected()
if connected:
    print("connected to WiFi")
else:
    print("not connected")
    
HOST = 'Your IP'
PORT = 8000

#nodeSocket.connect(usocket.getaddrinfo(HOST, PORT, 0, usocket.SOCK_STREAM)[0] [-1])
#nodeSocket.connect((HOST, PORT))

nrOfFails = 0
while connected:
    try:
        data = b'POST /"data" HTTP/1.1\r\nUser-Agent: Client\r\nHost: Your IP \r\nContent-Type: text/strings \r\nContent-Length: 12 \r\nAccept-Laguage:en-us \r\nAccept-Encoding: gzip, deflate\r\nConnection: Close \r\n\r\n'
        nodeSocket = usocket.socket(usocket.AF_INET, usocket.SOCK_STREAM)
        #socketAdress = usocket.getaddrinfo(HOST, PORT)
        #nodeSocket.connect(socketAdress[0][-1])
        nodeSocket.connect((HOST, PORT))
        time.sleep(2)
        sensor.MeasureTemperatureAndHumidity()
        
        #print("Humidity: {}.{}".format(sensor.humidity, sensor.humidityDecimal))
        #print("Temperature: {}.{}".format(sensor.temperature, sensor.temperatureDecimal))
        
        byteData = (sensor.humidity).to_bytes(2, 'big')
        byteData += (sensor.humidityDecimal).to_bytes(2, 'big')
        byteData += (sensor.temperature).to_bytes(2, 'big')
        byteData += (sensor.temperatureDecimal).to_bytes(2, 'big')
        #print(byteData)
        data += byteData
        #data += b'\r\n\r\n'
        if not sta_if.isconnected():
            break
        
        nodeSocket.sendall(data)
        nodeSocket.recv(1024)
        nodeSocket.close()
    
        nrOfFails = 0
        
    except Exception as e:
        print('Failed to read sensor')
        nrOfFails += 1
        if nrOfFails > 4:
            print('Failed too many times in a row')
            break
    
    
    
print("Lost Connection")
    
nodeSocket.close()    
