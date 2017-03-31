#! usr/bin/env python
import simpy
import pandas as pd
import pymc3
import scipy
import numpy as np
#


class Bank_Account_Flow(object):
    """Model clients opening and closing a bank account over time."""
    def __init__(self, env, average_number_of_meetings_per_week=100,
                 average_weekly_conversion_meeting_client=.05,
                 std_weekly_conversion_meeting_client=.05,
                 average_client_lifetime_weeks=10,
                 time_to_open_bank_account=.05,
                 time_between_bank_account_credit_card=20):
        self.average_number_of_meetings_per_week = \
            average_number_of_meetings_per_week
        self.average_weekly_conversion_meeting_client = \
            average_weekly_conversion_meeting_client
        self.std_weekly_conversion_meeting_client = \
            std_weekly_conversion_meeting_client
        self.average_client_lifetime_weeks = \
            average_client_lifetime_weeks
        self.time_to_open_bank_account = \
            time_to_open_bank_account
        self.time_between_bank_account_credit_card = time_between_bank_account_credit_card

        self.total_clients_with_bankaccount = 0
        self.total_clients_with_credit_card = 0

        self.env = env
        self.meet_client()
        self.total_clients()
        self.client_lifetimes = []

        self.list_of_all_clients = []

        self.open_cc_process =None

    def meet_client(self):
        """A random number of meetings with prospective client per week.
        Returns a random number of meetings per week"""
        number_of_meetings = np.random.poisson(
            lam=self.average_number_of_meetings_per_week)
        self.number_of_meetings = number_of_meetings

    def total_clients(self):
        """Takes the number of clients that were meet in the past week.
        And return the number that ultimately become prospects.
        This assumes the conversion rate is a normal distribution.
        This returns the number of prospects/clients for the week"""
        conversion_rate = np.random.normal(loc=
                self.average_weekly_conversion_meeting_client ,
                scale = self.std_weekly_conversion_meeting_client)
        if conversion_rate<0: ##  can't have negative
            conversion_rate = .0001
        self.conversion_rate = conversion_rate
        total_clients = self.number_of_meetings*conversion_rate
        self.total_clients = round(total_clients) # for the week
        self.time_between_clients = self.total_clients / 7

    def initiate_client_run(self):
        """This is the main function for initiating clients throughout the time
        at the bank. The number of customers is an input which is given when you
        instantiate this class.

        This function uses an exponential distribution to find the
        customer_lifetime for each client. Then, each customer opoens up
        a bank account, when the time between each customer given by
        a normal distribution of conversion rate from the number of meetings
        to client.

        This function calls sub functions 'open bank account' and 'close bank
        account' with a simpy process wrapper to keep track of the time for each.

        In addition, this function keep a class accumulator for the total number
        of customers that have a bank account at any given time. This
        can be used to calculate the LTV for these customers.

        """
        for client_id in range(self.total_clients):
            # number of client for this week
            client_lifetime = np.random.exponential(scale =
                                        self.average_client_lifetime_weeks)
            self.client_lifetimes.append(client_lifetime)
            #client_process = self.env.processs()
            client = Client(client_id, client_lifetime)
            self.list_of_all_clients.append(client)
            # start the process for each customer's lifetime
            print('The client lifetime for customer {} is {} weeks'.format(
                client.client_id,client.client_lifetime))
            # how frequently do coustomers come in?
            # weekly average for the number of customers
            time_between_clients = \
                round(np.random.exponential(1/self.time_between_clients),2)
            print('The time between each clients is {} weeks'.format(
                time_between_clients))
            ## Now, either open a bank account, or close a bank account depending
            # on the customer's lifetime
            # # Either open bank account for next customer, of close bank account
            # # for previous customer

            open_bank_process = self.env.process(
                self.open_bank_account('Customer%02d' % client.client_id,
                                                          client))
            close_bank_process = self.env.process(self.close_bank_account(client))
            open_bank_process | close_bank_process

            # Below, is the time between customers or the 'flow' of customers
            yield self.env.timeout(time_between_clients)
            ### ASSUMPTION ####
            ### This is assuming that the first thing a client will do is open a

        for client_object in self.list_of_all_clients:
            open_cc_process = self.env.process(self.open_credit_card(client_object))
            # open_cc = self.open_credit_card(client)
            # close_bank = self.env.process(self.close_bank_account(client_object))
            self.open_cc_process = open_cc_process
            open_cc_process | close_bank_process


            # for client_object in self.list_of_all_clients:
            #
            #
            #     open_cc_process = self.env.process(self.open_credit_card(client_object))
            #     open_cc = self.open_credit_card(client_object)
            #     # close_bank = self.env.process(self.close_bank_account(client_object))
            #     open_cc_process | close_bank_process




                #received this  week


    def open_bank_account(self, client_id, client):
        """This is a simpy process for creating a bank account"""
        print()
        #print(' {} opened a bank account'.format(customer_id))
        print("Client {} is opening a bank account at time={}".format(
                            client.client_id, self.env.now))
        self.total_clients_with_bankaccount += 1
        print(' There are {} people with bank accounts at time-weeks {}'.format(
            self.total_clients_with_bankaccount, round(self.env.now,2)))

        yield self.env.timeout(self.time_to_open_bank_account, value='open')
        client.time_bank_was_opened = self.env.now

        #response = yield self.env.timeout(self.time_to_open_bank_account, value='open') | \
        #    self.env.process(self.close_bank_account(customer_id, cust_lifetime))


    def close_bank_account(self, client):
        """If a client's lifetime is reached, their bank account is closed.
        This assumes that the client is dead and can no longer open up additional
        products"""
        #print(client.bank_closed, ' CHECKGIN BANK CLOSED')
        #print(client.client_id,'cleint id')
        if client.time_bank_closed == None: # see if we already closed this account
            yield self.env.timeout(client.client_lifetime)
            print("WE CLOSED AN ACCOUNT for client {}".format(client.client_id))
            self.total_clients_with_bankaccount -= 1
            client.time_bank_closed = self.env.now
            print(client.time_bank_closed , ' Bank was closed at this time !')
            print('Total people with bank accounts= {} at time= {}'.format(
                self.total_clients_with_bankaccount, self.env.now))
            #self.env.interrupt()
        else: # we already closed this account
            print('We ALREADY closed client {} bank account at time {}'.format(
                client.client_id, client.time_bank_closed
            ))
            pass

    def open_credit_card(self,client):
        """A Simpy process for opening up credit cards. This assumes that
        a credit card can only be opened up AFTER opening a bank account."""


        time_between_bank_account_credit_card = np.random.exponential(scale =
                                    self.time_between_bank_account_credit_card )
        print("Client {} will open a credit card at {}".format(
           client.client_id, time_between_bank_account_credit_card))
        if client.time_between_bank_and_cc == None:
            client.time_between_bank_and_cc = time_between_bank_account_credit_card
        else: # already have a time to open the CC at
            pass


        # if (client.time_credit_card_opened == None) and\
        #     (client.time_bank_was_opened != None) and \
        #     (self.env.now > client.time_bank_was_opened ) and \
        #     (client.time_bank_closed==None):
        if (client.time_credit_card_opened == None) and \
            (client.time_bank_closed==None):
            # No credit card opened but a bank account was opened

            yield self.env.timeout(client.time_between_bank_and_cc)

            client.time_credit_card_opened = self.env.now
            print(" Client {} opened a credit card at time = {}, the time between the bank opened \
                  and credit open was {}".format(client.client_id,self.env.now,
                                                 client.time_between_bank_and_cc))
            self.total_clients_with_credit_card  += 1
            print('The total number of clients with credit cards are {}'.format(
                self.total_clients_with_credit_card
            ))
        else: # a bank account was not opened yet
            #Need to interrupt this process
            #raise RuntimeError
            #self.open_cc_process.interrupt()
            print("failed to open credit card")

