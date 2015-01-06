#-------------------------------------------------------------------------------
# Name:        createAquaConnStreamsData.py
# Purpose:     This script runs through the data preprocessing steps developed
#              by Z.Tagar for the aquatic connectivity index analysis model. The
#              steps involve extracting a subset of stream types, clipping 
#              lake connectors by public waters, then merging those datasets 
#              back together. 
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
inStreams = r'E:\GIS_Data\Hydrology\Hydrology.gdb\dnr_rivers_and_streams'
inLakes = r'E:\GIS_Data\Hydrology\Hydrology.gdb\public_waters_basin_delineations'

outStreams = r'D:\Users\begosack\Documents\WHAF\Index_Development\Connectivity\Aquatic_Connectivity\Data\Inputs.gdb\preppedStreams'

# extract all features that match stream type 20, 40, 60 or 62
arcpy.AddMessage('Prepping streams...')
arcpy.AddMessage('\tCreating layer query...')
perenQuery = '"STRM_TYPE" in (20, 40, 60, 62)'
arcpy.MakeFeatureLayer_management(inStreams, 'in_memory\perenStreams', perenQuery)

# erase features that intersect public waters
arcpy.AddMessage('\tErasing lakes from streams...')
arcpy.Erase_analysis('in_memory\perenStreams', inLakes, outStreams)
t2 = time.time()
arcpy.AddMessage('\tDone prepping streams! - {0} sec'.format(round((t2-t1), 2)))