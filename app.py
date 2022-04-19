from flask import Flask, render_template
import json
import sys
import pymysql as mysql
import yaml

# Attempt to load config file
try:
	configfile = 'config.yaml'
	with open(configfile, 'r') as file:
		config = yaml.safe_load(file)
except Exception as e:
	print('Failed to load config file at {}!'.format(configfile))
	print('Config load error: ' + str(e))
	quit()

# Attempt to connect to database
try:
	sqlcon = mysql.connect(host=config['Database']['db_host'], user=config['Database']['db_user'], password=config['Database']['db_pass'], autocommit=True)
except Exception as e:
	print('Failed to connect to the database with error ' + str(e))
	quit()

app = Flask(__name__)

@app.route('/get_temps')
def get_avg():
	# Pull a list of inputs from the database
	sqlcur = sqlcon.cursor()
	sqlcur.execute('USE grillcon;')
	sqlcur.execute('SELECT * FROM inputs;')

	retval = {}
	retval['Units'] = config['General']['Units']
	retval['Inputs'] = {}

	for input in sqlcur.fetchall():
		retval['Inputs'][str(input[0])] = {'type': input[2], 'name': input[3], 'target': input[1]}
		sqlcur.execute('SELECT MAX(temp_id) FROM temps WHERE input_id = ' + str(input[0]) + ';')
		latest_temp_id = sqlcur.fetchall()[0][0]
		sqlcur.execute('SELECT temp FROM temps where temp_id = ' + str(latest_temp_id) + ';')
		retval['Inputs'][str(input[0])]['current_temp'] = sqlcur.fetchall()[0][0]
	sqlcur.close()
	return json.dumps(retval)
	
@app.route('/')
def get_index():
	print('get_index called.')
	return render_template('index.html')
