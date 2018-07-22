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

## AWS API Function
def stack_list():
    stacks = cfn.list_stacks()
    names = list(map(lambda x: x['StackName'], stacks['StackSummaries']))
    return names

def stack_info(stack):
    stack_details = cfn.describe_stacks(StackName=stack)
    #print(stack_details['Stacks'])
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

    return { 'raw': change_set, 'processed': set_details }
