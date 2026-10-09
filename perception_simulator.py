import random
from datetime import datetime

class PerceptionSimulator:
    def __init__(self):
        self.step = 0
        self.scenario = "normal"

    def set_scenario(self, scenario):
        self.scenario = scenario
        self.step = 0

    def generate_reading(self):
        self.step += 1
        cam_v, cam_c, blur = random.uniform(90,97), random.uniform(88,96), random.uniform(3,8)
        lr, lp, ln, lc = random.uniform(72,82), random.uniform(90,97), random.uniform(3,8), random.uniform(88,96)
        rc, rs, rf, rt = random.uniform(91,97), random.uniform(82,94), random.uniform(1,4), random.uniform(90,97)

        severity = min(1.0, self.step / 15)
        if self.scenario in ("dust_buildup", "coupled"):
            cam_v -= 48*severity; cam_c -= 52*severity; blur += 25*severity
            lr -= 45*severity; lp -= 55*severity; ln += 38*severity; lc -= 48*severity
        if self.scenario in ("vibration", "coupled"):
            blur += 22*severity; cam_c -= 28*severity; lp -= 20*severity; lc -= 18*severity
            rt -= 10*severity; rc -= 8*severity
        if self.scenario == "fog":
            cam_v -= 60*severity; cam_c -= 62*severity; blur += 12*severity
            lr -= 18*severity; lp -= 22*severity; lc -= 20*severity; rs -= 8*severity
        if self.scenario == "camera_failure":
            s=min(1.0,self.step/8); cam_v-=75*s; cam_c-=75*s; blur+=35*s
        if self.scenario == "lidar_failure":
            s=min(1.0,self.step/8); lr-=55*s; lp-=70*s; ln+=55*s; lc-=70*s
        if self.scenario == "radar_interference":
            s=min(1.0,self.step/10); rc-=55*s; rs-=45*s; rf+=30*s; rt-=45*s
        if self.scenario == "recovery":
            r=min(1.0,self.step/20)
            cam_v=42+50*r; cam_c=38+55*r; blur=30-24*r
            lr=35+42*r; lp=42+52*r; ln=42-35*r; lc=40+52*r
            rc=68+27*r; rs=55+35*r; rf=18-15*r; rt=60+35*r

        def c(v,a=0,b=100): return round(max(a,min(b,v)),2)
        return {"timestamp":datetime.now().isoformat(timespec="seconds"),
                "camera":{"visibility":c(cam_v),"object_confidence":c(cam_c),"blur":c(blur)},
                "lidar":{"effective_range_m":c(lr,0,100),"point_density":c(lp),"noise":c(ln),"object_confidence":c(lc)},
                "radar":{"detection_confidence":c(rc),"snr":c(rs),"false_detections":c(rf),"target_continuity":c(rt)}}
