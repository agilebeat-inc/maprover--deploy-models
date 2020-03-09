#!/usr/bin/env bash

# updating function code

# here are all the specific name dependencies

# file/directory with the lambda function code:
lambda_func="./lambda_example.py"
entrypoint="lambda_example.lambda_handler"
lambda_name="petri"
 # this can have multiple entries, separated by spaces
 # apparently we need to use full ARNs here, not just the name
layer_deps="arn:aws:lambda:us-east-1:531395337930:layer:numpillow:1"

AWS_CMD="aws2" # if using version 1 of the AWS CLI, this should just be AWS

# zip it up (could put it in S3 for a more 'cloudy' experience)
zip -r pkg.zip "${lambda_func}"

echo "Updating function code"

${AWS_CMD} lambda update-function-code \
    --function-name ${lambda_name} \
    --zip-file fileb://pkg.zip \
    --publish > publish_result.json

# updating function configuration, for example
# if we refactor or rename the lambda handler function
# or upgrade the Python version
# note that the 'handler' argument needs both the file path and function name
# since the lambda code can contain multiple files

echo "Updating function config"

# some parameter info:
# --timeout allows up to this many seconds for execution (default is 3)
# --memory-size must be a multiple of 64; the implied units are Mb
${AWS_CMD} lambda update-function-configuration \
    --function-name ${lambda_name} \
    --handler "${entrypoint}" \
    --timeout 100 \ 
    --memory-size 2048 \ 
    --runtime python3.7 \
    --layers "${layer_deps}" \
    > config_result.json  \
    && echo "Success!"
