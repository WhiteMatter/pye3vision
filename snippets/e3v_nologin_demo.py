# Note: this code snippet is relevant for use under the development API in 
# e3vision watchtower v0.3.0 https://www.white-matter.com/e3vision

#import necessary libraries
import urllib3,requests,json
import time

# quick and dirty method for looking up cameras from name
def getCamByName(jsonobj, name):
    for dict in jsonobj:
        if name in dict['Hostname']:
            return dict

# get the cam id # from name
def getCamIdByName(jsonobj, name):
    return getCamByName(jsonobj, name)['Id']

# (optional) Disable the "insecure requests" warning for https certs
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# what watchtower url to control
watchtowerurl = 'https://localhost:4343'
cameraname = 'e3v8100'

# Scan for cameras
r = requests.get(watchtowerurl+'/api/cameras/scan', verify=False)

# List cameras, translate into a json object
r = requests.get(watchtowerurl+'/api/cameras', verify=False)
j = json.loads(r.text)
print("Available cameras:")
for cam in j:
    print("Id {:d}: {:s}".format(cam['Id'], cam['Hostname']))

# Search for a specific camera Id by name
camid = getCamIdByName(j, cameraname)

# Update the sync source
requests.post(watchtowerurl+'/api/cameras/action', data = {'Id': camid, 'Action': 'UPDATEMC'}, verify=False)
print(">> Choosing {:d}: {:s} as sync source\n".format(cam['Id'], cam['Hostname']))

# List network interfaces
r = requests.get(watchtowerurl+'/api/interfaces/available', verify=False)
j = json.loads(r.text)
print("Available interfaces: ")
for iface in j:
    print(iface['Device'] + ': ' + iface['IPAddr'])
# choose an interface (network card) that communicates with the cameras
interface = j[0]['IPAddr']
print(">> Choosing: " + interface + "\n")

# Get available configs
r = requests.get(watchtowerurl+'/api/cameras/manage/configs/available', verify=False)
j = json.loads(r.text)

# List resolution
print("Available resolutions: ")
for res in j['AvailRes']:
    print(res['Shortname'] + ': ' + res['Fulldisplay'])
resolution = '600p60'
print(">> Choosing: " + resolution + '\n')

# List codecs
print("Available Codecs: ")
for codec in j['AvailCodec']:
    print(codec)
codec = 'H264'
print(">> Choosing: " + codec + '\n')

# List annotations
print("Available annotations: ")
for anno in j['AvailAnno']:
    print(anno)
anno = 'CameraName'
print(">> Choosing: " + anno + '\n')

segment = "2m"

# Bind to camera
requests.post(watchtowerurl+'/api/cameras/action', data = {'Id': camid, 'Action': 'BIND', 'apitoken': apit}, verify=False)

# Connect to a camera
requests.post(watchtowerurl+'/api/cameras/action', data = {'Id': camid, 'Action': 'CONNECT', 'Iface': interface, 'Config': resolution, 'Codec': codec, 'Annotation': anno, 'Segtime': segment}, verify=False)

# See if it's running
r = requests.get(watchtowerurl+'/api/cameras', verify=False)
j = json.loads(r.text)
cam = getCamByName(j, cameraname)
print("Running state: {:d}".format(cam['Runstate']))
print("Waiting for sync...")
print("Normally, keep all the cameras connected and streaming all the time, and start/stop saving at will")

# Wait a while for sync
time.sleep(35)

# Start saving
requests.post(watchtowerurl+'/api/cameras/action', data = {'IdGroup[]': [camid], 'Action': 'RECORDGROUP'}, verify=False)
print("Started saving, 30 seconds")

time.sleep(30)

# Stop saving
requests.post(watchtowerurl+'/api/cameras/action', data = {'IdGroup[]': [camid], 'Action': 'STOPRECORDGROUP'}, verify=False)
print("Stopped saving")

time.sleep(2) # let file writing on-disk clean-up
# normally this wait would not be necessary unless you're IMMEDIATELY disconnecting afterwards.

# Disconnect from camera
requests.post(watchtowerurl+'/api/cameras/action', data = {'Id': camid, 'Action': 'DISCONNECT', 'Iface': interface}, verify=False)
print("Disconnected")
