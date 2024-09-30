import matplotlib.pyplot as plt
from dataclasses import dataclass
import re
from itertools import groupby
import os
import sys
import pathlib


def make_out_path(name, format):
    work_dir = pathlib.Path(__file__).parent.resolve()
    out_dir = work_dir / "output" / format
    return out_dir / f"{name}.{format}"


RUNNERS = ["naive_bayes", "naive_bayes_udtf"]

IMPLEMENTATION_LABELS = {
    "naive_bayes": "Plain SQL",
    "naive_bayes.sql": "Plain SQL",
    "naive_bayes_udtf": "Python UDTF",
    "naive_bayes_udtf.sql": "Python UDTF",
}

def save_plot(name):
    format = "pdf"
    plt.savefig(make_out_path(name, format),
                format=format, bbox_inches="tight")


@dataclass
class Measurement:
    runner: str
    repetition: str
    elapsed_time: float
    accuracy: float

    @staticmethod
    def from_file(file: str):
        with open(file) as f:
            lines = f.readlines()
            content = ''.join(lines)

        config_items = [x.split("=", 1) for x in lines[0].strip().split(", ")]
        config = {k: v for k, v in config_items}

        time = re.search(
            r"real\t(?P<minutes>\d+)m(?P<seconds>\d+\.\d+)s", content).groupdict()
        elapsed = int(time["minutes"]) * 60 + float(time["seconds"])

        accuracy = float(re.search(r'SUCCESS_RATE[^\n]+\n"([\d\.]+)"', content).group(1))

        return Measurement(
            runner=config["runner"],
            repetition=config["repetition"],
            elapsed_time=elapsed,
            accuracy=accuracy
        )

    def configuration_key(self):
        return f"{self.runner}"


@dataclass
class Configuration:
    key: str
    measurements: list[Measurement]

    def average_by(self, key: str):
        return sum([getattr(m, key) for m in self.measurements]) / len(self.measurements)


def read_data(folder):
    rows = []
    for entry in os.listdir(folder):
        # try:
        row = Measurement.from_file(os.path.join(folder, entry))
        rows.append(row)
        # except:
        #     print(f"Error processing {entry}")

    print(f"Loaded {len(rows)} experiments")

    return rows


def plot_variance(configs: list[Configuration]):
    y_max = max(max(m.elapsed_time for m in c.measurements) for c in configs)

    plt.figure(figsize=(13, 5))

    xs = [[m.elapsed_time for m in c.measurements] for c in configs]
    labels = [c.key for c in configs]

    print(len(xs), len(labels))
    print(xs, labels)

    plt.boxplot(xs, labels=labels)

    plt.ylim(0, y_max)
    plt.xlabel("Latency (seconds)")
    plt.ylabel("Query implementation")

    lines = [
        r"\begin{tabular}{lll}",
        r"\toprule",
        r"Implementation & Latency & Accuracy \\",
        r"\midrule",
    ]

    for c in configs:
        label = IMPLEMENTATION_LABELS[c.key]
        time = c.average_by('elapsed_time')
        accuracy = c.average_by('accuracy')
        lines.append(rf"{label} & {time:.1f}s & {accuracy * 100:.1f}\% \\")

    lines.append(r"""\bottomrule\end{tabular}""")

    with open(make_out_path("naive_bayes_averages", "tex"), "w") as f:
        f.write('\n'.join(lines))



if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python plotter.py <bench dir path>")
        exit(1)

    measurements = read_data(sys.argv[1])

    configurations = [Configuration(key=k, measurements=list(g)) for k, g in groupby(
        sorted(measurements, key=lambda x: x.configuration_key()), lambda x: x.configuration_key())]

    plot_variance(configurations)
