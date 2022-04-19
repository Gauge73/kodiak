import gpiozero as gpio
import time

class Fan:
	_leds = []	# gpio.LEDBarGraph to indicate fan speed
	_en = int	# gpio.DigitalOutputDevice connected to enable 1 pin of L293D
	_in1 = int	# gpio.DigitalOutputDevice connected to input 1 pin of L293D
	_in2 = int	# gpio.DigitalOutputDevice connected to input 2 pin of L293D
	_duty = 0	# Current duty cycle of fan (0-1)

	def __init__(self, enable, input1, input2, **kwargs):
		"""
		Usage: __init__(int enable, int input1, int input2, list leds)

		Required (positional) Arguments:
		enable = GPIO pin number connected to the Enable 1 (pin 1) of the L293D
		input1 = GPIO pin number connected to the Input 1 (pin 2) of the L293D
		input2 = GPIO pin number connected to the Input 2 (pin 7) of the L293D

		Optional (keyword) Arguments:
		leds = List of GPIO pins connected to LEDs used for LED bar graph
		"""
		try:
			self._duty = 0
			self._en = gpio.PWMOutputDevice(enable)
			self._en.value = self._duty
		except:
			raise Exception('Failed to enable GPIO pin for Enable 1 on L293D')
			return None
		try:
			self._in1 = gpio.DigitalOutputDevice(input1)
			self._in1.on()
		except:
			raise Exception('Failed to enable GPIO pin for Input 1 on L293D')
			return None
		try:
			self._in2 = gpio.DigitalOutputDevice(input2)
			self._in2.off()
		except:
			raise Exception('Failed to enable GPIO pin for Input 2 on L293D')
			return None

		# Enable bar graph if 'bar' argument is true
		if 'leds' in kwargs.keys():
			try:
				self._bar = gpio.LEDBarGraph(*kwargs['leds'])
				self._bar.value = self._duty
				self._has_bar = True
			except Exception as e:
				raise Exception('Failed to enable LEDBarGraph with error: ' + str(e))
				return None
		else:
			self._has_bar = False


	def set_duty(self, duty):
		"""
		Sets the duty cycle of the fan and sets the LED bar graph accordingly.

		Usage: set_duty(float duty)

		Arguments:
		set_duty = The duty cycle of the fan represented as a decimal value between 0 and 1 (inclusive)
		"""
		if duty < 0 or duty > 1:
			raise Exception('Expected a numeric value between 0 and 1 (inclusive)')
		# Give fan 100% power momentarily to kickstart the motor
		if self._en.value == 0 and duty > 0 and duty < 1:
			self._en.value = 1
			time.sleep(0.1)
		# Set final fan duty cycle
		self._en.value = duty
		if self._has_bar:
			self._bar.value = duty
		self._duty = duty

	def get_duty(self):
		return self._duty

	def on(self):
		self.set_duty(1)

	def off(self):
		self.set_duty(0)
