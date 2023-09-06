import requests
import time
from datetime import datetime
import re
import pymsteams

PRE_ENV_CONSOLE = 'http://XX.XX.X.XXX:8004/system/console/'
JMX_URL =  PRE_ENV_CONSOLE + 'jmx'
VMSTAT_URL = PRE_ENV_CONSOLE + 'vmstat'
MEMORY_URL = PRE_ENV_CONSOLE + 'memoryusage'
GC_URL = PRE_ENV_CONSOLE + 'jmx/java.lang%3Atype%3DMemory/op/gc'
TEAMS = pymsteams.connectorcard("XXXXX")

USERNAME = 'XXXX'
PASSWORD = 'XXXX'
SECONDS_INTERVAL = 15
SESSION_LIMIT = 190
MEMORY_LIMIT = 75
SECONDS_WAIT_ON_RESTART = 60
LOG_FILE = 'log.txt'
COUNT_LIMIT = 0


# Get date
def get_date():
    now = datetime.now()
    return now.strftime("%d-%m-%Y")

# Get hour
def get_time():
    now = datetime.now()
    return now.strftime("%H:%M:%S")


# Get memory usage
def get_memory_usage():
    try:
        response = requests.get(MEMORY_URL, auth=(USERNAME, PASSWORD))
        response.raise_for_status()
        
        content = response.text
        percentage_match = re.search(r"'score':'(\d+)%'}]", content)

        if percentage_match:
            percentage_value = int(percentage_match.group(1))
            return percentage_value
        
    except requests.exceptions.RequestException as e:
        write_in_log(f"{get_time()}\n  Error al obtener la memoria: {e}")
    except Exception as e:
        write_in_log(f"{get_time()}\n  Error inesperado al obtener la memoria: {e}")

# Get sessions number
def get_sessions_number():
    try:
        response = requests.get(JMX_URL, auth=(USERNAME, PASSWORD))
        response.raise_for_status()

        content = response.text
        return content.count(">SessionStatistics</a>")
    
    except requests.exceptions.RequestException as e:
        write_in_log(f"{get_time()}\n  Error al obtener el número de sesiones: {e}")
    except Exception as e:
        write_in_log(f"{get_time()}\n  Error inesperado al obtener el número de sesiones: {e}")

# Run Garbage Collector
def garbage_collector():
    try:
        response = requests.post(GC_URL, auth=(USERNAME, PASSWORD))
        response.raise_for_status()

        write_in_log(f"  ------ GC ejecutado a las {get_time()}")
        TEAMS.text(f"GC ejecutado")
        TEAMS.send()
    
    except requests.exceptions.RequestException as e:
        write_in_log(f"{get_time()}\n  Error al ejecutar el GC: {e}")
    except Exception as e:
        write_in_log(f"{get_time()}\n  Error inesperado al ejecutar el GC: {e}")
    
# Run restart AEM
def restart_aem():
    try:
        data = {'shutdown_type': 'Restart'}
        response = requests.post(VMSTAT_URL, data=data, auth=(USERNAME, PASSWORD))
        response.raise_for_status()

        write_in_log(f"  ------ REINICIANDO a las {get_time()}\n  Script inactivo durante {SECONDS_WAIT_ON_RESTART} segundos")
        TEAMS.text(f"REINICIANDO...")
        TEAMS.send()
        time.sleep(SECONDS_WAIT_ON_RESTART)
    
    except requests.exceptions.RequestException as e:
        write_in_log(f"{get_time()}\n  Error al reiniciar: {e}")
    except Exception as e:
        write_in_log(f"{get_time()}\n  Error inesperado al reiniciar: {e}")

# Write in log
def write_in_log(text):
    LOG_NAME = get_date() + "_" + LOG_FILE
    with open(LOG_NAME, "a") as log_file:
        print(text)
        log_file.write(text + '\n')


# MAIN
def main():
    global COUNT_LIMIT

    sessions_number = get_sessions_number()
    memory_usage = get_memory_usage()

    if sessions_number is not None and memory_usage is not None:
        write_in_log(f"{get_time()}\n  SessionStatistics: {sessions_number}\n  Memory usage: {memory_usage}%")

        if sessions_number > SESSION_LIMIT:
            COUNT_LIMIT = COUNT_LIMIT + 1
            write_in_log(f"  --- AVISO DE SESIONES Nº {COUNT_LIMIT}: (Sesiones) Mayor de {SESSION_LIMIT}")
            TEAMS.text(f"AVISO DE SESIONES Nº {COUNT_LIMIT}: (Sesiones) Mayor de {SESSION_LIMIT}")
            TEAMS.send()

            if COUNT_LIMIT == 2:
                garbage_collector()
            if COUNT_LIMIT > 3:
                restart_aem()
        else:
            COUNT_LIMIT = 0

        if memory_usage > MEMORY_LIMIT:
            write_in_log(f"  --- AVISO DE MEMORIA: (GC) Mayor de {MEMORY_LIMIT}%")
            TEAMS.text(f"AVISO DE MEMORIA: (GC) Mayor de {MEMORY_LIMIT}%")
            TEAMS.send()
            garbage_collector()

# Bucle on SECONDS_INTERVAL
while True:
    main()
    time.sleep(SECONDS_INTERVAL)