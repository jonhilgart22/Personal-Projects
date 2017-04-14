#! usr/bin/env python
import simpy
import scipy.stats as stats
import pandas as pd
import pymc3
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

        self.esp_open_money_market_bonus_request = None
        self.esp_open_collateral_mma_request  = None
        self.esp_open_cash_management_request = None
        self.esp_open_fx_request = None
        self.esp_open_letters_of_credit_request = None
        self.esp_open_enterprise_sweep_request = None
        self.esp_open_checking_request = None

        self.credit_card_resource_request = None



class ESP_Accelerator_Stripe_flow(object):
    """Model clients opening and closing a bank account over time.
    Note, all time units are in terms of one week. One day would correspond
    to 1/7 of a week or .143."""
    def __init__(self, env, average_client_lifetime_weeks=10,
                 time_to_open_bank_account=.05,
                 time_between_bank_account_credit_card=2,
                 number_of_weeks_to_run = 2,
                 esp_open_money_market_bonus_capacity=1000,
                 esp_open_collateral_mma_capacity =1000,
                 esp_open_cash_management_capacity = 1000, esp_fx_capacity = 1000,
                 esp_open_letters_of_credit_capacity = 1000,
                 esp_open_enterprise_sweep_capacity = 1000,esp_open_checking_capacity = 1000,


                 cc_capacity=200, esp_capacity = 5000,
                 stripe_capacity=3000):
        self.env = env

        #self.average_client_lifetime_weeks = \
            #average_client_lifetime_weeks
        #self.time_to_open_bank_account = \
            #time_to_open_bank_account
        #self.time_between_bank_account_credit_card =\
         #time_between_bank_account_credit_card

        self.number_of_weeks_to_run = number_of_weeks_to_run

        self.esp_money_market_bonus_resource = simpy.Resource(env, capacity=esp_open_money_market_bonus_capacity)
        self.esp_collateral_mma_resource = simpy.Resource(env, capacity=esp_open_collateral_mma_capacity)
        self.esp_cash_management_resource=  simpy.Resource(env, capacity=esp_open_cash_management_capacity)
        self.esp_fx_resource = simpy.Resource(env, capacity=esp_fx_capacity)
        self.esp_letters_of_credit_resource = simpy.Resource(env, capacity=esp_open_letters_of_credit_capacity )
        self.esp_enterprise_sweep_resource = simpy.Resource(env, capacity=esp_open_enterprise_sweep_capacity )
        self.esp_checking_resource = simpy.Resource(env, capacity= esp_open_checking_capacity )

        #self.credit_card_resource = simpy.Resource(env, capacity=cc_capacity)
        #self.esp_team_resource =  simpy.Resource(env, capacity=esp_capacity)
        #self.accelerator_team_resource =  simpy.Resource(env, capacity=acceleartor_capacity)
        #self.stripe_team_resource = simpy.Resource(env, capacity=stripe_capacity)

        self.time_series_esp_money_market_bonus = []
        self.time_series_esp_collateral_mma = []
        self.time_series_esp_cash_management = []
        self.time_series_esp_fx = []
        self.time_series_esp_letters_of_credit = []
        self.time_series_esp_enterprise_sweep = []
        self.time_series_esp_checking= []


        #self.time_series_client_with_bankaccount = []
        #self.time_series_client_with_cc = []
        #self.env = env
        #self.client_lifetimes = []

        #self.list_of_all_clients = []

    def esp_clients_per_week(self,mean=20.433962264150942, std=3.5432472792051746):
        """This generates the number of new clients in ESP for a given week.
        The default parameters are taken from the years 2013-2016."""
        self.oneweek_esp_clients = round(stats.norm.rvs(mean,std))
        if self.oneweek_esp_clients <0:
            self.oneweek_esp_clients = 0

    def accelerator_clients_per_week(self,mean=4.1792452830188678,
                                     std=0.92716914151900442):
        """This generates the number of new clients in accelerator for a given week.
        The default parameters are taken from the years 2013-2016"""
        self.oneweek_accelerator_clients = round(stats.norm.rvs(mean,std))
        if self.oneweek_accelerator_clients < 0:
            self.oneweek_accelerator_clients =0

    def stripe_clients_per_week(self,mean =23.209302325581394,
                                std =12.505920717868896):
        """"This generates the number of new Stripe customers from the given week.
        The default parameters from from 2016"""

        self.oneweek_stripe_clients = round(stats.norm.rvs(mean, std))
        if self.oneweek_stripe_clients < 0:
            self.oneweek_stripe_clients = 0

    def time_between_esb_accelerator(self,shape = 1.3513865965152867,
        location = -0.85750795314579964, scale = 57.412494398862549):
        """This is an exponential distribution of the average time between
        a client being in the esp team and being moved to the acceleartor team.
        Default parameters are from 2000-2016"""
        self.time_between_esb_accelerator = stats.gamma.rvs(shape, location, scale)
        if self.time_between_esb_accelerator <0:
            self.time_between_esb_accelerator = 1
            # at least one week before transferring to accelerator

    # def total_clients(self):
    #     """Takes the number of clients that were meet in the past week.
    #     And return the number that ultimately become prospects.
    #     This assumes the conversion rate is a normal distribution.
    #     This returns the number of prospects/clients for the week"""
    #     conversion_rate = np.random.normal(loc=
    #             self.average_weekly_conversion_meeting_client ,
    #             scale = self.std_weekly_conversion_meeting_client)
    #     if conversion_rate<0: ##  can't have negative
    #         conversion_rate = .0001
    #     self.conversion_rate = conversion_rate
    #     total_clients = self.number_of_meetings*conversion_rate
    #     self.total_clients = round(total_clients) # for the week
    #     self.time_between_clients = self.total_clients / 7

    def initiate_week_client_run(self, esp_mean=20.433962264150942,
        esp_std=3.5432472792051746, accel_mean = 4.1792452830188678,
        accel_std = 0.92716914151900442, stripe_mean = 23.209302325581394,
        stripe_std = 12.505920717868896):
        """This is the main function for initiating clients throughout the time
        at the bank. The number of customers is an input which is given when you
        instantiate this class.

        This function steps through the simulated time one week at a time
        and keeps track of the number of clients at each node during this simulation.

        This function calls sub functions 'open bank account' and 'close bank
        account' with a simpy process wrapper to keep track of the time for each.

        In addition, this function keep a class accumulator for the total number
        of customers that have a bank account at any given time. This
        can be used to calculate the LTV for these customers.

        """
        for week_n in range(self.number_of_weeks_to_run):
            print("WEEK NUMBER {}".format(week_n))
            ## generate new clients for each channel
            self.esp_clients_per_week(esp_mean,esp_std)
            self.accelerator_clients_per_week(accel_mean, accel_std)
            self.stripe_clients_per_week(stripe_mean, stripe_std)
            print(self.oneweek_esp_clients, ' ESP clients this week')
            print(self.oneweek_accelerator_clients, "acceleartor clinets this week")
            print(self.oneweek_stripe_clients, ' stripe clients this week')
            for esp_client_n in range(int(self.oneweek_esp_clients)):
                esp_client = Client(str(esp_client_n)+'-'+str(week_n),10) # default client lifetime
                open_mmb = self.env.process(self.esp_open_money_market_bonus(esp_client))
                open_cmma = self.env.process(self.esp_open_collateral_mma(esp_client))
                open_ocm = self.env.process(self.esp_open_cash_management(esp_client))
                open_fx = self.env.process(self.esp_open_fx(esp_client))
                open_loc = self.env.process(self.esp_open_letters_of_credit(esp_client))
                open_es = self.env.process(self.esp_open_enterprise_sweep(esp_client))
                open_c = self.env.process(self.esp_open_checking(esp_client))
                yield open_mmb & open_cmma & open_ocm & open_fx & open_loc & \
                    open_es & open_c

            ## add in the number of clients for each week
            self.time_series_esp_money_market_bonus.append(("Time = {}",
                self.env.now,self.esp_money_market_bonus_resource.count))
            self.time_series_esp_collateral_mma.append(("Time = {}",
                self.env.now,self.esp_collateral_mma_resource.count))
            self.time_series_esp_cash_management.append(("Time = {}",
                self.env.now,self.esp_cash_management_resource.count))
            self.time_series_esp_fx.append(("Time = {}",
                self.env.now,self.esp_fx_resource.count))
            self.time_series_esp_letters_of_credit.append(("Time = {}",
                self.env.now,self.esp_letters_of_credit_resource.count))
            self.time_series_esp_enterprise_sweep.append(("Time = {}",
                self.env.now,self.esp_enterprise_sweep_resource.count))
            self.time_series_esp_checking.append(("Time = {}",
                self.env.now,self.esp_checking_resource.count))


            one_week_increment = self.env.timeout(1)
            yield one_week_increment

            ## need to generate wait times to open each product


        #
        # for client_id in range(self.total_clients):
        #     # number of client for this week
        #     client_lifetime = np.random.exponential(scale =
        #                                 self.average_client_lifetime_weeks)
        #     self.client_lifetimes.append(client_lifetime)
        #     #client_process = self.env.processs()
        #     client = Client(client_id, client_lifetime)
        #     self.list_of_all_clients.append(client)
        #     # start the process for each customer's lifetime
        #     print('The client lifetime for customer {} is {} weeks'.format(
        #         client.client_id,client.client_lifetime))
        #     # how frequently do coustomers come in?
        #     # weekly average for the number of customers
        #     time_between_clients = \
        #         round(np.random.exponential(1/self.time_between_clients),2)
        #     print('The time between each clients is {} weeks'.format(
        #         time_between_clients))
        #     ## Now, either open a bank account, or close a bank account depending
        #     # on the customer's lifetime
        #     # # Either open bank account for next customer, ofrclose bank account
        #     # # for previous customer
        #     open_bank_process = self.env.process(self.open_bank_account(client))
        #     close_accounts = self.env.process(self.close_accounts(client))
        #     ## which one finishes first
        #     open_bank_process | close_accounts
        #
        #     # Below, is the time between customers or the 'flow' of customers
        #     yield self.env.timeout(time_between_clients)
        #     open_credit_card = self.env.process(self.open_credit_cart(client))
        #     ## either open a credit card OR this customer has churned
        #     open_credit_card | close_accounts
        #     ### ASSUMPTION ####
            ### This is assuming that the first thing a client will do is open a bank# account.

    def monitor_resource(self, resource, resource_name):
        """Print out monitoring statistics for a given resource.
        NUmber of slots allocated.
        Number of people using the resource
        Number of queued events for the resource"""
        print()
        print("MONITORING STATISTICS FOR {}".format(resource_name))
        print('{} of {} slots are allocated at time {}.'.format (
            resource.count, resource.capacity, self.env.now))
        #print('  Users :', resource.users)
        print('  Queued events:', resource.queue)
        print()

    def esp_open_money_market_bonus(self, client):
        """This is a simpy process for opening a money market bonus account"""

        open_mmb = self.esp_money_market_bonus_resource.request()
        # Wait until its our turn or until or the customer churns
        yield open_mmb

        ###### POSSIBLY YIELD TIME HERE BEFORE NEXT PROCESS?###

        print("Client {} is opened an esp money market bonus at time={}".format(
                                 client.client_id, self.env.now))
            ## keep track of the number of people with bank accounts
        self.monitor_resource(self.esp_money_market_bonus_resource,'money-market-bonus-esp')
        client.esp_open_money_market_bonus_request = open_mmb

    def esp_open_collateral_mma(self, client):
        """This is a simpy process for opening a open collateral mma account"""

        open_cmma = self.esp_collateral_mma_resource.request()
        # Wait until its our turn or until or the customer churns
        yield open_cmma

        ###### POSSIBLY YIELD TIME HERE BEFORE NEXT PROCESS?###

        print("Client {} is opened an esp open colalteral at time={}".format(
                                 client.client_id, self.env.now))
            ## keep track of the number of people with bank accounts
        self.monitor_resource(self.esp_collateral_mma_resource, 'collateral mma-esp')
        client.esp_open_collateral_mma = open_cmma

    def esp_open_cash_management(self, client):
        """This is a simpy process for opening a cash management checking account"""

        open_cmc = self.esp_cash_management_resource.request()
        # Wait until its our turn or until or the customer churns
        yield open_cmc

        ###### POSSIBLY YIELD TIME HERE BEFORE NEXT PROCESS?###

        print("Client {} is opened an esp checking vash management at time={}".format(
                                 client.client_id, self.env.now))
            ## keep track of the number of people with bank accounts
        self.monitor_resource(self.esp_cash_management_resource,'cash_managementesp')
        client.esp_open_cash_management_request = open_cmc

    def esp_open_fx(self, client):
        """This is a simpy process for opening a fx-account account"""

        open_fx = self.esp_fx_resource.request()
        # Wait until its our turn or until or the customer churns
        yield open_fx

        ###### POSSIBLY YIELD TIME HERE BEFORE NEXT PROCESS?###

        print("Client {} is opened an esp fx at time={}".format(
                                 client.client_id, self.env.now))
            ## keep track of the number of people with bank accounts
        self.monitor_resource(self.esp_fx_resource,'fx-esp')
        client.esp_open_fx_request = open_fx

    def esp_open_letters_of_credit(self, client):
        """This is a simpy process for opening a letters of credit"""

        open_letter_credit = self.esp_letters_of_credit_resource.request()
        # Wait until its our turn or until or the customer churns
        yield open_letter_credit

        ###### POSSIBLY YIELD TIME HERE BEFORE NEXT PROCESS?###

        print("Client {} is opened an esp letter of credit at time={}".format(
                                 client.client_id, self.env.now))
            ## keep track of the number of people with bank accounts
        self.monitor_resource(self.esp_letters_of_credit_resource,'letter credit-esp')
        client.esp_open_letters_of_credit_request = open_letter_credit

    def esp_open_enterprise_sweep(self, client):
        """This is a simpy process for opening a letters of credit"""

        open_es = self.esp_enterprise_sweep_resource.request()
        # Wait until its our turn or until or the customer churns
        yield open_es

        ###### POSSIBLY YIELD TIME HERE BEFORE NEXT PROCESS?###

        print("Client {} is opened an esp enterprise sweepat time={}".format(
                                 client.client_id, self.env.now))
            ## keep track of the number of people with bank accounts
        self.monitor_resource(self.esp_letters_of_credit_resource,'enterprise sweep-esp')
        client.esp_open_enterprise_sweep_request = open_es


    def esp_open_checking(self, client):
        """This is a simpy process for opening a letters of credit"""

        open_checking = self.esp_checking_resource.request()
        # Wait until its our turn or until or the customer churns
        yield open_checking

        ###### POSSIBLY YIELD TIME HERE BEFORE NEXT PROCESS?###

        print("Client {} is opened an esp checking at time={}".format(
                                 client.client_id, self.env.now))
            ## keep track of the number of people with bank accounts
        self.monitor_resource(self.esp_checking_resource,'checking esp')
        client.esp_open_checking_request = open_checking





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
            if client.time_credit_card_opened != None:
                self.credit_card_resource.release(client.credit_card_resource_request)
                self.time_series_client_with_cc.append(("time = ",
                    self.env.now, self.credit_card_resource.count))
                print("Client {} just closed their credit card".format(
                    client.client_id))
            else: # this client didn't have a credit card
                print('error closing credit card!!')

            client.time_bank_closed = self.env.now
            print(client.time_bank_closed , ' Bank was closed at this time !')

        else: # we already closed this account
            print('We ALREADY closed client {} bank account at time {}'.format(
                client.client_id, client.time_bank_closed
            ))



    def open_credit_cart(self,client):
        """Try to open a credit card for the client.
        A client needs to have a bank account before getting a credit card.
        A client can not open a credit card if they have churned."""

        if client.client_lifetime < self.env.now:
            print("Customer {} tried to open a CC but already churned".format(
                client.client_id
            ))
        else:
            ## wait some time between opening a bank and CC
            yield self.env.timeout(self.time_between_bank_account_credit_card)
            if client.client_lifetime < self.env.now:
                pass
            else:
                with self.credit_card_resource.request() as open_cc:
                    # Time between bank account and credit card

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
    esp_accel_stripe_flow = ESP_Accelerator_Stripe_flow(env)

    env.process(esp_accel_stripe_flow.initiate_week_client_run())
    env.run(until=100)
    print()
    print("SUMMARY STATISTICS")
    print('Finished at time {}'.format(env.now))


    print("Time series of esp money market bonus {} ".format(
        esp_accel_stripe_flow .time_series_esp_money_market_bonus))
    print("Time series of esp collateral mma {} ".format(
        esp_accel_stripe_flow .time_series_esp_collateral_mma))
    print("Time series of esp cash management {} ".format(
            esp_accel_stripe_flow .time_series_esp_cash_management))
    print("Time series of esp fx{} ".format(
                esp_accel_stripe_flow .time_series_esp_fx))
    print("Time series of esp letters of credit {} ".format(
                    esp_accel_stripe_flow .time_series_esp_letters_of_credit))
    print("Time series of esp enterprise sweep {} ".format(
                esp_accel_stripe_flow .time_series_esp_enterprise_sweep))
    print("Time series of esp checking {} ".format(
            esp_accel_stripe_flow .time_series_esp_checking))
