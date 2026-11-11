# Sistema de riego automatizado con Raspberry Pi 3B

## 1. Descripción general

Este proyecto implementa un sistema de riego automatizado utilizando una
**Raspberry Pi 3B**. El programa mide:

-   El nivel de agua del tanque mediante un sensor ultrasónico
    **HC-SR04**.
-   La humedad del suelo mediante un sensor capacitivo analógico
    **HW-390**, conectado a un convertidor analógico-digital
    **ADS1115**.

Con las mediciones, el sistema determina si debe activar o desactivar
una bomba de agua mediante un módulo de relé conectado a la Raspberry
Pi.

## 2. Hardware utilizado

  -----------------------------------------------------------------------
  Componente                          Función
  ----------------------------------- -----------------------------------
  Raspberry Pi 3B                     Unidad de procesamiento y control

  HC-SR04                             Medición de la distancia hasta la
                                      superficie del agua

  Sensor capacitivo HW-390            Medición analógica de humedad del
                                      suelo

  ADS1115                             Conversión de la señal analógica
                                      del sensor de humedad

  Módulo de relé de 5 V               Conmutación de la bomba

  Bomba de agua                       Suministro de agua al sistema de
                                      riego

  Fuente de alimentación              Alimentación de los módulos y de la
                                      bomba, según sus especificaciones
  -----------------------------------------------------------------------

## 3. Conexiones utilizadas

El programa utiliza numeración **BCM** para los pines GPIO.

  Elemento                        Pin Raspberry Pi (BCM)
  ----------------------------- ------------------------
  TRIG del HC-SR04                               GPIO 18
  ECHO del HC-SR04                               GPIO 24
  Entrada de control del relé                    GPIO 26
  ADS1115 SDA                                 SDA de I2C
  ADS1115 SCL                                 SCL de I2C
  Salida analógica del HW-390     Entrada A0 del ADS1115

**Importante:** el pin ECHO del HC-SR04 entrega normalmente una señal de
5 V. La Raspberry Pi utiliza GPIO de 3,3 V y sus entradas no son
tolerantes a 5 V. Utilice un divisor de tensión o un adaptador de nivel
lógico entre ECHO y GPIO 24. No conecte directamente una señal de 5 V a
un GPIO.

La bomba debe alimentarse mediante una fuente adecuada y conmutarse a
través de los contactos del relé. No alimente la bomba desde un pin
GPIO.

## 4. Requisitos de software

-   Raspberry Pi OS.
-   Python 3.
-   Interfaz I2C habilitada.
-   Biblioteca `RPi.GPIO`.
-   Biblioteca `adafruit-blinka`.
-   Biblioteca `adafruit-circuitpython-ads1x15`.

Instalación de las bibliotecas:

``` bash
sudo apt update
sudo apt install python3-pip python3-venv
```

En un entorno virtual compatible con el sistema:

``` bash
python3 -m venv --system-site-packages entorno
source entorno/bin/activate
pip install adafruit-blinka adafruit-circuitpython-ads1x15
```

La biblioteca `RPi.GPIO` suele estar disponible en Raspberry Pi OS. Si
no está instalada, consulte el método de instalación compatible con la
versión de Raspberry Pi OS utilizada.

Para habilitar I2C, ejecute:

``` bash
sudo raspi-config
```

Seleccione **Interface Options → I2C → Enable** y reinicie la Raspberry
Pi si el sistema lo solicita.

## 5. Parámetros de configuración

El código define los siguientes parámetros:

  ------------------------------------------------------------------------
  Variable                                     Valor Descripción
  --------------------- ---------------------------- ---------------------
  `TRIG`                                          18 GPIO que envía el
                                                     pulso de disparo al
                                                     HC-SR04

  `ECHO`                                          24 GPIO que recibe el
                                                     pulso de respuesta

  `RELE`                                          26 GPIO que controla el
                                                     módulo de relé

  `NIVEL_MINIMO`                               11 cm Umbral de distancia
                                                     para el control del
                                                     nivel del tanque

  `V_SECO`                                     2.6 V Umbral de voltaje
                                                     asociado al suelo
                                                     seco

  `V_HUMEDO`                                   1.2 V Umbral de voltaje
                                                     asociado al suelo
                                                     húmedo
  ------------------------------------------------------------------------

