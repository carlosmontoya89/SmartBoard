from ConfigParser import SafeConfigParser
from com_monitor import configurationMonitor
import string
import serial
import select
from xmodem import XMODEM
import Queue, threading, time
import ManejoBD as bd
import logging
import modulosSmartBoard as module
import platform
import schedule
import os
import sys
import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BOARD)
config = SafeConfigParser()
##        #el formato del mensaje debe ser
##        #at!SMAPP add port=uartserial;baudrate=9600;name=sensorname;
#---------------------------------------------------------------------------------------------------        
def get_all_from_queue(Q):
    try:
        while True:
            yield Q.get_nowait( )
    except Queue.Empty:
        raise StopIteration
#---------------------------------------------------------------------------------------------------
def get_item_from_queue(Q,timeout=0.01):   
    try: 
        item = Q.get(True, 0.01)
    except Queue.Empty:        
        return None    
    return item
#---------------------------------------------------------------------------------------------------
def getc(size, timeout=3):
        w,t,f = select.select([ser], [], [], timeout)
        if w:
            data = ser.read(size)
        else:
            data = None
  
        print 'getc(', repr(data), ')'
        return data
  
def putc(data, timeout=3):
    w,t,f = select.select([], [ser], [], timeout)
    if t:
        ser.write(data)
        ser.flush()
        size = len(data)
    else:
        size = None

    print 'putc(', repr(data), repr(size), ')'
    return size
#---------------------------------------------------------------------------------------------------
def read_db_data():
    config.read("/home/pi/config.ini")
    irmatrama=None
    tpmstrama=None
    weighttrama=None
    for section in config.sections():
        if(config.has_option(section,'sensorname')):
            if ((config.get(section,'sensorname')=='Irma3D')
                    and (config.getboolean(section,'connected'))):
                irmaval=bd.selectIrma3D()            
                if irmaval is not None:        
                    irmatrama= ('I,'
                    + str(irmaval['psnin'])
                    + ','+ str(irmaval['psnout'])
                    + ','+str(irmaval['psnintot'])
                    + ','+str(irmaval['psnouttot']))
                    logging.info('trama irma creada')
                    ID = irmaval['_ID']
                    bd.updateSendIrma(ID)                
            if ((config.get(section,'sensorname')=='tpms')
                    and (config.getboolean(section,'connected'))):            
                tpmsval=bd.selectTpms()            
                if tpmsval is not None:                               
                    tpmstrama=('T,'+ str(tpmsval['tire'])
                               + ','+ str(tpmsval['temperatura'])
                               + ','+ str(tpmsval['presion']))
                    logging.info('trama tpms creada')
                    ID = tpmsval['_ID']
                    bd.updateSendTpms(ID)
            if ((config.get(section,'sensorname')=='weight')
                    and (config.getboolean(section,'connected'))):            
                weightval=bd.selectWeight()           
                if weightval is not None:                               
                    weighttrama=('W,'+ str(weightval['sensorid'])
                               + ','+ str(weightval['weight'])
                               )
                    logging.info('trama weight creada')
                    ID = weightval['_ID']
                    bd.updateSendWeight(ID)
             
            if ((config.get(section,'sensorname')=='hanover')
                

                
    return irmatrama, tpmstrama, weighttrama   
   
def read_serial_data(data_q,config):        
        data_o= None
        flagfirst=False
        flag=False
        logging.info("Leyendo Dato Serial")
        message = get_item_from_queue(data_q)        
        if message is not None:
            #print message
            header, command, payload, data_o=module.messageSpliter(message)
            #print(data_o)
            if 'fileready' in data_o:
                data_o=data_o
                flagfirst=command
                pass
            elif 'xmodem' in data_o:
                pass
            else:
                    flag, data_o=module.headerChecker(header)
                    print("este es")
                    print(data_o)
                    if flag:                
                        data_o,flagfirst=module.commandParser(command, payload)
                        print("aqui es")
                        print(data_o)            
        return data_o, flagfirst                
#---------------------------------------------------------------------------------------------------       
def main():    
    data_q=''
    data_o=''
    path=os.path.dirname(os.path.abspath(__file__))
    file_name=path+'/report.log'
    logging.basicConfig(filename=file_name,
            level=logging.DEBUG,
            format='%(levelname)s:(%(threadName)-10s) %(asctime)s %(message)s')
    conf_name=path+'/config.ini'
    config.read(conf_name)
    for section in config.sections():
        for name,value in config.items(section):        
            if (value.lower()=="gps_unit"):
                baudrate =config.getint(section,'baudrate')
                port   = config.get(section, 'port')
                data_q      =  Queue.Queue()
                data_o      =  Queue.Queue()
                error_q     =  Queue.Queue()
                sensor_name = config.get(section,'sensorname')
                com_monitor =  configurationMonitor(
                                    data_q,
                                    data_o,
                                    error_q,
                                    port,
                                    baudrate,
                                    config)                            
                logging.info('Iniciando puerto Serial')
                com_monitor.start()
                com_error = get_item_from_queue(error_q)
                if com_error is not None:                        
                        logging.critical('ComMonitorThread error')
                        print com_error
                        com_monitor = None
    while True:                    
        out_msg,flagfirst=read_serial_data(data_q,config)
        if out_msg is not None:
            #print out_msg
            if 'xmodem' in out_msg:
                data_o.put("AT!GXDIAG CHECKAPPFILE\r\n")
                out_msg=''
            if 'fileready' in out_msg:
                data_o.put('AT!GXDIAG GETAPPFILE\r\n')
                time.sleep(10)
                print 'envialo ya'
                time.sleep(20)
                print os.system('/usr/bin/python /home/pi/Documents/test-recv.py %s'%flagfirst)                 
                print flagfirst
                print 'envio el archivo'                
                out_msg=''
                #com_monitor.stop()
##                ser = serial.Serial(port, 115200)
##                xmodem = XMODEM(getc, putc)
##                pathfile='/home/pi/'+flagfirst
##                stream=open(pathfile,'wb')
##                nbytes = xmodem.recv(stream, retry=8) 
##                print >> sys.stderr, 'received', nbytes, 'bytes'    
##                stream.close()
##                ser.close()
        #call function to recieve through xmodem.      
        data_o.put(out_msg)                    
        irmatrama, tpmstrama,weighttrama=read_db_data()
        if irmatrama is not None:
            print irmatrama
            data_o.put(irmatrama)
        if tpmstrama is not None:
            print tpmstrama
            data_o.put(tpmstrama)
        if weighttrama is not None:
            print weighttrama
            data_o.put(weighttrama)                    
#---------------------------------------------------------------------------------------------------
if __name__ == "__main__":
    main()   

