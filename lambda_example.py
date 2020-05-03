import numpy as np
import json
import os, re
import datetime as dt

import base64, io # deserializing tiles
from PIL import Image
import tensorflow as tf

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

is_aws = 'AWS_REGION' in os.environ

# read in pb file and re-hydrate it into a tf.GraphDef
if is_aws: 
    import boto3
    s3 = boto3.resource('s3')
    tf_model = s3.Object('abobob','tf/tf_model_motorway.pb')
    raw_data = tf_model.get()['Body'].read()
else:
    with open("/mnt/c/Users/skm/Dropbox/AWS/tf_model_motorway.pb",'rb') as fh:
        raw_data = fh.read()

motor_model = tf.GraphDef()
motor_model.ParseFromString(raw_data)


# inf = s3.Object('abobob','datasrc/sacred.txt')
# reading a file from an S3 bucket involves rather horrendous syntax:
# bigtxt = inf.get()['Body'].read().decode('utf-8')[:1000000].split('\n')
# rg = np.random.default_rng()

# name of S3 bucket where a result is written
# OUT_BUCKET = 'abobobout'

# example testing tile decoding:
# png_prefix = 'data:image/png;base64,'
# os.chdir("/mnt/c/Users/skm/Dropbox/Agilebeat/maprover-deploy")
# from b64tile import base64_test_string as b64s
# if b64s.startswith(png_prefix):
#     b64s = b64s[len(png_prefix):]

# img = deserialize_image(b64s)
# input_array = image_to_array(img)


# load the graph from the GraphDef object
motor_g = tf.Graph()
with motor_g.as_default() as graph:
    # g is updated silently as a side effect here!
    tf.import_graph_def(motor_model,name = 'motor')
    # if we don't know the name up front, need to hunt through them:
    opnames = [op.name for op in g.get_operations()]
    # is softmax only used for output layer? can also get the last activation layer
    # name of final actiavtion layer:
    last_activ = [op for op in opnames if 'activation' in op][-1]
    # are there other suffixes like :1, :2???
    softmax_t = graph.get_tensor_by_name(last_activ + ':0')


def motorway_prediction(img_b64):
    """
    Classify a tile
    """
    img = deserialize_image(img_b64)
    input_array = image_to_array(img)
    with tf.Session(graph = motor_g) as sess:
        preds = sess.run(
            fetches = softmax_t,
            feed_dict = {'motor/conv2d_1_input_1:0': input_array}
        )
    return preds

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
        Body = line.encode(), # defaults to UTF-8
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

# mapping of categories to models
PREDICTION_CATEGORIES = {
    "motorway": motorway_prediction,
    "railroad": model1,
    "gumball": model2,
    "snorlax": model1,
    "contango": model3
}

def lambda_handler(event, context):
    """
    'event' is an HTTP request with fields:
    x,y,z: integers giving tile coordinates and zoom (not currently used, just makes it easier to keep the info bundled together?)
    tile_base64: a base64-encoded string which gets turned into a numeric array for prediction
    category: string, indicating which category we want to predict
    can check context.authorizer.claims for JSON Web Token data via Cognito
    """
    # once the models are ready, this can dispatch to them
    category = event['category']
    if not category in PREDICTION_CATEGORIES:
        return {
            'statusCode': 400,
            'headers': {'Content-Type': 'text/html; charset=utf-8'},
            'body': f"Category {category} is not available for prediction."
        }
    the_model = PREDICTION_CATEGORIES[category]
    pred_prob = the_model(event['tile_base64'])
    
    HTTP_response = {
        'statusCode': 200,
        'headers': {'Content-Type': 'text/html; charset=utf-8'},
        'body': {'category': category,'probability': pred_prob}
    }
    return HTTP_response
    
