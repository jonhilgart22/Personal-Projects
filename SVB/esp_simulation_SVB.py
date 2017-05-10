#! usr/bin/env python
import simpy
import scipy.stats as stats
import pandas as pd
import numpy as np
import time
from esp_product_revenue import ESP_revenue_predictions
from ESP_Markov_Model_Client_Lifetime import ESP_Joint_Product_Probabilities, \
    ESP_Markov_Model_Joint_Prob
__author__='Jonathan Hilgart'





class Client(object):
    """This is the base class to represent client that enter the bank.
    The class will contain attributes such as lifetime, when their bank account
    was opened ...etc"""

    def __init__(self, client_id):
        """Initialize with the client ID and lifetime. As the time progresses,
        keep track of different events that occur."""
        self.client_id = client_id
        self.client_lifetime = None
        self.time_bank_closed = None
        self.time_credit_card_opened = None
        self.time_bank_was_opened = None
        # Store the resource requests for SImpy
        self.esp_open_money_market_bonus_request = None
        self.esp_open_collateral_mma_request  = None
        self.esp_open_cash_management_request = None
        self.esp_open_fx_request = None
        self.esp_open_letters_of_credit_request = None
        self.esp_open_enterprise_sweep_request = None
        self.esp_open_checking_request = None


        self.have_mmb = None
        self.have_cmma = None
        self.have_cm = None
        self.have_fx = None
        self.have_loc = None
        self.have_es = None
        self.have_checking = None

        self.client_age = None

        self.close_account_process = None







