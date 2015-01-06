#-------------------------------------------------------------------------------
# Name:        upscaleAquaticConnectivity.py
# Purpose:     This script uses the catchment scale scores for aquatic connectivity
#              to calculate an upscaled score for the major watershed scale. 
#
# Author:      begosack
#
# Created:     12/29/2014
# Copyright:   (c) begosack 2014
# Licence:     <your licence>
#-------------------------------------------------------------------------------

import arcpy, time

t1 = time.time()

arcpy.env.overwriteOuput = True

# get input parameters: inCatch = Catchments with index values calculated, inMajor = major watersheds that will be copied to create an output, 
inCatch = r'D:\Users\begosack\Documents\WHAF\Index_Development\Connectivity\Aquatic_Connectivity\Data\Inputs.gdb\WHAF_DNR_Catchments_Current_UTM'
inField_AC = 'C_I_AC'
#inClipCatch = r'D:\Users\begosack\Documents\GIS_Data\WHAF_Inputs.gdb\DNR_Level_08_Catchments_MN_Clip_WatArea'
inMajor = r'D:\Users\begosack\Documents\GIS_Data\WHAF_Inputs.gdb\DNR_Level_04_Majors' 
outDir = r'D:\Users\begosack\Documents\WHAF\Index_Development\Connectivity\Aquatic_Connectivity\Data\Outputs.gdb'

print "\nCreating output file..."
outFile = outDir + r'\Major_AquaConn'
arcpy.CopyFeatures_management(inMajor, outFile)
arcpy.AddField_management(outFile, "C_I_AC", "SHORT")
arcpy.AddField_management(outFile, "compare_area", "DOUBLE")
print "Created!"

# clip input catchments to the major polygon boundaries
tempCatch = r'in_memory\tempCatch'
arcpy.Clip_analysis(inCatch, inMajor, tempCatch)

# write attributes into a dictionary
t2 = time.time()
print 'Creating Dictionary...'
majorDict = {}
with arcpy.da.SearchCursor(tempCatch, ['CATCH_ID', inField_AC, 'MAJOR', 'SHAPE@AREA']) as cur:
	for row in cur:
		# if the major ID for the given row in inCatch is already in the Dictionary append the dictionary list objects with the score*area product (for an area weighted average) value and the area value
		if row[2] in majorDict and row[1] >= 0:
			majorDict[row[2]][0].append((row[1]*row[3]))
			majorDict[row[2]][1].append(row[3])
		# if major not yet in dictionary, create a new entry with the area*score product and area in a list of lists
		else:
			majorDict[row[2]] = [[(row[1]*row[3])], [row[3]]]
			print '\tCreating new dicitionary row for major - {0}'.format(row[2])

del cur
t3 = time.time()
print 'Dictionary created in {0} sec'.format(round((t3-t2), 2))


# use an update cursor to write values to the output feature class
with arcpy.da.UpdateCursor(outFile, ['major', 'C_I_AC', 'compare_area', 'SHAPE@AREA']) as cur1:
	for row1 in cur1:
		avg = (float(sum(majorDict[row1[0]][0]))/float(sum(majorDict[row1[0]][1])))
		comp = sum(majorDict[row1[0]][1])/row1[3]
		avg1 = round(avg,0)
		#scr = ((avg1 - 57)*100)/(100-57)
		row1[1] = avg1
		row1[0] = comp
		cur1.updateRow(row1)
	del row1
del cur1

arcpy.Delete_management(tempCatch)

t4 = time.time()
print 'Done! - Script completed in {0} sec'.format(round(t4-t1, 2))



# print '\nAppending dictionary...'
# with arcpy.da.SearchCursor(inClipCatch, ['CATCH_ID', 'Shape_Area']) as cur1:
# 	for row1 in cur1:
# 		if catchDict[row1[0]]:
# 			catchDict[row1[0]].append(row1[1])
# 		else:
# 			print 'no row exists for {0}'.format(row[0])
# del cur1
# t4 = time.time()
# print "Dictionary appended in {0} sec".format(round((t4-t3), 2))
# print catchDict

# print '\nCalculating and populating upscled scores...'
# counter = 0 
# with arcpy.da.UpdateCursor(outFile, ['MAJOR', "W_I_PS", 'compare_area', 'Shape_Area']) as cur2:
# 	for row in cur2:
# 		area = []
# 		score = []

# 		for val in catchDict:
# 			if catchDict[val][1] == row[0] and len(catchDict[val])> 2:

# 				catch_area = catchDict[val][2]
# 				catch_val = catchDict[val][0]
# 				catch_product = catch_area * catch_val
				
# 				area.append(catch_area)
# 				score.append(catch_product)

# 			else: 
# 				pass
# 		if len(score)>0:
# 			compare_area = row[3]/sum(area)
# 			out_score = sum(score)/sum(area)

# 			row[1] = out_score
# 			row[2] = compare_area
# 			cur2.updateRow(row)
# 		else:
# 			pass
# 		print counter 
# 		counter += 1
# del cur2
# t5 = time.time()

# print "Script completed in {0} sec".format(round((t5-t1), 2))