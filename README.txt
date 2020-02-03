The objective of this program is to take GIS data of railroad tracks throughout New York State and use it as GTFS Data. The baseline GTFS consists of schedule information for Amtrak's Empire Corridor Service throughout New York State. Previously, each trip rendered on the map with straight lines in between stations, as opposed to rendering the geogopraphically accurate shapes of the railroad tracks. Using this GIS data, this program creates a new shapes.txt file and a new trips.txt file taking in a GIS shp file and a baseline GTFS feed. 

**************Declarations************

There are three object classes declared to hold information about the stops and trips. 

The stopinfo class holds information about the stop, including information from stops.txt. This class is used to create a map in the form of a binary tree, pointing to its next stop as its right child. An object may also have a left child if the tracks north of the its respective station diverge resulting in two possible paths for the train. A stopinfo object also holds lists of coordinates making up the path shape to the stations that are its children in the binary tree. 

The stop class has a pointer to the stopinfo object for it's respective station. It also holds the sequence number from stops_times.txt. This number varys by trip (northbound vs southbound) and is not constant for each stop and is stored in a separate object from it's respective stopinfo object.

The trip class holds information about the trip, including information the trip id as well as a list holding stop objects for each station this trip stops at (pattern). It also holds a list of every coordinate that makes up the shape that is associated with this trip (shapecoord). 


stopdic is a dictonary that holds each stopinfo class created with its keys being the value of stopid as well as the station name

triplist is a list that holds tripids for each trip and is used to loop through every possible trip as needed

tripdic is a dictionary that holds each tripid class created with its keys being the value of tripid

convertlist is a local list that holds coordinates converted from UTM-WGS84. 35 segments of coordinates in UTM-WGS84 in the form of lists or tuples of lists. For each segment, the coordinates are extracted and converted and stored in this list. A copy of this list is then stored as a list within the segmentlist. This is done for all 35 segments of coordinates from the shp file. 

segmentlist is a global list that that holds the 35 lists holding of the coordinates from the GIS shp file coverted. This list is used to assign shapes to stopinfo objects for assembling the trip shape. 


getsequence is a function that takes in a stop object and returns only the sequence associated with that object. This is used as a key for sorting a list of stop objects. 

visitedlist is a global list that is generated for each stop for each pattern (except the origin station). This holds every stop object visited in a traversal of the binary tree to locate the next station and determine the shortest path as a result of the traverse function. The list is also cleaned to the shortest path to the next station by the cleanpath funtion. This list is used to select the segmentlist shapes used to make the shape for each trip from origin to destination. 

traverse is a function that takes in a pointer to a stopinfo object in the binary tree, as well as a pointer to the target that is stopinfo object representing the next station. The function has its own stack in the form of a list (visitstack) and it holds all children of the stopinfo objects that are traversed. The function is called recursivly, so each object in the tree has its own visitstack list. For every recursive function call, the function moves the pointer to the object's right child and compares the stopinfo object it is pointing to with the target. Each stopinfo object is added to the global visitedlist list that holds all stopinfo objects that have been visited during the traversal of a tree for each station (the visitedlist is cleared for each new station). If the target is found, a global boolean variable is used to terminate any function calls. The traversal defaults to the right child of each object in the tree. If the pointer reaches the end of the path and the target is not found because it traversed the wrong path, the recursive function calls will end until a scope is reached where there is a second stopinfo object in the visitclass list, representing another possible traversal. This process continues until the target is found. All stopinfo objects visited in this traversal are added to the global visitedlist list when the pointer points to them for this first time for each target.

cleanpath is a function that refers to the global visitedlist list generated for each station in the trip and removes stations that are not on the way to the next stop for the trip which may have been added from traversing the wrong path in the binary tree. Two indices are created-one pointing to the next station at the end of the list and one pointing to the stopinfo object before that in the list. The two indices are used to verify that they are connected in the binary tree. If the two objects are connected in the binary tree, then they are in the path to the next station and the order of their placement in the list is correct. The two indices are then decremented by one in the list so the next station in the list going backward is checked.  If the two objects are not connected, then parent object being checked does in the path to the next station. The parent object is popped from the list. In this case,the two indices are also decremented by one. This is because the size of the list changes with the popping of an object and the indices must be decremented to point to the next objects to be checked. This process repeats under a while loop until an index points out of range for the list and the list now has the stopinfo objects in order resembling the shortest path to the next station. 


