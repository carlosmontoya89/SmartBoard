import Queue
from ConfigParser import SafeConfigParser
import time
from com_monitor import ComMonitorThread
from com_monitor import UsbMonitorThread
from com_monitor import weigthMonitor
import configuration as monitor
import logging
import schedule
import ManejoBD
import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BOARD)
dbname='home/pi/sensorLog.sqlite'
config = SafeConfigParser()
data_q=''
data_u=''
data_w=''
#---------------------------------------------------------
def saving_flag2():
        saving_flag(" ")
def saving_flag(channel):        
        global saveflag
        saveflag=True
def read_serial_data(data_q,flag):        
        qdata = list(get_all_from_queue(data_q))
        if len(qdata) > 0:
                data = dict(timestamp=qdata[-1][1], 
                Llanta=qdata[-1][0][0],
                Presion=qdata[-1][0][1],
                Temperatura=qdata[-1][0][2],                               
                )
                print data
                logging.info('Guardando Datos Serial en Base de Datos')
                ManejoBD.insertTpms(data['Llanta'],data['Presion'],data['Temperatura'])

def read_weight_data(data_w,weigthflag):
        qdata = list(get_all_from_queue(data_w))
        if len(qdata) > 0:
                data=dict(timestamp=qdata[-1][1],
                weigth=qdata[-1][0][0],
                sensorid=qdata[-1][0][1],
                firmware=qdata[-1][0][2],
                )
                print(data)
                logging.info('Guardando Datos Peso en Base de Datos')
                ManejoBD.insertWeight(data['sensorid'],data['weigth'],data['firmware'])
                        
def read_usb_data(data_u,flag):        
        qdata = list(get_all_from_queue(data_u))
        if len(qdata) > 0:
                data = dict(timestamp=qdata[-1][1], 
                psnin=qdata[-1][0][0],
                psnout=qdata[-1][0][1],
                psninCount=qdata[-1][0][2],
                psnoutCount=qdata[-1][0][3],
                 )
                print data
                logging.info('Guardando Datos Usb-Serial en Base de Datos')
                ManejoBD.insertIrma3D(data['psnin'],data['psnout'],data['psninCount'],data['psnoutCount'])                
        
def get_all_from_queue(Q):            
        try:
                while True:
                        yield Q.get_nowait( )
        except Queue.Empty:
                raise StopIteration

def get_item_from_queue(Q, timeout=0.01):   
        try: 
                item = Q.get(True, 0.01)
        except Queue.Empty:        
                return None
        return item

