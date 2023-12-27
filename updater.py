import requests
import re
import time
import json


# Load config.json
with open('config.json', 'r') as file:
	config_data = json.load(file)

	zone_identifier = config_data.get('zone_identifier')
	auth_email = config_data.get('auth_email')
	auth_key = config_data.get('auth_key')
	records_to_sync = config_data.get('records_to_sync')
	ttl = config_data.get('ttl')
	proxy = config_data.get('proxy')


SECONDS_BETWEEN_UPDATE_REQUESTS = 1
SECONDS_BETWEEN_IP_UPDATE_CHECKS = 120
IPV4_REGEX = r'([01]?[0-9]?[0-9]|2[0-4][0-9]|25[0-5])\.([01]?[0-9]?[0-9]|2[0-4][0-9]|25[0-5])\.([01]?[0-9]?[0-9]|2[0-4][0-9]|25[0-5])\.([01]?[0-9]?[0-9]|2[0-4][0-9]|25[0-5])'


authentication_headers = {
	"X-Auth-Email": auth_email,
	"X-Auth-Key": auth_key,
	"Content-Type": "application/json",
}


def get_records():
	url = f"https://api.cloudflare.com/client/v4/zones/{zone_identifier}/dns_records?type=A"

	response = requests.get(url, headers=authentication_headers)

	if response.status_code == 200:
		records = response.json()

		return records['result']
	else:
		print(f"Error: {response.status_code}, {response.text}")


def update_record(record_name, record_identifier, ip):
	dns_update_payload = {
		"type": "A",
		"name": record_name,
		"content": ip,
		"ttl": ttl,
		"proxied": proxy
	}

	url = f"https://api.cloudflare.com/client/v4/zones/{zone_identifier}/dns_records/{record_identifier}"

	try:
		# Make the PATCH request to update the DNS record
		response = requests.patch(url, headers=authentication_headers, json=dns_update_payload)

		# Check the response
		if response.status_code == 200:
			print(f"Update successful! {record_name} now points to {ip}.")
		else:
			print(f"Update failed with status code {response.status_code}")
			print(response.text)
	except Exception as e:
		print(f"Exception: {e}")

def get_public_ip():
	try:
		response = requests.get('https://cloudflare.com/cdn-cgi/trace')
		if response.status_code != 200:
			# In the case that Cloudflare failed to return an IP.
			# Attempt to get the IP from other websites.
			response = requests.get('https://api.ipify.org')
			if response.status_code != 200:
				response = requests.get('https://ipv4.icanhazip.com')

				if response.status_code != 200:
					print(f"None of the providers returned an IP.")
					return None
	except Exception as e:
		print(f"Exception: {e}")
		return None
	
	# Extract just the IP from the response.
	ip_line = re.search(r'^ip=(%s)$' % IPV4_REGEX, response.text, flags=re.MULTILINE)
	ip = ip_line.group(1) if ip_line else None
	return ip


def correct_records(public_ip):
	public_ip = get_public_ip()

	records = get_records()
	record_data = [(record['name'], record['content'], record['id']) for record in records]

	for a_record, ip_entry, record_id in record_data:
		if a_record in records_to_sync and ip_entry != public_ip:
			print(f"[{record_id}] {a_record} does not match your public IP, {ip_entry}. Updating to {public_ip}")
			update_record(a_record, record_id, public_ip)
			time.sleep(SECONDS_BETWEEN_UPDATE_REQUESTS)


previous_public_ip = None

while True:
	public_ip = get_public_ip()

	# If we failed to get the public IP, try again in 10 seconds.
	if public_ip is None:
		print("Failed to get public IP. Trying again in 10 seconds...")
		time.sleep(10)
		continue

	ip_has_changed = previous_public_ip != public_ip

	print(f"Your IP is {public_ip}.")

	# IP has changed, go and correct them in Cloudflare
	if ip_has_changed:

		correct_records(public_ip)

		previous_public_ip = public_ip

		print(f"Updated all {len(records_to_sync)} records to be synced.")

	print(f"Waiting {SECONDS_BETWEEN_IP_UPDATE_CHECKS} seconds before checking public IP again...")
	time.sleep(SECONDS_BETWEEN_IP_UPDATE_CHECKS)
