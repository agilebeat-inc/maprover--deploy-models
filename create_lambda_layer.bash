#! /usr/bin/env bash
# preparing python modules for AWS layer:

# input arguments: 
# name of S3 bucket where layer gets copied
# requirements.txt file specifying the dependencies
# (and can incude things like specific Python runtime)
layername="$1"
reqsfile="$2"
myBucketName="$3"

mkdir -p staging/python

# if the module has dependencies, consider whether to use --no-deps
pip3 install -r ${reqsfile} -t ./staging/python

AWS_CMD="aws2"

# remove symbols from compiled objects to reduce file size:
# note that this appears to backfire mysteriously! Some of the
# numpy binaries become much LARGER after strip
# find staging -name '*.so' | xargs strip -s

# -r is 'recurse into directories', -9 is 'compress better'
# zip will include the extra layer of directories so we must cd into/out of it...
zipf="${layername}_data.zip"
cd staging && zip -r9 "../${zipf}" python && cd ../
echo "Total zipped layer size:"
du -sh ${zipf}

# clean up the files we don't need:
rm -r staging

# the bucket name needs to be coordinated with the account holder
# running this command
${AWS_CMD} s3 cp "${zipf}" "s3://${myBucketName}"


# now create (or update if it already exists) the layer
# use --zip-file arg rather than --content if publishing local content as a layer
# the 'description' field would need to be updated manually
${AWS_CMD} lambda publish-layer-version \
    --layer-name ${layername} \
    --description "a layer" \
    --compatible-runtimes python3.7 python3.8 \
    --content S3Bucket=${myBucketName},S3Key=${zipf}

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