"""
Class with all userinput for running eodie as command line tool

authors: Samantha Wittke, Juuso Varho, Petteri Lehti

"""

import argparse
import os
from datetime import datetime 
import glob
import re
import yaml

class UserInput(object):
    """ Userinput object for EODIE
    Attributes
    -----------
    see help text for description of each attribute
    """

    def __init__(self):
        self.get_userinput()


    def get_userinput(self):
        """ gets all userinput from commandline call to run the tool and stores them as userinput attributes """

        parser = argparse.ArgumentParser()
        parser.add_argument('--platform', dest='platform',help='which platform does the data come from? options: s2, tif, ls8', choices=['s2', 'tif', 'ls8'], required=True)
        inputrastergroupparser = parser.add_mutually_exclusive_group(required=True)
        inputrastergroupparser.add_argument('--rasterdir', dest='rasterdir', help='directory where data is stored')
        inputrastergroupparser.add_argument('--rasterfile', dest='rasterfile', help='one file')

        parser.add_argument('--vector', dest='vectorbase', help='name of the vectorfile with polygons (without extension)', required=True)
        parser.add_argument('--out', dest='outpath', default='./results', help='directory where results shall be saved')
        parser.add_argument('--id', dest='idname', help='name of ID field in vectorfile', required=True)

        parser.add_argument('--input_type', dest='input_type', default='.shp', help='determine the input file type, supported formats: .shp (default), .gpkg, .geojson, .csv, .fgb')
        parser.add_argument('--gpkg_layer', dest='gpkg_layer', default=None, help="determine the layer in geopackage to be used")
        parser.add_argument('--epsg_for_csv', dest='epsg_for_csv', default=None, help='determine the EPSG code if vector input is .csv')

        parser.add_argument('--statistics', dest='statistics',default=['count'],help='statistics to be extracted', nargs='*')
        parser.add_argument('--index', dest='indexlist', help=' give names of indices to be processed', nargs='*')
        parser.add_argument('--start', dest='startdate',default = '20160101', help='give startdate of timerange of interest')
        parser.add_argument('--end', dest='enddate',default= datetime.now().strftime("%Y%m%d") ,help='give enddate of timerange of interest')
        parser.add_argument('--keep_splitted', dest='keep_splitted', action='store_true', help='flag to indicate that newly created splitted vectordata files should be stored')
        
        parser.add_argument('--test', dest='test', action='store_true', help='only needed for automatic testing')
        parser.add_argument('--exclude_border', dest='exclude_border', action='store_true',help='if this flag is set border pixels are excluded from calculations')
        parser.add_argument('--external_cloudmask', dest= 'extmask', default = None, help= ' location and name of external cloudmask (without tile and date and extension) if available')
        parser.add_argument('--exclude_splitbytile', dest='exclude_splitbytile', action='store_true',help='if this flag is set, it is assumed that splitbytile has been run manually beforehand')
        parser.add_argument('--verbose', '-v',dest='verbose', action='store_true',help=' logging in logfile and prints in terminal')

        parser.add_argument('--geotiff_out', dest='geotiff_out', action='store_true', help='flag to indicate that geotiffs shall be extracted')
        parser.add_argument('--statistics_out', dest='statistics_out',action='store_true',help='flag to indicate that statistics shall be calculated')
        parser.add_argument('--array_out', dest= 'array_out', action='store_true', help='flag to indicate that arrays shall be extracted')

        args = parser.parse_args()

        self.platform = args.platform
        configfile = '../config_'+ self.platform + '.yml'

        #loading config files and merging into one dict
        with open(configfile, "r") as ymlfile:
            platform_cfg = yaml.safe_load(ymlfile)

        with open('../user_config.yml', "r") as ymlfile:
            user_cfg = yaml.safe_load(ymlfile)

        #starting python 3.9: platform_cfg | user_cfg also works
        self.config = {**platform_cfg, **user_cfg}

        self.rasterdir = args.rasterdir
        self.rasterfile = args.rasterfile
        if args.rasterfile is not None:
            self.input = [args.rasterfile]
        else:
            #self.input = glob.glob(os.path.join(args.rasterdir,self.config['productnameidentifier']))
            # this searches for exact right files fitting a given pattern
            self.input = [os.path.join(self.rasterdir, file) for file in os.listdir(self.rasterdir) if re.search(self.config['filepattern'], file)]
        
        self.input_type = args.input_type
        self.epsg_for_csv = args.epsg_for_csv
        self.gpkg_layer = args.gpkg_layer
        # remove extension if given by mistake (assumption, . is only used to separate filename from extension)
        if '.' in args.vectorbase:
            self.vectorbase = os.path.splitext(args.vectorbase)[0]
        else:
            self.vectorbase = args.vectorbase
        self.outpath = args.outpath
        self.idname = args.idname

        self.statistics_out = args.statistics_out
        
        self.array_out = args.array_out
        self.indexlist = args.indexlist
        # Add count to statistics in case it's missing
        if not 'count' in args.statistics:
            self.statistics= ['count'] + args.statistics
        else:
            self.statistics = args.statistics
        self.startdate = args.startdate
        self.enddate = args.enddate
        self.keep_splitted = args.keep_splitted

        self.geotiff_out = args.geotiff_out
        self.test = args.test
        self.exclude_border = args.exclude_border
        self.extmask = args.extmask
        self.exclude_splitbytile = args.exclude_splitbytile
        if self.platform == 'tif':
            self.exclude_splitbytile = True
        self.verbose = args.verbose

        # Determine output formats
        self.format =  []
        if self.statistics_out:
            self.format.append('statistics')
        if self.geotiff_out:
            self.format.append('geotiff')
        if self.array_out:
            self.format.append('array')       

        # If no output formats are specified, only output statistics
        if len(self.format) == 0:
            self.format.append('statistics')



        
