from flask import Flask
from flask import render_template, make_response
from flask import Response
import cv2
import time
from matplotlib import image
import mediapipe as mp

import smtplib
from decouple import config
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

import serial
import json

spo2 = "0"
bpm = "0"
ecg = "0"
'''
if __name__ == '__main__':
    ser = serial.Serial('/dev/ttyACM0', 115200, timeout=1)
    ser.flush()
'''
ser=serial.Serial()
ser.port = 'COM3'
ser.baudrate= 115200
ser.open()

mp_drawing = mp.solutions.drawing_utils
mp_pose = mp.solutions.pose

cap = cv2.VideoCapture(0)                 #use the camera

y1 = []
fall = []

time.sleep(1) #delay to start

image = []
results = []

app = Flask(__name__)

def send_mail():
     global image
     global results
       # Render detections
     mp_drawing.draw_landmarks(image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS,
                    mp_drawing.DrawingSpec(color=(245,117,66), thickness=2, circle_radius=2), 
                    mp_drawing.DrawingSpec(color=(245,66,230), thickness=2, circle_radius=2) 
                    )  
    
     cv2.imwrite('last_fall.jpg',image)     #saves the the fall frame in an image 
     
     email_user = config('MY_EMAIL')        #set the user email
     email_password = config('MY_PASSWORD') #set the password
     email_send = config('RECEIVER_MAIL')   #set the receiver email
     
     subject = 'Detected Fall Alert'        #subject of the email
     
     msg = MIMEMultipart()                  #set the data for the email
     msg['From'] = email_user
     msg['To'] = email_send
     msg['Subject'] = subject
     
     body = 'A fall has been detected.'   
     msg.attach(MIMEText(body,'plain'))
     
     filename= 'last_fall.jpg'             #select a file to send in the email
     attachment  =open(filename,'rb')
     
     part = MIMEBase('application','octet-stream') #set parameters to the email
     part.set_payload((attachment).read())
     encoders.encode_base64(part)
     part.add_header('Content-Disposition',"attachment; filename= "+filename)
     
     msg.attach(part)
     text = msg.as_string()
     server = smtplib.SMTP('smtp.gmail.com',587)  #use this as server
     server.starttls()
     server.login(email_user,email_password)      #log in to the gmail account to send the content 
     
     
     server.sendmail(email_user,email_send,text)  #send the email
     server.quit()                                #finish the session 
     
     print("Correo enviado")

def generate():
     global image
     global results
     with mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5) as pose:
          while cap.isOpened():
               ret, frame = cap.read()
               
               # Recolor image to RGB
               image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
               image.flags.writeable = False
               
               # Make detection
               results = pose.process(image)
          
               # Recolor back to BGR
               image.flags.writeable = True
               image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
               
               # Extract landmarks
               try:
                    landmarks = results.pose_landmarks.landmark
                    
                    # Get coordinates
                    nose_1 = [landmarks[mp_pose.PoseLandmark.NOSE.value].x,landmarks[mp_pose.PoseLandmark.NOSE.value].y]
                    
                    y1.append(nose_1[1])             #append the y coordinate of nose to 'y1' array
                    fall.append(0)                   #append a zero to the fall array
                    
                    if ((nose_1[1] - y1[-2])>0.25):  #if acceleration going down of the nose is bigger than 0.25 then
                         print("fall detected")       #print 'fall detected and append a one to the fall array
                         fall.append(1)
                         #print(fall)
                    
                    if fall[-1]==0 and fall[-2]==0 and fall[-3]==0 and fall[-4]==1: #filter to not send a lot of mails in at once
                         send_mail()                  #goes to the send_mail function     
                    
               except:
                    pass
               
               
               # Render detections
               mp_drawing.draw_landmarks(image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS,
                                        mp_drawing.DrawingSpec(color=(245,117,66), thickness=2, circle_radius=2), 
                                        mp_drawing.DrawingSpec(color=(245,66,230), thickness=2, circle_radius=2) 
                                        )               
               
               #grayscale = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) #change the video to grayscale
               #cv2.imshow('Fall Detection', grayscale)    #show the grayscale video at real time 

               #if cv2.waitKey(10) & 0xFF == ord('q'): #press 'q' if you want to end the program
               #     break

               frame = image
               
               (flag, encodedImage) = cv2.imencode(".jpg", frame)
               if not flag:
                    continue
               yield(b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' +
                    bytearray(encodedImage) + b'\r\n')
               
               if ser.in_waiting > 0:
                    line = ser.readline().decode('utf-8').rstrip()
                    line = line.split(' - ')
                    
                    global spo2, bpm, ecg
                    spo2 = int(line[0])
                    bpm = int(line[1])
                    ecg = int(line[2])

                    #print(spo2, bpm, ecg)
               
'''
               (flag2, encodedData) = cv2.imencode(".json", spo2)
               if not flag2:
                    continue
               yield(b'--spo2\r\n' b'Content-Type: image/json\r\n\r\n' +
                    bytearray(encodedData) + b'\r\n')'''
                                                          

@app.route("/")
def index():
     return render_template('index.html')
     
@app.route("/video_feed")
def video_feed():
     return Response(generate(),
          mimetype = "multipart/x-mixed-replace; boundary=frame")

@app.route('/data', methods=["GET", "POST"])
def data():
     global spo2, bpm, ecg
     data = [time.time()*1000, spo2, bpm, ecg]
     print(data)

     response = make_response(json.dumps(data))

     response.content_type = 'application/json'

     return response

if __name__ == "__main__":
     app.run(debug=False)

cap.release()