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
import ast
import seaborn as sns
import scipy.stats as st

from skmultiflow.data import SEAGenerator
from skmultiflow.trees import HoeffdingTreeClassifier
from skmultiflow.trees import ExtremelyFastDecisionTreeClassifier
from skmultiflow.lazy import KNNClassifier
from skmultiflow.bayes import NaiveBayes

from skmultiflow.evaluation import EvaluatePrequential
from skmultiflow.data import DataStream
from matplotlib.patches import PathPatch

from experiments.constants import *

ht = HoeffdingTreeClassifier()
efdt = ExtremelyFastDecisionTreeClassifier()
nb = NaiveBayes()
knn = KNNClassifier()

RESULTS_PATH = "../../results/staging/ddos-10s"


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


def statistical_tests(data):
    k2, p = st.normaltest(data)
    alpha = 1e-3
    print(k2, p)
    if p < alpha:
        print("The null hypothesis can be rejected")
    else:
        print("The null hypothesis cannot be rejected")


def _label_columns():
    df = pd.read_csv("./analytics/random_data_test.csv")
    for index, row in df.iterrows():
        # print(row)
        measurement = Measurement(
            row["cepLatency"], row["cpu"], row["memory"], row["bandwidth"]
        )
        # print(measurement)
        policy_manager.process()
        violated = policy_manager.is_composed_violated(
            measurement.to_dict()
        ) or policy_manager.is_simple_violated(measurement.to_dict())
        # df['violated'] = int(violated)
        df.loc[index, "violated"] = int(violated)
    df.to_csv("./random_data_labeled.csv", index=False)


def _generate_line_chart_timestamp(file, metric, output, type):
    data = pd.read_csv(
        "./results/formatted/{}/{}.csv".format(type, file),
        parse_dates=True,
        usecols=[metric, "timestamp"],
    )
    data.timestamp = pd.to_datetime(data.timestamp)
    date = data["timestamp"].dt.strftime("%H:%M:%S")
    memory = data[metric]
    plot = _create_plot(date, memory, "timestamp", metric, title="aaaa")


def _setup_multiple_plots(ax, xaxis, yaxis, xlabel, ylabels):
    # print(xaxis, yaxis.head())
    for label in ylabels:
        print(yaxis[label])
        ax.plot(xaxis, yaxis[label], label=label)
        ax.legend()
    return ax


def _create_plot(
    xdata, ydata, xlabel, ylabel, title="average usage over time", mode="simple"
):
    fig, ax = plt.subplots()

    if mode == "simple":
        ax.plot(xdata, ydata)
    elif mode == "multiple":
        ax = _setup_multiple_plots(ax, xdata, ydata, xlabel, ylabel)

    ax.xaxis.set_major_locator(ticker.MultipleLocator(10))
    ax.grid(True)

    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)

    fig.autofmt_xdate()

    return plt


def _save_plot_to_figure(plt, filename):
    plt.savefig("{}.eps".format(filename), format="eps")


def process_nmon_files():
    data = pd.read_csv(
        "./nmon_500throughput.csv",
        parse_dates=True,
        usecols=["timestamp", "user", "system"],
    )
    data.timestamp = pd.to_datetime(data.timestamp)
    date = data["timestamp"].dt.strftime("%H:%M:%S")
    plot = _create_plot(
        date,
        data,
        "timestamp",
        ["user", "system"],
        title="average CPU usage over time",
        mode="multiple",
    )
    plot.ylabel("cpu (%)")
    _save_plot_to_figure(plot, "medium_throughput")
    # print(date)


def process_staging_files():
    files = glob.glob("./results/staging/*.txt")
    for file in files:
        p = Path(file)
        type = p.stem[: p.stem.index(":")]
        _process_profiler_logs(type, p.stem)
        _generate_line_chart_timestamp(
            p.stem, "cpu", "./results/images/{}".format(type), type
        )
        _generate_line_chart_timestamp(
            p.stem, "memory", "./results/images/{}".format(type), type
        )


