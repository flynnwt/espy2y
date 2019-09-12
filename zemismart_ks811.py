from p2y import Py2Yaml
from esphome_p2y import *

# clear flash first time!  weird reset button (pcb) behavior - wouldn't complete boot w/o reflashing
# python esptool.py -p COM23 erase_flash
# upload ota:
# esphome zemismart_ks811.yaml run --upload-port 192.168.0.11

p2y = Py2Yaml()
top = Top()

# --- Config ----------------------------------------------------------------------------------------------

name = 'zemismart_ks811'
outFile = 'zemismart_ks811.yaml'
ssid = 'jennyjenny'
pw = '18008675309'

# --- Core ------------------------------------------------------------------------------------------------

p2y = Py2Yaml()
top = Top()

esphome = Esphome(name=name, platform='esp8266', board='esp8285', esp8266_restore_from_flash=True)
top.esphome(esphome)

top.logger()

wifi = Wifi(ssid=ssid, password=pw, ap=AP(ssid=name))
top.wifi(wifi)

# prevent reboot timeout
top.api(reboot_timeout='0s', password=pw)
top.ota(safe_mode=True, password=pw)
top.web_server(port=80)
top.time(platform='sntp', id='datetime')

# --- Light -----------------------------------------------------------------------------------------------

top.output(GPIO(id='status', pin=Pin(number='GPIO2', inverted=True)))
top.light(BinaryLight(name='LED 1', id='led1', output='status'))

# --- Sensor ----------------------------------------------------------------------------------------------

press1 = On().Then(SwitchToggle().id('relay1'))
top.binary_sensor(GPIOBinarySensor(name='Button 1', id='button1', pin= Pin(number='GPIO16', mode='INPUT_PULLUP', inverted=True), internal=True, on_press=press1))
press2 = On().Then(SwitchToggle().id('relay2'))
top.binary_sensor(GPIOBinarySensor(name='Button 2', id='button2', pin=Pin(number='GPIO5', inverted=True), internal=True, on_press=press2))
press3 = On().Then(SwitchToggle().id('relay3'))
top.binary_sensor(GPIOBinarySensor(name='Button 3', id='button3', pin=Pin(number='GPIO4', inverted=True), internal=True, on_press=press3))

# --- Switch ----------------------------------------------------------------------------------------------

top.switch(GPIOSwitch(name='Relay 1', id='relay1', pin='GPIO13', restore_mode='RESTORE_DEFAULT_OFF'))
top.switch(GPIOSwitch(name='Relay 2', id='relay2', pin='GPIO12', restore_mode='RESTORE_DEFAULT_OFF'))
top.switch(GPIOSwitch(name='Relay 3', id='relay3', pin='GPIO14', restore_mode='RESTORE_DEFAULT_OFF'))

p2y.build(top(), outFile)