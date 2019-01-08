#!/usr/bin/env python3
# coding: utf-8
#
'''
TODOs:
	features to manipulate images
	def parse_form(): make separate function for parsing forms
	def updatemake function for updating kwargs (deep)
	make function to check if given field is in scope
	make functions for manipulating images
	parse all form components correctly
	parse requests params correctly
	basic check response from server
	cache which fields have already been updated, =what the current values are
	cache date of update and compare this date to the update interval restriction
'''

# STEP_KWARGS = [
# 	'method',
# 	'url',
# 	'params',
# 	'data',
# 	'json',
# 	'headers',
# 	'cookies',
# 	'files',
# 	'auth',
# 	'timeout',
# 	'allow_redirects',
# 	'proxies',
# 	'verify',
# 	'stream',
# 	'cert',
# ]

SCOPE_ORDER = [
	'graphql',
	'rest',
	'web',
]

import argparse, logging, yaml, requests, lxml, urllib.parse
from lxml import html as lxml_html

def alter_photo(photo_path, service):
	'''Modifies the photo to comply with the service constraints'''
	# min-width: min required width
	# width: required width
	# max-width: max allowed width
	# min-height: min required height
	# height: required height
	# max-height: max allowed height
	# ratio: ratio of photo
	# rec-width: recommended width
	# rec-height: recommended height
	# TODO
	return photo_path

def render_vars(services_config, service_name, structure, user_config):
	if type(structure) == list:
		for i in range(len(structure)):
			structure[i] = render_vars(services_config, service_name, structure[i], user_config)
	elif type(structure) == dict:
		for key in structure.keys():
			structure[key] = render_vars(services_config, service_name, structure[key], user_config)
	elif type(structure) == str:
		structure = structure.format(
		                             username=user_config['services'][service_name]['username'],
		                             password=user_config['services'][service_name]['password'],
		                             displayname=user_config['services'][service_name]['update']['displayname'],
		                             bio=user_config['services'][service_name]['update']['bio'],
		                             photo=open(
		                                        alter_photo(
		                                                    photo_path=user_config['services'][service_name]['update']['photo'],
		                                                    service=services_config['services'][service_name]
		                                                    )
		                                        ),
		                             			'rb'
		                             )
		# if structure == '/username':
		# 	structure = user_config['services'][service_name]['username']
		# elif structure == '/password':
		# 	structure = user_config['services'][service_name]['password']
		# elif structure == '/displayname':
		# 	structure = user_config['services'][service_name]['update']['displayname']
		# elif structure == '/bio':
		# 	structure = user_config['services'][service_name]['update']['bio']
		# elif structure == '/photo':
		# 	if 'photo' in user_config['services'][service_name]['update']:
		# 		logging.debug('Photo update required.')
		# 		photo_path = user_config['services'][service_name]['update']['photo']
		# 		logging.debug('Photo path is "%s".', photo_path)
		# 		if 'constraints' in services_config['services'][service_name]:
		# 			logging.debug('Constraints specified. Passing photo to alter_photo().')
		# 			photo_path = alter_photo(photo_path, constraints=services_config['services'][service_name]['constraints'])
		# 		logging.debug('Setting structure to photo file object.')
		# 		structure = open(photo_path, 'rb')
		# 		logging.debug(structure)
		# 	else:
		# 		logging.error('Photo is not specified in user config but required.')
	return structure

def get_form_items(form_elem, is_root=True, files={}):
	# disabled!
	# check if form present and if it does not point to id, do not use it
	# required: make sure it has value
	# TODO!
	# https://developer.mozilla.org/en-US/docs/Web/HTML/Element/input
	# https://developer.mozilla.org/en-US/docs/Web/HTML/Element/button
	# https://developer.mozilla.org/en-US/docs/Web/HTML/Element/datalist
	# https://developer.mozilla.org/en-US/docs/Web/HTML/Element/fieldset
	# https://developer.mozilla.org/en-US/docs/Web/HTML/Element/keygen
	# https://developer.mozilla.org/en-US/docs/Web/HTML/Element/label
	# https://developer.mozilla.org/en-US/docs/Web/HTML/Element/legend
	# https://developer.mozilla.org/en-US/docs/Web/HTML/Element/meter
	# https://developer.mozilla.org/en-US/docs/Web/HTML/Element/optgroup
	# https://developer.mozilla.org/en-US/docs/Web/HTML/Element/option
	# https://developer.mozilla.org/en-US/docs/Web/HTML/Element/output
	# https://developer.mozilla.org/en-US/docs/Web/HTML/Element/progress
	# https://developer.mozilla.org/en-US/docs/Web/HTML/Element/select
	form_items = {}
	if type(form_elem) == list:
		for elem in form_elem:
			new_form_items, files = get_form_items(elem, is_root=False, files=files)
			form_items.update(new_form_items)
	elif type(form_elem) == lxml.html.FormElement and is_root:
		form_items, files = get_form_items(form_elem.getchildren(), is_root=False, files=files)
	elif type(form_elem) == lxml.html.InputElement:
		if 'disabled' not in form_elem.attrib and 'name' in form_elem.attrib:
			if form_elem.attrib.get('type', 'text') == 'file':
				files[form_elem.attrib['name']] = False
			else:
				form_items[form_elem.attrib['name']] = form_elem.attrib.get('value', '') # TODO: can inputs have children?
	elif type(form_elem) == lxml.html.LabelElement:
		# parse label
		attrib_for = form_elem.attrib.get('for', False)
		pass
	elif type(form_elem) == lxml.html.HtmlElement:
		if form_elem.tag in ['div']:
			new_form_items, files = get_form_items(form_elem.getchildren(), is_root=False, files=files)
			form_items.update(new_form_items)
	return form_items, files

