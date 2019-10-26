# -*- coding: UTF-8 -*-

#########################################################
# Name: dragNdrop.py
# Porpose: drag n drop interface
# Compatibility: Python3, wxPython Phoenix
# Author: Gianluca Pernigoto <jeanlucperni@gmail.com>
# Copyright: (c) 2018/2019 Gianluca Pernigoto <jeanlucperni@gmail.com>
# license: GPL3
# Rev: Dec.28.2018, Sept.12.2019
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
import os
from videomass3.vdms_IO import IO_tools

dirname = os.path.expanduser('~') # /home/user/
duration = []
data_files = []

azure = '#d9ffff' # rgb form (wx.Colour(217,255,255))
red = '#ea312d'
yellow = '#a29500'
greenolive = '#6aaf23'
orange = '#f28924'

def convert(time):
    """
    convert time human to seconds
    """
    print(time)
    
    if time == 'N/A':
        return int('0')
    
    pos = time.split(':')
    h,m,s = pos[0],pos[1],pos[2]
    totalsum = (int(h)*60+ int(m)*60+ float(s))
    
    return totalsum

########################################################################
class MyListCtrl(wx.ListCtrl):
    """
    This is the listControl widget. Note that this wideget has DnDPanel
    parent.
    """
    #----------------------------------------------------------------------
    def __init__(self, parent, fileList, ffprobe_link):
        """Constructor"""
        wx.ListCtrl.__init__(self, parent, style=wx.LC_REPORT|wx.LC_SINGLE_SEL)
        self.index = 0
        self.parent = parent # parent is DnDPanel class
        self.fileList = fileList
        self.invalid = False # used for directories import control
        self.ffprobe_link = ffprobe_link
        
        print(self.index)
        

    #----------------------------------------------------------------------#
    def dropUpdate(self, path):
        """
        Update list-control during drag and drop
        """
        if os.path.isdir(path):
            mess = _("Directories are not allowed, just add files, please")
            print (mess)
            self.parent.statusbar_msg(mess, orange)
            self.invalid = True
            return
        
        #if path not in self.fileList:
        if not [x for x in data_files if x['filename'] == path]:

            self.invalid = False
            #self.fileList.append(path)
            #self.InsertItem(self.index, path)
            #self.index += 1
            
            data_dict = IO_tools.probeDuration(path, self.ffprobe_link)
            
            if data_dict[1] == 'N/A':
                duration.append(0)
                #data_files.append(data_dict[0])
                msg = "%s; %s" %(data_dict[1],_('duration is skipped'))
                print(msg)
                
            elif data_dict[1]:
                self.parent.statusbar_msg(data_dict[1], red)
                return

            if self.parent.which() == 'Video Conversions':
                if not data_dict[0].get('video_codec_name') in ['mpeg4','h264']:
                    self.parent.statusbar_msg('Not such Video stream', orange)
                else:
                    self.InsertItem(self.index, path)
                    self.index += 1
                    data_files.append(data_dict[0])
                    t = convert(data_dict[0]['duration'])
                    duration.append(t)
                    self.parent.statusbar_msg('', None)
                    
            elif self.parent.which() == 'Audio Conversions':
                if data_dict[0].get('video_codec_type'):
                    self.parent.statusbar_msg('Not such Audio stream', orange)
                else:
                    self.InsertItem(self.index, path)
                    self.index += 1
                    data_files.append(data_dict[0])
                    t = convert(data_dict[0]['duration'])
                    duration.append(t)
                    self.parent.statusbar_msg('', None)
                    
            elif self.parent.which() == 'Pictures Slideshow Maker':
                l = ['bmp','png','mjpeg']
                if not data_dict[0].get('video_codec_name') in l:
                    self.parent.statusbar_msg('Not such Pictures imported', orange)
                else:
                    self.InsertItem(self.index, path)
                    self.index += 1
                    data_files.append(data_dict[0])
                    t = convert(data_dict[0]['duration'])
                    duration.append(t)
                    self.parent.statusbar_msg('', None)
            
            
            
        else:
            mess = _("Duplicate files are rejected: > '%s'") % path
            print (mess)
            self.parent.statusbar_msg(mess, yellow)
            
    #----------------------------------------------------------------------#
    def send_data(self):
        """
        enable buttons and send data to parent in non-recursive mode
        """
        self.parent.btn_enable(self.fileList, self.invalid)

