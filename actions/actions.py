# This files contains your custom actions which can be used to run
# custom Python code.
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions
# This is a simple example for a custom action which utters "Hello World!"

from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
import requests
import copy
from rasa_sdk.events import UserUtteranceReverted,ConversationPaused,FollowupAction,ActionExecuted,UserUttered,AllSlotsReset, SlotSet,EventType,Restarted,BotUttered
from rasa_sdk import Tracker
from rasa_sdk.forms import FormValidationAction
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.types import DomainDict
import random
from datetime import datetime
import pandas as pd
import numpy as np
import json
import re
from datetime import datetime as dt
from datetime import timedelta
from search_flight import city_to_airport,search_flight,search_flight_round,random_char,low

class ActionDefaultFallback(Action):
    """Executes the fallback action and goes back to the previous state
    of the dialogue"""

    def name(self) -> Text:
        return "action_default_fallback"

    async def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        dispatcher.utter_message("Something went wrong please start again!")

        # Revert user message which led to fallback.
        return [Restarted()]


class ActionRestart(Action):
    def name(self) -> Text:
        return "action_bye"

    def run(self, dispatcher, tracker, domain):
        # output a message saying that the conversation will now be
        # continued by a human.
        # pause tracker
        # undo last user interaction
        dispatcher.utter_message("Bye")
        return [Restarted()]


class ActionSearchAgain(Action):
    def name(self) -> Text:
        return "action_search_again"

    def run(self, dispatcher, tracker, domain):
        # output a message saying that the conversation will now be
        # continued by a human.
        # pause tracker
        # undo last user interaction
        print("restarted")
        events = [Restarted(),FollowupAction(name = "utter_greet_again")]
        #dispatcher.utter_message("Let's start again.How can I help you again?")
        return events