def make_request(services_config, service_name, session, request_settings, user_config, response=False):
	kwargs = {
		'method': 'GET',
		'headers': {
			'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:64.0) Gecko/20100101 Firefox/64.0'
		},
	}
	if response:
		kwargs['url'] = response.url
	if 'form' in request_settings:
		if not response:
			logging.error('Cannot fill in form: No previous response provided.')
			return False, False
		tree = lxml_html.fromstring(response.text)
		form_elem = tree.xpath(request_settings['form'])[0]
		kwargs['method'] = form_elem.attrib.get('method', kwargs.get('method', 'GET')).upper()
		if 'action' in form_elem.attrib:
			kwargs['url'] = urllib.parse.urljoin(kwargs.get('url',''), form_elem.attrib['action'])
		kwargs['headers']['Accept'] = 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
		form_elem.attrib.get('accept-charset', '') # TODO
		form_data, files = get_form_items(form_elem)

		# get stray form parts from page
		if 'id' in form_elem.attrib:
			stray_form_parts = tree.xpath('//input[@form="{}"]'.format(form_elem.attrib['id'])) # what about <button> and <submit>?
			for stray in stray_form_parts:
				if 'disabled' not in stray.attrib:
					if 'name' in stray.attrib:
						form_data[stray.attrib['name']] = stray.attrib.get('value', '')

		# assign form_data properly
		if kwargs['method'] == 'GET':
			kwargs['params'] = form_data
		elif kwargs['method'] == 'POST':
			kwargs['data'] = form_data

		# patch kwargs with settings from the services file
		if 'method' in request_settings:
			kwargs['method'] = request_settings['method']
		if 'url' in request_settings:
			kwargs['url'] = request_settings['url']
		if 'params' in request_settings:
			rendered_params = render_vars(services_config, service_name, request_settings['params'], user_config)
			if 'params' in kwargs:
				kwargs['params'].update(rendered_params)
			else:
				kwargs['params'] = rendered_params
		if 'data' in request_settings:
			rendered_data = render_vars(services_config, service_name, request_settings['data'], user_config)
			if 'data' in kwargs:
				kwargs['data'].update(rendered_data)
			else:
				kwargs['data'] = rendered_data
		if 'json' in request_settings:
			rendered_json = render_vars(services_config, service_name, request_settings['json'], user_config)
			if 'json' in kwargs:
				kwargs['json'].update(rendered_json)
			else:
				kwargs['json'] = rendered_json
		if 'headers' in request_settings:
			rendered_headers = render_vars(services_config, service_name, request_settings['headers'], user_config)
			if 'headers' in kwargs:
				kwargs['headers'].update(rendered_headers)
			else:
				kwargs['headers'] = rendered_headers
		if 'cookies' in request_settings:
			rendered_cookies = render_vars(services_config, service_name, request_settings['cookies'], user_config)
			if 'cookies' in kwargs:
				kwargs['cookies'].update(rendered_cookies)
			else:
				kwargs['cookies'] = rendered_cookies
		if 'files' in request_settings:
			rendered_files = render_vars(services_config, service_name, request_settings['files'], user_config)
			for file in rendered_files.keys():
				if file in files:
					files[file] = rendered_files[file]
			if form_elem.attrib.get('enctype') == 'multipart/form-data' or len(files) != 0:
				logging.debug('enctype is multipart!')
				files_list = []
				for file in files.keys():
					files_list.append((file, (files[file].name, files[file])))
					logging.debug('file list:')
					logging.debug(files_list)
				kwargs['files'] = files_list
			else:
				# TODO: should reparse files and path them on top of form_data
				...

		if 'auth' in request_settings:
			# TODO
			rendered_auth = render_vars(services_config, service_name, request_settings['auth'], user_config)
		if 'timeout' in request_settings:
			# TODO
			...
		if 'allow_redirects' in request_settings:
			# TODO
			...
		if 'proxies' in request_settings:
			# TODO
			rendered_proxies = render_vars(services_config, service_name, request_settings['proxies'], user_config)
		if 'verify' in request_settings:
			# TODO
			...
		if 'stream' in request_settings:
			# TODO
			...
		if 'cert' in request_settings:
			# TODO
			...

		# fill in form
		if 'fill' in request_settings:
			for xpath in request_settings['fill'].keys():
				if xpath.startswith('/html'):
					fill_elem = tree.xpath(xpath)[0]
				elif xpath.startswith('/'):
					fill_elem = form_elem.xpath(xpath)[0]
				else:
					# TODO: what about form elems other than input
					fill_elem = form_elem.xpath('//input[@name="{}"]'.format(xpath))[0]
				if 'name' in fill_elem.attrib:
					form_data[fill_elem.attrib['name']] = render_vars(services_config, service_name, request_settings['fill'][xpath], user_config)

	else:
		# patch kwargs with settings from the services file
		if 'method' in request_settings:
			kwargs['method'] = request_settings['method']
		if 'url' in request_settings:
			kwargs['url'] = request_settings['url']
		if 'params' in request_settings:
			rendered_params = render_vars(services_config, service_name, request_settings['params'], user_config)
			if 'params' in kwargs:
				kwargs['params'].update(rendered_params)
			else:
				kwargs['params'] = rendered_params
		if 'data' in request_settings:
			rendered_data = render_vars(services_config, service_name, request_settings['data'], user_config)
			if 'data' in kwargs:
				kwargs['data'].update(rendered_data)
			else:
				kwargs['data'] = rendered_data
		if 'json' in request_settings:
			rendered_json = render_vars(services_config, service_name, request_settings['json'], user_config)
			if 'json' in kwargs:
				kwargs['json'].update(rendered_json)
			else:
				kwargs['json'] = rendered_json
		if 'headers' in request_settings:
			rendered_headers = render_vars(services_config, service_name, request_settings['headers'], user_config)
			if 'headers' in kwargs:
				kwargs['headers'].update(rendered_headers)
			else:
				kwargs['headers'] = rendered_headers
		if 'cookies' in request_settings:
			rendered_cookies = render_vars(services_config, service_name, request_settings['cookies'], user_config)
			if 'cookies' in kwargs:
				kwargs['cookies'].update(rendered_cookies)
			else:
				kwargs['cookies'] = rendered_cookies
		if 'files' in request_settings:
			# TODO
			rendered_files = render_vars(services_config, service_name, request_settings['files'], user_config)
		if 'auth' in request_settings:
			# TODO
			rendered_auth = render_vars(services_config, service_name, request_settings['auth'], user_config)
		if 'timeout' in request_settings:
			# TODO
			...
		if 'allow_redirects' in request_settings:
			# TODO
			...
		if 'proxies' in request_settings:
			# TODO
			rendered_proxies = render_vars(services_config, service_name, request_settings['proxies'], user_config)
		if 'verify' in request_settings:
			# TODO
			...
		if 'stream' in request_settings:
			# TODO
			...
		if 'cert' in request_settings:
			# TODO
			...

	if 'url' in kwargs:
		logging.debug('Sending request')
		logging.debug(kwargs)
		response = session.request(**kwargs)
	else:
		logging.error('No url was provided for request!')
		return False, False

	if 'response' in request_settings:
		if 'status_codes' in request_settings['response']:
			if not response.status_code in request_settings['response']['status_codes']:
				logging.error('Request failed, wrong status code: "%d" returned. (Should be in %s)', response.status_code, request_settings['response']['status_codes'])
				return False, response
	logging.debug('Request was successful (code "%d")!', response.status_code)
	return True, response # TODO: basic check needed to see if a good response came from server

