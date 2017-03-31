#! usr/bin/env python
import simpy
import pandas as pd
import pymc3
import scipy
import numpy as np
#
#
# class Customer(Object):
#     """A base class to remember attributes of each customer like lifetime
#     products used ...etc"""
#     def __init__(self,lifetime,customer_id):
#         self.lifetime = lifetime
#         self.id = customer_id

class Bank_Account_Flow(object):
    """Model customers opening and closing a bank account over time."""
    def __init__(self, env, average_number_of_meetings_per_week=100,
                 average_weekly_conversion_meeting_client=.05,
                 std_weekly_conversion_meeting_client=.05,
                 average_customer_lifetime_weeks=10,
                 time_to_open_bank_account=.14):
        self.average_number_of_meetings_per_week = \
            average_number_of_meetings_per_week
        self.average_weekly_conversion_meeting_client = \
            average_weekly_conversion_meeting_client
        self.std_weekly_conversion_meeting_client = \
            std_weekly_conversion_meeting_client
        self.average_customer_lifetime_weeks = \
            average_customer_lifetime_weeks
        self.time_to_open_bank_account = \
            time_to_open_bank_account
        self.total_customer_with_bankaccount = 0

        self.env = env
        self.meet_customer()
        self.client()
        self.customer_lifetimes = []

    def meet_customer(self):
        """A random number of meetings with prospective customers per week.
        Returns a random number of meetings per week"""
        number_of_meetings = np.random.poisson(
            lam=self.average_number_of_meetings_per_week)
        self.number_of_meetings = number_of_meetings

    def client(self):
        """Takes the number of clients that were meet in the past week.
        And return the number that ultimately become prospects.
        This assumes the conversion rate is a normal distribution.
        This returns the number of prospects/clients for the week"""
        conversion_rate = np.random.normal(loc=
                self.average_weekly_conversion_meeting_client ,
                scale=self.std_weekly_conversion_meeting_client)
        if conversion_rate<0: ##  can't have negative
            conversion_rate = .0001
        self.conversion_rate = conversion_rate
        total_clients = self.number_of_meetings*conversion_rate
        self.total_clients = round(total_clients) # for the week
        self.time_between_clients = self.total_clients / 7

    def customer(self):
        """This creates a simpy process for each customer where the lifetime
        of each customer is defined by an exponenetial distribution."""
        for customer_id in range(self.total_clients ):
            # number of customer for this week
            customer_lifetime = np.random.exponential(scale =
                                        self.average_customer_lifetime_weeks)
            self.customer_lifetimes.append(customer_lifetime)
            # start the process for each customer's lifetime
            print('The customer lifetime for customer {} is {} weeks'.format(
                customer_id ,customer_lifetime))

            #received this  week
            print("Customer{} is opening a bank account at time={}".format(
                customer_id, self.env.now))

            self.env.process(self.open_bank_account('Customer%02d' % customer_id,
                                       customer_lifetime))

            # how frequently do coustomers come in?
            time_between_customers = \
                round(np.random.exponential(1/self.time_between_clients),2)# weekly average for the number of customers
            print('The time between each customer is {} weeks'.format(
                time_between_customers))
            yield self.env.timeout(time_between_customers) # time in weeks between customers

    def open_bank_account(self, customer_id, cust_lifetime=52):
        """This is a simpy process for creating a bank account"""

        #print(' {} opened a bank account'.format(customer_id))
        self.total_customer_with_bankaccount +=1
        print(' There are {} people with bank accounts at time-weeks {}'.format(
            self.total_customer_with_bankaccount, round(self.env.now,2)))
        response = yield self.env.timeout(self.time_to_open_bank_account, value='open') | \
            self.env.process(self.close_bank_account(customer_id, cust_lifetime))
        # if "open" in response:
        #     print(' {} successful completed opening a bank account'.format(customer_id))
        # else:
        #     print('CLOSED ACCOUNT', response)
        ## it takes one day to open a bank account


    def close_bank_account(self, customer_id, customer_lifetime):
        """If a customer's lifetime is reached, their bank account is closed"""
        yield self.env.timeout(customer_lifetime)
        print("WE CLOSED AN ACCOUNT")
        #print('Customer lifetime id= {} at {}'.format(customer_id, self.env.now))
        self.total_customer_with_bankaccount -= 1
        print('Total people with bank accounts= {} at time= {}'.format(
            self.total_customer_with_bankaccount, self.env.now))
        #(yield env.timeout(cust_lifetime) | (yield env.now)
        pass




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
    env.process(bank_account_flow.customer())
    env.run(until=120) # one year
    print('Finished at time {}'.format(env.now))
    print("Number of clients for this week {}".format(
        bank_account_flow.total_clients))
    print("Number of meetings for the week {}".format (
        bank_account_flow.number_of_meetings
    ))
    print("The conversion rate is {}".format(bank_account_flow.conversion_rate))
    print("Customer lifetimes = {}".format(bank_account_flow.customer_lifetimes))
