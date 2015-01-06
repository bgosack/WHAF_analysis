### Tool to select DNR catchments based on neighborhood to a subset of those catchments
### that ar eprovided as a separate feature class. Neighborhood rules:

### a.	The empty catchment is directly adjacent to one or more catchments that contain a point
### b.	The empty catchment is either upstream or downstream from the one(s) containing points.

### The empty catchments then receive an extrapolated value (for their IBI WHAF score), which is the mean
### of all catchments that comply with the neighborhood rules above. 


import arcpy
from arcpy import env

env.workspace = r"D:\Users\tetagar\Workspace\WAT_Downscaling\Biology\StreamSpecies.gdb"

selectingFC = arcpy.GetParameterAsText(0) # DNR CATCHMENTS that have a IBI points        #r"D:\Users\tetagar\Workspace\WAT_Downscaling\Biology\StreamSpecies.gdb\Catchments_withF_IBI" #
inFC = arcpy.GetParameterAsText(1) # DNR CATCHMENT LAYER that has also catchment WHAF score for IBI (only for those catchments that have an IBI point). Should also have field "WHAF_ExtScore"   r"D:\Users\tetagar\Workspace\WAT_Downscaling\Biology\StreamSpecies.gdb\Catchments_HUC_12_trial3"#
IBI_MeanFC = inFC # In initial iteration of script and for testing purposes this was different than inFC
fieldName =  arcpy.GetParameterAsText(2) #name of field that contains IBI values in catchments that contain IBI points #"WHAF_FishIBI" or "WHAF_Score"
ExtField = arcpy.GetParameterAsText(3)# "Ext"+ fieldName # field name for the extrapolated IBI value
Output = arcpy.GetParameterAsText(4)#"Output" 


# list catch_ID of features in selectingFC
selectionList = []
rows = arcpy.SearchCursor (selectingFC)
for row in rows:
    catch = row.CATCH_ID
    selectionList.append(catch)

del row
del rows

# For each catchment (of entire dataset), get a list of cathments upstream and its (one) downstream catchment. 
# get that list on a dictionary after catchment's CATCH_ID
# 'if' condition to do this only for catchments that do not contain an IBI point


longFUllNeighborList = [] #global list ALL catchments containing IBI points that are neighbors to empty catchments - not sure that's useful.
longEmptyNeighborList = [] # global list of catchments that will have IBI values extrapolated to them

IBI_Dict = {} # dictionary of catchments with IBI as key and the score as value
ExtrapolatedDict = {} #dictionary of empty catchments (catch ID) and their extrapolated value. 
catchments = arcpy.SearchCursor (inFC) 
cntr = 0


for catchment in catchments:

    if catchment.CATCH_ID in selectionList:
        IBIScore = catchment.getValue(fieldName)
        IBI_Dict [catchment.CATCH_ID] = [IBIScore]

del catchment
del catchments


catchments2 = arcpy.SearchCursor (inFC)
for catchment2 in catchments2:

    if catchment2.CATCH_ID not in selectionList: # excluding catchments that contain an IBI point
        longEmptyNeighborList.append(catchment2.CATCH_ID)

        NeighborChmentList = catchment2.UPADJ_CAT.split()
        downCatch = catchment2.DOWN_CAT
        NeighborChmentList.append(downCatch)# NeighborChmentList now has all directly adjecent catchmetns for the catchment that are upstream or downstream from it
                
        IBI_neighborList = [] # a list of those adjecent neighbors that contain an IBI value
        for neighbor in NeighborChmentList:
            if neighbor in selectionList: #i.e. if neigbor contains an IBI point
                IBI_neighborList.append(neighbor) # local list of neighbor catchments that contain an IBI point
                longFUllNeighborList.append(neighbor) # global list ALL catchments containing IBI points that are neighbors to empty catchments - not sure that's useful. 
                
        #get extrapolated value from mean value of neighbors: 
        IBI_neighborValues = []
        for neighbr in IBI_neighborList:
            if neighbr in IBI_Dict:
                score=IBI_Dict[neighbr][0]                
                IBI_neighborValues.append(score)
            else:
                arcpy.AddWarning("We have a problem with "+ catchment2.CATCH_ID)

        if len(IBI_neighborValues)>0:
            ExtrapolatedIBI = sum(IBI_neighborValues)/len(IBI_neighborValues)
            ExtrapolatedDict[catchment2.CATCH_ID] = [ExtrapolatedIBI]
            cntr = cntr+1
print ExtrapolatedDict, len(ExtrapolatedDict)

print cntr


del catchment2
del catchments2

rows = arcpy.UpdateCursor (IBI_MeanFC)
for row in rows:
    rowID = row.CATCH_ID
    if rowID in ExtrapolatedDict:
        score = ExtrapolatedDict[rowID][0] 
        row.setValue (ExtField,score) 
        rows.updateRow(row)
        



del row
del rows

arcpy.CopyFeatures_management(IBI_MeanFC, Output)

ScoreName = fieldName+"SCORE"

# Put together WHAF IBI values for catchments containing IBI point(s) and for ones that have extrapolated values in a single field
arcpy.AddField_management(Output, ScoreName, "LONG")


rows = arcpy.UpdateCursor (Output)
for row in rows:
    if row.getValue(fieldName)> -1:
        score = row.getValue(fieldName)
    elif row.getValue(ExtField) > -1:
        score = row.getValue(ExtField)
    else:
        score = None 

    row.setValue(ScoreName, score)
    rows.updateRow(row)
        



del row
del rows

