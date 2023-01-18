# Python 3
#
# Ziyang Xu
# May 1, 2019
#
# Present the results in HTML, plots,
# and a bunch of interesting stuff

import argparse
import os
import json
import numpy as np
import dash
from dash import dcc, html
import plotly.graph_objects as go
from VisualizeCoverage import getCdfFig

# Geometric mean helper
def geo_mean_overflow(iterable):
    a = np.log(iterable)
    return np.exp(a.sum() / len(a))


class ResultProvider:

    def __init__(self, path):
        self._path = path

    def getPriorResults(self, bmark_list):
        prior_file = "prior_results.json"
        with open(prior_file, 'r') as fd:
            prior_results = json.load(fd)

        speedup_list = []
        text_list = []
        for bmark in bmark_list:
            if bmark in prior_results:
                result = prior_results[bmark][0]
                speedup = result['speedup']
                text = "on %d cores from %s " % (
                    result['cores'], result['paper'])
                speedup_list.append(speedup)
                text_list.append(text)

        return speedup_list, text_list

    def getSequentialData(self, bmark_list, date_list):
        # Newer result overwrite old result
        result_dict = {}
        for date in date_list:
            status_path = os.path.join(self._path, date, "status.json")
            with open(status_path, "r") as fd:
                status = json.load(fd)

            for bmark in bmark_list:
                if bmark in status and "RealSpeedup" in status[bmark]:
                    real_speedup = status[bmark]["RealSpeedup"]
                    if not real_speedup:
                        continue

                    if "seq_time" not in real_speedup:
                        continue

                    result_dict[bmark] = real_speedup["seq_time"]

        return result_dict

    def getParallelData(self, bmark_list, date_list):

        para_time_dict = {}
        for date in date_list:
            status_path = os.path.join(self._path, date, "status.json")
            with open(status_path, "r") as fd:
                status = json.load(fd)

            for bmark in bmark_list:
                if bmark in status and "RealSpeedup" in status[bmark]:
                    real_speedup = status[bmark]["RealSpeedup"]
                    if not real_speedup or 'para_time' not in real_speedup:
                        continue

                    para_time_dict[bmark] = real_speedup['para_time']

        return para_time_dict

    def getRealSpeedup(self, bmark_list, date_list):
        prior_speedup_list, prior_text_list = self.getPriorResults(bmark_list)

        bar_list = [{'x': bmark_list, 'y': prior_speedup_list,
                     'text': prior_text_list, 'type': 'bar', 'name': "Best Prior Result"}]

        for date in date_list:
            status_path = os.path.join(self._path, date, "status.json")
            with open(status_path, "r") as fd:
                status = json.load(fd)

            have_results_bmark_list = []
            real_speedup_list = []
            text_list = []
            for bmark in bmark_list:
                if bmark in status and "RealSpeedup" in status[bmark]:
                    real_speedup = status[bmark]["RealSpeedup"]
                    if not real_speedup:
                        continue
                    have_results_bmark_list.append(bmark)
                    real_speedup_list.append(real_speedup['speedup'])
                    text_list.append("Seq time: %s, para time: %s" % (
                        round(real_speedup['seq_time'], 2), round(real_speedup['para_time'], 2)))

            bar_list.append({'x': have_results_bmark_list, 'y': real_speedup_list,
                             'text': text_list, 'type': 'bar', 'name': "Results from" + date})
        return bar_list

    def updateResult(self, date_list):
        all_reg_results = {}

        for date in date_list:
            date_path = os.path.join(self._path, date)
            all_status = {}
            for filename in os.listdir(date_path):
                if filename.endswith(".json") and filename.startswith("status"):
                    with open(os.path.join(date_path, filename), 'r') as fd:
                        status = json.load(fd)
                        bmark = filename.replace(
                            "status_", "").replace(".json", "")
                        all_status[bmark] = status

            all_reg_results[date] = all_status
        self._all_reg_results = all_reg_results

    def getMultiCoreData(self, bmark_list, date_list):

        # Newer result overwrite old result
        result_dict = {}
        for date in date_list:
            status_path = os.path.join(self._path, date, "status.json")
            with open(status_path, "r") as fd:
                status = json.load(fd)

            for bmark in bmark_list:
                if bmark in status and "RealSpeedup" in status[bmark]:
                    real_speedup = status[bmark]["RealSpeedup"]
                    if not real_speedup:
                        continue

                    if "para_time_dict" not in real_speedup:
                        continue

                    para_time_dict = real_speedup["para_time_dict"]
                    x_list = []
                    y_list = []
                    for x, y in para_time_dict.items():
                        x_list.append(int(x))
                        y_list.append(y)
                    x_list, y_list = (list(t)
                                      for t in zip(*sorted(zip(x_list, y_list))))

                    result_dict[bmark] = [x_list, y_list]

        return result_dict

    def getLoopData(self, bmark):

        date_list = ['2019-06-08']
        self.updateResult(date_list)
        # TODO: fake result, only 05-22
        if bmark not in self._all_reg_results['2019-06-08']:
            print(bmark + " not exists")
            return None

        status = self._all_reg_results['2019-06-08'][bmark]
        if 'Experiment' in status and status['Experiment']:
            status = status['Experiment']
            if "speedup" not in status or "loops" not in status:
                print("NO Speedup or loops")
                return None
        else:
            return None

        speedup = status['speedup']
        loops = status['loops']

        the_rest = 100
        para_whole = 100 / speedup
        para_the_rest = para_whole

        data = []

        for loop, loop_info in loops.items():
            if 'selected' in loop_info and loop_info['selected']:
                if 'loop_speedup' in loop_info:
                    exec_coverage = loop_info['exec_coverage']
                    the_rest -= exec_coverage

                    loop_speedup = loop_info['loop_speedup']
                    para_coverage = exec_coverage / loop_speedup

                    para_the_rest -= para_coverage
                    data.append(go.Bar(
                        x=['Sequential', 'Parallel'],
                        y=[exec_coverage, para_coverage],
                        name=loop
                    ))

        data.append(go.Bar(
            x=['Sequential', 'Parallel'],
            y=[the_rest, para_the_rest],
            name='The Rest'
        ))

        return data
 
    def getSpeedupExp3(self, date_list, speedup_threshold=2.0):
        self.updateResult(date_list)
        speedup_bar_list = []

        def getMemo(date):
            # if exist .log file
            log_path = self._path + date + '.log'
            if not os.path.exists(log_path):
                log_path = self._path + date + "/config.json"
            if not os.path.exists(log_path):
                return "No Log File"

            with open(log_path) as fd:
                obj = json.load(fd)
                if 'memo' in obj:
                    return obj['memo']
                else:
                    return "No Memo"

        def update_list(x_list, y_list, date, exp_key):
            # sort two list together
            y_list, x_list = (list(t)
                              for t in zip(*sorted(zip(y_list, x_list))))

            geomean = geo_mean_overflow(y_list)
            x_list.append("geomean")
            y_list.append(geomean)
            # y_list = list(map(lambda x: x - 1, y_list))
            return {'x': x_list, 'y': y_list, 'type': 'bar',
                    'name': date[5:] + " " + exp_key[11:] + " " + getMemo(date)}

        for date in date_list:
            reg_results = self._all_reg_results[date]
            #exps = [ "Experiment-no-spec", "Experiment-cheap-spec", "Experiment-all-spec", "Experiment-no-specpriv"]
            # exps = [ "Experiment-no-spec", "Experiment-cheap-spec", "Experiment-all-spec"]
            exps = [ "Experiment-no-spec", "Experiment-no-specpriv", "Exp-slamp"]
            for exp_key in exps:
                x_list = []
                y_list = []
                for bmark, status in reg_results.items():
                    if exp_key in status and status[exp_key]:
                        if 'speedup' in status[exp_key]:
                            x_list.append(bmark)
                            y_list.append(status[exp_key]['speedup'])
                            if status[exp_key]['speedup'] < speedup_threshold:
                                continue
                if len(x_list) > 0:
                    speedup_bar_list.append(update_list(x_list, y_list, date, exp_key))


        return speedup_bar_list

    def getSpeedupData(self, date_list, speedup_threshold=2.0):
        self.updateResult(date_list)
        speedup_bar_list = []
        speedup_bar_list_DOALL_only = []
        speedup_bar_list_without_DOALL = []

        def update_list(x_list, y_list, date):
            # sort two list together
            y_list, x_list = (list(t)
                              for t in zip(*sorted(zip(y_list, x_list))))

            geomean = geo_mean_overflow(y_list)
            x_list.append("geomean")
            y_list.append(geomean)
            # y_list = list(map(lambda x: x - 1, y_list))
            return {'x': x_list, 'y': y_list, 'type': 'bar',
                    'name': 'speedup for' + date}

        for date, reg_results in self._all_reg_results.items():
            x_list = []
            y_list = []
            x_list_DOALL = []
            y_list_DOALL = []
            x_list_no_DOALL = []
            y_list_no_DOALL = []
            for bmark, status in reg_results.items():
                if 'Experiment' in status and status['Experiment']:
                    if 'speedup' in status['Experiment']:
                        x_list.append(bmark)
                        y_list.append(status['Experiment']['speedup'])
                        if status['Experiment']['speedup'] < speedup_threshold:
                            continue
                        if 'loops' in status['Experiment']:
                            DOALL_only = True
                            for name, loop_status in status['Experiment']['loops'].items():
                                if 'selected' in loop_status and not loop_status['selected']:
                                    continue
                                if 'loop_stage' in loop_status and "P22" not in loop_status['loop_stage']:
                                    DOALL_only = False
                                    break
                            if DOALL_only:
                                x_list_DOALL.append(bmark)
                                y_list_DOALL.append(
                                    status['Experiment']['speedup'])
                            else:
                                x_list_no_DOALL.append(bmark)
                                y_list_no_DOALL.append(
                                    status['Experiment']['speedup'])

            speedup_bar_list.append(update_list(x_list, y_list, date))
            speedup_bar_list_DOALL_only.append(update_list(x_list_DOALL,
                                                           y_list_DOALL, date))
            if x_list_no_DOALL:
                speedup_bar_list_without_DOALL.append(update_list(x_list_no_DOALL,
                                                                  y_list_no_DOALL, date))

        return speedup_bar_list, speedup_bar_list_DOALL_only, speedup_bar_list_without_DOALL

    # Need to resolve nested loops issue
    def getLoopsDataForOneBmark(self, loops):
        raise NotImplementedError()
        loop_names = []
        for loop_name, loop_info in loops.items():
            loop_names.append(loop_name)


