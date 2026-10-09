def calculate_perception_fusion(p):
    cam=.45*p['camera']['visibility']+.45*p['camera']['object_confidence']+.10*(100-p['camera']['blur'])
    lidar=.30*p['lidar']['effective_range_m']+.30*p['lidar']['point_density']+.25*p['lidar']['object_confidence']+.15*(100-p['lidar']['noise'])
    radar=.40*p['radar']['detection_confidence']+.25*p['radar']['snr']+.25*p['radar']['target_continuity']+.10*(100-p['radar']['false_detections'])
    health={"camera":round(max(0,min(100,cam)),1),"lidar":round(max(0,min(100,lidar)),1),"radar":round(max(0,min(100,radar)),1)}
    fused=.35*health['camera']+.35*health['lidar']+.30*health['radar']
    status='GOOD' if fused>=80 else 'DEGRADED' if fused>=60 else 'HIGH RISK' if fused>=40 else 'CRITICAL'
    reliable=sum(v>=65 for v in health.values())
    redundancy='AVAILABLE' if reliable>=2 else 'LIMITED' if reliable==1 else 'INSUFFICIENT'
    return {"camera_health":health['camera'],"lidar_health":health['lidar'],"radar_health":health['radar'],"fused_perception_confidence":round(fused,1),"status":status,"redundancy":redundancy,"degradation_scores":{k:round((100-v)/100,3) for k,v in health.items()}}
