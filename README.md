## Gray Weather Station

An opinionated AWS Cloud Visibility Dashboard. GrayWS provides:

* A summary view of Cloudformation stacks, with create/updated times and drift status
* A list of all stack change sets and detailed list of resource drifts with diffs
* Detailed view of changes with diffs
* Force Directed Graph view of stack resources and dependencies, including create/update/delete status during stack operations

### Running

Export AWS Environment variables. GrayWS requires a [minimal IAM policy](aws/grayws-iam-policy.json) of:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "GrayWSAccess",
            "Effect": "Allow",
            "Action": [
                "cloudformation:DescribeChangeSet",
                "cloudformation:DescribeStacks",
                "cloudformation:DescribeStackResourceDrifts",
                "cloudformation:GetTemplate",
                "cloudformation:ListChangeSets",
                "cloudformation:ListStacks",
                "cloudformation:ListStackResources"
            ],
            "Resource": "*"
        }
    ]
}
```

#### With Python

```bash
pip3 install -r requirements.txt
export FLASK_APP=grayws
python3 -m flask run

```

#### With Docker Compose
```bash
docker-compose up
```

By default either approach will run locally on port 5000, i.e. http://127.0.0.1:5000