def parseArgs():
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--root_path", type=str, required=True,
                        help="Root path of CPF benchmark directory")
    args = parser.parse_args()

    return args.root_path


# some setting for plot
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
app.config.suppress_callback_exceptions = True


def getRealSpeedupLayout(resultProvider):
    bmark_list = ["correlation", "2mm", "3mm", "covariance", "gemm", "doitgen", "swaptions",
                  "blackscholes", "052.alvinn", "enc-md5", "dijkstra-dynsize", "179.art"]
    date_list = ["2019-06-27", "2019-07-01", "2019-07-06", "2019-07-08"]
    data_real_speedup = resultProvider.getRealSpeedup(bmark_list, date_list)
    layout = [html.Div(children='''
            Real Speedup on 24 cores (Average of 3 runs)
        '''),

              # Data Layout:
              # [
              #     {'x': [1, 2, 3], 'y': [4, 1, 2], 'type': 'bar', 'name': 'SF'},
              #     {'x': [1, 2, 3], 'y': [2, 4, 5], 'type': 'bar', 'name': 'Montréal'},
              # ]

              dcc.Graph(
        id='real-speed-graph',
        figure={
            'data': data_real_speedup,
            'layout': {
                'title': 'Real Speedup'
            }
        }
    )]

    return layout


def getComparePrivateerLayout(resultProvider):
    bmark_list = ["correlation", "2mm", "3mm", "covariance", "gemm", "doitgen", "swaptions",
                  "blackscholes", "052.alvinn", "enc-md5", "dijkstra-dynsize", "179.art"]
    spec_list = ["blackscholes", "052.alvinn", "enc-md5", "dijkstra-dynsize", "179.art"]
    perspective_time_list = ["2019-08-05-18-54"]
    privateer_peep_time_list = ["2019-08-06-15-03"]
    privateer_both_time_list = ["2019-08-07-00-38"]
    perspective_SAMA_time_list = ["2019-08-09-01-52"]
    perspective_cheap_priv_time_list = ["2019-08-13-21-23", "2019-08-13-22-41", "2019-08-14-14-27"]
    # perspective_cheap_priv_time_list = ["2019-08-12-17-22"]
    seq_date_list = ['2019-07-02', '2019-07-28', '2019-08-05-12-41', '2019-08-05-16-14']
    seq_data = resultProvider.getSequentialData(bmark_list, seq_date_list)

    def getOneBar(time_list, bar_name, color):
        one_para_data = resultProvider.getParallelData(bmark_list, time_list)

        one_bmark_list = []
        one_speedup_list = []
        one_text_list = []
        one_spec_speedup_list = []
        one_nonspec_speedup_list = []
        for bmark, para_time in one_para_data.items():
            if bmark not in seq_data:
                continue
            if bmark == "dijkstra-dynsize":
                one_bmark_list.append("dijkstra")
            else:
                one_bmark_list.append(bmark)
            seq_time = seq_data[bmark]
            speedup = round(seq_time / para_time, 2)
            one_speedup_list.append(speedup)
            if bmark in spec_list:
                one_spec_speedup_list.append(speedup)
            else:
                one_nonspec_speedup_list.append(speedup)
            one_text_list.append("Seq time: %s, para time: %s" %
                                  (round(seq_time, 2),
                                   round(para_time, 2)))
        one_speedup_list.append(geo_mean_overflow(one_speedup_list))
        one_bmark_list.append("Geomean")
        one_text_list.append("Geomean")

        # one_speedup_list.append(geo_mean_overflow(one_spec_speedup_list))
        # one_bmark_list.append("Spec Geomean")
        # one_text_list.append("Spec Geomean")

        # one_speedup_list.append(geo_mean_overflow(one_nonspec_speedup_list))
        # one_bmark_list.append("Nonspec Geomean")
        # one_text_list.append("Nonspec Geomean")

        bar_one = {'x': one_bmark_list, 'y': one_speedup_list, 'text': one_text_list,
                   'type': 'bar', 'name': bar_name, 'marker_color': color}
        return bar_one

    def getOneBarSpeedup(speedup_dict, bar_name, color):
        one_bmark_list = []
        one_speedup_list = []

        for bmark in bmark_list:
            if bmark == "dijkstra-dynsize":
                one_bmark_list.append("dijkstra")
            else:
                one_bmark_list.append(bmark)
            one_speedup_list.append(speedup_dict[bmark])

        one_text_list = one_speedup_list

        one_speedup_list.append(geo_mean_overflow(one_speedup_list))
        one_bmark_list.append("Geomean")
        one_text_list.append("Geomean")
        bar_one = {'x': one_bmark_list, 'y': one_speedup_list, 'text': one_text_list,
                   'type': 'bar', 'name': bar_name, 'marker_color': color}
        return bar_one

    #bar_privateer_peep = getOneBar(privateer_peep_time_list, "Privateer", '#ca0020')
    #bar_privateer_both = getOneBar(privateer_both_time_list, "Per<i>spec</i>tive (Planner Only)", '#f4a582')
    ## bar_perspective_SAMA = getOneBar(perspective_SAMA_time_list, "Per<i>spec</i>tive Speculative-Aware-Memory-Analysis", '#92c5de')
    #bar_perspective_cheap_priv = getOneBar(perspective_cheap_priv_time_list, "Per<i>spec</i>tive (Planner + Efficient SpecPriv)", '#abd9e9')
    #bar_perspective = getOneBar(perspective_time_list, "Per<i>spec</i>tive (Planner + Efficient SpecPriv +SAMA)", '#0571b0')
    #
    #bar_list = [bar_privateer_peep, bar_privateer_both, bar_perspective_cheap_priv, bar_perspective]

    icc_speedup_dict = {
            "correlation": 1.0,
            "2mm": 17.4,
            "3mm": 17.7,
            "covariance": 1.0, 
            "gemm": 15.3,
            "doitgen": 20.6,
            "swaptions": 1.0,
            "blackscholes": 1.151,
            "052.alvinn": 1.0,
            "enc-md5": 1.0,
            "dijkstra-dynsize": 1.0,
            "179.art": 1.0
            }

    gcc_speedup_dict = {
            "correlation": 1.0,
            "2mm": 1.149,
            "3mm": 1.129,
            "covariance": 1.196, 
            "gemm": 1.156,
            "doitgen": 1.138,
            "swaptions": 1.147,
            "blackscholes": 1.0,
            "052.alvinn": 1.0,
            "enc-md5": 1.0,
            "dijkstra-dynsize": 1.0,
            "179.art": 1.0
            }
    #bar_privateer_peep = getOneBar(privateer_peep_time_list, "Privateer", '#ca0020')
    bar_gcc = getOneBarSpeedup(gcc_speedup_dict, "GCC", '#f4a582')
    bar_icc = getOneBarSpeedup(icc_speedup_dict, "ICC", '#ca0020')#'#abd9e9')
    bar_privateer_peep = getOneBar(privateer_peep_time_list, "Privateer", '#abd9e9') #'#ca0020')
    bar_privateer_both = getOneBar(privateer_both_time_list, "Per<i>spec</i>tive (Planner Only)", '#92c5de')
    ## bar_perspective_SAMA = getOneBar(perspective_SAMA_time_list, "Per<i>spec</i>tive Speculative-Aware-Memory-Analysis", '#92c5de')
    bar_perspective_cheap_priv = getOneBar(perspective_cheap_priv_time_list, "Per<i>spec</i>tive (Planner + Efficient SpecPriv)", '#20a0de')
    # bar_perspective_SAMA = getOneBar(perspective_SAMA_time_list, "Per<i>spec</i>tive Speculative-Aware-Memory-Analysis", '#92c5de')
    bar_perspective = getOneBar(perspective_time_list, "Per<i>spec</i>tive (Planner + Efficient SpecPriv +SAMA)", '#0571b0')
    #bar_perspective = getOneBar(perspective_time_list, "Per<i>spec</i>tive", '#0571b0')
    
    bar_list = [bar_gcc, bar_icc, bar_privateer_peep, bar_privateer_both, bar_perspective_cheap_priv,  bar_perspective]

    fig = go.Figure({
                    'data': bar_list,
                    'layout': {
                        # 'title': 'Parallel Execution Comparison',
                        'legend': {'orientation': 'h', 'x': 0.2, 'y': 1.35},
                        'yaxis': {
                            'showline': True, 
                            'linewidth': 2,
                            'ticks': "inside",
                            'mirror': 'all',
                            'linecolor': 'black',
                            'gridcolor':'rgb(200,200,200)', 
                            'range': [0, 28.5],
                            'nticks': 15,
                            'title': {'text': "Whole Program Speedup over Sequential"},
                            'ticksuffix': "x",
                        },
                        'xaxis': {
                            'linecolor': 'black',
                            'showline': True, 
                            'linewidth': 2,
                            'mirror': 'all'
                        },
                        'font': {'family': 'Helvetica', 'color': "Black"},
                        'plot_bgcolor': 'white',
                        'autosize': False,
                        'width': 900, 
                        'height': 400}
                    })

    #fig.write_image("images/fig_compare_new.pdf")
    layout = [html.Div(children='''
            Compare Parallel Runtime with Privateer on 28 cores (Average of 5 runs)
        '''),

              dcc.Graph(
        id='privateer-compare-graph',
        figure=fig
    )]

    return layout


