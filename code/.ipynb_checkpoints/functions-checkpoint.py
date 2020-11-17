# python standard library packages:
import datetime
import time

# import more packages:
import pandas as pd
import numpy  as np
import matplotlib.pyplot as plt


def ev_create_resampled_data(my_periods_start, 
                             my_periods_stop, 
                             my_df_trip, 
                             my_df_charge
                            ):
    
    # start timer:
    t0 = time.time()
    
    # initialize data frame:
    my_periods = pd.date_range(start=my_periods_start, 
                               end=my_periods_stop,
                               freq='15min')
    my_df_resampled = pd.DataFrame(data=None, 
                                   index=my_periods, 
                                   columns=['driving (boolean)', 
                                            'power (kW)', 
                                            'charging (boolean)'])
    # default entries:
    my_df_resampled['power (kW)'] = 0
    my_df_resampled['driving (boolean)'] = False
    my_df_resampled['charging (boolean)'] = False
    
    # slice trip data to selected time window:
    my_trip_ind = (my_periods_start <= my_df_trip['TripStartDateTime']) & \
                  (my_df_trip['TripStopDateTime'] <= my_periods_stop)
    my_df_trip = my_df_trip.loc[my_trip_ind,]
    
    # fill in non-zero trip data:
    for trip_ind in my_df_trip.index:
        my_trip = my_df_trip.loc[trip_ind,]
        my_period_start = my_trip['TripStartDateTime'].round(freq='15min')
        my_period_stop  = my_trip['TripStopDateTime' ].round(freq='15min')
        my_df_resampled.loc[my_period_start:my_period_stop, 
                            'driving (boolean)'] = True
        my_duration = (my_period_stop - my_period_start + pd.to_timedelta('15min'))/pd.Timedelta('1 hour')
        my_df_resampled.loc[my_period_start:my_period_stop, 
                            'power (kW)'] += my_trip['Power Consumption (kWh)']/my_duration

    # slice charge data to selected time window:
    my_charge_ind = (my_periods_start <= my_df_charge['BatteryChargeStartDate']) & \
                    (my_df_charge['BatteryChargeStopDate'] <= my_periods_stop)
    my_df_charge = my_df_charge.loc[my_charge_ind,]
        
    # fill in non-zero charge data:
    for charge_ind in my_df_charge.index:
        my_charge = my_df_charge.loc[charge_ind,]
        my_period_start = my_charge['BatteryChargeStartDate'].round(freq='15min')
        my_period_stop  = my_charge['BatteryChargeStopDate' ].round(freq='15min')
        my_df_resampled.loc[my_period_start:my_period_stop, 
                            'charging (boolean)'] = True
        
    # correct concurrent driving and charging to not charging:
    my_ind = (my_df_resampled['driving (boolean)'] == True) & \
             (my_df_resampled['charging (boolean)'] == True)
    print(f"  found {sum(my_ind.astype(int))} concurrent driving and charging periods.")
    my_df_resampled.loc[my_ind,'charging (boolean)'] = False
    
    # set loadability:
    # initialize charging => loadable:
    my_df_resampled['loadable (boolean)'] = my_df_resampled['charging (boolean)']

    # expand loadability at night as long as one is not driving:
    my_night_start = datetime.time(0, 0)
    my_night_end   = datetime.time(6, 0)

    my_ind = (my_df_resampled['driving (boolean)'] == False) & \
             (my_night_start <= my_df_resampled.index.time) & \
             (my_df_resampled.index.time <= my_night_end)
    my_df_resampled.loc[my_ind,'loadable (boolean)'] = True

    # expand loadability as long as one is not driving:
    my_df_resampled.sort_index(ascending=False, inplace=True)
    loadable_last = False
    for period in my_df_resampled.index:
        driving  = my_df_resampled.loc[period,'driving (boolean)']
        loadable = my_df_resampled.loc[period,'loadable (boolean)']
        if loadable:
            loadable_last = True
        elif loadable_last and not driving:
            loadable_last = True
            my_df_resampled.loc[period,'loadable (boolean)'] = loadable_last
        else:
            loadable_last = False
    my_df_resampled.sort_index(ascending=True, inplace=True)
    for period in my_df_resampled.index:
        driving  = my_df_resampled.loc[period,'driving (boolean)']
        loadable = my_df_resampled.loc[period,'loadable (boolean)']
        if loadable:
            loadable_last = True
        elif loadable_last and not driving:
            loadable_last = True
            my_df_resampled.loc[period,'loadable (boolean)'] = loadable_last
        else:
            loadable_last = False

    # rename columns:
    my_columns={"driving (boolean)" : "driving_bool", 
                "power (kW)"        : "power_kW",
                "charging (boolean)": "charging_bool",
                "loadable (boolean)": "loadable_bool"}
    my_df_resampled.rename(columns=my_columns, inplace=True)
            
    # stop timer and print duration of computations:
    t1 = time.time()
    print(f"  time used = {t1 - t0:.2f} seconds = {(t1 - t0)/60:.2f} minutes.")

    return my_df_resampled


