import random
import time
from datetime import datetime


class SensorSimulator:
    def __init__(self):
        self.step = 0
        self.scenario = "normal"

    def set_scenario(self, scenario):
        self.scenario = scenario
        self.step = 0

    def generate_reading(self):
        self.step += 1

        temperature = 29 + random.uniform(-1.5, 1.5)
        dust = 120 + random.uniform(-10, 10)
        motion = random.uniform(0.05, 0.20)
        ldr = 850 + random.uniform(-30, 30)

        if self.scenario == "dust_buildup":
            dust += self.step * 18
            ldr -= self.step * 5

        elif self.scenario == "vibration":
            motion = random.uniform(0.1, 0.9)

        elif self.scenario == "coupled":
            dust += self.step * 20
            ldr -= self.step * 7
            motion = random.uniform(0.25, 0.95)

        elif self.scenario == "recovery":
            dust = max(120, 850 - self.step * 25)
            ldr = min(850, 350 + self.step * 20)
            motion = max(0.1, 0.9 - self.step * 0.04)

        return {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "temperature": round(temperature, 2),
            "dust": round(max(0, dust), 2),
            "motion": round(max(0, min(1, motion)), 3),
            "ldr": round(max(0, min(1023, ldr)), 2)
        }


if __name__ == "__main__":
    simulator = SensorSimulator()
    simulator.set_scenario("coupled")

    for _ in range(10):
        print(simulator.generate_reading())
        time.sleep(1)