def getEstimatedSpeedupLayoutExp3(resultProvider):
    # no change  '2021-06-01-16-19','2021-06-02-00-36',
    #date_list = ['2021-05-20-18-41', '2021-05-25-00-28', '2021-05-25-20-03',  '2021-06-03-11-47', '2021-06-03-18-39', '2021-06-08-00-14', '2021-06-08-22-36', '2021-06-21-17-44', '2021-07-07-21-43', '2021-09-28-15-59']
    #date_list = ['2021-05-20-18-41', '2021-05-25-00-28', '2021-05-25-20-03',  '2021-06-03-11-47', '2021-06-03-18-39', '2021-06-08-00-14', '2021-06-08-22-36', '2021-06-21-17-44', '2021-07-07-21-43', '2021-09-28-15-59', '2021-10-25-21-23']
    date_list = ['2021-10-25-21-23', '2022-09-12-18-02']

    data_speedup_exp3 = resultProvider.getSpeedupExp3(date_list, 1.0)

    fig = go.Figure({
        'data': data_speedup_exp3,
        'layout': {
            'title': 'Speedup',
            'yaxis': {
                'showline': True, 
                'linewidth': 2,
                'ticks': "inside",
                'mirror': 'all',
                'linecolor': 'black',
                'gridcolor':'rgb(200,200,200)', 
                'range': [0, 28.5],
                'nticks': 15,
                'title': {'text': "Whole Program Speedup over Sequential"},
                'ticksuffix': "x",
                },
            'xaxis': {
                'linecolor': 'black',
                'showline': True, 
                'linewidth': 2,
                'mirror': 'all'
                },
            'font': {'family': 'Helvetica', 'color': "Black"},
            'plot_bgcolor': 'white',
            }
        })

    fig.add_hline(y=1.0)
    
    layout_speedup = [html.Div(children='''
            Estimated Speedup on 22 cores
        '''),

        # Data Layout:
        # [
        #     {'x': [1, 2, 3], 'y': [4, 1, 2], 'type': 'bar', 'name': 'SF'},
        #     {'x': [1, 2, 3], 'y': [2, 4, 5], 'type': 'bar', 'name': 'Montréal'},
        # ]

        dcc.Graph(
            id='speed-graph',
            figure=fig
            )]

    return layout_speedup


