# -*- coding: utf-8 -*-
# Declaration of the output variables and related statistics. Possible options: mean, maximum, minimum, final, sum.
# The integration step, hour, day or year,  is specified at the end of the script  
# Alternatively, instead of declaring output variables and associated statistics as done below L7 -L37, a test file can be used with the instruction:
#from "filename" (ex: BRAY_varsToIntegrate) import varsToIntegrate

varsToIntegrate = '''
Last: mdl.locTime.Y
Last: mdl.locTime.DOY
Last: mdl.locTime.H
Sum:  mdl.climate.microclim.Rain
Mean: mdl.climate.microclim.u
Mean: mdl.climate.microclim.TaC
Mean: mdl.climate.microclim.d
Mean: mdl.climate.microclim.SWDir
Mean: mdl.climate.microclim.SWDif
Mean: mdl.climate.microclim.LWDw
Last: mdl.forest.treeStand.canopy.LAI
Last: mdl.forest.treeStand.canopy.WAI
Last: mdl.forest.underStorey.canopy.LAI
Last: mdl.forest.underStorey.canopy.WAI
Last: mdl.forest.treeStand.canopy.sunLayer.LAI
Last: mdl.forest.treeStand.canopy.shadeLayer.LAI
Min: mdl.forest.treeStand.canopy.WaterPotential
Min: mdl.forest.soil.waterCycle.RootLayerWaterPotential
Last: mdl.forest.soil.waterCycle.Stock_RootLayer
Last: mdl.forest.soil.waterCycle.w_A
Last: mdl.forest.soil.waterCycle.w_RootLayer
Mean: mdl.forest.LE
Mean: mdl.forest.Rnet
Mean: mdl.forest.H
Sum: mdl.forest.GPP
Sum: mdl.forest.NEE
Sum: mdl.forest.RAuto
Sum: mdl.forest.soil.carbonCycle.Rh
Sum: mdl.forest.treeStand.canopy.Assimilation
Sum: mdl.forest.treeStand.canopy.Respiration
Sum: mdl.forest.treeStand.canopy.Transpiration
Sum: mdl.forest.treeStand.canopy.Evaporation
Sum: mdl.forest.underStorey.canopy.ETR
Sum: mdl.forest.underStorey.canopy.Assimilation
Sum: mdl.forest.underStorey.canopy.Respiration
Sum: mdl.forest.underStorey.canopy.Transpiration
Sum: mdl.forest.underStorey.canopy.Evaporation
Sum: mdl.forest.soil.surface.ETR
Sum: mdl.forest.soil.surface.ETR_DrySurface
Sum: mdl.forest.soil.surface.ETR_WetSurface
Last: mdl.forest.treeStand.Age    
Last: mdl.forest.treeStand.density
Last: mdl.forest.treeStand.IStress   
Last: mdl.forest.treeStand.DBHmean 
Last: mdl.forest.treeStand.HEIGHTmean
Last: mdl.forest.treeStand.BasalArea
Last: mdl.forest.treeStand.PROD_VOL
Last: mdl.forest.treeStand.WDeadTrees
Last: mdl.forest.treeStand.LeafFall
Last: mdl.forest.treeStand.Wr
Last: mdl.forest.treeStand.WStem
Last: mdl.forest.treeStand.WBranch
Last: mdl.forest.treeStand.WFoliage
Last: mdl.forest.treeStand.WTapRoot
Last: mdl.forest.treeStand.WCoarseRoot
Last: mdl.forest.treeStand.WSmallRoot
Last: mdl.forest.treeStand.WFineRoot
Last: mdl.manager.harvest_WStem
Last: mdl.manager.harvest_WBranch
Last: mdl.forest.underStorey.foliage.W
Last: mdl.forest.underStorey.perennial.W
Last: mdl.forest.underStorey.roots.W
Last: mdl.forest.soil.carbonCycle.HUM
Last: mdl.forest.soil.carbonCycle.BIO
Last: mdl.forest.soil.carbonCycle.DPM
Last: mdl.forest.soil.carbonCycle.RPM
Last: mdl.forest.soil.waterCycle.SOC
'''

