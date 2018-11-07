from ConfigParser import SafeConfigParser
#from configuration import read_db_data
import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BOARD)
import schedule
import platform
import sendgrid
#from sendgrid import *
import os
from sendgrid.helpers.mail import *
import smtplib 
import logging
import ManejoBD as bd
config = SafeConfigParser()
config.read("/home/pi/config.ini")
message=None
path=os.path.dirname(os.path.abspath(__file__))
file_name=path+'/report.log'
logging.basicConfig(filename=file_name,
                    level=logging.DEBUG,
                    format='%(levelname)s:(%(threadName)-10s) %(asctime)s %(message)s')
 
def messageSpliter(message):
    payload=None
    data_o=''
    command=''
    header=''
    try:
        message=message.split(' ')
        print(message)
        print(len(message))
        if len(message)==1:            
            if 'xmodem' in message[0]:
                data_o=message[0]
                pass
        elif len(message)<7:
            header=message[0]                    
            header=header.lower()
            command=message[1]                    
            command=command.lower()        
            if (message[2]):
                payload=message[2]
                payload=payload.lower()
            else:
                payload=""
            data_o="OK \n"
            print(payload)
        else:
            rcv=message[0]
            rcv=rcv.split(';')            
            header=rcv[0]
            if(rcv[1]):
                command=rcv[1]
                data_o='fileready'              
    except Exception as e:
        data_o="Comando Incorrecto \n"              
        pass
    return header, command, payload, data_o

def headerChecker(header):
    if 'at!smapp' in header:
        print ("comando es de configuracion")
        logging.info("Comando es de Configuracion")
        data_o='OK \n'
        flag=True
    else:
        print ("Dato no es correcto intente de nuevo")
        data_o="Comando Incorrecto \n"
        logging.info(data_o)
        flag=False
    return flag, data_o
        
def saveConfigFile(config):
    with open('/home/pi/config.ini','wb') as configfile:
        config.write(configfile)
        data_o="Sensor Configurado OK \n"                
        logging.info(data_o)
        return data_o
                
def payloadSpliter(payload):
    payload=payload.split(';')
    dicPayload=dict(map(str, x.split('=')) for x in payload)
    return dicPayload

def returnBoardInfo():
    config.read("/home/pi/config.ini")
    smName=platform.node()
    serial=config.get('boardinfo','serialnum')
    if config.has_option('boardinfo','alias'):
        smAlias=config.get('boardinfo','alias')
    else:
        smAlias=""    
    return serial,smName,smAlias
    
def outputConfig():
    config.read("/home/pi/config.ini")
    if(config.getboolean('reportmethod','time')):
       reportmethod="time: "+str(config.getint('reportmethod','reportime'))       
    elif(config.getboolean('reportmethod','input')):
        for section in config.sections():
            if(config.has_option(section,'sensorname')
                  and config.has_option(section,'connected')):
                if ((config.get(section,'sensorname')=='report')
                        and (config.getboolean(section,'connected'))):     
                    reportmethod="input, "+str(section)
    return reportmethod

def sendMail(destinatario,mensaje):
    try:
        smName=platform.node()    
        remitente = "%s@smartboard.info"%(smName)    
        sg = sendgrid.SendGridAPIClient(apikey="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")
        from_email = Email(remitente)
        subject = "info From SmartBoard!"
        to_email = Email(destinatario)
        msg="<html><body>%s</body></html>"%(mensaje)
        content = Content("text/html", msg)
        mail = Mail(from_email, subject, to_email, content)    
        response = sg.client.mail.send.post(request_body=mail.get())
    except Exception as e:
        print(e)
    print(response.status_code)

def firmware():    
    try:
        config.read("/home/pi/config.ini")
        weightlast=""
        for section in config.sections():
            if(config.has_option(section,'sensorname')):
                if ((config.get(section,'sensorname')=='weight')
                        and (config.getboolean(section,'connected'))):
                    try:
                        lastweight=bd.selectlastWeight()
                    except Exception as e:
                        print (e)                    
                    weightlast="weight firmware: "+str(lastweight['FIRMWARE'])                    
    except Exception as e:
        print (e)
    return weightlast
    