def main():
        time.sleep(10)
        Irma3Dflag=False
        tpmsflag = False
        counter=0
        gpsflag= False
        weigthflag=False
        inflag=False
        lasttiempo=0
        global saveflag
        saveflag=False
        logging.basicConfig(filename='home/pi/report.log', level=logging.DEBUG,
                format='%(levelname)s:(%(threadName)-10s) %(asctime)s %(message)s')
        config.read("/home/pi/config.ini")                 
        for section in config.sections():
                if(config.has_option(section,'sensorname')): 
                        if ((config.get(section,'sensorname')=='tpms')
                            and (config.getboolean(section,'connected'))):                                
                                tpmsflag = True
                                baudrate =config.getint(section,'baudrate')
                                print baudrate
                                port   = config.get(section, 'port')
                                data_q      =  Queue.Queue()
                                error_q     =  Queue.Queue()
                                sensor_name = config.get(section,'sensorname')
                                com_monitor =  ComMonitorThread(
                                                    data_q,
                                                    error_q,
                                                    port,
                                                    baudrate,
                                                    tpmsflag)               
                                logging.info('Iniciando puerto Serial')
                                com_monitor.start()
                                com_error = get_item_from_queue(error_q)
                                if com_error is not None:                        
                                        logging.critical('ComMonitorThread error')
                                        print com_error
                                        com_monitor = None

                        if ((config.get(section,'sensorname')=='weight')
                            and (config.getboolean(section,'connected'))):                                
                                weigthflag = True
                                baudrate =config.getint(section,'baudrate')
                                print baudrate
                                port   = config.get(section, 'port')
                                data_w      =  Queue.Queue()
                                error_w     =  Queue.Queue()
                                sensor_name = config.get(section,'sensorname')
                                com_monitor =  weigthMonitor(
                                                    data_w,
                                                    error_w,
                                                    port,
                                                    baudrate,
                                                    weigthflag)               
                                logging.info('Iniciando puerto Serial')
                                com_monitor.start()
                                com_error = get_item_from_queue(error_w)
                                if com_error is not None:                        
                                        logging.critical('weigthThread error')
                                        print com_error
                                        com_monitor = None
                                        
                        if ((config.get(section,'sensorname')=='hanover')
                            and(config.getboolean(section,'connected'))):
                                hanover=True
                                baudrate =config.getint(section,'baudrate')
                                port   = config.get(section, 'port')
                                data_z     =  Queue.Queue()
                                error_z     =  Queue.Queue()
                                sensor_name = config.get(section,'sensorname')                
                                hanover_monitor =  HanoverSignController(
                                                    data_z,
                                                    error_z,
                                                    port,
                                                    baudrate,
                                                    hanover)               
                                logging.info('Iniciando Hanover Service')
                                usb_monitor.start()  
                                usb_error = get_item_from_queue(error_z)
                                if usb_error is not None:                        
                                        logging.critical('Hanover Thread error')
                                        print usb_error
                                        usb_monitor = None

                                        
                        if ((config.get(section,'sensorname')=='Irma3D')
                            and(config.getboolean(section,'connected'))):
                                Irma3Dflag=True
                                baudrate =config.getint(section,'baudrate')
                                port   = config.get(section, 'port')
                                data_u     =  Queue.Queue()
                                error_u     =  Queue.Queue()
                                sensor_name = config.get(section,'sensorname')                
                                usb_monitor =  UsbMonitorThread(
                                                    data_u,
                                                    error_u,
                                                    port,
                                                    baudrate,
                                                    Irma3Dflag)               
                                logging.info('Iniciando puerto USB Serial')
                                usb_monitor.start()  
                                usb_error = get_item_from_queue(error_u)
                                if usb_error is not None:                        
                                        logging.critical('USBMonitorThread error')
                                        print usb_error
                                        usb_monitor = None
                                        
        while True:
                if (config.getboolean('reportmethod','time')):                        
                        tiempo=config.getint('reportmethod','reportime')
                        if (inflag):
                            GPIO.cleanup()
                            inflag=False
                            counter=0
                        if (tiempo!=lasttiempo):
                                try:
                                        schedule.every(tiempo).minutes.do(saving_flag2)
                                except Exception as e:
                                        print(e)
                                print("siguiente ejecucion en: "+str(tiempo))
                                lasttiempo=tiempo
                        try:
                                schedule.run_pending()
                        except Exception as e:
                                print(e)
                        time.sleep(1)
                elif (config.getboolean('reportmethod','input')):
                        try:
                                for section in config.sections():                                
                                        if(config.has_option(section,'sensorname')):                                    
                                                if ((config.get(section,'sensorname')=='report')
                                                  and (config.getboolean(section,'connected'))):                                       
                                                        puerto=config.getint(section,'port')
                                        #print(puerto)
                        except Exception as e:
                                print(e)
                        if (counter==0):
                                try:
                                        GPIO.setmode(GPIO.BOARD)
                                        GPIO.setup(puerto, GPIO.IN, pull_up_down = GPIO.PUD_DOWN)
                                        GPIO.add_event_detect(puerto, GPIO.RISING, callback=saving_flag, bouncetime=300)
                                        inflag=True
                                        counter=counter+1
                                except Exception as e:
                                        print(e)
                if (gpsflag):
                        out_msg=configuration.read_serial_data(data_g,config)
                        if out_msg is not None:                                
                                data_o.put(out_msg)                        
                if (Irma3Dflag):
                        if (saveflag):  
                                read_usb_data(data_u,Irma3Dflag)
                if(weigthflag):
                        if (saveflag):  
                                read_weight_data(data_w,weigthflag)                
                if (tpmsflag):                        
                        if (saveflag):                                
                                read_serial_data(data_q,tpmsflag)
                                saveflag=False
                            

if __name__ == "__main__":
    main()
    
    


