from flask import Flask, render_template, request, redirect, url_for
import os
from pymongo import MongoClient
from pymongo.errors import PyMongoError, OperationFailure

app = Flask(__name__)

MONGO_URI_FILE = os.environ.get("MONGO_URI_FILE", "/vault/secrets/mongo-credentials")

_mongo_client = None

def get_mongo_client():
    
    global _mongo_client
    
    if os.path.exists(MONGO_URI_FILE):
        try:
            with open(MONGO_URI_FILE, 'r') as f:
                mongo_uri = f.read().strip()
        except IOError as e:
            app.logger.error(f"Failed to read Vault secret file: {e}")
            mongo_uri = os.environ.get("MONGO_URI", "mongodb://localhost:27017/")
    else:
        mongo_uri = os.environ.get("MONGO_URI", "mongodb://localhost:27017/")

    if _mongo_client is None:
        app.logger.info("Creating a new MongoDB client instance...")
        _mongo_client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
        return _mongo_client

    try:
        _mongo_client.admin.command('ping')
        return _mongo_client
    except (OperationFailure, PyMongoError) as e:
        app.logger.warning(f"MongoDB connection stale or auth failed ({e}). Re-reading Vault secret...")
        try:
            _mongo_client.close()
        except Exception:
            pass
        
        _mongo_client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
        return _mongo_client

def get_db_collection():
    client = get_mongo_client()
    db = client["my_cars"]
    return db["cars"]


@app.route('/')
def home():
    try:
        cars_collection = get_db_collection()
        all_cars = list(cars_collection.find())
        return render_template('index.html', cars=all_cars)
    except PyMongoError as e:
        app.logger.error(f"MongoDB error in home route: {e}")
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
        try:
            cars_collection = get_db_collection()
            cars_collection.insert_one(new_car)
            return redirect(url_for('home'))
        except PyMongoError as e:
            app.logger.error(f"MongoDB error in add-car route: {e}")
            return render_template('addcar.html', error="Failed to save car to database"), 503
    
    return render_template('addcar.html')

@app.route('/health')
def health():
    # ה-Health Check הוא המקום המושלם לוודא שגם החיבור ל-DB בריא ורענן
    try:
        client = get_mongo_client()
        client.admin.command('ping')
        return {'status': 'ok', 'database': 'connected'}, 200
    except Exception as e:
        app.logger.error(f"Health check failed: {e}")
        return {'status': 'unhealthy', 'reason': str(e)}, 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000, threaded=True, use_reloader=False)