def getEstimatedSpeedupLayout(resultProvider):
    date_list = ['2019-04-28', '2019-05-20', '2019-05-22',
                 '2019-06-04', '2019-06-06', '2019-06-08',
                 '2020-08-14-00-17', '2021-02-22-12-22',
                 '2021-03-01-00-19', '2021-03-04-00-18',
                 '2021-03-05-00-19', '2021-03-07-00-19',
                 '2021-03-09-00-20', '2021-03-11-00-20',
                 '2021-03-15-19-31', '2021-03-16-01-20',
                 '2021-03-18-01-21', '2021-03-26-01-54']

    data_speedup, data_speedup_DOALL, data_speedup_no_DOALL = resultProvider.getSpeedupData(
        date_list, 1.0)

    layout = [html.H1(children='CPF Estimated Speedup Result')]

    layout_speedup = [html.Div(children='''
            Estimated Speedup on 22 cores
        '''),

                      # Data Layout:
                      # [
                      #     {'x': [1, 2, 3], 'y': [4, 1, 2], 'type': 'bar', 'name': 'SF'},
                      #     {'x': [1, 2, 3], 'y': [2, 4, 5], 'type': 'bar', 'name': 'Montréal'},
                      # ]

                      dcc.Graph(
        id='speed-graph',
        figure={
            'data': data_speedup,
            'layout': {
                'title': 'Speedup'
            }
        }
    )]

    layout_speedup_DOALL = [html.Div(children='''
            Estimated Speedup on 22 cores
        '''),
                            dcc.Graph(
        id='speed-graph-DOALL',
        figure={
            'data': data_speedup_DOALL,
            'layout': {
                'title': 'Speedup DOALL Only'
            }
        }
    )]

    layout_speedup_no_DOALL = [html.Div(children='''
            Estimated Speedup on 22 cores
        '''),
                               dcc.Graph(
        id='speed-graph-noDOALL',
        figure={
            'data': data_speedup_no_DOALL,
            'layout': {
                'title': 'Speedup DSWP (excluding DOALL only)'
            }
        }
    )]

    if layout_speedup:
        layout += layout_speedup

    if layout_speedup_DOALL:
        layout += layout_speedup_DOALL

    if layout_speedup_no_DOALL:
        layout += layout_speedup_no_DOALL

    return layout