# =============================================================================
import csv
import math
from sys import path
import os,sys
basePath  = os.path.join(os.path.dirname(os.path.realpath(__file__)), "..")
sys.path.append(os.path.join(basePath, "goplus"))
sys.path.append(os.path.join(basePath, "goplus", "goModel"))
from goBases import *
from goModel.mdlModel import Model
from goModel.ManagerElements import mdlMngt_Operations
from goTools.VarsIntegrater import Integrater



# Set of management practices that were applied to the Soroe Site 1951-2007 ===
INTERVENTIONS = {
        1951:  ('THINNING', 1162, 0, True),
        1954:  ('THINNING', 1023, 0, True),
        1957:  ('THINNING', 906, 0, True),
        1960:  ('THINNING', 806, 0, True),
        1963:  ('THINNING', 723, 0, True),
        1966:  ('THINNING', 652, 0, True),
        1969:  ('THINNING', 589, 0, True),
        1973:  ('THINNING', 535, 0, True),
        1977:  ('THINNING', 489, 0, True),
        1981:  ('THINNING', 448, 0, True),
        1985:  ('THINNING', 412, 0, True),
        1989:  ('THINNING', 381, 0, True),
        1993:  ('THINNING', 353, 0, True),
        1997:  ('THINNING', 329, 1, True),
        2002:  ('THINNING', 307, 1.5, True),
        2007:  ('THINNING', 288, 1.0, True),
        }

class Soroe_Manager(mdlMngt_Operations.Manager):

    def update(self):
        
        #Management variables initialisation
        
        self.harvest_WStem      = 0.
        self.harvest_WBranch    = 0.
        self.harvest_WTapRoot   = 0.
        self.harvest_WFoliage   = 0.
        self.NbCutTrees         = 0.
        self.harvest_DBHmean    = 0.
        self.harvest_DBHsd      = 0.
        self.harvest_DBHquadratic = 0.
        self.harvest_HEIGHTmean = 0.
        self.harvest_HEIGHTsd   = 0.
        self.harvest_basalArea  = 0.
       
        del self.Cut_Trees [:]
        
        if self.locTime.isSimulBeginning:
            self.lastThinningYear   = self.locTime.Y - 10
            self.thinnings          = 0        
            self.seedingYear     = self.locTime.Y - self.forest.treeStand.Age - 5
            self.FirstThinning      = False
        
        # Specifications of the Plantation and thinnings operation
        for interventionYear, interventionParameters in INTERVENTIONS.items():
            if  self.locTime.isYearEnd and self.locTime.Y == interventionYear  : 
                
                if  interventionParameters[0] == 'THINNING' :
                    self.do_Density_Thinning(
                            ThinFactor=interventionParameters[2], 
                            densityObjective = interventionParameters[1], 
                            )
                    self.do_Logging(
                            harvestStem = interventionParameters[3], 
                            harvestBranchWood = False, 
                            harvestTapRoot = False, 
                            harvestStump=False,
                            harvestFoliage = False, 
                            )
                    self.lastThinningYear= self.locTime.Y
                self.forest.treeStand.pcs_SetSizes() # update sand characteristics after management operations


