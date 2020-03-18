import shapefile
import fiona
import utm


class stopinfo:#includes information about the stop 
    def __init__(self):
        self.stopid = ""#from stops.txt
        self.rightstop = None#point to next stop northbound (to the right if at a junction)
        self.leftstop = None#point to next stop to the left if at a junction
        self.rightshape = []#list of points assembling track northbound to next stop (to the right if at a junction)
        self.leftshape = []#list of points assembling track to next stop to the left if at a junction
        self.name = ""#from stops.txt
        self.coord = ()#from stops.txt

class stop:#includes information about the stop sequence (varys by trip)
    def __init__(self):
        self.sequence = 0#from stop_times.txt based on pattern
        self.info = None#point to stops.txt info

class trip:
    def __init__(self):
        self.shapeid = ""#id for the shape assosiated with this trip(unique to each trip)
        self.shapecoord = []#create a list of all coordinates for this for this trip's shape in order 
        self.tripid = ""
        self.pattern = []#holds the pattern of stops based on on stop_times.txt

#get information about the stops from stops.txt
stopstxt = open("baselineGTFS/stops.txt", 'r')
stopdic = {}#create dictionary to hold every stopinfo instance

#loop goes through stopstxt to create stop information objects
for row in stopstxt:
    row = row.strip()
    rowlist = row.split(',')
    
    if rowlist[0] == 'stop_id':
        continue
    
    instance = stopinfo()#create  object to hold information
    instance.stopid = rowlist[0]
    x = rowlist[2].strip('"')
    instance.name = x
    
    #special cases 
    if instance.name == "Niagara Falls" and rowlist[3] == ' NY"':
        instance.name = 'Niagara Falls, NY'
    elif instance.name == "Niagara Falls" and rowlist[3] == ' ON"':
        instance.name = 'Niagara Falls, ON'
        
    if instance.name == 'New York Penn Station':
        instance.coord = (float(rowlist[4]), float(rowlist[5]))
    else:
        instance.coord = (float(rowlist[5]), float(rowlist[6]))
        
    #create two keys that hold the stop information values
    stopdic[instance.name] = instance
    stopdic[instance.stopid] = instance
    
#hard code map 

#list of stops outside NY-shapes not supported for thesr stops
outsideny = [stopdic['Castleton'], stopdic['Rutland'], stopdic['St. Lambert'], stopdic['Central Station-Montreal'], stopdic['Niagara Falls, ON'], stopdic['St. Catharines'], stopdic['Grimsby'], stopdic['Aldershot'], stopdic['Oakville'], stopdic['Toronto']]

#create map of stops going north 
stopdic['New York Penn Station'].rightstop = stopdic['Yonkers']
stopdic['Yonkers'].rightstop = stopdic['Croton-Harmon']
stopdic['Croton-Harmon'].rightstop = stopdic['Poughkeepsie']
stopdic['Poughkeepsie'].rightstop = stopdic['Rhinecliff']
stopdic['Rhinecliff'].rightstop = stopdic['Hudson']
stopdic['Hudson'].rightstop = stopdic['Albany/Rensselaer']
stopdic['Albany/Rensselaer'].rightstop = stopdic['Schenectady']
stopdic['Schenectady'].leftstop = stopdic['Amsterdam']
stopdic['Schenectady'].rightstop = stopdic['Saratoga Springs']
stopdic['Saratoga Springs'].rightstop = stopdic['Fort Edward-Glens Falls']
stopdic['Fort Edward-Glens Falls'].leftstop = stopdic['Whitehall']
stopdic['Fort Edward-Glens Falls'].rightstop = stopdic['Castleton']
stopdic['Castleton'].rightstop = stopdic['Rutland']
stopdic['Whitehall'].rightstop = stopdic['Ticonderoga']
stopdic['Ticonderoga'].rightstop = stopdic['Port Henry']
stopdic['Port Henry'].rightstop = stopdic['Westport']#skip port kent
stopdic['Westport'].rightstop = stopdic['Plattsburgh']
stopdic['Plattsburgh'].rightstop = stopdic['Rouses Point']
stopdic['Rouses Point'].rightstop = stopdic['St. Lambert']
stopdic['St. Lambert'].rightstop = stopdic['Central Station-Montreal']
stopdic['Amsterdam'].rightstop = stopdic['Utica']
stopdic['Utica'].rightstop = stopdic['Rome']
stopdic['Rome'].rightstop = stopdic['Syracuse']#skip new york state fair
stopdic['Syracuse'].rightstop = stopdic['Rochester']
stopdic['Rochester'].rightstop = stopdic['Buffalo-Depew']
stopdic['Buffalo-Depew'].rightstop = stopdic['Buffalo-Exchange St.']
stopdic['Buffalo-Exchange St.'].rightstop = stopdic['Niagara Falls, NY'] 
stopdic['Niagara Falls, NY'].rightstop = stopdic['Niagara Falls, ON']
stopdic['Niagara Falls, ON'].rightstop = stopdic['St. Catharines']
stopdic['St. Catharines'].rightstop = stopdic['Grimsby']
stopdic['Grimsby'].rightstop = stopdic['Aldershot']
stopdic['Aldershot'].rightstop = stopdic['Oakville']
stopdic['Oakville'].rightstop = stopdic['Toronto']