def main():
	global devvar1, devvar2, devvar3
	parser = argparse.ArgumentParser(argument_default=False, description='Update the metadata (profile picture, bio, display name, etc.) of your social media profiles.')
	parser.add_argument('--config', type=argparse.FileType('r', encoding='UTF-8'), default='test_config.yaml', help='The configuration file with your identifiers.')
	parser.add_argument('--services', type=argparse.FileType('r', encoding='UTF-8'), default='SERVICES.yaml', help='API schema file for all supported services.')
	parser.add_argument('--verbose', '-v', action='count', default=0, help='Turn on verbose mode.')
	parser.add_argument('--log', help='Logfile path. If omitted, stdout is used.')
	parser.add_argument('--debug', '-d', action='store_true', help='Log all messages including debug.')
	args = parser.parse_args()
	# DEBUG: args = parser.parse_args(['--debug','--config=test_config.yaml','--services=SERVICES.yaml'])

	# Setting logging level
	if args.debug:
		loglevel = logging.DEBUG
	elif args.verbose:
		loglevel = logging.INFO
	else:
		loglevel = logging.WARNING

	# Setting log file settings
	if args.log:
		logging.basicConfig(filename=args.log, filemode='a', level=loglevel)
	else:
		logging.basicConfig(level=loglevel)

	logging.debug('Begin of log')

	logging.debug('Loading services file')
	if type(args.services)==str:
		services_file = open(args.services, 'r', encoding='utf-8')
	else:
		services_file = args.services
	services = yaml.load(services_file)

	logging.debug('Loading user config file')
	if type(args.config)==str:
		user_config_file = open(args.config, 'r', encoding='utf-8')
	else:
		user_config_file = args.config
	logging.debug('User config file is "%s".', user_config_file.name)
	user_config = yaml.load(user_config_file)

	logging.debug('Beginning to update services')
	for service_name in user_config['services'].keys():
		service_name = service_name.lower()
		logging.debug('Looking for service "%s".', service_name)
		if service_name in services['services']:
			logging.debug('Found service definition for "%s".', service_name)
			service = services['services'][service_name]
			pending_fields = list(user_config['services'][service_name]['update'].keys())
			logging.debug('%d pending fields for service "%s".', len(pending_fields), service_name)

			for scope in sorted(service['scopes'].keys(), key=lambda x: SCOPE_ORDER.index(x.lower())):
				logging.debug('Trying service "%s", scope "%s".', service_name, scope)
				session = requests.Session()
				authed = False
				response = False

				for supported_fields in service['scopes'][scope]['fields']:
					for field in supported_fields.split(','):
						field = field.strip()
						logging.debug('Looking if field "%s" of service "%s", scope "%s" is wanted.', field, service_name, scope)
						if field in pending_fields:
							logging.debug('Field "%s" of service "%s", scope "%s" is wanted.', field, service_name, scope)
							if 'auth' in service['scopes'][scope] and not authed:
								logging.debug('Authentication required for service "%s", scope "%s".', service_name, scope)
								if 'requirements' in service['scopes'][scope]:
									logging.debug('Checking requirements for service "%s", scope "%s".', service_name, scope)
									requirements_fullfilled = False
									for requirement in service['scopes'][scope]['requirements']:
										if requirement not in user_config['services'][service_name]:
											logging.error('Authing cannot be performed for service "%s", scope "%s": Necessary option "%s" not given.', service_name, scope, requirement)
											break
									else:
										logging.debug('Requirements given!')
										requirements_fullfilled = True
								else:
									logging.debug('No requirements specified for service "%s", scope "%s".', service_name, scope)
									requirements_fullfilled = True
								if requirements_fullfilled:
									logging.debug('Logging into "%s", scope "%s".', service_name, scope)
									for i, step in enumerate(service['scopes'][scope]['auth']):
										successful, response = make_request(services, service_name, session, step, user_config, response)
										if not successful:
											logging.error('Authing for service "%s", scope "%s" failed at step %d!', service_name, scope, i)
											break
									else:
										logging.debug('Authing successful for service "%s", scope "%s"!', service_name, scope)
										authed = True
							elif 'auth' not in service['scopes'][scope]:
								logging.debug('Authetication not required for service "%s", scope "%s".', service_name, scope)
								authed = True

							if authed:
								logging.debug('Trying to update field "%s" of service "%s", scope "%s".', field, service_name, scope)
								for i, step in enumerate(service['scopes'][scope]['fields'][supported_fields]):
									(successful, response) = make_request(services, service_name, session, step, user_config, response)
									if not successful:
										logging.error('Step %d in field "%s" of service "%s", scope "%s" failed. Aborting step.', i, field, service_name, scope)
										break
								else:
									logging.debug('Update of field "%s" (service "%s", scope "%s") successful!', field, service_name, scope)
									pending_fields.remove(field)

			if len(pending_fields) != 0:
				logging.warning('For service "%s", the following fields could not be updated:', service_name)
				for field in pending_fields:
					logging.warning('%s', field)
		else:
			logging.debug('Service "%s" not found in service definitions.', service_name)

if __name__ == '__main__':
	main()
