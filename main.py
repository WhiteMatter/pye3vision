import urllib3, requests, json, time
from pathlib import Path
import urllib.parse
from urllib.parse import urljoin



class e3vision:
    #pass in parameters
    watchtowerurl = 'https://localhost:4343'
    username = 'whitematter'
    password = 'test'
    
    #leave alone
    isRemoteAccess = False
    apit = ''
    camid = [] # array of camid integers
    cameraname = ['e3v0001'] # array of camera name strings
    
    #values
    rListCams = None
    j = None
    
    interface = None
    segment = "2m" #global segment time (can set for specific camera)
         
    resolution = '600p60'
    codec = 'H264'
    anno = 'Time'
    
    def __init__(self, watchtower = 'https://localhost:4343', username = 'whitematter', password = 'test'):
        self.watchtowerurl = watchtower
        
        self.username = username
        self.password = password      
        
        # Search for a specific camera Id by name
        # print(self.camid)
        
        # (optional) Disable the "insecure requests" warning for https certs
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning) 
        
        #tests whether API token is necessaary based on remote access choice
        response = requests.get(urljoin(self.watchtowerurl, '/api/cameras'), verify=False)
        if response.status_code == 200:
            self.isRemoteAccess = False
            print('you did not choose remote web access')
            print('use \'listCameras()\' to scan and list cameras')
        else:
            self.isRemoteAccess = True
            print('you chose remote web access, make sure to use \'login(username, password)\' to login')
    
    # Method to run through video recording
    def recordVideo(self, x, camIdArray):
        if self.isRemoteAccess:
            self.login(self.username, self.password)
        self.scanCameras()
        self.listCameras()
        syncCam = int(input("Sync Camera ID: "))
        self.setSyncCamera(syncCam)
        self.networkInterfaces()
        self.listConfig()
        
        self.setConfigs('600p60', 'H264', 'Time') #resol, codec, annot
        self.chooseCameras(camIdArray) #camid[], segtimes[] (segtimes optional)
        time.sleep(60)
        self.saveVideo(x, camIdArray) #seconds, camid
        self.disconnectCamera()
        self.unbindAllCameras()
            
#------------------------------------------------------------------------------
    def getCameraName(self):
        print(self.cameraname)
        
    def getWatchTowerUrl(self):
        print(self.watchtowerurl)
        
    # Quick and dirty function for looking up cameras from name
    def getCamByName(jsonobj, name):
        for dict in jsonobj:
            if name in dict['Hostname']:
                return dict
            
    # Get the cam id # from name
    def getCamIdByName(self, jsonobj, name):
        return self.getCamByName(jsonobj, name)['Id']
