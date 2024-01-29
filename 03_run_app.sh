#!/bin/bash

export FLASK_APP=flask_app/app.py
flask run -p 5001 -h 0.0.0.0
