# fall_detection

## Fall Detector

This project is a fall detector using Python and Flask in a Raspberry Pi.
This is a fall detector that send an e-mail with a photo of the moment when a fall was detected and register the date and time.
Also the Raspberry Pi will be connected to two sensors, SpO2 (Pulse Oximeter) and BPM (Beats per minute), of the person that is 
using it and will be constantly monitored remotely using IoT so the data could be seen in a web server using remoteit.io.

The project consist in three parts:
  - the fall detection
  - the sensor reading
  - the streaming and data visualization
  
 ### The Fall Detection Part
 This first part was made using `mediapipe` for computer vision to get the figure of the human body and get the joints so then can
 choose a reference to make the comparation between frames, get an acceleration by position of the reference and define if there
 is a fall or not to send the notification by e-mail with `smtplib`.
 
 ### The Sensor Reading Part
 This second part consist in take the data of the sensors from an Arduino (with the program previously loaded) to the Raspberry Pi.
 This was made using serial communication (UART).
 
 ### The Streaming and Data Visualization
 Now comes the IoT part, for this I used `remoteit.io` to host the streaming and data visualization made it with Flask and HTML.
 
 
