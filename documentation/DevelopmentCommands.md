# Running the application

General commands for flask
```
flask run
flask run --host==0.0.0.0                           # host in on your lan
nohup flask run --host=0.0.0.0 > flask.log 2>&1 &   # background launch
tail -n 50 -f flask.log                             # read the logs
```

```
pip install -e .
pip install -e "[.dev]"
```

Flask helpers
```
flask init-db
flask status
flask start-dev 
flask start-prod
flask log-summary 
flask --help
```

Makefile 
```
make install
make fix
make format
make lint
make security
make --help
```

Database Migrations
```
# after flask init-db

flask db current
flask db history

# Generate a new migration script 
flask db migrate -m "Message about migration"

# Generate an empty migration script
flask db revision -m "Message about revision"

# Revise the script, check if it seems ok
flask db upgrade
flask db downgrade
```

SQLite3
```
sqlite3 
.open filename.db
.databases
.table
.schema [table]
.indices [table]
CREATE TABLE ...
```


# Rerunning individual upload jobs
Once you create a session with the application, an upload_samples.ini file is created.
This file is created in a way which makes it possible to be rerun individually without the need of Flask.

Prerequisites:
- upload_samples.ini
- launcher shell script 
  - md5_upload_sc.sh
  - bulk_md5.sh

The launcher shell scripts can be found under
`geo_uploader/utils/upload_scripts/run_python_with_config.py` 

Here are the total commands to be ran  
- `./md5_upload_sc.sh "-c upload_samples.ini -o md5sheet.tsv"` 
- `./bulk_md5.sh "-c upload_samples.ini -o md5sheet.tsv --notify"` 
- `./single_cell_upload.sh "-c upload_samples.ini -o md5sheet.tsv --upload --notify-md5 --notify-upload"` 
