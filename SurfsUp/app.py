# Import the dependencies.
import numpy as np
import pandas as pd
import datetime as dt
import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func
from sqlalchemy.sql import func, desc
from flask import Flask, jsonify
from flask import Flask, url_for

#################################################
# Database Setup
#################################################
#engine = create_engine("sqlite:///Resources/hawaii.sqlite")

engine = create_engine("sqlite:///SurfsUp/Resources/hawaii.sqlite")
# reflect an existing database into a new model
Base = automap_base()
Base.prepare(autoload_with=engine)

# Save references to each table
Measurements = Base.classes.measurement
Stations = Base.classes.station

# Create our session (link) from Python to the DB
session = Session(engine)

#################################################
# Flask Setup
#################################################
app = Flask(__name__)


#################################################
# Flask Routes
#################################################
# Homepage with list of available routes

@app.route("/")
def Welcome():
    return(
        f"Welcome!<br>"
        f"Available Routes:<br>"
        f"/api/v1.0/precipitation<br>"
        f"/api/v1.0/stations<br>"
        f"/api/v1.0/tobs<br>"
        f"/api/v1.0/start<br>"
        f"choose start date OR start and end dates - must be in format YYYY-MM-DD"
    )

# Convert the query results from your precipitation analysis 
# to a dictionary using date as the key and prcp as the value.

@app.route("/api/v1.0/precipitation")
def precip_api():
    last_date_query = session.query(func.max(Measurements.date)).scalar()
    last_date = pd.to_datetime(last_date_query)
    one_year_ago = last_date - pd.DateOffset(years=1)
    one_year_ago_str = one_year_ago.strftime('%Y-%m-%d')
    precip = session.query(Measurements.date, Measurements.prcp).\
    filter(Measurements.date >= one_year_ago_str).all()
    precip_data = {date:prcp for date, prcp in precip}
    session.close()
    return jsonify(precip_data)

# Return a JSON list of stations from the dataset.

@app.route("/api/v1.0/stations")
def stations_api():
    list_stations = session.query(Measurements.station).distinct().all()
    list_station_ids = [station[0].strip(",") for station in list_stations]
    session.close()
    return jsonify(list_station_ids)

# Query the dates and temperature observations of the 
# most-active station for the previous year of data.

@app.route("/api/v1.0/tobs")
def tobs_api():
    most_active_station_id = session.query(Measurements.station, 
        func.count().label('count')).group_by(Measurements.station).order_by(func.count().desc()).first()[0]
    last_date_query = session.query(func.max(Measurements.date)).scalar()
    last_date = pd.to_datetime(last_date_query)
    one_year_ago = last_date - pd.DateOffset(years=1)
    one_year_ago_str = one_year_ago.strftime('%Y-%m-%d')
    temp_date = session.query(Measurements.date, Measurements.tobs).\
    filter(Measurements.date >= one_year_ago_str).all()
    results_data = {date:tobs for date, tobs in temp_date}
    session.close()
    return jsonify(results_data)

# Start route accepts the start date as a parameter from the URL
# Start/End route accepts the start and end dates as parameters from the URL

@app.route("/api.v1.0/start/<start>")
@app.route("/api.v1.0/start/<start>/<end>")
def start_api(start=None, end=None):

    sel = [func.min(Measurements.tobs).label('TMIN'), 
        func.max(Measurements.tobs).label('TAVG'), 
        func.avg(Measurements.tobs).label('TMAX')
    ]

    if not end:
        start_query = session.query(*sel).filter(Measurements.date >= start).all()
        session.close()
        start_data = list(np.ravel(start_query))
        return jsonify(start_data)
    
    start_query = session.query(*sel).filter(Measurements.date >= start).filter(Measurements.date <= end).all()
    session.close()
    start_data = list(np.ravel(start_query))
    return jsonify(start_data)
    

if __name__ == '__main__':
    app.run(debug=True)

