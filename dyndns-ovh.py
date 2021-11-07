#!/usr/bin/env python3

#The livebox can't use DynDNS with OVH ...
#So this script go into the crontab.

import os
import sys
import requests

OVH_DYNDNS_USERNAME= os.environ["OVH_DYNDNS_USERNAME"]
OVH_DYNDNS_PASSWORD= os.environ["OVH_DYNDNS_PASSWORD"]
OVH_DYNDNS_DOMAIN  = os.environ["OVH_DYNDNS_DOMAIN"]

LIVEBOX_USERNAME = os.environ["LIVEBOX_USERNAME"]
LIVEBOX_PASSWORD = os.environ["LIVEBOX_PASSWORD"]
LIVEBOX_ADDRESS  = os.environ["LIVEBOX_ADDRESS"]

def getLiveboxWAN4(addr, user, passwd):
	endpoint = f"http://{addr}/ws"
	s = requests.Session()

	r = s.get(f"http://{addr}/", headers={"Accept-Language": "en-US,en;q=0.5"});

	r = s.post(endpoint, json={
		"method": "createContext",
		"parameters": {
				"applicationName": "webui",
				"password": passwd,
				"username": user,
			},
			"service": "sah.Device.Information",
		}, headers={
			"Content-Type": "application/x-sah-ws-4-call+json",
			"Authorization": "X-Sah-Login",
		});

	if r.json()["status"] != 0:
		raise Exception("Logging error");

	contextID=r.json()["data"]["contextID"];
	s.cookies.set("sah/contextId", contextID);

	endpoint_headers={
		"Content-Type": "application/x-sah-ws-4-call+json",
		"X-Context": contextID,
		"Authorization": f"X-Sah {contextID}",
	}

	r = s.post(endpoint, json={
			"method": "getWANStatus",
			"parameters": {},
			"service": "NMC",
		}, headers=endpoint_headers)

	if not r.json()["status"]:
		raise Exception("Failed to query WAN Status");

	return r.json()["data"]["IPAddress"];

try:
	ip = getLiveboxWAN4(LIVEBOX_ADDRESS, LIVEBOX_USERNAME, LIVEBOX_PASSWORD)
except:
	sys.exit("[-] Failed to query IP from livebox (%s)" % LIVEBOX_ADDRESS)


try:
	r = requests.get("https://www.ovh.com/nic/update",
				auth=(OVH_DYNDNS_USERNAME, OVH_DYNDNS_PASSWORD),
				params={
					"system": "dyndns",
					"hostname": OVH_DYNDNS_DOMAIN,
					"ip": ip,
				}
			)
except:
	sys.exit("[-] Failed to connect to OVH")

if(r.status_code != 200):
	sys.exit("[-] Can't connect to ovh to update DNS.\n\tHTTP Error code: %i" % r.status)

#If the ip did change, write it. (the crontab will sent it via mail)
if("good" in r.text):
	print("[+] IP of %s changed to %s" % (OVH_DYNDNS_DOMAIN, ip))
elif("nochg" in r.text):
	pass
else:
	sys.exit("[-] Something went wrong while updating DNS.\n\tReturned content: %s", r.text)
