from flask import Flask, redirect, render_template, url_for, jsonify

from grayws import app, aws

@app.route("/")
def welcome():
    return redirect("/stacks/")

@app.route("/_status/")
def status():
    return jsonify({ 'STATUS': 'OK' })

@app.route("/about/")
def about():
    return "GrayWS: A Cloudformation Orchestration Dashboard"

@app.route("/stacks/")
def stacks():
    stack_list = aws.stack_list()
    stacks = list(map(lambda x: { 'name': x['name'], 'link': url_for('stack', stack_name = x['name']), 'status': x['status'], 'drift': x['drift'], 'created': x['created'], 'updated': x['updated'] }, stack_list))
    return render_template('stacks.html', data = stacks)

@app.route("/stack/<stack_name>/")
def stack(stack_name):
    stack_info = aws.stack_info(stack_name)
    return render_template('stack.html', stack = stack_info, data = stack_info)

@app.route("/stack/<stack_name>/graph/")
def graph(stack_name):
    template = aws.get_template(stack_name)
    return render_template('graph.html', stack = stack_name, data = template)

@app.route("/stack/<stack_name>/set/<changeset>/")
def changeset(stack_name, changeset):
    set_details = aws.change_set_info(stack_name, changeset)
    return render_template('changeset.html', stack = stack_name, changeset = changeset, data = set_details)

@app.route("/stack/<stack_name>/set/<changeset>/apply")
def apply(stack_name, changeset):
    aws.apply_change_set(stack_name, changeset)
    return render_template('confirm_apply.html', stack = stack_name, changeset = changeset, data = {})

@app.route("/stack/<stack_name>/set/<changeset>/delete")
def delete(stack_name, changeset):
    aws.delete_change_set(stack_name, changeset)
    return render_template('confirm_delete.html', stack = stack_name, changeset = changeset, data = {})

@app.route("/stack/<stack_name>/events")
def events(stack_name):
    scope = None
    events = aws.stack_events(stack_name, None)
    return render_template('events.html', stack = stack_name, scope = scope, data = events)

@app.route("/stack/<stack_name>/json/events/")
def json_events(stack_name):
    events = aws.events_json(stack_name)
    return jsonify(events)

@app.route("/stack/<stack_name>/json/resources/")
def json_resources(stack_name):
    resources = aws.resources_json(stack_name)
    return jsonify(resources)

@app.route("/stack/<stack_name>/json/template/")
def json_template(stack_name):
    template = aws.get_template(stack_name)
    return jsonify(template)

@app.route("/stack/<stack_name>/json/status/")
def json_status(stack_name):
  status = aws.status_json(stack_name)
  return jsonify(status)

@app.route("/stack/<stack_name>/icons/")
def icons(stack_name):
    template = aws.get_template(stack_name)
    return render_template('icons.html', stack = stack_name, data = template)