class Client(object):
    """This is the base class to represent client that enter the bank.
    The class will contain attributes such as lifetime, when their bank account
    was opened ...etc"""

    def __init__(self, client_id, client_lifetime):
        """Initialize with the client ID and lifetime. As the time progresses,
        keep track of different events that occur."""
        self.client_id = client_id
        self.client_lifetime = client_lifetime
        self.time_bank_closed = None
        self.time_credit_card_opened = None
        self.time_bank_was_opened = None
        self.time_between_bank_and_cc = None





if __name__ == "__main__":


    # average_number_of_meetings_per_week = 50
    # average_weekly_conversion_meeting_client = .05
    # std_weekly_conversion_meeting_client = .05
    # total_customer_with_bankaccount = 0
    # average_customer_lifetime_weeks = 10

    # # defiing the meting - client generator for the week
    # number_of_meetings = meet_customer(average_number_of_meetings_per_week)
    # print(number_of_meetings, " NUmber of meetings this week")
    # total_clientsorprospects = prospect(number_of_meetings,
    #                                     average_weekly_conversion_meeting_client,
    #                                     std_weekly_conversion_meeting_client)
    # print("Total number of clients from the meetings {}".format(
    #     total_clientsorprospects
    # ))

    env = simpy.Environment()
    bank_account_flow = Bank_Account_Flow(env)

    env.process(bank_account_flow.initiate_client_run())

    env.run(until=120) # one year
    print('Finished at time {}'.format(env.now))
    print("Number of clients for this week {}".format(
        bank_account_flow.total_clients))
    print("Number of meetings for the week {}".format (
        bank_account_flow.number_of_meetings
    ))
    print("The conversion rate is {}".format(bank_account_flow.conversion_rate))
    print("Client lifetimes = {}".format(bank_account_flow.client_lifetimes))
    print("All clients {} ".format( bank_account_flow.list_of_all_clients))
