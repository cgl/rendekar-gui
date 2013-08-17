import os, signal, time, select, fcntl
import subprocess
import utils
from datetime import datetime

def check_if_program_has_data(program):
    p_state = select.select([program.stdout], [], [], 0)
    if not p_state[0]:
        return False
    return True

class Flux(object):
    def __init__(self, more):
        self.flux_video = None
        self.flux_audio1 = None
        self.flux_audio2 = None

        if more['video_port']:
            self.flux_video = '-c udp://1900*live*' + more['protocol'] + more['host'] + ':' + more['video_port']
        if more['audio1_port']:
            self.flux_audio1 = '-c udp://1902*live*' + more['protocol'] + more['host'] + ':' + more['audio1_port']
        if more['audio2_port']:
            self.flux_audio2 = '-c udp://1904*live*' + more['protocol'] + more['host'] + ':' + more['audio2_port']

    def start(self):
        cmd = 'flux'
        if self.flux_video:
            cmd = "%s %s" % (cmd, self.flux_video)
        if self.flux_audio1:
            cmd = "%s %s" % (cmd, self.flux_audio1)
        if self.flux_audio2:
            cmd = "%s %s" % (cmd, self.flux_audio2)

        self.first = subprocess.Popen(cmd, shell=True, close_fds=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        #check if source software has started, should perform a more reliable check in the future
        time.sleep(0.5)
        self.first.poll()

        if self.first.returncode != None:
            return None

        print 'STARTED',cmd
        return self

    def check_if_everything_is_running(self):
        self.first.poll()
        if self.first.returncode != None:
            return False

        return True

    def communicate(self):
        if not self.check_if_everything_is_running():
            return -1

        return True

    def stop(self):
        if self.first:
            try:
                os.kill(self.first.pid, signal.SIGKILL)
                self.first.wait()
            except:
                pass


class Recorder(object):
    def __init__(self, record_name, enable_secondary_audio):
        self.type = type
        stamp = datetime.now().strftime("%Y%m%d.%H%M%S")

        self.record_dvgrab = "dvgrab -f raw -"
        self.record_ffmpeg= 'ffmpeg -y -re -f dv -i - -acodec mp2 -ab 128000 -vcodec mpeg2video -s 480x360 -vb 512000 -f mpeg %s -acodec mp2 -ab 48000 -ac 1 -f rtp rtp://localhost:1902 -an -vcodec mpeg2video -vb 200000 -s 320x200 -f rtp rtp://localhost:1900' % (record_name+'_' + stamp + '.mpg')
        self.more_ffmpegs = []

        self.record_dvgrab='dvgrab -f hdv -size 0'
        self.record_ffmpeg='xargs echo'

#  dvgrab -f hdv -size 0 -i $M2TDIR/rendekar-$KONUSMACI-$EVSAHIBIFN-$MISAFIRFN-$MACTARIHIFN- 2> $MYTTY

        #if enable_secondary_audio:
        #    self.more_ffmpegs.append('ffmpeg -y -f oss -i /dev/dsp -acodec mp2 -ab 128000 %s -acodec mp2 -ac 1 -ab 48000 -f rtp rtp://localhost:%s' % (record_name+'_a.mp3', 1904))

        self.record_name = record_name

    def start(self):
        cmd1 = self.record_dvgrab
        cmd2 = self.record_ffmpeg


        self.first = subprocess.Popen(cmd1, shell=True, close_fds=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        #check if source software has started, should perform a more reliable check in the future
        time.sleep(0.5)
        self.first.poll()

        if self.first.returncode != None:
            return None

        self.second = subprocess.Popen(cmd2, shell=True, close_fds=True, stdin=subprocess.PIPE )
        if not self.second:
            return None

        print 'STARTED',cmd1,'|',cmd2

        fcntl.fcntl(self.first.stdout.fileno(), fcntl.F_SETFL, os.O_NONBLOCK)

        self.others = []
        for more in self.more_ffmpegs:
            print 'STARTING MORE', more
            sub = subprocess.Popen(more, shell=True, close_fds=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if not sub:
                print 'Failed to start', more
                return None
            time.sleep(0.5)
            sub.poll()
            if sub.returncode != None:
                print 'Failed to start', more
                return None
            self.others.append(sub)

        return self

    def check_if_everything_is_running(self):
        self.first.poll()
        if self.first.returncode != None:
            return False

        self.second.poll()
        if self.second.returncode != None:
            return False

        return True

    def communicate(self):
        if not self.check_if_everything_is_running():
            return -1

        if not check_if_program_has_data(self.first):
            return False

        dv_data = self.first.stdout.read(2048)
        if dv_data:
            try:
                self.second.stdin.write(dv_data)
                return True
            except:
                return False

        return False

    def stop(self):
        if self.second:
            try:
                os.kill(self.second.pid, signal.SIGKILL)
                self.second.wait()
            except:
                pass

        if self.first:
            try:
                os.kill(self.first.pid, signal.SIGKILL)
                self.first.wait()
            except:
                pass

        for more in self.others:
            try:
                os.kill(more.pid, signal.SIGKILL)
                more.wait()
            except:
                pass


def run_dvgrab(record_name, enable_secondary_audio):
    r = Recorder(record_name, enable_secondary_audio)
    return r.start()

def run_flux(more):
    r = Flux(more)
    return r.start()

def terminate(p):
    if not p:
        return

    try:
        p.stop()
    except Exception, e:
        print e
        os.kill(p.pid, signal.SIGTERM)
        p.wait()