def lastReading():
    config.read("/home/pi/config.ini")
    irmalast=""
    tpmslast=""
    weightlast=""
    for section in config.sections():
        if(config.has_option(section,'sensorname')):
            if ((config.get(section,'sensorname')=='Irma3D')
                    and (config.getboolean(section,'connected'))):                    
                lastirma=bd.selectlastIrma()                
                irmalast="Irma3D: "+str(lastirma['TIMESTAMP'])                
            if ((config.get(section,'sensorname')=='tpms')
                    and (config.getboolean(section,'connected'))):
                lasttpms=bd.selectlastTpms()
                tpmslast="tpms: "+str(lasttpms['TIMESTAMP'])
            if ((config.get(section,'sensorname')=='weigth')
                    and (config.getboolean(section,'connected'))):
                lastweight=bd.selectlastWeight()
                weightlast="weight: "+str(lastweight['TIMESTAMP']) 
    return irmalast,tpmslast,weightlast
      
def returnSensorConfig():
    config.read("/home/pi/config.ini")
    sensorname=[]
    port=[]    
    for section in config.sections():
        if(config.has_option(section,'connected')):
            if(config.getboolean(section,'connected')):
                if(config.has_option(section,'sensorname')):
                    sensorname.append(config.get(section,'sensorname'))
                    port.append(section)    
    return sensorname,port
       
def addSensor(payload):
    try:
        config.read("/home/pi/config.ini")
        dicPayload=payloadSpliter(payload)
        port=dicPayload['port']                    
        logging.info("Comando Configuracion Correcto")                                      
        if 'serial' in port:                            
            logging.info("Es un puerto serial")
            config.set(dicPayload['port'],'baudrate',dicPayload['baudrate'])
            config.set(dicPayload['port'],'sensorname',dicPayload['name'])
            config.set(dicPayload['port'],'connected','true')
            data_o=saveConfigFile(config)
        if 'port' in port:
            logging.info("Es un GPIO")
            config.set(dicPayload['port'],'type',dicPayload['type'])
            config.set(dicPayload['port'],'port',dicPayload['port'])
            config.set(dicPayload['port'],'sensorname',dicPayload['name'])
            config.set(dicPayload['port'],'connected','true')
            data_o=saveConfigFile(config)             
    except Exception as e:
        logging.error(e)
        print (e)
        data_o="Sensor No Configurado \n"
        pass
    return data_o
        
def delSensor(payload):
    try:
        config.read("/home/pi/config.ini")
        dicPayload=payloadSpliter(payload)
        config.set(dicPayload['port'],'connected','false')
        data_o=saveConfigFile(config)        
    except Exception as e:
        logging.error(e)        
        data_o="Sensor No Configurado \n"
        pass
    return data_o
    
def inputParser(payload):
    try:
        config.read("/home/pi/config.ini")
        flagfirst=False
        if 'time' in payload[0]:       
            dicPayload=payload[1]        
            config.set('reportmethod',payload[0],'True')
            config.set('reportmethod','reportime',payload[1])
            config.set('reportmethod','command','false')
            config.set('reportmethod','input','false')
            data_o=saveConfigFile(config)          
        elif 'command' in payload[0]:
            config.set('reportmethod',payload[0],'True')
            config.set('reportmethod','input','false')
            config.set('reportmethod','time','false')
            data_o=saveConfigFile(config)
        elif 'input' in payload[0]:
            config.set('reportmethod',payload[0],'True')
            config.set('reportmethod','command','false')
            config.set('reportmethod','time','false')
            flagfirst=True
            data_o=saveConfigFile(config)
        else:
            data_o="comando incorrecto"
            print (data_o)
            logging.info(data_o)
    except Exception as e:
        logging.error(e)
        print (e)
        data_o="Sensor No Configurado \n"
        pass
    return data_o,flagfirst

