# Licensed under a 3-clause BSD style license - see LICENSE.rst

"""This class supports communication with DS9 through the XPA """

from __future__ import print_function, division, absolute_import

import os
import shutil
import time
import weakref
import numpy as np
from subprocess import Popen
import time
import warnings
import logging
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from tempfile import mkdtemp

import photutils

import imexam.xpa_wrap as xpa
from imexam.xpa import XpaException

from . import  util
from  .math_helper import gaussian

try:
    import astropy
except ImportError:
    has_astropy = False
else:
    has_astropy = True

if has_astropy:
    from astropy.io import fits as pyfits
else:
    import pyfits

class UnsupportedDatatypeException(Exception):
    pass

class UnsupportedImageShapeException(Exception):
    pass

__all__=['ds9']    

#make a new obect for every window you want to create
class ds9(object):
    """ A class which controls all interactions between the user and the ds9 window
    
        The ds9() contructor takes a ds9 target as its main argument. If none is given,
        then a new window will be opened. 

        DS9's xpa access points are documented in the reference manual, but the can also
        be returned to the user with a call to xpaset.

        http://hea-www.harvard.edu/saord/ds9/ref/xpa.html


        Parameters
        ----------
        target: string, optional
             the ds9 target name or id (default is to start a new instance)
        
        path : string, optional
            path of the ds9
        
        wait_time : float, optional
            waiting time before error is raised
        
        quit_ds9_on_del : boolean, optional
            If True, try to quit ds9 when this instance is deleted.
            
            
        Attributes
        ----------

        wait_time: float
             The waiting time before error is raised

        path: string
            The path to the DS9 executable
            
        _xpa_name: string
            The value in XPA_METHOD, the name of the DS9 window
            
        _quit_ds9_on_del: boolean
             Determine whether to quit ds9 when object goes out of scope.

        _ds9_unix_name: string
            The full path filename to the unix socket, only if unix sockets are being used with local
            
        _need_to_purge: boolean
             whether there are unix socket directories which need to be purged when the object goes out of scope
             
        _tmpd_name: string
            The full path name to the unix socket file on the local system
            
        _filename: string
            The name of the image that's currently loaded into DS9
            
        _ext: int
            Extension of the current image that is loaded. If one extension of an MEF file is loaded this will be 1
            regarless of the extension that was specified (because DS9 and the XPA now see it as a single image and header)
            
        _extname: string
            If available, the EXTNAME of the MEF extension that is loaded, taken from the current data header
            
        _extver: int
            If available, the EXTVER of the MEF extension that is loaded, taken from the current data header       
       
        _ds9_process: pointer
            Points to the ds9 process id on the system, returned by Popen
             
    """
    
    # _ImgCode : copied from pyfits, used for displaying arrays straight to DS9
    _ImgCode = {'float32': -32,
                'float64': -64,
                'int16': 16,
                'int32': 32,
                'int64': 64,
                'uint8': 8}

    _tmp_dir_list = ""
    _process_list = list()
    
    
    def __init__(self,target=None, path=None, wait_time=5, quit_ds9_on_del=True):
        """
        
        I think this is a quirk in the XPA communication. The xpans, and XPA prefer to have all connections
        be of the same type. DS9 defaults to creating an INET connection. In some cases, if no IP address can be
        found for the computer, the startup can hang. In these cases, a local connection is preferred, which 
        uses a unix filename for the socket.
        
        The problem arises that if the user already has DS9 windows running, that were started by default,
        imexam can run into communication problems with local sockets,and I can't register them with the xpa
        nameserver. So I'm defaulting it to start an INET socket when no target it provided. The user can 
        override this if they set XPA_METHOD to local  in their environment
        
        You should not have DS9 windows which use both socket types running at the same time
        
        """
        self._quit_ds9_on_del = quit_ds9_on_del  # determine whether to quit ds9 also when object deleted.
        self.wait_time=wait_time
        self._need_to_purge=False
        self._tmpd_name=None
        self._filename="" #no image loaded yet, use this for faster data access
        self._ext=1 #extension of the loaded image
        self._extname=""
        self._extver=None
        self._xpa_method="inet"
        self._xpa_name=""
        
        openNew=False
        if not target:
            openNew=True
            
        if path is None:
            self.path = util.find_ds9()
        else:
            self.path = path
        
        if openNew:            
            #Check to see if the user has chosen a preference first
            if 'XPA_METHOD' in os.environ.keys():
                self._xpa_method = os.environ['XPA_METHOD']
               
            if 'inet' in self._xpa_method:
                self._xpa_name  = self.run_inet_ds9()

            elif 'local' in self._xpa_method:
                print("starting unixonly local")
                self._xpa_name, self._ds9_unix_name = self._run_unixonly_ds9()
        else:
            #just register with the target the user provided
            self._xpa_name = target 
            self._ds9_process=None
        
        self.xpa = xpa.XPA(self._xpa_name) #xpa_name sets the template for the get and set commands
        self._set_filename()
        self._define_cmaps() #dictionary of color maps 
                

    def __str__(self):
        pass

    def __del__(self):
        if self._quit_ds9_on_del:
            if 'local' in self._xpa_method:
                self._purge_local()
            else:
                self._stop_process()

    def _set_filename(self):
        """set the name and extension information for the data displayed in the current frame 
        
        
        the absolute path reference is stored to make XPA happy in all cases, wherever the user
        started the DS9 session
        """
        
        load_header=False
        #see if any file is currently loaded into ds9
        try:
            self._filename=str(self.get('file').strip().split('[')[0])
            if len(self._filename) > 1:
                load_header=True
                self._filename=os.path.abspath(self._filename)
            else: 
                self._filename=""
                print("No file loaded")
            
        except XpaException:
            self._extver=None
            self._filename=""
            self._extname=""
        
        
        if load_header:    
            #set the extension from the header information
            header=self.get('fits header')
            header_cards=pyfits.Header.fromstring(header,sep='\n')

            try:
                self._extver=int(header_cards['EXTVER'])
                self._extname=str(header_cards['EXTNAME'])
            except KeyError:
                self._extver=None
                self._extname=""
            
        #if you load a single extension from an MEF into DS9, XPA references the extension as 1 afterwards for access points
        #you need to look in the header of the displayed image to find out what the actual extension that is loaded is
        self._ext=1

    def get_filename(self):
        """return the filename currently on display"""
        if not self._filename:
            print("No file loaded")
        return self._filename
        

    @classmethod
    def _purge_tmp_dirs(cls):
        """Delete temporary directories made for the unix socket
        
        When used with ipython (pylab mode), it seems that the objects
        are not properly deleted, i.e., temporary directories are not
        deleted. This is a work around for that.
        """
 
        if cls._tmp_dir_list :
            shutil.rmtree(cls._tmp_dir_list)
                
    @classmethod
    def _stop_running_process(cls):
        """stop self generated DS9 windows when user quits python window"""
        while cls._process_list:
            process=cls._process_list.pop()
            if process.poll() is None: 
                process.terminate()
                    
                    
                
    def _stop_process(self):
        """stop the ds9 window process nicely, only if this package started it"""
        
        try:
            if self._ds9_process:
                if self._ds9_process.poll() is None: #none means not yet terminated
                    self.set("exit")
                    self._process_list.remove(self._ds9_process) 

        except XpaException as e:
            print("Exception: {0}".format(e))


    def _purge_local(self):
        """remove temporary directories from the unix socket"""
        
        if not self._need_to_purge:
            return
            
        if not self._quit_ds9_on_del:
            warnings.warn("You need to manually delete tmp. dir ({0:s})".format(self._tmpd_name))
            return
            
        self._stop_process()
        #add a wait for the process to terminate before trying to delete the tree
        time.sleep(0.5)     
            
        try:
            shutil.rmtree(self._tmpd_name)
        except OSError:
            warnings.warn("Warning : couldn't delete the temporary directory ({0:s})".format(self._tmpd_name,))
    
        self._need_to_purge=False

    def close(self):
        """ close the window and end connection"""
        #make sure we clean up the object and quit_ds9ocal files
        if 'local' in self._xpa_method:
            self._purge_local()        
        else:
            self._stop_process()

    def run_inet_ds9(self):
        """start a new ds9 window with an inet connection
        
        
        We'll give it a unique name so we can identify it later
        """
        
        env = os.environ
        xpaname= str(time.time()) #that should be unique enough, something better? 
        try:
            p = Popen([self.path,
                       "-xpa", "inet",
                       "-title",xpaname],
                      shell=False, env=env)
            self._ds9_process = p
            self._process_list.append(p)
            self._need_to_purge=False
            return xpaname

        except Exception as e: #refine error class
            warnings.warn("Opening  ds9 failed")
            print("Exception: {0}".format(e))
            from signal import SIGTERM
            os.kill(p.pid, SIGTERM)
            raise Exception               
                
        
        
    def _run_unixonly_ds9(self):
        """ start new ds9 window and connect to object using a unix socket
        
        When the xpa method in libxpa parses given template as an unix socket, it checks if the template string starts with tmpdir (from env["XPA_TMPDIR"] 
        or default to "/tmp/.xpa"). This makes having multiple instances of ds9 a bit difficult, but if you give it unique names or use the inet address
        you should be fine

        For unix only, we run ds9 with XPA_TMPDIR set to temporary directory whose prefix start with "/tmp/xpa" 
        (eg, "/tmp/xpa_sf23f"), them set os.environ["XPA_TMPDIR"] (which affect xpa set and/or get command from python) to "/tmp/xpa".
        
        
        when xpaname is parsed for local, the prefix should match the XPA_TMPDIR Hence, we create temporary dir under that directory.

        The env variable "XPA_TMPDIR" is set to correct value when ds9 is run, and also xpa command is called (ie, python process).
        """
        env = os.environ
        wait_time=self.wait_time
        
        self._tmpd_name = mkdtemp(prefix="xpa_"+env.get("USER",""),
                                  dir="/tmp")

        env["XPA_TMPDIR"] = self._tmpd_name #this is the first directory the servers looks for on the path

        iraf_unix = "%s/.IMT" % self._tmpd_name
        title= str(time.time()) #that should be unique enough, something better? 
        try:
            #unix only flag disables the fifos and inet connections
            p = Popen([self.path,
                       "-xpa", "local",
                       "-unix_only","-title",title,
                       "-unix",  "%s" % iraf_unix],
                      shell=False, env=env)

            # wait until ds9 starts and the .IMT socket exists
            while wait_time > 0:
                file_list = os.listdir(self._tmpd_name)
                if ".IMT" in file_list:
                    break
                time.sleep(0.5)
                wait_time -= 0.5
                
            if wait_time==0:
                from signal import SIGTERM
                os.kill(p.pid, SIGTERM)
                raise OSError("Connection timeout with the ds9. Try to increase the *wait_time* parameter (current value is  %d s)" % (self.wait_time,))
            
        except Exception as e:
            warnings.warn("running  ds9 failed")
            print("Exception: {0}".format(e))
            shutil.rmtree(self._tmpd_name)
            raise Exception

        else:
            self._tmp_dir_list=self._tmpd_name
            self._ds9_process = p

        #this might be sketchy
        try:
            file_list.remove(".IMT") #should be in the directory, if not 
        except:
            warnings.warn("IMT not found in tmp, using first thing in list")
            
        xpaname = os.path.join(self._tmpd_name, file_list[0])

        env["XPA_TMPDIR"] = "/tmp/xpa"
        self._need_to_purge=True
        self._xpa_method=xpaname
        return xpaname, iraf_unix



    def set_iraf_display(self):
        """ Set the environemnt variable IMTDEV to the socket address of the current imexam.ds9 instance. 
        
        For example, your pyraf commands will use this ds9 for display.
        TODO: Not sure this is needed
        """
        os.environ["IMTDEV"] = "unix:%s" % (self._ds9_unix_name)


    def _check_ds9_process(self):
        """check to see if the ds9 process is stil running"""
        if self._ds9_process:
            ret = self._ds9_process.poll()
            if ret is not None:
                raise RuntimeError("The ds9 process is externally killed.")
                self._purge_local()


    def set(self, param, buf=None):
        """XPA set method to ds9 instance


        set(param, buf=None)
        param : parameter string (eg. "fits" "regions")
        buf : aux data string (sometime string needed to be ended with CR)
        """
        self._check_ds9_process()
        self.xpa.set(param, buf)


    def get(self, param):
        """XPA get method to ds9 instance


        get(param)
        param : parameter string (eg. "fits" "regions")
        returns received string
        """
        self._check_ds9_process()
        return self.xpa.get(param)


    def readcursor(self):
        """returns image coordinate postion and key pressed, 
        
        
           XPA returns strings of the form u'a  257.5 239 \n' 
        """
        try:       
            xpa_string = self.get("imexam any coordinate image")
        except XpaException as e:
            print("Xpa exception: {0}".format(str(e)))
            raise KeyError
        k, x, y = xpa_string.split()

        return float(x), float(y), str(k)


    def alignwcs(self,on=True):
        """align wcs?"""
        self.set("align %s"%(str(on)))
        
    def blink(self,blink=True,interval=None):
        """Blink frames
        
        
        blink_syntax=
            Syntax: 
            blink 
            [true|false]
            [interval <value>]
 
        """
        cstring="blink "
        if blink:
            cstring += "yes "
        else:
            cstring += "no "
            if interval:
                cstring+=(" %d")%(interval)
        
        self.set(cstring)

    def clear_contour(self):
        """clear contours from the screen"""
        self.set("contour clear")


    def _define_cmaps(self):
        """
        These are some options for the class which are used in other methods """

        self._cmap_syntax="""
        Syntax: 
        cmap [<colormap>]
            [file]
            [load <filename>] 
            [save <filename>] 
            [invert true|false] 
            [value <constrast> <bias>] 
            [tag [load|save] <filename>]
            [tag delete]
            [match]
            [lock [true|false]]
            [open|close]

         Example: 
            >obj.cmap(map="Heat") 
            >obj.cmap(invert=True) 
         """
        
        self._cmap_colors=["heat","grey","cool","aips0","a","b","bb","he","i8"] #is there a list I can pull from ds9?
           

    def cmap(self,color=None,load=None,invert=None,lock=None):
        """ Set the color map table to something else, in a defined list of options  """
            
        if color:
            color=color.lower()
            if color in self._cmap_colors:
                cstring="cmap %s"%(color)
                self.set(cstring)
            else:
                print("Unrecognized color map, choose one of these:")
                print(self._cmap_colors)
                
        if invert:
            cstring=('cmap invert %s')%(invert)        
            self.set(cstring)
            
        if lock:
            cstring=('cmap lock %s')%(lock)
            self.set(cstring)
         
         
        if load:
            cstring=('cmap load %s')%(load) #where load is the filename
            self.set(cstring)


    def colorbar(self,on=True):
        """turn the colorbar on the bottom of the window on and off"""
        self.set("colorbar %s".format(str(on)))
        
    def contour(self,on=True,construct=True):
        """show contours on the window
        
            construct will open the contour dialog box with more options
        """
        self.set("contour {0:s}".format(str(on)))
        if construct:
            self.set("contour levels")
    
        
    def contour_load(self,filename):
        """load a contour file into the window"""
        if filename:
            self.set("contour loadlevels {0:s}".format(str(filename)))
        else:
            warnings.warn("No filename provided for contours")
       
    def crosshair(self,x=None,y=None,coordsys="physical",skyframe="wcs",skyformat="fk5",match=False,lock=False):
        """Control the current position of the crosshair in the current frame, crosshair mode is turned on"""
        if x and y:
            if "wcs" in skyframe:
                format=skyformat
            else:
                format=""
            self.window.set("crosshair {0:s} {1:s} {2:s} {3:s}".format(str(x),str(y),str(coordsys),format))
        if match:
            self.window.set("crosshair match wcs")
        if lock:
            self.window.set("crosshair lock wcs")
           
    def cursor(self,x=None,y=None):
        """move the cursor in the current frame to the specified image pixel, it will also move selected regions"""
        if x and y:
            self.set("cursor {0:s} {1:s}".format(str(x),str(y)))   
        else:
            warnings.warn("You need to supply both an x and y location for the cursor")
         
    def disp_header(self,ext=None):
        """Display the header of the current image to a DS9 window"""
        cstring="header "
        if not ext:
            ext=self._ext
        cstring+=str(ext)       
        self.set(cstring) #display the header of the current frame


    def frame(self,n=None,command=None):
        """convenience function to change or report frames"""
        if n:
            self.set("frame {0:s}".format(str(n)))
            self._set_filename()
            
        elif command:
            self.set("frame {0:s}".format(str(command)))
            self._set_filename()
        else:
            return ("{0:d}".format(int(self.get("frame"))))

    def get_data(self):
        """ return a numpy array of the data in the current window"""

        self._set_filename() #make sure the filename and extension info are correct for the current frame in DS9
        if not self._filename:
            return None
        else:
            if not self._extver and (len(self._extname) == 0):
                data=pyfits.getdata(self._filename)
            else:
                data=pyfits.getdata(self._filename,extname=self._extname,extver=self._extver)                  
            return data

    def get_header(self):
        """return the current fits header as a string"""
        if self._filename:
            return self.get("fits header")       
        else:
            warnings.warn("No file loaded")
            return None       
        
    def grid(self,on=True,param=False):
        """convenience to turn the grid on and off, grid can be flushed with many more options"""
        self.set("grid %s"%(str(on)))
        if param:
            self.set("grid open")

    def hideme(self):
        """lower the ds9 window"""
        self.set("lower")

    def load_fits(self, fname="", extver=1,extname=""):
        """convenience function to load fits image to current frame
        
        
          To tell ds9 to open a file whose name or path includes spaces, 
          surround the path with "{...}", e.g.
          % xpaset -p ds9 file "{foo bar/my image.fits}"  
          This is assuming that the image loads into the current or next new frame, watch the internal
          file and ext values because the user can switch frames through DS9 app itself      
          
          XPA needs to have the absolute path to the filename so that if the DS9 window was started
          in another directory it can still find the file to load. arg. 
        """
        if fname:
            #see if the image is MEF or Simple   
            fname=os.path.abspath(fname)         
            try:
                #strip the extensions for now
                shortname=fname.split("[")[0]
                isExtend=pyfits.getval(shortname,ext=0,keyword='EXTEND')
                if not isExtend or '[' in fname:
                    cstring=('file fits {0:s}'.format(fname))
                elif extver and not extname:
                    cstring=('file fits {0:s}[{1:d}]'.format(fname,extver))
                elif extver and extname:
                    cstring=('file fits {0:s}[{1:s},{2:d}]'.format(fname,extname,extver))
            except IOError as e:
                print("Exception: {0}".format(e))
                raise IOError
                
            self.set(cstring)
            self._set_filename()
        else:
            print("No filename provided")
                        
    def load_region(self, filename):
        """Load regions from a file which uses ds9 standard formatting"""
        if os.access(filename,os.F_OK):
            self.set("regions load %s" % filename)
        else:
            warnings.warn("No such file:{0:s}".format(filename))

    def mark_region_from_array(self,input_points,rtype="circle",ptype="image",textoff=10,size=5):
        """mark ds9 regions regions  given an input list of tuples
        
        Parameters
        ----------
        input_points: a tuple, or list of tuples, or a string: (x,y,comment), 
            
        
        ptype: string
            the reference system for the point locations, image|physical|fk5
        rtype: string
            the matplotlib style marker type to display
        size: int
            the size of the region marker
            
        textoff: string
            the offset for the comment text, if comment is empty it will not show
            
        """
        if isinstance(input_points,tuple):
            input_points=[tuple(input_points)]
        elif isinstance(input_points,str):
            input_points=[tuple(input_points.split())]
        
        X=0
        Y=1
        COMMENT=2
        for location in list(input_points):
            pline="image; "+rtype+"("+str(location[X])+","+str(location[Y])+","+str(size)+")\n"
            self.set_region(pline)
            if(len(str(location[COMMENT])) > 0):
                pline="image;text(" +str(float(location[X])+textoff)+","+str(float(location[Y])+textoff)+"{ "+str(location[COMMENT])+" })# font=\"time 12 bold\"\n"
                self.set_region(pline)


    def make_region(self,infile,labels=False,header=0,textoff=10,rtype="circle",size=5):
        """make an input reg file with  [x,y,comment] to a DS9 reg file, the input file should contains lines with x,y,comment
        
        
        Parameters
        ----------
        
        infile: str
            input filename
            
        labels: bool
            add labels to the regions
            
        header: int
            number of header lines in text file to skip
            
        textoff: int
            offset in pixels for labels
            
        rtype: str
            region type, one of the acceptable ds9 regions
            
        size: int
            size of the region type
        
        """

        try:
            f=open(infile,'r')
            lines=f.readlines()
            f.close()

        except IOError as e:
            warnings.warn("Unable to open input file")
            print("{0}".format(e))
            raise ValueError

        #assumed defaults for simple regions file
        point=rtype
        delta=textoff #pixels to offset text
        lines=lines[header:]

        numCols=len(lines[0])
        text=list()
        x=list()
        y=list()

        for i in range(0,len(lines),1):
            words=lines[i].split(',')
            x.append(words[0].strip())
            y.append(words[1].strip())
            if(numCols > 2 and labels):
                text.append(words[2].strip())

        #now write out to a reg file
        out=infile + ".reg"
        f=open(out,'w')
        for i in range(0,len(lines),1):
            pline="image; "+point+"("+x[i]+","+y[i]+","+str(size)+")\n"
            f.write(pline)
            if(len(text) > 0):
                pline="image;text(" +str(float(x[i])+delta)+","+str(float(y[i])+delta)+"{ "+text[i]+" })# font=\"time 12 bold\"\n"
                f.write(pline)
        f.close()

        print("output reg file saved to: {0:s}".format(out))


    def match(self,coordsys="physical",frame=False,crop=False,fslice=False,scale=False,bin=False,colorbar=False,smooth=False,crosshair=False):
        """match all other frames to the current frame"""
        cstring="match "
        if frame:
            cstring += "frame {0:s}".format(corrdsys)
        elif crosshair:
            cstring += "crosshair {0:s}".format(corrdsys)
        elif crop:
            cstring += "crop {0:s}".format(corrdsys)
        elif fslice:
            cstring += "slice"
        elif bin:
            cstring += "bin"
        elif scale:
            cstring += "scale"
        elif colorbar:
            cstring += "colorbar"
        elif smooth:
            cstring += "smooth"
        self.set(cstring)          

    def nancolor(self,color="red"):
        """set the not-a-number color, default is red"""
        self.set("nan {0:s}".format(color))      
        
        
    def panto_image(self, x, y):
        """convenience function to change to x,y images coordinates using ra,dec
           x, y in image coord"""
           
        self.set("pan to %10.8f %10.8f image" % (x, y)) # (ra, dec))

    def panto_wcs(self, x, y,system='fk5'):
        """pan to wcs coordinates in image"""
        self.set("pan to %10.8f %10.8f wcs %s"%(x,y,system))

    def save_header(self,filename=None):
        """save the header of the current image to a file"""
        cstring="header "
        if not filename:
            filename=self._filename + "_header.txt"
        #leaving this out for now so that the current header of frame is used
        #it will need to be updated if an image cube is loaded I believe    
        cstring+="save %s"%(filename)
        self.set(cstring)
        print("header saved to {0:s}".format(filename))
        logging.info("header saved to {0:s}".format(filename))

            
    def save_regions(self, filename=None):
        """save the regions in the current window to a DS9 style regions file"""
        regions=self.get("regions save")
        
        #check if the file already exists
        if not os.access(filename,os.F_OK):
            with open(filename,"w") as region_file:
                region_file.write(regions)
        else:
            warnings.warn("File already exists, try again")

    def scale(self,scale='zscale'):
        """ The default zscale is the most widely used option"""
        
        _help="""Syntax: 
           scales available: [linear|log|pow|sqrt|squared|asinh|sinh|histequ]
           
          [log exp <value>] 
          [datasec yes|no] 
          [limits <minvalue> <maxvalue>] 
          [mode minmax|<value>|zscale|zmax] 
          [scope local|global] 
          [match]
          [lock [yes|no]]
          [open|close]

          """
        mode_scale=["zscale","zmax","minmax"]
        
        if scale in mode_scale:
            cstring=("scale mode %s")%(scale)
        else:
            cstring=("scale %s")%(scale)
        try:
            self.set(cstring)     
        except:
            print(_help)


    def set_region(self, region_string=""):
        """display a region using the specifications in region_string"""
        if region_string[-1] != "\n":
            region_string = region_string + "\n"

        self.set("regions", region_string)

    def showme(self):
        """raise the ds9 window"""
        self.set("raise")

    def showpix(self,close=False):
        """display the pixel value table, close window when done"""
        self.get("pixeltable")
        if close:
            self.set("pixeltable close")
    
    def snapsave(self,filename=None,format=None,resolution=100):
        """create a snap shot of the current window and save in specified format. If no format is specified the filename extension is used
        
            filename: str
                filename of output image
                
            format: str
                available formats are fits, eps, gif, tiff, jpeg, png
                
            resolution: int
                1 to 100, for jpeg images
        """
        if not filename:
            filename=self._filename + "_snap.jpg"
            
        cstring="saveimage "
        name=filename
        if format:
            name=filename + format            
        cstring += name
        if "jpeg" in name:
            cstring += (" " + str(resolution))
        self.set(cstring)
        print("Image saved to {0:s}".format(filename))
        logging.info("Image saved to {0:s}".format(filename))

    def view(self, img, header=None, frame=None):
        """ Display numpy image array
        
        img: numpy array
        header: pyfits.header
        frame: display frame
        """

        _frame_num = self.frame()

        try:
            if frame:
                self.frame(frame)

            self.view_array(img)

        except:
            self.frame(_frame_num)
            raise

    def view_array(self, img):
        """Helper function to display numpy image array"""
        
        img = np.array(img)
        if img.dtype.type == np.bool8:
            img = img.astype(np.uint8)

        try:
            img.shape = img.shape[-2:]
        except:
            raise UnsupportedImageShapeException(repr(img.shape))


        if img.dtype.byteorder in ["=", "|"]:
            dt=img.dtype.newbyteorder(">")
            img=np.array(img, dtype=dt)
            #img=img.astype(dt)
            byteorder=">"
        else:
            byteorder=img.dtype.byteorder

        endianness = {">":",arch=bigendian",
                      "<":",arch=littleendian"}[byteorder]
        (ydim, xdim) = img.shape
        arr_str = img.tostring()

        itemsize = img.itemsize * 8
        try:
            bitpix = self._ImgCode[img.dtype.name]

            #bitpix = pyfits.core._ImageBaseHDU.ImgCode[img.dtype.name]
        except KeyError as a:
            raise UnsupportedDatatypeException(a)

        option = "[xdim=%d,ydim=%d,bitpix=%d%s]" % (xdim, ydim,
                                                    bitpix, endianness)

        self.set("array "+option, arr_str)

    def zoomtofit(self):
        """convenience function for zoom"""
        self.set("zoom to fit")

                                      
    def zoom(self,par="to fit"):
        """ par can be a number, to fit, open or close"""
        self.set("zoom %s"%(str(par)))
                    

import atexit
atexit.register(ds9._purge_tmp_dirs)

