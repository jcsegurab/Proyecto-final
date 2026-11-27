import RPi.GPIO as GPIO
import time
import os
from datetime import datetime


import board
import busio
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn
import requests

#DEFINICIÓN DE VARIABLES, PINES GPIO DE LA RASPBERRY PI 3B

TRIG = 18
ECHO = 24
RELE = 17

GPIO.setmode(GPIO.BCM)
GPIO.setup(TRIG, GPIO.OUT)
GPIO.setup(ECHO, GPIO.IN)
GPIO.setup(RELE, GPIO.OUT)
GPIO.output(RELE, GPIO.HIGH)
GPIO.setwarnings(False)


i2c = busio.I2C(board.SCL, board.SDA)
ads = ADS.ADS1115(i2c)
sensor = AnalogIn(ads, 0)


NIVEL_MINIMO = 11
V_SECO = 2.6
V_HUMEDO = 1.2

SUPABASE_URL = "https://pkvdijnnoaabuwulovdk.supabase.co"
API_KEY = "sb_publishable_z2dqFMhGY8I8fZMd03jucA_CZgajW2f"

endpoint = f"{SUPABASE_URL}/rest/v1/sensores_riego"

headers = {"apikey": API_KEY, "Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json", "Prefer": "return=minimal"}

#FUNCIÓN PARA LECTURA DEL SENSOR DE NIVEL HC-SR04

def altura():

    GPIO.output(TRIG, GPIO.LOW)

    GPIO.output(TRIG, GPIO.HIGH)
    time.sleep(0.000010)
    GPIO.output(TRIG, GPIO.LOW)

    # Esperar el inicio del pulso ECHO
    tiempo_inicio = time.time()
    timeout = 0.038

    while GPIO.input(ECHO) == 0:

        if time.time() - tiempo_inicio > timeout:
            return None

    ida = time.time()

    # Esperar el final del pulso ECHO
    while GPIO.input(ECHO) == 1:

        if time.time() - ida > timeout:
            return None

    regreso = time.time()

    # Calcular distancia en centimetros
    viaje = regreso - ida
    distancia = (viaje * 34300) / 2
    return round(distancia, 2)

#FUNCIÓN PARA LA LECTURA DEL SENSOR DE HUMEDAD ANÁLOGO  HW-390

def leer_voltaje():

    voltaje = sensor.voltage
    return round(voltaje, 2)

#FUNCIÓN DE CONTROL DE ENCENDIDO/APAGADO BOMBA CON UMBRALES DE NIVEL Y HUMEDAD

def control_bomba(distancia, voltaje):

    if distancia < NIVEL_MINIMO and voltaje > V_HUMEDO:

           activacion = GPIO.LOW
           return activacion

    elif distancia >= NIVEL_MINIMO:
           activacion = GPIO.HIGH
           return activacion

    elif voltaje <= V_HUMEDO:
           activacion = GPIO.HIGH
           return activacion 

#FUNCIÓN PARA AACTIVACIÓN O DESACTIVACIÓN DEL RELÉ

def control_rele(activacion):

    if activacion is GPIO.LOW:

       estado = GPIO.LOW
       GPIO.output(RELE, estado)
       return estado

    if activacion is GPIO.HIGH:

       estado = GPIO.HIGH
       GPIO.output(RELE, estado)
       return estado

#FUNCIÓN ENVÍO DATOS PARA REGISTRO EN BASE DE DATOS SUPABASE

def enviar_datos(voltaje, distancia, activacion, estado):


    datos = { "humedad": voltaje, "nivel": distancia, "bomba": activacion, "rele": estado}

    try:

       respuesta = requests.post(endpoint, json=datos, headers=headers, timeout=2)

       if respuesta.status_code in (200, 201):

           print(f"Enviando: Nivel: {distancia} cm | Humedad: {voltaje} V | Bomba: {activacion} | Rele: {estado}")

       else:

           print(f"Error {respuesta.status_code}: {respuesta.text}")

    except Exception as e:

        print(f"Fallo de red: {e}")

# FUNCIÓN PRINCIPAL EJECUCIÓN, MUESTRA DATOS EN RASPBERRY Y ENVÍO DE DATOS A SUPABASE
def main():

    print("----------------------------------------")
    print("    SISTEMA DE RIEGO AUTOMATIZADO")
    print("----------------------------------------")
try:
    while True:
       nivel = altura()
       humedad = leer_voltaje()
       bomba = control_bomba(nivel, humedad)
       rele = control_rele(bomba)


       print(f"Fecha: {datetime.now().strftime(' %Y-%m-%d %H:%M:%S')}")
       print("Nivel de tanque", nivel, "cm")
       print("Humedad en voltaje", humedad, "V")


       if bomba and rele == GPIO.HIGH:

           print("Bomba: Apagada")
           print("Relé: Abierto")

       else:

           print("Bomba: Prendida")
           print("Relé: Cerrado")

       enviar_datos(humedad, nivel, bomba, rele)

       time.sleep(2)


except KeyboardInterrupt:
    print("\nPrograma detenido por usuario")

finally:

     GPIO.output(RELE, GPIO.HIGH)
     GPIO.cleanup()
     print("Bomba apagada")


if __name__== "__main__":
    main()



