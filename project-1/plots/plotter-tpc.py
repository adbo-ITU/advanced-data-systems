import matplotlib.pyplot as plt
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

    @staticmethod
    def from_file(file: str):
        with open(file) as f:
            lines = f.readlines()
            content = ''.join(lines)

        config_items = [x.split("=", 1) for x in lines[0].strip().split(", ")]
        config = {k: v for k, v in config_items}

        time_match = re.search(
            r"Time Elapsed: (?P<seconds>[\d\.]+)s\nGoodbye!", content).groupdict()
        elapsed = float(time_match["seconds"])

        return Measurement(
            query=config["query"],
            elapsed_time=elapsed,
            warehouse=config["warehouse"],
            repetition=config["repetition"],
            scaling_factor=config["scaling_factor"]
        )

    def configuration_key(self):
        q = f'Q{int(self.query.replace("q", "")):02}'
        return f"{q}-{self.scaling_factor}-{self.warehouse}"


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


def plot_latency(configs: list[Configuration]):
    y_max = max(max(m.elapsed_time for m in c.measurements) for c in configs)

    for q in QUERY_LABELS.keys():
        plt.figure()

        for i, wh in enumerate(WAREHOUSES):
            cs = [c for c in configs if c.measurements[0].query == q and c.measurements[0].warehouse == wh]
            cs.sort(key=lambda x: x.measurements[0].scaling_factor)

            xs = [SCALING_FACTOR_NUMS[c.measurements[0].scaling_factor]
                  for c in cs]
            ys = [c.average_by("elapsed_time") for c in cs]

            marker, facecolor = MARKERS[i]
            plt.loglog(xs, ys, f'-{marker}',
                     markerfacecolor=facecolor, label=WAREHOUSE_LABELS[wh])

        plt.title(f"{QUERY_LABELS[q]} Latency for Different Warehouse sizes and Scaling Factors")

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

