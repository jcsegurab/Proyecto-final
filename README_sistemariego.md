# Sistema de riego automatizado con Raspberry Pi 3B

## 1. Descripción

Este proyecto implementa un sistema de riego automatizado utilizando una
**Raspberry Pi 3B**. El sistema mide la humedad del suelo mediante un
sensor capacitivo **HW-390** conectado a un convertidor
analógico-digital **ADS1115**, y mide el nivel de agua del tanque
mediante un sensor ultrasónico **HC-SR04**.

Con las mediciones obtenidas, la Raspberry Pi toma la decisión de
encender o apagar una bomba de agua mediante un módulo relé de lógica
inversa. Además, envía periódicamente los datos a una tabla de
**Supabase** para su almacenamiento y posterior visualización en un
dashboard.

## 2. Funcionalidades

-   Lectura del voltaje entregado por el sensor de humedad HW-390.
-   Medición de la distancia entre el sensor HC-SR04 y la superficie del
    agua.
-   Control automático de la bomba según los umbrales de humedad y nivel
    del tanque.
-   Activación del relé mediante una señal de nivel bajo (`GPIO.LOW`) y
    desactivación mediante nivel alto (`GPIO.HIGH`).
-   Envío de las mediciones y estados del sistema a Supabase mediante
    una solicitud HTTP `POST`.
-   Actualización de datos aproximadamente cada dos segundos.
-   Apagado de la bomba y liberación de los pines GPIO al interrumpir el
    programa con `Ctrl+C`.

## 3. Hardware utilizado

  -----------------------------------------------------------------------
  Componente                          Función
  ----------------------------------- -----------------------------------
  Raspberry Pi 3B                     Unidad de procesamiento y control

  Sensor capacitivo HW-390            Medición de humedad del suelo

  Convertidor ADS1115                 Conversión de la señal analógica
                                      del sensor

  Sensor ultrasónico HC-SR04          Medición del nivel del agua del
                                      tanque

  Módulo relé                         Conmutación de la bomba

  Bomba de agua                       Suministro de agua al sistema de
                                      riego

  Fuente de alimentación              Alimentación de los módulos y la
                                      bomba, según sus especificaciones
  -----------------------------------------------------------------------

## 4. Conexiones

Las conexiones GPIO utilizadas por el programa están definidas con
numeración **BCM**:

  Dispositivo                     Pin Raspberry Pi (BCM)
  ----------------------------- ------------------------
  TRIG del HC-SR04                               GPIO 18
  ECHO del HC-SR04                               GPIO 24
  Entrada del relé                               GPIO 17
  SDA del ADS1115                           SDA (GPIO 2)
  SCL del ADS1115                           SCL (GPIO 3)
  Salida analógica del HW-390     Entrada A0 del ADS1115

**Importante:** el pin ECHO del HC-SR04 trabaja normalmente a 5 V. La
entrada GPIO de la Raspberry Pi tolera como máximo 3,3 V; por tanto, se
debe instalar un divisor de tensión o un adaptador de nivel lógico entre
ECHO y GPIO 24. Verifique también las tensiones y corrientes requeridas
por el relé y la bomba. No alimente la bomba directamente desde un pin
GPIO.

## 5. Requisitos de software

-   Raspberry Pi OS.
-   Python 3.
-   Interfaz I2C habilitada.
-   Conexión a Internet para enviar registros a Supabase.

Bibliotecas de Python utilizadas:

-   `RPi.GPIO`
-   `board`
-   `busio`
-   `adafruit-circuitpython-ads1x15`
-   `requests`

Instalación orientativa:

``` bash
sudo apt update
sudo apt install python3-pip python3-venv
```

Se recomienda crear un entorno virtual. En Raspberry Pi OS, si el
sistema restringe la instalación global de paquetes, utilice el entorno
virtual:

``` bash
python3 -m venv .venv --system-site-packages
source .venv/bin/activate
pip install adafruit-circuitpython-ads1x15 requests
```

La biblioteca `RPi.GPIO` puede requerir instalación o estar disponible
según la versión de Raspberry Pi OS. Compruebe que los módulos `board`,
`busio` y `RPi.GPIO` se puedan importar antes de ejecutar el programa.

## 6. Configuración de Supabase

El programa envía los datos a la tabla REST:

``` text
https://<PROYECTO>.supabase.co/rest/v1/sensores_riego
```

La tabla `sensores_riego` debe tener columnas compatibles con los campos
enviados por el programa:

  Campo       Dato enviado                          Tipo sugerido
  ----------- ------------------------------------- -----------------------
  `humedad`   Voltaje del sensor, en V              `numeric`
  `nivel`     Distancia medida, en cm               `numeric`
  `bomba`     Estado lógico de activación           `boolean` o `integer`
  `rele`      Estado lógico de la salida del relé   `boolean` o `integer`

