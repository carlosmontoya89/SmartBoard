#!/usr/bin/python

from __future__ import absolute_import, print_function, unicode_literals

from optparse import OptionParser, make_option 
from ConfigParser import SafeConfigParser
from configuration import read_db_data
import modulosSmartBoard as module
import Queue, time
import logging
import sys
import select
import platform
import schedule
import os
import sys
import socket
import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BOARD)
import uuid
import dbus
import dbus.service
import dbus.mainloop.glib
try:
  from gi.repository import GObject
except ImportError:
  import gobject as GObject
config = SafeConfigParser()
config.read("config.ini")
message=None
logging.basicConfig(filename='report.log',
                    level=logging.DEBUG,
                    format='%(levelname)s:(%(threadName)-10s) %(asctime)s %(message)s')
def configureinput(channel):    
    config.set('reportmethod','time','True')
    config.set('reportmethod','command','false')
    config.set('reportmethod','input','false')
    time=config.getint('reportmethod','reportime')
    with open('config.ini','wb') as configfile:
        config.write(configfile)
        print ("configurado ok")
        
def sendbluetooth2():
    sendbluetooth(" ")

def sendbluetooth(channel):
    global outtrama
    outtrama=""
    if config.has_option('boardinfo','alias'):
        smAlias=config.get('boardinfo','alias')
    else:
        smAlias=None
    try:
       irmatrama, tpmstrama, weighttrama=read_db_data()
    except Exception as e:
        print(e)
        pass
    print(smAlias)
    if smAlias is None:
        smName=platform.node()                            
    else:
        smName=smAlias
        print (smName)                        
    if tpmstrama is not None:    
        if outtrama is not "":              
            outtrama=outtrama+";" +tpmstrama
        else:
            outtrama=smName+";"+outtrama+tpmstrama             
                                  
    if irmatrama is not None:        
        if outtrama is not "":              
              outtrama=outtrama+";" +irmatrama
        else:
              outtrama=smName+";"+outtrama+irmatrama

    if weighttrama is not None:        
        if outtrama is not "":              
              outtrama=outtrama+";" + weighttrama
        else:
              outtrama=smName+";"+outtrama+weighttrama
     
       