#get trip information

tripstxt = open("baselineGTFS/trips.txt", 'r')
stoptimestxt = open("baselineGTFS/stop_times.txt", 'r')

triplist = []# a list of trip id in the GTFS
tripdic = {}#a dictionary to access any trip by key
for row in tripstxt:#loop through trips
    row = row.strip()
    rowlist = row.split(',')
    
    if rowlist[0] == 'trip_id':
        continue
    triplist.append(rowlist[0])#add trip id to list of every trip id
    tripclass = trip()#create object associated with trip id
    tripdic[rowlist[0]] = tripclass#add object for trip id to dictionary
    tripclass.tripid = rowlist[0]

for row in stoptimestxt:#loop through stop times
    row = row.strip()
    rowlist = row.split(',')
    if rowlist[0] == 'trip_id':
        continue
    #create the trip patterns for each trip
    stopclass = stop()#object to hold info and sequence number
    stopclass.sequence = rowlist[1]#sequence number from stopstimes.txt
    stopclass.info = stopdic[rowlist[2]]#point to info associated with stop
    
    tripdic[rowlist[0]].pattern.append(stopclass)#add pattern to trip object
    
    
#read shape data

shp = fiona.open('Amtrakgis/AMTRAK.shp', 'r')
segmentlist = []#list of all segments that will be extracted from shp file
for i in range(len(shp)):#loop through each segment and extract coordinates
    convertlist = []#list to hold extracted coordinates
    data = (shp[i]['geometry']['coordinates'])#access coordinates in GeoJSON
    
    #extract all coordinates in segment and convert to lat/long. The data can be in the form of a tuple or a list. Coordinates must be converted into lat/long from UTM-WGS84
    if type(data[0]) is tuple:
        for ii in range(len(data)):
            conversion = utm.to_latlon(data[ii][0], data[ii][1], 18, 'U')
            convertlist.append(conversion)
            
    elif type(data[0]) is list:
        for ii in range(len(data)):
            for iii in range(len(data[ii])):
                conversion = utm.to_latlon(data[ii][iii][0], data[ii][iii][1], 18, 'U')
                convertlist.append(conversion)
    
    #append the list of converted coordinates to a list to hold all list of converted coordinates for each segment
    segmentlist.append(convertlist)
    

#hardcode segment assignments to map of stops (segment numbers determined manually)
stopdic['New York Penn Station'].rightshape = segmentlist[22]
stopdic['Yonkers'].rightshape = segmentlist[21]
stopdic['Croton-Harmon'].rightshape = segmentlist[1]
stopdic['Poughkeepsie'].rightshape = segmentlist[20]
stopdic['Rhinecliff'].rightshape = segmentlist[19]
stopdic['Hudson'].rightshape = segmentlist[18]
stopdic['Albany/Rensselaer'].rightshape = segmentlist[17]
stopdic['Schenectady'].leftshape = segmentlist[16]
stopdic['Schenectady'].rightshape = segmentlist[3]
stopdic['Saratoga Springs'].rightshape = segmentlist[31]

