# Visualize the Results of Speedups of Automatic Parallelization Frameworks

This visualizer framework visualizes the speedup in an interactive format.
Users can understand the speedups in multiple aspects (estimated speedup, real
speedups, speedup loop breakdown, multiple techniques comparison).  Please
check out [the full running example](http://13.58.206.207:8050) to see its
capabilities.

Currently, only RealSpeedup feature is documented here.

## Current Users

- [CPF](https://github.com/PrincetonUniversity/cpf)
- [NOELLE](https://github.com/scampanoni/noelle)

## Quick Guide 

- Set up the Python3 environment
- Install requirements by `pip3 install -r requirements.txt`
- [Set up results directory](#set-up-results-directory)
- Run the visualizer by `python3 ResultPresenter.py -r PATH/TO/RESULTS -p PORT_NUM`
- View the results at `http://localhost:PORT_NUM`

## Set Up Results Directory

The visualizer parses the file structure and json files to load parallelization
results.  It also uses another optional json file
(`MATCHING_DIRECTORY_NAME.log`) file to record metadata of the run.

As shown below, Each directory under results represents a run (the directory
name can be the date or other more representatitve names), inside the
directory, the visualize tries to find a status.json file, the structure of
which is described [next](#status-json-file-structure).

```
results
├── 2021-04-26
│   └── status.json
├── (optional) 2021-04-26.log
└── 2021-04-27
    └── status.json
...
```

## Status Json File Structure 

The bare minimal of the json file to use the speedup bar plot feature is as
shown below. It is a map of benchmark names to speedups.  The speedup key is
required, while `seq_time` and `para_time` keys are optional (they are used to
show exact time when hover on the bar).

```json
{
  "benchmark1": {
      "RealSpeedup": {
        "seq_time": #float,
        "para_time": #float,
        "speedup": #float,
      }
  }
}
```

Example: 

``` json
{"correlation": {"RealSpeedup": {"seq_time": 642.647, "para_time": 39.847, "speedup": 16.13}},
 "swaptions": {"RealSpeedup": {"seq_time": 1214.318, "para_time": 57.434, "speedup": 21.14}},
 "2mm": {"RealSpeedup": {"seq_time": 1615.038, "para_time": 87.248, "speedup": 18.51}},
 "blackscholes": {"RealSpeedup": {"seq_time": 3408.095, "para_time": 185.741, "speedup": 18.35}},
 "3mm": {"RealSpeedup": {"seq_time": 2581.376, "para_time": 138.171, "speedup": 18.68}},
 "052.alvinn": {"RealSpeedup": {"seq_time": 1077.882, "para_time": 165.555, "speedup": 6.51}},
 "covariance": {"RealSpeedup": {"seq_time": 713.114, "para_time": 94.867, "speedup": 7.52}},
 "gemm": {"RealSpeedup": {"seq_time": 821.948, "para_time": 44.451, "speedup": 18.49}},
 "doitgen": {"RealSpeedup": {"seq_time": 138.632, "para_time": 10.215, "speedup": 13.57}}
} 
```