class Profile(dbus.service.Object):
    fd = -1
    @dbus.service.method("org.bluez.Profile1",
                    in_signature="", out_signature="")
    def Release(self):
        print("Release")
        logging.info("Release")        
        mainloop.quit()

    @dbus.service.method("org.bluez.Profile1",
                    in_signature="", out_signature="")
    def Cancel(self):
        print("Cancel")
        logging.info("Cancel")

    @dbus.service.method("org.bluez.Profile1",
                in_signature="oha{sv}", out_signature="")
    def NewConnection(self, path, fd, properties):
        flagfirst=True
        inflag=False
        flag=True
        global outtrama
        outtrama=""
        lasttiempo=0
        begin=time.time()
        timeout=4
        self.fd = fd.take()
        print("Nueva Conexion (%s, %d)" % (path, self.fd))
        logging.info("N (%s, %d)" % (path, self.fd))
        server_sock = socket.fromfd(self.fd, socket.AF_UNIX, socket.SOCK_STREAM)
        server_sock.send("Bluetooth Comunication \n ")
        logging.info("Inicio de la comunicacion Bluetooth \n")
        try:
            while True:                
                try:
                    ready = select.select([server_sock], [], [], 5)
                except Exception as e:
                    print (e)               
                if ready[0]:
                    message = server_sock.recv(1024)
                else:
                    message=None           
                if message is not None:
                    message=message.split(' ')
                    print("recibido: %s" % message)
                    try:
                        header=message[0]                    
                        header=header.lower()
                        if message[1]:
                            command=message[1]                    
                            command=command.lower()
                        if (message[2]):
                            payload=message[2]                            
                    except Exception as e:
                        payload=""
                        pass
                    if 'at!smapp' in header:
                        print ("comando es de configuracion")
                        logging.info("Comando es de Configuracion")
                        try:
                            server_sock.send('OK \n')
                                                      
                        except Exception as e:
                                logging.error(e)                                
                                server_sock.send("Dato Erroneo\n")
                                print (e)
                                pass
                        if 'add' in command: 
                            try:
                                payload=message[2]                
                                payload=payload.lower() 
                                payload=payload.split(';')
                                dicPayload=dict(map(str, x.split('=')) for x in payload)
                                port=dicPayload['port']                    
                                logging.info("Comando Configuracion Correcto")                                      
                                if 'serial' in port:                            
                                    logging.info("Es un puerto serial")
                                    config.set(dicPayload['port'],'baudrate',dicPayload['baudrate'])
                                    config.set(dicPayload['port'],'sensorname',dicPayload['name'])
                                    config.set(dicPayload['port'],'connected','true')
                                    with open('config.ini','wb') as configfile:
                                        config.write(configfile)
                                        data_o="Sensor Configurado OK \n"
                                        server_sock.send(data_o)
                                        logging.info(data_o)
                                if 'port' in port:
                                    logging.info("Es un GPIO")
                                    config.set(dicPayload['port'],'type',dicPayload['type'])
                                    config.set(dicPayload['port'],'port',dicPayload['port'])
                                    config.set(dicPayload['port'],'sensorname',dicPayload['name'])
                                    config.set(dicPayload['port'],'connected','true')
                                    with open('config.ini','wb') as configfile:
                                        config.write(configfile)                            
                                        data_o="Sensor Configurado OK \n"
                                        server_sock.send(data_o)
                                        logging.info(data_o)                
                            except Exception as e:
                                logging.error(e)
                                print (e)
                                data_o="Sensor No Configurado \n"
                                server_sock.send(data_o)
                                pass                            
                        elif 'del' in command:
                            try:
                                payload=message[2]                
                                payload=payload.lower() 
                                payload=payload.split(';')
                                dicPayload=dict(map(str, x.split('=')) for x in payload)
                                config.set(dicPayload['port'],'connected','false')
                                with open('config.ini','wb') as configfile:
                                        config.write(configfile)
                                data_o="Sensor Desactivado OK \n"
                                server_sock.send(data_o)
                                print(data_o)
                                logging.info(data_o)
                            except Exception as e:
                                logging.error(e)
                                server_sock.send("Error \n")
                                pass
                        elif 'reptype' in command:
                            payload=message[2]                
                            payload=payload.lower() 
                            payload=payload.split(';')
                            print (payload[0])                         
                            if 'time' in payload[0]:
                                try:
                                    dicPayload=payload[1]
                                    config.set('reportmethod',payload[0],'True')
                                    config.set('reportmethod','reportime',payload[1])
                                    config.set('reportmethod','command','false')
                                    config.set('reportmethod','input','false')
                                    config.set('reportmethod','flag','false')
                                except Exception as e:
                                    print(e)
                                    logging.error(e)
                                    pass   
                            elif 'command' in payload[0]:
                                config.set('reportmethod',payload[0],'True')
                                config.set('reportmethod','input','false')
                                config.set('reportmethod','time','false')
                                config.set('reportmethod','flag','false')
                            elif 'input' in payload[0]:
                                config.set('reportmethod',payload[0],'True')
                                config.set('reportmethod','command','false')
                                config.set('reportmethod','time','false')
                                config.set('reportmethod','flag','true')
                                flagfirst=True
                            else:
                                print ("comando incorrecto")
                            with open('config.ini','wb') as configfile:
                                config.write(configfile)
                        elif 'sensors' in command:
                            mensaje=""
                            mensaje2=""
                            try:
                                sensorname,port=module.returnSensorConfig()                                
                                for i in range(len(sensorname)):#and (j in port):
                                    mensaje+=(str(sensorname[i])+", ")
                                    mensaje+=(str(port[i])+"<br>")
                                    mensaje2+=(str(sensorname[i])+", ")
                                    mensaje2+=(str(port[i])+"\n")
                            except Exception as e:
                                print(e)
                            if "replyto" in payload:
                                if payload=='replytome':
                                    server_sock.send(mensaje2)                                    
                                else:                                    
                                    destinatario=message[3]
                                    print(destinatario)                                    
                                    try:                                       
                                        outmsg=module.sendMail(destinatario,mensaje)                                        
                                    except exception as e:
                                        print(e)
                            else:
                                server_sock.send(mensaje2)                                          
                                
                        elif 'boardinfo' in command:                            
                            serial,smName,smAlias=module.returnBoardInfo()
                            mensaje=serial+"\n"+smName+"\n"+smAlias+"\n"
                            mensaje2=serial+"<br>"+smName+"<br>"+smAlias+"<br>"
                            if "replyto" in payload:
                                if payload=='replytome':
                                    server_sock.send(mensaje)
                                else:                                    
                                    destinatario=message[3]                                   
                                    try:                                       
                                        outmsg=module.sendMail(destinatario,mensaje2)                                        
                                    except exception as e:
                                        print(e)
                            else:
                                server_sock.send(mensaje)                                       
                        elif 'firmware' in command:
                            print("entro aqui")
                            try:
                                if 'weight' in payload:
                                    weightlast=module.firmware()
                                    #mensaje=weightlast+"<br>"
                                    mensaje=weightlast+"\n"                                    
                                    server_sock.send(mensaje)
                            except Exception as e:
                                print (e)
                        elif 'lastreading' in command:
                            try:
                                irmalast,tpmslast,weightlast=module.lastReading()
                                mensaje=irmalast+"<br>"+tpmslast+"<br>"+weightlast+"<br>"
                                mensaje2=irmalast+"\n"+tpmslast+"\n"+weightlast+"\n"
                            except Exception as e:
                                print (e)
                            if "replyto" in payload:
                                if payload=='replytome':
                                    server_sock.send(mensaje2)
                                else:                                    
                                    destinatario=message[3]                                   
                                    try:                                       
                                        outmsg=module.sendMail(destinatario,mensaje)                                        
                                    except exception as e:
                                        print(e)
                            else:
                                server_sock.send(mensaje2)                                        
                                
                        elif 'outputconfig' in command:
                            try:
                               reportmethod=module.outputConfig()                               
                            except Exception as e:
                                print (e)
                            if "replyto" in payload:
                                if payload=='replytome':
                                    server_sock.send(reportmethod +"\n")
                                else:                                    
                                    destinatario=message[3]                                   
                                    try:                                       
                                        outmsg=module.sendMail(destinatario,reportmethod)                                        
                                    except exception as e:
                                        print(e)
                            else:
                                server_sock.send(reportmethod)                          
                        else:
                            try:
                                print ("Dato no es correcto intente de nuevo")
                                data_o="Comando Incorrecto \n"
                                server_sock.send(data_o)
                                logging.info(data_o)
                            except Exception as e:
                                print(e)                            
                        logging.info("received: %s" % message)
                        #server_sock.send("looping back: %s\n" % message)                  
                else:
                    for section in config.sections():                                
                        if(config.has_option(section,'sensorname')): 
                            if ((config.get(section,'sensorname')=='input')
                                    and (config.getboolean(section,'connected'))):
                                port=config.getint(section,'port')
                                if(flag):                                    
                                    try:
                                        GPIO.setmode(GPIO.BOARD)
                                        GPIO.setup(port, GPIO.IN, pull_up_down = GPIO.PUD_DOWN)
                                        GPIO.add_event_detect(port, GPIO.RISING, callback=configureinput, bouncetime=300)
                                        flag=False
                                    except Exception as e:
                                        print(e)
                                        
                    if (config.getboolean('reportmethod','time')):                        
                        tiempo=config.getint('reportmethod','reportime')
                        if (inflag):
                            GPIO.cleanup()
                            inflag=False                                                
                        try:                         
                            if (tiempo!=lasttiempo):                                
                                try:
                                    schedule.every(tiempo).minutes.do(sendbluetooth2)
                                except Exception as e:
                                    print(e)
                                print("\n siguiente ejecucion en: "+str(tiempo)+"\n")
                                lasttiempo=tiempo
                        except Exception as e:
                            print(e)                    
                        try:
                            schedule.run_pending()
                        except Exception as e:
                            print(e)
                        time.sleep(1)                        
                        try:
                            if outtrama is not "":
                                print(outtrama)
                                server_sock.send(outtrama)
                                server_sock.send("\n")
                                outtrama=""
                        except Exception as e:
                            print(e)                    
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
                        #print (flagfirst)
                        if (flagfirst):
                            try:
                                GPIO.setmode(GPIO.BOARD)
                                GPIO.setup(puerto, GPIO.IN, pull_up_down = GPIO.PUD_DOWN)
                                GPIO.add_event_detect(puerto, GPIO.RISING, callback=sendbluetooth, bouncetime=300)
                                inflag=True
                            except Exception as e:
                                print(e)
                            flagfirst=False
                        try:
                            if outtrama is not "":
                                print(outtrama)
                                server_sock.send(outtrama)
                                server_sock.send("\n")
                                outtrama=""
                        except Exception as e:
                            print(e)
                    
        except IOError:
            logging.info("Error")
            pass

        server_sock.close()
        print("all done")
        logging.info("All Done")

    @dbus.service.method("org.bluez.Profile1",
                in_signature="o", out_signature="")
    def RequestDisconnection(self, path):
        print("RequestDisconnection(%s)" % (path))
        logging.info("RequestDisconnection(%s)" % (path))
        if (self.fd > 0):
            os.close(self.fd)
            self.fd = -1