class ESP_Accelerator_Stripe_flow(object):
    """Model cclients in ESP opening up produts over time.
    Client lifetime drawn from distribution of client lifetimes from 2013-2016.
    The probability of ech product is inferred from a Markov Model, where the
    factors between the product nodes represent the joint probabilities. These
    join probabilities are updated are every week number to performance inference.

    The revenue per product is drawn from 2016 historical data (per month)
    The number of clients per week is drawn from 2016 data.

    Note, all time units are in terms of one week. One day would correspond
    to 1/7 of a week or .143."""
    def __init__(self, env,
                 time_to_open_bank_account=.05,
                 time_between_bank_account_credit_card=2,
                 number_of_weeks_to_run = 4,
                 esp_open_money_market_bonus_capacity=1000,
                 esp_open_collateral_mma_capacity =1000,
                 esp_open_cash_management_capacity = 1000, esp_fx_capacity = 1000,
                 esp_open_letters_of_credit_capacity = 1000,
                 esp_open_enterprise_sweep_capacity = 1000,esp_open_checking_capacity = 1000,
                 cc_capacity=200, esp_capacity = 5000,
                 stripe_capacity=3000):
        self.env = env
        self.list_of_all_clients = []

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

        self.time_series_esp_money_market_bonus_total_weekly_rev= []
        self.time_series_esp_collateral_mma_total_weekly_rev = []
        self.time_series_esp_cash_management_total_weekly_rev= []
        self.time_series_esp_fx_total_weekly_rev= []
        self.time_series_esp_letters_of_credit_total_weekly_rev = []
        self.time_series_esp_enterprise_sweep_total_weekly_rev= []
        self.time_series_esp_checking_total_weekly_rev = []

        self.time_series_esp_money_market_bonus_rev_per_customer = []
        self.time_series_esp_collateral_mma_rev_per_customer = []
        self.time_series_esp_cash_management_rev_per_customer = []
        self.time_series_esp_fx_rev_per_customer = []
        self.time_series_esp_letters_of_credit_rev_per_customer = []
        self.time_series_esp_enterprise_sweep_rev_per_customer = []
        self.time_series_esp_checking_rev_per_customer = []


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

    def esp_client_lifetime(self):
        """Draws from a distribution of client lifetimes (in months) from 2013-2016.
        Return the number of weeks that a client will be alive.

        Multiply the result by 4 to turn months into weeks"""
        exponential_lifetime_parameters = (0.99999999990617705, 4.3807421352102089)
        return round(stats.expon(*exponential_lifetime_parameters ).rvs())*4

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
            print("Starting WEEK NUMBER {}".format(week_n))
            ## generate new clients for each channel
            self.esp_clients_per_week(esp_mean,esp_std)
            self.accelerator_clients_per_week(accel_mean, accel_std)
            self.stripe_clients_per_week(stripe_mean, stripe_std)
            print(self.oneweek_esp_clients, ' ESP clients this week')
            # print(self.oneweek_accelerator_clients, "acceleartor clinets this week")
            # print(self.oneweek_stripe_clients, ' stripe clients this week')


            ## See where the ESP clients end up across the products
            for esp_client_n in range(int(self.oneweek_esp_clients)):

                # Client id is number for the week + week number
                esp_client = Client(str(esp_client_n)+'-'+str(week_n))
                 # default client lifetime
                esp_client.client_age = 0 # new client

                # Draw a lifetime value from an exponential distribution
                esp_client.client_lifetime = self.esp_client_lifetime()

                # make a list of all esp clients
                self.list_of_all_clients.append(esp_client)

            for idx,client in enumerate(self.list_of_all_clients):
                #client = client[0] # tuple of client , client client id

                # print client lifetime (see when clients are closing accounts)
                if client.client_lifetime < 10:
                    print('Client {} lifetime = {}'.format(client.client_id,
                                                           client.client_lifetime))



                # Yield for the client lifetime
                # only span one close account process per client
                # Otherwise, SImpy will try to close the same account
                # Multiple times
                if client.close_account_process == None:
                    close_accounts = self.env.process(self.close_accounts(client))
                    client.close_account_process = close_accounts

                if client.client_age == 0: ## Don't have any products yet
                    checking_prob, cmma_prob, mmb_prob, cm_prob, fx_prob ,loc_prob, es_prob = \
                    ESP_Markov_Model_Joint_Prob(ESP_Joint_Product_Probabilities,
                            single=True,week_n_one_time=client.client_age)

                    ## See if a client has each product
                    client.have_checking = np.random.choice([1,0],p=np.array(
                        [checking_prob,(1-checking_prob)]))
                    client.have_cmma = np.random.choice([1,0],p=np.array(
                        [cmma_prob,(1-cmma_prob)]))
                    client.have_mmb = np.random.choice([1,0],p=np.array(
                        [mmb_prob,(1-mmb_prob)]))
                    client.have_cm = np.random.choice([1,0],p=np.array(
                        [cm_prob,(1-cm_prob)]))
                    client.have_fx = np.random.choice([1,0],p=np.array(
                        [fx_prob,(1-fx_prob)]))
                    client.have_loc = np.random.choice([1,0],p=np.array(
                        [loc_prob,(1-loc_prob)]))
                    client.have_es = np.random.choice([1,0],p=np.array(
                        [es_prob,(1-es_prob)]))

                    # open an account if a client has each product if not
                    # have a default event to yield to

                    if client.have_checking == 1:
                        open_checking = self.env.process(self.esp_open_checking(esp_client))
                        # either open product or
                    else:
                        open_checking = self.env.timeout(0)
                    if client.have_cmma == 1:
                        open_cmma = self.env.process(
                            self.esp_open_collateral_mma(esp_client))
                        # yield close_accounts |open_cmma
                    else:
                        open_cmma = self.env.timeout(0)
                    if client.have_mmb ==1:
                        open_mmb = self.env.process(
                            self.esp_open_money_market_bonus(esp_client))
                        # yield close_accounts | open_mmb
                    else:
                        open_mmb = self.env.timeout(0)
                    if client.have_cm == 1:
                        open_cm = self.env.process(
                            self.esp_open_cash_management(esp_client))
                        # yield close_accounts | open_cm
                    else:
                        open_cm = self.env.timeout(0)
                    if client.have_fx == 1:
                        open_fx = self.env.process(self.esp_open_fx(esp_client))
                        # yield close_accounts |open_fx
                    else:
                        open_fx = self.env.timeout(0)
                    if client.have_loc == 1:
                        open_loc = self.env.process(
                            self.esp_open_letters_of_credit(esp_client))
                        # yield close_accounts | open_loc
                    else:
                        open_loc = self.env.timeout(0)
                    if client.have_es == 1:
                        open_es = self.env.process(
                            self.esp_open_enterprise_sweep(esp_client))
                        # yield close_accounts | open_es
                    else:
                        open_es = self.env.timeout(0)
                    # either open product or close account
                    # only yield closing accoutns ONCE (otherwise, Simpy
                    # will try to close the same client multiple times
                    yield (open_checking &open_cmma & open_mmb & open_cm \
                           &open_fx & open_loc & open_es) | client.close_account_process

                    client.client_age +=1  # increment the age of the client

                else:
                    # every client now has an indicator for if they have
                    # a product or not
                    if idx % 5 ==0 :
                        ## print out stats of every 10th client
                        print(client.client_id, ' client id')
                        print(client.client_age,'client age')
                        print(client.have_mmb, ' client.have_mmb')
                        print(client.have_cmma, 'client.have_cmma')
                        print(client.have_cm, 'client.have_cm')
                        print( client.have_es, ' client.have_es')
                        print(client.have_fx,'client.have_fx')
                        print(client.have_loc,'client.have_loc')
                        print(client.have_checking,'client.have_checking')
                    checking_prob, cmma_prob, mmb_prob, cm_prob, fx_prob ,loc_prob, es_prob = \
                    ESP_Markov_Model_Joint_Prob(ESP_Joint_Product_Probabilities,
                            single=True,week_n_one_time=client.client_age,
                            evidence_={'money_market_bonus':client.have_mmb,
                                       'collateral_mma':client.have_cmma,
                                'cash_management':client.have_cm,
                                'enterprise_sweep':client.have_es,
                                'fx_products':client.have_fx,
                                'letters_of_credit':client.have_loc,
                                'checking_usd':client.have_checking})
                    # update if these clients have each product
                    client.have_checking = np.random.choice([1,0],p=np.array(
                        [checking_prob,(1-checking_prob)]))
                    client.have_cmma = np.random.choice([1,0],p=np.array(
                        [cmma_prob,(1-cmma_prob)]))
                    client.have_mmb = np.random.choice([1,0],p=np.array(
                        [mmb_prob,(1-mmb_prob)]))
                    client.have_cm = np.random.choice([1,0],p=np.array(
                        [cm_prob,(1-cm_prob)]))
                    client.have_fx = np.random.choice([1,0],p=np.array(
                        [fx_prob,(1-fx_prob)]))
                    client.have_loc = np.random.choice([1,0],p=np.array(
                        [loc_prob,(1-loc_prob)]))
                    client.have_es = np.random.choice([1,0],p=np.array(
                        [es_prob,(1-es_prob)]))


                    ## See if a client has each product
                    client.have_checking = np.random.choice([1,0],p=np.array(
                        [checking_prob,(1-checking_prob)]))
                    client.have_cmma = np.random.choice([1,0],p=np.array(
                        [cmma_prob,(1-cmma_prob)]))
                    client.have_mmb = np.random.choice([1,0],p=np.array(
                        [mmb_prob,(1-mmb_prob)]))
                    client.have_cm = np.random.choice([1,0],p=np.array(
                        [cm_prob,(1-cm_prob)]))
                    client.have_fx = np.random.choice([1,0],p=np.array(
                        [fx_prob,(1-fx_prob)]))
                    client.have_loc = np.random.choice([1,0],p=np.array(
                        [loc_prob,(1-loc_prob)]))
                    client.have_es = np.random.choice([1,0],p=np.array(
                        [es_prob,(1-es_prob)]))

                    # open an account if a client has each product
                    # Otherwise, add a default event to yield
                    if client.have_checking == 1:
                        open_checking = self.env.process(self.esp_open_checking(esp_client))
                        # either open product or
                    else:
                        open_checking = self.env.timeout(0)
                    if client.have_cmma == 1:
                        open_cmma = self.env.process(
                            self.esp_open_collateral_mma(esp_client))
                        # yield close_accounts |open_cmma
                    else:
                        open_cmma = self.env.timeout(0)
                    if client.have_mmb ==1:
                        open_mmb = self.env.process(
                            self.esp_open_money_market_bonus(esp_client))
                        # yield close_accounts | open_mmb
                    else:
                        open_mmb = self.env.timeout(0)
                    if client.have_cm == 1:
                        open_cm = self.env.process(
                            self.esp_open_cash_management(esp_client))
                        # yield close_accounts | open_cm
                    else:
                        open_cm = self.env.timeout(0)
                    if client.have_fx == 1:
                        open_fx = self.env.process(self.esp_open_fx(esp_client))
                        # yield close_accounts |open_fx
                    else:
                        open_fx = self.env.timeout(0)
                    if client.have_loc == 1:
                        open_loc = self.env.process(
                            self.esp_open_letters_of_credit(esp_client))
                        # yield close_accounts | open_loc
                    else:
                        open_loc = self.env.timeout(0)
                    if client.have_es == 1:
                        open_es = self.env.process(
                            self.esp_open_enterprise_sweep(esp_client))
                        # yield close_accounts | open_es
                    else:
                        open_es = self.env.timeout(0)
                    # either open product or close the account
                    yield (open_checking &open_cmma & open_mmb & open_cm \
                           &open_fx & open_loc & open_es) | client.close_account_process

                    client.client_age +=1 ## increment the age of the client

            ## go through clients to see if they have churned

            ## add in the number of clients for each week
            print()
            print('WEEK METRICS {}'.format(week_n))
            print(self.esp_money_market_bonus_resource.count,'esp mmb clients ')
            print(self.esp_collateral_mma_resource.count, ' esp mma clients')
            print(self.esp_cash_management_resource.count, ' esp cm clients')
            print(self.esp_fx_resource.count, 'fx count')
            print(self.esp_letters_of_credit_resource.count, ' loc count')
            print(self.esp_enterprise_sweep_resource.count, 'es count')
            print(self.esp_checking_resource.count , 'checking count')
            print()
            # Increment by one week
            one_week_increment = self.env.timeout(1)
            yield one_week_increment
            print(self.env.now, 'time now ENV')

        # At the end of each week, find the weekly GP and weekly GP per client
        self.time_series_esp_money_market_bonus.append(("Week = ",
            self.env.now,self.esp_money_market_bonus_resource.count))

        self.time_series_esp_collateral_mma.append(("Week = ",
            self.env.now,self.esp_collateral_mma_resource.count))
        self.time_series_esp_cash_management.append(("Week = ",
            self.env.now,self.esp_cash_management_resource.count))
        self.time_series_esp_fx.append(("Week = ",
            self.env.now,self.esp_fx_resource.count))
        self.time_series_esp_letters_of_credit.append(("Week = ",
            self.env.now,self.esp_letters_of_credit_resource.count))
        self.time_series_esp_enterprise_sweep.append(("Week = ",
            self.env.now,self.esp_enterprise_sweep_resource.count))
        self.time_series_esp_checking.append(("Week = ",
            self.env.now,self.esp_checking_resource.count))

        ### esp money market bonus weekly gp
        self.get_weekly_gp(week_n, self.time_series_esp_money_market_bonus,
            ESP_revenue_predictions.money_market_bonus_weekly_rev(),
            self.time_series_esp_money_market_bonus_total_weekly_rev,
            self.time_series_esp_money_market_bonus_rev_per_customer)
        ### esp collateral mma weekly gp
        self.get_weekly_gp(week_n, self.time_series_esp_collateral_mma,
            ESP_revenue_predictions.collateral_mma_weekly_rev(),
            self.time_series_esp_collateral_mma_total_weekly_rev,
            self.time_series_esp_collateral_mma_rev_per_customer)
        ### esp cash management weekly revenue
        self.get_weekly_gp(week_n, self.time_series_esp_cash_management,
            ESP_revenue_predictions.cash_management_weekly_rev(),
            self.time_series_esp_cash_management_total_weekly_rev,
            self.time_series_esp_cash_management_rev_per_customer)
        ### esp fx weekly gp
        self.get_weekly_gp(week_n, self.time_series_esp_fx,
            ESP_revenue_predictions.fx_weekly_rev(),
            self.time_series_esp_fx_total_weekly_rev,
            self.time_series_esp_fx_rev_per_customer)
        ### esp letters of credit
        self.get_weekly_gp(week_n, self.time_series_esp_letters_of_credit,
            ESP_revenue_predictions.letters_of_credit_weekly_rev(),
            self.time_series_esp_letters_of_credit_total_weekly_rev,
            self.time_series_esp_letters_of_credit_rev_per_customer)
        ### esp enterprise sweep weekly gp
        self.get_weekly_gp(week_n, self.time_series_esp_enterprise_sweep,
            ESP_revenue_predictions.enterprise_sweep_weekly_rev(),
            self.time_series_esp_enterprise_sweep_total_weekly_rev,
            self.time_series_esp_enterprise_sweep_rev_per_customer)
        ### esp checking weekly gp
        self.get_weekly_gp(week_n, self.time_series_esp_checking,
            ESP_revenue_predictions.checking_weekly_rev(),
            self.time_series_esp_checking_total_weekly_rev,
            self.time_series_esp_checking_rev_per_customer)




            ## need to generate wait times to open each product

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

    def get_weekly_gp(self,week_n, time_series, gp_data_function, total_rev_week,
                      rev_per_client_week):
        """Get the total revenue for the week, and revenue per client, for a
        given product"""
        total_weekly_rev= 0
        #print(time_series, ' time series')
        if time_series[week_n][2] ==0:
            total_rev_week.append( ('week = ',week_n, 0))
            rev_per_client_week.append( ('week = ',week_n,0))

        else:
            for esp_customer in range(time_series[week_n][2]):
                total_weekly_rev += gp_data_function
                # total value of the product
                total_rev_week.append( ('week = ',week_n, total_weekly_rev))
                # average value per customer
                rev_per_client_week.append( ('week = ',week_n,total_weekly_rev  / \
                     time_series[week_n][2]))

    def esp_open_money_market_bonus(self, client):
        """This is a simpy process for opening a money market bonus account.
        Also, append the resource request for simpy to the client object.
        This will let us release this resource request later"""

        # insert numpy random choice here for probability of a customer
        # opening a money market bonus account

        open_mmb = self.esp_money_market_bonus_resource.request()
        # Wait until its our turn or until or the customer churns
        yield open_mmb

        ###### POSSIBLY YIELD TIME HERE BEFORE NEXT PROCESS?###

        #print("Client {} is opened an esp money market bonus at time={}".format(
        #                         client.client_id, self.env.now))
            ## keep track of the number of people with bank accounts
        #self.monitor_resource(self.esp_money_market_bonus_resource,'money-market-bonus-esp')
        client.esp_open_money_market_bonus_request = open_mmb

    def esp_open_collateral_mma(self, client):
        """This is a simpy process for opening a open collateral mma accounts
        Also, append the resource request for simpy to the client object.
        This will let us release this resource request later"""

        open_cmma = self.esp_collateral_mma_resource.request()
        # Wait until its our turn or until or the customer churns
        yield open_cmma

        ###### POSSIBLY YIELD TIME HERE BEFORE NEXT PROCESS?###

        #print("Client {} is opened an esp open colalteral at time={}".format(
        #                         client.client_id, self.env.now))
            ## keep track of the number of people with bank accounts
        #self.monitor_resource(self.esp_collateral_mma_resource, 'collateral mma-esp')
        client.esp_open_collateral_mma = open_cmma

    def esp_open_cash_management(self, client):
        """This is a simpy process for opening a cash management checking account
        Also, append the resource request for simpy to the client object.
        This will let us release this resource request later"""

        open_cmc = self.esp_cash_management_resource.request()
        # Wait until its our turn or until or the customer churns
        yield open_cmc

        ###### POSSIBLY YIELD TIME HERE BEFORE NEXT PROCESS?###

        #print("Client {} is opened an esp checking vash management at time={}".format(
        #                         client.client_id, self.env.now))
            ## keep track of the number of people with bank accounts
        #self.monitor_resource(self.esp_cash_management_resource,'cash_managementesp')
        client.esp_open_cash_management_request = open_cmc

    def esp_open_fx(self, client):
        """This is a simpy process for opening a fx-account account
        Also, append the resource request for simpy to the client object.
        This will let us release this resource request later"""

        open_fx = self.esp_fx_resource.request()
        # Wait until its our turn or until or the customer churns
        yield open_fx

        ###### POSSIBLY YIELD TIME HERE BEFORE NEXT PROCESS?###

        #print("Client {} is opened an esp fx at time={}".format(
        #                         client.client_id, self.env.now))
            ## keep track of the number of people with bank accounts
        #self.monitor_resource(self.esp_fx_resource,'fx-esp')
        client.esp_open_fx_request = open_fx

    def esp_open_letters_of_credit(self, client):
        """This is a simpy process for opening a letters of credit
        Also, append the resource request for simpy to the client object.
        This will let us release this resource request later"""

        open_letter_credit = self.esp_letters_of_credit_resource.request()
        # Wait until its our turn or until or the customer churns
        yield open_letter_credit

        ###### POSSIBLY YIELD TIME HERE BEFORE NEXT PROCESS?###

        #print("Client {} is opened an esp letter of credit at time={}".format(
        #                         client.client_id, self.env.now))
            ## keep track of the number of people with bank accounts
        #self.monitor_resource(self.esp_letters_of_credit_resource,'letter credit-esp')
        client.esp_open_letters_of_credit_request = open_letter_credit

    def esp_open_enterprise_sweep(self, client):
        """This is a simpy process for opening a letters of credit
        Also, append the resource request for simpy to the client object.
        This will let us release this resource request later"""

        open_es = self.esp_enterprise_sweep_resource.request()
        # Wait until its our turn or until or the customer churns
        yield open_es

        ###### POSSIBLY YIELD TIME HERE BEFORE NEXT PROCESS?###

        #print("Client {} is opened an esp enterprise sweepat time={}".format(
        #                         client.client_id, self.env.now))
            ## keep track of the number of people with bank accounts
        #self.monitor_resource(self.esp_letters_of_credit_resource,'enterprise sweep-esp')
        client.esp_open_enterprise_sweep_request = open_es


    def esp_open_checking(self, client):
        """This is a simpy process for opening a letters of credit
        Also, append the resource request for simpy to the client object.
        This will let us release this resource request later"""

        open_checking = self.esp_checking_resource.request()
        # Wait until its our turn or until or the customer churns
        yield open_checking

        ###### POSSIBLY YIELD TIME HERE BEFORE NEXT PROCESS?###

        #print("Client {} is opened an esp checking at time={}".format(
        #                         client.client_id, self.env.now))
            ## keep track of the number of people with bank accounts
        #self.monitor_resource(self.esp_checking_resource, 'checking esp')
        client.esp_open_checking_request = open_checking


    def close_accounts(self, client):
        """Release the simpy process for each of the Simpy Products.
        This occurs once a client has churned.
        In addition, remove this client from the list of clients that we have"""
        yield self.env.timeout(client.client_lifetime)
        print()
        print('WE are closing accoutns for client {}'.format(client.client_id))
        print(len(self.list_of_all_clients),' length of client list before')
        # try:
        self.list_of_all_clients.remove(client)
        # except Exception as e:
        #     print(e)
        #     print(self.list_of_all_clients)
        print(len(self.list_of_all_clients),'len list of all cleitns')
        # Drop the clients from each product once they churn
        self.esp_cash_management_resource.release(client.esp_open_cash_management_request)
        self.esp_checking_resource.release(client.esp_open_checking_request)
        self.esp_collateral_mma_resource.release(client.esp_open_collateral_mma_request)
        self.esp_enterprise_sweep_resource.release(client.esp_open_enterprise_sweep_request)
        self.esp_letters_of_credit_resource.release(client.esp_open_letters_of_credit_request)
        self.esp_money_market_bonus_resource.release(client.esp_open_money_market_bonus_request)
        self.esp_fx_resource.release(client.esp_open_fx_request)


    # def close_accounts(self, client):
    #     """If a client's lifetime is reached, their bank account is closed.
    #     This assumes that the client is dead and can no longer open up additional
    #     products"""
    #
    #     if client.time_bank_closed == None: # see if we already closed this account
    #         yield self.env.timeout(client.client_lifetime)
    #         print("WE CLOSED AN ACCOUNT for client {}".format(client.client_id))
    #         # release the bank account resource
    #         self.bank_account_resource.release(
    #             client.bank_account_resource_request)
    #
    #         # track the number of clients over time
    #         self.time_series_client_with_bankaccount.append(("Time =",
    #             self.env.now,self.bank_account_resource.count))
    #             # try to release the credit card resource (if a client has a CC)
    #         if client.time_credit_card_opened != None:
    #             self.credit_card_resource.release(client.credit_card_resource_request)
    #             self.time_series_client_with_cc.append(("time = ",
    #                 self.env.now, self.credit_card_resource.count))
    #             print("Client {} just closed their credit card".format(
    #                 client.client_id))
    #         else: # this client didn't have a credit card
    #             print('error closing credit card!!')
    #
    #         client.time_bank_closed = self.env.now
    #         print(client.time_bank_closed , ' Bank was closed at this time !')
    #
    #     else: # we already closed this account
    #         print('We ALREADY closed client {} bank account at time {}'.format(
    #             client.client_id, client.time_bank_closed
    #         ))



    # def open_credit_cart(self,client):
    #     """Try to open a credit card for the client.
    #     A client needs to have a bank account before getting a credit card.
    #     A client can not open a credit card if they have churned."""
    #
    #     if client.client_lifetime < self.env.now:
    #         print("Customer {} tried to open a CC but already churned".format(
    #             client.client_id
    #         ))
    #     else:
    #         ## wait some time between opening a bank and CC
    #         yield self.env.timeout(self.time_between_bank_account_credit_card)
    #         if client.client_lifetime < self.env.now:
    #             pass
    #         else:
    #             with self.credit_card_resource.request() as open_cc:
    #                 # Time between bank account and credit card
    #
    #                 # CC requet
    #                 cc_request = self.credit_card_resource.request()
    #                 yield cc_request # request was successful
    #
    #                 print()
    #                 print("Client {} is opening a credit card at time={}".format(
    #                                          client.client_id, self.env.now))
    #
    #                     ## wait some time until the next client can open a bank account
    #                 print('Time to wait between bank account and credit card is {}, \
    #                       client {} will open a CC at time {}'.format(
    #                       self.time_between_bank_account_credit_card,
    #                       client.client_id, self.env.now+self.time_between_bank_account_credit_card))
    #
    #                     ## keep track of the number of people with credit cards
    #                 self.monitor_resource(self.credit_card_resource, 'credit_card')
    #
    #                 self.time_series_client_with_cc.append(("Time = {}",
    #                     self.env.now,self.credit_card_resource.count))
    #                 client.time_credit_card_opened= self.env.now
    #                 # Store the CC request
    #                 client.credit_card_resource_request = cc_request