def getOneBenchmarkLayout(resultProvider, bmark):
    data_bmark = resultProvider.getLoopData(bmark)
    if data_bmark is not None:
        layout = [html.Div(children='Speedup breakdown of ' + bmark),

                  dcc.Graph(
            id='bmark-graph',
            figure={
                'data': data_bmark,
                'layout': {
                    'title': 'Execution Time Breakdown',
                    'barmode': 'stack'
                }
            }
        )]
    else:
        layout = None

    return layout


def getMultiCoreLayout(resultProvider):
    bmark_list = ["enc-md5", "dijkstra-dynsize", "swaptions", "doitgen", "gemm", "blackscholes", "2mm",
                  "3mm", "179.art", "correlation", "covariance", "052.alvinn"]
    parallel_date_list = ['2019-07-26', '2019-07-27', '2019-07-30', '2019-08-05', '2019-08-06-02-43', '2019-08-10-02-33', '2019-08-11-02-09']
    seq_date_list = ['2019-07-02', '2019-07-28', '2019-08-05-12-41', '2019-08-05-16-14']

    fig = go.Figure()

    multicore_data = resultProvider.getMultiCoreData(
        bmark_list, parallel_date_list)
    seq_data = resultProvider.getSequentialData(bmark_list, seq_date_list)

    color_list =['#a6cee3', '#ffff99', '#1f78b4', '#6a3d9a','#fb9a99',
                 '#fdbf6f','#cab2d6', '#ff7f00', '#b2df8a', '#e31a1c',
                 '#33a02c','#b15928']
    shape_list = ["star", "star-square", "cross", "circle",
                  "square", "square-open", "circle-open", "x",
                  "triangle-up", "triangle-up-open", "diamond", "diamond-open"]
    fig.update_xaxes(range=[1, 28], showgrid=True, gridwidth=1, nticks=28,
                     title_text="Number of Cores", showline=True, linewidth=2, ticks="inside",
                     linecolor='black', gridcolor='rgb(200,200,200)', mirror='all', layer="below traces")
    fig.update_yaxes(range=[0, 28], showgrid=True, gridwidth=1, nticks=29, title_text="Whole Program Speedup over Sequential", ticks="inside",
                     showline=True, linewidth=2, linecolor='black', gridcolor='rgb(200,200,200)', mirror='all', ticksuffix="x", layer="below traces")
 
    for bmark in bmark_list:
        if bmark not in multicore_data:
            continue
        result =  multicore_data[bmark]
        x_list, y_list = result
        seq_time = seq_data[bmark]
        speedup_list = [seq_time / x for x in y_list]
        shape = shape_list.pop()
        color = color_list.pop()
        fig.add_trace(go.Scatter(x=x_list, y=speedup_list,
                      mode='lines+markers', line={'width': 1},
                      marker={"symbol": shape, "size": 8, 'opacity': 0.9},
                                     name=bmark))

    fig.update_layout(autosize=False,
                      width=1000, height=500,
                      plot_bgcolor='white',
                      font={'family': 'Helvetica', 'color': 'Black'},
                      legend=go.layout.Legend(
                          x=0.01,
                          y=0.98,
                          traceorder="normal",
                          bgcolor="White",
                          bordercolor="Black",
                          borderwidth=2))

    # fig.update_layout(title=go.layout.Title(text="Differnt Cores"))
    # fig.write_image("images/fig_multi_core.svg")

    layout = [html.Div(children='''
            Multiple Core Speedup Results
        '''),
              dcc.Graph(
        id='multicore-speedup-graph',
        figure=fig
    )]

    return layout


