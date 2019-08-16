# -*- coding: UTF-8 -*-

#########################################################
# Name: streams_tools.py
# Porpose: Redirect any input/output resources to process
# Compatibility: Python3, wxPython Phoenix
# Author: Gianluca Pernigoto <jeanlucperni@gmail.com>
# Copyright: (c) 2018/2019 Gianluca Pernigoto <jeanlucperni@gmail.com>
# license: GPL3
# Rev (02) December 28 2018
#########################################################

# This file is part of Videomass.

#    Videomass is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.

#    Videomass is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.

#    You should have received a copy of the GNU General Public License
#    along with Videomass.  If not, see <http://www.gnu.org/licenses/>.

#########################################################

import wx
import platform

if platform.system() == 'Windows':
    from videomass3.vdms_PROCESS.task_processingWin32 import GeneralProcess
    from videomass3.vdms_PROCESS.task_processingWin32 import ProcThread
    from videomass3.vdms_PROCESS.task_processingWin32 import DoublePassThread
    from videomass3.vdms_PROCESS.task_processingWin32 import GrabAudioProc
    from videomass3.vdms_PROCESS.task_processingWin32 import SingleProcThread
    from videomass3.vdms_PROCESS.volumedetectWin32 import VolumeDetectThread
    from videomass3.vdms_PROCESS.volumedetectWin32 import PopupDialog
    from videomass3.vdms_PROCESS.ffplay_reproductionWin32 import Play
    from videomass3.vdms_PROCESS.ffprobe_parserWin32 import FFProbe
    from videomass3.vdms_PROCESS.check_bin import ffmpeg_conf
else:
    from videomass3.vdms_PROCESS.task_processing import GeneralProcess
    from videomass3.vdms_PROCESS.task_processing import ProcThread
    from videomass3.vdms_PROCESS.task_processing import DoublePassThread
    from videomass3.vdms_PROCESS.task_processing import GrabAudioProc
    from videomass3.vdms_PROCESS.task_processing import SingleProcThread
    from videomass3.vdms_PROCESS.volumedetect import VolumeDetectThread
    from videomass3.vdms_PROCESS.volumedetect import PopupDialog
    from videomass3.vdms_PROCESS.ffplay_reproduction import Play
    from videomass3.vdms_PROCESS.ffprobe_parser import FFProbe
    from videomass3.vdms_PROCESS.check_bin import ffmpeg_conf
    
from videomass3.vdms_DIALOGS.mediainfo import Mediainfo
from videomass3.vdms_DIALOGS import checkconf

#-----------------------------------------------------------------------#
def process(self, varargs, path_log, panelshown, duration, OS, time_seq):
    """
    1) TIME DEFINITION FOR THE PROGRESS BAR
        For a suitable and efficient progress bar, if a specific 
        time sequence has been set with the duration tool, the total duration 
        of each media file will be replaced with the set time sequence. 
        Otherwise the duration of each media will be the one originated from 
        its real duration.
        
    2) STARTING THE PROCESS
        Than, the process is assigned to the most suitable thread and at 
        the same time the panel with the progress bar is instantiated.
    """
    if time_seq:
        newDuration = []
        dur = time_seq.split()[3] # the -t flag
        h,m,s = dur.split(':')
        totalsum = (int(h)*60+ int(m)*60+ int(s))
        for n in duration:
            newDuration.append(totalsum)
        duration = newDuration
    
    if varargs[0] == 'normal':# video conv and audio conv panels
        ProcThread(varargs, duration, OS) 
        
    elif varargs[0] == 'doublepass': # video conv panel
        DoublePassThread(varargs, duration, OS)
        
    elif varargs[0] == 'saveimages': # video conv panel
        SingleProcThread(varargs, duration, OS)
        
    elif varargs[0] == 'grabaudio':# audio conv panel
        GrabAudioProc(varargs, duration, OS)

    self.ProcessPanel = GeneralProcess(self, path_log, panelshown, varargs)
#-----------------------------------------------------------------------#
def stream_info(title, filepath , ffprobe_link):
    """
    Show media information of the streams content.
    This function make a bit control of file existance.
    """
    try:
        with open(filepath):
            dialog = Mediainfo(title, filepath, ffprobe_link)
            dialog.Show()

    except IOError:
        wx.MessageBox(_("File does not exist or not a valid file:  %s") % (
            filepath), "Videomass: warning", wx.ICON_EXCLAMATION, None)
        
#-----------------------------------------------------------------------#
def stream_play(filepath, param, ffplay_link, loglevel_type, OS):
    """
    Thread for media reproduction with ffplay
    """
    try:
        with open(filepath):
            thread = Play(filepath, param, ffplay_link, loglevel_type, OS)
            #thread.join()# attende che finisca il thread (se no ritorna subito)
            #error = thread.data
    except IOError:
        wx.MessageBox(_("File does not exist or not a valid file:  %s") % (
            filepath), "Videomass: warning", wx.ICON_EXCLAMATION, None)
        return
    
#-----------------------------------------------------------------------#
def probeDuration(path_list, ffprobe_link):
    """
    Parsa i metadati riguardanti la durata (duration) dei media importati, 
    utilizzata per il calcolo della progress bar. Questa funzione viene 
    chiamata nella MyListCtrl(wx.ListCtrl) con il pannello dragNdrop.
    Se i file non sono supportati da ffprobe e quindi da ffmpeg, avvisa
    con un messaggio di errore.
    """
    metadata = FFProbe(path_list, ffprobe_link, 'no_pretty') 
        # first execute a control for errors:
    if metadata.ERROR():
        err = metadata.error
        print ("[FFprobe] Error:  %s" % err)
        #wx.MessageBox("%s\nFile not supported!" % (metadata.error),
                      #"Error - Videomass", 
                      #wx.ICON_ERROR, None)
        duration = 0
        return duration, err
    try:
        for items in metadata.data_format()[0]:
            if items.startswith('duration='):
                duration = (int(items[9:16].split('.')[0]))
    except ValueError as ve:
        duration = 0
        if ve.args[0] == "invalid literal for int() with base 10: 'N/A'":
            return duration, 'N/A'
        else:
            return duration, ve.args
    
    return duration , None
#-------------------------------------------------------------------------#
def volumeDetectProcess(ffmpeg, filelist, OS):
    """
    Run a thread for get audio peak level data and show a pop-up dialog 
    with message. 
    """
    thread = VolumeDetectThread(ffmpeg, filelist, OS) 
    loadDlg = PopupDialog(None, 
                          _("Videomass - Loading..."), 
                          _("\nWait....\nAudio peak analysis.\n")
                          )
    loadDlg.ShowModal()
    #thread.join()
    data = thread.data
    loadDlg.Destroy()
    
    return data
#-------------------------------------------------------------------------#
def testFFmpeg_conf(ffmpeg_link, ffprobe_link, ffplay_link, OS):
    """
    Call *check_bin.ffmpeg_conf* to get data to test the building 
    configurations of the installed or imported FFmpeg executable 
    and send it to dialog box.
    
    
    """
    out = ffmpeg_conf(ffmpeg_link, OS)
    if 'Not found' in out[0]:
        wx.MessageBox(_("FFmpeg executable not found !"
                        "\n\n{0}".format(out[1])), 
                      "Videomass: error",
                      wx.ICON_ERROR, 
                      None)
        return
    else:
        dlg = checkconf.Checkconf(out, ffmpeg_link, 
                                  ffprobe_link, ffplay_link
                                  )
        dlg.Show()
        