multiple = segmentlist[5] + segmentlist[34]
stopdic['Fort Edward-Glens Falls'].leftshape = multiple


#stopdic['Fort Edward-Glens Falls'].rightshape = segmentlist[4]#going southbound IGNORE THIS
stopdic['Whitehall'].rightshape = segmentlist[30]
stopdic['Ticonderoga'].rightshape = segmentlist[29]
stopdic['Port Henry'].rightshape = segmentlist[28]

multiple = segmentlist[27] + segmentlist[26]
stopdic['Westport'].rightshape = multiple

stopdic['Plattsburgh'].rightshape = segmentlist[25]
stopdic['Rouses Point'].rightshape = segmentlist[32]
stopdic['Amsterdam'].rightshape = segmentlist[15]
stopdic['Utica'].rightshape = segmentlist[14]
stopdic['Rome'].rightshape = segmentlist[13]

multiple = segmentlist[12] + segmentlist[11]
stopdic['Syracuse'].rightshape = multiple

stopdic['Rochester'].rightshape = segmentlist[10]

multiple = segmentlist[9] + segmentlist[8]
stopdic['Buffalo-Depew'].rightshape = multiple

stopdic['Buffalo-Exchange St.'].rightshape = segmentlist[7]



#Use a depth first search algorithm to determine which segments must be used to reach the next stop


def getsequence(elem):
    return int(elem.sequence)

visitedlist = []#a global list used to hold the final path the next stop. THIS HOLDS ALL STOPS VISITED IN TRAVERSE
targetfound = False#the first stop is the current stop. The last stop is the next stop. In between, are stops that may or may not be on the way added from traversal of the tree
def traverse(pointer, target):
    visitstack = []#create a list local stack of all that hold stops where diverging is possible
    global visitedlist#reference global list that final path will be stored to
    global targetfound#reference the global variable- this is global because the function is called recursively
    
    if targetfound is True or target is None:#break out of the recursive function if the target is found or there are no stops furthur north
        return
    
    visitedlist.append(pointer)#add each visited station to the global visited list
    
    if pointer == target:#target found
        targetfound = True#set the targetfound to be true so no more recurvive calls go through for this stop
        return
    
    #add the adjacent stops the visited stack
    if pointer.rightstop != None:
        visitstack.append(pointer.rightstop)
    if pointer.leftstop != None:
        visitstack.append(pointer.leftstop)
    
    
    if len(visitstack) == 0:#this happens if there are no stops to end
        return
    
    for i in range(len(visitstack)):#loop though the stack of stops to visit. The stack is a local variable so each stop has it's own stack of zero, one, or two
        traverse(visitstack[i], target)#recursivly loop through the stack of stops to be visited
    
def cleanpath():
    global visitedlist#reference the global visitedlist for this scope. 
    
    #two indices needed to loop through the list
    index1 = len(visitedlist)-1
    index2 = index1-1
    while index2 >= 0:#the list is cleaned by looping backward though the list and removing stops and do not that are not linked in the map tree
        if visitedlist[index2].leftstop != visitedlist[index1] and visitedlist[index2].rightstop != visitedlist[index1]:
            visitedlist.pop(index2)
        index1-= 1#move the indices back. if an object does not get popped, move to the next object and see if they are connected in the tree.
        index2-= 1#if an object does get popped, the indices will point to different objects as the size of list has changed so the indices must be move back to where they were
    
        
    
