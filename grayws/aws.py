import boto3
from cfn_flip import flip, to_yaml, to_json
import json
from deepmerge import Merger, always_merger
from dictdiffer import diff, patch
import re
import yaml

cfn = boto3.client('cloudformation')

diff_merger = Merger(
    [
        (list, ["append"]),
        (dict, ["merge"])
    ],
    ["override"],
    ["override"]
)

## Data Manipulation Functions
def compose_reason(detail, parameters):
    if detail['ChangeSource'] == 'DirectModification':
        return "Resource {1} {0} changed through Direct Modification".format(detail['Target']['Name'], detail['Target']['Attribute'])
    elif detail['ChangeSource'] == 'ResourceAttribute':
        return "Resource {1} {0} changed by Resource attribute {2}".format(detail['Target']['Name'], re.sub("(ies)$", "y", detail['Target']['Attribute']), detail['CausingEntity'])
    elif detail['ChangeSource'] == 'ResourceReference':
        return "Resource {1} {0} changed by Resource {2}".format(detail['Target']['Name'], re.sub("(ies)$", "y", detail['Target']['Attribute']), detail['CausingEntity'])
    elif detail['ChangeSource'] == 'ParameterReference':
        return "Resource {1} {0} changed by Parameter {2}: {03}".format(detail['Target']['Name'], re.sub("(ies)$", "y", detail['Target']['Attribute']), detail['CausingEntity'], parameters[detail['CausingEntity']])
    else:
        return 'unknown'

def parse_reasons(change, parameters):
    reasons = list(map(lambda x: compose_reason(x, parameters), change))
    return reasons

def parse_event(event):
    status_length = len(event['ResourceStatus'])
    tabs = "\t\t\t\t\t"

    if status_length > 13:
        tabs = "\t\t\t\t"

    if status_length > 23:
        tabs = "\t\t\t"

    if status_length > 27:
        tabs = "\t\t"

    if len(event['ResourceStatus']) == 44:
        tabs = "\t"

    event_string = "[{0}] {1} {2} \t\"{3}\"".format(
        event['Timestamp'].strftime("%Y-%M-%d %H:%M:%S UTC"),
        "{0}{1}".format(event['ResourceStatus'], tabs),
        event['ResourceType'],
        event['LogicalResourceId']
        )
    return event_string

def construct_diff(args):
    if isinstance(args[1], str):
        node_keys = args[1].split(".")
    else:
        node_keys = args[1]
    leaf_index = len(node_keys) - 1

    obj = current = {}
    for index, key in enumerate(node_keys):
        if index == leaf_index:
            if args[0] == "change":
                #current[key] = "{0} -> {1}".format(args[2][0], args[2][1])
                current["- {0}".format(key)] = args[2][0]
                current["+ {0}".format(key)] = args[2][1]
            else:
                if args[0] == "add":
                    operator = "+"
                elif args[0] == "remove":
                    operator = "-"
                if isinstance(args[2], str):
                    current["{0} {1}".format(operator, key)] = args[2]
                elif isinstance(args[2], list):
                    if isinstance(args[2][0], tuple):
                        if isinstance(args[2][0][0], int):
                            current["{0} {1}".format(operator,key)] = [ args[2][0][1] ]
                        else:
                            current[key] = { "{0} {1}".format(operator,args[2][0][0]): args[2][0][1]}
                    else:
                        current[key] = list(map(lambda x: "{0} {1}".format(operator, x), args[2][0]))
        else:
            current[key] = {}
            current = current[key]
    return obj

def resource_diffs(orig, new):
    diffs = {}
    for resource in orig:
        if resource in list(new.keys()):
            resource_diff = diff(orig[resource], new[resource])
            if resource_diff:
                diffs[resource] = {}
                for index,dff in enumerate(list(resource_diff)):
                    diffs[resource] = diff_merger.merge(diffs[resource], construct_diff(dff))
    return diffs

