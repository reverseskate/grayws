from flask import Flask, render_template, url_for

from grayws import app, aws

@app.route("/")
def welcome():
    return "Gray Weather Station"

@app.route("/about/")
def about():
    return "GrayWS: A Cloudformation Orchestration Dashboard"

@app.route("/stacks/")
def stacks():
    stack_list = aws.stack_list()
    stacks = list(map(lambda x: { 'name': x, 'link': url_for('stack', stack_name = x) }, stack_list))
    return render_template('stacks.html', stacks = stacks, data = stacks)

@app.route("/stack/<stack_name>/")
def stack(stack_name):
    stack_info = aws.stack_info(stack_name)
    return render_template('stack.html', stack = stack_info, data = stack_info)

@app.route("/stack/<stack_name>/set/<changeset>/")
def changeset(stack_name, changeset):
    set_details = aws.change_set_info(stack_name, changeset)
    return render_template('changeset.html', stack = stack_name, changeset = changeset, data = set_details)
