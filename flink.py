import requests
from datetime import datetime

def _get_cep_job_id(address):
    r = requests.get('{}/jobs'.format(address))
    response = r.json()
    return response['jobs'][0]['id']

def save_flink_overall_metrics(address, execution_number, application):
    job_id = _get_cep_job_id(address)
    requests.get('{}/jobs/{}'.format(address, job_id))
    r = requests.get('{}/jobs/{}'.format(address, job_id))
    response = r.text
    file = open('./results/flink/flink-execution-{}-workload-{}-{}.json'.format(execution_number, application, datetime.now()).replace(" ", ""), "w")
    file.write(response)
    file.close()
    return r.json()