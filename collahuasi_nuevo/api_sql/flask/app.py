from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import text

from config import SQLALCHEMY_DATABASE_URI
from models import db, Inventario, Latencia

# Create the Flask application
app = Flask(__name__)

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI']           = SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS']    = False

# Initialize SQLAlchemy with the app
db.init_app(app)

##  - - - - - - - - - - - ENDPOINTS - - - - - - - - - - - - 
# > > > Default page to test database connection
@app.route('/')
def default_page():
    try:
        db.session.execute(text('SELECT 1'))
        return jsonify({"message": "Successfully connected to the MariaDB database"}), 200
    except Exception as e:
        return jsonify({"message": "Failed to connect to the database", "error": str(e)}), 500


# > > > Endpoints para Inventario
@app.route('/inventario', methods=['GET'])
def get_all_inventario():
    try:
        inventario_records = Inventario.query.all()
        return jsonify([record.to_dict() for record in inventario_records]), 200
    except Exception as e:
        return jsonify({"message": "Error fetching data", "error": str(e)}), 500


@app.route('/inventario/id/<int:id>', methods=['GET'])
def get_inventario_by_id(id):
    try:
        # Use `filter_by` to query based on `id`
        record = Inventario.query.filter_by(id=id).first()

        if not record:
            return jsonify({"message": f"No record found with id {id}"}), 404

        return jsonify(record.to_dict()), 200
    except Exception as e:
        return jsonify({"message": "Error fetching record", "error": str(e)}), 500


@app.route('/inventario/marca/<string:marca>', methods=['GET'])
def get_inventario_by_marca(marca):
    try:
        # Query all records where "marca" matches the input
        records = Inventario.query.filter(Inventario.marca == marca).all()

        if not records:
            return jsonify({"message": f"No records found with marca '{marca}'"}), 404

        # Convert each record to a dictionary
        records_list = [record.to_dict() for record in records]

        return jsonify(records_list), 200
    
    except Exception as e:
        return jsonify({"message": "Error fetching record", "error": str(e)}), 500


# > > > Endpoints para Latencia
@app.route('/latencia', methods=['POST'])
def insert_new_latencia():
    try:
        # Get JSON data from the request
        data = request.json
        #print(data)

        # Validate that the data is a list
        if not isinstance(data, list):
            return jsonify({"message": "Invalid data format. Expected an array of objects."}), 400

        # Validate required fields in each object
        for record in data:
            if not all(key in record for key in ['ip', 'latencia', 'fecha']):
                return jsonify({"message": f"Missing required fields in record: {record}"}), 400

        # Create Latencia objects for each record
        new_latencias = [
            Latencia(
                ip=record['ip'],
                latencia=record['latencia'],
                fecha=record['fecha']
            )
            for record in data
        ]

        # Add all objects to session and commit in bulk
        db.session.add_all(new_latencias)
        db.session.commit()

        # Return success message with the count of inserted records
        return jsonify({"message": f"{len(new_latencias)} records added successfully"}), 201
    
    except Exception as e:
        return jsonify({"message": "Error creating record", "error": str(e)}), 500


# Run the Flask app
if __name__ == '__main__':
    app.run(host='192.168.2.223', port=5000, debug=False)
