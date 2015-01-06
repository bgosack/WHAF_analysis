#-------------------------------------------------------------------------------
# Name:        calcMajorAquaConn_OldMethods.py
# Purpose:     This script attempts to use Z Tagar's approach to calculate the 
#              major scale aquatic connectivity.
#
# Author:      begosack
#
# Created:     12/30/2014
# Copyright:   (c) begosack 2014
# Licence:     <your licence>
#-------------------------------------------------------------------------------

import arcpy, time, sys

t1 = time.time()

arcpy.env.overwriteOuput = True

# get input parameters: inCatch = Catchments with index values calculated, inCatch = major watersheds that will be copied to create an output, 
inStreams = r'D:\Users\begosack\Documents\WHAF\Index_Development\Connectivity\Aquatic_Connectivity\Data\Inputs.gdb\zTagar_StreamsForAnalysis'
inLakes = r'
#inClipCatch = r'D:\Users\begosack\Documents\GIS_Data\WHAF_Inputs.gdb\DNR_Level_08_Catchments_MN_Clip_WatArea'
inCatch = r'D:\Users\begosack\Documents\GIS_Data\WHAF_Inputs.gdb\DNR_Level_08_Catchments_MN_Clip_WatArea' 
inScale = 'Catchment' # dropdown with major or catchment as the two options
outDir = r'D:\Users\begosack\Documents\WHAF\Index_Development\Connectivity\Aquatic_Connectivity\Data\Outputs.gdb'
inDams = r'D:\Users\begosack\Documents\WHAF\Index_Development\Connectivity\Aquatic_Connectivity\Data\Inputs.gdb\dam_locations'
inDOT = r'D:\Users\begosack\Documents\WHAF\Index_Development\Connectivity\Aquatic_Connectivity\Data\Inputs.gdb\dot_bridge_and_culvert_inventory'
threshold = 1

outWS = r'D:\Users\begosack\Documents\WHAF\Index_Development\Connectivity\Aquatic_Connectivity\Data\Outputs.gdb\Catchment_AquaConn_OldMethods'
tempWS = r'in_memory\tempWS'

# get value of ID field to calc summary stats on
if inScale == 'Catchment':
	idField = "CATCH_ID"
elif inScale == 'Major':
	idField = 'major'
elif inScale == 'Upstream':
	idFields = '????'
	#arcpy.AddMessage('Script Failed: \n\t The parameters have not yet been set up for upstream area analysis.')
	print 'Script Failed: \n\t The parameters have not yet been set up for upstream area analysis.'
	sys.exit()
else:
	#arcpy.AddMessage('Script Failed: \n\t Not registering the field name.')
	print 'Script Failed: \n\t Not registering the field name.'
	sys.exit()

# upstream and downstream query functions

def findUpstreamCatchments(catchment,catchmentDict,upCatchmentList):
    upCatchments = str(catchmentDict.get(catchment)[0])
    catchmentLst = str.split(upCatchments," ")
    for aCatchment in catchmentLst:
        aCatchmentn = aCatchment
        aCatchmentInfo = catchmentDict.get(aCatchmentn)
        if aCatchmentInfo:
            upCatchmentList.append(aCatchmentn)
            findUpstreamCatchments(aCatchmentn,catchmentDict,upCatchmentList)

def findDownstreamCatchments(catchment,catchmentDict,upCatchmentList):
    downCatchment = catchmentDict.get(catchment)[1]
    if downCatchment:
        aCatchmentn = downCatchment
        aCatchmentInfo = catchmentDict.get(aCatchmentn)
        if aCatchmentInfo:
            upCatchmentList.append(aCatchmentn)
            findDownstreamCatchments(aCatchmentn,catchmentDict,upCatchmentList)

# create copy of input watersheds and add output fields 
arcpy.AddMessage('\nAdding fields...')
if arcpy.Exists(outWS):
	arcpy.Delete_management(outWS)
