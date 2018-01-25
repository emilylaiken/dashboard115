import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import seaborn as sns

def lineChartDownload(labels, data, seriesnames, colors, title, minx, maxx, total, avg, fname):
    sns.set()
    newlabels = []
    # Formatting for x axis ticks
    divisor = int(len(labels)/10)
    for i in range (0, len(labels)):
        if i % divisor == 0:
            newlabels.append(labels[i][2:])
    plt.rcParams['lines.markersize'] = 3
    fig = plt.figure(figsize=(8.5, 11))
    ax = fig.add_subplot(111)
    plt.title(title)
    plt.xticks(np.arange(0, len(labels), divisor), newlabels, rotation=45)
    plt.tick_params(labelsize=7)
    plt.subplots_adjust(left=0.08, bottom=0.6, right=0.95, top=0.9, wspace=0, hspace=0)
    if total is not None:
        plt.annotate('Total: ' + str(total), (0,0), (0, -60), xycoords='axes fraction', textcoords='offset points', va='top', fontsize=9)
    if avg is not None:
        plt.annotate('Average (by day): ' + str(avg), (0,0), (0, -77), xycoords='axes fraction', textcoords='offset points', va='top', fontsize=9)
    for i in range (0, len(data)):
        ax.plot(np.arange(0, len(labels)), data[i], label=seriesnames[i], color=colors[i], linewidth=1, marker='o')
    if len(seriesnames) > 1:
        legend = ax.legend(loc='upper right')
    plt.savefig(fname)

def pieChartDownload(labels, data, colors, title, fname):
    sns.set()
    fig = plt.figure(figsize=(8.5, 11))
    ax = fig.add_subplot(111)
    plt.subplots_adjust(left=0.1, bottom=0.28, right=0.9, top=0.9, wspace=0, hspace=0)
    plt.title(title)
    patches, texts = ax.pie(data, labels=labels, colors=colors)
    for t in texts:
        t.set_fontsize(7)
    plt.savefig(fname)