def group_staging_files_together(category, application, type="edge"):
    data = []
    for t in [250, 500, 750]:
        for i in range(1, 31):
            # print(f'./results/staging/{i}/{app}/{t}/{type}:profiler*')
            files = glob.glob(
                f"/Users/jneto/drive/experimentos/{category}/{application}/service-logs/{i}/{application}/{t}/{type}:profiler:*.txt"
            )
            print(files)
            for file in files:
                p = Path(file)
                _get_profiler_logs(p, data)
        _create_profiler_logs_file(type, application, t, data)
        data = []


# ~/drive/experimentos/policy/csv-files/profiler-edge-ddos-128s-500.csv'
def group_all_profiling_data(directory):
    header = ["bandwidth", "cepLatency", "cpu", "memory", "rtt", "timestamp"]
    all_filenames = [i for i in glob.glob(f"{directory}/profiler-edge*.csv")]
    combined_csv = pd.concat([pd.read_csv(f) for f in all_filenames])
    combined_csv.to_csv(f"{directory}/combined_csv.csv", index=False, header=header)

def _get_profiler_logs(filename, data):
    file = open(filename)
    next(file)
    for line in file:
        instance = json.loads(line)
        data.append(instance.values())
    return data


def _create_profiler_logs_file(type, app, throughput, data):
    header = []
    if type == "edge":
        header = ["bandwidth", "cepLatency", "cpu", "memory", "rtt", "timestamp"]
    else:
        header = ["cpu", "memory", "timestamp"]

    with open(f"../results/formatted/profiler-{type}-{app}-{throughput}.csv", "w") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        for d in data:
            writer.writerow(d)


def set_box_color(bp, color):
    plt.setp(bp["boxes"], color=color)
    plt.setp(bp["whiskers"], color=color)
    plt.setp(bp["caps"], color=color)
    plt.setp(bp["medians"], color=color)

def clear_df(df, metric, type):
    if metric == 'bandwidth':
        df = df[df.bandwidth > 4]
    if metric == 'cepLatency':
        df = df[df.cepLatency > 0]
    if metric == 'cpu' and type == 'cloud':
        df = df[df.cpu < 90]
        df = df[df.cpu > 0]
    return df

def get_application_data(category, app, metric, type="edge"):
    grouped_data = []
    files = glob.glob(f"/Users/jneto/drive/experimentos/{category}/csv-files/profiler-{type}-{app}*.csv")
    for file in files:
        p = Path(file)
        df = pd.read_csv(p)
        df = clear_df(df, metric, type)
        data = df[metric].to_list()
        grouped_data.append(data)
    return grouped_data

def get_long_form_df(data, application, metric):
    tmp = {
        'application': [],
        'throughput': [],
    }

    tmp[metric]=[]

    for key in data:
        for entry in data[key]:
            # print(entry)
            tmp['application'].append(application)
            tmp['throughput'].append(key)
            tmp[metric].append(entry)

    df = pd.DataFrame.from_dict(tmp)
    print(df.head())
    df_long = pd.melt(df, "application", var_name="throughput", value_name=metric)
    return df

def adjust_box_widths(g, fac):
    """
    Adjust the withs of a seaborn-generated boxplot.
    """

    # iterating through Axes instances
    for ax in g.axes:

        # iterating through axes artists:
        for c in ax.get_children():

            # searching for PathPatches
            if isinstance(c, PathPatch):
                # getting current width of box:
                p = c.get_path()
                verts = p.vertices
                verts_sub = verts[:-1]
                xmin = np.min(verts_sub[:, 0])
                xmax = np.max(verts_sub[:, 0])
                xmid = 0.5*(xmin+xmax)
                xhalf = 0.5*(xmax - xmin)

                # setting new width of box
                xmin_new = xmid-fac*xhalf
                xmax_new = xmid+fac*xhalf
                verts_sub[verts_sub[:, 0] == xmin, 0] = xmin_new
                verts_sub[verts_sub[:, 0] == xmax, 0] = xmax_new

                # setting new width of median line
                for l in ax.lines:
                    if np.all(l.get_xdata() == [xmin, xmax]):
                        l.set_xdata([xmin_new, xmax_new])

