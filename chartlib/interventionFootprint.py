# 'e':Declaration of Emergency 
# 't':'Travel restrictions'
# 'c': Border Closure/Visitor Quarantine
# 's': School closure 
# 'n':Closure of non-essential businesses
# 'l': Stay at home order
severityScore = {'e':0.1,'g':0.3, 'c':0.3, 's':0.4,'r':0.6 , 't':0.6, 'n':0.8, 'l':1}

import pandas as pd
import numpy as np
from utils import create_lockdown_type, split_into_list, str2emo
df = pd.read_csv("../data/quarantine-activity-US-Apr16-long.csv")


# START modified from _ingest_usa_quarantine_df
quarantine_csv = "../data/quarantine-activity-US-Apr16-long.csv"
quarantine_df = pd.read_csv(quarantine_csv)
groupcol = 'Province_State'

quarantine_df = quarantine_df.rename(columns={'State': 'Province_State', 'Effective Date': 'lockdown_date','Coverage.type':'Coverage'})
quarantine_df = quarantine_df.sort_values('Coverage', ascending=True)
quarantine_df['lockdown_type'] = quarantine_df.apply(lambda x: create_lockdown_type(x, 0), axis=1)
quarantine_df['emoji_string'] = quarantine_df.apply(lambda x: create_lockdown_type(x, 1), axis=1)
quarantine_df['lockdown_type'].replace('', np.nan, inplace=True)

quarantine_df = quarantine_df.dropna(subset=['lockdown_type'])
# #TODO: this is where the columns get dropped
# quarantine_df = quarantine_df.groupby(['lockdown_date', 'Province_State']).agg({
#     'lockdown_type': lambda col: '; '.join(col),
#     'emoji_string': lambda col: ''.join(col),
#     'population_size': lambda col:col,
#     'Coverage.location': lambda col:col
# }).reset_index()

quarantine_df.loc[quarantine_df.lockdown_type=="Regional Border Closure/Visitor Quarantine","emoji_string"]="t"#bugfix
# Breaking up emoji into separate rows for vertical stacking
quarantine_df.emoji_string = quarantine_df.emoji_string.apply(split_into_list)

quarantine_df = quarantine_df.explode(column='emoji_string')
quarantine_df['Coverage'] = quarantine_df.emoji_string.apply(
    lambda x: 'Statewide' if str(x).isupper() else 'Regional'
)
quarantine_df = quarantine_df.sort_values('Coverage', ascending=False)
quarantine_df.emoji_string = quarantine_df.emoji_string.str.lower()
quarantine_df['emoji'] = quarantine_df['emoji_string'].map(str2emo)
quarantine_df['event_index'] = quarantine_df.groupby(['Province_State', 'lockdown_date']).cumcount()

# # quarantine_cols = [
# #     groupcol, 'lockdown_date', 'lockdown_type', 'emoji', 'emoji_string', 'event_index', 'Coverage','Coverage.location'
# # ]
quarantine_cols = ['Province_State', 'Coverage', 'Coverage.location', 'lockdown_date','population_size','lockdown_type', 'emoji_string', 'emoji',
       'event_index']
quarantine_df = quarantine_df[quarantine_cols]

# # END modified from _ingest_usa_quarantine_df

quarantine_df_orig = pd.read_csv(quarantine_csv)
state_populations = quarantine_df_orig[quarantine_df_orig["Coverage.type"]=="State-wide"][["State","population_size"]].drop_duplicates()
state_populations = state_populations.rename(columns={'State': 'Province_State',"population_size":"state_population_size"})
state_populations.loc[state_populations["Province_State"]=="Puerto Rico","state_population_size"] = 3725789 # Obtained from https://www.census.gov/quickfacts/PR
state_populations.state_population_size = state_populations.state_population_size.astype("int")

quarantine_df = quarantine_df.merge(state_populations)

quarantine_df = quarantine_df.dropna(subset=["population_size"])
quarantine_df.population_size = quarantine_df.population_size.str.replace(",","")
quarantine_df.population_size = quarantine_df.population_size.astype("int")

quarantine_df["severityScore"] = quarantine_df.emoji_string.apply(lambda x: severityScore[x])
quarantine_df.lockdown_date = quarantine_df.lockdown_date.str.replace("/","-")
quarantine_df.lockdown_date = pd.to_datetime(quarantine_df.lockdown_date)
quarantine_df = quarantine_df[['Province_State', 'Coverage', 'Coverage.location', 'lockdown_date',
       'population_size', 'state_population_size', 'severityScore']]

