from typing import Any
from matplotlib.font_manager import json
import matplotlib.pyplot as plt
from dataclasses import dataclass
from itertools import groupby
import sys
import pathlib


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
    query: str
    threads: str
    scaling_factor: str
    elapsed_time: float
    profile: Any

    @staticmethod
    def from_file(file: str):
        profilings = []
        with open(file) as f:
            buffer = []

            for line in f:
                buffer.append(line)

                if line.rstrip() == "}":
                    profile = json.loads(''.join(buffer))
                    profilings.append(profile)
                    buffer.clear()

        measurements = []
        for profile in profilings:
            q_str, sf_str, t_str = profile["benchmark_name"].split("_")
            measurements.append(Measurement(
                query=q_str.replace("q", ""),
                scaling_factor=sf_str.replace("sf", ""),
                threads=t_str.replace("threads", ""),
                elapsed_time=profile["operator_timing"],
                profile=profile
            ))

        return measurements

    def configuration_key(self):
        return self.profile["benchmark_name"]


@dataclass
class Configuration:
    key: str
    measurements: list[Measurement]
    query: str = ""
    threads: int = -1
    scaling_factor: int = -1

    def __post_init__(self):
        self.query = self.measurements[0].query
        self.threads = int(self.measurements[0].threads)
        self.scaling_factor = int(self.measurements[0].scaling_factor)

    def average_by(self, key: str):
        return sum([getattr(m, key) for m in self.measurements]) / len(self.measurements)


def get_queries(configs: list[Configuration]):
    return sorted(set(c.query for c in configs))


def get_threads(configs: list[Configuration]):
    return sorted(set(c.threads for c in configs))


def get_scaling_factors(configs: list[Configuration]):
    return sorted(set(c.scaling_factor for c in configs))


def plot_latency(configs: list[Configuration]):
    # y_max = max(max(m.elapsed_time for m in c.measurements) for c in configs)

    for q in get_queries(configs):
        plt.figure()
        ax = plt.gca()

        for i, t in enumerate(get_threads(configs)):
            cs = [c for c in configs if c.query == q and c.threads == t]
            cs.sort(key=lambda x: x.scaling_factor)

            xs = [c.scaling_factor for c in cs]
            ys = [c.average_by("elapsed_time") for c in cs]

            marker, facecolor = MARKERS[i]
            plt.loglog(xs, ys, f'-{marker}',
                       markerfacecolor=facecolor, label=f"{t} threads")

        plt.title(f"Query {q} latency")

        plt.legend()
        plt.ylabel("Query Latency (s)")
        plt.xlabel("Scaling Factor")

        save_plot("latency-q" + q)


def read_data(file):
    rows = Measurement.from_file(file)
    print(f"Loaded {len(rows)} experiments")
    return rows


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python plotter.py <bench file path>")
        exit(1)

    measurements = read_data(sys.argv[1])

    configurations = [Configuration(key=k, measurements=list(g)) for k, g in groupby(
        sorted(measurements, key=lambda x: x.configuration_key()), lambda x: x.configuration_key())]
    configurations.sort(key=lambda x: x.key)

    REPETITIONS = 5
    for c in configurations:
        if len(c.measurements) != REPETITIONS:
            print(f"Missing measurements for {c.key}, only has {len(c.measurements)}")
            break
    else:
        print(f"All configurations have {REPETITIONS} repetitions, good")

    plot_latency(configurations)
