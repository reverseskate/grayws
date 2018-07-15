import boto3

cfn = boto3.client('cloudformation')

## Data Manipulation Functions
def compose_reason(detail):
    #print(detail)
    if detail['ChangeSource'] == 'DirectModification':
        return "Direct modification of resource attribute {0} in {1}".format(detail['Target']['Name'], detail['Target']['Attribute'])
    elif detail['ChangeSource'] == 'ResourceAttribute':
        return "Resource attribute {0} in {1} changed via resource {2}".format(detail['Target']['Name'], detail['Target']['Attribute'], detail['CausingEntity'])
    elif detail['ChangeSource'] == 'ResourceReference':
        return "Resource attribute {0} in {1} changed via resource {2}".format(detail['Target']['Name'], detail['Target']['Attribute'], detail['CausingEntity'])
    elif detail['ChangeSource'] == 'ParameterReference':
        return "Resource attribute {0} in {1} changed via parameter {2}".format(detail['Target']['Name'], detail['Target']['Attribute'], detail['CausingEntity'])
    else:
        return 'unknown'

def parse_reasons(change):
    reasons = list(map(lambda x: compose_reason(x), change))
    print(reasons)
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
    #print(change_set['Changes'])
    set_details = {
        'parameters': change_set['Parameters'],
        'changes': list(map(lambda x: {
            'Action': x['ResourceChange']['Action'],
            'LogicalResourceId': x['ResourceChange'].get('LogicalResourceId', None),
            'PhysicalResourceId': x['ResourceChange'].get('PhysicalResourceId', None),
            'Replacement': x['ResourceChange'].get('Replacement', None),
            'ResourceType': x['ResourceChange']['ResourceType'],
            'Scope': x['ResourceChange']['Scope'],
            'Details': parse_reasons(x['ResourceChange']['Details'])
        }, change_set['Changes']))
    }

    return { 'raw': change_set, 'processed': set_details }
