import Queue, threading, time, serial
import logging

lock = threading.Lock()

class ComMonitorThread(threading.Thread):
    
    def __init__(   self, 
                    data_q, data_o, error_q, 
                    port_num,
                    port_baud,
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
        self.data_o  = data_o
        
        self.alive    = threading.Event()
        self.alive.set()
    #------------------------------------------------------
    def Show_Data(self, message):        
        pressure=message[4]
        #print (pressure,hex)
        pressure=ord(pressure)
        #print pressure
        pressure=float(pressure)
        pressure=pressure*3.44
        #pressure=pressure-0.1
        pressure=round(pressure,3)
        numllanta=ord(message[3])
        #print numllanta
        #print numllanta
        if numllanta==16:
            numllanta=2
        if numllanta==17:
            numllanta=3
        numllanta=numllanta+1
        msg_string= "presion llanta " + str(numllanta) + ": " + str(pressure)+ " KPa"
        #print(msg_string)
        #print("\n")
        temp=message[5]
        #print (temp,hex)
        temp=ord(temp)
        #print temp
        temp=temp-50
        msg_string= "temperatura llanta " + str(numllanta) + ": " + str(temp)+ chr(186) + "C"
        #print(msg_string)
        #print("\n")
        return {"llanta":numllanta,"temperatura":temp,"presion":pressure}
        
    def run(self):
        try:
            if self.serial_port: 
                self.serial_port.close()
            self.serial_port = serial.Serial(**self.serial_arg)
            self.serial_port.flushInput()
        except serial.SerialException, e:
            self.error_q.put(e.message)
            return
        logging.basicConfig(filename='report.log',level=logging.DEBUG, format='%(levelname)s:(%(threadName)-10s) %(asctime)s %(message)s')
        # Restart the clock
        logging.info('Iniciando')
        #self.serial_port.write("Esperando Dato Serial...\n")
        startTime = time.time()
##        while self.alive.isSet():                            
##            message = self.serial_port.read(20)
##            #print message
##            qdata = [0,0,0]
##            if len(message) >= 4:                    
##                logging.info('Dato Serial Valido Registrado')
##                print message
##                timestamp = time.time() - startTime
##                sensordata=self.Show_Data(message)
##                if sensordata is not None:
##                    qdata[0]=sensordata['llanta']
##                    qdata[1]=sensordata['temperatura']
##                    qdata[2]=sensordata['presion']
##                    timestamp = time.clock()
##                    self.data_q.put((qdata, timestamp))
##                    time.sleep(2)
##            else:
##                if(message!=''):                    
##                    logging.warning('Dato Serial corrupto')                        
##                    message=''  
        while self.alive.isSet():            
            #message=self.serial_port.read(100)
            #print "aqui llego"            
            #if len(message)>0:
                #print "recibi dato!!!"
                #logging.info("Comando Recibido")
                #message=message.split(' ')
                #print map(ord,list(message))
                #print int(map(ord,list(message)),16)
                #print (message[0]),(message[1]),(message[2]),ord(message[3]),message[4],message[5],message[6]
                #self.data_q.put(message)
            outmessage= self.data_o.get()
            if outmessage is not None:                
                self.serial_port.write(outmessage)
                print "comando enviado"
                logging.info("Comando Enviado")
        
        if self.serial_port:
            self.serial_port.close()
    

    def join(self, timeout=None):
        self.alive.clear()
        threading.Thread.join(self, timeout)


