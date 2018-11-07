import Queue, threading, time, serial
import logging
lock = threading.Lock()

class configurationMonitor(threading.Thread):                       
    def __init__(   self, 
                    data_q, data_o, error_q, 
                    port_num,
                    port_baud,
                    config,
                    port_stopbits = serial.STOPBITS_ONE,
                    port_parity   = serial.PARITY_NONE,
                    port_timeout  = 0.01):
        threading.Thread.__init__(self)        
        self.serial_port = None
        self.serial_arg  = dict( port      = port_num,
                                 baudrate  = port_baud,
                                 stopbits  = port_stopbits,
                                 parity    = port_parity,
                                 timeout   = port_timeout)
        self.data_q   = data_q
        self.data_o  = data_o
        self.error_q  = error_q
        self.config=config
        self.alive    = threading.Event()
        self.alive.set()

    def run(self):
        try:
            if self.serial_port: 
                self.serial_port.close()
            self.serial_port = serial.Serial(**self.serial_arg)
            self.serial_port.flushInput()
        except serial.SerialException, e:
            self.error_q.put(e.message)
            return
        logging.info('Iniciando Monitor Configuraciones')            
        self.serial_port.write("Esperando Dato Serial...\n")
        while self.alive.isSet():            
            message=self.serial_port.read(100)
            #print (message,hex)
            if len(message)>0:
                print "recibi dato!!!"
                logging.info("Comando Recibido")
                #message=message.split(' ')
                print message
                self.data_q.put(message)
            outmessage= self.data_o.get()
            if outmessage is not None:                
                self.serial_port.write(outmessage)
        if self.serial_port:
            self.serial_port.close()            
    def join(self, timeout=None):
        self.alive.clear()
        threading.Thread.join(self, timeout)

#------------------------------------------------------------------------------------------
class weigthMonitor(threading.Thread):
    def __init__(   self, 
                    data_q, error_q, 
                    port_num,
                    port_baud,
                    flag,
                    port_stopbits = serial.STOPBITS_ONE,
                    port_parity   = serial.PARITY_NONE,
                    port_timeout  = 0.01):
        threading.Thread.__init__(self)        
        self.serial_port = None
        self.serial_arg  = dict( port      = port_num,
                                 baudrate  = port_baud,
                                 stopbits  = port_stopbits,
                                 parity    = port_parity,
                                 timeout   = port_timeout)
        self.data_q   = data_q
        self.error_q  = error_q
        self.flag = flag
        self.alive    = threading.Event()
        self.alive.set()

    def run(self):
        try:
            if self.serial_port: 
                self.serial_port.close()
            self.serial_port = serial.Serial(**self.serial_arg)
            self.serial_port.flushInput()
        except serial.SerialException, e:
            self.error_q.put(e.message)
            return
        psnInCount=0
        psnOutCount=0        
        logging.info('Iniciando weigth-Serial')
        startTime = time.time()        
        while self.alive.isSet():
            if (self.flag):                
                message=self.serial_port.readline()
                message=str(message)
                message=message.strip('\r\n')
                message=message.split('|')                
                qdata=[0,0,0]                
                if len(message) >= 4:
                    print(message)
                    logging.info('Dato weigth-serial Valido Registrado')
                    timestamp = time.time() - startTime                
                    weigth=message[len(message)-1]
                    header=message[0]
                    firmwareversion=header[5:11]                    
                    print(firmwareversion)
                    sensorid=header[15:24]
                    print(sensorid)
                    #print "Peso Total", weigth                    
                    qdata[0]=weigth
                    qdata[1]=sensorid
                    qdata[2]=firmwareversion
                    time.sleep(2)
                    timestamp = time.clock()
                    self.data_q.put((qdata, timestamp))
                else:
                    if(message!=''):                    
                        logging.warning('Dato weigth-Serial corrupto')
                        message=''                 
        if self.serial_port:
            self.serial_port.close()

    def join(self, timeout=None):
        self.alive.clear()
        threading.Thread.join(self, timeout)  
#------------------------------------------------------------------------------------------ 

class UsbMonitorThread(threading.Thread):
    def __init__(   self, 
                    data_q, error_q, 
                    port_num,
                    port_baud,
                    flag,
                    port_stopbits = serial.STOPBITS_ONE,
                    port_parity   = serial.PARITY_NONE,
                    port_timeout  = 0.01):
        threading.Thread.__init__(self)        
        self.serial_port = None
        self.serial_arg  = dict( port      = port_num,
                                 baudrate  = port_baud,
                                 stopbits  = port_stopbits,
                                 parity    = port_parity,
                                 timeout   = port_timeout)
        self.data_q   = data_q
        self.error_q  = error_q
        self.flag = flag
        self.alive    = threading.Event()
        self.alive.set()

    def run(self):
        try:
            if self.serial_port: 
                self.serial_port.close()
            self.serial_port = serial.Serial(**self.serial_arg)
            self.serial_port.flushInput()
        except serial.SerialException, e:
            self.error_q.put(e.message)
            return
        psnInCount=0
        psnOutCount=0        
        logging.info('Iniciando USB-Serial')
        startTime = time.time()        
        while self.alive.isSet():
            if (self.flag):                
                usbmessage=self.serial_port.readline()
                qdata=[0,0,0,0]                
                if len(usbmessage) >= 9:
                    logging.info('Dato Usb-serial Valido Registrado')
                    timestamp = time.time() - startTime                
                    psnIn=ord(usbmessage[4])                
                    psnOut=ord(usbmessage[7])
                    psnInCount=psnInCount+psnIn
                    psnOutCount=psnOutCount+psnOut
                    print "Entraron", psnIn
                    print "Salieron", psnOut
                    qdata[0]=psnIn
                    qdata[1]=psnOut
                    qdata[2]=psnInCount
                    qdata[3]=psnOutCount                    
                    timestamp = time.clock()
                    self.data_q.put((qdata, timestamp))
                else:
                    if(usbmessage!=''):                    
                        logging.warning('Dato Usb-Serial corrupto')
                        usbmessage=''                 
        if self.serial_port:
            self.serial_port.close()

    def join(self, timeout=None):
        self.alive.clear()
        threading.Thread.join(self, timeout)   
