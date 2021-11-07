#!/usr/bin/env python3

#The livebox can't use DynDNS with OVH ...
#So this script go into the crontab.

import os
import sys
import requests
import http.client
from base64 import b64encode

OVH_DYNDNS_USERNAME= "USERNAME"
OVH_DYNDNS_PASSWORD= "PASSWORD"
OVH_DYNDNS_DOMAIN  = "example.com"

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

#Time to update our DNS field.
conn = http.client.HTTPSConnection("www.ovh.com")
userAndPass = OVH_DYNDNS_USERNAME + ":" + OVH_DYNDNS_PASSWORD
headers = { 'Authorization' : 'Basic %s ' % b64encode( bytes(userAndPass, "utf-8") ).decode("ascii")}
conn.request("GET", "/nic/update?system=dyndns&hostname=%s&myip=%s" % (OVH_DYNDNS_DOMAIN, ip), headers = headers)

r1 = conn.getresponse()
if(r1.status != 200):
	print("[-] Can't connect to ovh to update DNS.", file=sys.stderr)
	print("\tHTTP Error code: %i" % r1.status, file=sys.stderr)
	sys.exit()

line = str(r1.readline())
r1.close()

#If the ip did change, write it. (the crontab will sent it via mail)
if(line.find("good") >= 0):
	print("[+] IP of %s changed to %s" % (OVH_DYNDNS_DOMAIN, ip))
else:
	#nochg is OK, the rest are probably errors.
	if(line.find("nochg") < 0 ):
		print("[-] Something went wrong while updating DNS.", file=sys.stderr)
		print("Return content: %s" % line[2:-1], file=sys.stderr)