def commandParser(command, payload):
    flagfirst=False
    if 'add' in command:
        data_o=addSensor(payload) 
    elif 'xmodem' in command:
        data_o='xmodem' 
    elif 'del' in command:
        data_o=delSensor(payload)
    elif 'reptype' in command:                            
        payload=payload.split(';')
        print (payload[0])
        data_o,flagfirst=inputParser(payload)
    elif 'sensors' in command:
        mensaje=""
        mensaje2=""
        try:
            sensorname,port=returnSensorConfig()                                
            for i in range(len(sensorname)):#and (j in port):
                mensaje+=(str(sensorname[i])+", ")
                mensaje+=(str(port[i])+"<br>")
                mensaje2+=(str(sensorname[i])+", ")
                mensaje2+=(str(port[i])+"\n")
        except Exception as e:
            print(e)
        if "replyto" in payload:
            if payload=='replytome':
                data_o=mensaje2                                   
            else:                                    
                destinatario=message[3]
                print(destinatario)                                    
                try:                                       
                    outmsg=sendMail(destinatario,mensaje)                                        
                except exception as e:
                    print(e)
        else:
            data_o=mensaje2
    elif 'boardinfo' in command:                            
        serial,smName,smAlias=returnBoardInfo()
        mensaje=serial+"\n"+smName+"\n"+smAlias+"\n"
        mensaje2=serial+"<br>"+smName+"<br>"+smAlias+"<br>"
        if "replyto" in payload:
            if payload=='replytome':
                data_o=mensaje
            else:                                    
                destinatario=message[3]                                   
                try:                                       
                    outmsg=sendMail(destinatario,mensaje2)                                        
                except exception as e:
                    print(e)
        else:
            data_o=mensaje
    elif 'firmware' in command:
        print("entro aqui")
        try:
            if 'weight' in payload:
                weightlast=firmware()
                #mensaje=weightlast+"<br>"
                mensaje=weightlast+"\n"                                    
                data_o=mensaje
        except Exception as e:
            print (e)
    elif 'lastreading' in command:
        try:
            irmalast,tpmslast,weightlast=lastReading()
            mensaje=irmalast+"<br>"+tpmslast+"<br>"+weightlast+"<br>"
            mensaje2=irmalast+"\n"+tpmslast+"\n"+weightlast+"\n"
        except Exception as e:
            print (e)
        if "replyto" in payload:
            if payload=='replytome':
                data_o=mensaje2
            else:                                    
                destinatario=message[3]                                   
                try:                                       
                    outmsg=sendMail(destinatario,mensaje)                                        
                except exception as e:
                    print(e)
        else:
            data_o=mensaje2                                        
                                
    elif 'outputconfig' in command:
        try:
           reportmethod=outputConfig()                               
        except Exception as e:
            print (e)
        if "replyto" in payload:
            if payload=='replytome':
                data_o=(reportmethod +"\n")
            else:                                    
                destinatario=message[3]                                   
                try:                                       
                    outmsg=sendMail(destinatario,reportmethod)                                        
                except exception as e:
                    print(e)
        else:
            data_o=reportmethod
    elif 'set_route' in command:
        dicPayload=payloadSpliter(payload)
        dest=dicPayload['dest']
        code=dicPayload['code']
        


        
    else:
        print "Dato no es correcto intente de nuevo"
        data_o="Comando Incorrecto"
        logging.info(data_o)
    return data_o,flagfirst
        
def outputInterface(inflag,lasttiempo,flagfirst):
    try:
        config.read("/home/pi/config.ini")
        global outtrama
        outtrama=""
        if (config.getboolean('reportmethod','time')):                        
            tiempo=config.getint('reportmethod','reportime')
            if (inflag):
                GPIO.cleanup()
                inflag=False         
            if (tiempo!=lasttiempo):                          
                schedule.every(tiempo).minutes.do(sendbluetooth2)            
                print("siguiente ejecucion en: "+str(tiempo)+"\n")
                lasttiempo=tiempo                        
            schedule.run_pending()
            time.sleep(1)     
        elif (config.getboolean('reportmethod','input')):            
            for section in config.sections():                                
                if(config.has_option(section,'sensorname')):                                    
                    if ((config.get(section,'sensorname')=='report')
                          and (config.getboolean(section,'connected'))):                                       
                        puerto=config.getint(section,'port')
            if (flagfirst):                
                GPIO.setup(puerto, GPIO.IN, pull_up_down = GPIO.PUD_DOWN)
                GPIO.add_event_detect(puerto, GPIO.RISING, callback=sendbluetooth, bouncetime=300)
                inflag=True                
                flagfirst=False
    except Exception as e:
        logging.error(e)
        print (e)
        data_o="Sensor No Configurado \n"
        pass
    return inflag,outtrama,lasttiempo,flagfirst
