#!/usr/bin/env python3

#The livebox can't use DynDNS with OVH ...
#So this script go into the crontab.

import re
import sys
import http.client
from base64 import b64encode

OVH_DYNDNS_USERNAME= "morderca.net-cronny"
OVH_DYNDNS_PASSWORD= "doh]th}oo6Di"
OVH_DYNDNS_DOMAIN  = "morderca.net"

DYNDNS_WEB_GETIP = "checkip.dyndns.org"
RE_IP_PATTERN = "\d{1,3}.\d{1,3}.\d{1,3}.\d{1,3}"

#Get our IP by visiting DYNDNS website
conn = http.client.HTTPConnection( DYNDNS_WEB_GETIP )
conn.request("GET", "/")

r1 = conn.getresponse()
if(r1.status != 200):
	print("[-] Can't connect to " + DYNDNS_WEB_GETIP, file=sys.stderr )
	sys.exit()

matchObj = re.search(RE_IP_PATTERN, str(r1.readline()))
r1.close() #Be gentle ... cleanup your mess.

if not matchObj:
	print("[-] " + DYNDNS_WEB_GETIP + " did not return our IP.", file=sys.stderr)
	sys.exit()

ip = matchObj.group()

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

