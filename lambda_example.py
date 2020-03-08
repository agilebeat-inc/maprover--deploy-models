import numpy as np
import json
import os
import datetime as dt
import base64, io # deserializing tiles
from PIL import Image



# AWS package
import boto3

s3 = boto3.resource('s3')

# a static resource we'd like to use but not re-load every time
# that the lambda function is called:
inf = s3.Object('abobob','datasrc/sacred.txt')
# reading a file from an S3 bucket involves rather horrendous syntax:
bigtxt = inf.get()['Body'].read().decode('utf-8')[:1000000].split('\n')

if False:
    import tensorflow as tf
    # loading tensorflow graph and weights:
    tf_model = s3.Object('abobob','tf/tf_model.pb')
    weightsdata = tf_model.get()['Body'].read()
    graph_def = tf.GraphDef()
    graph_def.ParseFromString(weightsdata)

# name of S3 bucket where a result is written
OUT_BUCKET = 'abobobout'


rg = np.random.default_rng()

def deserialize_image(img_string: str):
    img = base64.urlsafe_b64decode(img_string)
    return Image.open(io.BytesIO(img))

def serialize_image(path: str):
    with Image.open(path) as img:
        # set up a bytes buffer:
        buf = io.BytesIO()
        img.save(buf,format = 'PNG')
        return base64.urlsafe_b64encode(buf.getvalue())

def image_to_array(image):
    rgb_img = image.convert('RGB')
    rgb_img = np.asarray(rgb_img) / 255.
    # why do we need to expand dims?
    return np.expand_dims(rgb_img, axis=0)

def model1():
    pass

def model2():
    pass

def model3():
    pass

# mapping of categories to models
PREDICTION_CATEGORIES = {
    "railroad": model1,
    "gumball": model2,
    "snorlax": model1,
    "arbitrage": model3
}

if False:
    img_loc = '/mnt/z/webpage/media/4-gLaCFz7JE.jpg'
    img_enc = serialize_image(img_loc)
    img_dec = deserialize_image(img_enc)
    img_arr = image_to_array(img_dec)

def random_line():
    """
    testing function which gives the lambda something to do
    """
    # choose a random line to write to the output bucket
    z = int(rg.integers(0,len(bigtxt))) # coerce to 'regular' int so that json serialization doesn't fail
    line = bigtxt[z]
    # path = os.popen("echo $PATH").read()
    # optdirs = os.listdir("/opt")
    # if saving the result to an S3 bucket, we can do something like this:
    outKey = f"invocation {dt.datetime.now()}.txt"
    outf = s3.Object(OUT_BUCKET, outKey)
    outf.put(
        ACL = 'bucket-owner-full-control',
        Body = line.encode(), # defaults to UTF-8,
        ContentEncoding = 'UTF-8'
    )
    # if responding to an HTTP request, we should return a properly formatted HTTP response
    # note that Lambda will use JSON to encode the response, so we don't need to explicitly encode anything
    # within the handler (in fact it will cause errors!)
    HTTP_response = {
        'statusCode': 200,
        'headers': {'Content-Type': 'text/html; charset=utf-8'},
        'body': json.dumps({'no.': z, 'text': line.replace('\r','')})
    }
    return HTTP_response

def lambda_handler(event, context):
    """
    'event' is an HTTP request with fields:
    x,y,z: integers giving tile coordinates and zoom (not currently used unless we want to cache)
    tile: a base64-encoded string which gets turned into a numeric array for prediction
    category: string, indicating which category we want to predict
    """
    return random_line() # remove when possible
    # once the models are ready, this can dispatch to them
    category = event['category']
    if not category in PREDICTION_CATEGORIES:
        return {
            'statusCode': 400,
            'headers': {'Content-Type': 'text/html; charset=utf-8'},
            'body': f"Category {category} is not available for prediction."
        }
    the_model = PREDICTION_CATEGORIES[category]
    
    # create a numeric array from the input tile:
    img = deserialize_image(event['tile'])
    tile_array = image_to_array(img)
    pred = the_model(tile_array)
    # the model should return a dict of (category: prob) items
    pred_prob = pred[category]
    HTTP_response = {
        'statusCode': 200,
        'headers': {'Content-Type': 'text/html; charset=utf-8'},
        'body': {'category': category,'probability': pred_prob}
    }
    return HTTP_response
    
