#! usr/bin/env python
import simpy
import pandas as pd
import pymc3
import scipy
import numpy as np

def meet_customer( meetings_per_week):
    """A random number of meetings with prospective customers per week.
    Returns a random number of meetings per week"""
    number_of_meetings = np.random.poisson(lam=meetings_per_week)
    return number_of_meetings

def prospect(number_of_clients, mean, std):
    """Takes the number of clients that were meet in the past week.
    And return the number that ultimately become prospects.
    This assumes the conversion rate is a normal distribution.
    This returns the number of prospects/clients for the week"""
    conversion_rate = np.random.normal(loc=mean,scale=std)
    if conversion_rate<0: ##  can't have negative
        conversion_rate = .0001
    total_prospects = number_of_clients*conversion_rate
    return round(total_prospects)

def customer(env,number_of_weekly_customers, avg_customer_lifetime_weeks):
    """This creates a simpy process for each customer where the lifetime
    of each customer is defined by an exponenetial distribution."""


    customer_lifetime = np.random.exponential(scale =
                                              avg_customer_lifetime_weeks)
    # start the process for each customer's lifetime
    print('The customer lifetime is {} weeks'.format(customer_lifetime))
    for i in range(number_of_weekly_customers): # one customer for the ones we
        #received this  week
        print("Customer{} is opening a bank account at time={}".format(i,env.now))
        c = open_bank_account(env, 'Customer%02d' % i,
                              cust_lifetime = avg_customer_lifetime_weeks)
        env.process(c)
        # how frequently do coustomers come in?
        time_between_customers = \
            round(np.random.exponential(1/number_of_weekly_customers),2)# weekly average
        print('The time between each customer is {} weeks'.format(
            time_between_customers))
        yield env.timeout(time_between_customers) # time in weeks between customers


def open_bank_account(env,customer_id,cust_lifetime):
    """This is a simpy process for creating a bank account"""
    global total_customer_with_bankaccount  # set to class var in future
    print(' {} opened a bank account'.format(customer_id))
    total_customer_with_bankaccount +=1
    print(' There are {} people with bank accounts at time-weeks {}'.format(
        total_customer_with_bankaccount, env.now
    ))
    yield env.timeout(cust_lifetime)




if __name__ == "__main__":

    average_number_of_meetings_per_week = 50
    average_weekly_conversion_meeting_client = .05
    std_weekly_conversion_meeting_client = .05
    total_customer_with_bankaccount = 0
    average_customer_lifetime_weeks = 100

    # defiing the meting - client generator for the week
    number_of_meetings = meet_customer(average_number_of_meetings_per_week)
    print(number_of_meetings, " NUmber of meetings this week")
    total_clientsorprospects = prospect(number_of_meetings,
                                        average_weekly_conversion_meeting_client,
                                        std_weekly_conversion_meeting_client)
    print("Total number of clients from the meetings {}".format(
        total_clientsorprospects
    ))

    env = simpy.Environment()
    env.process(customer(env, total_clientsorprospects, average_customer_lifetime_weeks))
    env.run(until=100) # one year
    print('Finished at time {}'.format(env.now))