#------------------------------------------------------------------------------

    # If user chooses to use web remote access, require a login
    def login(self, username, password):
        r = requests.post(urljoin(self.watchtowerurl, '/api/login'), data = {'username': username, 'password': password}, verify=False)
        j = json.loads(r.text)
        self.apit = j['apitoken']
        print(r.text)    
        print('use \'listCameras()\' to list for cameras')
        
    # Scan for cameras
    def scanCameras(self):
        if(self.isRemoteAccess):
            requests.get(urljoin(self.watchtowerurl, '/api/cameras/scan'), params = {'apitoken': self.apit}, verify=False)
        else:
            requests.get(urljoin(self.watchtowerurl, '/api/cameras/scan'), verify=False)
    
    # List available cameras, translate into json objects
    def listCameras(self):
        #scan cameras first
        self.scanCameras()
        
        if(self.isRemoteAccess):
            self.rListCams = requests.get(urljoin(self.watchtowerurl, '/api/cameras'), params = {'apitoken': self.apit}, verify=False)
        else:
            self.rListCams = requests.get(urljoin(self.watchtowerurl, '/api/cameras'), verify=False)
        self.j = json.loads(self.rListCams.text)
        print("Available cameras:")
        for cam in self.j:
            print("Id {:d}: {:s}".format(cam['Id'], cam['Hostname']))
            
        print('use \'setSyncCamera(syncCameraId)\' to set sync camera')
                       
    def setSyncCamera(self, syncId):
        # Set sync source camera
        index = self.parseSyncId(syncId)
        
        requests.post(urljoin(self.watchtowerurl, '/api/cameras/action'), data = {'Id': self.camid, 'Action': 'UPDATEMC', 'apitoken': self.apit}, verify=False)
        print(">> Choosing {:d}: {:s} as sync source\n".format(syncId, self.j[index]['Hostname'])) 
        
        print('\'use networkInterfaces()\' to choose interface')
    
    # parse sync camera id into index     
    def parseSyncId(self, syncId):
        
        if(self.isRemoteAccess):
            self.rListCams = requests.get(urljoin(self.watchtowerurl, '/api/cameras'), params = {'apitoken': self.apit}, verify=False)
        else:
            self.rListCams = requests.get(urljoin(self.watchtowerurl, '/api/cameras'), verify=False)
        self.j = json.loads(self.rListCams.text)
        
        index = 0
        for cam in self.j:
            if(cam['Id'] == syncId):
                return index
            index = index + 1
        return index
        
    # List network interfaces
    def networkInterfaces(self):
        r = requests.get(urljoin(self.watchtowerurl, '/api/interfaces/available'), params = {'apitoken': self.apit}, verify=False)
        j = json.loads(r.text)
        print("Available interfaces: ")
        for iface in j:
            print(iface['Device'] + ': ' + iface['IPAddr'])
            
        # choose an interface (network card) that communicates with the cameras
        self.interface = j[0]['IPAddr']
        print(">> Choosing: " + self.interface + "\n")    
        
        print('use \'listConfigs()\' to list configuration settings for video')
        
    # List out configuration options
    def listConfig(self):
        # Get available configs
        r = requests.get(urljoin(self.watchtowerurl, '/api/cameras/manage/configs/available'), params = {'apitoken': self.apit}, verify=False)
        j = json.loads(r.text)
        
        # List resolution
        print("Available resolutions: ")
        for res in j['AvailRes']:
            print(res['Shortname'] + ': ' + res['Fulldisplay'])
        
        # List codecs
        print("Available Codecs: ")
        for codec in j['AvailCodec']:
            print(codec)
                
        # List annotations
        print("Available annotations: ")
        for anno in j['AvailAnno']:
            print(anno)
            
        print('use \'setConfigs(resolution, codec, ann)\' or move to next step \'chooseCameras(cameraID, segtime)\' to choose cameras and set segmentation times for each/all cameras')
    
    # Set configuration      
    def setConfigs(self, res, cod, ann):
        self.resolution = res 
        print(">> Choosing: " + self.resolution + '\n')
        
        self.codec = cod
        print(">> Choosing: " + self.codec + '\n')
        
        self.anno = ann
        print(">> Choosing: " + self.anno + '\n')
        
        print('use \'chooseCameras(cameraID(s))\'')
       
    # Connect to camera(s), takes in array of camid and segtimes    
    def chooseCameras(self, cid, segtimes=None):
        #set global variable
        if(isinstance(cid, list)):
            self.camid.extend(cid)
        elif(isinstance(cid, int)):
            self.camid.append(cid)
        
        #bind cameras
        for x in self.camid:
            self.bindCamera(x)
        
        #method overload (segtimes[] is optional parameter)
        for i in range(len(self.camid)):
            if segtimes is not None:
                self.connectCamera(self.camid[i], segtimes[i])
            else:
                self.connectCamera(self.camid[i], self.segment)    
                    
    # Bind to a camera
    def bindCamera(self, cid):
        #Bind camera
        requests.post(urljoin(self.watchtowerurl, '/api/cameras/action'), data = {'Id': cid, 'Action': 'BIND', 'apitoken': self.apit}, verify=False)
        print("binded")
        
        # Bind to a camera
    def unbindCamera(self, cid):
        #Bind camera
        requests.post(urljoin(self.watchtowerurl, '/api/cameras/action'), data = {'Id': cid, 'Action': 'UNBIND', 'apitoken': self.apit}, verify=False)
        print("unbinded")
        
    # Connect to a camera
    def connectCamera(self, cid, seg):
        requests.post(urljoin(self.watchtowerurl, '/api/cameras/action'), data = {'Id': cid, 'Action': 'CONNECT', 'Iface': self.interface, 'Config': self.resolution, 'Codec': self.codec, 'Annotation': self.anno, 'Segtime': seg, 'apitoken': self.apit}, verify=False)
        
        # See if it's running
        r = requests.get(urljoin(self.watchtowerurl, '/api/cameras'), params = {'apitoken': self.apit}, verify=False)
        j = json.loads(r.text)
        #cam = self.getCamByName(j, self.cameraname)
        #print("Running state: {:d}".format(cam['Runstate']))
        print("Waiting for sync...")
        print("Normally, keep all the cameras connected and streaming all the time, and start/stop saving at will")
        
    # Start and stop save, x is parameter so how many seconds
    def saveVideo(self, x, camid):
        if(self.isRemoteAccess):
            # Start saving
            requests.post(urljoin(self.watchtowerurl, '/api/cameras/action'), data = {'IdGroup[]': camid, 'Action': 'RECORDGROUP', 'apitoken': self.apit}, verify=False)
            print("Started saving, " + str(x) + " seconds")
            #wait x seconds
            time.sleep(x)
            # Stop saving
            requests.post(urljoin(self.watchtowerurl, '/api/cameras/action'), data = {'IdGroup[]': camid, 'Action': 'STOPRECORDGROUP', 'apitoken': self.apit}, verify=False)
            print("Stopped saving")
        else:
            # Start saving
            requests.post(urljoin(self.watchtowerurl, '/api/cameras/action'), data = {'IdGroup[]': camid, 'Action': 'RECORDGROUP'}, verify=False)
            print("Started saving, " + str(x) +  " seconds")
            #wait x seconds
            time.sleep(x)
            # Stop saving
            requests.post(urljoin(self.watchtowerurl, '/api/cameras/action'), data = {'IdGroup[]': camid, 'Action': 'STOPRECORDGROUP'}, verify=False)
            print("Stopped saving")
        time.sleep(2)
        
    # Start function
    def startRecord(self, camid=-1):
        
        if camid == -1:
            camid = self.camid
        #figure out whether camid is int or int array
        if len(camid) is None:
            requests.post(urljoin(self.watchtowerurl, '/api/cameras/action'), data = {'IdGroup[]': [camid], 'Action': 'RECORDGROUP', 'apitoken': self.apit}, verify=False)
        else: #if camid is an array
            requests.post(urljoin(self.watchtowerurl, '/api/cameras/action'), data = {'IdGroup[]': camid, 'Action': 'RECORDGROUP', 'apitoken': self.apit}, verify=False)
        
    # Stop function
    def stopRecord(self, camid =-1):
        if camid == -1:
            camid = self.camid
        #figure out whether camid is int or int array
        if type(camid) is int:
            requests.post(urljoin(self.watchtowerurl, '/api/cameras/action'), data = {'IdGroup[]': [camid], 'Action': 'STOPRECORDGROUP', 'apitoken': self.apit}, verify=False)
        else: #if camid is an array
            requests.post(urljoin(self.watchtowerurl, '/api/cameras/action'), data = {'IdGroup[]': camid, 'Action': 'STOPRECORDGROUP', 'apitoken': self.apit}, verify=False)

    def disconnectCamera(self, camid):
        for x in camid:    
            requests.post(urljoin(self.watchtowerurl, '/api/cameras/action'), data = {'Id': x, 'Action': 'DISCONNECT', 'Iface': self.interface, 'apitoken': self.apit}, verify=False)
            print("Disconnected")

    # Disconnect from camera
    def disconnectAllCameras(self):
        for x in self.camid:    
            requests.post(urljoin(self.watchtowerurl, '/api/cameras/action'), data = {'Id': x, 'Action': 'DISCONNECT', 'Iface': self.interface, 'apitoken': self.apit}, verify=False)
            print("Disconnected")
    
    # Unbind all cameras
    def unbindAllCameras(self):
        for x in self.camid:
            self.unbindCamera(x)
        print("unbinded all")
        
    
    
