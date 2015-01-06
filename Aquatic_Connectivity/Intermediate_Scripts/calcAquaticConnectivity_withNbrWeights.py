#-------------------------------------------------------------------------------
# Name:        calcAquaticConnectivity.py
# Purpose:     This script uses point files for bridges, culverts and dams, as
#              well as line file for perennial streams to calculate the dnsity
#              of structures per unit of stream length. with a measure of stream 
#              length per watershed and a count of structures per watershed, we 
#              calculate the density. Using a catchment neighborhood analyis we 
#              measure the relative connectivity by weighting the catchment at 1.0
#              imediately adjacent (and hydrologically connected) catchments at .5,
#              and catchments removed by
#
# Author:      begosack
#
# Created:     12/22/2014
# Copyright:   (c) begosack 2014
# Licence:     <your licence>
#-------------------------------------------------------------------------------
import arcpy, time


t1 = time.time()
arcpy.env.overwriteOutput = True

# inputs
inStreams = r'D:\Users\begosack\Documents\WHAF\Index_Development\Connectivity\Aquatic_Connectivity\Data\Inputs.gdb\AlteredWater_type1n2'
inWS = r'D:\Users\begosack\Documents\GIS_Data\WHAF_Inputs.gdb\DNR_Level_08_Catchments_MN_Clip_WatArea'
inScale = 'Catchment' # dropdown with major or catchment as the two options
inDams = r'D:\Users\begosack\Documents\WHAF\Index_Development\Connectivity\Aquatic_Connectivity\Data\Inputs.gdb\dam_locations'
inDOT = r'D:\Users\begosack\Documents\WHAF\Index_Development\Connectivity\Aquatic_Connectivity\Data\Inputs.gdb\dot_bridge_and_culvert_inventory'
# identified by assessing the 95th percentile of the density values calculated in this script
threshold = 2.006743119


# outputs
outWS = r'D:\Users\begosack\Documents\WHAF\Index_Development\Connectivity\Aquatic_Connectivity\Data\Outputs.gdb\Output_Catchments_AltStr_AvgLen'


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


# create copy of input watersheds and add output fields 
arcpy.AddMessage('\nAdding fields...')
arcpy.CopyFeatures_management(inWS, outWS)
arcpy.AddField_management(outWS, 'Dam_Count', 'DOUBLE')
arcpy.AddField_management(outWS, 'Bridge_Count', 'DOUBLE')
arcpy.AddField_management(outWS, 'Culvert_Count', 'DOUBLE')
arcpy.AddField_management(outWS, 'Stream_Length', 'DOUBLE')
arcpy.AddField_management(outWS, 'Nbrhd_Dam_Count', 'DOUBLE')
arcpy.AddField_management(outWS, 'Nbrhd_Bridge_Count', 'DOUBLE')
arcpy.AddField_management(outWS, 'Nbrhd_Culvert_Count', 'DOUBLE')
arcpy.AddField_management(outWS, 'Nbrhd_Stream_Length', 'DOUBLE')
arcpy.AddField_management(outWS, 'Structure_Density', 'DOUBLE')
arcpy.AddField_management(outWS, 'C_I_AC', 'SHORT')
arcpy.AddMessage('Fields added!')


# intersect point features with catchments to get features by watershed ID. 
arcpy.AddMessage('\nIntersecting feature classes and watersheds...')
arcpy.Intersect_analysis([inStreams, inWS], 'in_memory\\intersectStreams')
arcpy.Intersect_analysis([inDams, inWS], 'in_memory\\intersectDams')
arcpy.Intersect_analysis([inDOT, inWS], 'in_memory\\intersectDOT')
arcpy.AddMessage('Intersected!')


# dissolve streams on watershed id, so as to get a total length of stream per watershed. 
arcpy.AddMessage('\nDissolving streams on watershed ID...')
arcpy.Dissolve_management('in_memory\\intersectStreams', 'in_memory\\dissolveStreams', idField)
t2 = time.time()
arcpy.AddMessage('Dissolved! - {0} sec'.format(round((t2 -t1),2)))


# create dictionaries from dissolved or intersected feature classes.
arcpy.AddMessage('\nCreating dictionaries...')

# stream dictionary {CATCH_ID : Stream_Length}
Streams = {}
with arcpy.da.SearchCursor('in_memory\\dissolveStreams', [idField, 'SHAPE@LENGTH']) as cur:
	for row in cur:
		Streams[row[0]] = [row[1]]
	del row
del cur

Dams = {}
with arcpy.da.SearchCursor('in_memory\\intersectDams', [idField, 'TopDamHGT']) as cur1:
	for row1 in cur1:
		if row1[0] in Dams:
			try:
				Dams[row1[0]].append(row1[1])
			except:
				Dams[row1[0]].append('null')
		else:
			if row1[1]:
				Dams[row1[0]] = [row1[1]]
			else:
				Dams[row1[0]] = ['null']
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