def getCoverageDatePickerLayout():
    dates = ["2022-01-27-16-37", "2022-02-10-16-12", "2022-02-17-20-36", "2022-03-01-17-27"]

    def getLatestDir(path):
        dates = []
        dirs = [d for d in os.listdir(path) if os.path.isdir(os.path.join(path, d))]
        if len(dirs) == 0:
            return None
        for date in sorted(dirs):
            if os.path.isfile(os.path.join(path, date, "status.json")):
                if date > "2022-03-01-17-27":
                    dates.append(date)
        return dates

    dates.extend(getLatestDir(app._resultProvider._path))

    def getMemo(date):
        # if exist .log file
        log_path = app._resultProvider._path + date + '.log'
        if not os.path.exists(log_path):
            log_path = app._resultProvider._path + date + "/config.json"
        if not os.path.exists(log_path):
            return "No Log File"

        with open(log_path) as fd:
            obj = json.load(fd)
            if 'memo' in obj:
                return obj['memo']
            else:
                return "No Memo"

    options = []
    for date in dates:
        options.append({"label": date + ":" + getMemo(date), "value": date})

    layout = html.Div([
        dcc.Dropdown(
            id="coverage-date-picker",
            options=options,
            value=options[-1]['value']
            ),
        html.Div(id="coverage-container")
        ])

    return layout