# Object Model ================================================================                
def model(
    startYear,      #initial year
    meteoFile,      #meteo file path 
    ):
    '''return an instance of the Model parameterized and initialized f.
    '''

   #instanciate the model, set a specific manager and define start year
    mdl= Model()
    mdl.manager = Soroe_Manager()
    mdl.locTime.Y_start = startYear
    mdl.climate.meteo_file_path = meteoFile
    mdl.climate.Scenario=0 
    
   # Set the site specific parameters from csv external file
    paraSiteFilePath =os.path.join(basePath, 'Parameters_files', 'Site', 'DK-Sor.csv')
    fileParaSite = open(paraSiteFilePath,'r')
    line=next(fileParaSite)
    for line in fileParaSite :
        L = line.split(',') 
        nam = 'mdl' + str(L[0]).lstrip(',').split(" ",1)[0].replace("'","").replace('"','')
        val = float(L[1])
        exec("%s = %s" %(nam,val))  
    fileParaSite.close()  
    
   # Set the species parameters from csv external file:  Fsylvatica 
    paraSpeFilePath =os.path.join(basePath, 'Parameters_files', 'Species', 'Fsylvatica.csv') 
    fileParaSpe = open(paraSpeFilePath,'r')
    line=next(fileParaSpe)
    for line in fileParaSpe :
        L = line.split(',') 
        nam = 'mdl' + str(L[0]).lstrip("'").split(',')[0].replace("'","").replace('"','')
        try :
            val = round(float(L[1]),6)
        except ValueError :
            val = str(L[1])
        exec("%s = %s" %(nam,val))
    fileParaSpe.close()

    yearLastIntervention = max([y for y in INTERVENTIONS.keys() if y < startYear])
    _initial_trees_Density = INTERVENTIONS[yearLastIntervention][1]
    _installation =mdl.forest.treeStand.pcs_TreeStandInstallation
    mdl.forest.treeStand.RotationYear = _installation.initialTreesAge
    _installation.initialTreesDimensionsFile =os.path.join(basePath, 'Parameters_files', 'Tree_stand', 'DK-Sor_dbh_1998.csv') 

    return mdl

def simulate(
    mdl,              
    endYear,          # last year simulated
    fileoutName,      #name of the output file 
    outFrequency,     
    log,              #boolean to indicate if simulation information is to be printed
    header= True, 
    fileOutAppend = False, 
    ):
    ''' simulation 
    '''
#Specify the integration
    integrater =Integrater(mdl, varsToIntegrate) 
#open the fileOut and write header
    with open(fileoutName, 'w') as fileOut:
        fileOut.write('%s\n' % integrater.varNames)
#short reference to locTime object to speed up conditionnal tests
        locTime = mdl.locTime     
#simulation loop
        while (locTime.Y is None) or (locTime.Y <endYear + 1):      
#update the model state
            mdl.update()
#made  the integrations of model variables and output the integrated values each day
            integrater.integrate() 
            if (True,  locTime.isDayEnd,  locTime.isYearEnd)[outFrequency]:
                fileOut.write('%s\n' % integrater.putStr())

#Display selected output values on a python console to monitor the simulation                
            if log and locTime.DOY == 195 and locTime.H == 23:
                print (str(locTime.Y),
                      'Age:',  str(mdl.forest.treeStand.Age), 
                      'nb: ',  str(mdl.forest.treeStand.treesCount),
                      'HEIGHT:',  str(mdl.forest.treeStand.HEIGHTmean), 
                      'DBH:', str(mdl.forest.treeStand.DBHmean),  
                      'LAI:', str(mdl.forest.treeStand.canopy.LAI), 
                      'IStress:', str(mdl.forest.treeStand.IStress), 
                      'LAI-T:', str(mdl.forest.treeStand.canopy.LAI), 
                      'Basal Area:', str(mdl.forest.treeStand.BasalArea),
                      'Thinnings', str(mdl.manager.thinnings)
                      )

if __name__ == '__main__':
    from time import  time

#instantiate the model 
    mdl = model( 
        startYear = 1998,
        meteoFile = os.path.join(basePath, 'Met_files', 'Met_DK-Sor_1998-2013.csv'),
        )
    endYear = 2012 #included
    fileoutName =os.path.join(basePath, 'Output_files', 'DK-Sor_1998-2013_dtest.csv')
        
    #Do simulation
    if endYear>1998:
        tstart =time()
        simulate(
            mdl             = mdl, 
            endYear         = endYear, 
            fileoutName     = fileoutName,
            outFrequency    = 1,         #0: hour, 1: day, 2: year
            log             = True, 
            header          = True, 
            fileOutAppend   = False, 
            )
        tend =time()
        print("\n Completed \n Output file is:", fileoutName, "\n simulate in %s mn." % str((tend-tstart)/60.))  