def _create_boxplot_charts(category, metric, legend="", type="edge"):
    ddos_128s_data = get_application_data(category, "ddos-128s", metric, type)
    ddos_10s_data = get_application_data(category, "ddos-10s", metric, type)
    data_10s = {
        '250': ddos_10s_data[0],
        '500': ddos_10s_data[1],
        '750': ddos_10s_data[2]
    }

    data_128s = {
        '250': ddos_128s_data[0],
        '500': ddos_128s_data[1],
        '750': ddos_128s_data[2]
    }

    df_10s = get_long_form_df(data_10s, "ddos-10s", metric)
    df_128s = get_long_form_df(data_128s, "ddos-128s", metric)
    fig = plt.figure()
    sns.set_theme(style="whitegrid")
    fig.ax = sns.boxplot(x="throughput", hue="application", y=metric, width=0.7, data=pd.concat([df_10s, df_128s]))

    plt.xlabel("Throughput (events/second)")
    plt.ylabel(legend)
    plt.xlim(-1, 4)
    # fig.ax.set_aspect(-2)
    # plt.xticks(range(0, 3 * 2, 2), ["250", "500", "750"])
    adjust_box_widths(fig, 0.7)
    plt.tight_layout()
    plt.savefig(f'./images/{category}-{type}-{metric}.eps', format='eps')
    plt.clf()
    # plt.show()

def create_data_histogram(category, metric, legend="", type="edge"):
    ddos_128s_data = get_application_data(category, "ddos-128s", metric, type)
    # ddos_10s_data = get_application_data(category, "ddos-10s", metric, type)

    x = [i for i in ddos_128s_data[1] if i <= 40]
    x = ddos_128s_data[1]

    statistical_tests(x)

    plt.hist(x, density=True)  # density=False would make counts

    mn, mx = plt.xlim()
    plt.xlim(mn, mx)

    kde_xs = np.linspace(mn, mx, 300)
    kde = st.gaussian_kde(x)
    plt.plot(kde_xs, kde.pdf(kde_xs), label="PDF")

    plt.ylabel('Probability')
    plt.xlabel('Data');
    plt.show();

def is_json(myjson):
    try:
        json.loads(myjson)
    except ValueError as e:
        return False
    return True

def _get_execution_output_logs(category, application):
    df = pd.DataFrame(columns=['response_time', 'timestamp'])
    files = glob.glob(f'/Users/jneto/drive/experimentos/{category}/{application}/execution-output/*')
    for file in files:
        f = open(file)
        for l in f:
            try:
                data_dict = ast.literal_eval(l)
                df = df.append(data_dict, ignore_index=True)
            except Exception:
                pass
    return df

def _process_script_output_logs(category):
    logs_10s = _get_execution_output_logs(category, 'ddos-10s')
    logs_128s = _get_execution_output_logs(category, 'ddos-128s')

    print(logs_10s.head())

def _get_shapiro_normality_info(data):
    stat, p = st.shapiro(data)
    print('normality=%.3f, p=%.3f' % (stat, p))

def _get_mannwhitneyu_info(data1, data2):
    stat, p = st.mannwhitneyu(data1, data2, alternative = 'two-sided')
    print('statistic=%.3f, p=%.3f' % (stat, p))

def _calculate_p_values(application='', type='edge'):
    strategies = ['policy', 'online-learning']
    throughputs = ['250','500','750']
    metrics = ['cpu', 'memory']

    if type == 'edge':
        metrics.append('bandwidth')

    for index in range(len(throughputs)):
        for m in metrics:
            policy = get_application_data("policy", application, m, type)
            online = get_application_data("online-learning", application, m, type)

            print(f'\nstatistic info for: ({m}) {type} {throughputs[index]} | {application}')
            data1 = policy[index]
            data2 = online[index]
            print(len(data1), len(data2))
            _get_mannwhitneyu_info(data1, data2)
        # print(strategies[i], throughputs[i])

def _get_statistics_info(category, metric, type):
    ddos_128s_data = get_application_data(category, "ddos-128s", metric, type)
    ddos_10s_data = get_application_data(category, "ddos-10s", metric, type)

    throughputs = ['250','500','750']

    for index in range(len(ddos_10s_data)):
        data = ddos_10s_data[index]
        print(f'\nstatistic info for: {throughputs[index]} - {metric} - {type} | {category} - ddos-10s')
        print('std deviation: ', np.std(data))
        print('mean: ', np.mean(data))
        print('min: ', np.min(data))
        print('max: ', np.max(data))
        _get_shapiro_normality_info(data)

    for index in range(len(ddos_128s_data)):
        data = ddos_128s_data[index]
        print(f'\nstatistic info for: {throughputs[index]} - {metric} - {type} | {category} - ddos-128s')
        print('std deviation: ', np.std(data))
        print('mean: ', np.mean(data))
        print('min: ', np.min(data))
        print('max: ', np.max(data))
        _get_shapiro_normality_info(data)

        # print(ddos_10s_data[index])

