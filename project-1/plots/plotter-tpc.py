import matplotlib.pyplot as plt
import csv
from dataclasses import dataclass
import re
from itertools import groupby
import os
import sys
import pathlib
import numpy as np


def make_out_path(name, format):
    work_dir = pathlib.Path(__file__).parent.resolve()
    out_dir = work_dir / "output" / format
    return out_dir / f"{name}.{format}"


def save_plot(name):
    format = "pdf"
    plt.savefig(make_out_path(name, format),
                format=format, bbox_inches="tight")


QUERY_LABELS = {
    "q1": "Query 1",
    "q5": "Query 5",
    "q18": "Query 18"
}
SCALING_FACTOR_NUMS = {
    "SF1": 1,
    "SF10": 10,
    "SF100": 100,
    "SF1000": 1000
}
WAREHOUSES = ["CHEETAH_WH_XS", "CHEETAH_WH_S", "CHEETAH_WH_M", "CHEETAH_WH_L"]
WAREHOUSE_LABELS = {
    "ANIMAL_TASK_WH": "X-Small",
    "CHEETAH_WH_XS": "X-Small",
    "CHEETAH_WH_S": "Small",
    "CHEETAH_WH_M": "Medium",
    "CHEETAH_WH_L": "Large",
}
WAREHOUSE_ORDER = ["CHEETAH_WH_XS", "CHEETAH_WH_S", "CHEETAH_WH_M", "CHEETAH_WH_L"]

MARKERS = [('s', None), ('x', None), ('*', None),
           ('|', None), ('s', 'none'), ('o', 'none')]


@dataclass
class Measurement:
    query: str
    elapsed_time: float
    warehouse: str
    repetition: str
    scaling_factor: str
    bytes_spilled_local: float

    @staticmethod
    def from_file(file: str, query_history):
        with open(file) as f:
            lines = f.readlines()
            content = ''.join(lines)

        config_items = [x.split("=", 1) for x in lines[0].strip().split(", ")]
        config = {k: v for k, v in config_items}

        time_match = re.search(
            r"Time Elapsed: (?P<seconds>[\d\.]+)s\nGoodbye!", content).groupdict()
        elapsed = float(time_match["seconds"])

        config_key = Measurement.make_config_key(config["query"], config["warehouse"], config["scaling_factor"])

        if config_key not in query_history:
            raise Exception(f"Unknown configuration: {config_key}")

        qh = query_history[config_key]

        return Measurement(
            query=config["query"],
            elapsed_time=elapsed,
            warehouse=config["warehouse"],
            repetition=config["repetition"],
            scaling_factor=config["scaling_factor"],
            bytes_spilled_local=float(qh["BYTES_SPILLED_TO_LOCAL_STORAGE"]),
        )


    @staticmethod
    def make_config_key(query: str, warehouse: str, scaling_factor: str):
        q = f'Q{int(query.replace("q", "")):02}'
        return f"{q}-{warehouse}-{scaling_factor}"

    def configuration_key(self):
        return Measurement.make_config_key(self.query, self.warehouse, self.scaling_factor)


@dataclass
class Configuration:
    key: str
    measurements: list[Measurement]

    def average_by(self, key: str):
        return sum([getattr(m, key) for m in self.measurements]) / len(self.measurements)