def hh_create_timestamp(my_dtc):
    my_date_offset = pd.Timestamp("2009-01-01 00:00:00")
    my_add_days = int(my_dtc[:3]) - 1
    my_add_half_hours = int(my_dtc[3:]) - 1
    my_timestamp = my_date_offset + \
                   pd.Timedelta(my_add_days, unit='days') + \
                   pd.Timedelta(my_add_half_hours/2, unit="hours")
    return my_timestamp


def checks(my_df, my_year='2016', verbose=True):
    
    # check for rows with a NaN value:
    my_df_nan = my_df[my_df.isna().any(axis=1)]
    if my_df_nan.shape[0]:
        print(f"WARNING: Found {my_df_nan.shape[0]} my_df_nan.shape[0]:")
        print(my_df_nan)
    else:
        if verbose:
            print("- check for rows with a NaN value: OK")
        
    # check for duplicate timestamps:
    my_ind = my_df.index.duplicated()
    if my_ind.any():
        print(f"WARNING: Found {my_ind.astype(int).sum()} duplicate timestamps:")
        print(my_df.loc[my_ind,])
    else:
        if verbose:
            print("- check for duplicate timestamps : OK")
        
    # check if all timestamps of the year are given:
    if my_year == '2016':
        my_date_range = pd.date_range(start='2016-01-01 00:00:00', 
                                      end  ='2016-12-31 23:45:00',
                                      freq='15min')
        if my_df.index.equals(my_date_range):
            if verbose:
                print("- check for set of timestamps    : OK")
        else:
            print(f"WARNING: Not all timestamps of the year are given correctly!")
    elif not my_year:
        if verbose:
            print("INFO: no check for set of timestamps performed.")
    else:
        print(f"WARNING: Year {my_year} not implemented!")
            
    if 0: # check in number of timestamps in year:
        if my_year == '2016':
            my_diff = my_df.shape[0] - 366*24*4
        else:
            my_diff = my_df.shape[0] - 365*24*4
        if my_diff:
            print(f"WARNING: Found {my_diff} difference in number of timestamps!")
        else:
            if verbose:
                print("- check for number of timestamps : OK")

    # check time changes in 2016 by visual inspection:
    # qgrid.show_grid(my_df.loc['2016-03-27'])
    # qgrid.show_grid(my_df.loc['2016-10-30'])
    
    