Los valores de voltaje son de referencia y deben calibrarse con el
sensor instalado, midiendo su salida en condiciones reales de suelo seco
y húmedo.

## 6. Funcionamiento del programa

### 6.1 Medición del nivel del tanque

La función `altura()` genera un pulso de 10 microsegundos en el pin TRIG
y mide la duración del pulso recibido en ECHO.

La distancia se calcula mediante:

\[ d = `\frac{t \cdot 34300}{2}`{=tex} \]

Donde:

-   (d): distancia en centímetros.
-   (t): tiempo de viaje del pulso ultrasónico en segundos.
-   (34300): velocidad aproximada del sonido en cm/s.
-   El divisor entre 2 considera el recorrido de ida y vuelta del
    sonido.

Si no se recibe el pulso dentro del tiempo límite, la función devuelve
`None`.

### 6.2 Medición de humedad

La función `leer_voltaje()` obtiene el voltaje medido por el canal A0
del ADS1115. El valor se utiliza como indicador de humedad del suelo.

En la configuración propuesta:

-   Un voltaje igual o superior a `V_SECO` representa una condición de
    suelo seco.
-   Un voltaje igual o inferior a `V_HUMEDO` representa una condición de
    suelo húmedo.

Esta relación debe comprobarse experimentalmente, ya que puede variar
según el sensor, el suelo y su calibración.

### 6.3 Control de la bomba

La función `control_bomba()` compara las mediciones con los umbrales
establecidos y determina la orden de funcionamiento de la bomba.


### 6.4 Control del relé

El código inicia el pin del relé en nivel `HIGH`. Esto corresponde a un
relé desactivado únicamente si el módulo instalado tiene lógica activa
en bajo (LOW).

Para un módulo de lógica inversa:

-   `GPIO.LOW`: relé activado.
-   `GPIO.HIGH`: relé desactivado.


## 7. Información mostrada en consola

Durante la ejecución, el programa está diseñado para mostrar:

-   Fecha y hora de la medición.
-   Distancia medida por el sensor ultrasónico.
-   Voltaje del sensor de humedad.
-   Orden de funcionamiento de la bomba.
-   Estado de la bomba: prendida o apagada.

El ciclo de lectura se repite aproximadamente cada segundo, aunque la
espera de un segundo dentro de `altura()` hace que el intervalo real sea
mayor.

## 8. Ejecución

Guarde el programa Python, por ejemplo, con el nombre:

``` text
sistema_riego.py
```

Ejecute:

``` bash
python3 sistema_riego.py
```

Si la configuración del sistema requiere permisos elevados para acceder
a GPIO o I2C, utilice el método de ejecución recomendado para su
instalación de Raspberry Pi OS.

Para detener el programa desde la terminal, presione:

``` text
Ctrl + C
```

El bloque de finalización debe apagar el relé y liberar los pines GPIO
mediante `GPIO.cleanup()`.

  
## 9. Diagrama general de funcionamiento

``` text
       Sensor ultrasónico HC-SR04
                  |
                  v
             GPIO 18/24
                  |
                  v
              Raspberry Pi 3B <------ Sensor HW-390
                  |                         |
                  |                       ADS1115
                  |                         |
                  +-----------+-------------+
                              |
                              v
                    Lógica de control
                    nivel + humedad
                              |
                              v
                       GPIO 26
                              |
                              v
                         Módulo relé
                              |
                              v
                           Bomba
                              |
                              v
                         Sistema de riego
```

## 10. Mantenimiento y pruebas

-   Verifique periódicamente las conexiones del sensor ultrasónico y del
    sensor de humedad.
-   Compruebe que el ADS1115 aparece en el bus I2C; puede utilizar
    `i2cdetect -y 1`.
-   Calibre los umbrales de humedad con muestras representativas del
    suelo.
-   Pruebe inicialmente el control del relé sin conectar la bomba.
-   Verifique el comportamiento del relé ante el arranque, la
    interrupción del programa y los errores de lectura.
-   Mantenga protegidas de la humedad la Raspberry Pi, el ADS1115 y las
    conexiones eléctricas.

------------------------------------------------------------------------


