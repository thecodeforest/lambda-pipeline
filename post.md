
This is a very long post, simply because it touches on lots of areas. By the end, you'll be exposed to the following topics: 



There are courses that focus on each of these topics alone. 

First, let's start by initializing a github repository. 

```shell
git init
```

Then, create a repository on Github.com and copy the repository URL. Enter the following command at the terminal to connect the local repository to the remote repository on Github. 

```shell
git remote add origin https://github.com/<your_repository_name>/lambda-pipeline.git
```

I added a `README` file as well as a `.gitignore` file when creating the original repository, so I'll make sure to pull theses changes into the local repository as well. 

```shell
git pull origin main
```

The next step will be to navigate to our `.gitignore` file to ensure that we don't commit things related to our virtual environment (which we'll set up below) to our repository. Open up this file and add the following to the bottom of file. 
```
# ignore all binaries
lambda-pipeline/bin

# ignore pyvenv
pyvenv.cfg
```


let's start by creating a virtual environment. We'll be using Python 3.9. This will isolate our development environment. 

```shell
python3.9 -m venv lambda-pipeline
source lambda-pipeline/bin/activate
```

Now let's install the packages we'll need. Create a `requirements.txt` file and add the following text: 
```text
boto3==1.26.70
pandas==1.5.3
awswrangler==2.19.0
```

Then use `pip install -r requirements.txt` to install all of the packages into our newly created virtual environment. 

We'll also need to install the AWS CLI (command line interface). This allows us to programatically interact with the AWS services we'll be using during this post. You can check if it's installed by typing `aws --version` at the command line. If you get something back, then you should be good to go! 

Assuming the CLI is set up, let's dive into the core logic of our lambda function. 

### Creation our app

Let's start by creating a directory in the root of project called `app`. This is where our source code will live. We will go into that directory and create an `__init__.py` file. This is where we'll put our logic. 
```shell
mkdir app
cd app
touch __init__.py
mkdir utils
cd utils
touch weather.py
```

Next, open up `weather.py` and paste the code below. 

```python
# app/utils/weather.py
import requests


def get_weather(city: str, api_key: str) -> dict:
    """Get the weather for a city."""
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return data
    else:
        print("Error: Failed to retrieve weather data.")
        return None


def extract_weather_data(data: dict) -> list:
    """Convert the JSON response to a Pandas DataFrame."""
    temperature = data["main"]["temp"]
    humidity = data["main"]["humidity"]
    description = data["weather"][0]["description"]
    return [temperature, humidity, description]


def convert_celcius_to_fahrenheit(celcius: float) -> float:
    """Convert Celcius to Fahrenheit."""
    return celcius * 9 / 5 + 32
```

These are our "utility functions" that help collect, clean, and transform our weather data. This is a toy example, so the only transformation that occurs is converting the temperature from celsius to farenheit. 

Next, open up `__init__.py`. This is where the lambda "handler function" will go, which we'll call `weather_collector`. The handler function must be specified in the function's configuration, and it must conform to a specific signature that depends on the programming language used. For example, in python, your function must have two parameters -- `event` and `context`. When the Lambda function is invoked, AWS Lambda passes event data to the handler function, which can process the data and return a response. We aren't going to use either here, but you still need to specify them. 