Los tipos definitivos deben coincidir con la estructura real de la tabla
y con la forma en que se desean interpretar los estados. El programa
envía `GPIO.LOW` o `GPIO.HIGH` (valores numéricos 0 y 1), no las cadenas
`"Prendida"` o `"Apagada"`.

En el código se configuran `SUPABASE_URL` y `API_KEY`. Para evitar
exponer credenciales, es preferible leerlas desde variables de entorno y
no publicar claves en el repositorio. Una clave publicable
(`sb_publishable_...`) no debe confundirse con una clave secreta; aun
así, las políticas de seguridad de filas (RLS) y los permisos de la
tabla deben configurarse correctamente. Nunca incluyas una
`service_role` key en código distribuido al dispositivo.

## 7. Parámetros de control

El programa define los siguientes umbrales:

``` python
NIVEL_MINIMO = 11
V_SECO = 2.6
V_HUMEDO = 1.2
```

-   `NIVEL_MINIMO`: distancia límite, en centímetros, utilizada para
    decidir si hay suficiente agua en el tanque. En este código se
    compara directamente con la distancia medida por el HC-SR04.
-   `V_SECO`: voltaje de referencia asociado a la condición seca. Está
    definido, pero **no se utiliza actualmente** en la función
    `control_bomba`.
-   `V_HUMEDO`: voltaje límite asociado a la condición húmeda. La bomba
    se apaga cuando el voltaje es menor o igual a este valor.

La lógica implementada en `control_bomba` es:

1.  Si la distancia es menor que 11 cm y el voltaje es mayor que 1,2 V,
    se solicita encender la bomba.
2.  Si la distancia es mayor o igual a 11 cm, se solicita apagar la
    bomba.
3.  Si el voltaje es menor o igual a 1,2 V, se solicita apagar la bomba.

Los valores de voltaje dependen del sensor, del suelo y de su
calibración. Se deben medir experimentalmente y ajustar antes de
utilizar el sistema de forma autónoma.

## 8. Flujo de funcionamiento

1.  La Raspberry Pi inicializa los pines GPIO y el bus I2C.
2.  El ADS1115 lee el canal A0 conectado al sensor de humedad.
3.  El HC-SR04 mide la distancia hasta la superficie del agua.
4.  El programa evalúa las condiciones de humedad y nivel.
5.  Se activa o desactiva el relé.
6.  Se muestran en consola la fecha, el nivel, el voltaje de humedad y
    los estados de la bomba y el relé.
7.  Se envía un registro a Supabase.
8.  El proceso espera dos segundos y repite las mediciones.

## 9. Ejecución

Guarde el programa Python, por ejemplo, como `riego.py`. Active el
entorno virtual (si se creó) y ejecute:

``` bash
python3 riego.py
```

Para detener el programa desde la terminal:

``` text
Ctrl + C
```

Al detenerlo mediante una interrupción normal, el bloque `finally` debe
colocar la salida del relé en `GPIO.HIGH` y liberar los recursos GPIO.

## 10. Estructura de los datos enviados

Cada solicitud HTTP `POST` envía un objeto JSON con esta estructura:

``` json
{
  "humedad": 1.85,
  "nivel": 8.42,
  "bomba": 0,
  "rele": 0
}
```

Los números anteriores son únicamente un ejemplo ilustrativo. En la
ejecución real, los valores corresponden a las lecturas y estados del
sistema.


## 11. Solución de problemas

  -----------------------------------------------------------------------
  Problema                            Posible causa o revisión
  ----------------------------------- -----------------------------------
  No se detecta el ADS1115            Verificar I2C, cableado SDA/SCL,
                                      dirección I2C y alimentación

  El voltaje de humedad no cambia     Revisar conexión del HW-390 a A0,
                                      alimentación y calibración

  La distancia aparece como `None`    Revisar TRIG/ECHO, alimentación,
                                      divisor de tensión y tiempo de
                                      espera

  El relé funciona al revés           Confirmar si el módulo es activo en
                                      bajo o activo en alto

  Supabase devuelve error HTTP        Revisar URL, clave, nombre de
                                      tabla, columnas, permisos y
                                      políticas RLS

  Error de acceso a GPIO              Verificar permisos, instalación de
                                      la biblioteca y que ningún otro
                                      proceso esté usando los pines
  -----------------------------------------------------------------------

## 12. Autoría

Proyecto: **Sistema de riego automatizado con Raspberry Pi
3B**.

Autor: **Julián Camilo Segura**.