curl 'https://cykelgear.dk/reset-password' \
  -H 'accept: application/json, text/plain, */*' \
  -H 'accept-language: en-GB,en-US;q=0.9,en;q=0.8,da;q=0.7' \
  -H 'cache-control: no-cache' \
  -H 'content-type: application/json' \
  -H 'cookie: clerk_visitor=e906ae5cebcaa8cc54978677aa2964e8; CookieInformationConsent=%7B%22website_uuid%22%3A%220469e9fc-0335-4edc-869b-a8991fee915a%22%2C%22timestamp%22%3A%222024-04-25T06%3A51%3A28.448Z%22%2C%22consent_url%22%3A%22https%3A%2F%2Fcykelgear.dk%2F%22%2C%22consent_website%22%3A%22cykelgear.dk%22%2C%22consent_domain%22%3A%22cykelgear.dk%22%2C%22user_uid%22%3A%22cbcb68bb-4148-4097-b12b-149312635a74%22%2C%22consents_approved%22%3A%5B%22cookie_cat_necessary%22%2C%22cookie_cat_functional%22%2C%22cookie_cat_statistic%22%2C%22cookie_cat_marketing%22%2C%22cookie_cat_unclassified%22%5D%2C%22consents_denied%22%3A%5B%5D%2C%22user_agent%22%3A%22Mozilla%2F5.0%20%28Macintosh%3B%20Intel%20Mac%20OS%20X%2010_15_7%29%20AppleWebKit%2F537.36%20%28KHTML%2C%20like%20Gecko%29%20Chrome%2F124.0.0.0%20Safari%2F537.36%22%7D; include_vat=true; XSRF-TOKEN=eyJpdiI6IjRKVGdnWFdvRWEyOEptbUViY3BpNVE9PSIsInZhbHVlIjoiditKSUtYb215Ym9EUG5FTUNsV3RJMXdhSnRZR1FVdlFHczZDTVZ6SEx4MGtFNVBhc2JNTjV4Rm5OQjBadWw1MnN6WHJXOU9pSHNrdDBMcnYwbU5NTTBzaGdoSWNhRzd2cjgybGZOZUpBaDRaYStFWGVlaFNjV3pGdzdxY1BwT3ciLCJtYWMiOiJiNGZmNjZjOGM2YTRmZWUwYzJjYmU1ZWMyYjUzZmFkM2NkMWYyYjUxNzBkMDZlYzE1ZWM1ZGZhZTI4Yzc3ODdlIiwidGFnIjoiIn0%3D; cykelgear_session=eyJpdiI6InpBbW40dkI4dER5ZEZnL2hrbXFuWFE9PSIsInZhbHVlIjoiTFcwYVAxWFdGNWF1MzhFclJ0Rm1CbVpOY08xZGdmL2ZFamVNdVBOQXlia2ZjbVNlSHo5R3BGV1FjbDJKZjVQeHBNckM4Tm5IWm9MRWRiSWVrL0FWT2pNeFViNGZ5ZFl2Q1dBTmVqUHpFckFqWVV0REkwVTZSRG91U3dwWmZVbEsiLCJtYWMiOiIzNzYyYjM2MTM3MmRmMDUxNGMyNTFkYjc4M2ZlOTVmMTVkNDA5NDdiY2Y2Y2U5MDQyN2FkN2M4N2UyMjIzYjAzIiwidGFnIjoiIn0%3D' \
  -H 'dnt: 1' \
  -H 'origin: https://cykelgear.dk' \
  -H 'pragma: no-cache' \
  -H 'priority: u=1, i' \
  -H 'referer: https://cykelgear.dk/password-reset/1081ca7044a3fd6b26b885d024ab8486906cabd8312a3faa978ebdf3f1e93fae?email=avborup+cykelgear@gmail.com' \
  -H 'sec-ch-ua: "Chromium";v="129", "Not=A?Brand";v="8"' \
  -H 'sec-ch-ua-mobile: ?0' \
  -H 'sec-ch-ua-platform: "macOS"' \
  -H 'sec-fetch-dest: empty' \
  -H 'sec-fetch-mode: cors' \
  -H 'sec-fetch-site: same-origin' \
  -H 'user-agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36' \
  -H 'x-requested-with: XMLHttpRequest' \
  -H 'x-xsrf-token: eyJpdiI6IjRKVGdnWFdvRWEyOEptbUViY3BpNVE9PSIsInZhbHVlIjoiditKSUtYb215Ym9EUG5FTUNsV3RJMXdhSnRZR1FVdlFHczZDTVZ6SEx4MGtFNVBhc2JNTjV4Rm5OQjBadWw1MnN6WHJXOU9pSHNrdDBMcnYwbU5NTTBzaGdoSWNhRzd2cjgybGZOZUpBaDRaYStFWGVlaFNjV3pGdzdxY1BwT3ciLCJtYWMiOiJiNGZmNjZjOGM2YTRmZWUwYzJjYmU1ZWMyYjUzZmFkM2NkMWYyYjUxNzBkMDZlYzE1ZWM1ZGZhZTI4Yzc3ODdlIiwidGFnIjoiIn0=' \
  --data-raw '{"token":"1081ca7044a3fd6b26b885d024ab8486906cabd8312a3faa978ebdf3f1e93fae","customers_email_address":"avborup+cykelgear@gmail.com","customers_password":"Kptd$2%D3f4CQd","customers_password_confirmation":"Kptd$2%D3f4CQd","isDirty":true,"errors":{},"hasErrors":false,"processing":false,"progress":null,"wasSuccessful":false,"recentlySuccessful":false,"__rememberable":true}'



def make_results_table(configs: list[Configuration]):
    lines = [
        r"\begin{tabular}{llllll}",
        r"\toprule",
        r"Query & Scaling Factor & Warehouse & Avg. Latency & Min. Latency & Max Latency \\",
    ]

    pq = None
    for c in configs:
        q = c.measurements[0].query

        if pq != q:
            lines.append(r"\midrule")
            pq = q

        time = c.average_by('elapsed_time')
        query = QUERY_LABELS[q]
        sf = SCALING_FACTOR_NUMS[c.measurements[0].scaling_factor]
        warehouse = WAREHOUSE_LABELS[c.measurements[0].warehouse]

        min_time = min(m.elapsed_time for m in c.measurements)
        max_time = max(m.elapsed_time for m in c.measurements)

        lines.append(
            rf"{query} & {sf} & {warehouse} & {format_time(time)} & {format_time(min_time)} & {format_time(max_time)} \\")

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
