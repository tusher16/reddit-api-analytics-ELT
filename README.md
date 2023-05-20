# REDDIT API DATA ELT PIPELINE
This project aims to create a data pipeline for extracting data from the Reddit API and generating a dashboard for data analysis. The pipeline focuses on extracting data from the subreddit `r/datascience` (https://www.reddit.com/r/datascience/) on a daily basis. The extracted data is then uploaded to AWS S3 buckets and copied to Redshift for further analysis. The orchestration of the pipeline is handled by Apache Airflow running in a Docker container.

The full documentation for the Reddit Data Pipeline can be found on Medium at the following link: [Reddit Data Pipeline Documentation]( https://tusher16.medium.com/8664d5ff842a)

## Architecture

![workflow image](https://github.com/tusher16/reddit-api-analytics-ELT/blob/146005d576a97b58f8c1cce1f6211f641e0f6e25/images/Workflow.jpg "Workflow Image")

1. Data extraction: Data is extracted from the [Reddit API](https://www.reddit.com/dev/api/) using the PRAW API wrapper.
2. AWS resources setup: Terraform is used to create necessary AWS resources, including S3 buckets and Redshift cluster.
3. Data loading: Extracted data is loaded into an S3 [AWS S3](https://aws.amazon.com/s3/) bucket for storage.
4. Data copying: The data is then copied from the S3 bucket to the Redshift data warehouse. [AWS Redshift](https://aws.amazon.com/redshift/)
5. Orchestration: Airflow, running within a Docker container, orchestrates the pipeline tasks. [Airflow](https://airflow.apache.org/) in [Docker](https://www.docker.com/)
6. Dashboard creation: Tableau is utilized to create a dashboard for data visualization and analysis.


## Dashboard

![Dashboard image](https://github.com/tusher16/reddit-api-analytics-ELT/blob/146005d576a97b58f8c1cce1f6211f641e0f6e25/images/tableau_dashboard.png "Dashboard Image")

## Setup

To set up the pipeline, follow the steps below. Note that if you are using the AWS free tier, there will be no costs incurred. However, make sure to terminate all resources within 2 months to avoid any charges. Also, be aware of any changes to the AWS free tier terms and conditions.

Clone the repo

```
git clone https://github.com/tusher16/reddit-api-analytics-ELT.git
cd  reddit-api-analytics-ELT
```

### Overview

* The data extraction is performed using the PRAW API wrapper, scheduled to run daily as a DAG (Directed Acyclic Graph) in Airflow.
* The extracted data is stored in CSV files, uploaded to AWS S3 buckets, and then copied to Redshift for analysis.
* The pipeline is orchestrated using Apache Airflow running within a Docker container.

### Reddit API

The data is extracted from the subbreddit `r/datascience`. 
In order to extarct Reddit data, we need to use the Reddit API. Follow the below steps.

* Create a [Reddit account](https://www.reddit.com/register/).
* Create an [app](https://www.reddit.com/prefs/apps).
* Note down the following details.
    * App Name
    * App ID
    * API secret key

### AWS

The extracted data is stored on AWS using AWS free tier. There are 2 services used.
1. [Simple Storage Service(S3)](https://aws.amazon.com/s3/): This object storage is used to store the raw data extracted from Reddit.
2. [Redshift](https://aws.amazon.com/redshift/): This data warehousing service, based on PostgreSQL, allows for fast processing of large datasets using massively parallel processing. 

To get started with AWS, create a new AWS account and set up the free tier. Follow best practices to secure your account. Create a new IAM role and set up the AWS CLI. This will generate a credentials file `(e.g., ~/.aws/credentials)` with the necessary access key and secret access key.


### IaC using Terraform

We are using [Terraform](https://learn.hashicorp.com/terraform?utm_source=terraform_io)  to setup and destroy our cloud resources using code.
We are creating the following resources

 * S3 bucket: Used for data storage.

 * Redshift cluster: A columnar data warehouse provided by AWS. 

 * IAM Role for Redshift: Assigns Redshift the necessary permissions to read data from S3 buckets.

 * Security Group: Applied to Redshift to allow incoming traffic for connecting to the dashboard.

To create the resources:

  1. install Terraform by following the [instructions](https://learn.hashicorp.com/tutorials/terraform/install-cli) provided.

  2. Change into `terraform` directory.

  ```
  cd terraform
  ```

  3. Edit the `variables.tf` file and fill in the default parameters for Redshift DB password, S3 bucket name, and region.

  4. Initialize Terraform and download the AWS plugin:

  ```
  terraform init
  ```

  5. Create a plan based on the `main.tf` file and execute it to create the AWS resources:


  ```
  terraform apply
  ```

  6. Once the entire project is finished and no longer needed, use this command to delete all the resources.. 

  ```
  terraform destroy
  ```
  The resources will be available in the AWS interface once you have finished the processes.

### Configuration

* Set up a configuration file configuration.conf under the `airflow/extraction/` folder and fill in the required configuration variables.. 

```
[aws_config]
bucket_name = XXXXX
redshift_username = awsuser
redshift_password = XXXXX
redshift_hostname =  XXXXX
redshift_role = RedShiftLoadRole
redshift_port = 5439
redshift_database = dev
account_id = XXXXX
aws_region = XXXXX

[reddit_config]
secret = XXXXX
developer = XXXXX
name = XXXXX
client_id = XXXXX
```

### Docker and Airflow

The Reddit Data Pipeline is scheduled to execute once every day using Airflow. There are three scripts in the extraction folder:

1. `reddit_extract_data.py`: This script extracts data from Reddit and saves it to a CSV file.

2. `s3_data_upload_etl.py`: This script uploads the CSV file to the S3 bucket.

3. `redshift_data_upload_etl.py`: This script copies the data from the S3 bucket to the Redshift cluster.

The script `etl_reddit_pipeline.py` in `airflow\dags` folder is the DAG which runs daily to execute the above three files using Bash commands.

If you are runnning on Linux, run the following commands.
To set up the pipeline, follow these steps:

1. Install Docker and Docker Compose:
The `docker-compose.yaml` file contains definitions for each service required by Airflow. The local file system is linked to Docker containers thanks to an upgrade to the `volumes` option. The Docker containers also have the AWS credentials mounted as ready-only. 


The `docker-compose.yaml` file defines every service required for Airflow.

2. Navigate to the project's airflow directory.

```
cd airflow
```
3. we added two extra lines under volumes to mount two folders from our local file system to the Docker containers. The first line mounts the extraction folder containing our scripts to /opt/airflow, where our Airflow DAG will run. The second line mounts our AWS credentials as read-only into the containers.

```
- ${AIRFLOW_PROJ_DIR:-.}/extraction:/opt/airflow/extraction
- $HOME/.aws/credentials:/home/airflow/.aws/credentials:ro
```
Additionally, we added a line to pip install specific packages within the containers. We used the _PIP_ADDITIONAL_REQUIREMENTS variable to specify these packages, including praw, boto3, configparser, and psycopg2-binary. Note that there are other ways to install these packages within the containers.
```
_PIP_ADDITIONAL_REQUIREMENTS: ${_PIP_ADDITIONAL_REQUIREMENTS:-praw boto3 configparser psycopg2-binary}

```
4. Create the necessary folders required by Airflow:
```
mkdir -p ./logs ./plugins
```
5. Create an .env file with the following content to set the Airflow user ID:
```
echo -e "AIRFLOW_UID=$(id -u)" > .env
```

6. Initialize the Airflow database by running the following command: 
```
sudo docker-compose up airflow-init
```
This will take a few minutes to complete.

Create the airflow containers. This will take some time to run.

7. Start the Airflow containers:

```
sudo docker-compose up
```
his will start the Airflow services defined in the docker-compose.yaml file.

8. Access the Airflow web interface at http://localhost:8080.

9. To stop the containers, use the following command:

```
docker-compose down
```
This will shut down the containers gracefully.

Note: If you want to remove all containers, volumes, and downloaded images, you can use the following command: 

```
docker-compose down --volumes --rmi all

```
This command will completely remove the containers and clean up all resources, allowing you to start fresh if needed.