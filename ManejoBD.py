#!/usr/bin/python 

import sqlite3
def connect(sqlite_file='sensorLog.sqlite'):    
    conn = sqlite3.connect(sqlite_file)
    cursor = conn.cursor()
    return conn, cursor
    
def close(conn):    
    conn.commit()
    conn.close()
        
def check_table(cursor, tablename): 
    cursor.execute(""" SELECT COUNT(*) FROM sqlite_master WHERE name = ?  """, (tablename, ))
    res = cursor.fetchone()
    return bool(res[0]) 
def create_tables(cursor):    
    if not check_table(cursor, "SENSOR_TPMS"):
        cursor.execute("""CREATE TABLE SENSOR_TPMS (
                            _ID INTEGER PRIMARY KEY AUTOINCREMENT,
                            timestamp DATETIME,
                            tire INTEGER,                          
                            temperatura INTEGER,                           
                            presion INTEGER,
                            enviado INTEGER
                        );""")  
    if not check_table(cursor, "SENSOR_IRMA3D"):
        cursor.execute("""CREATE TABLE SENSOR_IRMA3D (
                            _ID INTEGER PRIMARY KEY AUTOINCREMENT,
                            timestamp DATETIME,
                            psnin INTEGER,                         
                            psnout INTEGER,                            
                            psnintot INTEGER,
                            psnouttot INTEGER,
                            enviado INTEGER
                        );""")   
    if not check_table(cursor, "SENSOR_WEIGHT"):
        cursor.execute("""CREATE TABLE SENSOR_WEIGHT (
                            _ID INTEGER PRIMARY KEY AUTOINCREMENT,
                            timestamp DATETIME,
                            sensorid STRING,                         
                            weight INTEGER,                      
                            enviado INTEGER,
                            firmware STRING
                        );""")   

def insertTpms(tire, temperatura, presion): 
    conn, cursor = connect(sqlite_file)
    cursor.execute("""INSERT INTO SENSOR_TPMS(TIMESTAMP,TIRE,
                    TEMPERATURA, PRESION, ENVIADO)
                    VALUES (datetime('now'),(?),(?),(?),0);""",(tire,temperatura,presion))
    close(conn)

def insertIrma3D(psnIn, psnOut, psnInTot, psnOutTot):   
    conn, cursor = connect(sqlite_file)
    cursor.execute("""INSERT INTO SENSOR_IRMA3D(TIMESTAMP,PSNIN,
                    PSNOUT, PSNINTOT, PSNOUTTOT,ENVIADO)
                    VALUES (datetime('now'),(?),(?),(?),(?),0);""",(psnIn, psnOut, psnInTot, psnOutTot))
    close(conn)

def insertWeight(sensorid,weight,firmware):
    conn, cursor = connect(sqlite_file)
    cursor.execute("""INSERT INTO SENSOR_WEIGHT(TIMESTAMP,SENSORID,
                    WEIGHT, FIRMWARE, ENVIADO)
                    VALUES (datetime('now'),(?),(?),(?),0);""",(sensorid,weight,firmware))
    close(conn)

def selectWeight():
    conn= sqlite3.connect(sqlite_file)
    conn.row_factory = sqlite3.Row
    cursor=conn.cursor()  
    cursor.execute("""SELECT * FROM SENSOR_WEIGHT WHERE ENVIADO=0;""")
    val=cursor.fetchone()    
    close(conn)
    return val    

def selectIrma3D():
    conn= sqlite3.connect(sqlite_file)
    conn.row_factory = sqlite3.Row
    cursor=conn.cursor()  
    cursor.execute("""SELECT * FROM SENSOR_IRMA3D WHERE ENVIADO=0;""")
    val=cursor.fetchone()    
    close(conn)
    return val

def selectlastWeight():
    conn= sqlite3.connect(sqlite_file)
    conn.row_factory = sqlite3.Row
    cursor=conn.cursor()  
    cursor.execute("""SELECT * FROM SENSOR_WEIGHT  WHERE _ID = (SELECT MAX(_ID) FROM SENSOR_WEIGHT);""")
    val=cursor.fetchone()    
    close(conn)
    return val

def selectlastTpms():
    conn= sqlite3.connect(sqlite_file)
    conn.row_factory = sqlite3.Row
    cursor=conn.cursor()  
    cursor.execute("""SELECT * FROM SENSOR_TPMS WHERE _ID = (SELECT MAX(_ID) FROM SENSOR_TPMS);""")
    val=cursor.fetchone()      
    close(conn)
    return val

def selectlastIrma():
    conn= sqlite3.connect(sqlite_file)
    conn.row_factory = sqlite3.Row
    cursor=conn.cursor()  
    cursor.execute("""SELECT * FROM SENSOR_IRMA3D WHERE _ID = (SELECT MAX(_ID) FROM SENSOR_IRMA3D);""")
    val=cursor.fetchone()      
    close(conn)
    return val
    
def selectTpms():
    conn= sqlite3.connect(sqlite_file)
    conn.row_factory = sqlite3.Row
    cursor=conn.cursor()  
    cursor.execute("""SELECT * FROM SENSOR_TPMS WHERE ENVIADO=0;""")
    val=cursor.fetchone()      
    close(conn)
    return val

def updateSendTpms(ID):
    conn, cursor = connect(sqlite_file)
    cursor.execute("UPDATE SENSOR_TPMS SET ENVIADO=1 WHERE _ID=(?);",(ID,))
    close(conn)

def updateSendWeight(ID):
    conn, cursor = connect(sqlite_file)
    cursor.execute("UPDATE SENSOR_WEIGHT SET ENVIADO=1 WHERE _ID=(?);",(ID,))
    close(conn)
	
def updateSendIrma(ID):
    conn, cursor = connect(sqlite_file)
    cursor.execute("UPDATE SENSOR_IRMA3D SET ENVIADO=1 WHERE _ID=(?);",(ID,))
    close(conn)    
        
if __name__ == '__main__':
    conn, cursor = connect()
    create_tables(cursor)
    close(conn)
    
sqlite_file = 'sensorLog.sqlite'
