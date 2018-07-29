import boto3
from cfn_flip import flip, to_yaml, to_json
import json
import jsondiff
import re
import yaml

cfn = boto3.client('cloudformation')

## Data Manipulation Functions
def compose_reason(detail, parameters):
    #print(detail)
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
    event_string = "{0}\t\t{1}\t\t{2}\t\t{3}".format(
        event['Timestamp'].strftime("%Y-%M-%d %H:%M:%S UTC"),
        "{0}\t".format(event['ResourceStatus']) if len(event['ResourceStatus']) < 17 else event['ResourceStatus'],
        "{0}\t".format(event['ResourceType']) if len(event['ResourceType']) < 24 else event['ResourceType'],
        event['LogicalResourceId']
        )
    return event_string

def resource_diffs(orig, new):
    diffs = {}
    for resource in orig:
        print(resource)
        if resource in list(new.keys()):
            print(orig[resource])
            print(new[resource])
            diff = jsondiff.diff(orig[resource], new[resource], syntax='explicit')
            if diff:
                print(diff)
                diffs[resource] = diff
    print(diffs)
    return diffs

## AWS API Function
def stack_list():
    stacks = cfn.list_stacks()
    names = list(map(lambda x: x['StackName'], stacks['StackSummaries']))
    return names

def stack_info(stack):
    stack_details = cfn.describe_stacks(StackName=stack)
    changesets = cfn.list_change_sets(StackName=stack)
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
        #'current_change_set': x['ChangeSetId'],
        #'description': x['Description'],
        'created': x['CreationTime'],
        #'last_updated': x['LastUpdatedTime'],
        'status': x['StackStatus']
        }, stack_details['Stacks']))
    return details[0]

def change_set_info(stack, changeset):
    change_set = cfn.describe_change_set(StackName=stack, ChangeSetName=changeset)

    original_template = json.loads(to_json(cfn.get_template(StackName=stack)['TemplateBody']))
    change_set_template = json.loads(to_json(cfn.get_template(StackName=stack,  ChangeSetName=changeset)['TemplateBody']))
    orig_resources = original_template['Resources']
    new_resources = change_set_template['Resources']

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

    set_info = { 'raw': change_set, 'processed': set_details, 'orig': orig_resources, 'new': new_resources}
    return set_info

def stack_events(stack, scope):
    raw_events = cfn.describe_stack_events(StackName=stack)['StackEvents']
    if scope:
        events = list(map(lambda x: parse_event(x), raw_events))
        print("Filtering events")
    else:
        events = list(map(lambda x: parse_event(x), raw_events))
    return events

def apply_change_set(stack, changeset):
    cfn.execute_change_set(StackName=stack, ChangeSetName=changeset)
    return True

def delete_change_set(stack, changeset):
    cfn.delete_change_set(StackName=stack, ChangeSetName=changeset)
    return True
