import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import seaborn as sns

def lineChartDownload(labels, data, seriesnames, colors, title, minx, maxx, fname):
    sns.set()
    newlabels = []
    # Formatting for x axis ticks
    divisor = int(len(labels)/10)
    for i in range (0, len(labels)):
        if i % divisor == 0:
            newlabels.append(labels[i][2:])
    plt.rcParams["figure.figsize"] = [8, 4]
    plt.rcParams['lines.markersize'] = 3
    fig = plt.figure()
    ax = plt.subplot(111)
    plt.title(title)
    plt.xticks(np.arange(0, len(labels), divisor), newlabels, rotation=45)
    plt.tick_params(labelsize=7)
    for i in range (0, len(data)):
        plt.plot(labels, data[i], label=seriesnames[i], color=colors[i], linewidth=1, marker='o')
    plt.savefig(fname)

def pieChartDownload(labels, data, colors, title, fname):
    sns.set()
    plt.rcParams["figure.figsize"] = [8, 8]
    fig = plt.figure()
    plt.title(title)
    patches, texts = plt.pie(data, labels=labels, colors=colors)
    for t in texts:
        t.set_fontsize(7)
    plt.savefig(fname)