*********Program Sequence***********
The following events occur in the event flow of this program 

Read baseline GTFS Data
Create Map in form of Binary Tree based on the GTFS data
Read GIS Shape Data
Build on Binary Tree assigning extracted shape data to objects
Assemble shapes for each trip in GTFS using data from Binary Tree
Create New GTFS files

The program begins by extracting relevant data from the baseline GTFS feed. The program loops through the baseline GTFS stops.txt file and creating stopinfo objects for each stop.

The binary map tree is then hard-coded with New York Penn Station as the root object going northbound towards Albany, Buffalo, and Canada. This is done with using the stopdic dictionary with station names as the keys.

The program loops through the baseline trips.txt and and creates trip objects for each trip

The program loops through the baseline stop_times.txt file. For each stop time, the a stop object is created with the sequence number from stop_times.txt. The stop_id is also used to associate the stop object with its respective stopinfo object. Finally, the stop object is added to the pattern list of the trip so that the sequence numbers are saved associated with the trip. This concludes extracting all relevant data from the baseline GTFS

The program proceeds to extract GIS data from the shpfile using shapefile and fiona libraries. Opening the shp file returns a list of 35 different segments. Each segment contains data in GeoJSON, including coordinates as a list or a tuple of lists. The coordinates for each segment are in UTM-WGS84 so are extracted and converted into lat/long before being stored into the convertlist list. For segment has it's own list of extracted and converted coordinates and each segment is geograhpically adjacent to another segment. The convertlist for each segment is stored in the segmentlist list.

Each list of coordinates is assigned to manually assigned to an object in the binary tree based on geographic location. This is done with using the stopdic dictionary with station names as the keys.

With the binary tree assembled with stops as well as shape data, the program begins assembling full shapes for each trip from the GTFS.

For each trip, the its pattern list of all stops serviced by the trip is sorted  by sequence, in the event that they were not sorted already in the trips.txt file. The getsequence function is used for this.

Next the program determines whether the trip is going northbound or southbound. All trips either originate or terminate at New York Penn Station, so the trip is southbound if the last element in the patternlist is the stopinfo object for New York Penn Station. If the trip is southbound, the pattern list is reversed. This is done because objects in the binary tree are not doubly linked and the tree can only be traversed in the northbound direction.

Now the shape is assembled by combining stations and shapes in the trip object's shapecoord list. For each stop looping through each trip's patternlist list, the stop coordinates are added to the trip object's shapecoord list. Following that, the traverse algorithm is called with the poiinter set to the current station as in the list with the index of the for loop. The next station in the list is set passed into traverse as the target. The traverse and clean functions are called to find the path to the next station. The global visitedlist list ends up with this shortest path. Looping through the visitedlist list that is generated for each stop in the trip pattern list, the track shape to the next station is selected by checking if the next station is a left child or right child of the current station's stopinfo object in the loop through the visitedlist list, then selecting stopinfo object's right or left shape respectivly. Finally, with the shape to the next station selected, all of the coordinates making up the shape are added to the trip object's shapecoord list. This is done for each stop in the trip object's pattern list. The result is a shape consisting of every coordinate between the trip's origin and destination stored to the trip object's shapecoord list. The trip coordlist gets reversered for southbound trips since it was made as if the trip was nothbound. 

Now with the shape assembled, the new gtfs is assembled. A new shapes.txt is created. For each trip, a new shapeid is created to associate with the each trip. Then the new tripid and each coordinate in the appropriate trip object's shapecoordlist is written to the new shapes.txt file. The trip object's new shape id is stored so the trips.txt can also be updated. 

The new trips.txt file is created to replace the shapeid's associated with each trip with the newly generated ones using the shapeid stored as an attribute of the trip object. 

The new GTFS files appear in the same directory in this script when it is run. 