if __name__ == "__main__":
    env = simpy.Environment()
    start = time.time()
    n_weeks_run = 5
    esp_accel_stripe_flow = ESP_Accelerator_Stripe_flow(env,
                                number_of_weeks_to_run = n_weeks_run)

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
    print("Total rgp for esp money market bonus per week {}".format(
    esp_accel_stripe_flow .time_series_esp_money_market_bonus_total_weekly_rev))
    print("GP per custome rfor esp money market bonus per week {}".format(
        esp_accel_stripe_flow.time_series_esp_money_market_bonus_rev_per_customer
    ))
    print("GP per total {} and per customer for collateral MMA  {}".format(
            esp_accel_stripe_flow.time_series_esp_collateral_mma_total_weekly_rev,
            esp_accel_stripe_flow.time_series_esp_collateral_mma_rev_per_customer
    ))
    print('GP for cash management total {} and gp cash management per customer {}'.format(
        esp_accel_stripe_flow.time_series_esp_cash_management_total_weekly_rev,
        esp_accel_stripe_flow.time_series_esp_cash_management_rev_per_customer
    ))
    print(' GP for fx total {} and fx per client {}'.format(
        esp_accel_stripe_flow.time_series_esp_fx_total_weekly_rev,
        esp_accel_stripe_flow.time_series_esp_fx_rev_per_customer))
    print('GP fox letters of credit toal {} and gp for letters of credit per customer {}'.format(
    esp_accel_stripe_flow.time_series_esp_letters_of_credit_total_weekly_rev,
                esp_accel_stripe_flow.time_series_esp_letters_of_credit_rev_per_customer
    ))
    print('GP for enterprise sweep total {} and enterprise sweep gP per client{}'.format(
            esp_accel_stripe_flow.time_series_esp_enterprise_sweep_total_weekly_rev,
            esp_accel_stripe_flow.time_series_esp_enterprise_sweep_rev_per_customer
    ))
    print('GP for checking total {} and checking per client per week {} '.format(
            esp_accel_stripe_flow.time_series_esp_checking_total_weekly_rev,
            esp_accel_stripe_flow.time_series_esp_checking_rev_per_customer
    ))
    end = time.time()
    print('{} weeks tooks {}'.format(n_weeks_run,end-start))
