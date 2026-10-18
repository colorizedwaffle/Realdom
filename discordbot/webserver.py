from flask import Flask
from threading import Thread
#render needs a web server for some reason

app=Flask('')
@app.route('/')
def home():
 return "Works"

def run(): #pings the server
 app.run(host="0.0.0.0",port=8080)

def keepalive(): #pings the server
 t=Thread(target=run)
 t.start()
