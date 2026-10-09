# MineSense AI - ESP32 Integrated Prototype

## Current hybrid architecture

Real ESP32:
- DHT11 -> temperature/humidity
- GP2Y1010AU0F -> dust estimate
- MPU6050 -> acceleration/vibration proxy
- LM393 LDR module -> digital light/dark proxy

Synthetic:
- Camera perception
- LiDAR perception
- Radar perception

Flow:
ESP32 -> COM7 -> PySerial -> Flask backend -> existing AI models -> dashboard

## Run

1. Close Arduino Serial Monitor.
2. Make sure ESP32 is connected on COM7.
3. Install dependencies:

   python -m pip install -r requirements.txt

4. Start the backend:

   cd backend
   python app.py

5. Open the dashboard with the existing OPEN_DASHBOARD.bat or serve
   dashboard/index.html as before.

## Important

The LM393 is connected only through its digital output in this prototype,
so the backend maps its state to the existing LDR feature as a light/dark
proxy. It is not presented as a measured 0-1023 analog illumination value.

The GP2Y1010AU0F dust density is the estimate produced by the ESP32 sketch.
For a real deployment it should be calibrated against a reference
particulate measurement system.

If the ESP32 is disconnected, the backend explicitly falls back to
simulated environmental data so the dashboard can still be demonstrated.
