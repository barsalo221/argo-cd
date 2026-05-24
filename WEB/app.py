from flask import Flask, render_template, request, redirect, url_for
import os
from pymongo import MongoClient

app = Flask(__name__)

MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017/")

client = MongoClient(MONGO_URI)
db = client["my_cars"] 
cars_collection = db["cars"] 



@app.route('/')
def home():
    all_cars = list(cars_collection.find())
    return render_template('index.html', cars=all_cars)

@app.route('/add-car', methods=['GET', 'POST'])
def add_car():
    if request.method == 'POST':
        brand = request.form.get('brand')
        model = request.form.get('model')
        year = request.form.get('year')
        color = request.form.get('color')
        
        new_car = {
            "brand": brand,
            "model": model,
            "year": int(year),
            "color": color
        }
        cars_collection.insert_one(new_car)
        return redirect(url_for('home'))
    
    return render_template('addcar.html')


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000, threaded=True, use_reloader=False)