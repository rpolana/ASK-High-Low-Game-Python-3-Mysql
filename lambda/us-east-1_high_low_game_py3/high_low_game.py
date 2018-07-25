# -*- coding: utf-8 -*-
#
# Copyright 2018 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"). You may not
# use this file except in compliance with the License. A copy of the License
# is located at
#
# http://aws.amazon.com/apache2.0/
#
# or in the "license" file accompanying this file. This file is distributed
# on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either
# express or implied. See the License for the specific language governing
# permissions and limitations under the License.
#

# This is a High Low Guess game Alexa Skill.
# The skill serves as a simple sample on how to use the
# persistence attributes and persistence adapter features in the SDK.
import random
import sys
import traceback
from os import environ

from ask_sdk.standard import StandardSkillBuilder
from ask_sdk_core.utils import is_request_type, is_intent_name
from ask_sdk_core.dispatch_components import AbstractRequestHandler, AbstractResponseInterceptor
from ask_sdk_core.dispatch_components import AbstractExceptionHandler
from ask_sdk_model.ui import SimpleCard
import pymysql

SKILL_NAME = 'High Low Game'
sb = StandardSkillBuilder(
    # table_name="High-Low-Game", auto_create_table=True
    )

endpoint=environ.get('MYSQL_ENDPOINT')
port=environ.get('MYSQL_PORT')
dbuser=environ.get('MYSQL_DBUSER')
password=environ.get('MYSQL_DBPASSWORD')
database=environ.get('MYSQL_DATABASE')

tablename = "High_Low_Game"
tablename = tablename.replace('\'', '\'\'')

print("db connection parameters: mysql host={}, port={}, dbuser={}, db={}".format( 
        endpoint, port, dbuser, database))
try:
    db_connection = pymysql.connect(host=endpoint, user=dbuser, passwd=password,
        port=int(port), db=database, autocommit=True)
    if not db_connection:
        raise Exception("ERROR: Cannot connect to database from handler")
    db_cursor = db_connection.cursor()
    print("high_low_game: connected to mysql, checking if table {} exists in database..".format(
                tablename))
    db_cursor.execute("""
        SHOW TABLES LIKE %s
        """, (tablename,))
    if not db_cursor.fetchone():
        print("high_low_game: table {} does not exist in database, creating..".format(
                tablename))
        query = """\
            CREATE TABLE {}(id int primary key auto_increment, user_id varchar(256), \
                game_state varchar(32), games_played int, ended_session_count int, \
                guess_number int, no_of_guesses int)  \
            """.format(tablename)
        db_cursor.execute(query)
except Exception as e:
    print("ERROR: Error connecting or checking if table {} exists to database.\n{}".format(
        tablename, traceback.format_exc()))
    raise

def get_persistent_attributes(user_id):
    print("high_low_game: checking if user_id {} exists in table ..".format(
                user_id))
    db_dict_cursor = db_connection.cursor(pymysql.cursors.DictCursor)
    db_dict_cursor.execute("""\
        SELECT * from {} where user_id=%s\
        """.format(tablename), (user_id,))
    attr = {}
    if db_dict_cursor.rowcount < 1:
        print("high_low_game: user_id {} does not exist in table, initializing..".format(
                user_id))
        attr['game_state'] = ''
        attr['games_played'] = 0
        attr['ended_session_count'] = 0
        attr['guess_number'] = 0
        attr['no_of_guesses'] = 0
        db_cursor.execute("""\
            INSERT INTO {} (user_id, game_state, games_played, ended_session_count, guess_number, no_of_guesses)\
            VALUES (%s, %s, %s, %s, %s, %s)\
            """.format(tablename), (user_id, attr['game_state'], attr['games_played'], 
            attr['ended_session_count'], attr['guess_number'], attr['no_of_guesses']))
        print("high_low_game: user_id {} row created: auto increment row id: {}".format(user_id, 
            db_cursor.lastrowid))
    else:
        row = db_dict_cursor.fetchone()
        print("high_low_game: got row for user_id {} from table: {}".format(
                user_id, row))
        attr['game_state'] = row['game_state']
        attr['games_played'] = row['games_played']
        attr['ended_session_count'] = row['ended_session_count']
        attr['guess_number'] = row['guess_number']
        attr['no_of_guesses'] = row['no_of_guesses']
    return attr

