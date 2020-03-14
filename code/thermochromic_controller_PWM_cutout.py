from microcontroller import delay_us
from microcontroller import pin
import digitalio
import time
import adafruit_dht
# import random

temp_unit = "C"         # temperature unit ("C" or "F")
dutycycle = 0.055        # PWM duty cycle (0 to 0.058)
frequency = 100.       # PWM frequency (Hz)

# heating time is linearly interpolated between two points
P1 = [26, 3.5, 55]  # first point [temperature (°C/F), heating time (s), cooling time (s)]
P2 = [21, 6.5, 30]   # second point [temperature (°C/F), heating time (s), cooling time (s)]

# t_cool = 30             # cooling duration (s)

# reduction factor of duty cycle if segment was heated before
f_reduce = 0.55

seg1E = digitalio.DigitalInOut(pin.PA02)
seg1G = digitalio.DigitalInOut(pin.PA03)
seg1D = digitalio.DigitalInOut(pin.PA04)
seg1C = digitalio.DigitalInOut(pin.PA05)
seg2E = digitalio.DigitalInOut(pin.PA06)
seg2G = digitalio.DigitalInOut(pin.PA07)
seg2D = digitalio.DigitalInOut(pin.PA08)
seg2C = digitalio.DigitalInOut(pin.PA09)
segD2 = digitalio.DigitalInOut(pin.PA10)
segD3 = digitalio.DigitalInOut(pin.PA11)
segD1 = digitalio.DigitalInOut(pin.PA14)
seg2B = digitalio.DigitalInOut(pin.PA15)
seg2A = digitalio.DigitalInOut(pin.PA16)
seg2F = digitalio.DigitalInOut(pin.PA17)
seg1B = digitalio.DigitalInOut(pin.PA18)
seg1A = digitalio.DigitalInOut(pin.PA19)
seg1F = digitalio.DigitalInOut(pin.PA22)

seg1A.direction = digitalio.Direction.OUTPUT
seg1B.direction = digitalio.Direction.OUTPUT
seg1C.direction = digitalio.Direction.OUTPUT
seg1D.direction = digitalio.Direction.OUTPUT
seg1E.direction = digitalio.Direction.OUTPUT
seg1F.direction = digitalio.Direction.OUTPUT
seg1G.direction = digitalio.Direction.OUTPUT
seg2A.direction = digitalio.Direction.OUTPUT
seg2B.direction = digitalio.Direction.OUTPUT
seg2C.direction = digitalio.Direction.OUTPUT
seg2D.direction = digitalio.Direction.OUTPUT
seg2E.direction = digitalio.Direction.OUTPUT
seg2F.direction = digitalio.Direction.OUTPUT
seg2G.direction = digitalio.Direction.OUTPUT
segD1.direction = digitalio.Direction.OUTPUT
segD2.direction = digitalio.Direction.OUTPUT
segD3.direction = digitalio.Direction.OUTPUT

# Initial the dht device, with data pin connected to:
dhtDevice = adafruit_dht.DHT22(pin.PA23)

# last heated segments
seg_last = []

# adjust factor for heating duration of each segment
def adjust_factor(pinname):
    if pinname == seg1A:
        return 1.
    elif pinname == seg1B:
        return 1.
    elif pinname == seg1C:
        return 1.
    elif pinname == seg1D:
        return 1.25
    elif pinname == seg1E:
        return 1.
    elif pinname == seg1F:
        return 1.
    elif pinname == seg1G:
        return 1.
    elif pinname == seg2A:
        return 1.
    elif pinname == seg2B:
        return 1.
    elif pinname == seg2C:
        return 1.
    elif pinname == seg2D:
        return 1.2
    elif pinname == seg2E:
        return 1.
    elif pinname == seg2F:
        return 1
    elif pinname == seg2G:
        return 1
    elif pinname == segD1:
        return 1.
    elif pinname == segD2:
        return 1.
    elif pinname == segD3:
        return 8.5
    else:
        return 0


# calculate heating time through linear interpolation
def CalcHeat(T):
    global P1, P2
    # print("heating time:")
    # print((T - P1[0]) * (P2[1] - P1[1]) / (P2[0] - P1[0]) + P1[1])
    return (T - P1[0]) * (P2[1] - P1[1]) / (P2[0] - P1[0]) + P1[1]

# calculate cooling time through linear interpolation
def CalcCool(T):
    global P1, P2
    # print("heating time:")
    # print((T - P1[0]) * (P2[1] - P1[1]) / (P2[0] - P1[0]) + P1[1])
    return (T - P1[0]) * (P2[2] - P1[2]) / (P2[0] - P1[0]) + P1[2]

