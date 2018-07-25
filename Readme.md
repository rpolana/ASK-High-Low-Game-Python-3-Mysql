# High low game Alexa skill with SDK 2 and python 3 lambda using aws mysql db for persistence

Works as a starter with ASK SDK 2 and python 3 lambda using mysql db.  Derived from [standard High Low Game sample](https://github.com/alexa-labs/alexa-skills-kit-sdk-for-python/tree/master/samples/HighLowGame) which uses python 2.7 and Dynamo DB.  Changed to en-IN for purpose of testing in India. I also changed the lambda handlers to traditional class style in stead of decorators style.

## TODO

Better organize the handler classes and separate DB code into another file.

## Interaction model

Same model json as the original, as specified below:
```
Give examples
```

## Usage

1. Clone this repository in a newly created project folder
2. Change to the subdirectory lambda/use-east-1_high_low_game_py3 under the project folder.  Setup ask-sdk in local machine in a this subdirectory following instructions in [original repository](https://github.com/alexa-labs/alexa-skills-kit-sdk-for-python/tree/master/samples/HighLowGame).  This is where the high_low_game.py source code lives too.
3. Install pymysql in the same subdirectory as in step 2, using 'pip3 install pymysql'
4. In the subdirectory, issue 'zip -ru ../../../lambda.zip * ' to create a zip file
5. Login to developer.amazon.com and go to Alexa skill kit console. Create a new skill following same directions in the [original repository](https://github.com/alexa-labs/alexa-skills-kit-sdk-for-python/tree/master/samples/HighLowGame) with same model as in the original or the one in this repository for en-IN. Build and save the model for the skill.
6. Login to aws management console, go to lambda service, create a new lambda from scratch.  Set its environment to python 3.6 and handler to 'high_low_game.handler'.  Add 'Alexa Skill Kit' as a trigger, giving the specific skillID copied from the skill UI. For this lambda, create a new aws user role or use existng user role ensuring this user role has access to a public mysql instance you created in AWS RDS service.  Set five environment variables listed below as required for the lambda:
...
MYSQL_ENDPOINT to the public mysql db instance endpoint in aws RDS
MYSQL_PORT to 3306 for mysql db
MYSQL_DATABASE to 'high_low_game'
MYSQL_DBUSER to the name of the mysql db user with read write access to 'high_low_game' database schema
MYSQL_DBPASSWORD to the db user password
...
7. Upload the lambda.zip just created to this aws lambda using the upload button and then click save. 
8. Set endpoint of skill in the UI to the new lambda arn and save the model.

## Note
I had to use the zip file upload method for lambda because, for some reason, ask-cli does not work to upload lambda. It happens after pymysql installation, causing a zip file creation that exhausts all disk space during command 'ask deploy -t lambda' from the project directory.