def match_ev(my_participant, verbose=False):
    
    # read unmatched data:
    my_df_ev = pd.read_pickle(f"../data/ev/processed/ev_df_{my_participant}.pickle")
    
    # checks:
    checks(my_df_ev, my_year='', verbose=verbose)
    
    # Info:
    if verbose:
        print(f"EV data start: {my_df_ev.index[ 0]}.")
        print(f"EV data end:   {my_df_ev.index[-1]}.")
    
    # check if data encompasses enough days for matching:
    my_time_delta = my_df_ev.index[-1] - my_df_ev.index[0]
    if my_time_delta/pd.Timedelta('1 day') >= 366 + 10:
        if verbose:
            print('Data encompasses enough days for matching.')
        GO = True
    else:
        print(f'Data does not encompasses enough days for matching: SKIPPING {my_participant}!')
        GO = False
        my_df_ev_2016 = None
        
    if GO:
        # check if Saturday 3 January 2015 00:00:00 is in data:
        if pd.Timestamp('2015-01-03') <= my_df_ev.index[-1]:
            my_start_day_str = '2015-01-02' # Friday is entirely in data
            my_start_day = pd.Timestamp('2015-01-02').date()
        # check if Saturday 4 January 2014 00:00:00 is in data:
        elif pd.Timestamp('2014-01-04') < my_df_ev.index[-1]: 
            my_start_day_str = '2014-01-03' # Friday is entirely in data
            my_start_day = pd.Timestamp('2014-01-03').date()
        else:
            my_start_day_str = None
            print(f"No appropriate start day found: SKIPPING {my_participant}!")
            my_df_ev_2016 = None

        if not my_start_day_str is None:
            my_future_day = np.unique(my_df_ev.index.date)[-2] #.strftime(format="%Y-%m-%d")
            my_future_day_str = my_future_day.strftime(format='%Y-%m-%d')
            my_days_part_1 = (my_future_day - my_start_day)/pd.Timedelta('1 day') + 1
            if verbose:
                print(f"{my_future_day.weekday() = }")

            my_past_day = my_df_ev.index[-2] - pd.Timedelta(365, unit='days')
            my_past_day = my_past_day.date()

            my_past_day_wanted_weekday = my_future_day.weekday() + 1
            if verbose:
                print(f"{my_past_day_wanted_weekday = }")

            if my_past_day.weekday() != my_past_day_wanted_weekday:
                my_days_diff = my_past_day.weekday() - my_past_day_wanted_weekday
                if my_days_diff > 0:
                    my_past_day = my_past_day - pd.Timedelta(my_days_diff, unit='days')
                else:
                    my_past_day = my_past_day - pd.Timedelta(my_days_diff + 7, unit='days')
            if my_past_day.weekday() != my_past_day_wanted_weekday:
                if verbose:
                    print(f"Weekday correction did not work!")
            else:
                my_past_day_str = my_past_day.strftime(format='%Y-%m-%d')
                if verbose:
                    print(f"{my_past_day.weekday() = }")
            my_days_part_2 = 366 - my_days_part_1
            my_end_day = my_past_day + pd.Timedelta(my_days_part_2 - 1, unit='days')
            my_end_day_str = my_end_day.strftime(format='%Y-%m-%d')
            if verbose:
                print(f"my_start_day  = {my_start_day_str}")
                print(f"my_future_day = {my_future_day_str}")
                print(f"my_past_day   = {my_past_day_str}")
                print(f"my_end_day    = {my_end_day_str}")
                
            # create my_df_ev_2016
            my_end = pd.Timestamp("2016-01-01 23:45:00") + pd.Timedelta(my_days_part_1 - 1, unit='days')
            my_index = pd.date_range(start='2016-01-01', end=my_end, freq='15min')
            my_df_ev_2016 = pd.DataFrame(my_df_ev.loc[my_start_day_str:my_future_day_str, ].values,
                                         columns=my_df_ev.columns,
                                         index=my_index)
            
            my_start = pd.Timestamp("2016-01-01 00:00:00") + pd.Timedelta(my_days_part_1, unit='days')
            my_index = pd.date_range(start=my_start, end="2016-12-31 23:45:00", freq='15min')
            my_df_ev_2016_addon = pd.DataFrame(my_df_ev.loc[my_past_day_str:my_end_day_str, ].values,
                                               columns=my_df_ev.columns,
                                               index=my_index)
            
            my_df_ev_2016 = my_df_ev_2016.append(my_df_ev_2016_addon)
            
            # checks:
            checks(my_df_ev_2016, my_year='2016', verbose=verbose)
            
    return my_df_ev_2016


