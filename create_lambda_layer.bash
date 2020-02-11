#! /usr/bin/env bash
# preparing python modules for AWS layer:

# install files in the input (requirements.txt) locally
# the main 'parameter' here is just the python package name
mkdir -p staging/python

# can be a specific version
module_name="numpy==1.18"
# if the module has dependencies, consider whether to use --no-deps
pip3 install ${module_name} -t ./staging/python

# remove symbols from compiled objects to reduce file size:
# note that this appears to backfire mysteriously! Some of the
# numpy binaries become much LARGER after strip
# find staging -name '*.so' | xargs strip -s

# -r is 'recurse into directories', -9 is 'compress better'
# zip will include the extra layer of directories so we must cd into/out of it...
cd staging && zip -r9 ../numpylayer.zip python && cd ../

# the bucket name needs to be coordinated with the account holder
# running this command
myBucketName="num-py-layer"
aws s3 cp numpylayer.zip "s3://${myBucketName}"

# now create (or update if it already exists) the layer
# use --zip-file arg rather than --content if publishing local content as a layer
aws lambda publish-layer-version \
    --layer-name py37numpy \
    --description "numpy 1.17" \
    --compatible-runtimes python3.7 python3.8 \
    --content S3Bucket=num-py-layer,S3Key=numpylayer.zip


# publishing a version of a function
# given a directory , zip the contents and
# send it off to the cloud
# we can create an abbreviated version of this
# in serverless (or SAM) which would amount to the same thing

# aws lambda create-function \
#     --function-name lambdaCLI \
#     --runtime python3.8 \
#     --role S3_accessor \ # need to check in IAM what roles this account has created/access to
#     --handler file.main \ # note the file.function syntax to indicate the location of event handler function
#     --no-publish