```python
# app/__init__.py
import os
import pandas as pd
from utils.weather import (get_weather,
                           extract_weather_data,
                           convert_celcius_to_fahrenheit)


output_bucket = os.environ["OUTPUT_BUCKET"]
openweather_api_key = os.environ["OPENWEATHER_API_KEY"]


def weather_collector(event, context):
    """Lambda function to retrieve weather data from openweathermap api. 
    The data is then stored in a S3 bucket as a CSV file. Note you will need 
    to create an openweathermap account and get an API key to use this function.
    """

    all_data = pd.DataFrame()
    cities = ['New York', 'Portland', 'Chicago', 'Seattle', 'Dallas']
    columns = ['temperature', 'humidity', 'description', 'city']
    for city in cities:
        data = get_weather(city)
        if data:
            data_fmt = extract_weather_data(data) + [city]
            weather_df = pd.DataFrame([data_fmt],
                                      columns=columns,
                                      index=[0]
                                      )
            all_data = pd.concat([all_data, weather_df], axis=0)
    # convert temperature to fahrenheit
    all_data['temperature'] = all_data['temperature'].apply(
        convert_celcius_to_fahrenheit)
    # save to s3
    wr.s3.to_csv(df=all_data,
                 path=f"s3://{output_bucket}/weather_data.csv",
                 index=False
                 )
```

We now have our core logic for the lambda function. In the next section, we'll configure our AWS CLI to interact with AWS service. 

### Setting up AWS
To complete this walkthrough, you'll need an AWS account. There are many resources on how to get set-up, so I won't go into much depth here. However, getting started can be a bit confusing. One thing to keep in mind is that you will need to set permissions that allow your account to interact with each of the services. By default, you won't be able to access S3 or Lamdbda, or even have S3 interact with Lamdbda, without enabling these connections. 

The first step is to configure the AWS CLI. You will need an Access Key ID, Secret Access key to complete this step. Run the following command:

```shell
aws configure
```
And you should see something like this: 
```
AWS Access Key ID [******************]: 
AWS Secret Access Key [****************]: 
Default region name [us-west-2]: 
Default output format [json]: 
```
This information will be stored locally in a `credentials` file in ~/.aws/credentials (Linux & Mac) or %USERPROFILE%\.aws\credentials (Windows). 

The next thing we'll do is navigate to the console. This is only time we'll use the console, and it's merely to illustrate that we can. We'll add a single policy --IAMFullAccess-- to our user `lambda-example`.  Here's the steps: 

* Search for 'IAM'

* Under the Access Management tab, click on Users. You should see the user name `lambda-example`. Click on the name. 

* Click on `Add Permissions`

* Click on `Attach policies directly`

* Search for 'IAMFullAccess' and check the box next to the name, and then click on next

* Then click on 'Add Permissions'

We can add permissions to the other services we'll be interacting with via the console, but I'd recommend using the command line. The main reason is that you can keep a configuration file that can be versioned and shared with other developers. 



The User name associated with these keys is called `lambda-example`. You can name it whatever you would like, but we want this particular profile to be able to access S3 (note that we are assuming that this profile has access to S3). * AmazonS3FullAccess

Run the following: 
```sh
export AWS_PROFILE=lambda-example
```

We can test that everything is configured correctly by creating our `output_bucket` in S3. This is where we'll store the transformed weather data collected by our Lambda function. 

The last thing we'll need to do is create the `output_bucket` in S3. You can do that by running the following from the command line. Note that you can verify that your variable was created by running `echo $<VARIABLE_NAME>. Note that you will need to name your bucket something different, as all buckets must have a unique name. 
```shell
export OUTPUT_BUCKET=city-weather-data-bucket
aws s3 mb s3://$OUTPUT_BUCKET
```

You can verify that your bucket was created with the following: 
```shell
aws s3 ls
```

That's all we'll do for now. 

### Building our docker container
In the root of your project, create a `Dockerfile` and paste the following into it: 
```Docker

FROM public.ecr.aws/lambda/python:3.9

# copy from local to container root
COPY requirements.txt requirements.txt

# executes any command and creates a new layer and commits the results
RUN pip install -r requirements.txt

# this is a special directory that is used to store the lambda function
# this is part of the base image
COPY app ${LAMBDA_TASK_ROOT}/app

ENV PYTHONPATH=${LAMBDA_TASK_ROOT}/app

# set the environment variables
ENV BUCKET_NAME="city-weather-data"

# specify the lambda handler
CMD [ "app.weather_collector" ]
```

Let's breakdown what is happening here. 

