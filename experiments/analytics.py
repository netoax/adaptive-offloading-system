# The first example demonstrates how to evaluate one model
from skmultiflow.data import SEAGenerator
from skmultiflow.trees import HoeffdingTreeClassifier
from skmultiflow.trees import ExtremelyFastDecisionTreeClassifier
from skmultiflow.lazy import KNNClassifier
from skmultiflow.bayes import NaiveBayes

from skmultiflow.evaluation import EvaluatePrequential
from skmultiflow.data import DataStream
from matplotlib import pyplot as plt

from analytics.models.metric import Measurement
import pandas as pd

DATASET_COLUMNS = ['bandwidth', 'cpu', 'cepLatency', 'memory', 'violated']
MODEL_NAMES = ['HT', 'EFDT', 'NB', 'KNN']
METRICS = ['accuracy', 'kappa', 'precision', 'recall', 'f1']

ATTACK_MACHINES = ['192.168.100.149', '192.168.100.148','192.168.100.147','192.168.100.150']

ht = HoeffdingTreeClassifier()
efdt = ExtremelyFastDecisionTreeClassifier()
nb = NaiveBayes()
knn = KNNClassifier()

models = [ht, efdt, nb, knn]

MAP_METRICS = {
    "accuracy": ['mean_acc_[HT]', 'mean_acc_[EFDT]', 'mean_acc_[NB]', 'mean_acc_[KNN]'],
    "precision": ['mean_precision_[HT]', 'mean_precision_[EFDT]', 'mean_precision_[NB]', 'mean_precision_[KNN]'],
    "recall": ['mean_recall_[HT]', 'mean_recall_[EFDT]', 'mean_recall_[NB]', 'mean_recall_[KNN]'],
    "f1": ['mean_f1_[HT]', 'mean_f1_[EFDT]', 'mean_f1_[NB]', 'mean_f1_[KNN]'],
    "kappa": ['mean_kappa_[HT]', 'mean_kappa_[EFDT]', 'mean_kappa_[NB]', 'mean_kappa_[KNN]']
}

def _is_data_normal():
    return true

def get_metric_name(name):
    return name[name.find("[")+1:name.find("]")]

def generate_evaluation_charts(metric, output):
    columns = ['id'] + MAP_METRICS[metric]
    data = pd.read_csv('./results/ml/ml.csv', skiprows=8, usecols=columns)
    id = data['id']
    fig, ax = plt.subplots()

    for m in MAP_METRICS[metric]:
        model_metric = data[m]
        ax.plot(id, model_metric, label=get_metric_name(m))
        ax.legend()

    ax.grid(True)
    plt.title("{}".format(metric))
    plt.xlabel("number of instances")
    plt.ylabel(metric)
    plt.savefig('{}/{}.eps'.format(output, metric), format='eps') # TODO: improve quality

def clear_df(df):
    df = df.dropna()
    df = df.dropna(subset=['sport', 'dport'])
    df = df[df['sport'] != '0x0303']
    df = df[df['sport'] != '0x0303']
    df = df[df['dport'] != '0x5000']
    df = df[df['dport'] != '0xe292']
    df = df[df['proto'] != 'icmp']
    return df

def filter_by_attacker(df, attacker):
    return df[df['saddr'] == attacker]

def map_df_to_json(row):
    return {
        "timestamp": row['stime'],
        "protocol": row['proto'],
        "sourceAddr": row['saddr'],
        "sourcePort": row['sport'],
        "destAddr": row['daddr'],
        "destPort": row['dport'],
        "bytes": row['bytes'],
        "state": row['state'],
    }

def prepare_dataset():
    reader = pd.read_csv(
        './test.csv',
        usecols=['stime', 'proto', 'saddr', 'sport', 'daddr', 'dport', 'bytes', 'state'],
        dtype={'stime': float, 'proto': str, 'saddr': str, 'daddr': str, 'bytes': int, 'state': str},
        nrows=int(1000000),
        chunksize=100000,
    )

    for chunk in reader:
        filtered.to_csv('./dataset_with_header.csv'.format(attacker), mode='a', header=False)

def prepare_dataset_2():
    fout=open("file_with_header.csv","a")
    for line in open("header.csv"):
        fout.write(line)
        fout.write('\n')
    fout.close()

    reader = pd.read_csv(
        './dataset.csv',
        chunksize=100000,
    )

    for chunk in reader:
        chunk.to_csv('./file_with_header.csv', mode='a', header=False)


def evaluate_models(dataset_file, output_file):
    df = pd.read_csv(dataset_file, usecols=DATASET_COLUMNS)
    df = df.astype({'violated':int})
    stream = DataStream(df, n_targets=1, target_idx=-1)
    evaluator = EvaluatePrequential(max_samples=5000,
                                    max_time=1000,
                                    show_plot=False,
                                    output_file=output_file,
                                    metrics=METRICS)
    evaluator.evaluate(stream, model=models, model_names=MODEL_NAMES)

evaluate_models('./results/random_data_labeled.csv', './results/ml/ml.csv')
# generate_evaluation_charts('accuracy', './results/ml')
# generate_evaluation_charts('precision', './results/ml')
# generate_evaluation_charts('recall', './results/ml')
# generate_evaluation_charts('f1', './results/ml')
# generate_evaluation_charts('kappa', './results/ml')

# print('is data normal: ', _is_data_normal('./results/random_data_labeled.csv'))

# prepare_dataset()
# prepare_dataset_2()