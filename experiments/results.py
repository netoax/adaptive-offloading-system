
import json
import csv
from matplotlib import pyplot as plt
import pandas as pd
import matplotlib.dates as mdates
import matplotlib.ticker as ticker
import datetime
import glob
import numpy as np
from pathlib import Path

from skmultiflow.data import SEAGenerator
from skmultiflow.trees import HoeffdingTreeClassifier
from skmultiflow.trees import ExtremelyFastDecisionTreeClassifier
from skmultiflow.lazy import KNNClassifier
from skmultiflow.bayes import NaiveBayes

from skmultiflow.evaluation import EvaluatePrequential
from skmultiflow.data import DataStream

from experiments.constants import *

ht = HoeffdingTreeClassifier()
efdt = ExtremelyFastDecisionTreeClassifier()
nb = NaiveBayes()
knn = KNNClassifier()

RESULTS_PATH = '../../results/staging/ddos-10s'

def _prepare_profiler_logs(type):
    files = glob.glob("{}/{}:profiler*.txt".format(RESULTS_PATH, type))
    data = []
    for file in files:
        p = Path(file)
        data = _get_profiler_logs(type, p.stem, data)

    _create_profiler_logs_file(type, data)
    # return data

# type = p.stem[:p.stem.index(":")]
# _process_profiler_logs(type, p.stem)
# _generate_line_chart_timestamp(p.stem, 'cpu', './results/images/{}'.format(type), type)
# _generate_line_chart_timestamp(p.stem, 'memory', './results/images/{}'.format(type), type)

def statistical_tests():
    df = pd.read_csv('./data_2.csv')
    k2, p = stats.normaltest(df['memory'])
    alpha = 1e-3
    print(k2, p)
    if p < alpha:
        print("The null hypothesis can be rejected")
    else:
        print("The null hypothesis cannot be rejected")

def _label_columns():
    df = pd.read_csv('./analytics/random_data_test.csv')
    for index, row in df.iterrows():
        # print(row)
        measurement = Measurement(row['cepLatency'], row['cpu'], row['memory'], row['bandwidth'])
        # print(measurement)
        policy_manager.process()
        violated = policy_manager.is_composed_violated(measurement.to_dict()) or policy_manager.is_simple_violated(measurement.to_dict())
        # df['violated'] = int(violated)
        df.loc[index, 'violated'] = int(violated)
    df.to_csv('./random_data_labeled.csv', index=False)

def _generate_line_chart_timestamp(file, metric, output, type):
    data = pd.read_csv('./results/formatted/{}/{}.csv'.format(type, file), parse_dates=True, usecols=[metric, 'timestamp'])
    data.timestamp = pd.to_datetime(data.timestamp)
    date = data['timestamp'].dt.strftime("%H:%M:%S")
    memory = data[metric]
    plot = _create_plot(date, memory, 'timestamp', metric, title='aaaa')

def _setup_multiple_plots(ax, xaxis, yaxis, xlabel, ylabels):
    # print(xaxis, yaxis.head())
    for label in ylabels:
        print(yaxis[label])
        ax.plot(xaxis, yaxis[label], label=label)
        ax.legend()
    return ax

def _create_plot(xdata, ydata, xlabel, ylabel, title='average usage over time', mode='simple'):
    fig, ax = plt.subplots()

    if mode == 'simple':
        ax.plot(xdata, ydata)
    elif mode == 'multiple':
        ax = _setup_multiple_plots(ax, xdata, ydata, xlabel, ylabel)

    ax.xaxis.set_major_locator(ticker.MultipleLocator(10))
    ax.grid(True)

    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)

    fig.autofmt_xdate()

    return plt

def _save_plot_to_figure(plt, filename):
    plt.savefig('{}.eps'.format(filename), format='eps')

def process_nmon_files():
    data = pd.read_csv('./nmon_500throughput.csv', parse_dates=True, usecols=['timestamp', 'user', 'system'])
    data.timestamp = pd.to_datetime(data.timestamp)
    date = data['timestamp'].dt.strftime("%H:%M:%S")
    plot = _create_plot(date, data, 'timestamp', ['user', 'system'], title='average CPU usage over time', mode='multiple')
    plot.ylabel('cpu (%)')
    _save_plot_to_figure(plot, 'medium_throughput')
    # print(date)

def process_staging_files():
    files = glob.glob("./results/staging/*.txt")
    for file in files:
        p = Path(file)
        type = p.stem[:p.stem.index(":")]
        _process_profiler_logs(type, p.stem)
        _generate_line_chart_timestamp(p.stem, 'cpu', './results/images/{}'.format(type), type)
        _generate_line_chart_timestamp(p.stem, 'memory', './results/images/{}'.format(type), type)

