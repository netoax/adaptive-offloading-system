import requests
from datetime import datetime
from time import sleep

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

def get_mean_latency_from_job(address):
    job_id = _get_cep_job_id(address)
    r = requests.get('{}/jobs/{}/metrics'.format(address, job_id))
    sleep(5)
    r = requests.get('{}/jobs/{}/metrics'.format(address, job_id))
    response = r.json()
    latency_mean = ""
    for metric in response:
        if metric['id'].endswith("index.0.latency_mean"):
            latency_mean = metric['id']

    r = requests.get('{}/jobs/{}/metrics?get={}'.format(address, job_id, latency_mean))
    r = requests.get('{}/jobs/{}/metrics?get={}'.format(address, job_id, latency_mean))
    values = r.json()
    if len(values) > 0:
        return values[0]['value']

    return 0.0