t3 = time.time()
arcpy.AddMessage('Dictionaries created! - {0} sec'.format(round((t3 -t2),2)))

avgStream = {}

# use and update cursor to calculate the field for the output watershed feature class
arcpy.AddMessage('\nCalculating watershed fields...')
Catchments = {}
with arcpy.da.UpdateCursor(outWS, [idField, 'Dam_Count', 'Bridge_Count', 'Culvert_Count', 'Stream_Length', 'Structure_Density', 'UP_COUNT', 'UPADJ_CAT', 'DOWN_CAT', 'MAJOR']) as cur4:
	for row4 in cur4:
		if row4[0] in Streams:
			streamLen = (Streams[row4[0]][0]/1609.34) # convert meters stream to miles
		else:
			streamLen = 0
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
		
		row4[1] = damCount
		row4[2] = bridgeCount
		row4[3] = culvertCount
		row4[4] = streamLen
		
		# if streamLen > 0:
		# 	structureDensity = structureCount/float(streamLen)
		# 	row4[5] = structureDensity

		# append stream length to average stream dictionary
		if row4[9] in avgStream:
			avgStream[row4[9]].append(streamLen)
		else:
			avgStream[row4[9]] = [streamLen]

		# create a list of the upstream and downstream immediately adjacent catchments
		if row4[6] > 0:
			Adjacent = row4[7].split()
			Adjacent.append(row4[8])
		else:
			Adjacent = [row4[8]]

		# create an entry in the catchments dictionary to use in neighborhood analysis
		Catchments[row4[0]] = [Adjacent, damCount, bridgeCount, culvertCount, streamLen]

		#print '{0}'.format(Catchments[row4[0]])
		cur4.updateRow(row4)
	del row4
del cur4

arcpy.AddMessage('Catchments Dictionary Length: {0}'.format(len(Catchments)))

t4 = time.time()
arcpy.AddMessage('Fields calculated!  -  {0} sec'.format(round((t4-t3),2)))	


# use a Catchments dicionary to calculate neighborhood values for structure counts and stream lengths
counter = 0
missing = []
arcpy.AddMessage('\nCalculating neighborhood fields...')

with arcpy.da.UpdateCursor(outWS, [idField, 'Nbrhd_Dam_Count', 'Nbrhd_Bridge_Count', 'Nbrhd_Culvert_Count', 'Nbrhd_Stream_Length', 'Structure_Density', 'C_I_AC', 'MAJOR']) as cur5:
	for row5 in cur5:

		# get structure counts within catchment
		nbrList = Catchments[row5[0]][0]
		damList = [Catchments[row5[0]][1]]
		bridgeList = [Catchments[row5[0]][2]]
		culvertList = [Catchments[row5[0]][3]]
		streamList = [Catchments[row5[0]][4]]

		# use neighbor list to get structure count on neighboring catchments
		for nbr in nbrList:
			try:
				damList.append((Catchments[nbr][1]*0.5))
				bridgeList.append((Catchments[nbr][2]*0.5))
				culvertList.append((Catchments[nbr][3]*0.5))
				streamList.append((Catchments[nbr][4]*0.5))
			except:
				#arcpy.AddMessage('\tWatershed: {0} \n\t***Not found in dictionary***'.format(nbr))
				missing.append(nbr)
				counter += 1

		# get total structure values and apply to attribute fields
		totDams = sum(damList)
		totBridges = sum(bridgeList)
		totCulverts = sum(culvertList)
		totStreams = sum(streamList)
		totStructures = totDams + totBridges + totCulverts 
		row5[1] = totDams
		row5[2] = totBridges
		row5[3] = totCulverts
		row5[4] = totStreams

		# if total structures is 0 set density to 0 and score to 100
		if totStructures == 0:
			row5[5] = 0
			row5[6] = 100
		# else if stream len within catchment is 0 set score to 100
		elif Catchments[row5[0]][4] == 0:
			row5[6] = 100
		# else if total streams is greater than 0 calculate score normally.
		elif totStreams > 0:
			
			# Method used to calculate density using a neighborhood stream length
			#totDensity = (totDams + totBridges + totCulverts)/totStreams
			
			# Method used to calculate density using the average stream length for catchments in the current major
			totDensity = (totDams + totBridges + totCulverts)/(sum(avgStream[row5[7]])/len(avgStream[row5[7]]))
			
			row5[5] = totDensity
			scr = (1 - (totDensity/threshold))*100
			if scr < 0:
				scr = 0
			row5[6] = scr
		cur5.updateRow(row5)
	del row5
del cur5

t5 = time.time()
arcpy.AddMessage('Fields calculated! - {1} missing upstream catchments\nScript completed in {0} sec'.format(round((t5-t1),2), counter))