arcpy.CopyFeatures_management(inCatch, outWS)
arcpy.AddField_management(outWS, 'Dam_Count', 'DOUBLE')
arcpy.AddField_management(outWS, 'Bridge_Count', 'DOUBLE')
arcpy.AddField_management(outWS, 'Culvert_Count', 'DOUBLE')
arcpy.AddField_management(outWS, 'Catchment_Stream_Length', 'DOUBLE')
arcpy.AddField_management(outWS, 'Avg_Stream_Length', 'DOUBLE')
arcpy.AddField_management(outWS, 'Structure_Density', 'DOUBLE')
arcpy.AddField_management(outWS, 'C_I_AC', 'SHORT')
t2 = time.time()
arcpy.AddMessage('Fields added! - {0} sec'.format(round(t2-t1, 2)))

# # buffer streams layer by 100 m and clip all structures to the buffer distance
# arcpy.AddMessage('\nBuffering streams and clipping structures...')
# buffStreams = r'in_memory\buffStreams'
# clipDams = r'in_memory\clipDams'
# clipDOT = r'in_memory\clipDOT'
# #arcpy.Buffer_analysis(inStreams, buffStreams, 100)
# arcpy.Buffer_analysis(inStreams, buffStreams,"100 Meters","FULL","ROUND","NONE","#")
# print 'buffer'
# arcpy.Clip_analysis(inDams, buffStreams, clipDams)
# print 'clip 1 of 2'
# arcpy.Clip_analysis(inDOT, buffStreams, clipDOT)
t3 = time.time()
# arcpy.AddMessage('Buffered and Clipped! - {0} sec'.format(round(t3-t2, 2)))
# arcpy.Delete_management(buffStreams)

# above commented out code can be uncommented to rerun buffer and clip ~ 20 min analysis process
clipDams = r'D:\Users\begosack\Documents\ArcGIS\Default.gdb\dam_locations_Clip'
clipDOT = r'D:\Users\begosack\Documents\ArcGIS\Default.gdb\DOT_clip1'

# intersect point features with majors to get features by watershed ID. 
arcpy.AddMessage('\nIntersecting feature classes and watersheds...')
arcpy.Intersect_analysis([inStreams, inCatch], r'in_memory\intersectStreams')
arcpy.Intersect_analysis([clipDams, inCatch], r'in_memory\intersectDams')
arcpy.Intersect_analysis([clipDOT, inCatch], r'in_memory\intersectDOT')
#arcpy.Delete_management(clipDams)
#arcpy.Delete_management(clipDOT)
t4 = time.time()
arcpy.AddMessage('Intersected! - {0} sec'.format(round(t4-t3, 2)))

# dissolve streams on watershed id, so as to get a total length of stream per watershed. 
arcpy.AddMessage('\nDissolving streams on watershed ID...')
arcpy.Dissolve_management('in_memory\\intersectStreams', 'in_memory\\dissolveStreams', idField)
t5 = time.time()
arcpy.AddMessage('Dissolved! - {0} sec'.format(round((t5 -t4),2)))

# create dictionaries from dissolved or intersected feature classes.
arcpy.AddMessage('\nCreating dictionaries...')

# stream dictionary {CATCH_ID : Stream_Length}
Streams = {}
with arcpy.da.SearchCursor('in_memory\\dissolveStreams', [idField, 'SHAPE@LENGTH']) as cur:
	for row in cur:
		if row[0] in Streams:
			print '****ERROR: Streams row is duplicated!!!'
		else:
			Streams[row[0]] = [row[1]]
	del row
del cur

Dams = {}
with arcpy.da.SearchCursor('in_memory\\intersectDams', [idField]) as cur1:
	for row1 in cur1:
		if row1[0] in Dams:
			Dams[row1[0]].append(1)
		else:
			Dams[row1[0]] = [1]
	del row1
del cur1
arcpy.Delete_management('in_memory\\intersectDams')

Bridges = {}
with arcpy.da.SearchCursor('in_memory\\intersectDOT', [idField], "Bridg_culv = 'bridge'") as cur2:
	for row2 in cur2:
		if row2[0] in Bridges:
			Bridges[row2[0]].append(1)
		else:
			Bridges[row2[0]] = [1]
	del row2
del cur2

Culverts = {}
with arcpy.da.SearchCursor('in_memory\\intersectDOT', [idField], "Bridg_culv = 'culvert'") as cur3:
	for row3 in cur3:
		if row3[0] in Culverts:
			Culverts[row3[0]].append(1)
		else:
			Culverts[row3[0]] = [1]
	del row3
del cur3
arcpy.Delete_management('in_memory\\intersectDOT')

