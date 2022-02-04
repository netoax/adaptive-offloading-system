# The first example demonstrates how to evaluate one model
from skmultiflow.data import SEAGenerator
from skmultiflow.trees import HoeffdingTreeClassifier
from skmultiflow.trees import ExtremelyFastDecisionTreeClassifier
from skmultiflow.lazy import KNNClassifier
from skmultiflow.bayes import NaiveBayes

from skmultiflow.evaluation import EvaluatePrequential, EvaluateHoldout
from skmultiflow.data import DataStream
from matplotlib import pyplot as plt
import matplotlib.ticker as mtick
import matplotlib.dates as md
import pandas as pd
from datetime import datetime
from pathlib import Path
import glob
import json
import scipy.stats as st
import seaborn as sns

from analytics.init_logger import init_logger
from analytics.models.metric import Measurement
from analytics.policy_manager import PolicyManager
from analytics.network.mqtt import MQTT
from analytics.network.publisher import MessagePublisher

from experiments.constants import *
from statsmodels.stats.contingency_tables import mcnemar

from functools import reduce

ATTACK_MACHINES = ['192.168.100.149', '192.168.100.148','192.168.100.147','192.168.100.150']

ht = HoeffdingTreeClassifier()
efdt = ExtremelyFastDecisionTreeClassifier()
nb = NaiveBayes()
knn = KNNClassifier(n_neighbors=5)

models = [ht, efdt, nb, knn]

MAP_METRICS = {
    "accuracy": ['mean_acc_[HT]', 'mean_acc_[EFDT]', 'mean_acc_[NB]', 'mean_acc_[KNN]'],
    "precision": ['mean_precision_[HT]', 'mean_precision_[EFDT]', 'mean_precision_[NB]', 'mean_precision_[KNN]'],
    "recall": ['mean_recall_[HT]', 'mean_recall_[EFDT]', 'mean_recall_[NB]', 'mean_recall_[KNN]'],
    "f1": ['mean_f1_[HT]', 'mean_f1_[EFDT]', 'mean_f1_[NB]', 'mean_f1_[KNN]'],
    "kappa": ['mean_kappa_[HT]', 'mean_kappa_[EFDT]', 'mean_kappa_[NB]', 'mean_kappa_[KNN]'],
    "true_vs_predicted": ['true_value', 'predicted_value_[HT]', 'predicted_value_[EFDT]', 'predicted_value_[NB]', 'predicted_value_[KNN]']
}

MAP_MODELS = {
    "ht": "predicted_value_[HT]",
    "efdt": "predicted_value_[EFDT]",
    "nb": "predicted_value_[NB]",
    "knn": "predicted_value_[KNN]",
}

PAIRWISE_TEST = [
    ['ht', 'efdt'],
    ['ht', 'nb'],
    ['ht', 'knn'],
    ['efdt', 'nb'],
    ['efdt', 'knn'],
    ['nb', 'knn']
]

def _is_data_normal():
    return true

def get_metric_name(name):
    return name[name.find("[")+1:name.find("]")]

def generate_knn_chart():
    values = load_knn_k_data()
    new_list = [ round(x*100,2) for x in values]
    # print(values[:30])
    fig, ax = plt.subplots()
    ax.plot(range(1, 501), new_list[:500], label='Accuracy')
    # ax.yaxis.set_major_formatter(mtick.PercentFormatter(1))
    ax.yaxis.set_major_locator(plt.MaxNLocator(10))
    # ax.invert_yaxis()

    # plt.gca().yaxis.set_major_formatter(plt.FuncFormatter('{:.0f}%'.format))
    ax.grid(True)
    plt.title("Best k value for kNN classifier")
    plt.xlabel("Number of instances")
    plt.ylabel("Accuracy (%)")
    plt.savefig('knn_k_values.eps', format='eps') # TODO: improve quality

def load_knn_k_data():
    with open('./knn_k_accuracy_v2.txt') as file:
        lines = file.readlines()
        lines = [float(line.rstrip()) for line in lines]
        return lines

