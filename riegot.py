import RPi.GPIO as GPIO
import time
import os
from datetime import datetime


import board
import busio
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn

#DEFINICION VARIABLES Y PINES DE LA RASPBERRY PI 3B
GPIO.setmode(GPIO.BCM)

TRIG = 18
ECHO = 24
RELE = 26

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
#FUNCIÓN PARA LECTURA DEL SENSOR DE NIVEL def altura
def altura():

    GPIO.output(TRIG, GPIO.LOW)
    time.sleep(1)

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
#FUNCION PARA LECTURA DEL SENSOR DE HUMEDAD ANÁLOGO def leer voltaje
def leer_voltaje():

    voltaje = sensor.voltage

    return round(voltaje, 2)

#FUNCION DE DEFINICIÓN DE UMBRALES DE NIVEL Y HUMEDAD PARA ACTIVAR BOMBA def control_bomba
def control_bomba(distancia, voltaje):

    if distancia < NIVEL_MINIMO:

           activacion = 0
           return activacion


    elif distancia > NIVEL_MINIMO:

           activacion = 1
           return activacion

    elif voltaje >= V_SECO:
           activacion = 0
           return activacion
           
    elif voltaje <= V_HUMEDO:
           activacion = 1
           return activacion

#FUNCIÓN PARA ACTIVACION O DESACTIVACION RELE def control_rele
def control_rele(activacion):

    if activacion is True:
        estado = True
    else:
        estado = False
        GPIO.output(RELE, estado)
        return estado

#FUNCION PRINCIPAL EJECUCIÓN Y MUESTRA DE DATOS
def main():

    print("----------------------------------------")
    print("    SISTEMA DE RIEGO AUTOMATIZADO")
    print("----------------------------------------")
try:
    while True:
       nivel = altura()
       humedad = leer_voltaje()
       bomba = control_bomba(nivel, humedad)
       control_rele(bomba)

       print(f"Fecha: {datetime.now().strftime(' %Y-%m-%d %H:%M:%S')}")
       print("Nivel de tanque", nivel, "cm")
       print("Humedad en voltaje", humedad, "V")
       print("Bomba", bomba)

       if bomba == GPIO.HIGH:

           print("Bomba: Apagada")

       else:

           print("Bomba: Prendida")


       time.sleep(1)

   
except KeyboardInterrupt:
    print("\nPrograma detenido por usuario")

finally:

     GPIO.output(RELE, GPIO.HIGH)
     GPIO.cleanup()
     print("Bomba apagada")


if __name__== "__main__":
    main()