if __name__ == '__main__':
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

    bus = dbus.SystemBus()

    manager = dbus.Interface(bus.get_object("org.bluez",
                "/org/bluez"), "org.bluez.ProfileManager1")

    option_list = [
            make_option("-C", "--channel", action="store",
                    type="int", dest="channel",
                    default=None),
            ]

    parser = OptionParser(option_list=option_list)

    (options, args) = parser.parse_args()

    options.uuid = "1101"
    options.psm = "3"
    options.role = "server"
    options.name = "SmartBoard"
    options.service = "smartboard comunication"
    options.path = "/foo/bar/profile"
    options.auto_connect = False
    options.record = ""

    profile = Profile(bus, options.path)

    mainloop = GObject.MainLoop()

    opts = {
            "AutoConnect" : options.auto_connect,
        }

    if (options.name):
        opts["Name"] = options.name

    if (options.role):
        opts["Role"] = options.role

    if (options.psm is not None):
        opts["PSM"] = dbus.UInt16(options.psm)

    if (options.channel is not None):
        opts["Channel"] = dbus.UInt16(options.channel)

    if (options.record):
        opts["ServiceRecord"] = options.record

    if (options.service):
        opts["Service"] = options.service

    if not options.uuid:
        options.uuid = str(uuid.uuid4())

    manager.RegisterProfile(options.path, options.uuid, opts)
    logging.info("Iniciando el bluetooth")
    mainloop.run()

