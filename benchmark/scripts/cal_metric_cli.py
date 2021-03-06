#!/usr/bin/env python3 

import argparse 
import json 


def _collect_perf_metric(metric_dict, metric_name):
    count = 0
    for k, v in metric_dict.items():
        # if k.startswith("dram_bank") and isinstance(v, dict):
        #    count += v[metric_name]
        if k == metric_name:
            count += v
        elif isinstance(v, dict):
            count += _collect_perf_metric(v, metric_name)
    return count 


def main():

    parser = argparse.ArgumentParser(
        description="Collect the performance metric from the perf trace file",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter 
    )

    parser.add_argument("perf_trace_file", help="Input performance trace "
                        "files generated by the MPU simulator")
    parser.add_argument("metric_name", help="The performance metric to "
                        "collect through the performance trace file")

    args = parser.parse_args() 

    with open(args.perf_trace_file, "r") as f:
        perf_metrics = json.load(f)

    count = _collect_perf_metric(perf_metrics, args.metric_name)

    print("Collected the metric {} from the file {}:".format(
        args.metric_name, args.perf_trace_file))
    print(count)


if __name__ == "__main__":
    main() 
