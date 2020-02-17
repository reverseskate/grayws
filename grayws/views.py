from flask import Flask, redirect, render_template, url_for, jsonify, request

from grayws import app, aws

@app.route("/")
def welcome():
    return redirect("/<region>/stacks/")

@app.route("/_status/")
def status():
    return jsonify({ 'STATUS': 'OK' })

@app.route("/about/")
def about():
    return "GrayWS: A Cloudformation Orchestration Dashboard"

@app.route("/stacks/")
def default_stacks():
    region = aws.default_region()
    return redirect(f"/{region}/stacks/")

@app.route("/<region>/stacks/")
def stacks(region):
    print(region)
    stack_list = aws.stack_list(region)
    stacks = list(map(lambda x: { 'name': x['name'], 'link': url_for('stack', region=region, stack_name = x['name']), 'status': x['status'], 'drift': x['drift'], 'created': x['created'], 'updated': x['updated'] }, stack_list))
    return render_template('stacks.html', region = region, data = stacks)

@app.route("/<region>/stack/<stack_name>/")
def stack(stack_name, region):
    stack_info = aws.stack_info(stack_name, region)
    return render_template('stack.html', stack = stack_info, data = stack_info)

@app.route("/<region>/stack/<stack_name>/graph/")
def graph(stack_name, region):
    template = aws.get_template(stack_name, region)
    return render_template('graph.html', stack = stack_name, data = template)

@app.route("/<region>/stack/<stack_name>/set/<changeset>/")
def changeset(stack_name, region, changeset):
    set_details = aws.change_set_info(stack_name, region, changeset)
    return render_template('changeset.html', stack = stack_name, changeset = changeset, data = set_details)

@app.route("/<region>/stack/<stack_name>/set/<changeset>/apply")
def apply(stack_name, region, changeset):
    aws.apply_change_set(stack_name, region, changeset)
    return render_template('confirm_apply.html', stack = stack_name, changeset = changeset, data = {})

@app.route("/<region>/stack/<stack_name>/set/<changeset>/delete")
def delete(stack_name, region, changeset):
    aws.delete_change_set(stack_name, region, changeset)
    return render_template('confirm_delete.html', stack = stack_name, changeset = changeset, data = {})

@app.route("/<region>/stack/<stack_name>/events")
def events(stack_name, region):
    scope = None
    events = aws.stack_events(stack_name, region, None)
    return render_template('events.html', stack = stack_name, scope = scope, data = events)

@app.route("/<region>/stack/<stack_name>/json/events/")
def json_events(stack_name, region):
    events = aws.events_json(stack_name, region)
    return jsonify(events)

@app.route("/<region>/stack/<stack_name>/json/resources/")
def json_resources(stack_name, region):
    resources = aws.resources_json(stack_name, region)
    return jsonify(resources)

@app.route("/<region>/stack/<stack_name>/json/template/")
def json_template(stack_name, region):
    template = aws.get_template(stack_name, region)
    return jsonify(template)

@app.route("/<region>/stack/<stack_name>/json/status/")
def json_status(stack_name, region):
  status = aws.status_json(stack_name, region)
  return jsonify(status)

@app.route("/<region>/stack/<stack_name>/icons/")
def icons(stack_name, region):
    template = aws.get_template(stack_name, region)
    return render_template('icons.html', stack = stack_name, data = template)
