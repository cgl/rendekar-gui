#!/usr/bin/env python
import sys, time
from PyQt4 import QtCore, QtGui
import gui, utils, shell
from threading import Thread
from datetime import datetime, timedelta

class UpdateLogEvent(QtCore.QEvent):
    EVENT_ID = QtCore.QEvent.Type(1500) 
    
    def __init__(self, type, text):
        QtCore.QEvent.__init__(self, UpdateLogEvent.EVENT_ID)
        self.text = text
        self.log_type = type

class PipesGui(QtGui.QMainWindow):
    def __init__(self, programs_tracker, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.ui = gui.Ui_MainWindow()
        self.ui.setupUi(self)
        
        self.programs = programs_tracker
        self.recorder = utils.RecordManager(self, self.programs)
        self.flux = utils.FluxManager(self, self.programs)
    	#self.ui.conf_audio_only_chk.setEnabled(False)
        
    def onOptionsSwitch(self, state):
        option = utils.get_record_source_from_checkbox_name(self.sender())
        utils.switch_port_entry_state(self.ui, option, state)

    def onFluxCmd(self):
        if self.flux.get_status() == 'started':
            self.flux.stop()
        else:
            self.flux.start()

    def onRecordStart(self):
        if not self.recorder.start():
            return
        self.flux.enable(True)

    def onRecordStop(self):
        self.flux.enable(False)
        self.recorder.stop()
        
    def customEvent(self, event):
        if event.type() == UpdateLogEvent.EVENT_ID:
            self.log(event.log_type, event.text)
            
    def onTabSwitch(self, tab_id):
        if (tab_id == 0):
            self.ui.logtab.setTabText(0, "AV Producer")
        elif (tab_id == 1):
            self.ui.logtab.setTabText(1, "Audio Only Producer")
        elif (tab_id == 2):
            self.ui.logtab.setTabText(2, "Flux")
            
    def log(self, type, text):        
        if type == 'record':
            self.ui.log_record.append("[%s] %s" % (datetime.now().strftime("%H:%M:%S"), text))
            if self.ui.logtab.currentIndex() != 0:
                self.ui.logtab.setTabText(0, "* AV Producer")
        elif type == 'audio_only':
            self.ui.log_producer_audio1.append("[%s] %s" % (datetime.now().strftime("%H:%M:%S"), text))
            if self.ui.logtab.currentIndex() != 1:
                self.ui.logtab.setTabText(1, "* Audio Only Producer")
        elif type == 'flux':
            self.ui.log_flux.append("[%s] %s" % (datetime.now().strftime("%H:%M:%S"), text))
            if self.ui.logtab.currentIndex() != 2:
                self.ui.logtab.setTabText(2, "* Flux")

class ProgramsTracker(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.ui = None
        
        self.dvgrab = None
        self.last_dvgrab_update = datetime.now()
        self.flux = None
        
        self.running = True
        
    def run(self):
        while self.running:
            if self.dvgrab != None:
                res = self.dvgrab.communicate() 
                if res == True:
                    self.last_dvgrab_update = datetime.now()
                elif res == False:
                    delta = datetime.now() - self.last_dvgrab_update
                    if delta >= timedelta(0, 2, 0):
                        event = UpdateLogEvent('record', "??? SLOW DVGRAB... ???")
                        QtGui.qApp.postEvent(self.ui, event)
                        self.last_dvgrab_update = datetime.now()
                else:
                    event = UpdateLogEvent('record', "!!! PRODUCER DIED !!!")
                    QtGui.qApp.postEvent(self.ui, event)
                    dvgrab = self.dvgrab
                    self.dvgrab = None
                    shell.terminate(dvgrab)
            if self.flux != None:
                if self.flux.communicate() == -1:
                    event = UpdateLogEvent('flux', "!!! FLUX DIED !!!")
                    QtGui.qApp.postEvent(self.ui, event)
                    prod = self.flux
                    self.flux = None
                    shell.terminate(prod)
            if self.flux == self.dvgrab == None:
                time.sleep(0.2)
                    
    def stop(self):
        self.running = False
        if self.dvgrab:
            shell.terminate(self.dvgrab)
        if self.flux:
            shell.terminate(self.flux)

if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    
    programs = ProgramsTracker()    
    myapp = PipesGui(programs)
    programs.ui = myapp
    
    programs.start()
    myapp.show()
    
    val = app.exec_()
    programs.stop()
    programs.join()
    sys.exit(val)