for i in range(len(triplist)):#loop through all trips and create shape for each one
    tripclass = tripdic[triplist[i]]#get the trip's object
    #sort the list by sequence
    trippattern = tripclass.pattern#get the list of stops in this pattern
    trippattern.sort(key=getsequence)#sort the list based on sequence (sequence can be different depending on direction)

    #determine direction of the trip-all trips originate or terminate at New York Penn Station. Check the last stop to see if trip is northbound or southbound
    if trippattern[len(trippattern)-1].info.name == 'New York Penn Station':
        trippattern.reverse()#if the trip is southbound, reverse the list as if it were going northound-the map tree can only be traversed in the northbound direction. Another reversal will take place later.
        southbound = True
    else:
        southbound = False

    #now loop through the trip pattern
    for ii in range(len(trippattern)):
        
        #clear the list here -clear list function not available in python2
        while(len(visitedlist) != 0):
            visitedlist.pop()
        
        
        targetfound = False#for each new target, the global variable is defaulted to false
       
        pointer = trippattern[ii]#pointer used for traversing the map tree
        
        if pointer.info in outsideny:#for stops outside New York
            tripclass.shapecoord.append(pointer.info.coord)
            
            if ii == (len(trippattern)-1):
                break
            else:
                continue#track maps not supported for outside NY stops
        
        if ii == (len(trippattern)-1):
            break#break out of loop at end of pattern so traverse is not called
        

        target = trippattern[ii+1]#set the target to be the next stop 
        traverse(pointer.info, target.info)#traverse the map tree to determine the path to the next stop. Pass in info on the current stop and what the next stop is 
        cleanpath()#clean the path of visited stations to the shortest path to the next station
        
        #visitedlist holds the cleaned path, now assemble the shapes for the path
        for iii in range(len(visitedlist)-1):#loop through the visited list 
            #for each stop, select the shape that leads to the next stop in the path
            if visitedlist[iii].leftstop == visitedlist[iii+1]:
                nextpath = visitedlist[iii].leftshape
            elif visitedlist[iii].rightstop == visitedlist[iii+1]:
                nextpath = visitedlist[iii].rightshape
            
            #next path is a list of coordinatates in between two stops. This last for loop takes those coordinates and adds them to a master list of coordinates for the whole trip
            for i4 in range(len(nextpath)):
                tripclass.shapecoord.append(nextpath[i4])
    #reverse the order of the list of coordinates for southbound trips since they were ordered as if the trip was going northbound
    if southbound == True:
        tripclass.shapecoord.reverse()
        
#close old files
stopstxt.close()
stoptimestxt.close()
tripstxt.close()

#make the new GTFS files shapes.txt & trips.txt
with open('shapes.txt', mode='w') as newshapes:
    newshapes.write('shape_id,shape_pt_sequence,shape_pt_lat,shape_pt_lon')#write the first row
    newshapes.write('\n')
    

    for i in range(len(triplist)):#loop trip through each trip and write the shape coordinates for each trip
        tripclass = tripdic[triplist[i]]
        tripclass.shapeid = 'shape' + str(tripclass.tripid)#assign a shapeid the the trip and shape (using the tripid)
        for ii in range(len(tripclass.shapecoord)):#write the to the shapes.txt file
            newshapes.write(tripclass.shapeid)
            newshapes.write(',')
            newshapes.write(str(ii))
            newshapes.write(',')
            newshapes.write(str(tripclass.shapecoord[ii][0]))
            newshapes.write(',')
            newshapes.write(str(tripclass.shapecoord[ii][1]))
            newshapes.write('\n')
    
    newshapes.close()

#create a new trips.txt file that updates the shapeid associated with each trip
oldtrips = open("baselineGTFS/trips.txt", 'r') 
with open('trips.txt', mode='w') as newtrips:
    for row in oldtrips:
        row = row.strip()
        rowlist = row.split(',')
        
        if rowlist[0] == 'trip_id':
            pass
        else:   
            rowlist[7] = tripdic[rowlist[0]].shapeid
            
        for i in range(len(rowlist)):
            newtrips.write(rowlist[i])
            if i != len(rowlist)-1:
                newtrips.write(',')
        newtrips.write('\n')
    

    newtrips.close()
oldtrips.close()


#update stops_times.txt file removing shape_dist_travel causing OpenTripPlanner to reject
oldstoptimes = open("baselineGTFS/stop_times.txt", 'r')
with open('stop_times.txt', mode='w') as newstoptimes: 
    for row in oldstoptimes:
        row = row.strip()
        rowlist = row.split(',')
        
        for i in range(len(rowlist)):
            if i == 8:
                pass
            else:
                newstoptimes.write(rowlist[i])
            
            if i != len(rowlist)-1 and i != 8:
                newstoptimes.write(',')
        newstoptimes.write('\n')
    newstoptimes.close()
oldstoptimes.close()