* `FROM public.ecr.aws/lambda/python:3.9`: Specifies the base image to use for the container, which is the official AWS Lambda Python image for Python 3.9.

* `COPY requirements.txt requirements.txt`: Copies the requirements.txt file from the local directory to the root directory of the container.

* `RUN pip install -r requirements.txt`: Runs the command to install the Python packages listed in requirements.txt.

* `COPY app ${LAMBDA_TASK_ROOT}/app`: Copies the app directory from the local directory to the /app directory within the container's Lambda function folder ($LAMBDA_TASK_ROOT).

* `ENV PYTHONPATH=${LAMBDA_TASK_ROOT}/app`: Sets the PYTHONPATH environment variable to the location of the app directory within the Lambda function folder. PYTHONPATH indicates where Python should look for modules and packages. When you import a module or package (e.g., `import requests`), the interpreter will search a pre-determined set of directories. We are adding a custom directory to our search path. 

In our Docker file above,  `ENV PYTHONPATH=${LAMBDA_TASK_ROOT}/app` sets the PYTHONPATH environment variable to the location of the app directory within the Lambda function folder, so that the Lambda function can import its own code modules from that directory.

* `ENV BUCKET_NAME="city-weather-data"`: Sets the BUCKET_NAME environment variable to "city-weather-data". This is where we'll save the output of our Lambda function. 

* `CMD [ "app.weather_collector" ]`: Specifies the Lambda handler function to use, which is weather_collector within the app directory. This command will be executed when the container is run.

To build our container, we'll execute the following (just make sure you have Docker running beforehand). 

```sh
docker build -t lambda-weather .
```
This command builds a Docker image using the current directory as the build context, assigns the image the tag `lambda-weather`, and creates a named image for it. The dot (".") at the end of the command refers to the current directory (the root of your git repo). It will take a few minutes to build the container. 

Now that our docker container has built, let's start it by running the following: 

```shell
docker run \
--name lambda-weather \
-v /Users/<your_username>/.aws:/root/.aws \
-p 9080:8080 \
-e AWS_PROFILE=lambda-example \
-e OPENWEATHER_API_KEY=<your_api_key> \
-d \
lambda-weather
```

Again, let's breakdown what this command is doing: 

* The `-v` option is mounting the host machine's /Users/Mark/.aws directory to the container's /root/.aws directory, which will allow the container to access the host machine's AWS credentials.

* The `-p` option maps the host machine's port 9080 to the container's port 8080, which will make it possible to access the container from the host machine on port 9080.

* The `-e` option sets an environment variable named AWS_PROFILE to the value lambda-example.

* The `-d` option specifies that the container should run in the background.

* Finally, `lambda-weather` is the image name or image ID of the Docker image to run.

Now that our container is running and configured, we can test our lambda function locally before pushing our container to the Elastic Container Registery (ECR) to make sure everything works. 

You can verify that your container is up and running by executing `docker ps -a`. 

We can interact with our container using the following command: 

```sh
docker exec -it lambda-weather bash
```

A new commandline prompt should appear, which means you are succesfully interacting with the container. Now that we are in the container, we'll need to set another environment variable for testing, specifically our openweather API key. Note that we will set this an environment variable in our lambda function, but are doing it here just for the purpose of testing. 

Now we can test our Lambda function. 
```sh
python -c "import app; app.weather_collector(None, None)"
```

If this is the first time you've tried your lambda, there is a good chance that a Syntax or Logical error will surface. You can simply type `exit` to leave the container, and run the following: 

```shell
docker stop lambda-weather
docker rm -f lambda-weather
docker build -t lambda-weather .
docker run \
--name lambda-weather \
-v /Users/<your_username>/.aws:/root/.aws \
-p 9080:8080 \
-e AWS_PROFILE=lambda-example \
-e OPENWEATHER_API_KEY=<your_api_key> \
-d \
lambda-weather
```

