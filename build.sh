#!/bin/bash
pipenv run jupyter nbconvert --to python --template python_clean gcal_csv_generator.ipynb