class ActionAllSlotReset(Action):

     def name(self) -> Text:
            return "action_reset_slots"

     def run(self, dispatcher: CollectingDispatcher,
             tracker: Tracker,
             domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

         dispatcher.utter_message("Something went wrong!")

         return [AllSlotsReset()]

def clean_name(name):
    return "".join([c for c in name if c.isalpha()])

class ValidateBookForm(Action):
    def name(self) -> Text:
        return "action_validate_form"
    
    def run(self, dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        dep=tracker.get_slot("departure")
        destination = tracker.get_slot("destination")
        print(dep)
        print(destination)
        # If the city is super short or has $ something like this, it might be wrong.
        name = clean_name(destination)
        if len(name) == 0:
            dispatcher.utter_message(text=f"That must've been a typo.")
            return [Restarted(),FollowupAction(name = "book_flight_form")]

        elif dep.lower()==destination.lower():
            dispatcher.utter_message(text=f"Departure and Destination cities can't be same.Please start again.")
            return [Restarted(),FollowupAction(name = "book_flight_form")]
        else:
            return [SlotSet("destination", destination)]


class ActionSendFlightInfo(Action):

    def name(self) -> Text:
        return "action_send_flight_info"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        email=tracker.get_slot("email")
        dispatcher.utter_message(text="I have sent your PNR number: {} flight information for to {} adress.Have a nice Trip.Do you need anything else?".format(random_char(5),email))
        return []

class ActionSearchflightCheap(Action):

    def name(self) -> Text:
        return "action_search_flight_cheapest"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
 
        latest_intent = tracker.latest_message['intent'].get('name')

        dep=tracker.get_slot("departure")
        des=tracker.get_slot("destination")
        no_people=tracker.get_slot("no_of_people")

        latest_intent = tracker.latest_message['intent'].get('name')
        print(latest_intent)
        if latest_intent ==  "inform_book_flight_with_date":
            print("latest_intent")
            try:
                depart_date=pd.DataFrame(tracker.latest_message["entities"])["additional_info"].dropna().iloc[0]["values"][0]["value"]
                return_date=pd.DataFrame(tracker.latest_message["entities"])["additional_info"].dropna().iloc[1]["values"][0]["value"]
            except:
                print("except worked inform_book_flight_with_date")
                depart_date=tracker.get_slot("time")
        else:
            date=tracker.get_slot("time")
            try:
                depart_date=date["from"]
                return_date=date["to"]
            except:
                print("only depart date worked")
                depart_date=date

        print(depart_date) 
        
        depart_date = dt.strptime(depart_date, "%Y-%m-%dT%H:%M:%S.%f%z").strftime("%Y-%m-%d")
        try:
            return_date = dt.strptime(return_date, "%Y-%m-%dT%H:%M:%S.%f%z").strftime("%Y-%m-%d")
            return_date=(dt.strptime(return_date,"%Y-%m-%d") - timedelta(1)).strftime('%Y-%m-%d')
            print(return_date)  
        except:
            return_date=None            
        
        if return_date is None:  
            
            departure=dep.lower()
            print("cheap depart",departure)
            destination=des.lower()
            print("cheap dest",destination)
            
            message="Here is the 'CHEAPEST' option."
            message=message+"On " + depart_date
            message=message+" From " + departure + " to " + destination
            message_df=pd.read_excel("src/prices.xlsx",sheet_name="one")            
            search_message=message_df[(message_df["cheap"]==1) & (message_df["Departure"].apply(low)==departure) & (message_df["Destination"].apply(low)==destination)]["Message"].values[0]     

            #search_message=search_flight(departure[0],destination[0],depart_date,sort="cheapest")

            print(search_message)
            message=message+search_message
            message=message+"...Do you want me to book this flight for you?"

            #dispatcher.utter_message(text=message)
        else:

            departure=dep.lower()
            destination=des.lower()
            message="Here is the 'CHEAPEST' option."

            message=message+"On " + depart_date  + " - " + return_date + " "
            message=message+" From " + departure + "to " + destination + + " "
            message_df=pd.read_excel("src/prices.xlsx",sheet_name="round")            
            search_message=message_df[(message_df["cheap"]==1) & (message_df["Departure"].apply(low)==departure) & (message_df["Destination"].apply(low)==destination)]["Message"].values[0]     
            
            # search_message=search_flight_round(departure[0],destination[0],depart_date,return_date,sort="cheapest")
            print(search_message)
            
            text="Something went wrong while searching the flight,please say 'Search again'"
            message=message+search_message
            message=message+"...Do you want me to book this flight for you?"

        if search_message=='-------> ':
            dispatcher.utter_message(text=text)
            print("search empty")
        else:
            dispatcher.utter_message(text=message)
            print("search doesnt empty")
        return []

class ActionSearchflight(Action):

    def name(self) -> Text:
        return "action_search_flight"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
 
        latest_intent = tracker.latest_message['intent'].get('name')


        dep=tracker.get_slot("departure")
        des=tracker.get_slot("destination")
        no_people=tracker.get_slot("no_of_people")

        latest_intent = tracker.latest_message['intent'].get('name')
        print(latest_intent)
        if latest_intent ==  "inform_book_flight_with_date":
            print("latest_intent")
            try:
                depart_date=pd.DataFrame(tracker.latest_message["entities"])["additional_info"].dropna().iloc[0]["values"][0]["value"]
                return_date=pd.DataFrame(tracker.latest_message["entities"])["additional_info"].dropna().iloc[1]["values"][0]["value"]
            except:
                print("except worked inform_book_flight_with_date")
                depart_date=tracker.get_slot("time")
        else:
            date=tracker.get_slot("time")
            try:
                depart_date=date["from"]
                return_date=date["to"]
            except:
                print("only depart date worked")
                depart_date=date
 
        
        depart_date = dt.strptime(depart_date, "%Y-%m-%dT%H:%M:%S.%f%z").strftime("%Y-%m-%d")
        print("Departure date: ",depart_date)
        try:
            return_date = dt.strptime(return_date, "%Y-%m-%dT%H:%M:%S.%f%z").strftime("%Y-%m-%d")
            return_date=(dt.strptime(return_date,"%Y-%m-%d") - timedelta(1)).strftime('%Y-%m-%d')
            print("Return date:",return_date)  
        except:
            return_date=None            
        
        if return_date is None:  
            
            departure=dep.lower()
            print(departure)
            destination=des.lower()
            print(destination)
            
            message = "Here is the 'BEST' option based on duration. "

            message=message+"On " + depart_date 
            message=message+" From " + departure + " to " + destination + " "
            message_df=pd.read_excel("src/prices.xlsx",sheet_name="one")            
            search_message=message_df[(message_df["cheap"]==0) & (message_df["Departure"].apply(low)==departure) & (message_df["Destination"].apply(low)==destination)]["Message"].values[0]      
            

            #search_message=search_flight(departure[0],destination[0],depart_date)
            print("aaaa",search_message)
            text="Something went wrong while searching the flight,please say 'Book me again'"
            message=message+search_message

            message=message+"...Do you want me to book this flight for you? Otherwise,I have have some cheaper options,just say 'Show me cheap one'"

            #dispatcher.utter_message(text="Here is the 'Best' option based on duration and price.From {} to {} for {} USD at {} ---> {}".format(dep,des,df["Price"][0],depart_date,df['First Flight'][0]))
        else:

            departure=dep.lower()
            print(departure)
            destination=des.lower()
            print(destination)
            
            message = "Here is the 'BEST' option based on duration. "

            message=message+"On " + depart_date  + " - " + return_date
            message=message+" From " + departure + "to " + destination + " "
            message_df=pd.read_excel("src/prices.xlsx",sheet_name="round")          
            search_message=message_df[(message_df["cheap"]==0) & (message_df["Departure"].apply(low)==departure) & (message_df["Destination"].apply(low)==destination)]["Message"].values[0]         
            
            #search_message=search_flight_round(departure[0],destination[0],depart_date,return_date)
            print([search_message])
            text="Something went wrong while searching the flight,please say 'Book me again'"
            message=message+search_message
            message=message+"...Do you want me to book this flight for you? Otherwise,I have have some cheaper options,just say 'Show me cheap one'"
        
        if search_message=='-------> ':
            dispatcher.utter_message(text=text)
            print("search empty")
        else:
            dispatcher.utter_message(text=message)
            print("search doesnt empty")
        return []

            
class ActionVerifyPeople(Action):

    def name(self) -> Text:
        return "action_verify_no_people"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        latest_intent = tracker.latest_message['intent'].get('name')
        print(latest_intent)
        if latest_intent ==  "inform_no_people":
            print(latest_intent)
            no_people=tracker.get_slot("no_of_people")
            dispatcher.utter_message(text="You mean, {}, right?".format(no_people))
        else:
            dispatcher.utter_message(text="I didn't understand,how many ticket would you like?")
        return []

class ActionVerifyDate(Action):

    def name(self) -> Text:
        return "action_verify_date"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        latest_intent = tracker.latest_message['intent'].get('name')
        if latest_intent ==  "inform_flight_date":
            #if it is round trip,there are to variable otherwise there is only depart_date
            print(latest_intent)
            try:
                depart_date=pd.DataFrame(tracker.latest_message["entities"])["additional_info"].dropna().values[0]["values"][0]["from"]["value"]
                return_date=pd.DataFrame(tracker.latest_message["entities"])["additional_info"].dropna().values[0]["values"][0]["to"]["value"]
                depart_date=dt.strptime(depart_date, "%Y-%m-%dT%H:%M:%S.%f%z").strftime("%Y-%m-%d")
                return_date=dt.strptime(return_date, "%Y-%m-%dT%H:%M:%S.%f%z").strftime("%Y-%m-%d")

                return_date=(dt.strptime(return_date,"%Y-%m-%d") - timedelta(1)).strftime('%Y-%m-%d')

                dispatcher.utter_message(text="You mean, {} to {}, right?".format(depart_date,return_date))
            except:
                print("except worked inform_flight_date")
                depart_date=tracker.get_slot("time")
                depart_date=dt.strptime(depart_date, "%Y-%m-%dT%H:%M:%S.%f%z").strftime("%Y-%m-%d")
                dispatcher.utter_message(text="You mean, {}, right?".format(depart_date))

        else:
            dispatcher.utter_message(text="I didn't understand,please tell me when would you like to flight?")
        return []

class ActionVerifyDeparture(Action):

    def name(self) -> Text:
        return "action_verify_departure"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        latest_intent = tracker.latest_message['intent'].get('name')
        if latest_intent ==  "inform_departure_city":
            print(latest_intent)
            depart_city=tracker.get_slot("departure")
            dispatcher.utter_message(text="You mean, {}, right?".format(depart_city))
        else:
            dispatcher.utter_message(text="I didn't understand,what is your departure city?")
        return []

class ActionVerifyDestination(Action):

    def name(self) -> Text:
        return "action_verify_destination"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        latest_intent = tracker.latest_message['intent'].get('name')
        if latest_intent ==  "inform_destination_city":
            print(latest_intent)
            destination_city=tracker.get_slot("destination")
            dispatcher.utter_message(text="You mean, {}, right?".format(destination_city))
        else:
            dispatcher.utter_message(text="I didn't understand,what is your destination city?")
        return []

class ActionVerifyflight(Action):

    def name(self) -> Text:
        return "action_verify_flight"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
 
        latest_intent = tracker.latest_message['intent'].get('name')


        dep=tracker.get_slot("departure")
        des=tracker.get_slot("destination")
        no_people=tracker.get_slot("no_of_people")

        latest_intent = tracker.latest_message['intent'].get('name')
        print(latest_intent)
        if latest_intent ==  "inform_book_flight_with_date":
            print("latest_intent")
            print(tracker.latest_message["entities"])
            try:
                depart_date=pd.DataFrame(tracker.latest_message["entities"])["additional_info"].dropna().iloc[0]["values"][0]["value"]
                return_date=pd.DataFrame(tracker.latest_message["entities"])["additional_info"].dropna().iloc[1]["values"][0]["value"]
            except:
                print("except worked inform_book_flight_with_date")
                depart_date=tracker.get_slot("time")
        else:
            date=tracker.get_slot("time")
            try:
                depart_date=date["from"]
                return_date=date["to"]
            except:
                print("only depart date worked")
                depart_date=date

        print(depart_date) 
        
        depart_date = dt.strptime(depart_date, "%Y-%m-%dT%H:%M:%S.%f%z").strftime("%Y-%m-%d")
        try:
            return_date = dt.strptime(return_date, "%Y-%m-%dT%H:%M:%S.%f%z").strftime("%Y-%m-%d")
            return_date=(dt.strptime(return_date,"%Y-%m-%d") - timedelta(1)).strftime('%Y-%m-%d')
            print(return_date)  
        except:
            return_date=None            
        
        if return_date is not None:
            dispatcher.utter_message(text="I am going to search flight from {} to {} on {} - {} for {} people, can you please confirm that? Or just say 'Start again' for new query.".format(dep,des,depart_date,return_date,no_people))
        else:
            dispatcher.utter_message(text="I am going to search flight from {} to {} on {} for {} people, can you please confirm that? Or just say 'Start again' for new query.".format(dep,des,depart_date,no_people))
        return []


class ActionAirport_Airlines(Action):

    def name(self) -> Text:
        return "action_airport_airlines_info"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        airport_or_airline_code = tracker.get_slot("airline_or_airport_code")
        airport_name = tracker.get_slot("airport_name")
        if airport_name is None:
            df=pd.read_excel("src/airportcodes.xlsx",sheet_name="Sheet1")

            airline_name=df[df["Code"]==airport_or_airline_code.upper()]["Airport Name"].values[0]
            country=df[df["Code"]==airport_or_airline_code.upper()]["City or Airline"].values[0]
            dispatcher.utter_message(text="It is stand for {} located in {}".format(airline_name,country))
        else:
            df=pd.read_excel("src/airportcodes.xlsx",sheet_name="Sheet1")
            airport_city_name=df[df["airport_name"]==airport_name.upper()]["City or Airline"].values[0]
            country=df[df["airport_name"]==airport_name.upper()]["Country"].values[0]
            dispatcher.utter_message(text="It is an airport located in {}, with short name {}".format(country,airport_city_name))

        return []

class ActionDestinationSlotReset(Action):

     def name(self) -> Text:
            return "action_reset_destination"

     def run(self, dispatcher: CollectingDispatcher,
             tracker: Tracker,
             domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

         return [SlotSet("destination", None)]