def group_staging_files_together(type="edge"):
    data = []
    for app in APPLICATIONS:
        for t in [250, 500, 750]:
            for i in range(1, 31):
                        # print(f'./results/staging/{i}/{app}/{t}/{type}:profiler*')
                files = glob.glob(f'/Users/jneto/drive/experiment-phase-1/{i}/{app}/{t}/{type}:profiler:*.txt')
                print(files)
                for file in files:
                    p = Path(file)
                    _get_profiler_logs(p, data)
            _create_profiler_logs_file(type, app, t, data)
            data = []

def _get_profiler_logs(filename, data):
    file = open(filename)
    next(file)
    for line in file:
        instance = json.loads(line)
        data.append(instance.values())
    return data

def _create_profiler_logs_file(type, app, throughput, data):
    header = []
    if type == 'edge':
        header = ['bandwidth', 'cepLatency', 'cpu', 'memory', 'rtt', 'timestamp']
    else:
        header = ['cpu', 'memory', 'timestamp']

    with open(f'../results/formatted/profiler-{type}-{app}-{throughput}.csv', 'w') as f:
        writer = csv.writer(f)
        writer.writerow(header)
        for d in data:
            writer.writerow(d)

def set_box_color(bp, color):
    plt.setp(bp['boxes'], color=color)
    plt.setp(bp['whiskers'], color=color)
    plt.setp(bp['caps'], color=color)
    plt.setp(bp['medians'], color=color)

def get_application_data(app, metric, type="edge"):
    grouped_data = []
    files = glob.glob(f'../results/formatted/profiler-{type}-*.csv')
    # print(files)
    for file in files:
        p = Path(file)
        df = pd.read_csv(p)
        # print(df["cpu"].min)
        data = df[metric].to_list()
        grouped_data.append(data)
    return grouped_data

def _create_boxplot_charts(metric, legend="", type="edge"):
    ddos_128s_data = get_application_data("ddos-128s", metric, type)

    ticks = ['250', '500', '750']

    # app1 = [[1,2,3,4,5], [1,2,3,4,5], [1,2,3,4,5]]
    app2 = [[1,2,3,4,5], [1,2,3,4,5], [1,2,3,4,5]]

    boxplot_1 = plt.boxplot(app2, positions=np.array(range(len(app2)))*2.0-0.4, sym='', widths=0.6, showfliers=True)
    boxplot_2 = plt.boxplot(ddos_128s_data, positions=np.array(range(len(ddos_128s_data)))*2.0+0.4, sym='', widths=0.6, showfliers=True)

    set_box_color(boxplot_1, '#D7191C') # colors are from http://colorbrewer2.org/
    set_box_color(boxplot_2, '#2C7BB6')

    plt.plot([], c='#D7191C', label='ddos-10s')
    plt.plot([], c='#2C7BB6', label='ddos-128s')
    # plt.plot([], c='#2C7BB6', label='750')
    plt.legend()

    plt.xticks(range(0, len(ticks) * 2, 2), ticks)
    plt.xlim(-2, len(ticks)*2)
    # plt.ylim(0, 8)
    plt.xlabel("Throughput (events/second)")
    plt.ylabel(legend)
    plt.tight_layout()
    plt.savefig(f'./images/{type}-{metric}.eps', format='eps')
    plt.clf()

group_staging_files_together(type="cloud")

### Edge Graphs

# _create_boxplot_charts("cpu", legend="CPU Usage (%)", type="edge")
# _create_boxplot_charts("memory", legend="Memory Usage (%)", type="edge")
# _create_boxplot_charts("bandwidth", legend="Network Bandwidth (Mbps)", type="edge")
# _create_boxplot_charts("cepLatency", legend="CEP Latency (Ms)", type="edge")
# _create_boxplot_charts("rtt", legend="Round-Trip Time (Ms)", type="edge")


### Cloud Grapths

_create_boxplot_charts("cpu", legend="CPU Usage (%)", type="cloud")
_create_boxplot_charts("memory", legend="Memory Usage (%)", type="cloud")
# _create_boxplot_charts("bandwidth", legend="Network Bandwidth (Mbps)", type="cloud")

# _process_profiler_logs("profiling_logs")
# file = './nmon.csv'
# _create_and_save_plot(file, 'cpu', 'nmon-test-output')
# _create_charts_from_files()
# process_staging_files()
# process_nmon_files()

# _prepare_profiler_logs('edge')
# _create_boxplot_charts()