def get_average_value_evaluation(model):
    dfs = []

    # for key in MAP_METRICS:
    files = glob.glob('/Users/jneto/msc/workspace/adaptive-offloading-system/model-results/*')
    for file in files:
        # columns = MAP_METRICS[key]
        path = Path(file)
        print(path)
        # print(path)
        df = pd.read_csv(path, skiprows=8, index_col=False).drop(['id'], axis='columns')
        # print(df.head())
        dfs.append(df)

    # result = reduce(lambda x, y: pd.DataFrame.add(x, y, fill_value=0), dfs)
    # result = sum(dfs)
    # print(result[MAP_METRICS['accuracy']])
    # print(len(dfs))
    result_1 = pd.concat(dfs)

    # print(result_1.mean())

    # for key in MAP_METRICS

    result_1.to_csv('./combined_evaluation_v2.csv')

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

def label_dataset_columns(policy_manager, dataset_file):
    df = pd.read_csv(dataset_file)
    for index, row in df.iterrows():
        measurement = Measurement(row['cepLatency'], row['cpu'], row['memory'], row['bandwidth'])
        violated = policy_manager.is_policy_violated(measurement.to_dict())
        df.loc[index, 'violated'] = int(violated)
    df.to_csv('./random_data_labeled.csv', index=False)

def evaluate_models(dataset_file, output_file):
    df = pd.read_csv(dataset_file, usecols=DATASET_COLUMNS)
    df = df.astype({'violated':int})
    stream = DataStream(df, n_targets=1, target_idx=-1)

    for i in range(10):
        print(f'Running model evaluation, execution={i}')
        now = datetime.now()
        evaluator = EvaluatePrequential(max_samples=5000,
                                        max_time=1000,
                                        show_plot=False,
                                        output_file=f'./model-results/{i}:{now}.txt',
                                        metrics=METRICS,
                                        n_wait=1,
                                        restart_stream=True)
        evaluator.evaluate(stream, model=models, model_names=MODEL_NAMES)

def force_knn_warm(stream, k=5, samples=1000):
    knn = KNNClassifier(n_neighbors=k, max_window_size=2000, leaf_size=40)

    n_samples = 0
    corrects = 0

    while n_samples < samples:
        X, y = stream.next_sample()
        my_pred = knn.predict(X)
        if y[0] == my_pred[0]:
            corrects += 1
        knn = knn.partial_fit(X, y)
        n_samples += 1

    return knn

def evaluate_knn_k_value(dataset_file):
    df = pd.read_csv(dataset_file, usecols=DATASET_COLUMNS)
    df = df.astype({'violated':int})
    print(df.head())

    prequential = EvaluatePrequential(pretrain_size=100,
                                    max_samples=4000,
                                    show_plot=False,
                                    # metrics=['mean_square_error'],
                                    metrics=['accuracy'],
                                    n_wait=100,
                                    restart_stream=True)

    stream_2 = DataStream(df.tail(4000), n_targets=1, target_idx=-1)

    # prequential_1.evaluate(stream, model=[KNNClassifier(n_neighbors=1)], model_names=['knn'])

    # prequential_1.evaluate(stream_2, model=[knn], model_names=['knn'])


    for i in range(1,15):
        print(f'Running k-value experiment for kNN classifier with n={i}')
        stream = DataStream(df.head(1000), n_targets=1, target_idx=-1)
        knn = force_knn_warm(stream, k=i, samples=1000)
        # evaluator.evaluate(stream, model=[KNNClassifier(n_neighbors=i)], model_names=['knn'])
        prequential.evaluate(stream_2, model=[knn], model_names=['knn'])

def pairwise(data):
    return zip(data[::2], data[1::2])

def get_contingency_table(dataset_file):
    data = pd.read_csv(dataset_file, usecols=MAP_METRICS['true_vs_predicted'] + ['id'])
    # data = pd.read_csv(dataset_file, skiprows=8, usecols=MAP_METRICS['true_vs_predicted'] + ['id'])
    # print(data.head())

    print(data.head())

    for pair in PAIRWISE_TEST:
        print('\npairwise McNemar\'s test with: ', pair)
        model_1 = data[MAP_MODELS[pair[0]]] == data['true_value']
        model_2 = data[MAP_MODELS[pair[1]]] == data['true_value']

        # print(model_1, model_2)

        data_crosstab = pd.crosstab(model_1,
                                    model_2,
                                    margins = False)

        print(data_crosstab)

        result = mcnemar(data_crosstab, exact=True)
        # print(result)
        # summarize the finding
        print('statistic=%.3f, p-value=%.3f' % (result.statistic, result.pvalue))
        # interpret the p-value
        alpha = 0.05
        if result.pvalue > alpha:
            print('Same proportions of errors (fail to reject H0)')
        else:
            print('Different proportions of errors (reject H0)')