@app.callback(
    dash.dependencies.Output("coverage-container", "children"),
    [dash.dependencies.Input("coverage-date-picker", "value")])
def getCoverageLayout(date):
    resultProvider = app._resultProvider

    def setLayout(figs):
        for fig in figs:
            fig.update_layout(autosize=False,
                    width=1000, height=500,
                    font={'family': 'Helvetica', 'color': 'Black'})
    directory = os.path.join(resultProvider._path, date)
    fig, bar = getCdfFig(directory)
    figOnlyIgnore, barOnlyIgnore = getCdfFig(directory, onlyIgnoreFn=True)
    figOnlyNotIgnore, barOnlyNotIgnore = getCdfFig(directory, onlyNotIgnoreFn=True)

    setLayout([fig, bar, figOnlyIgnore, barOnlyIgnore, figOnlyNotIgnore, barOnlyNotIgnore])
    layout = [html.Div([
        html.H1("Threshold-Coverage plot"),
        html.P("Each threshold correspond to the maximum coverage of loops with the largest sequential SCC smaller than the threshold."),
        html.P("For example, when threshold=0%, only DOALL loops are selected. When threshold=100%, all loops are selected."),
        html.P("Loops have to be more than 10% of the program execution and on average 8 iteration/invocation."),
        html.P("When multiple loops meet threshold requirement, a max clique algorithm is run to select the max coverage")]),
        dcc.Graph(
            id='threshold-coverage-graph',
            figure=fig,
            ),
        dcc.Graph(
            id='threshold-coverage-bar',
            figure=bar,
            ),
        dcc.Graph(
            id='threshold-coverage-graph-only-not-ignore',
            figure=figOnlyNotIgnore,
            ),
        dcc.Graph(
            id='threshold-coverage-bar-only-not-ignore',
            figure=barOnlyNotIgnore,
            ),
        dcc.Graph(
            id='threshold-coverage-graph-only-ignore',
            figure=figOnlyIgnore,
            ),
        dcc.Graph(
            id='threshold-coverage-bar-only-ignore',
            figure=barOnlyIgnore,
            ),
        ]



    return layout

def getStatusLayout(resultProvider):
    path = os.path.join(resultProvider._path)

    def getLatestDir(path):
        dates = []
        dirs = [d for d in os.listdir(path) if os.path.isdir(os.path.join(path, d))]
        if len(dirs) == 0:
            return None
        for date in sorted(dirs):
            if os.path.isfile(os.path.join(path, date, "status.json")):
                if date >= "2022-01-27-16-37":
                    dates.append(date)
        return dates

    dates = getLatestDir(path) 
    if not dates:
        return [html.Div([html.H1("No valid status files")])]

    def getMemo(date):
        # if exist .log file
        path = app._resultProvider._path
        log_path = path + date + '.log'
        if not os.path.exists(log_path):
            log_path = path + date + "/config.json"
        if not os.path.exists(log_path):
            return "No Log File"

        with open(log_path) as fd:
            obj = json.load(fd)
            if 'memo' in obj:
                return obj['memo']
            else:
                return "No Memo"

    options = []
    for date in dates:
        options.append({"label": date + ":" + getMemo(date), "value": date})

    layout = html.Div([
        dcc.Dropdown(
            id="status-date-picker",
            options=options,
            value=options[-1]['value']
            ),
        html.Div(id="status-container")
        ])

    return layout