def _get_all_statistic_info():
    _get_statistics_info("policy", "cpu", type="edge")
    _get_statistics_info("policy", "memory", type="edge")
    _get_statistics_info("policy", "cepLatency", type="edge")
    _get_statistics_info("policy", "rtt", type="edge")
    _get_statistics_info("policy", "bandwidth", type="edge")

    _get_statistics_info("policy", "cpu", type="cloud")
    _get_statistics_info("policy", "memory", type="cloud")

    _get_statistics_info("online-learning", "cpu", type="edge")
    _get_statistics_info("online-learning", "memory", type="edge")
    _get_statistics_info("online-learning", "cepLatency", type="edge")
    _get_statistics_info("online-learning", "rtt", type="edge")
    _get_statistics_info("online-learning", "bandwidth", type="edge")

    _get_statistics_info("online-learning", "cpu", type="cloud")
    _get_statistics_info("online-learning", "memory", type="cloud")


_calculate_p_values('ddos-10s')
_calculate_p_values('ddos-128s')

_calculate_p_values('ddos-10s', 'cloud')
_calculate_p_values('ddos-128s', 'cloud')

# _get_all_statistic_info()
# group_all_profiling_data('/Users/jneto/drive/experimentos/policy/csv-files')

# group_staging_files_together('online-learning', 'ddos-128s', type="edge")
# group_staging_files_together('online-learning', 'ddos-128s', type="cloud")

# group_staging_files_together('online-learning', 'ddos-10s', type="edge")
# group_staging_files_together('online-learning', 'ddos-10s', type="cloud")

### ******** Policy Based Mechanism ***********

### Edge Graphs

# _create_boxplot_charts("cpu", legend="CPU Usage (%)", type="edge")
# _create_boxplot_charts("memory", legend="Memory Usage (%)", type="edge")
# _create_boxplot_charts("bandwidth", legend="Network Bandwidth (Mbps)", type="edge")
# _create_boxplot_charts("cepLatency", legend="CEP Latency (Ms)", type="edge")
# _create_boxplot_charts("rtt", legend="Round-Trip Time (Ms)", type="edge")


### Cloud Grapths

# _create_boxplot_charts("cpu", legend="CPU Usage (%)", type="cloud")
# _create_boxplot_charts("memory", legend="Memory Usage (%)", type="cloud")
# _create_boxplot_charts("bandwidth", legend="Network Bandwidth (Mbps)", type="cloud")



### ******** Online Learning Mechanism ***********

# _create_boxplot_charts("online-learning", "cpu", legend="CPU Usage (%)", type="edge")
# _create_boxplot_charts("online-learning", "memory", legend="Memory Usage (%)", type="edge")
# _create_boxplot_charts("online-learning", "bandwidth", legend="Network Bandwidth (Mbps)", type="edge")
# _create_boxplot_charts("online-learning", "cepLatency", legend="CEP Latency (Ms)", type="edge")
# _create_boxplot_charts("online-learning", "rtt", legend="Round-Trip Time (Ms)", type="edge")

### Cloud Grapths

# _create_boxplot_charts("online-learning", "cpu", legend="CPU Usage (%)", type="cloud")
# _create_boxplot_charts("online-learning", "memory", legend="Memory Usage (%)", type="cloud")

# create_data_histogram("online-learning", "memory", legend="Memory Usage (%)", type="edge")
# create_data_histogram("online-learning", "cpu", legend="COU Usage (%)", type="edge")




# _process_profiler_logs("profiling_logs")
# file = './nmon.csv'
# _create_and_save_plot(file, 'cpu', 'nmon-test-output')
# _create_charts_from_files()
# process_staging_files()
# process_nmon_files()
# _prepare_profiler_logs('edge')
# _create_boxplot_charts()
# _process_script_output_logs('policy')
