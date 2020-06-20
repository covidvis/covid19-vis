import urllib.request as rq
from collections import defaultdict
from pprint import pprint
import csv
import json
from sys import exit, exc_info

COUNTRY = {}
TARGET = ['C1', 'C2', 'C3', 'C4', 'C5', 'C6', 'C7', 'C8']
oxford_to_covidvis = {
    'C1': [4, "K-12 School Closure"],
    'C2': [5, "Non-essential Businesses Closure"],
    'C3': [6, "Gathering Limitations"],
    'C4': [7, "Banning Gatherings of a Certain Size"],
    'C5': [8, "Public information campaigns"],
    'C6': [9, "Shelter-in-place Order"],
    'C7': [10, "Close public transport"],
    'C8': [11, "Travel Restrictions"]
}

EXPORT_HEADER=[
    "country_id",
    "country_name",
    "date",
    "Coverage",
    "K-12 School Closure", # C1 actually include up to university
    "Non-essential Businesses Closure", # C2
    "Gathering Limitations", # C3
    "Banning Gatherings of a Certain Size", # C4
    "Public information campaigns", # C5
    "Shelter-in-place Order", # C6
    "Close public transport", # C7
    "Travel Restrictions", # C8
    "State of Emergency Declaration",
    "Note"    
]

def get_data():
    rq.urlretrieve("https://raw.githubusercontent.com/OxCGRT/covid-policy-tracker/master/data/OxCGRT_latest_withnotes.csv", "OxCGRT_latest.csv")
    raw_csv = open("OxCGRT_latest.csv", 'r')
    raw_data = csv.reader(raw_csv, delimiter=',')
    data = [row for row in raw_data]
    return data[0], data[1:]

def transpose(data):
    for entry in data:
        if len(entry) < 40: continue
        country_idx = entry[1]

        if country_idx not in COUNTRY:
            COUNTRY[country_idx] = {
                "country_name": entry[0],
                "country_code": entry[1]
            }
            
        entry_date = entry[2]
        previous_flag = ""
        current_record = {}
        for label_idx, label in enumerate(header):
            flag = label[:2]
            if flag in oxford_terms and flag != previous_flag:
                previous_flag = flag
                if flag not in COUNTRY[country_idx]:
                    COUNTRY[country_idx][flag]={
                        "code": flag,
                        "name": oxford_terms[flag]["name"],
                        "events": []
                    }
                current_record = {"date": entry_date}                
            # elif flag in oxford_terms and len(COUNTRY[country_idx][flag]["events"])>0:
            #     if COUNTRY[country_idx][flag]["events"][-1] != current_record:
            #         COUNTRY[country_idx][flag]["events"].append(current_record)
            if flag in oxford_terms:
                try:
                    if "Notes" in label:
                        pass
                    elif len(entry[label_idx]) > 0:
                        recorded_value = str(int(float(entry[label_idx])))
                    else: continue
                except:
                    for idx, e in enumerate(entry):
                        print(header[idx], "\t|\t",  e)
                    exit()

                if "Notes" in label:
                    current_record["Notes"] = entry[label_idx]
                
                elif "Flag" in label:
                    if "amount" in oxford_terms[flag]:
                        pass
                    else:
                        current_record["coverage"] = oxford_terms[flag]["coverage"][recorded_value]

                else:
                    if "amount" in oxford_terms[flag]:
                        current_record["amount"] = str(recorded_value) + ' USD'
                    else:
                        current_record["level"] = oxford_terms[flag]["levels"][recorded_value]
            
            #save into history
            if 'level' not in current_record and 'amount' not in current_record:
                pass
            elif flag in oxford_terms and flag in COUNTRY[country_idx] and len(COUNTRY[country_idx][flag]["events"])>0:
                p_record = COUNTRY[country_idx][flag]["events"][-1]
                
                if p_record['date'] == current_record['date'] and len(current_record) >= len(p_record):
                    COUNTRY[country_idx][flag]["events"] = COUNTRY[country_idx][flag]["events"][:-1]
                COUNTRY[country_idx][flag]["events"].append(current_record)

            elif flag in oxford_terms and flag in COUNTRY[country_idx] and len(COUNTRY[country_idx][flag]["events"]) == 0:
                    COUNTRY[country_idx][flag]["events"].append(current_record)

