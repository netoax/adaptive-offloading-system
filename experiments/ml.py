import pandas as pd
from datetime import datetime
import glob
import scipy.stats as st
import scikit_posthocs as sp
import numpy as np

from skmultiflow.evaluation import EvaluatePrequential, EvaluateHoldout
from skmultiflow.data import DataStream

from skmultiflow.trees import HoeffdingTreeClassifier
from skmultiflow.trees import ExtremelyFastDecisionTreeClassifier
from skmultiflow.lazy import KNNClassifier
from skmultiflow.bayes import NaiveBayes


from experiments.constants import *

from analytics.init_logger import init_logger
from analytics.models.metric import Measurement
from analytics.policy_manager import PolicyManager
from analytics.network.mqtt import MQTT
from analytics.network.publisher import MessagePublisher


ht = HoeffdingTreeClassifier()
efdt = ExtremelyFastDecisionTreeClassifier()
nb = NaiveBayes()
knn = KNNClassifier(n_neighbors=5)

models = [ht, efdt, nb, knn]

def group_all_profiling_data(directory, pattern, output_dir):
    header = ["bandwidth", "cepLatency", "cpu", "memory", "rtt", "timestamp"]
    # all_filenames = [i for i in glob.glob(f"{directory}/{pattern}")]
    all_filenames = [
        '/Users/jneto/drive/experimentos/policy/csv-files/combined_csv.csv',
        '/Users/jneto/drive/experimentos/online-learning/csv-files/combined_csv.csv',
        '/Users/jneto/drive/experimentos/concept-drift/csv-files/combined_csv.csv'
    ]
    combined_csv = pd.concat([pd.read_csv(f) for f in all_filenames])
    combined_csv.to_csv(f"/Users/jneto/drive/experimentos/general_combined_csv.csv", index=False, header=header)

def label_dataset_columns(policy_manager, dataset_file):
    df = pd.read_csv(dataset_file)
    for index, row in df.iterrows():
        measurement = Measurement(row['cepLatency'], row['cpu'], row['memory'], row['bandwidth'])
        violated = policy_manager.is_policy_violated(measurement.to_dict())
        df.loc[index, 'violated'] = int(violated)
    df.to_csv('./random_data_labeled.csv', index=False)

def calculate_wilcoxon_signed_rank():
    pass

# Mean performance:
# HT - Accuracy     : 0.9984
# HT - Kappa        : 0.9963
# HT - Precision: 0.9977
# HT - Recall: 0.9970
# HT - F1 score: 0.9974
# EFDT - Accuracy     : 0.9979
# EFDT - Kappa        : 0.9950
# EFDT - Precision: 0.9985
# EFDT - Recall: 0.9945
# EFDT - F1 score: 0.9965
# NB - Accuracy     : 0.9709
# NB - Kappa        : 0.9311
# NB - Precision: 0.9320
# NB - Recall: 0.9729
# NB - F1 score: 0.9520
# KNN - Accuracy     : 0.9343
# KNN - Kappa        : 0.8477
# KNN - Precision: 0.8493
# KNN - Recall: 0.9467
# KNN - F1 score: 0.8954

def calculate_friedman_test(dataset_file):
    models = ["HT", "EFDT", "KNN", "NB"]

    # get_model_columns("HT")

    # columns = [*MAP_METRICS['accuracy'], *MAP_METRICS['recall'], *MAP_METRICS['precision'], *MAP_METRICS['f1'], *MAP_METRICS['kappa']]
    # data = pd.read_csv(dataset_file, skiprows=8, usecols=columns)

    ht = [0.9984, 0.9963, 0.9977, 0.9970, 0.9974]
    vfdt = [0.9979, 0.9950, 0.9985, 0.9945, 0.9965]
    nb = [0.9709, 0.9311, 0.9320, 0.9729, 0.9520]
    knn = [0.9343, 0.8477, 0.8493, 0.9467, 0.8954]

    # for model in models:
    #     df = pd.read_csv(dataset_file, skiprows=8, usecols=get_model_columns(model))
    #     print(df.values)
    #     data.append([df.values])

    # for key in MAP_METRICS:
    #     if key != 'true_vs_predicted':
    #         df = pd.read_csv(dataset_file, skiprows=8, usecols=MAP_METRICS[key])
    #         # data = data.drop(['true_vs_predicted', 'id', 'true_value'], axis=1)
    #         print(df.values)

    stat, p = st.friedmanchisquare(ht, vfdt, nb, knn)
    print('Statistics=%.3f, p=%.3f' % (stat, p))
    # interpret
    alpha = 0.05
    if p > alpha:
        print('Same distributions (fail to reject H0)')
    else:
        print('Different distributions (reject H0)')

    data = np.array([ht, vfdt, nb, knn])
    a = sp.posthoc_nemenyi_friedman(data.T)
    print(a)

def undersample_data(df):
    class_2,class_1 = df.violated.value_counts()
    c2 = df[df['violated'] == 0.0]
    c1 = df[df['violated'] == 1.0]
    df_2 = c2.sample(class_1)
    return pd.concat([df_2,c1],axis=0)


def evaluate_models(dataset_file, output_file):
    df = pd.read_csv(dataset_file, usecols=DATASET_COLUMNS)
    # print(df.head())
    # print(df.info())
    df = df.drop(df[df.cepLatency == 0].index)
    # print(df.head())
    # print(df.info())

    # df = undersample_data(df)

    print(df.info())

    print(df['violated'].value_counts())

    df = df.astype({'violated':int})
    stream = DataStream(df, n_targets=1, target_idx=-1)

    for i in range(5):
        print(f'Running model evaluation, execution={i}')
        now = datetime.now()

        ht = HoeffdingTreeClassifier()
        efdt = ExtremelyFastDecisionTreeClassifier()
        nb = NaiveBayes()
        knn = KNNClassifier(n_neighbors=5)

        evaluator = EvaluatePrequential(max_samples=28000,
                                        show_plot=False,
                                        output_file=f'./model-results/{i}:{now}.txt',
                                        metrics=METRICS,
                                        n_wait=1,
                                        pretrain_size=200,
                                        restart_stream=True)
        evaluator.evaluate(stream, model=[ht, efdt, nb, knn], model_names=MODEL_NAMES)


evaluate_models('./random_data_labeled.csv', './evaluation_results.csv')
# calculate_friedman_test('')

# TBD: correlação entre valores, remoção de NaN, etc

# group_all_profiling_data('/Users/jneto/drive/experimentos/concept-drift/csv-files', 'profiler-edge*.csv')
# group_all_profiling_data('./', 'profiler-edge*.csv', '')

# logger = init_logger(__name__, testing_mode=False)

# mqtt = MQTT(hostname="localhost", port=1883)
# mqtt.start()
# publisher = MessagePublisher(mqtt)

# policy_manager = PolicyManager('./analytics/policies.xml', logger, publisher)
# policy_manager.process()
# label_dataset_columns(policy_manager, '~/drive/experimentos/general/combined_csv.csv')