# create catchment list and dictionary
featureRow=[]
upCatchmentList=[]
downCatchmentList=[]
catchmentDict = {}

with arcpy.da.SearchCursor(outWS, [idField, "UPADJ_CAT", "DOWN_CAT", "MAJOR"] ) as cur:
	for row in cur:
	    featureRow.append(row[0])
	    catchmentDict[row[0]] = [row[1], row[2], row[3]]
	del row
del cur

# Use catchment dictionary to calculate mean stream length for up and downstream catchment within the same major watershed
catchStrDict = {}
count=1
for catchment in featureRow:
	#print catchment
	watershed= catchmentDict.get(catchment)[2]
	UpCatchmentList=[catchment]
	findUpstreamCatchments(catchment,catchmentDict,UpCatchmentList)

	downCatchmentList=[catchment]
	findDownstreamCatchments(catchment,catchmentDict,downCatchmentList)

	upDownCatchmentList=downCatchmentList+UpCatchmentList

	# Build a to select watersheds in the upstream/downstream list
	i = 0
	for h in upDownCatchmentList:
		if i == 0:
			theStr = "'{0}'".format(h)
		else:
			theStr = "{0}, '{1}'".format(theStr, h)
		i+=1
	theQuery = """("CATCH_ID" IN ({0})) AND "MAJOR" = {1}""".format(theStr, str(watershed))

	# Use query to calc mean stream length for each catchment - mean length based on the average of all upstream and downstream catchments of the give catchment within the major watershed containing the catchment
	CatchStrLen=[]

	with arcpy.da.SearchCursor(outWS, [idField], theQuery) as cur:
		for row in cur:
			if row[0] in Streams:
				streamLength = Streams[row[0]][0]
			elif row[0] not in Streams:
				streamLength = 0
			CatchStrLen.append(streamLength)
		del row
	del cur
	arcpy.Delete_management(r'in_memory\vWatershed')

	if len(CatchStrLen) > 0:
		meanLen = (sum(CatchStrLen)/1609.34)/ len(CatchStrLen)
	else: 
		meanLen = 0
	catchStrDict[catchment] = meanLen
	#print meanLen
	count+=1
	arcpy.AddMessage('{0}'.format(count))
#print len(catchStrDict) 
t6 = time.time()
arcpy.AddMessage('Dictionaries created! - {0} sec'.format(round((t6 -t5),2)))


# use and update cursor to calculate the field for the output watershed feature class
arcpy.AddMessage('\nCalculating watershed fields...')

with arcpy.da.UpdateCursor(outWS, [idField, 'Dam_Count', 'Bridge_Count', 'Culvert_Count', 'Avg_Stream_Length', 'Structure_Density', 'C_I_AC', 'Catchment_Stream_Length']) as cur4:
	for row4 in cur4:
		#if row4[0] in Streams:
			#streamLen = (Streams[row4[0]][0]/1609.34) # convert meters stream to miles
		#else:
		#	streamLen = 0
		if row4[0] in catchStrDict:
			streamLen = catchStrDict[row4[0]]
		else:
			print '{0} not in average stream length dictonary'
			streamLen = 0
		if row4[0] in Streams:
			catchStreams = Streams[row4[0]][0]
		else: 
			catchStreams = 0
		if row4[0] in Dams:
			damCount = len(Dams[row4[0]])
		else: 
			damCount = 0
		if row4[0] in Bridges:
			bridgeCount = len(Bridges[row4[0]])
		else:
			bridgeCount = 0 
		if row4[0] in Culverts:
			culvertCount = len(Culverts[row4[0]])
		else:
			culvertCount = 0

		structureCount = damCount + bridgeCount + culvertCount 
		if streamLen > 0:
			structureDensity = structureCount / streamLen		
			if structureDensity > threshold:
				scr = 0
			else:
				scr = ((1 - (structureDensity/threshold)) * 100)
		else:
			scr = 100

		row4[1] = damCount
		row4[2] = bridgeCount
		row4[3] = culvertCount
		row4[4] = streamLen
		row4[5] = structureDensity
		row4[6] = scr
		row4[7] = catchStreams

		cur4.updateRow(row4)
	del row4
del cur4

t7 = time.time()
arcpy.AddMessage('Fields calculated!  -  {0} sec'.format(round((t7-t1),2)))