def clean_the_measure(data):
    if len(data) == 1:
        return data
    
    cleaned_data = [data[0]]
    cleaned_data[-1]['counter'] = 0

    for idx, event in enumerate(data):
        if idx == 0:continue
        
        # collapsing level changes        
        if 'level' in event:
            if event['level'] != cleaned_data[-1]['level']:
                cleaned_data[-1]['duration'] = idx - cleaned_data[-1]['counter']
                event['counter'] = idx
                cleaned_data.append(event)
        
        if 'coverage' in event and 'coverage' in cleaned_data[-1] and cleaned_data[-1]['date']!= event['date']:
            if event['coverage'] != cleaned_data[-1]['coverage']:
                cleaned_data[-1]['duration'] = idx - cleaned_data[-1]['counter']
                event['counter'] = idx
                cleaned_data.append(event)

        if 'amount' in event and cleaned_data[-1]['date']!= event['date']:
            if event['amount'] != cleaned_data[-1]['amount'] and event['amount']!='0 USD':
                cleaned_data[-1]['duration'] = idx - cleaned_data[-1]['counter']
                event['counter'] = idx
                cleaned_data.append(event)        
        # if 'Notes' in event and cleaned_data[-1]['date']!= event['date']:
        #     if event['Notes'] != cleaned_data[-1]['Notes'] and event['coverage'] == cleaned_data[-1]['coverage'] and event['level'] == cleaned_data[-1]['level']:
        #         cleaned_data[-1]['duration'] = idx - cleaned_data[-1]['counter']
        #         event['counter'] = idx
        #         cleaned_data.append(event)            

        if (idx == (len(data)-1)):
            cleaned_data[-1]['duration'] = idx - cleaned_data[-1]['counter']                        

    # preventative actions, dropping recently imposed measures
    try:
        if cleaned_data[-1]['duration'] <= 3:
            cleaned_data = cleaned_data[:-1]
    except:
        pprint(data)
        pprint(cleaned_data)
        exit()


    return cleaned_data


def cleanup(data):
    for country in COUNTRY:
        for measure in COUNTRY[country]:
            if "country" in measure: continue
            if len(COUNTRY[country][measure]["events"]) == 0:
                continue
            updated_events = clean_the_measure(COUNTRY[country][measure]["events"])
            COUNTRY[country][measure]["events"] = updated_events
    
def export(data):
    out_file = csv.writer(open('quarantine-activity-world-new-export.csv', 'w'))
    out_file.writerow(EXPORT_HEADER)

    for country in COUNTRY:
        c_code = COUNTRY[country]['country_code']
        c_name = COUNTRY[country]['country_name']
        for measure in COUNTRY[country]:
            if "country" in measure: continue
            if measure in TARGET:
                measure_index = oxford_to_covidvis[measure][0] 
                measure_name = oxford_to_covidvis[measure][1] 
                
                events = COUNTRY[country][measure]['events']
                
                for event in events:
                    string_arr = ['' for x in range(len(EXPORT_HEADER))]
                    string_arr[0] = c_code
                    string_arr[1] = c_name
                    string_arr[2] = format_date(event['date'])
                    
                    if 'coverage' in event:
                        string_arr[3] = event['coverage']
                    
                    if 'level' in event:
                        if event['level'] == 'No measures':
                            string_arr = ['' for x in range(len(EXPORT_HEADER))]
                            continue
                        string_arr[measure_index] = event['level']

                    
                    if 'Notes' in event:
                        string_arr[len(EXPORT_HEADER)-1] = event['Notes']
                    
                    string_arr = [str(x) for x in string_arr]
                    out_file.writerow(string_arr)
                    
                    
        
        
        
def format_date(date):
    # yyyymmdd to mm-dd-yyyy
    m = date[4:6]
    d = date[6:]
    y = date[:5]
    return '-'.join([m,d,y])
    

if __name__ == '__main__':
    oxford_terms = json.load(open("oxford_terms.json", "r"))
    header, data = get_data()

    transpose(data)
    cleanup(COUNTRY)
    export(COUNTRY)
    # for c in COUNTRY:
    #     if c == 'USA':
    #         pprint(COUNTRY[c])
        # elif c == 'TWN':
        #     pprint(COUNTRY[c])
    
    
