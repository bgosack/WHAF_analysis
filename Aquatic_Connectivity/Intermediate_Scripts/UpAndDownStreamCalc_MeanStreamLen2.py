# For each catchment polygon in feature class, identify cathcments that are
# up- and downstream.  


import arcpy
from arcpy import env
arcpy.env.overwriteOutput = True

workspace=r"D:\Users\tetagar\Workspace\WAT_Downscaling\UpDownExperiments.gdb" # arcpy.GetParameterAsText(0) # Workspace

polyFeature=r"D:\Users\tetagar\Workspace\WAT_Downscaling\Connectivity.gdb\AqConnectivityCatchment" #arcpy.GetParameterAsText(1) # Polygon feature catchemnts

 ## Check if fields exist (if True, field needs to be created)

field_MEAN_STR = "True"
field_STR_mSTR = "True"
field_SUM_STR = "True"
fieldList = arcpy.ListFields(polyFeature)

for f in fieldList:
    if f.name=="MEAN_STR":
        field_MEAN_STR = "False"
    if f.name=="STR_mSTR":
        field_STR_mSTR = "False"
    if f.name=="SUM_STR":
        field_SUM_STR = "False"

if field_MEAN_STR:
    arcpy.AddField_management(polyFeature, "MEAN_STR", "FLOAT")

if field_STR_mSTR:
    arcpy.AddField_management(polyFeature, "STR_mSTR", "FLOAT")

if field_SUM_STR:
    arcpy.AddField_management(polyFeature, "SUM_STR", "LONG")



                              
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


featureRow=[]
upCatchmentList=[]
downCatchmentList=[]
catchmentDict = {}
rows = arcpy.SearchCursor(polyFeature) 


for row in rows:
##    if row.CATCH_ID[:4]== "1503":  # =="1503000":; Catchment selection expression
        
    featureRow.append(row.CATCH_ID)
    catchment = row.getValue("CATCH_ID")
    catchmentUp = row.getValue("UPADJ_CAT")
    catchmentDown = row.getValue("DOWN_CAT")
    catchmentMajor = row.getValue("MAJOR")
    catchmentDict[catchment] = [catchmentUp,catchmentDown,catchmentMajor]
        
del row
del rows


 ## SELECT UPSTREAM, DOWNSTREAM OR BOTH
selection= "both" # "up" or "down" or "both" / arcpy.GetParameterAsText(2)



 ## BOUNDS SELECTION BY MAJOR WATERSHED OF CATCHMENT
bound=True # True or False / arcpy.GetParameterAsText(3) 


 ## DOWNSTREAM
if selection == "down": 
    for catchment in featureRow:
        watershed= catchmentDict.get(catchment)[2]
        downCatchmentList=[catchment]
        findDownstreamCatchments(catchment,catchmentDict,downCatchmentList)
       
        # Build a Query...
        theStr = ""
        i = 0
        for h in downCatchmentList:
            if i == 0:
                theStr = theStr + "'"+h+"'"
            else:
                theStr = theStr + " OR CATCH_ID = '"+h+"'"
            i+=1

        if bound:
            theQuery = '("CATCH_ID" = ' + theStr + ') AND "MAJOR" =' +str(watershed)
        else:
            theQuery = '"CATCH_ID" = ' + theStr

              
        outFC="D:/Users/tetagar/Workspace/WAT_Downscaling/DownscaleOutputExperiment/DownSTR_"+str(catchment)+".shp"

        arcpy.MakeFeatureLayer_management(polyFeature,"vWatershed",theQuery)

##        arcpy.CopyFeatures_management("vWatershed",outFC)



 ## UPSTREAM
elif selection == "up":
    for catchment in featureRow:
        watershed= catchmentDict.get(catchment)[2]
        upCatchmentList=[catchment]
        findUpstreamCatchments(catchment,catchmentDict,upCatchmentList)

               
        # Build a Query...
        theStr = ""
        i = 0
        for h in upCatchmentList:
            if i == 0:
                theStr = theStr + "'"+h+"'"
            else:
                theStr = theStr + " OR CATCH_ID = '"+h+"'"
            i+=1

        if bound:
            theQuery = '("CATCH_ID" = ' + theStr + ') AND "MAJOR" =' +str(watershed)
        else:
            theQuery = '"CATCH_ID" = ' + theStr
        
        outFC="D:/Users/tetagar/Workspace/WAT_Downscaling/DownscaleOutputExperiment/UpSTR_NotBound_"+str(catchment)+".shp"

        arcpy.MakeFeatureLayer_management(polyFeature,"vWatershed",theQuery)

        arcpy.CopyFeatures_management("vWatershed",outFC)

elif selection =="both":
    catchStrDict = {}
    for catchment in featureRow:
        print catchment
        watershed= catchmentDict.get(catchment)[2]
        UpCatchmentList=[catchment]
        findUpstreamCatchments(catchment,catchmentDict,UpCatchmentList)

        downCatchmentList=[catchment]
        findDownstreamCatchments(catchment,catchmentDict,downCatchmentList)

        upDownCatchmentList=downCatchmentList+UpCatchmentList

              
       
        # Build a Query...
        theStr = ""
        i = 0
        for h in upDownCatchmentList:
            if i == 0:
                theStr = theStr + "'"+h+"'"
            else:
                theStr = theStr + " OR CATCH_ID = '"+h+"'"
            i+=1

        if bound:
            theQuery = '("CATCH_ID" = ' + theStr + ') AND "MAJOR" =' +str(watershed)
        else:
            theQuery = '"CATCH_ID" = ' + theStr


        outFC="D:/Users/tetagar/Workspace/WAT_Downscaling/DownscaleOutputExperiment/UpDownSTR_"+str(catchment)+".shp"              

        arcpy.MakeFeatureLayer_management(polyFeature,"vWatershed",theQuery)


        # CALCULATE MEAN LENGTH OF STREAM
        CatchStrLen=[]
        
        records = arcpy.SearchCursor("vWatershed") 
        for record in records:
            
            streamLength = record.getValue("NewStreamLeng")
            CatchStrLen.append(streamLength)
            meanLen= sum(CatchStrLen)/len(CatchStrLen)
            catchStrDict[catchment] = [meanLen]
        del record
        del records
    print len(catchStrDict) 
        
    lines=arcpy.UpdateCursor(polyFeature)
    for line in lines:
##        if line.CATCH_ID[:4]== "1503": #Again same selection (can be removed)
        catch_id = line.getValue("CATCH_ID")
        meanLen=catchStrDict[catch_id][0]
        line.MEAN_STR = meanLen
##        line.STR_mSTR = line.SUM_STR/(meanLen/1609.34)
        lines.updateRow(line)
    del line
    del lines
        

        

else:
    print "It's either, up, down or both, in quotation marks!"

print "Done, Sir!"





    
    