## AWS API Function
def stack_list():
    # Return all stacks except DELETE_COMPLETE
    stacks = []
    stack_list = cfn.list_stacks(StackStatusFilter=['CREATE_IN_PROGRESS', 'CREATE_COMPLETE','CREATE_FAILED', 'CREATE_COMPLETE', 'ROLLBACK_IN_PROGRESS', 'ROLLBACK_FAILED', 'ROLLBACK_COMPLETE', 'DELETE_IN_PROGRESS', 'DELETE_FAILED', 'UPDATE_IN_PROGRESS', 'UPDATE_COMPLETE_CLEANUP_IN_PROGRESS', 'UPDATE_COMPLETE', 'UPDATE_ROLLBACK_IN_PROGRESS', 'UPDATE_ROLLBACK_FAILED', 'UPDATE_ROLLBACK_COMPLETE_CLEANUP_IN_PROGRESS', 'UPDATE_ROLLBACK_COMPLETE', 'REVIEW_IN_PROGRESS'])
    stacks.extend(list(map(lambda x: {
      'name': x.get('StackName'),
      'description': x.get('TemplateDescription'),
      'created': x.get('CreationTime'),
      'updated': x.get('LastUpdatedTime'),
      'status': x.get('StackStatus'),
      'drift': x['DriftInformation']['StackDriftStatus'],
      }, stack_list['StackSummaries'])))
    while 'NextToken' in stack_list:
      token = stack_list['NextToken']
      stack_list = cfn.list_stacks(StackStatusFilter=['CREATE_IN_PROGRESS', 'CREATE_COMPLETE','CREATE_FAILED', 'CREATE_COMPLETE', 'ROLLBACK_IN_PROGRESS', 'ROLLBACK_FAILED', 'ROLLBACK_COMPLETE', 'DELETE_IN_PROGRESS', 'DELETE_FAILED', 'UPDATE_IN_PROGRESS', 'UPDATE_COMPLETE_CLEANUP_IN_PROGRESS', 'UPDATE_COMPLETE', 'UPDATE_ROLLBACK_IN_PROGRESS', 'UPDATE_ROLLBACK_FAILED', 'UPDATE_ROLLBACK_COMPLETE_CLEANUP_IN_PROGRESS', 'UPDATE_ROLLBACK_COMPLETE', 'REVIEW_IN_PROGRESS'], NextToken=token)
      stacks.extend(list(map(lambda x: {
      'name': x.get('StackName'),
      'description': x.get('TemplateDescription'),
      'created': x.get('CreationTime'),
      'updated': x.get('LastUpdatedTime'),
      'status': x.get('StackStatus'),
      'drift': x['DriftInformation']['StackDriftStatus'],
      }, stack_list['StackSummaries'])))
    return stacks

def stack_info(stack):
    stack_details = cfn.describe_stacks(StackName=stack)
    changesets = cfn.list_change_sets(StackName=stack)
    drift = cfn.describe_stack_resource_drifts(StackName=stack, StackResourceDriftStatusFilters= ['MODIFIED','DELETED'])

    print('Parameters' in stack_details['Stacks'][0])
    if 'Parameters' in stack_details['Stacks'][0]:
      params = sorted(stack_details['Stacks'][0]['Parameters'], key = lambda x: x['ParameterKey'])
    else:
      params = []
    if 'Outputs' in stack_details['Stacks'][0]:
      outputs = sorted(stack_details['Stacks'][0]['Outputs'], key = lambda x: x['OutputKey'])
    else:
      outputs = []
    if 'Tags' in stack_details['Stacks'][0]:
      tags = sorted(stack_details['Stacks'][0]['Tags'], key = lambda x: x['Key'])
    else:
      tags = []
    stack_info = []

    max_length = max(len(params), len(outputs), len(tags))
    for x in range(0, max_length):
      items = {}
      if len(params) > x:
        items.update(params[x])
      if len(outputs) > x:
        items.update(outputs[x])
      if len(tags) > x:
        items.update(tags[x])
      stack_info.append(items)

    if len(changesets['Summaries']) > 0:
        stack_change_sets = list(map(lambda x: {
          'name': x['ChangeSetName'],
          'id': x['ChangeSetId'],
          'status': x['Status'],
          'exec_status': x['ExecutionStatus'],
          'created': x['CreationTime']
        }, changesets['Summaries']))
    else:
      stack_change_sets = []
    details = list(map(lambda x: {
        'name': stack,
        'change_sets': stack_change_sets,
        'drifts': drift['StackResourceDrifts'],
        #'current_change_set': x['ChangeSetId'],
        #'description': x['Description'],
        'created': x['CreationTime'],
        #'last_updated': x['LastUpdatedTime'],
        'status': x['StackStatus'],
        'info': stack_info
      }, stack_details['Stacks']))
    return details[0]

