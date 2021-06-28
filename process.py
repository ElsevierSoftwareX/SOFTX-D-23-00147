import glob
import argparse
import re
import sys
import os
sys.path.append("./objects")
from extractor import Extractor
from cloudobject import CloudObject
from indexobject import IndexObject
from geometry import Geometry
from pathfinder import Pathfinder
from raster_validator import RasterValidator
from writer import WriterObject
from userinput import UserInput
import logging
from datetime import datetime 
import yaml

#loading config file
with open("config.yml", "r") as ymlfile:
    cfg = yaml.safe_load(ymlfile)

userinput = UserInput()

#create results dir 
if not os.path.exists('./results'):
    os.mkdir('./results')

#setup logging 
logging.basicConfig(filename=os.path.join(userinput.outpath, datetime.now().strftime("%Y%m%d-%H%M%S") + '.log'), level=logging.INFO)

for path in glob.glob(os.path.join(userinput.mydir,'*.SAFE')):

    pathfinderobject = Pathfinder(path)
    
    logging.info('Imagepath is {}'.format(pathfinderobject.imgpath))
    logging.info('Tile is {}'.format(pathfinderobject.tile))
    logging.info('Date is {}'.format(pathfinderobject.date))
    

    if int(pathfinderobject.date) <= int(userinput.enddate) and int(pathfinderobject.date) >= int(userinput.startdate):
    
        cloudobject = CloudObject(pathfinderobject.imgpath)
        cloudmask = cloudobject.create_cloudmask()
        logging.info('Shape of cloudmask is {}'.format(cloudmask.shape))
        indexobject = IndexObject(pathfinderobject.imgpath,cfg['resolution'])
        geoobject = Geometry(userinput.shpbase + '_' + pathfinderobject.tile +'.shp')
        geoobject.reproject_to_epsg(indexobject.epsg)
        shapefile = geoobject.geometries

        maxcloudcover = cfg['maxcloudcover']
        rastervalidatorobject = RasterValidator(path, maxcloudcover, geoobject)
        logging.info('Cloudcover below {}: {}'.format(maxcloudcover, rastervalidatorobject.cloudcovered))
        logging.info('Data withing area of interest: {}'.format(rastervalidatorobject.datacovered))
        
        if rastervalidatorobject.cloudcovered and rastervalidatorobject.datacovered:

            for index in userinput.indexlist:
                # check if bands are re
                if index in indexobject.supportedindices:
                    array = indexobject.calculate_index(index)
                elif re.match('B[0-1]\d', index) or index == 'B8A':
                    array = indexobject.get_band(index)
                else:
                    logging.warning('Chosen index {} not available, continuing with next index.'.format(index))
                    
                affine = indexobject.affine

                if int(userinput.stat) == 1: 
                    logging.info('Statistics: {}'.format(pathfinderobject.tile))
                    extractorobject = Extractor(cloudmask, array, shapefile, userinput.idname,affine, userinput.statistics)
                    extractedarray = extractorobject.extract_arrays_stat()
                    writerobject = WriterObject(userinput.outpath, pathfinderobject.date, pathfinderobject.tile, extractedarray, index, userinput.statistics)
                    extractorobject.extract_arrays_stat()
                    writerobject.write_csv()
                    

                elif int(userinput.stat) == 0:
                    
                    extractorobject = Extractor(cloudmask, array, shapefile, userinput.idname,affine,['count'])
                    extractedarray = extractorobject.extract_arrays()
                    writerobject = WriterObject(userinput.outpath, pathfinderobject.date, pathfinderobject.tile, extractedarray, index, ['array'])
                    extractorobject.extract_arrays()
                    writerobject.write_pickle_arr()
            
        else:
            logging.warning('Cloudcovered or no data in Area of interest!')
            