#------------------------------------------------------------------------------------------        
class HanoverSignController(threading.Thread):
    def __init__(   self, 
                    data_q, data_o, error_q, 
                    port_num,
                    port_baud,
                    hanover,
                    port_stopbits = serial.STOPBITS_ONE,
                    port_parity   = serial.PARITY_NONE,
                    port_timeout  = 0.01):
        threading.Thread.__init__(self)        
        self.serial_port = None
        self.serial_arg  = dict( port      = port_num,
                                 baudrate  = port_baud,
                                 stopbits  = port_stopbits,
                                 parity    = port_parity,
                                 timeout   = port_timeout)
        self.data_q   = data_q
        self.data_o  = data_o
        self.error_q  = error_q
        self.config=config
        self.alive    = threading.Event()
        self.alive.set()

    def run(self):
        try:
            if self.serial_port: 
                self.serial_port.close()
            self.serial_port = serial.Serial(**self.serial_arg)
            self.serial_port.flushInput()
        except serial.SerialException, e:
            self.error_q.put(e.message)
            return
        logging.info('Iniciando Monitor Configuraciones')            
        self.serial_port.write("Esperando Dato Serial...\n")
        while self.alive.isSet():            
            message=self.serial_port.read(100)
            #print (message,hex)
            if len(message)>0:
                print "recibi dato!!!"
                logging.info("Comando Recibido")
                #message=message.split(' ')
                print message
                self.data_q.put(message)
            outmessage= self.data_o.get()
            if outmessage is not None:                
                self.serial_port.write(outmessage)
        if self.serial_port:
            self.serial_port.close()            
    def join(self, timeout=None):
        self.alive.clear()
        threading.Thread.join(self, timeout)   
    
#------------------------------------------------------------------------------------------  
class ComMonitorThread(threading.Thread):    
    def __init__(   self, 
                    data_q, error_q, 
                    port_num,
                    port_baud,
                    flag,
                    port_stopbits = serial.STOPBITS_ONE,
                    port_parity   = serial.PARITY_NONE,
                    port_timeout  = 0.01):
        threading.Thread.__init__(self)        
        self.serial_port = None
        self.serial_arg  = dict( port      = port_num,
                                 baudrate  = port_baud,
                                 stopbits  = port_stopbits,
                                 parity    = port_parity,
                                 timeout   = port_timeout)
        self.data_q   = data_q
        self.error_q  = error_q
        self.flag= flag
        self.alive    = threading.Event()
        self.alive.set()

    def Show_Data(self, message):     
        numllanta=ord(message[2])
        if (numllanta<=5):
            pressure=message[3]
            pressure=ord(pressure)
            pressure=float(pressure)
            pressure=pressure/0.1818
            pressure=pressure-0.1
            pressure=round(pressure,3)            
            msg_string= ("presion llanta "
            + str(numllanta)
            + ": " + str(pressure)+ " KPa")
            print(msg_string)            
            temp=message[4]
            temp=ord(temp)
            temp=temp-50
            msg_string=( "temperatura llanta "
            + str(numllanta) + ": "
            + str(temp)+ chr(186) + "C")
            print(msg_string)
            print("\n")
            return {"llanta":numllanta,"temperatura":temp,"presion":pressure}
        else:
            return None
            pass         
   
    def run(self):
        try:
            if self.serial_port: 
                self.serial_port.close()
            self.serial_port = serial.Serial(**self.serial_arg)
            self.serial_port.flushInput()
        except serial.SerialException, e:
            self.error_q.put(e.message)
            return
        psnInCount=0
        psnOutCount=0        
        logging.info('Iniciando Serial')
        print("iniciando serial")
        startTime = time.time()        
        while self.alive.isSet():
            if (self.flag):                
                message = self.serial_port.read(7)                
                qdata = [0,0,0]
                if len(message) >= 7:                    
                    logging.info('Dato Serial Valido Registrado')                    
                    timestamp = time.time() - startTime
                    sensordata=self.Show_Data(message)
                    if sensordata is not None:
                        qdata[0]=sensordata['llanta']
                        qdata[1]=sensordata['temperatura']
                        qdata[2]=sensordata['presion']
                        timestamp = time.clock()
                        self.data_q.put((qdata, timestamp))
                        time.sleep(2)
                else:
                    if(message!=''):                    
                        logging.warning('Dato Serial corrupto')                        
                        message=''  
        if self.serial_port:
            self.serial_port.close()    

    def join(self, timeout=None):
        self.alive.clear()
        threading.Thread.join(self, timeout)
#------------------------------------------------------------------------------------------