def get_model_columns(model):
    columns = []
    for key in MAP_METRICS:
        for value in MAP_METRICS[key]:
            if value.find(f'[{model}]') != -1:
                columns.append(value)
    return columns


logger = init_logger(__name__, testing_mode=False)

mqtt = MQTT(hostname="localhost", port=1883)
mqtt.start()
publisher = MessagePublisher(mqtt)

def _prepare_profiler_logs(type):
    files = glob.glob("{}/{}:profiler*.txt".format(RESULTS_PATH, type))
    data = []
    for file in files:
        p = Path(file)
        data = _get_profiler_logs(type, p.stem, data)

    _create_profiler_logs_file(type, data)

def get_perf_data(strategy, number, application, throughput):
    data = []
    # file = open('/Users/jneto/drive/experimentos/policy/ddos-128s/service-logs/28/ddos-128s/750/edge:profiler:28:2021-11-2323:39:56.795306.txt')

    if strategy == 'concept-drift':
        files = glob.glob(f'/Users/jneto/drive/experimentos/concept-drift/ddos-10s-128s/{number}/{application}/{throughput}/edge:profiler:*')
    else:
        print(strategy, number, application, throughput)
        path = f'/Users/jneto/drive/experimentos/{strategy}/{application}/service-logs/{number}/{application}/{throughput}/edge:profiler:*'
        print(path)
        files = glob.glob(path)

    for file in files:
        p = Path(file)
        file = open(p)
        next(file)
        for line in file:
            instance = json.loads(line)
            data.append(instance.values())

    return data

def matplot_perf_charts(x, y):
    fig, ax = plt.subplots()

    ax.plot(df_policy['timestamp'], df_policy['cpu'])
    ax.plot(df_ml['timestamp'], df_ml['cpu'])

    # ax.plot(range(1, 501), new_list[:500], label='Accuracy')
    # ax.yaxis.set_major_formatter(mtick.PercentFormatter(1))
    ax.yaxis.set_major_locator(plt.MaxNLocator(10))
    # ax.invert_yaxis()

    # plt.gca().yaxis.set_major_formatter(plt.FuncFormatter('{:.0f}%'.format))
    ax.grid(True)
    plt.title("Best k value for kNN classifier")
    plt.xlabel("Number of instances")
    plt.ylabel("Accuracy (%)")
    plt.show()

def list_of_timestamps():
    return (pd.DataFrame(columns=['NULL'],
                  index=pd.date_range('2021-11-25T12:00:00Z', '2021-11-25T12:31:00Z',
                                      freq='20S'))
    #    .between_time('07:00','21:00')
       .index.strftime('%H:%M:%S')
       .tolist()
    )

def seaborn_perf_charts(data1, data2, name_output):
    # prepare data
    timestamps = list_of_timestamps()

    d1 = data1.head(94)
    d1.loc[:,'timepoint'] = timestamps
    # d1.loc[:,'strategy'] = 'Policy-based'

    d2 = data2.head(94)
    d2.loc[:,'timepoint'] = timestamps
    # d2.loc[:,'strategy'] = 'ML-enhanced'

    data = d1.append(d2)
    data.reset_index(inplace=True)
    print(data.info())


    data['timepoint'] = pd.to_datetime(data['timepoint'], format = '%H:%M:%S')

    fig = plt.figure()
    fmri = sns.load_dataset("fmri")
    sns.set_theme(style="whitegrid")
    fig.ax = sns.lineplot(
        data=data,
        x="timepoint", y="cpu", hue="strategy",
        markers=True, dashes=False
    )
    fig.ax.yaxis.grid(True)

    plt.ylabel("CPU Usage (%)")
    plt.xlabel("Timestamp")

    # specify the position of the major ticks at the beginning of the week
    # plt.ax.xaxis.set_major_locator(md.WeekdayLocator(byweekday = 1))
    # specify the format of the labels as 'year-month-day'
    fig.ax.xaxis.set_major_formatter(md.DateFormatter('%H:%M:%S'))
    # (optional) rotate by 90° the labels in order to improve their spacing
    # plt.setp(fig.ax.xaxis.get_majorticklabels(), rotation = 90)

    # fig.ax.tick_params(axis = 'x', which = 'major', length = 10)
    fig.ax.tick_params(axis = 'x', which = 'minor', length = 1)

    plt.savefig(name_output, format='eps')
    # plt.show()