def get_template(stack, change_set=None):
    if change_set:
        template = cfn.get_template(StackName=stack,  ChangeSetName=changeset)['TemplateBody']
    else:
        template = cfn.get_template(StackName=stack)['TemplateBody']

    if isinstance(template, str):
      template = json.loads(to_json(template))

    return template

def change_set_info(stack, changeset):
    change_set = cfn.describe_change_set(StackName=stack, ChangeSetName=changeset)
    original_template_body = cfn.get_template(StackName=stack)['TemplateBody']
    change_set_template_body = cfn.get_template(StackName=stack,  ChangeSetName=changeset)['TemplateBody']
    if isinstance(original_template_body, str):
        original_template = json.loads(to_json(original_template_body))
    else:
        original_template = dict(original_template_body)
    if isinstance(change_set_template_body, str):
        change_set_template = json.loads(to_json(change_set_template_body))
    else:
        change_set_template = dict(change_set_template_body)
    if original_template:
      orig_resources = original_template['Resources']
    else:
      orig_resources = {}
    new_resources = change_set_template['Resources']

    diffs = resource_diffs(orig_resources, new_resources)

    parameters = {item['ParameterKey']:item['ParameterValue'] for item in change_set['Parameters']}
    set_details = {
        'parameters': parameters,
        'changes': list(map(lambda x: {
            'Action': x['ResourceChange']['Action'],
            'LogicalResourceId': x['ResourceChange'].get('LogicalResourceId', None),
            'PhysicalResourceId': x['ResourceChange'].get('PhysicalResourceId', None),
            'Replacement': x['ResourceChange'].get('Replacement', None),
            'ResourceType': x['ResourceChange']['ResourceType'],
            'Scope': x['ResourceChange']['Scope'],
            'Details': parse_reasons(x['ResourceChange']['Details'], parameters)
        }, change_set['Changes']))
    }

    set_info = { 'raw': change_set, 'processed': set_details, 'orig': orig_resources, 'new': new_resources, 'diffs': diffs }
    return set_info

def stack_events(stack, scope):
    raw_events = cfn.describe_stack_events(StackName=stack)['StackEvents']
    if scope:
        events = list(map(lambda x: parse_event(x), raw_events))
    else:
        events = list(map(lambda x: parse_event(x), raw_events))
    return events

def resources_json(stack):
  resources = cfn.list_stack_resources(StackName=stack)['StackResourceSummaries']
  return resources

def events_json(stack):
  raw_events = cfn.describe_stack_events(StackName=stack)['StackEvents']
  return raw_events

def status_json(stack):
  status = cfn.describe_stacks(StackName=stack)['Stacks'][0]
  return status

def apply_change_set(stack, changeset):
    cfn.execute_change_set(StackName=stack, ChangeSetName=changeset)
    return True

def delete_change_set(stack, changeset):
    cfn.delete_change_set(StackName=stack, ChangeSetName=changeset)
    return True
