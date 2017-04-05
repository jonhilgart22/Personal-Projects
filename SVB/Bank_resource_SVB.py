#! usr/bin/env python
import simpy
import simpy
import pandas as pd
import pymc3
import scipy
import numpy as np
__author__='Jonathan Hilgart'





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
        self.bank_account_resource_request = None
        self.credit_card_resource_request = None



class Bank_Account_Flow(object):
    """Model clients opening and closing a bank account over time.
    Note, all time units are in terms of one week. One day would correspond
    to 1/7 of a week or .143."""
    def __init__(self, env, average_number_of_meetings_per_week=100,
                 average_weekly_conversion_meeting_client=.05,
                 std_weekly_conversion_meeting_client=.05,
                 average_client_lifetime_weeks=10,
                 time_to_open_bank_account=.05,
                 time_between_bank_account_credit_card=2,
                 bank_capacity=1000,
                 cc_capacity=200):
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
        self.time_between_bank_account_credit_card =\
         time_between_bank_account_credit_card

        self.bank_account_resource = simpy.Resource(env, capacity=bank_capacity)
        self.credit_card_resource = simpy.Resource(env, capacity=cc_capacity)


        self.time_series_client_with_bankaccount = []
        self.time_series_client_with_cc = []


        self.env = env
        self.meet_client()
        self.total_clients()
        self.client_lifetimes = []

        self.list_of_all_clients = []

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

            open_bank_process = self.env.process(self.open_bank_account(client))
            close_accounts = self.env.process(self.close_accounts(client))
            ## which one finishes first
            open_bank_process | close_accounts

            # Below, is the time between customers or the 'flow' of customers
            yield self.env.timeout(time_between_clients)
            open_credit_card = self.env.process(self.open_credit_cart(client))

            open_credit_card | close_accounts
            ### ASSUMPTION ####
            ### This is assuming that the first thing a client will do is open a

    def monitor_resource(self, resource, resource_name):
        """Print out monitoring statistics for a given resource.
        NUmber of slots allocated.
        Number of people using the resource
        Number of queued events for the resource"""
        print()
        print("MONITORING STATISTICS FOR {}".format(resource_name))
        print('{} of {} slots are allocated at time {}.'.format (
            resource.count, resource.capacity, self.env.now))
        print('  Users :', resource.users)
        print('  Queued events:', resource.queue)
        print()

    def open_bank_account(self, client):
        """This is a simpy process for creating a bank account"""

        open_bank_acct = self.bank_account_resource.request()
                # Wait until its our turn or until or the customer churns
        yield open_bank_acct
        ## Monitoring block

            ## wait some time until the next client can open a bank account
        yield self.env.timeout(self.time_to_open_bank_account)

        print("Client {} is opened a bank account at time={}".format(
                                 client.client_id, self.env.now))
            ## keep track of the number of people with bank accounts
        self.monitor_resource(self.bank_account_resource,'bank_account_opening')

        self.time_series_client_with_bankaccount.append(("Time =",
            self.env.now,self.bank_account_resource.count))
        client.time_bank_was_opened = self.env.now

        client.bank_account_resource_request = open_bank_acct


    def close_accounts(self, client):
        """If a client's lifetime is reached, their bank account is closed.
        This assumes that the client is dead and can no longer open up additional
        products"""

        if client.time_bank_closed == None: # see if we already closed this account
            yield self.env.timeout(client.client_lifetime)
            print("WE CLOSED AN ACCOUNT for client {}".format(client.client_id))
            # release the bank account resource
            self.bank_account_resource.release(
                client.bank_account_resource_request)

            # track the number of clients over time
            self.time_series_client_with_bankaccount.append(("Time =",
                self.env.now,self.bank_account_resource.count))
                # try to release the credit card resource (if a client has a CC)
            try:
                self.credit_card_resource.release(client.credit_card_resource_request)
                self.time_between_bank_account_credit_card.append(("time = ",
                    self.env.now, self.credit_card_resource.count))
            except: # this client didn't have a credit card
                print('error closing credit card!!')

            client.time_bank_closed = self.env.now
            print(client.time_bank_closed , ' Bank was closed at this time !')

            #self.env.interrupt()
        else: # we already closed this account
            print('We ALREADY closed client {} bank account at time {}'.format(
                client.client_id, client.time_bank_closed
            ))
            pass


    def open_credit_cart(self,client):
        """Try to open a credit card for the client.
        A client needs to have a bank account before getting a credit card.
        A client can not open a credit card if they have churned."""

        if client.client_lifetime < self.env.now:
            print("Customer {} tried to open a CC but already churned".format(
                client.client_id
            ))
        else:
            with self.credit_card_resource.request() as open_cc:
                # Time between bank account and credit card
                yield self.env.timeout(self.time_between_bank_account_credit_card)
                # CC requet
                cc_request = self.credit_card_resource.request()
                yield cc_request # request was successful

                print()
                print("Client {} is opening a credit card at time={}".format(
                                         client.client_id, self.env.now))


                    ## wait some time until the next client can open a bank account
                print('Time to wait between bank account and credit card is {}, \
                      client {} will open a CC at time {}'.format(
                      self.time_between_bank_account_credit_card,
                      client.client_id, self.env.now+self.time_between_bank_account_credit_card))

                    ## keep track of the number of people with credit cards
                self.monitor_resource(self.credit_card_resource, 'credit_card')

                self.time_series_client_with_cc.append(("Time = {}",
                    self.env.now,self.credit_card_resource.count))
                client.time_credit_card_opened= self.env.now
                # Store the CC request
                client.credit_card_resource_request = cc_request



if __name__ == "__main__":
    env = simpy.Environment()
    bank_account_flow = Bank_Account_Flow(env)

    env.process(bank_account_flow.initiate_client_run())

    until = 15
    while env.peek() < until:
        env.step()

    print('Finished at time {}'.format(env.now))
    print("Number of clients for this week {}".format(
        bank_account_flow.total_clients))
    print("Number of meetings for the week {}".format (
        bank_account_flow.number_of_meetings
    ))
    print("The conversion rate is {}".format(bank_account_flow.conversion_rate))
    print("Client lifetimes = {}".format(bank_account_flow.client_lifetimes))
    print("Time series of bank accounts {} ".format(
        bank_account_flow.time_series_client_with_bankaccount))
    print("Time series of people with credit cards {}".format(
        bank_account_flow.time_series_client_with_cc))
