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


def statistical_tests():
    df = pd.read_csv("./data_2.csv")
    k2, p = stats.normaltest(df["memory"])
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


def group_staging_files_together(type="edge"):
    data = []
    for app in APPLICATIONS:
        for t in [250, 500, 750]:
            for i in range(1, 31):
                # print(f'./results/staging/{i}/{app}/{t}/{type}:profiler*')
                files = glob.glob(
                    f"/Users/jneto/drive/resultados-10s/staging/{i}/{app}/{t}/{type}:profiler:*.txt"
                )
                print(files)
                for file in files:
                    p = Path(file)
                    _get_profiler_logs(p, data)
            _create_profiler_logs_file(type, app, t, data)
            data = []


# ~/drive/experimentos/policy/csv-files/profiler-edge-ddos-128s-500.csv'
def group_all_profiling_data(directory):
    header = ["bandwidth", "cepLatency", "cpu", "memory", "rtt", "timestamp"]
    all_filenames = [i for i in glob.glob(f"{directory}/profiler-edge*.csv")]
    combined_csv = pd.concat([pd.read_csv(f) for f in all_filenames])
    combined_csv.to_csv(f"{directory}/combined_csv.csv", index=False, header=header)

    # data = []
    # # print(f'./results/staging/{i}/{app}/{t}/{type}:profiler*')
    # files = glob.glob(f'{directory}/profiler-*.csv')
    # print(files)
    # for file in files:
    #     p = Path(file)
    #     file = open(p)
    #     next(file)
    #     for line in file:
    #         data.append(line)

    # with open(f'{directory}/combined.csv', 'w') as f:
    #     writer = csv.writer(f)
    #     writer.writerow(['bandwidth', 'cepLatency', 'cpu', 'memory', 'rtt', 'timestamp'])
    #     for d in data:
    #         print(d)
    #         writer.writerow(d)


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


def get_application_data(app, metric, type="edge"):
    grouped_data = []
    files = glob.glob(f"../results/formatted/profiler-{type}-{app}*.csv")
    # print(files)
    for file in files:
        p = Path(file)
        df = pd.read_csv(p)
        # print(df["cpu"].min)
        data = df[metric].to_list()
        grouped_data.append(data)
    return grouped_data

def get_application_data_dfs(app, metric, type="edge"):
    grouped_data = []
    files = glob.glob(f"../results/formatted/profiler-{type}-{app}*.csv")
    # print(files)
    for file in files:
        p = Path(file)
        print(file)
        df = pd.read_csv(p)
        # print(df["cpu"].min)
        # data = df[metric].to_list()
        grouped_data.append(df)
    return grouped_data


# def _create_boxplot_charts(metric, legend="", type="edge"):
#     ddos_128s_data = get_application_data("ddos-128s", metric, type)
#     ddos_10s_data = get_application_data("ddos-10s", metric, type)

#     ticks = ['250', '500', '750']
#     flierprops = dict(marker='o', markerfacecolor='green', markersize=12,
#                   markeredgecolor='none')

#     boxplot_1 = plt.boxplot(ddos_10s_data, positions=np.array(range(len(ddos_10s_data)))*2.0-0.4, widths=0.6)
#     boxplot_2 = plt.boxplot(ddos_128s_data, positions=np.array(range(len(ddos_128s_data)))*2.0+0.4, widths=0.6)

#     set_box_color(boxplot_1, '#D7191C') # colors are from http://colorbrewer2.org/
#     set_box_color(boxplot_2, '#2C7BB6')

#     plt.plot([], c='#D7191C', label='ddos-10s')
#     plt.plot([], c='#2C7BB6', label='ddos-128s')
#     # plt.plot([], c='#2C7BB6', label='750')
#     plt.legend()

#     plt.xticks(range(0, len(ticks) * 2, 2), ticks)
#     plt.xlim(-2, len(ticks)*2)
#     # plt.ylim(0, 8)
#     plt.xlabel("Throughput (events/second)")
#     plt.ylabel(legend)
#     plt.tight_layout()
#     # plt.savefig(f'./images/{type}-{metric}.eps', format='eps')
#     # plt.clf()
#     plt.show()

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

def _create_boxplot_charts(metric, legend="", type="edge"):
    ddos_128s_data = get_application_data("ddos-128s", metric, type)
    ddos_10s_data = get_application_data("ddos-10s", metric, type)
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
    plt.savefig(f'./images/{type}-{metric}.eps', format='eps')
    plt.clf()
    # plt.show()

def is_json(myjson):
    try:
        json.loads(myjson)
    except ValueError as e:
        return False
    return True


def _process_script_output_logs():
    response_time_data = []
    file = open(
        "/Users/jneto/drive/experiment-phase-1/ddos-128s/execution-output/script.txt"
    )
    for l in file:
        # if is_json(l):
        #     print(l)
        try:
            data_dict = ast.literal_eval(l)
            response_time_data.append(json.dumps(data_dict))
            # print(l)
            # value = json.loads(l)
            # print(value)
            # break
        except Exception:
            pass

    print(len(response_time_data))



# group_all_profiling_data('/Users/jneto/drive/experimentos/policy/csv-files')

# group_staging_files_together(type="edge")
# group_staging_files_together(type="cloud")

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

# _process_script_output_logs()
