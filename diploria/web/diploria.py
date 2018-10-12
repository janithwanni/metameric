import os
import io
import base64
import matplotlib.pyplot as plt

from flask import Flask, render_template, request, Response
from itertools import chain
from diploria.prepare.data import process_and_write
from diploria.run import make_run, get_model

# Switch backend because of tk errors.
plt.switch_backend("Agg")
from diploria.plot import result_plot # noqa

global m
global max_cycles


app = Flask(__name__,
            template_folder='templates',
            static_folder='static')


@app.route("/about", methods=['GET'])
def about():
    return render_template("about.tpl")


@app.route("/analysis", methods=['GET'])
def analysis():
    return render_template("analysis.tpl",
                           rla=-.05,
                           step=1.0,
                           decay=.07,
                           min=-.02,
                           max=350,
                           threshold=.07,
                           rlalayers="orthography",
                           rlavars="frequency",
                           outputlayers="orthography",
                           w=True,
                           monitorlayers="orthography")


@app.route("/experiment", methods=['GET'])
def experiment():
    return render_template("experiment.tpl",
                           rla=-.05,
                           step=1.0,
                           decay=.07,
                           min=-.02,
                           max=350,
                           threshold=.07,
                           rlalayers="orthography",
                           rlavars="frequency",
                           outputlayers="orthography",
                           w=True,
                           monitorlayers="orthography")


@app.route("/prepare", methods=['GET'])
def prepare():
    return render_template("prepare.tpl",
                           decomp_layer="orthography",
                           decomp_name="letters",
                           feature_layer="letters",
                           feature_set="fourteen")


@app.route("/prepare", methods=['POST'])
def prepare_post():
    input_file = request.files.get("path_train")
    d_layer = request.form.get("decomp_layer")
    d_name = request.form.get("decomp_name")
    f_layers = request.form.get("feature_layer")
    f_set = request.form.get("feature_set")

    out_f = "result_{}".format(os.path.splitext(input_file.filename)[0])
    try:
        junk_file = io.StringIO()
        process_and_write(input_file,
                          junk_file,
                          d_layer.split(),
                          d_name.split(),
                          f_layers.split(),
                          f_set.split(),
                          strict=False)
    except Exception as e:
        print(e)
        return render_template("prepare.tpl",
                               validation="{}".format(e),
                               decomp_layer=d_layer,
                               decomp_name=d_name,
                               feature_layer=f_layers,
                               feature_set=f_set)

    junk_file = junk_file.getvalue()
    return Response(response=junk_file,
                    mimetype="text/csv",
                    headers={"Content-disposition":
                             "attachment; filename={}".format(out_f)})


@app.route("/home", methods=['GET'])
def home():
    return render_template("home.tpl")


@app.route("/", methods=['GET'])
def default():
    return render_template("home.tpl")


@app.route("/analysis", methods=['GET'])
def get_analysis():
    return render_template("analysis.tpl")


@app.route("/analysis", methods=['POST'])
def analysis_post():
    """Analyze an IA model."""
    input_file = request.files.get("path_train")
    param_file = request.files.get("path_param")
    rla = request.form.get("rla")
    step = request.form.get("step")
    decay = request.form.get("decay")
    min_val = request.form.get("min")
    max_cyc = request.form.get("max")
    outputlayers = request.form.get("outputlayers")
    rla_layers = request.form.get("rlalayers")
    rla_variable = request.form.get("rlavars")
    w = request.form.get("w")
    monitorlayers = request.form.get("monitorlayers")

    if not param_file:
        weights = None
    else:
        weights = param_file
    items = input_file

    global m
    global max_cycles
    try:
        max_cycles = int(max_cyc)
        m = get_model(items,
                      weights,
                      rla_variable=rla_variable,
                      rla_layers=rla_layers,
                      output_layers=outputlayers.split(),
                      monitor_layers=monitorlayers.split(),
                      global_rla=float(rla),
                      step_size=float(step),
                      decay_rate=float(decay),
                      minimum_activation=float(min_val),
                      adapt_weights=bool(w))

        inputs = [[l.name for l in x._to_connections]
                  for x in m.inputs.values()]
        inputs = sorted(set(chain.from_iterable(inputs)))
    except Exception as e:
        print(e)
        return render_template("analysis.tpl",
                               rla=-.05,
                               step=1.0,
                               decay=.07,
                               min=-.02,
                               max=350,
                               threshold=.07,
                               rlalayers="orthography",
                               rlavars="frequency",
                               outputlayers="orthography",
                               w=True,
                               monitorlayers="orthography",
                               validation=str(e))

    return render_template("analysis_2.tpl", inputs=inputs, data="")


@app.route("/analysis_2", methods=["POST"])
def post_item():
    """Post an item and show the graph."""
    global m
    global max_cycles

    inputs = [[l.name for l in x._to_connections] for x in m.inputs.values()]
    inputs = sorted(set(chain.from_iterable(inputs)))

    item = {}
    for x in inputs:
        max_length = max([y for x, y in m[x].name2idx.keys()])
        max_length += 1
        data = request.form.get(x).ljust(max_length)
        data = data[:max_length]
        item[x] = [(data[idx], idx)
                   for idx in range(max_length)]

    item = m.expand(item)
    res = m.activate([item], max_cycles=max_cycles, strict=False)[0]
    f = result_plot(item,
                    res,
                    {k: m[k].node_names for k in res.keys()},
                    dpi=500)

    image = io.BytesIO()
    f.canvas.print_png(image)
    plt.close()
    img = base64.b64encode(image.getvalue())
    img = str(img)[2:-1]
    return render_template("analysis_2.tpl", inputs=inputs, data=img)


@app.route("/experiment", methods=['POST'])
def main_experiment():
    """The main experiment page."""
    input_file = request.files.get("path_train")
    param_file = request.files.get("path_param")
    test_file = request.files.get("path_test")
    rla = request.form.get("rla")
    step = request.form.get("step")
    decay = request.form.get("decay")
    min_val = request.form.get("min")
    max_cyc = request.form.get("max")
    threshold = request.form.get("threshold")
    rla_layers = request.form.get("rlalayers")
    rla_variable = request.form.get("rlavars")
    w = request.form.get("w")
    monitorlayers = request.form.get("monitorlayers")

    out_f = "run_{}.csv".format(os.path.splitext(input_file.filename)[0])

    if not param_file:
        weights = None

    input_file = input_file
    test_file = test_file

    junk_file = io.StringIO()
    try:
        make_run(input_file,
                 test_file,
                 junk_file,
                 weights,
                 threshold=float(threshold),
                 rla_variable=rla_variable,
                 rla_layers=rla_layers,
                 output_layers=monitorlayers.split(),
                 monitor_layers=monitorlayers.split(),
                 global_rla=float(rla),
                 step_size=float(step),
                 max_cycles=int(max_cyc),
                 decay_rate=float(decay),
                 minimum_activation=float(min_val),
                 adapt_weights=bool(w))
    except Exception as e:
        print(e)
        return render_template("experiment.tpl",
                               rla=-.05,
                               step=1.0,
                               decay=.07,
                               min=-.02,
                               max=350,
                               threshold=.07,
                               rlalayers="orthography",
                               rlavars="frequency",
                               outputlayers="orthography",
                               w=True,
                               monitorlayers="orthography",
                               validation=str(e))

    junk_file = junk_file.getvalue()
    return Response(response=junk_file,
                    mimetype="text/csv",
                    headers={"Content-disposition":
                             "attachment; filename={}".format(out_f)})