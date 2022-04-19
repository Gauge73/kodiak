from numpy import log
import time
from progressbar import ProgressBar


class Thermometer:
	#max_hist	Maximum number of historical temp readings to retain
	#max_age	Maximum age of historical temp readings in seconds
	#_hist		List of previous temperature readings
	#name		Friendly name for thermometer object
	#channel	MCP3008 input channel (0-7)
	#coefficients	List of Steinhart-Hart coefficients
	#r1		Resistance of static resistor in Ohms
	#vcc		Supply voltage

	def __init__(self, channel, coefficients, r1, **kwargs):
		"""
		Usage: __init__(int channel, [] coefficients, int r1, **kwargs)

		Required arguments:
		channel = (int) MCP3008 input channel (0-7)
		coefficients = [float, float, float] List of Steinhart-Hart coefficients A, B, and C
		r1 = (float) Resistance of static resistor in Ohms 

		Optional kwargs:
		name = (str) Friendly name for Thermometer
		vcc = (float) Supply voltage
		max_age = (int) Maximum age of historical readings (used for averages)
		max_hist = (int) Maximum number of historical readings (used for averages)
		unit = (str) 'c' for Celcius, 'f' for Fahrenheit (default 'f')
		"""

		self._hist = []
		# channel
		if not type(channel) == int or channel < 0 or channel > 7:
			raise Exception('First argument, channel, must be an integer between 0 and 7 (inclusive)')
		else:
			self.channel = channel

		# coefficients
		if not type(coefficients) == list or not len(coefficients) == 3:
			raise Exception('Second argument, coefficients, must be a list of three floats')
		else:
			for i in coefficients:
				if not type(i) == float:
					raise Exception('Second argument, coefficients, must be a list of three floats')
			self.coefficients = coefficients

		# r1
		if not type(r1) == float and not type(r1) == int:
			raise Exception('Third argument, r1, must be a float')
		else:
			self.r1 = float(r1)

		# ------
		# kwargs
		# ------
		if 'max_hist' in kwargs.keys():
			self.max_hist = kwargs['max_hist']
		else:
			self.max_hist = 300
		if 'max_age' in kwargs.keys():
			self.max_age = kwargs['max_age']
		else:
			self.max_age = 30
		if 'vcc' in kwargs.keys():
			self.vcc = kwargs['vcc']
		else:
			self.vcc = 3.3
		if 'name' in kwargs.keys():
			self.name = kwargs['name']
		else:
			self.name = 'Input ' + str(self.channel)
		if 'unit' in kwargs.keys():
			if kwargs['unit'].lower() in ['c', 'f']:
				self._unit = kwargs['unit']
			else
				raise Exception('Argument \'unit\' must be either \'f\' or \'c\'')
		else
			self._unit = 'f'


	# Function to prune extra or expired historical readings
	def __prune_hist__(self):
		while True:
			try:
				if len(self._hist) > self.max_hist or self._hist[0][0] < (time.time() - self.max_age):
					self._hist.pop(0)
				else:
					break
			except:
				break

	def get_average(self):
		"""
		Returns the average temperature over the current history of readings.
		"""

		self.__prune_hist__()
		try:
			return sum(map(lambda x: x[1], self._hist))/len(self._hist)
		except Exception as e:
			raise Exception('Failed to get average with error: ' + str(e))
			return None

	def get_instant(self, mcp3008):
		"""
		Returns an instant reading from the thermometer.
		"""

		v2 = mcp3008.read_adc(self.channel) / 1023 * self.vcc
		v1 = self.vcc - v2

		if v1 > 0 and v2 > 0:
			r2 = self.r1 * v2 / v1

			# Calculate temp in Kelvin using Steinhart-Hart method
			t = 1 / (self.coefficients[0] + (self.coefficients[1] * log(r2)) + (self.coefficients[2] * (log(r2) ** 3)))

			# Convert to Fahrenheit or Celcius
			if self._unit.lower == 'c':
				t = (t - 273.15)
			else:
				t = (t - 273.15) * (9/5) + 32
			return t
		else:
			return None

	def check(self, mcp3008):
		"""
		Causes the Thermometer object to add the current reading to the history of readings.  If max_hist is exceeded, then the oldest recorded reading is dropped.
		"""

		reading = self.get_instant(mcp3008)
		if not reading is None:
			self._hist.append((time.time(), reading))
		self.__prune_hist__()
		return reading

	def get_calibration_point(self, mcp3008):
		"""
		Returns an average of many resistance readings over a short period of time.  Return values are measured in Ohms.  This can be used as calibration points to find Steinhart-Hart coefficients A, B, and C.
		"""

		readings = []
		bar = ProgressBar()
		for i in bar(range(300)):
			v2 = mcp3008.read_adc(self.channel) / 1023 * self.vcc
			v1 = self.vcc - v2
			r2 = self.r1 * v2 / v1
			readings.append(r2)
			time.sleep(0.1)

		return sum(readings) / len(readings)

