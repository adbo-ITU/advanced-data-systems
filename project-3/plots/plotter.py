from typing import Any, Dict, List
from matplotlib.font_manager import json
import matplotlib.pyplot as plt
from dataclasses import dataclass
from itertools import groupby
import sys
import pathlib
import numpy as np
import colorsys


work_dir = pathlib.Path(__file__).parent.resolve()


def make_out_path(name, format):
    out_dir = work_dir / "output" / format
    return out_dir / f"{name}.{format}"


def save_plot(name):
    format = "pdf"

    if not (work_dir / "output").exists():
        (work_dir / "output").mkdir()
    if not (work_dir / "output" / format).exists():
        (work_dir / "output" / format).mkdir()

    plt.savefig(make_out_path(name, format),
                format=format, bbox_inches="tight")


MARKERS = [('s', None), ('x', None), ('*', None),
           ('|', None), ('s', 'none'), ('o', 'none')]


@dataclass
class Measurement:
    file: str
    workload: str
    records: int
    projected: bool
    elapsed_time_ms: float
    iteration: int
    source: str

    @staticmethod
    def from_file(file: str):
        with open(file) as f:
            ms = json.load(f)

        measurements = []
        for m in ms:
            measurements.append(Measurement(
                file=m["path"],
                workload=m["workload"],
                records=m["numRecords"],
                iteration=m.get("iteration", 0),
                projected=m["projected"],
                elapsed_time_ms=m["executionTimeMillis"],
                source=m["path"].split(".")[-1]
            ))

        return measurements

    def configuration_key(self):
        return f"{self.workload}-{self.records}-{self.projected}-{self.source}"


@dataclass
class Configuration:
    key: str
    measurements: list[Measurement]

    file: str
    workload: str
    records: int
    projected: bool
    elapsed_time_ms: float
    source: str

    @staticmethod
    def from_measurements(key, measurements: list[Measurement]):
        return Configuration(
            key=key,
            measurements=measurements,
            file=measurements[0].file,
            workload=measurements[0].workload,
            records=measurements[0].records,
            projected=measurements[0].projected,
            elapsed_time_ms=measurements[0].elapsed_time_ms,
            source=measurements[0].source
        )

    def average_by(self, key: str):
        return sum([getattr(m, key) for m in self.measurements]) / len(self.measurements)

    def filesize(self):
        if self.source == "parquet" and self.records == 6001171:
            return "409 MB"
        if self.source == "csv" and self.records == 6001171:
            return "1.9 GB"
        if self.source == "parquet" and self.records == 59986214:
            return "4.6 GB"
        if self.source == "csv" and self.records == 59986214:
            return "20 GB"
        if self.source == "parquet" and self.records == 50000:
            return "22 MB"
        if self.source == "csv" and self.records == 50000:
            return "35 MB"
        if self.source == "parquet" and self.records == 650000:
            return "286 MB"
        if self.source == "csv" and self.records == 650000:
            return "457 MB"
        return "N/A"



# def get_queries(configs: list[Configuration]):
#     return sorted(set(c.query for c in configs))
#
#
# def get_threads(configs: list[Configuration]):
#     return sorted(set(c.threads for c in configs))
#
#
# def get_scaling_factors(configs: list[Configuration]):
#     return sorted(set(c.scaling_factor for c in configs))


def plot_latency(configs: list[Configuration]):
    # y_max = max(max(m.elapsed_time for m in c.measurements) for c in configs)

    ...
    # for q in get_queries(configs):
    #     plt.figure()
    #     ax = plt.gca()
    #
    #     for i, t in enumerate(get_threads(configs)):
    #         cs = [c for c in configs if c.query == q and c.threads == t]
    #         cs.sort(key=lambda x: x.scaling_factor)
    #
    #         xs = [c.scaling_factor for c in cs]
    #         ys = [c.average_by("elapsed_time") for c in cs]
    #
    #         marker, facecolor = MARKERS[i]
    #         plt.loglog(xs, ys, f'-{marker}',
    #                    markerfacecolor=facecolor, label=f"{t} threads")
    #
    #     plt.title(f"Query {q} latency")
    #
    #     plt.legend()
    #     plt.ylabel("Query Latency (s)")
    #     plt.xlabel("Scaling Factor")
    #
    #     save_plot("latency-q" + q)


def get_groups(configs: list[Configuration]):
    return {
        "SSB (SF1)": [
            next(c for c in configs if c.key == "ssb-6001171-False-parquet"),
            next(c for c in configs if c.key == "ssb-6001171-True-parquet"),
            next(c for c in configs if c.key == "ssb-6001171-False-csv"),
        ],
        "SSB (SF10)": [
            next(c for c in configs if c.key == "ssb-59986214-False-parquet"),
            next(c for c in configs if c.key == "ssb-59986214-True-parquet"),
            next(c for c in configs if c.key == "ssb-59986214-False-csv"),
        ],
        "Yelp (test)": [
            next(c for c in configs if c.key == "yelp-50000-False-parquet"),
            next(c for c in configs if c.key == "yelp-50000-True-parquet"),
            next(c for c in configs if c.key == "yelp-50000-False-csv"),
        ],
        "Yelp (train)": [
            next(c for c in configs if c.key == "yelp-650000-False-parquet"),
            next(c for c in configs if c.key == "yelp-650000-True-parquet"),
            next(c for c in configs if c.key == "yelp-650000-False-csv"),
        ],
    }

