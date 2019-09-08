from p2y import Py2Yaml
from esphome_p2y import *

# aicliv as2100 3-relay outdoor outlet
# 3 relays, 1 led, 1 button
# https://docs.tuya.com/docDetail?code=K8uhknau42nof
# https://github.com/ct-Open-Source/tuya-convert/wiki/Compatible-devices
#
# Switch Operation
#
# The LED has to react to both web and button changes (on if state=1).  Change state in loop if:
#  In state = 0, if any switch is on (web must have turned it on)
#  In state = 1, if all switches are off (web must have turned last one off)
#
# The button action is based on state:
#  In state = 0, press turns on to previous state, unless previous state is all off.  Then it turns all on.
#  In state = 1, press saves current state and turns all off.
#
#
# alternate: button presses could rotate through 0-7 combos (or extra mode after long press)

# not enough room for ota update
#
# curl http://192.168.0.192/light/led_1
# curl http://192.168.0.192/switch/relay_1
#
# curl -d "" http://192.168.0.216/switch/relay_1/toggle


# --- Config ----------------------------------------------------------------------------------------------

name = 'aicliv_as2100'
outFile = 'aicliv_as2100.yaml'
ssid = 'jennyjenny'
pw = '18008675309'

# --- Core ------------------------------------------------------------------------------------------------

p2y = Py2Yaml()
top = Top()

esphome = Esphome(name=name, platform='esp8266', board='esp01', esp8266_restore_from_flash=True)
top.esphome(esphome)

top.logger()

top.wifi(ssid=ssid, password=pw)

# prevent reboot timeout
top.api(reboot_timeout='0s', password=pw)
top.ota(safe_mode=True, password=pw)
top.web_server(port=80)

# --- Globals ---------------------------------------------------------------------------------------------

globals = Globals().add([
           ('id', 'state1'),
           ('type', 'int'),
           ('restore_value', 'no'),
           ('initial_value', '0')
          ])
globals.add([
           ('id', 'state2'),
           ('type', 'int'),
           ('restore_value', 'no'),
           ('initial_value', '0')
          ])
globals.add([
           ('id', 'state3'),
           ('type', 'int'),
           ('restore_value', 'no'),
           ('initial_value', '0')
          ])
globals.add([
           ('id', 'state'),
           ('type', 'int'),
           ('restore_value', 'no'),
           ('initial_value', '0')
          ])

top.globals(globals)

# --- Code ------------------------------------------------------------------------------------------------

# update summary state and return True if state changed
# handle web press updates
#   if the saved states are different from the relay states, the relays were switched by web
#   this can happen with state 0 or 1
#   if state is 0, all relays were shut off by button;  if any are on, change state to 1
#   if state is 1, some relays were turned on by button; if all are off, change state to 0
loop_lambda = """
int temp = id(relay1).state or id(relay2).state or id(relay3).state;
int rc = temp != id(state);
if (!id(state)) {
   if (temp) {
      id(state) = 1;
   }
} else {
   if (!temp) {
      id(state) = 0;
   }
}
if (rc) {
   id(state1) = id(relay1).state; id(state2) = id(relay2).state; id(state3) = id(relay3).state;
}
return rc;
"""

# handle button press updates
button_lambda="""
if (id(state)) {
   id(state1) = id(relay1).state; id(state2) = id(relay2).state; id(state3) = id(relay3).state;
   id(relay1).turn_off(); id(relay2).turn_off(); id(relay3).turn_off(); 
   id(state) = 0;
   auto call = id(led1).turn_off(); call.perform();   
} else {
   id(state) = id(state1) or id(state2) or id(state3);
   if (id(state)) {
      if (id(state1)) {id(relay1).turn_on();}
      if (id(state2)) {id(relay2).turn_on();}
      if (id(state3)) {id(relay3).turn_on();}
   } else {
      id(state) = 1;
      id(relay1).turn_on(); id(relay2).turn_on(); id(relay3).turn_on();
   }
   id(state1) = id(relay1).state; id(state2) = id(relay2).state; id(state3) = id(relay3).state;
   auto call = id(led1).turn_on(); call.perform();   
}
"""

# --- Boot ------------------------------------------------------------------------------------------------

boot = OnBoot(priority=100)
# set led and global state based on relay states
if1 = If().condition(Condition('lambda', 'return id(state);')).Then(LightTurnOn().id('led1')).Else(LightTurnOff().id('led1'))
boot.Then(if1)
esphome.on_boot(boot)

# --- Loop ------------------------------------------------------------------------------------------------

if2 = If().condition(Condition('lambda', loop_lambda)() )
if3 = If().condition(Condition('lambda', 'return id(state);'))
if3.Then(LightTurnOn().id('led1')).Else(LightTurnOff().id('led1'))
if2.Then(if3)
esphome.on_loop(if2)

# --- Light -----------------------------------------------------------------------------------------------

top.output(GPIO(id='status', pin=Pin(number='GPIO4', inverted=True)))
top.light(BinaryLight(name='LED 1', id='led1', output='status'))

# --- Sensor ----------------------------------------------------------------------------------------------

button = GPIOBinarySensor(name='Button 1', id='button1', pin= Pin(number='GPIO13',  inverted=True))
press = On().Then(Lambda(button_lambda))
button.on_press(press)
top.binary_sensor(button)

# --- Switch ----------------------------------------------------------------------------------------------

top.switch(GPIOSwitch(name='Relay 1', id='relay1', pin='GPIO12', restore_mode='RESTORE_DEFAULT_OFF'))
top.switch(GPIOSwitch(name='Relay 2', id='relay2', pin='GPIO14', restore_mode='RESTORE_DEFAULT_OFF'))
top.switch(GPIOSwitch(name='Relay 3', id='relay3', pin='GPIO3', restore_mode='RESTORE_DEFAULT_OFF'))

try:
   p2y.build(top(), outFile)
   print 'Created ' + outFile + '.'
except e:
   print e
