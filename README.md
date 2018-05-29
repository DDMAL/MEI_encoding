# JSOMR2MEI
Conversion from jsomr, a json like format containing pitches and CC information, into MEI as a job in the workflow builder [```Rodan```](https://github.com/DDMAL/Rodan)

## Installation
- Move this directory into the rodan jobs folder
- If it does not already exist, create a python file called `settings.py` in the rodan folder like so: `rodan_docker/rodan/code/rodan/rodan/settings.py`
- Copy and paste the contents of `settings.py.development` into `settings.py`
- Include the path to this folder in the Rodan Job Package registration in the settings.py file. This should look something like the following
``` python
RODAN_JOB_PACKAGES = (
  "rodan.jobs.JSOMR2MEI",
  # Paths to other jobs
)
```
- In `docker-compose.job-dev.yml`, add the following reference to volumes like so
``` python
    volumes:
     - ./jobs/JSOMR2MEI:/code/rodan/rodan/jobs/JSOMR2MEI
     - ./jobs/settings.py:/code/rodan/rodan/settings.py
```

## Running Rodan
- Follow the [rodan-docker guide](https://github.com/DDMAL/rodan-docker/blob/master/README.md) to have docker set up.
- Once the above installation steps are complete, run ```docker-compose -f docker-compose.yml -f docker-compose.rodan-dev.yml up``` 
