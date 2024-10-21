from typing import Any
from matplotlib.font_manager import json
import matplotlib.pyplot as plt
from dataclasses import dataclass
from itertools import groupby
import sys
import pathlib


def make_out_path(name, format):
    work_dir = pathlib.Path(__file__).parent.resolve()
    out_dir = work_dir / "output" / format
    return out_dir / f"{name}.{format}"


def save_plot(name):
    format = "pdf"
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

    def average_by(self, key: str):
        return sum([getattr(m, key) for m in self.measurements]) / len(self.measurements)


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