def match_hh(my_residential_ID, verbose=False):
    
    # read unmatched data:
    my_df_hh = pd.read_pickle(f"../data/hh/processed/hh_df_{my_residential_ID}.pickle")
    
    # checks:
    checks(my_df_hh, my_year='', verbose=verbose)
    
    # Info:
    if verbose:
        print(f"HH data start: {my_df_hh.index[ 0]}.")
        print(f"HH data end:   {my_df_hh.index[-1]}.")
    
    my_start_day_str = '2010-01-01' # Friday
    my_start_day = pd.Timestamp('2010-01-01').date()
    
    my_future_day = np.unique(my_df_hh.index.date)[-2] #.strftime(format="%Y-%m-%d")
    my_future_day_str = my_future_day.strftime(format='%Y-%m-%d')
    my_days_part_1 = (my_future_day - my_start_day)/pd.Timedelta('1 day') + 1
    if verbose:
        print(f"{my_future_day.weekday() = }")

    my_past_day = my_df_hh.index[-2] - pd.Timedelta(365, unit='days')
    my_past_day = my_past_day.date()

    my_past_day_wanted_weekday = my_future_day.weekday() + 1
    if verbose:
        print(f"{my_past_day_wanted_weekday = }")

    if my_past_day.weekday() != my_past_day_wanted_weekday:
        my_days_diff = my_past_day.weekday() - my_past_day_wanted_weekday
        if my_days_diff > 0:
            my_past_day = my_past_day - pd.Timedelta(my_days_diff, unit='days')
        else:
            my_past_day = my_past_day - pd.Timedelta(my_days_diff + 7, unit='days')
    if my_past_day.weekday() != my_past_day_wanted_weekday:
        print(f"Weekday correction did not work!")
    else:
        my_past_day_str = my_past_day.strftime(format='%Y-%m-%d')
        if verbose:
            print(f"{my_past_day.weekday() = }")
    my_days_part_2 = 366 - my_days_part_1
    my_end_day = my_past_day + pd.Timedelta(my_days_part_2 - 1, unit='days')
    my_end_day_str = my_end_day.strftime(format='%Y-%m-%d')
    if verbose:
        print(f"my_start_day  = {my_start_day_str}")
        print(f"my_future_day = {my_future_day_str}")
        print(f"my_past_day   = {my_past_day_str}")
        print(f"my_end_day    = {my_end_day_str}")
        
    # create my_hh_2016:
    my_end = pd.Timestamp("2016-01-01 23:45:00") + pd.Timedelta(my_days_part_1 - 1, unit='days')
    my_index = pd.date_range(start='2016-01-01', end=my_end, freq='15min')
    my_df_hh_2016 = pd.DataFrame(my_df_hh.loc[my_start_day_str:my_future_day_str, ].values,
                                 columns=my_df_hh.columns,
                                 index=my_index)
    
    my_start = pd.Timestamp("2016-01-01 00:00:00") + pd.Timedelta(my_days_part_1, unit='days')
    my_index = pd.date_range(start=my_start, end="2016-12-31 23:45:00", freq='15min')
    my_df_hh_2016_addon = pd.DataFrame(my_df_hh.loc[my_past_day_str:my_end_day_str, ].values,
                                       columns=my_df_hh.columns,
                                       index=my_index)
        
    my_df_hh_2016 = my_df_hh_2016.append(my_df_hh_2016_addon)
    
    # checks:
    checks(my_df_hh_2016, my_year='2016', verbose=verbose)
    
    return my_df_hh_2016