# convert number to segments
# unit = empty or "%"
def num2seg(number, unit=""):
    segments1 = {
        1: [seg1B, seg1C],
        2: [seg1A, seg1B, seg1D, seg1E, seg1G],
        3: [seg1A, seg1B, seg1C, seg1D, seg1G],
        4: [seg1F, seg1B, seg1G, seg1C],
        5: [seg1A, seg1F, seg1G, seg1C, seg1D],
        6: [seg1A, seg1F, seg1G, seg1E, seg1C, seg1D],
        7: [seg1A, seg1B, seg1C],
        8: [seg1A, seg1B, seg1C, seg1D, seg1E, seg1F, seg1G],
        9: [seg1A, seg1B, seg1C, seg1D, seg1F, seg1G]

    }
    segments2 = {
        0: [seg2A, seg2B, seg2C, seg2D, seg2E, seg2F],
        1: [seg2B, seg2C],
        2: [seg2A, seg2B, seg2D, seg2E, seg2G],
        3: [seg2A, seg2B, seg2C, seg2D, seg2G],
        4: [seg2F, seg2B, seg2G, seg2C],
        5: [seg2A, seg2F, seg2G, seg2C, seg2D],
        6: [seg2A, seg2F, seg2G, seg2E, seg2C, seg2D],
        7: [seg2A, seg2B, seg2C],
        8: [seg2A, seg2B, seg2C, seg2D, seg2E, seg2F, seg2G],
        9: [seg2A, seg2B, seg2C, seg2D, seg2F, seg2G]
    }

    number = round(number)
    number1 = int(number/10)
    number2 = number % 10
    print("digit 1:")
    print(number1)
    print("digit 2:")
    print(number2)
    if number1 > 0:
        digit1 = segments1.get(number1)
    else:
        digit1 = []
    digit2 = segments2.get(number2)
    segments = digit1 + digit2 + [segD1]
    # segments.append(segD1)
    if unit == "%":
        segments += [segD2, segD3]
    return segments

# read DHT22
def readDHT():
    try:
        # Print the values to the serial port
        temperature_c = dhtDevice.temperature
        # temperature_c = random.uniform(15, 35)
        temperature_f = temperature_c * (9 / 5) + 32
        humidity = dhtDevice.humidity
        # humidity = random.uniform(20, 90)
        print("Temp: {:.1f} F / {:.1f} C    Humidity: {}% "
              .format(temperature_f, temperature_c, humidity))
        if temp_unit == "C":
            return temperature_c, humidity
        elif temp_unit == "F":
            return temperature_f, humidity

    except RuntimeError as error:
        # Errors happen fairly often, DHT's are hard to read, just keep going
        print(error.args[0])
        return 0


# check if pinname is in list
def compare(pinname1, pinnames):
    for pinname2 in pinnames:
        if pinname1 == pinname2:
            return 1
    return 0

# create fake PWM signal
def fakePWM(pinnames, pinnames_last, duration):
    global dutycycle
    global frequency
    global adjust_factor
    global f_reduce
    T = 1./frequency                    # period in s
    ontime = T*dutycycle*1e6            # on time in µs
    offtime = T*(1-dutycycle)*1e6       # off time in µs
    cycles = int(duration/T)            # number of cycles
    npins = len(pinnames)               # number of segments
    # print("ontime: {:.0f} us" .format(ontime))
    # print("offtime: {:.0f} us" .format(offtime))
    # print("cycles: {:.0f}" .format(cycles))
    # print("npins: {:.0f}" .format(npins))

    # calculate on time for each segment
    ontime_adjusted = []
    for pinname in pinnames:
        if compare(pinname, pinnames_last):
            # reduce duration if element was heated before
            ontime_adjusted.append(f_reduce*ontime*adjust_factor(pinname))
        else:
            ontime_adjusted.append(ontime*adjust_factor(pinname))
    dt = offtime-sum(ontime_adjusted)+ontime_adjusted[0]       # delay at end of pulse cycle
    # print("dt: {:.0f} us" .format(dt))
    # print("total duration: {:.0f} us" .format(sum(ontime_adjusted)+dt))
    if dt < 0.:
        dt = 0.
    # heat segments
    for i in range(cycles):
        # to limit current segments are heated one after another
        j = 0
        for pinname in pinnames:
            pinname.value = True
            delay_us(int(ontime_adjusted[j]))
            pinname.value = False
            j += 1
        delay_us(int(dt))

    return

time.sleep(2)

while True:
    DHT_data = readDHT()
    if DHT_data:
        print("showing temperature")
        seg = num2seg(DHT_data[0])              # temperature
        print("heating ...")
        fakePWM(seg, seg_last, CalcHeat(DHT_data[0]))
        seg_last = seg
        print("cooling ...")
        time.sleep(CalcCool(DHT_data[0]))
    DHT_data = readDHT()
    if DHT_data:
        print("showing humidity")
        seg = num2seg(DHT_data[1], unit="%")          # humidity
        print("heating ...")
        fakePWM(seg, seg_last, CalcHeat(DHT_data[0]))
        seg_last = seg
        print("cooling ...")
        time.sleep(CalcCool(DHT_data[0]))