Now if we enter back into the container and run `python -c "import app; app.weather_collector(None, None)"` from the command line, a .csv file will appear in the `city-weather-data` bucket with the current weather of the five cities specifed in the `__init__.py` module. 

Assuming everything worked, our next step is to push the container to ECR, which is like Github but for Docker containers. To enable command line access to ECR, you'll have to attach the `AmazonEC2ContainerRegistryFullAccess` policy to your profile. We'll call our repository name `lambda-weather-img`

```shell
aws ecr create-repository --repository-name lambda-weather-img
```

After the command executes successfully, you should see a JSON output with information about your new repository, including its URL and Amazon Resource Name (ARN).

Now we'll manually push our container with the following command: 
```shell
aws ecr get-login-password \
--region us-west-2 | docker login \
--username AWS \
--password-stdin 371410071971.dkr.ecr.us-west-2.amazonaws.com # this is from the repositoryUri 
```

Then we'll tag our image and push to remote. 

```shell
docker tag lambda-weather:latest \
371410071971.dkr.ecr.us-west-2.amazonaws.com/lambda-weather-img:latest
docker push 371410071971.dkr.ecr.us-west-2.amazonaws.com/lambda-weather-img:latest
```

On a side note - if you received the following error message "denied: Your authorization token has expired. Reauthenticate and try again." it means that you need to refresh your authorization token. You can execute the command below.

```shell
aws --region us-west-2 ecr get-login-password | docker login --username AWS --password-stdin 371410071971.dkr.ecr.us-west-2.amazonaws.com
```
Here is what's happening: 

* `aws --region us-west-2 ecr get-login-password`: This command uses the AWS Command Line Interface (CLI) to retrieve an authentication token from ECR for the specified AWS region (us-west-2) using the get-login-password command. The token is used to authenticate the Docker client to ECR.

* `|`: This is a pipe symbol, which is used to redirect the output of the previous command to the next command in the pipeline. That is, we want to use the output from the command to the left of the pipe as input to the command to the right of the pipe. 

* `docker login --username AWS --password-stdin 371410071971.dkr.ecr.us-west-2.amazonaws.com`: This command logs in to the specified ECR repository (371410071971.dkr.ecr.us-west-2.amazonaws.com) using the Docker CLI. The --username flag specifies the username to use for authentication (in this case, "AWS"), and the --password-stdin flag tells Docker to read the authentication token from standard input. Since the output of the previous command was piped to this command, the authentication token is read from the output of the aws command.


### Automating the build with Github Actions

In the previous section, we created a Docker container, tested it locally, and then saved the result to ECR. If the process felt manual, that's because it was! And we don't want to go through all of those steps everytime we make a change. Furthermore, if we working with other developers the codebase, we want to ensure that when they are making their own changes to the repository, they are working from the most recent version. Accordingly, this section will focus on 1. automating the build process, 2., ensuring that any changes to the core logic are also pushed to ECR.
To make all of this possible, we'll rely on Github Actions - <insert explanation>. 
It is simple to set-up. In the root of our project, run the following: 

```shell
mkdir .github
cd .github
mkdir workflows
cd workflows
touch push-to-ecr.yml
```

In the `push-to-ecr.yml` file, we'll add the following: 
```yaml
name: Push to ECR

on:
  push:
    branches:
      - main

env:
  ECR_REGISTRY: 371410071971.dkr.ecr.us-west-2.amazonaws.com
  AWS_REGION: us-west-2

jobs:
  build-and-push:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v2

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v1
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: ${{ env.AWS_REGION }}

      - name: Build and tag Docker image
        run: |
          docker build -t $ECR_REGISTRY/lambda-weather-img:latest .
          docker tag $ECR_REGISTRY/lambda-weather-img:latest $ECR_REGISTRY/lambda-weather-img:latest

      - name: Login to ECR
        id: login-ecr
        uses: aws-actions/amazon-ecr-login@v1

      - name: Push Docker image to ECR
        run: |
          docker push $ECR_REGISTRY/lambda-weather-img:latest

```

