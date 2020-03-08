# Pipeline 3: Deployment

This will be updated with scripts and documentation about managing the deployment of MapRover models.

## Automation

What can and should be automated (that is, scripted) to make updating and deploying efficient and easy?

- S3 bucket creation probably should _not_ be automated since we must choose globally unique names
- uploading data into S3 can be easily automated but is very easy (main obvious thing is trained model file)
- Setting permissions/policies/roles is tedious but important and should definitely be automated.
- All the boilerplate code linking Lambda function(s) to S3 triggers, layers, etc. can be scripted since it serves as documentation and also shouldn't change too frequently.

The 'deliverable' is an HTTP(S) REST API which can be called by the MapRover site for image classification.