def save_persistent_attributes(user_id, attr):
    print("high_low_game: checking if user_id {} exists in table ..".format(
                user_id))
    db_dict_cursor = db_connection.cursor(pymysql.cursors.DictCursor)
    db_dict_cursor.execute("""\
        SELECT * from {} where user_id=%s\
        """.format(tablename), (user_id,))
    if db_dict_cursor.rowcount < 1:
        print("high_low_game: user_id {} does not exist in table, initializing..".format(
                user_id))
        db_cursor.execute("""\
            INSERT INTO {} (user_id, game_state, games_played, ended_session_count, guess_number, no_of_guesses)\
            VALUES (%s, %s, %s, %s, %s, %s)\
            """.format(tablename), (user_id, attr['game_state'], attr['games_played'], 
            attr['ended_session_count'], attr['guess_number'], attr['no_of_guesses']))
        print("high_low_game: user_id {} row created: auto increment row id: {}".format(user_id, 
            db_cursor.lastrowid))
    else:
        db_dict_cursor.execute("""\
            UPDATE {} SET game_state = %s, games_played = %s, ended_session_count = %s, \
            guess_number = %s, no_of_guesses = %s WHERE user_id = %s \
            """.format(tablename), (attr['game_state'], attr['games_played'], 
            attr['ended_session_count'], attr['guess_number'], attr['no_of_guesses'], user_id))
    return

class LaunchRequestHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_request_type("LaunchRequest")(handler_input)

    def handle(self, handler_input):
        print("session user=", handler_input.request_envelope.session.user)
        user_id = handler_input.request_envelope.session.user.user_id

        # Handler for Skill Launch
        print("Launch request: {}".format(
                handler_input.request_envelope.request))
        # Get the persistence attributes, to figure out the game state
        try:
            # attr = handler_input.attributes_manager.persistent_attributes
            attr = get_persistent_attributes(user_id)
            if not attr:
                print("Launch request: persistent_attributes in session = null, initializing..")
                attr['ended_session_count'] = 0
                attr['games_played'] = 0
                attr['game_state'] = 'ENDED'
                print("Launch request: persistent_attributes = {}".format(str(attr)))
            else:
                print("Launch request: persistent_attributes in session = {}".format(attr))
        except Exception as e:
            print("Launch request: Unexpected error:", sys.exc_info()[0])
            raise

        handler_input.attributes_manager.session_attributes = attr

        speech_text = (
            "Welcome to the High Low guessing game. You have played {} times. "
            "Would you like to play?".format(attr["games_played"]))
        reprompt = "Say yes to start the game or no to quit."

        handler_input.response_builder.speak(speech_text).ask(reprompt)
        return handler_input.response_builder.response


class HelpIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_intent_name("AMAZON.HelpIntent")(handler_input)

    def handle(self, handler_input):
        # Handler for Help Intent
        speech_text = (
            "I am thinking of a number between zero and one hundred, try to "
            "guess it and I will tell you if you got it or it is higher or "
            "lower")
        reprompt = "Try saying a number."

        handler_input.response_builder.speak(speech_text).ask(reprompt)
        return handler_input.response_builder.response


class CancelAndStopIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return (is_intent_name("AMAZON.CancelIntent")(handler_input) or
                    is_intent_name("AMAZON.StopIntent")(handler_input))

    def handle(self, handler_input):
        # Single handler for Cancel and Stop Intent
        speech_text = "Thanks for playing!!"

        handler_input.response_builder.speak(
            speech_text).set_should_end_session(True)
        return handler_input.response_builder.response


class SessionEndedRequestHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_request_type("SessionEndedRequest")(handler_input)

    def handle(self, handler_input):
        # Handler for Session End
        print(
            "Session ended with reason: {}".format(
                handler_input.request_envelope.request.reason))
        return handler_input.response_builder.response


def currently_playing(handler_input):
    is_currently_playing = False
    session_attr = handler_input.attributes_manager.session_attributes

    if ("game_state" in session_attr
            and session_attr['game_state'] == "STARTED"):
        is_currently_playing = True

    return is_currently_playing


class YesIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return (not currently_playing(handler_input) and
                    is_intent_name("AMAZON.YesIntent")(handler_input))

    def handle(self, handler_input):
        # Handler for Yes Intent, only if the player said yes for
        # a new game.
        session_attr = handler_input.attributes_manager.session_attributes
        session_attr['game_state'] = "STARTED"
        session_attr['guess_number'] = random.randint(0, 100)
        session_attr['no_of_guesses'] = 0

        speech_text = "Great! Try saying a number to start the game."
        reprompt = "Try saying a number."

        handler_input.response_builder.speak(speech_text).ask(reprompt)
        return handler_input.response_builder.response


class NoIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return (not currently_playing(handler_input) and
                    is_intent_name("AMAZON.NoIntent")(handler_input))

    def handle(self, handler_input):
        # Handler for No Intent, only if the player said no for
        # a new game.
        session_attr = handler_input.attributes_manager.session_attributes
        session_attr['game_state'] = "ENDED"
        session_attr['ended_session_count'] += 1

        # handler_input.attributes_manager.persistent_attributes = session_attr
        # handler_input.attributes_manager.save_persistent_attributes()
        user_id = handler_input.request_envelope.session.user.user_id
        save_persistent_attributes(user_id, session_attr)

        speech_text = "Ok. See you next time!!"

        handler_input.response_builder.speak(speech_text)
        return handler_input.response_builder.response


class NumberGuessIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return (currently_playing(handler_input) and
                    is_intent_name("NumberGuessIntent")(handler_input))

    def handle(self, handler_input):
        print("number_guess_handler: {}".format(
                handler_input.request_envelope.request))
        # Handler for processing guess with target
        session_attr = handler_input.attributes_manager.session_attributes
        target_num = session_attr["guess_number"]
        guess_num = int(handler_input.request_envelope.request.intent.slots[
            "number"].value)

        session_attr["no_of_guesses"] += 1

        if guess_num > target_num:
            speech_text = (
                "{} is too high. Try saying a smaller number.".format(guess_num))
            reprompt = "Try saying a smaller number."
        elif guess_num < target_num:
            speech_text = (
                "{} is too low. Try saying a larger number.".format(guess_num))
            reprompt = "Try saying a larger number."
        elif guess_num == target_num:
            speech_text = (
                "Congratulations. {} is the correct guess. "
                "You guessed the number in {} guesses. "
                "Would you like to play a new game?".format(
                    guess_num, session_attr["no_of_guesses"]))
            reprompt = "Say yes to start a new game or no to end the game"
            session_attr["games_played"] += 1
            session_attr["game_state"] = "ENDED"

            # handler_input.attributes_manager.persistent_attributes = session_attr
            # handler_input.attributes_manager.save_persistent_attributes()
            user_id = handler_input.request_envelope.session.user.user_id
            save_persistent_attributes(user_id, session_attr)
        else:
            speech_text = "Sorry, I didn't get that. Try saying a number."
            reprompt = "Try saying a number."

        handler_input.response_builder.speak(speech_text).ask(reprompt)
        return handler_input.response_builder.response


class FallbackIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return (is_intent_name("AMAZON.FallbackIntent")(handler_input) or
                    is_intent_name("AMAZON.YesIntent")(handler_input) or
                    is_intent_name("AMAZON.NoIntent")(handler_input))

    def handle(self, handler_input):
        # AMAZON.FallbackIntent is only available in en-US locale.
        # This handler will not be triggered except in that locale,
        # so it is safe to deploy on any locale
        print("fallback_handler: request={}".format(
                handler_input.request_envelope.request))

        session_attr = handler_input.attributes_manager.session_attributes

        if ("game_state" in session_attr and
                session_attr["game_state"]=="STARTED"):
            speech_text = (
                "The {} skill can't help you with that.  "
                "Try guessing a number between 0 and 100. ".format(SKILL_NAME))
            reprompt = "Please guess a number between 0 and 100."
        else:
            speech_text = (
                "The {} skill can't help you with that.  "
                "It will come up with a number between 0 and 100 and "
                "you try to guess it by saying a number in that range. "
                "Would you like to play?".format(SKILL_NAME))
            reprompt = "Say yes to start the game or no to quit."

        handler_input.response_builder.speak(speech_text).ask(reprompt)
        return handler_input.response_builder.response


class UnhandledIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return True

    def handle(self, handler_input):
        # Handler for all other unhandled requests
        speech = "Say yes to continue or no to end the game!!"
        handler_input.response_builder.speak(speech).ask(speech)
        return handler_input.response_builder.response


class AllExceptionHandler(AbstractExceptionHandler):
    def can_handle(self, handler_input, exception):
        return True

    def handle(self, handler_input, exception):
        # Catch all exception handler, log exception and
        # respond with custom message
        print("Encountered following exception: {}".format(exception))
        speech = "Sorry, I can't understand that. Please say again!!"
        handler_input.response_builder.speak(speech).ask(speech)
        return handler_input.response_builder.response


class LogResponseInterceptor(AbstractResponseInterceptor):
    def process(self, handler_input, response):
        print("Response : {}".format(response))


sb.request_handlers.extend([
    LaunchRequestHandler(),
    HelpIntentHandler(),
    CancelAndStopIntentHandler(),
    SessionEndedRequestHandler(),
    YesIntentHandler(),
    NoIntentHandler(),
    NumberGuessIntentHandler(),
    FallbackIntentHandler(),
    UnhandledIntentHandler()
    ])
sb.add_exception_handler(AllExceptionHandler())
sb.add_global_response_interceptor(LogResponseInterceptor())

handler = sb.lambda_handler()