Here's what happening: 

This workflow triggers when a push event occurs on the main branch. It then sets some environment variables with the ECR registry and AWS region. Next, it checks out the code from the repository, configures AWS credentials, builds and tags the Docker image with a unique tag (using the GITHUB_SHA environment variable), and then logs in to the ECR registry using the aws-actions/amazon-ecr-login action. Finally, it pushes the Docker image to ECR.

Before you can use this workflow, you will need to set up some secrets in your GitHub repository:

<image of secrets in repo>

AWS_ACCESS_KEY_ID: Your AWS access key ID.
AWS_SECRET_ACCESS_KEY: Your AWS secret access key.

Also, make sure to replace the <YOUR_ECR_REGISTRY>, <YOUR_AWS_REGION>, and <YOUR_AWS_ACCOUNT_ID> placeholders in the workflow with your own values.

In the next section, we'll create our lambda function. 


### Building our Lambda Function

The first step here is to create a "role" for our lambda function. Roles are created and managed in the IAM (Identity and Access Management) service. 

To find a role in AWS:

* Go to the AWS Management Console and open the IAM service.

* In the left-hand navigation menu, select "Roles".

* You will see a list of all the roles in your account. You can use the search bar to find a specific role by name, or you can filter the list by the roles that are assigned to a specific service or by the roles that have a specific policy attached.

* Click on the role name to view the role details. This will show you information about the role, including its ARN (Amazon Resource Name), the policies attached to the role, and any trusted entities (such as AWS services or specific AWS accounts) that are allowed to assume the role.

* Roles are often used to grant permissions to AWS services or other AWS resources, such as a Lambda function or an EC2 instance. When creating or configuring an AWS service or resource, you may be prompted to select an existing IAM role or create a new one.


This command returns information about the AWS account and IAM user or role that is making the request. The "Arn" field in the output specifies the ARN of the IAM entity that is making the request.

Now make a configuration file for the lambda function. 

```json
{
    "FunctionName": "daily-weather",
    "PackageType": "Image",
    "Role": "arn:aws:iam::371410071971:role/lamba-weather-role",
    "Code": {
        "ImageUri": "371410071971.dkr.ecr.us-west-2.amazonaws.com/lambda-weather-img:latest"
    },
    "Timeout": 180,
    "MemorySize": 128
}
```

And then you run this to create your lambda function:
```sh
aws lambda create-function --cli-input-json file://lambda-function-config.json
```

Once we've created our function, we also need to add one critical piece of information -- the openweather API key. When we were testing our function locally, we just passed it in as a variable. However, we want to make this variable accessible every time our lambda function is executed, so we'll add it to the runtime environment below: 

```shell
aws lambda update-function-configuration --function-name daily-weather --environment "Variables={OPENWEATHER_API_KEY=XXXXXXXXXXXXXXXXXXXX}"
```

Let's go ahead and test our lambda function. 
```shell
aws lambda invoke --function-name daily-weather
```

Then run the following to confirm that a new `.csv` file has been created in the your S3 bucket. 
```shell
aws s3 ls city-weather-data-bucket
```
### now add your staging function
```shell
aws lambda create-function \
--function-name daily-weather-staging \
--package-type Image \
--role "arn:aws:iam::371410071971:role/lamba-weather-role" \
--code ImageUri=$ECR_REGISTRY/lambda-weather-img:staging \
--timeout 180 \
--memory-size 128

aws lambda update-function-configuration \
  --function-name daily-weather-staging \
  --environment "Variables={OPENWEATHER_API_KEY=XXXXXX,EMAIL_ADDRESS=XXXXX}"
```


And there you have it! Now that we've deployed and tested our lambda function, we'll need a way to run on a schedule for the purpose of collecting the weather each day. 


### Scheduling our Data Pipeline with AWS EventBridge

