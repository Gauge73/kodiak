import argparse

#---------------------------
# Parse arguments
try:
	parser = argparse.ArgumentParser(prog='calibrate', description='Calibrates grillcon input devices.')

	parser.add_argument('command', type=str, metavar='command', help='low|mid|high|commit|clear')
	parser.add_argument('-c', action='store', metavar='<config_path>', help='Specify a configuration path (default=./config.yaml)')
	parser.add_argument('-i', action='store', type=int, metavar='<input>', help='MCP3008 input channel (required for low|mid|high)')
	parser.add_argument('-n', action='store', type=int, metavar='<readings>', help='Number of readings to be taken for calibartion (default=500)')
	parser.add_argument('-o', action='store_true', help='Overwrite existing value (void if Command=commit')
	parser.add_argument('-r', action='store_true', help='Maintain calibration values after committing')
	parser.add_argument('-t', action='store', type=float, metavar='<temp>', help='Temperature for calibration (required for low|mid|high)')
	parser.add_argument('-v', action='store_true', help='Verbose output')

	arguments = parser.parse_args()
except Exception as e:
	print('Failed to parse arguments with error: ' + str(e))
#---------------------------


#---------------------------
# Config
import yaml
if not arguments.c is None:
	configpath = arguments.c
else:
	configpath = 'config.yaml'
try:
	with open(configpath, 'r') as file:
		config = yaml.safe_load(file)
except Exception as e:
        print('FATAL: Failed to load configuration file with the following error: {}'.format(e))
        quit()
if arguments.v:
	print('Configuration loaded successfully.')
#---------------------------




######################################################
# Commit values
if arguments.command == 'commit':
	if arguments.i is None:
		print('-i is a require argument for the ' + arguments.command + ' command.')
		quit()
	from math import log
	print('Committing calibration...')
	r1, t1 = config['IO']['Inputs']['MCP3008'][arguments.i]['calibration']['low']
	r2, t2 = config['IO']['Inputs']['MCP3008'][arguments.i]['calibration']['mid']
	r3, t3 = config['IO']['Inputs']['MCP3008'][arguments.i]['calibration']['high']
	l1 = log(r1)
	l2 = log(r2)
	l3 = log(r3)
	y1 = 1/t1
	y2 = 1/t2
	y3 = 1/t3
	x2 = (y2 - y1) / (l2 -l1)
	x3 = (y3 - y1) / (l3 - l1)
	C = ((x3 - x2) / (l3 - l2)) * (l1 + l2 + l3) ** -1
	B = x2 - C * (l1 ** 2 + (l1 * l2) + l2 ** 2)
	A = y1 - (B + l1 ** 2 * C) * l1
	if arguments.v:
		print('A = {}\nB = {}\nC = {}'.format(A, B, C))

	config['IO']['Inputs']['MCP3008'][arguments.i]['coefficients']['A'] = A
	config['IO']['Inputs']['MCP3008'][arguments.i]['coefficients']['B'] = B
	config['IO']['Inputs']['MCP3008'][arguments.i]['coefficients']['C'] = C

	try:
		with open(configpath, 'w') as file:
			yaml.safe_dump(config, file)
	except Exception as e:
		print('Failed to commit calibration with error: ' + str(e))
		quit

	print('Calibration committed successfully.')
	quit()
######################################################




######################################################
# Clear values
if arguments.command == 'clear':
	if arguments.v:
		print('Clearing calibration points...')
	if arguments.i is None:
		print('-i is a required argument for command ' + arguments.command + '!')
		quit()
	try:
		for point in ['low', 'mid', 'high']:
			config['IO']['Inputs']['MCP3008'][int(arguments.i)]['calibration'][point] = None
		with open(configpath, 'w') as configfile:
			yaml.safe_dump(config, configfile)
		print('Successfully cleared calibration points for input ' + str(arguments.i) + '.')
		quit()
	except Exception as e:
		print('Failed to clear calibration points with error: ' + str(e))

	quit()
######################################################




######################################################
# Calibrate
#---------------------------
# Checking input values
if arguments.i is None:
	print('-i is a required argument for command \'' + arguments.command + '\'!')
	quit()
if arguments.t is None:
	print('-t is a required argument for command \'' + arguments.command + '\'!')
	quit()
if not config['IO']['Inputs']['MCP3008'][int(arguments.i)]['calibration'][arguments.command] is None and not arguments.o:
	print('Calibration point \'' + arguments.command + '\' already exists.  Use -o to overwrite.')
	quit()
#---------------------------



#---------------------------
# Enable SPI

# Importing required modules
import gpiozero as gpio
from Adafruit_GPIO.SPI import SpiDev
import Adafruit_MCP3008 as mcp3008
import time

if arguments.v:
	print('Attempting to enable SPI interface...')
try:
        mcp = mcp3008.MCP3008(spi=SpiDev(config['IO']['Inputs']['SPI']['port'], config['IO']['Inputs']['SPI']['device']))
except Exception as e:
        print('FATAL: Failed to enable SPI interface with error: {}'.format(e))
        quit()
if arguments.v:
	print('Succesfully enabled SPI interface.')
#---------------------------

mcp = mcp3008.MCP3008(spi = \
	SpiDev(config['IO']['Inputs']['SPI']['device'], config['IO']['Inputs']['SPI']['port']))
vs = config['IO']['Inputs']['MCP3008'][int(arguments.i)]['vcc']
resistor = config['IO']['Inputs']['MCP3008'][int(arguments.i)]['resistor']

hist = []
if not arguments.n is None:
	hist_max = arguments.n
else:
	hist_max = 500


print('Starting...')

for i in range(hist_max):
	v2 = mcp.read_adc(arguments.i)/1023 * vs
	v1 = vs - v2
	if v1 > 0:
		r2 = (resistor * v2 / v1)
		hist.append(r2)
		if arguments.v:
			print('{}/{}: Reading = {:.3}V\tResistance = {:,}Ω, Average = {:,.2f}Ω'.format(i, hist_max, float(v2), int(r2), sum(hist) / len(hist)))
		else:
			print('{} / {} readings.'.format(i, hist_max), end='\r')
	time.sleep(0.1)

# Convert to Kelvins
if config['General']['Units'] == 'F':
	arguments.t = (arguments.t + 459.67) * 5/9
if config['General']['Units'] == 'C':
	arguments.t = arguments.t + 273.15

try:
	config['IO']['Inputs']['MCP3008'][int(arguments.i)]['calibration'][arguments.command] = (sum(hist) / len(hist), arguments.t)
	with open(configpath, 'w') as file:
		yaml.safe_dump(config, file)
except Exception as e:
	print('Failed to save recording with error: ' + str(e))
	quit()

print('Recorded average resistance for input {} at {:.2f}°K is {:,.2f}Ω.'.format(arguments.i, arguments.t, sum(hist) / len(hist)))

quit()
######################################################

parser.print_help()