def read_query_history():
    configs = {}

    # SELECT *
    # FROM  snowflake.account_usage.query_history
    # WHERE
    #   start_time::date > dateadd('days', -1, current_date)
    #   AND user_name = 'CHEETAH'
    #   AND SCHEMA_NAME like 'TPCH_SF%'
    #   AND QUERY_TEXT not like 'ALTER SESSION%'
    # ORDER BY bytes_spilled_to_local_storage, warehouse_size DESC
    # LIMIT 200;

    with open('./plots/query_history.csv', newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            query = ""
            if row['QUERY_TEXT'].startswith("select   l_returnflag"):
                query = "Q01"
            elif row['QUERY_TEXT'].startswith("select   n_name"):
                query = "Q05"
            elif row['QUERY_TEXT'].startswith("select c_name"):
                query = "Q18"
            else:
                raise Exception("Unknown query")

            scaling_factor = row['SCHEMA_NAME'].replace("TPCH_", "")
            config_key = f"{query}-{row['WAREHOUSE_NAME']}-{scaling_factor}"

            configs[config_key] = row

    return configs


def read_data(folder):
    query_history = read_query_history()
    rows = []
    for entry in os.listdir(folder):
        # try:
        row = Measurement.from_file(os.path.join(folder, entry), query_history)
        rows.append(row)
        # except:
        #     print(f"Error processing {entry}")

    print(f"Loaded {len(rows)} experiments")

    return rows


def plot_latency(configs: list[Configuration]):
    y_max = max(max(m.elapsed_time for m in c.measurements) for c in configs)

    for q in QUERY_LABELS.keys():
        plt.figure()
        ax = plt.gca()
        ax.set_aspect(1.2)

        for i, wh in enumerate(WAREHOUSES):
            cs = [c for c in configs if c.measurements[0].query == q and c.measurements[0].warehouse == wh]
            cs.sort(key=lambda x: x.measurements[0].scaling_factor)

            xs = [SCALING_FACTOR_NUMS[c.measurements[0].scaling_factor]
                  for c in cs]
            ys = [c.average_by("elapsed_time") for c in cs]

            marker, facecolor = MARKERS[i]
            plt.loglog(xs, ys, f'-{marker}',
                     markerfacecolor=facecolor, label=WAREHOUSE_LABELS[wh])

        plt.title(f"{QUERY_LABELS[q]} latency")

        plt.ylim(top=y_max)
        plt.legend()
        plt.ylabel("Query Latency (s)")
        plt.xlabel("Scaling Factor")

        save_plot("tpc-h-latency-" + q)

    # ----

    for wh in WAREHOUSES:
        plt.figure()

        for i, q in enumerate(QUERY_LABELS.keys()):
            cs = [c for c in configs if c.measurements[0].query == q and c.measurements[0].warehouse == wh]
            cs.sort(key=lambda x: x.measurements[0].scaling_factor)

            xs = [SCALING_FACTOR_NUMS[c.measurements[0].scaling_factor]
                  for c in cs]
            ys = [c.average_by("elapsed_time") for c in cs]

            marker, facecolor = MARKERS[i]
            plt.loglog(xs, ys, f'-{marker}',
                     markerfacecolor=facecolor, label=QUERY_LABELS[q])

        plt.title(f"Query latencies for {WAREHOUSE_LABELS[wh]} warehouse size")

        plt.ylim(top=y_max)
        plt.legend()
        plt.ylabel("Query Latency (s)")
        plt.xlabel("Scaling Factor")

        save_plot("tpc-h-latency-" + wh)

        # ----

    for scaling_factor in SCALING_FACTOR_NUMS.keys():
        x = np.arange(len(WAREHOUSES))  # the label locations
        width = 1 / len(WAREHOUSES)  # the width of the bars

        fig, ax = plt.subplots(layout="constrained")

        for i, q in enumerate(QUERY_LABELS.keys()):
            cs = [c for c in configs if c.measurements[0].query == q and c.measurements[0].scaling_factor == scaling_factor]
            cs.sort(key=lambda x: WAREHOUSE_ORDER.index(x.measurements[0].warehouse))
            ys = [c.average_by("elapsed_time") for c in cs]

            offset = width * i
            ax.bar(x + offset, ys, width - 0.02, label=QUERY_LABELS[q], zorder=3)

        ax.grid(zorder=0)
        # Add some text for labels, title and custom x-axis tick labels, etc.
        ax.set_ylabel('Latency (seconds)')
        ax.set_title(f'Query latencies across warehouse sizes (scaling factor {SCALING_FACTOR_NUMS[scaling_factor]})')
        ax.set_xticks(x + width, [WAREHOUSE_LABELS[wh] for wh in WAREHOUSES])
        ax.legend(ncols=len(WAREHOUSES))

        save_plot("tpc-h-latency-" + scaling_factor)

def plot_bytes_spilled(configs: list[Configuration]):
    for q in QUERY_LABELS.keys():
        plt.figure()
        ax = plt.gca()

        for i, wh in enumerate(WAREHOUSES):
            cs = [c for c in configs if c.measurements[0].query == q and c.measurements[0].warehouse == wh]
            cs.sort(key=lambda x: x.measurements[0].scaling_factor)

            xs = [SCALING_FACTOR_NUMS[c.measurements[0].scaling_factor]
                  for c in cs]
            ys = [c.average_by("bytes_spilled_local") * 1e-9 for c in cs]

            marker, facecolor = MARKERS[i]
            plt.plot(xs, ys, f'-{marker}',
                     markerfacecolor=facecolor, label=WAREHOUSE_LABELS[wh])

        ax.set_yscale('symlog')
        ax.set_xscale('symlog')

        plt.title(f"Bytes spilled to local storage by {QUERY_LABELS[q]}")

        plt.legend()
        plt.ylabel("Bytes spilled to local storage (GB)")
        plt.xlabel("Scaling Factor")

        save_plot("tpc-h-bytes-" + q)

def make_results_table(configs: list[Configuration]):
    lines = [
        r"\begin{tabular}{llllll}",
        r"\toprule",
        r"Query & Warehouse & Scaling Factor & Avg. Latency & Min. Latency & Max Latency \\",
    ]

    pq = None
    pw = None
    for c in configs:
        q = c.measurements[0].query
        w = c.measurements[0].warehouse

        if pq != q or pw != w:
            lines.append(r"\midrule")
            pq = q
            pw = w

        time = c.average_by('elapsed_time')
        query = QUERY_LABELS[q]
        sf = SCALING_FACTOR_NUMS[c.measurements[0].scaling_factor]
        warehouse = WAREHOUSE_LABELS[c.measurements[0].warehouse]

        min_time = min(m.elapsed_time for m in c.measurements)
        max_time = max(m.elapsed_time for m in c.measurements)

        lines.append(
            rf"{query} & {warehouse} & {sf} & {format_time(time)} & {format_time(min_time)} & {format_time(max_time)} \\")

    lines.append(r"""\bottomrule\end{tabular}""")

    with open(make_out_path("tpc-h-results", "tex"), "w") as f:
        f.write('\n'.join(lines))


def format_time(seconds):
    if seconds > 60:
        return f"{int(seconds // 60)}m {seconds % 60:.1f}s"
    return f"{seconds % 60:.1f}s"


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python plotter.py <bench dir path>")
        exit(1)

    measurements = read_data(sys.argv[1])

    configurations = [Configuration(key=k, measurements=list(g)) for k, g in groupby(
        sorted(measurements, key=lambda x: x.configuration_key()), lambda x: x.configuration_key())]
    configurations.sort(key=lambda x: x.key)

    make_results_table(configurations)
    plot_latency(configurations)
    plot_bytes_spilled(configurations)