def generate_perf_chats(strategy, number, application, throughput):
    # values = load_knn_k_data()
    # df = pd.read_csv('/drive/experimentos/policy/csv-files/profiler-edge-ddos-128s-750.csv', skiprows=8, index_col=False).drop(['id'], axis='columns')
    # new_list = [ round(x*100,2) for x in values]
    # print(values[:30])

    policy = get_perf_data('policy', number, application, throughput)
    df_policy = pd.DataFrame.from_records(policy, columns=["bandwidth", "cepLatency", "cpu", "memory", "rtt", "timestamp"])
    df_policy.loc[:,'strategy'] = 'Policy-based'

    if strategy == 'ml':
        online_learning = get_perf_data('online-learning', number, application, throughput)
        df_ml = pd.DataFrame.from_records(online_learning, columns=["bandwidth", "cepLatency", "cpu", "memory", "rtt", "timestamp"])
        df_ml.loc[:,'strategy'] = 'ML-enhanced'
        seaborn_perf_charts(df_policy, df_ml, f'{strategy}-{number}-{application}-{throughput}.eps')
        return

    online_learning = get_perf_data('concept-drift', number, application, throughput)
    df_ml = pd.DataFrame.from_records(online_learning, columns=["bandwidth", "cepLatency", "cpu", "memory", "rtt", "timestamp"])
    df_ml.loc[:,'strategy'] = 'Drift-enhanced'
    seaborn_perf_charts(df_policy, df_ml, f'{strategy}-{number}-{application}-{throughput}.eps')

    # plt.savefig('knn_k_values.eps', format='eps') # TODO: improve quality

# policy_manager = PolicyManager('./analytics/policies.xml', logger, publisher)
# policy_manager.process()
# label_dataset_columns(policy_manager, '~/drive/experimentos/policy/csv-files/combined_csv.csv')

# generate_perf_chats('26', 'concept-drift')

number = 29

# generate_perf_chats('ml', number, 'ddos-128s', '250')
# generate_perf_chats('ml', number, 'ddos-128s', '500')
# generate_perf_chats('ml', number, 'ddos-128s', '750')
# generate_perf_chats('ml', number, 'ddos-10s', '250')
# generate_perf_chats('ml', 9, 'ddos-10s', '500')
# generate_perf_chats('ml', number, 'ddos-10s', '750')

# generate_perf_chats('concept-drift', number, 'ddos-128s', '250')
# generate_perf_chats('concept-drift', number, 'ddos-128s', '500')
# generate_perf_chats('concept-drift', number, 'ddos-128s', '750')
# generate_perf_chats('concept-drift', number, 'ddos-10s', '250')
# generate_perf_chats('concept-drift', 9, 'ddos-10s', '500')
# generate_perf_chats('concept-drift', number, 'ddos-10s', '750')


# get_perf_data()

# generate_knn_chart()
# evaluate_models('./random_data_labeled.csv', './evaluation_results.csv')
# get_average_value_evaluation('ht')
# evaluate_knn_k_value('./random_data_labeled.csv')
# get_contingency_table('./last_model_result_v2.csv')
# get_contingency_table('./evaluation_results.csv')
# calculate_friedman_test('./evaluation_results.csv')
# generate_evaluation_charts('accuracy', './results/ml')
# generate_evaluation_charts('precision', './results/ml')
# generate_evaluation_charts('recall', './results/ml')
# generate_evaluation_charts('f1', './results/ml')
# generate_evaluation_charts('kappa', './results/ml')

# print('is data normal: ', _is_data_normal('./results/random_data_labeled.csv'))

# prepare_dataset()
# prepare_dataset_2()