@app.callback(
    dash.dependencies.Output("status-container", "children"),
    [dash.dependencies.Input("status-date-picker", "value")])
def getStatusTable(date):
    path = app._resultProvider._path
    statusJson = os.path.join(path, date, "status.json")
    with open(statusJson, 'r') as fd:
        status = json.load(fd)

    passes = ["Loop", "Edge", "SLAMP", "Exp-slamp", "Exp-ignorefn"] #, "SpecPriv", "HeaderPhi", "Experiment"]

    tb = [html.Tr([html.Th(c) for c in (["bmark"] + passes)])]
    for bmark, st in sorted(status.items()):
        td = [html.Td(bmark)]

        for p in passes:
            if p not in st:
                td.append(html.Td("-"))
            else:
                if st[p]:
                    td.append(html.Td("Y", style={'color': 'green'}))
                else:
                    td.append(html.Td("X", style={'color': 'red'}))
        tb.append(html.Tr(td))

    keys = ["debug_info", "exec_coverage", "loop_stage", "loop_speedup", "slamp", "covered_lcDeps", "total_lcDeps", "lcDeps_coverage"]
    # for each benchmark, get "Exp-slamp", if not None, get "loops", render the json
    names = ["Benchmark", "Loop", "Debug Info", "Exec Coverage (%)", "Loop Stage", "Loop Speedup (x)", "SLAMP", "Covered LC Deps", "Total LC Deps", "LC Deps Coverage (%)"]
    loops_tb = [html.Tr([html.Th(c) for c in names])]

    for bmark, st in sorted(status.items()):
        if "Exp-slamp" in st and st["Exp-slamp"]:
            loops = st["Exp-slamp"]["loops"]
            if loops:
                for loop, values in loops.items():
                    # get all values of the dict, and render it as a table
                    rendered_values = []
                    for key in keys:
                        if key in values:
                            rendered_values.append(values[key])
                        else:
                            rendered_values.append("-")
                    loops_tb.append(html.Tr([html.Td(bmark), html.Td(loop), html.Td(rendered_values)]))

    return [html.Div([
        html.H1("Status as of " + date),
        html.Table(tb),
        html.H1("SLAMP Exps"),
        html.Table(loops_tb)
        ])]


@app.callback(dash.Output('page-content', 'children'),
              [dash.Input('url', 'pathname')])
def display_page(pathname):
    if not pathname:
        return 404

    if pathname == '/':
        pathname = '/realSpeedup'

    if pathname == '/status':
        layout = getStatusLayout(app._resultProvider)
        return layout
    if pathname == '/multiCore':
        layout = getMultiCoreLayout(app._resultProvider)
        return layout
    elif pathname == '/realSpeedup':
        layout = getRealSpeedupLayout(app._resultProvider)
        return layout
    elif pathname == '/estimatedSpeedup':
        layout = getEstimatedSpeedupLayout(app._resultProvider)
        return layout
    elif pathname == '/estimatedSpeedup-exp3':
        layout = getEstimatedSpeedupLayoutExp3(app._resultProvider)
        return layout
    elif pathname == '/coverage':
        layout = getCoverageDatePickerLayout()
        return layout
    elif pathname == '/comparePrivateer':
        layout = getComparePrivateerLayout(app._resultProvider)
        return layout
    elif pathname.startswith("/bmark_"):
        bmark = pathname.split("_")[1]
        layout = getOneBenchmarkLayout(app._resultProvider, bmark)
        return layout
    else:
        return 404
    # You could also return a 404 "URL not found" page here


if __name__ == '__main__':
    cpf_root = parseArgs()
    result_path = os.path.join(cpf_root, "./results/")
    app._resultProvider = ResultProvider(result_path)

    app.layout = html.Div([
        dcc.Location(id='url', refresh=False),
        dcc.Link('SPEC 2017 Status', href='/status'),
        html.Br(),
        dcc.Link('Different Cores', href='/multiCore'),
        html.Br(),
        # dcc.Link('Real Speedup', href='/realSpeedup'),
        # html.Br(),
        dcc.Link('Compare with Privateer', href='/comparePrivateer'),
        html.Br(),
        dcc.Link('Estimated Speedup', href='/estimatedSpeedup'),
        html.Br(),
        dcc.Link('Estimated Speedup (new)', href='/estimatedSpeedup-exp3'),
        html.Br(),
        dcc.Link('Coverage (OOPSLA22)', href='/coverage'),
        html.Div(id='page-content')
    ])

    app.run_server(debug=False, host='0.0.0.0')