One of the main applications of EventBridge is to trigger actions with AWS services. For example, you can trigger a lambda function to process raw data every time a new file is loaded to an S3 bucket. In our case, we won't rely on an event. Instead, we'll schedule our lambda function to run once per day at 1pm PST. 

We'll start off by using the `put-rule` command to create a rule in EventBridge. We'll create a rule that triggers our Lambda to run everyday at 6:00PM UTC. 

```sh
aws events put-rule --name "daily-weather-schedule" --schedule-expression "cron(0 18 * * ? *)"
```

Next, we'll enable a permission that allows EventBridge to invoke our Lambda function. Note that you will need to include the ARN of the newly created rule. 

```sh
aws lambda add-permission \
--function-name daily-weather \
--statement-id my-scheduled-event \
--action 'lambda:InvokeFunction' \
--principal events.amazonaws.com \
--source-arn arn:aws:events:us-west-2:371410071971:rule/daily-weather-schedule
```

We'll also need the FunctionARN (or Amazon Resource Name) of the thing we want to schedule. Let's create a query argument that filters to any functions with the word 'weather' in the function name. 

```sh
aws lambda list-functions --query \
'Functions[?contains(FunctionName, `weather`) == `true`].FunctionArn'
```

Finally, below we'll add a "target" to for our rule, in this case the target is our "daily-weather" Lambda function.
```sh
aws events put-targets \
--rule "daily-weather-schedule" \
--targets "Id"="daily-weather","Arn"="arn:aws:lambda:us-west-2:371410071971:function:daily-weather"
```

And that's it! Now we have a lambda function that will be triggered every morning at 10AM PST. A final step we'll want to include in our pipeline is monitoring. In the next section, we'll cover a simple example of how to monitor the execution of our Lambda function.  


### Data Validation with Pandera

Now that we've automated the data collection process, we need a way to validate that data is correct. Pandera is a python library that validates the schema of a Pandas DataFrame. In my opinion, it is one of the best forms of documentation, in that you are explicitly stating the expected structure of a Dataframe and then checking to ensure that it confirms the specification. It also relieves you of having to manually inspect the data and ensure quality and consistency every time you encounter new data. Let's set up a simple validation step that will run after our data is fully collected. 

```shell
cd app
mkdir validation
cd validation
touch validate_weather_data.py
```






### Sending notifications with Simple Notification Services (SNS)

A key component of any data pipeline is monitoring. There are a variety of steps that fall into this bucket, including data validation, progress tracking, network connectivity issues, but here we'll just focus on if the pipeline succesfully runs. If it does, we receive an email indicating that the pipeline completed without error. Additionally, we'll want a few details about what happened. For example, we might want to know how long it took to run, how many records were processed, and where the records were written to. 

From the command line, add: 
* Add AmazonSNSFullAccess to the lambda-example user
* create a topic
```shell
aws sns create-topic --name "weather-pipeline-monitoring"
"TopicArn": "arn:aws:sns:us-west-2:371410071971:weather-pipeline-monitoring"
```
* subscribe to the topic and provide an email address

```shell
aws sns subscribe --topic-arn arn:aws:sns:us-west-2:371410071971:weather-pipeline-monitoring --protocol email --notification-endpoint dpuresearch1@gmail.com
```


From here, you'll need to navigate to the email address that you provided and confirm that you would like to subsribe to the topic. Once you confirm, we'll need to add an additional permission to our Lambda function, allowing it to interact with the SNS service. We can 

```shell
aws iam attach-role-policy --role-name lamba-weather-role --policy-arn arn:aws:iam::aws:policy/AmazonSNSFullAccess
```

Once that's done, you'll up the __init__.py module so it looks like this: 


The next step is to make our new data accessible. For example, our weather data might serve as an input to a downstream machine learning model. One easy way to query data is to use AWS Athena. However, before we can query the data, we'll have to 

### Creating a Data Source with AWS Glue




### Querying our source data with Athena

