
import utime
import rp2
from rp2 import PIO, asm_pio
from machine import Pin

   
@asm_pio(set_init=(PIO.OUT_HIGH),autopush=True, push_thresh=8)
def DHT11_PIO():
    # clock set at 500Khz  Cycle is 2us
    # drive output low for at least 20ms
    set(y,1)                    # 0
    pull()                      # 1
    mov(x,osr)                  # 2
    set(pindirs,1)              # 3 set pin to output
    set(pins,0)                 # 4 set pin low
    label ('waitx')
    jmp(x_dec,'waitx')          # 5 decrement x reg every 32 cycles
    set(pindirs,0)              # 6 set pin to input 
    # STATE A. Wait for high at least 80us. max should be  very short
    set(x,31)                   # 7 
    label('loopA')
    jmp(pin,'got_B')            # 8
    jmp(x_dec,'loopA')          # 9
    label('Error')
    in_(y,1)                    # 10
    jmp('Error')                # 11  Infinity loop error

    # STATE B. Get HIGH pulse. max should be 40us
    label('got_B')
    set(x,31)                   # 12
    label('loop_B')
    jmp(x_dec,'check_B')        # 13
    jmp('Error')                # 14
    label('check_B') 
    jmp(pin,'loop_B')           # 15
 
    # STATE C. Get LOW pulse. max should be 80us
    set(x,31)                   # 16
    label('loop_C')
    jmp(pin,'got_D')            # 17     
    jmp(x_dec,'loop_C')         # 18
    jmp('Error')                # 19
    
    # STATE D. Get HIGH pulse. max should be 80us
    label('got_D')
    set(x,31)                   # 20
    label('loop_D')
    jmp(x_dec,'check_D')        # 21
    jmp('Error')                # 22
    label('check_D')
    jmp(pin,'loop_D')           # 23
    
    # STATE E. Get Low pulse delay. should be around 50us
    set(x,31)                   # 24
    label('loop_E')
    jmp(pin,'got_F')            # 25
    jmp(x_dec,'loop_E')         # 26
    jmp('Error')                # 27
   
    # STATE F.
    # wait 40 us
    label('got_F')              
    nop() [20]                  # 28
    in_(pins,1)                 # 29
    # now wait for low pulse
    set(x,31)                   # 30
    jmp('loop_D')               # 31    




class DHT11:
    
    def __init__(self,dataPin, powerPin=None,dht11=False,smID=1):
        self.dataPin = dataPin
        self.powerPin = powerPin
        self.dht11 = dht11
        self.smID = smID
        self.dataPin.init(Pin.IN, Pin.PULL_UP)
        if self.powerPin is not None:
            self.powerPin.init(Pin.OUT)
            self.powerPin.value(0)
        self.sm= rp2.StateMachine(self.smID)
        




    def read_array(self):
        if self.powerPin is not None:
            self.powerPin.value(1)
        utime.sleep_ms(100)
        #start state machine
        self.sm.init(DHT11_PIO,freq=500000,
                     set_base=self.dataPin,
                     in_base=self.dataPin,
                     jmp_pin=self.dataPin)
        if self.dht11:
            self.sm.put(10000)
        else:
            self.sm.put(1000)
        self.sm.active(1)
        value = []
        for i in range(5):
            value.append(self.sm.get())
        self.sm.active(0)
        return value
 
    def read(self):
        value = self.read_array()
        sumV = 0
        for i in range(4):
            sumV += value[i]
        if (sumV & 0xff) == value[4]:
            if self.dht11:
                humidity=value[0] & 0x7f
                temperature=value[2] 
            else:                
                humidity=((value[0]<<8)  + value[1])/10.0
                temperature=(((value[2] &0x7f) << 8)  + value[3]) /10.0 
            if (value[2] & 0x80) == 0x80:
                temperature = -temperature            
            return temperature, humidity
        else:
            return None, None
        
if __name__ == "__main__":
    from machine import Pin
    from DHT11 import DHT11
    import utime
    dht_data = Pin(15,Pin.IN,Pin.PULL_UP)
    dht_sensor=DHT11(dht_data,Pin(14,Pin.OUT),dht11=False)
    while True:
        T,H = dht_sensor.read()
        if T is None:
            print(" sensor error")
        else:
            print("{:3.1f}'C  {:3.1f}%".format(T,H))
        #DHT22 not responsive if delay to short
        utime.sleep_ms(1000)
        