########################################################################
class MyFileDropTarget(wx.FileDropTarget):
    """
    This is the file drop target
    """
    #----------------------------------------------------------------------#
    def __init__(self, window):
        """
        Constructor. File Drop targets are subsets of windows
        """
        wx.FileDropTarget.__init__(self)
        self.window = window # window is MyListCtr class
    #----------------------------------------------------------------------#
    def OnDropFiles(self, x, y, filenames):
        """
        When files are dropped, write where they were dropped and then
        the file paths themselves
        """
        for filepath in filenames:
            self.window.dropUpdate(filepath) # update list control

        # send data at end of every drag n drop action:
        self.window.send_data()
        return True

########################################################################
class DnDPanel(wx.Panel):
    """
    Panel for dragNdrop files queue. Accept one or more files.
    """
    def __init__(self, parent, ffprobe_link):  
        """Constructor. This will initiate with an id and a title"""
        wx.Panel.__init__(self, parent=parent)
        self.parent = parent # parent is the MainFrame
        self.file_dest = dirname # path name files destination
        self.fileList = [] # list of each imported file
        self.duration = duration # list of the duration of each file imported
        self.switch = 'off' # tells if one or more files are imported
        self.selected = False # tells if an imported file is selected or not
        #This builds the list control box:
        
        self.fileListCtrl = MyListCtrl(self, self.fileList, ffprobe_link)  #class MyListCtr
        #Establish the listctrl as a drop target:
        file_drop_target = MyFileDropTarget(self.fileListCtrl)
        self.fileListCtrl.SetDropTarget(file_drop_target) #Make drop target.

        # create widgets
        btn_clear = wx.Button(self, wx.ID_CLEAR, "")
        self.ckbx_dir = wx.CheckBox(self, wx.ID_ANY, (
                                _("Save destination in source folder")))
        self.btn_save = wx.Button(self, wx.ID_OPEN, "...", size=(-1,-1))
        self.text_path_save = wx.TextCtrl(self, wx.ID_ANY, "", 
                                                style=wx.TE_PROCESS_ENTER| 
                                                      wx.TE_READONLY
                                                      )
        self.lbl = wx.StaticText(self, label=_("Drag one or more files here:"))
        self.fileListCtrl.InsertColumn(0, '' ,width=700)
        # create sizers layout
        sizer = wx.BoxSizer(wx.VERTICAL)
        grid = wx.FlexGridSizer(1, 4, 5, 5)
        sizer.Add(self.lbl, 0, wx.ALL|
                          wx.ALIGN_CENTER_HORIZONTAL|
                          wx.ALIGN_CENTER_VERTICAL, 5)
        sizer.Add(self.fileListCtrl, 1, wx.EXPAND|wx.ALL, 5)
        sizer.Add(grid)
        grid.Add(btn_clear, 1, wx.ALL|
                               wx.ALIGN_CENTER_HORIZONTAL|
                               wx.ALIGN_CENTER_VERTICAL, 5
                               )
        grid.Add(self.ckbx_dir, 1, wx.ALL|
                                   wx.ALIGN_CENTER_HORIZONTAL|
                                   wx.ALIGN_CENTER_VERTICAL, 5
                                   )
        grid.Add(self.btn_save, 1, wx.ALL|
                                   wx.ALIGN_CENTER_HORIZONTAL|
                                   wx.ALIGN_CENTER_VERTICAL, 5
                                   )
        grid.Add(self.text_path_save, 1, wx.ALL|wx.EXPAND, 5)
        self.text_path_save.SetMinSize((290, -1)) 
        self.SetSizer(sizer)
        
        self.Bind(wx.EVT_BUTTON, self.deleteAll, btn_clear)
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.on_select, self.fileListCtrl)
        self.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.on_deselect, self.fileListCtrl)
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.on_doubleClick, self.fileListCtrl)
        self.Bind(wx.EVT_CONTEXT_MENU, self.onContext)
        #self.Bind(wx.EVT_CHECKBOX, self.same_filedest, self.ckbx_dir)
        #self.Bind(wx.EVT_BUTTON, self.on_custom_save, self.btn_save)
        
        self.text_path_save.SetValue(self.file_dest)
    
    #----------------------------------------------------------------------
    def which(self):
        """
        return topic name by choose_topic.py selection 
    
        """
        #self.lbl.SetLabel('Drag one or more Video files here')
        return self.parent.topicname
    #----------------------------------------------------------------------
    def onContext(self, event):
        """
        Create and show a Context Menu
        """
        # only do this part the first time so the events are only bound once 
        if not hasattr(self, "popupID1"):
            self.popupID1 = wx.NewId()
            self.itemTwoId = wx.NewId()
            self.itemThreeId = wx.NewId()
            self.Bind(wx.EVT_MENU, self.onPopup, id=self.popupID1)
            self.Bind(wx.EVT_MENU, self.onPopup, id=self.itemTwoId)
            self.Bind(wx.EVT_MENU, self.onPopup, id=self.itemThreeId)
 
        # build the menu
        menu = wx.Menu()
        itemOne = menu.Append(self.popupID1, _("Play selected file"))
        itemTwo = menu.Append(self.itemTwoId, _("Show metadata window"))
        itemThree = menu.Append(self.itemThreeId, _("Remove the selected file"))
 
        # show the popup menu
        self.PopupMenu(menu)
        menu.Destroy()
    #----------------------------------------------------------------------
    def onPopup(self, event):
        """
        Evaluate the label string of the menu item selected and start
        the related process
        """
        itemId = event.GetId()
        menu = event.GetEventObject()
        menuItem = menu.FindItemById(itemId)
        

        if not self.selected:
            self.parent.statusbar_msg(_('No file selected to `%s` yet') % 
                                      menuItem.GetLabel(), yellow)
        else:
            self.parent.statusbar_msg('Add Files', None)
            if menuItem.GetLabel() == _("Play selected file"):
                self.parent.ImportPlay()
                
            elif menuItem.GetLabel() == _("Show metadata window"):
                #self.on_doubleClick(self)
                self.parent.ImportInfo(self)
                
            elif menuItem.GetLabel() == _("Remove the selected file"):
                if self.fileListCtrl.GetItemCount() == 1:
                    self.deleteAll(self)
                else:
                    item = self.fileListCtrl.GetFocusedItem()
                    self.fileListCtrl.DeleteItem(item)
                    self.parent.importClicked_disable()
                    self.selected = False
                    self.fileList.pop(item)
                    self.duration.pop(item)
                    
    #----------------------------------------------------------------------
    def btn_enable(self, fileList, invalid):
        """
        When is dropped any files, Enable MainFrame Toolbar buttons.
        The 'if' statement prevents the call to the function to be unnecessarily 
        recursive, as well as the setting of the variables.
        """
        if invalid:
            return
        if self.switch == 'off':
            self.switch = 'on'
    #----------------------------------------------------------------------
    def deleteAll(self, event):
        """
        Delete and clear all text lines of the TxtCtrl,
        reset the fileList[], disable Toolbar button and menu bar
        Stream/play select imported file - Stream/display imported...
        """
        #self.fileListCtrl.ClearAll()
        self.fileListCtrl.DeleteAllItems()
        del self.fileList[:]
        del duration[:]
        del self.duration[:]
        self.switch = 'off'
        self.selected = False
    #----------------------------------------------------------------------
    def on_select(self, event):
        """
        Selecting a line with mouse or up/down keyboard buttons
        """
        index = self.fileListCtrl.GetFocusedItem()
        item = self.fileListCtrl.GetItemText(index)
        self.selected = True
        
        print(data_files)
    #----------------------------------------------------------------------
    def on_doubleClick(self, row):
        """
        Double click or keyboard enter button, open media info
        """
        self.onContext(self)
        #self.parent.ImportInfo(self)
    #----------------------------------------------------------------------
    def on_deselect(self, event):
        """
        De-selecting a line with mouse by click in empty space of
        the control list
        """
        self.selected = False
    #----------------------------------------------------------------------
    def on_custom_save(self):
        """
        Choice a specific directory for files save
        """
        dialdir = wx.DirDialog(self, _("Videomass: Choose a directory"))
            
        if dialdir.ShowModal() == wx.ID_OK:
            self.text_path_save.SetValue("")
            self.text_path_save.AppendText(dialdir.GetPath())
            self.file_dest = '%s' % (dialdir.GetPath())
            dialdir.Destroy()
    #----------------------------------------------------------------------
    def same_filedest(self):
        """
        Save destination as files sources 
        """
        if self.ckbx_dir.GetValue() is True:
            self.file_dest = 'same dest'
            self.text_path_save.Disable(), self.btn_save.Disable()
            self.parent.file_save.Enable(False)
            
        elif self.ckbx_dir.GetValue() is False:
            self.file_dest = self.text_path_save.GetValue()
            self.text_path_save.Enable(), self.btn_save.Enable()
            self.parent.file_save.Enable(True)
    #----------------------------------------------------------------------
    
    def statusbar_msg(self, mess, color):
        """
        Set a status bar message of the parent method.
        """
        self.parent.statusbar_msg('%s' % mess, color)
 