def compute_state_replacements(qdf,state):
    df_state_replacements = []
    qdf = quarantine_df[quarantine_df["Province_State"]==state]
    statewideEvents = qdf[qdf["Coverage"]=="Statewide"]
    relevantCountiesInState= list(set(qdf[qdf["Province_State"]==state]["Coverage.location"]) - set([state]))
    # adding "Others" dummy state populated with statewide population - sum(relevant counties population)
    relevantCountiesInState= list(set(qdf[qdf["Province_State"]==state]["Coverage.location"]) - set([state]))
    relevant_county_population_lookup = qdf[qdf["Coverage.location"].isin(relevantCountiesInState)][["Coverage.location","population_size"]].drop_duplicates()
    state_population_size = state_populations[state_populations["Province_State"]==state].state_population_size.values[0]
    other_population = state_population_size - relevant_county_population_lookup.population_size.sum()
    qdf.loc[len(qdf)] = [state,"Regional","Others",np.nan,other_population,state_population_size,np.nan]
    relevantCountiesInState  = relevantCountiesInState + ["Others"]
    for statewideEvent in statewideEvents.iterrows(): 
    #     statewideLockdown_date = "2020-03-12"
    #     statewideSeverity = "0.1"
        statewideLockdown_date = statewideEvent[1].lockdown_date
        statewideSeverity = statewideEvent[1].severityScore
        for county in relevantCountiesInState: 
            #print(county)
            #display(qdf[qdf["Coverage.location"]==county])
            try:
                # Catch error since some counties don't show up until a later date, ignore these counties 
                clone = np.repeat(qdf[qdf["Coverage.location"]==county].iloc[0],1)
                clone.lockdown_date = statewideLockdown_date
                clone.severityScore = statewideSeverity
                df_state_replacements.append(clone)
            except (IndexError):
                pass
                

    df_state_replacements = pd.DataFrame(df_state_replacements,columns=qdf.columns)
    return df_state_replacements 

def compute_state_intervention_footprint_curve(state):
    qdf = quarantine_df[quarantine_df["Province_State"]==state]
    qdf_additional = compute_state_replacements(qdf,state)
    qdf_result = pd.concat([qdf,qdf_additional])
    # For each date, compute a cumulative max, keeping only the entry with the maximum severity score
    qdf_keep_all=[]
    for ldate in qdf.lockdown_date.unique():
        # ldate = "2020-03-13"
        qdf_before = qdf_result[qdf_result["lockdown_date"]<=ldate]
        # Compute the max severity for that location for the given day
        qdf_before["severityMax"] = qdf_before.groupby("Coverage.location")["severityScore"].transform(max)
        qdf_keep = qdf_before[qdf_before["severityScore"] == qdf_before["severityMax"]]
        qdf_keep["dateBefore"] = ldate
        qdf_keep = qdf_keep.drop_duplicates(subset="Coverage.location") # applicable only for the last date when severityMax=1 for multiple lockdown_dates, keep just one so that last entry doesn't exceed 1
        qdf_keep_all.append(qdf_keep)
    #     display(qdf_keep)
    qdf_keep_all = pd.concat(qdf_keep_all)

    # compute the intervention footprint for the kept df
    qdf_keep_all["pctStateAffected"]= qdf_keep_all["population_size"]/qdf_keep_all["state_population_size"]
    qdf_keep_all["interventionFootprint"] = qdf_keep_all["pctStateAffected"]*qdf_keep_all["severityScore"]

    qdf_keep_all = qdf_keep_all[qdf_keep_all["Coverage"]=="Regional"]
    # Sum the intervention footprint based on the date we used for the keep max (note this is based on the lockdown date)
    qdf_keep_all_result = qdf_keep_all.groupby("dateBefore").sum().reset_index()
    return qdf_keep_all_result


df_all = []
for state in quarantine_df.Province_State.unique():
    print (state)
    
    statedf = compute_state_intervention_footprint_curve(state)
    statedf["State"]=state
    df_all.append(statedf)

df_all = pd.concat(df_all)
df_all.to_csv("../data/interventionFootprintByState.csv")