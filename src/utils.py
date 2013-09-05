import shell

def get_record_source_from_checkbox_name(chk):
    return chk.objectName()[:-4][5:]

def get_checkbox_for_record_source(ui, record_source):
    checkbox_name = str('conf_'+record_source+'_chk')
    chk = getattr(ui, checkbox_name)
    return chk

def get_entry_for_record_source(ui, record_source):
    if record_source == 'av':
        return [getattr(ui, str('flux_video_port')), getattr(ui, str('flux_audio_port'))]
    else: 
        entry_name = str('flux_'+record_source+'_port')
        entry = getattr(ui, entry_name)
        return [entry]

def get_flux_protocol(ui):
    if ui.tcp_enable_conf.checkState():
        return 'tcp://'
    else:
        return 'udp://'

def switch_port_entry_state(ui, option, state):
    entry = get_entry_for_record_source(ui, option)
    if state:
        for e in entry:
            e.setEnabled(True)
    else:
        for e in entry:
            e.setEnabled(False)

def cleanText(text):
    return text.replace(" ","_").replace("'","_").replace('"','_')
    
class RecordManager(object):
    def __init__(self, ui, programs):
        self.window = ui.ui
        self.programs = programs
        self.ui = ui
    
    def start(self):        
        self.ui.log('record', "--- STARTING RECORDER ---")
        try:
            enable_secondary_audio = self.window.conf_audio_only_chk.isChecked()
            name1 = cleanText(self.window.conf_record_name.text())
            name2 = cleanText(self.window.conf_record_name_2.text())
            date = self.window.date.text().replace("/","-")
            filename = name1+"-"+name2+"-"+date
            self.programs.dvgrab = shell.run_dvgrab(filename, enable_secondary_audio)
        except Exception, e:
            print e
            self.programs.dvgrab = None
        
        if self.programs.dvgrab:
            self.window.record_start_btn.setEnabled(False)
            self.window.record_stop_btn.setEnabled(True)
            self.window.conf_record_name.setEnabled(False)
            return True
        else:
            self.ui.log('record', "!!! FAILED TO START RECORDER !!!")
            return False
    
    def stop(self):
        self.window.record_start_btn.setEnabled(True)
        self.window.record_stop_btn.setEnabled(False)
        self.window.conf_record_name.setEnabled(True)

        dvgrab = self.programs.dvgrab
        self.programs.dvgrab = None
        shell.terminate(dvgrab)
        self.ui.log('record', "--- STOPPED RECORDER ---")
    
class FluxManager(object):
    def __init__(self, ui, programs):
        self.window = ui.ui
        self.programs = programs
        self.ui = ui
       
    def start(self):
        if self.get_status() == 'started':
            return
        
        self.ui.log('flux', "--- STARTING FLUX ---")
        try:
            flux_data = {'host':self.window.flux_host.text(), 
                         'video_port':None, 'audio1_port':None, 'audio2_port':None,
                         'protocol':get_flux_protocol(self.window)}

            flux_data['video_port'] = self.window.flux_video_port.text()
            flux_data['audio1_port'] = self.window.flux_audio_port.text()
            if self.window.conf_audio_only_chk.isChecked():
                flux_data['audio2_port'] = self.window.flux_audio_only_port.text()
                
            self.programs.flux = shell.run_flux(flux_data)
        except Exception, e:
            print e
            self.programs.flux = None
        
        if self.programs.flux:
            self.window.flux_btn.setText('STOP')            
            return True
        else:
            self.ui.log('flux', "!!! FAILED TO START FLUX !!!")
            return False
        
    def stop(self):
        if self.get_status() == 'stopped':
            return
    
        self.window.flux_btn.setText('START')

        flux = self.programs.flux
        self.programs.flux = None
        shell.terminate(flux)
        self.ui.log('flux', "--- STOPPED FLUX ---")
        
    def enable(self, state):
        if state:
            self.window.flux_btn.setEnabled(True)
        else:
            self.stop()
            self.window.flux_btn.setEnabled(False)

    def get_status(self):
        if self.window.flux_btn.text() == 'START':
            return 'stopped'
        else:
            return 'started'
                
