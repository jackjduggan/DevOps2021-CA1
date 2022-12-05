#### Week 4 Lab - Jack Duggan - 06/10/2022

#!/usr/bin/env python3

# --- Import Statements ---
import sys
import boto3
import webbrowser
import subprocess
import random
from datetime import datetime, timedelta
import time

# --- Variables ---
key_name = ".pem" # Enter Key Name

# --- Instance Creation ---
try:    
    ec2 = boto3.resource('ec2')
    new_instances = ec2.create_instances(

        # Image ID
        ImageId='ami-026b57f3c383c2eec', #This is the latest machine image ID.
	
        # Key-Pairs
        KeyName = '' , # Enter Key Name without .pem extension
    
        # User Data 
        UserData='''#!/bin/bash 
	    yum update -y
	    echo '<!doctype html>' >> index.html
	    echo '<html>' >> index.html
	    echo '<body><p>"####################"</p>' >> index.html
	    echo '<p>"metadata:"</p>' >> index.html
	    echo '<p>"####################"</p>' >> index.html
	    echo '<p>"Instance ID"</p>' >> index.html
	    curl http://169.254.169.254/latest/meta-data/instance-id >> index.html
	    echo '<p>"--------------------"</p>' >> index.html
	    echo '<p>ami id:</p>' >> index.html
	    curl http://169.254.169.254/latest/meta-data/ami-id >> index.html
	    echo '<p>"--------------------"</p>' >> index.html
	    echo '<p>"Instance IPv4:"</p>' >> index.html
	    curl http://169.254.169.254/latest/meta-data/local-ipv4 >> index.html
	    echo '<p>"--------------------"</p>' >> index.html
	    echo '<p>instance type:</p>' >> index.html
	    curl http://169.254.169.254/latest/meta-data/instance-type >> index.html
	    echo '<p>"--------------------"</p>' >> index.html
	    echo '</body>' >> index.html
	    echo '</html>' >> index.html
	    yum install httpd -y
	    cp index.html /var/www/html/index.html
	    systemctl enable httpd
	    systemctl start httpd
	    ''', #This multi-line string essentially builds the index.html from the terminal
	         #It uses the curl command to pull the intance metadata and append it to the index file.
	         #As well as this, it also starts the webserver.

        # Security Group IDs
        SecurityGroupIds = [''], # Enter Security Group ID

        # Tag Specifications
        TagSpecifications = [
          {
            'ResourceType': 'instance',
            'Tags' : [
              {
                'Key' : 'Name',
                'Value' : 'jduggan-devops-ca1'
              },
            ]
          },
        ],

        # Instance Counts
        MinCount=1,
        MaxCount=1,

        # Instance Type
        InstanceType='t2.nano'
        )
except:
    print("!!! Instance creation error")


# --- Instance Waiters ---
try:
    new_instances[0].wait_until_running() #waits for instance to start
    new_instances[0].reload() #reloads after start
    print("Instance Running | ID: " + new_instances[0].id)
except:
    print("!!! Waiter error")

# --- S3 Bucket Creation ---
try:    
    s3 = boto3.resource("s3")
    #creates a bucket with a name in the format "jd-devops-1234567890" 
    #with the digits being a random number betweeen 1 and 10 billion
    bucket_name = "jd-devops-" + str(random.randint(1000000000,9999999999)) 

    response = s3.create_bucket(Bucket=bucket_name, ACL='public-read') #bucket access
    print (response)
except:
    print ("!!! Bucket creation error")

# --- Image Handling ---
try:
    logo = subprocess.run("curl http://devops.witdemo.net/logo.jpg --output logo.jpg", shell = True)
    image = "logo.jpg" #curls the image from the website and saves it to logo.jpg as variable "image"
 
    response = s3.Object(bucket_name,image).put(Body=open(image, 'rb'), ACL='public-read', ContentType = 'image/jpeg') 
    print (response)
except:
    print ("!!! Image handling error")
    
# --- Bucket Index File ---
try:
    bucket_index_file = open('index.html', 'w') #creates another index.html file, with this one displaying the logo.jpg image
    index_file_contents = """
    <!doctype html>
    <html>
    <img src="https://{bucket_name}.s3.amazonaws.com/logo.jpg">
    </html>
    """.format(bucket_name=bucket_name)
    bucket_index_file.write(index_file_contents)
    bucket_index_file.close()
    indexPage = "index.html"
except:
    print("!!! Bucket index file error")

try:
    response = s3.Object(bucket_name,indexPage).put(Body=open(indexPage, 'rb'), ACL='public-read', ContentType = 'text/html')
    print (response)
except Exception as error:
    print (error)
    
# --- Web Server ---
time.sleep(75) #75 seconds pass before the web browser tabs open, enough time for things to run smoothly

try:
    website_configuration = {
        'ErrorDocument': {'Key': 'error.html'},
        'IndexDocument': {'Suffix': 'index.html'},
    }

    s3_website = s3.BucketWebsite(bucket_name)
    response = s3_website.put(WebsiteConfiguration=website_configuration)
except:
    print("!!! Bucket website config error")

try:
    web_address = "http://" + str(new_instances[0].public_ip_address) #a http address for the ec2 instance public ip address.
    webbrowser.open_new_tab(web_address)
    web_address_2 = "http://" + str(bucket_name) + ".s3-website-us-east-1.amazonaws.com" #a http address for the contents of the bucket.
    webbrowser.open_new_tab(web_address_2)
except:
    print("!!! URL building/Web Browser opening error")

# --- URL File ---
try:
    urls_file = open('jdugganurls.txt', 'w')
    urls_file_contents = web_address + "\n" + web_address_2
    urls_file.write(urls_file_contents)
    urls_file.close()
    print("jdugganurls.txt file created... URLs appended...")
except:
    print("!!! URL file creation error")

# --- Simple Monitoring ---
instance_private_ip = new_instances[0].private_ip_address
instance_public_ip = new_instances[0].public_ip_address
print("Private IP: " + instance_private_ip)
print("Public IP: " + instance_public_ip)

try:
    #Sample run to disable SSH host key checking for future scp/ssh calls
    process1 = "ssh -o StrictHostKeyChecking=no -i " + key_name + " ec2-user@" + instance_public_ip + " 'pwd'"
    subprocess.run(process1, shell = True)
except:
    print("process1 error")
try:
    #Actual scp/ssh calls.
    process2 = "scp -i " + key_name + " monitor.sh ec2-user@" + instance_public_ip + ":."
    subprocess.run(process2, shell = True)
except:
    print("process2 error")
try:
    process3 = "ssh -i " + key_name + " ec2-user@" + instance_public_ip + " 'chmod 700 monitor.sh'"
    subprocess.run(process3, shell = True)
except:
    print("process3 error")
try:
    #Script run
    process4 = "ssh -i " + key_name + " ec2-user@" + instance_public_ip + " './monitor.sh'"
    subprocess.run(process4, shell = True)
except:
    print("process4 error")
    
# --- CloudWatch Monitoring ---
try:
    cloudwatch = boto3.resource('cloudwatch')
    instance = ec2.Instance(new_instances[0].id)
    instance.monitor()
    time.sleep(360)

    metric_iterator = cloudwatch.metrics.filter(
                                                Namespace='AWS/EC2', 
                                                MetricName='CPUUtilization', 
                                                Dimensions=[{'Name':'InstanceId', 'Value': new_instances[0].id}]
                                                )
    metric = list(metric_iterator)[0]
except:
    print("!!! Cloudwatch Error")





