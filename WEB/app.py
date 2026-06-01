from flask import Flask, render_template, request, redirect, url_for
import os
from pymongo import MongoClient
from pymongo.errors import PyMongoError

app = Flask(__name__)

mongo_uri_file = os.environ.get('MONGO_URI_FILE')

if mongo_uri_file and os.path.exists(mongo_uri_file):
    with open(mongo_uri_file, 'r') as f:
        mongo_uri = f.read().strip()
else:
    mongo_uri = os.environ.get('MONGO_URI', 'mongodb://localhost:27017/my_cars')


@app.route('/')
def home():
    try:
        all_cars = list(cars_collection.find())
        return render_template('index.html', cars=all_cars)
    except PyMongoError as e:
        app.logger.error(f"MongoDB error: {e}")
        return render_template('index.html', cars=[], error="Database temporarily unavailable"), 503

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

@app.route('/health')
def health():
    return {'status': 'ok'}, 200


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000, threaded=True, use_reloader=False)