ORDER = ["Parquet (Without projection)", "Parquet (With projection)", "CSV"]

def plot_all_latencies(configs: list[Configuration]):
    groups = get_groups(configs)

    transposed: Dict[str, List[Configuration]] = {k: [] for k in ORDER}
    for i in range(3):
        for group in groups.values():
            transposed[ORDER[i]].append(group[i])

    x = np.arange(len(groups))
    width = 0.25  # the width of the bars

    patterns = ["o", "*", "//"]
    # colors = ["#77aeed", "#f2c57c", "#8deb8d"]

    fig = plt.subplots(layout="constrained")
    ax = plt.gca()
    for i, (label, c) in enumerate(transposed.items()):
        offset = width * i
        ys = [1000 * c.average_by("elapsed_time_ms") / c.average_by("records") for c in c]

        rects = ax.bar(x + offset, ys, width-0.01, zorder=3, label=label)
            # edgecolor="black", linewidth=1, hatch=patterns[i], color=colors[i])
        # ax.bar_label(rects, padding=3)
    ax.grid(zorder=0)
    ax.set_title(f'Comparison of per-record latencies')
    #  of reading from Parquet and CSV files for different datasets
    ax.set_ylabel('Latency per record (microseconds)')
    ax.set_xticks(x + width, list(groups.keys()))
    ax.legend(loc='upper right', ncols=1)

    save_plot("per-record-latencies")

    fig = plt.subplots(layout="constrained")
    ax = plt.gca()
    for i, (label, c) in enumerate(transposed.items()):
        offset = width * i
        ys = [c.average_by("elapsed_time_ms") for c in c]
        rects = ax.bar(x + offset, ys, width-0.01, zorder=3, label=label)
            # edgecolor="black", linewidth=1, hatch=patterns[i], color=colors[i])
        # ax.bar_label(rects, padding=3)
    ax.grid(zorder=0)
    ax.set_title(f'Comparison of total latencies')
    #  of reading from Parquet and CSV files for different datasets
    ax.set_ylabel('Latency (milliseconds)')
    ax.set_xticks(x + width, list(groups.keys()))

    box = ax.get_position()
    ax.set_position([box.x0, box.y0 - box.height * 0.1,
                     box.width, box.height * 0.9])
    ax.legend(loc='upper right', ncols=1)
    ax.set_yscale("log")

    save_plot("total-latencies")


def gen_tex_table(configs: list[Configuration]):
    groups = get_groups(configs)

    def fmt_ms(ms):
        if ms > 1000 * 60:
            return f"{int(ms / 1000 / 60)}\\,m {int(ms / 1000 % 60)}\\,s"
        if ms > 1000:
            return f"{ms / 1000:.1f}\\,s"
        return f"{ms:.0f}\\,ms"

    out = "\\begin{tabular}{llllll}\n"
    out += "\\toprule\n"
    # out += "& Parquet & Parquet (P) & CSV & No. records & File size \\\\\n"
    out += '&' + " & ".join("\\textbf{" + k + "}" for k in groups.keys()) + " \\\\\n"
    out += "\\midrule\n"

    rows = [
        ["Latency w/ Parquet (NP)"],
        ["Latency w/ Parquet (P)"],
        ["Latency w/ CSV"],
        ["Number of records"],
        ["Parquet file size"],
        ["CSV file size"],
    ]

    def add_group(group: List[Configuration]):
        rows[0].append(fmt_ms(group[0].average_by("elapsed_time_ms")))
        rows[1].append(fmt_ms(group[1].average_by("elapsed_time_ms")))
        rows[2].append(fmt_ms(group[2].average_by("elapsed_time_ms")))
        rows[3].append(f"{group[0].records:,}")
        rows[4].append(group[0].filesize().replace(" ", r"\,"))
        rows[5].append(group[2].filesize().replace(" ", r"\,"))

    for group in groups.values():
        add_group(group)

    for row in rows:
        out += " & ".join(row) + " \\\\\n"

    # for label, c in groups.items():
    #     ys = [fmt_ms(c.average_by("elapsed_time_ms")) for c in c]
    #     ys.append(f"{c[0].records:,}")
    #
    #     out += f"{label} & {' & '.join(ys)} \\\\\n"

    out += "\\bottomrule\n"
    out += "\\end{tabular}\n"

    out_path = make_out_path("latency_table", "tex")
    with open(out_path, "w") as f:
        f.write(out)


def read_data(file):
    rows = Measurement.from_file(file)
    print(f"Loaded {len(rows)} experiments")
    return rows


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python plotter.py <bench file path>")
        exit(1)

    measurements = read_data(sys.argv[1])

    configurations = [Configuration.from_measurements(key=k, measurements=list(g)) for k, g in groupby(
        sorted(measurements, key=lambda x: x.configuration_key()), lambda x: x.configuration_key())]
    configurations.sort(key=lambda x: x.key)

    print(len(configurations))
    for c in configurations:
        print(c.key)

    REPETITIONS = 4
    valid = True
    for c in configurations:
        if len(c.measurements) != REPETITIONS:
            print(f"Missing measurements for {c.key}, only has {len(c.measurements)}")
            valid = False
    if valid:
        print(f"All configurations have {REPETITIONS} repetitions, good")

    plot_all_latencies(configurations)
    gen_tex_table(configurations)
