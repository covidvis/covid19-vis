from datetime import datetime
from typing import Union

import pandas as pd


def days_between(d1: Union[str, datetime], d2: Union[str, datetime]):
    if pd.isna(d1) or pd.isna(d2):
        return None
    if isinstance(d1, str):
        try:
            d1 = datetime.strptime(d1, "%m-%d-%Y")
        except ValueError:
            d1 = datetime.strptime(d1, "%Y-%m-%d")
    if isinstance(d2, str):
        try:
            d2 = datetime.strptime(d2, "%m-%d-%Y")
        except ValueError:
            d2 = datetime.strptime(d2, "%Y-%m-%d")
    return int((d2 - d1).days)

# Closure:
# emergency declaration = e/E; restaurant closure = r/R
# border screening = b/B; travel restrictions= t/T; border closures = c/C
# shelter-in-place = l/L; gathering limitations= g/G; k-12 school closures = s/S
# non-essential business closure = n/N
# face covering requirement = f/F

# Opening:
# emergency declaration lifted = a/A; 
# travel restrictions lifted= d/D;
# border closures lifted = k/K;
# shelter-in-place lifted = h/H;
# night-time curfew lifted= i/I; 
# Banning gatherings lifted = j/J;
# Face covering requirement lifted =p/P;
# k-12 school open = m/M;
# Bar and Dine-in Restaurant open = q/Q;
# Non-essential Businesses open = o/O
def create_lockdown_type(x, emo_flag):
    s = r = emo_s = ""
    regional_flag = closure_flag = not_the_first_flag = 0
    if x['Coverage'] != 'State-wide':
        r = 'Regional'
        regional_flag = 1
    if x['State of Emergency Declaration'] == "State of Emergency declared":
        s = s + " Declaration of Emergency"
        not_the_first_flag = 1
        emo_s = (emo_s + "e") if (regional_flag == 1) else (emo_s + "E")
    if x['Travel Restrictions'] == x['Travel Restrictions']:
        if not_the_first_flag == 1:
            s = s + ","
        if "Travel restrictions for out of state travelers" in x['Travel Restrictions']:
            emo_s = (emo_s + "t") if (regional_flag == 1) else (emo_s + "T")
            s = s + " Border Closure/Visitor Quarantine"
        if "Travel restrictions for out of state travelers lifted" in x['Travel Restrictions']:
            emo_s = (emo_s + "d") if (regional_flag == 1) else (emo_s + "D")
            s = s + " Border Opening/Visitor Quarantine Lifted"
        if "Border closures" in x['Travel Restrictions']:
            emo_s = (emo_s + "c") if (regional_flag == 1) else (emo_s + "C")
            s = s + " Border Closure/Visitor Quarantine"
        if "Border closures lifted" in x['Travel Restrictions']:
            emo_s = (emo_s + "k") if (regional_flag == 1) else (emo_s + "K")
            s = s + " Border Opening/Visitor Quarantine Lifted"
        not_the_first_flag = 1
    if x['Shelter-in-place Order'] == x['Shelter-in-place Order']:
        if not_the_first_flag == 1:
            s = s + ","
        if x['Shelter-in-place Order'] == "Shelter-in-place order":
            s = s + " Stay-at-home Order"
            emo_s = (emo_s + "l") if (regional_flag == 1) else (emo_s + "L")
        if x['Shelter-in-place Order'] == "Night-time curfew":
            s = s + " Curfew"
            emo_s = (emo_s + "l") if (regional_flag == 1) else (emo_s + "L")
        if x['Shelter-in-place Order'] == "Shelter-in-place order lifted":
            s = s + " Stay-at-home Order Lifted"
            emo_s = (emo_s + "h") if (regional_flag == 1) else (emo_s + "H")
        if x['Shelter-in-place Order'] == "Night-time curfew lifted":
            s = s + " Curfew Lifted"
            emo_s = (emo_s + "i") if (regional_flag == 1) else (emo_s + "I")
        not_the_first_flag = 1
    if x['Gathering Limitations'] == x['Gathering Limitations']:
        if not_the_first_flag == 1:
            s = s + ","
        if x['Gathering Limitations'] == "Banning gatherings lifted": 
            s = s + " Gatherings Ban Lifted"
            not_the_first_flag = 1
            emo_s = (emo_s + "j") if (regional_flag == 1) else (emo_s + "J")
        else: 
            s = s + " Gatherings Banned"
            not_the_first_flag = 1
            emo_s = (emo_s + "g") if (regional_flag == 1) else (emo_s + "G")
    if x['Banning Gatherings of a Certain Size'] == x['Banning Gatherings of a Certain Size']:
        if not_the_first_flag == 1:
            s = s + ","
        s = s + " Gatherings (>" + str(x['Banning Gatherings of a Certain Size']) + ") Banned"
        emo_s = (emo_s + "g") if (regional_flag == 1) else (emo_s + "G")
        not_the_first_flag = 1
    if 'Face Covering Requirements' in x:
        if x['Face Covering Requirements'] == x['Face Covering Requirements']:
            if not_the_first_flag == 1:
                s = s + ","
            if x['Face Covering Requirements'] == "Face covering requirements lifted":
                s = s + " Face covering requirements lifted"
                emo_s = (emo_s + "p") if (regional_flag == 1) else (emo_s + "P")
            else:
                s = s + " Face covering required"
                emo_s = (emo_s + "f") if (regional_flag == 1) else (emo_s + "F")
            not_the_first_flag = 1
    if x['K-12 School Closure'] == x['K-12 School Closure']:
        if not_the_first_flag == 1:
            s = s + ","
        if x['K-12 School Closure'] == "Schools closed":
            s = s + " Closure of Schools"
            emo_s = (emo_s + "s") if (regional_flag == 1) else (emo_s + "S")
        elif x['K-12 School Closure'] == "Schools open":
            s = s + " Opening of Schools"
            emo_s = (emo_s + "m") if (regional_flag == 1) else (emo_s + "M")
        closure_flag = not_the_first_flag = 1
    if x['Bar and Dine-in Restaurant Closure'] == x['Bar and Dine-in Restaurant Closure']:
        if not_the_first_flag == 1:
            s = s + ","
        if x['Bar and Dine-in Restaurant Closure'] == "Bar and dine-in restaurant closed (except take-out and delivery)":
            emo_s = (emo_s + "r") if (regional_flag == 1) else (emo_s + "R")
            closure_flag = not_the_first_flag = 1
            s = (s + " Closure of Restaurants") if (closure_flag == 0) else (s + " Restaurants")
        else: 
            emo_s = (emo_s + "q") if (regional_flag == 1) else (emo_s + "Q")
            closure_flag = not_the_first_flag = 1
            s = (s + " Opening of Restaurants") if (closure_flag == 0) else (s + " Restaurants")
    if x['Non-essential Businesses Closure'] == x['Non-essential Businesses Closure']:
        if not_the_first_flag == 1:
            s = s + ","
        if x['Non-essential Businesses Closure'] == "Non-essential businesses closed" or x['Non-essential Businesses Closure'] == "Some (cherry-picked) businesses closed; others allowed to operate possibly with extra requirements" or x['Non-essential Businesses Closure'] == "Some (cherry-picked) businesses closed":
            s = (s + " Closure of Non-essential Businesses") if (closure_flag == 0) else (
                    s + " Non-essential Businesses")
            emo_s = (emo_s + "n") if (regional_flag == 1) else (emo_s + "N")
            closure_flag = not_the_first_flag = 1
        elif x['Non-essential Businesses Closure'] == 'Non-essential businesses allowed to operate possibly with extra requirements':
            s = (s + " Opening of Non-essential Businesses") if (closure_flag == 0) else (
                    s + " Non-essential Businesses")
            emo_s = (emo_s + "o") if (regional_flag == 1) else (emo_s + "O")
            closure_flag = not_the_first_flag = 1
    if emo_flag == 1:
        return emo_s
    if s == "":
        return s
    return (r + s).strip()


# Performing a delta for world events
def append_most_recent_events (df, x):
    df = df[df['Country_Region'] == x['Country_Region']]
    df = df[df['lockdown_date'] < x['lockdown_date']]
    if (x['coverage'] == 'General'):
        df = df[df['coverage'] != 'Targeted']
    df = df.sort_values(by = ['lockdown_date'])
    # print (x['lockdown_date'], df)
    for i in {'Travel Restrictions', 'Gathering Limitations', 'Shelter-in-place Order', 'K-12 School Closure', 'Non-essential Businesses Closure'}:
        s_global = "" # most recent global/complete
        s_targeted = "" # most recent targeted
        for index, r in df.iterrows():
            if (r[i] != ''):
                if (r['coverage'] == 'Targeted'):
                    s_targeted = r[i]
                else:
                    s_global = r[i]
        x[i] = x[i] + "*"  + s_global + "*" + s_targeted
    # print ("appended: ", x)
    return x

# Helper function that computes the emoji and string for world events
def interpret_events (y, regional_flag, not_the_first_flag, s, emo_s, lockdown_type):
    a = y[lockdown_type].lower().split('*')
    if (lockdown_type == 'Shelter-in-place Order'):
        readable_closed = " Shelter-in-place Order"; readable_open = " Shelter-in-place Order Lifted";
        emoji_close = "L"; emoji_open = "H"
    if (lockdown_type == 'Gathering Limitations'): 
        readable_closed = " Gatherings Banned"; readable_open = " Gathering Ban Lifted";
        emoji_close = "G"; emoji_open = "J"
    if (lockdown_type == 'K-12 School Closure'): 
        readable_closed = " Schools Closed"; readable_open = " Schools Reopened";
        emoji_close = "S"; emoji_open = "M"
    if (lockdown_type == 'Non-essential Businesses Closure'): 
        readable_closed = " Businesses Closed"; readable_open = " Businesses Reopened";
        emoji_close = "N"; emoji_open = "O"


    # a targeted reopening is one where we move to a 
    # -- "no measure/recommend" state from a targeted or global "restrict"
    # -- targeted "restrict" state from a global "restrict", and a targeted "non-restricted" state
    # a global reopening is one where we move to a  
    # -- "no measure/recommend" state from a targeted or global "restrict"
    if ((
            (("recommend" in a[0]) or ("no measures" in a[0])) and 
            (("require" in a[1]) or ("require" in a[2]))
        ) or 
        (
            (regional_flag == 1) and ("require" in a[0]) and 
            ("require" in a[1]) and ("require" not in a[2])
        )): 
        if not_the_first_flag == 1: s = s + ","
        s = s + readable_open
        r = emoji_open.lower() if (regional_flag == 1) else emoji_open
        emo_s = (emo_s + emoji_open.lower()) if (regional_flag == 1) else (emo_s + emoji_open)
        not_the_first_flag = 1

    # a targeted closing is one where we move to a 
    # -- "restrict" state where neither targeted nor global is "restricted"
    # a global reopening is one where we move to a  
    # -- "restrict" state where the global is not "restricted"
    if ((
            (regional_flag == 1) and ("require" in a[0]) and 
            ("require" not in a[1]) and ("require" not in a[2])
        ) or
        (
            (regional_flag != 1) and ("require" in a[0]) and ("require" not in a[1])
        )):
        if not_the_first_flag == 1: s = s + ","
        s = s + readable_closed
        r = emoji_close.lower() if (regional_flag == 1) else emoji_close
        emo_s = (emo_s + emoji_close.lower()) if (regional_flag == 1) else (emo_s + emoji_close)
        not_the_first_flag = 1


    return not_the_first_flag, s, emo_s 


# lockdown new export: requires df
def create_lockdown_type_world_new_export(df, x, emo_flag):
    s = r = emo_s = ""
    x = append_most_recent_events (df, x)
    regional_flag = closure_flag = not_the_first_flag = 0
    if x['coverage'] == 'Targeted':
        r = 'Regional'
        regional_flag = 1
    for i in {'Shelter-in-place Order', 'Gathering Limitations','K-12 School Closure', 'Non-essential Businesses Closure'}:
        not_the_first_flag, s, emo_s = interpret_events (x, regional_flag, not_the_first_flag, s, emo_s, i)
    if emo_flag == 1:
        return emo_s
    if s == "":
        return s  # Ensures just "Regional" is not returned
    return (r + s).strip()


# border screening = b/B; travel restrictions= t/T; border closures = c/C
# shelter-in-place = l/L; gathering limitations= g/G; k-12 school closures = s/S
# non-essential business closure = n/N
def create_lockdown_type_world(x, emo_flag):
    s = r = emo_s = ""
    regional_flag = closure_flag = not_the_first_flag = 0
    if x['coverage'] == 'Targeted':
        r = 'Regional'
        regional_flag = 1
    if x['Travel Restrictions'] == "Screening":  # assumption: only one travel restriction at a time
        s = s + " Border Screening"
        not_the_first_flag = 1
        emo_s = (emo_s + "b") if (regional_flag == 1) else (emo_s + "B")
    elif x['Travel Restrictions'] == "Quarantine on high-risk regions":
        s = s + " Visitor Quarantine"
        not_the_first_flag = 1
        emo_s = (emo_s + "t") if (regional_flag == 1) else (emo_s + "T")
    elif x['Travel Restrictions'] == "Ban on high risk regions":
        s = s + " Border Closures"
        not_the_first_flag = 1
        emo_s = (emo_s + "c") if (regional_flag == 1) else (emo_s + "C")
    if x['Shelter-in-place Order'] == "Restrict movement":
        # Movement restriction recommended is omitted
        if not_the_first_flag == 1:
            s = s + ","
        s = s + " Stay-at-home Order"
        not_the_first_flag = 1
        emo_s = (emo_s + "l") if (regional_flag == 1) else (emo_s + "L")
    if x['Gathering Limitations'] == "Required Cancelling Public Events":
        # Recommend Cancelling Public Events is omitted
        if not_the_first_flag == 1:
            s = s + ","
        s = s + " Gatherings Banned"
        not_the_first_flag = 1
        emo_s = (emo_s + "g") if (regional_flag == 1) else (emo_s + "G")
    if x['K-12 School Closure'] == "Required Closing":
        if not_the_first_flag == 1:
            s = s + ","
        s = s + " Closure of Schools"
        closure_flag = 1
        not_the_first_flag = 1
        emo_s = (emo_s + "s") if (regional_flag == 1) else (emo_s + "S")
    if x['Non-essential Businesses Closure'] == "Required Closing Workspaces":
        # Recommend Closing Workspaces is omitted
        if not_the_first_flag == 1:
            s = s + ","
        if closure_flag == 0:
            s = s + " Closure of Non-essential Businesses"
        else:
            s = s + " Non-essential Businesses"
        closure_flag = 1
        not_the_first_flag = 1
        emo_s = (emo_s + "n") if (regional_flag == 1) else (emo_s + "N")
    if emo_flag == 1:
        return emo_s
    if s == "":
        return s  # Ensures just "Regional" is not returned
    return (r + s).strip()





def str2emo(s):
    return ''.join(
        {
            'e': '🚫⚠️',
            'b': '🚫🛃',
            't': '🚫💼',
            'c': '🚫🛩',
            'l': '🚫🏠',
            'g': '🚫👨‍👩‍👧‍👦',
            's': '🚫🎓',
            'r': '🚫🍔',
            'n': '🚫🏬',
            'f': '🚫😷',
            'a': '⚠️',
            'k': '🛃',
            'd': '💼',
            'k': '🛩',
            'h': '🏠',
            'j': '👨‍👩‍👧‍👦',
            'm': '🎓',
            'q': '🍔',
            'o': '🏬',
            'p': '😷',
        }[c] for c in s.lower()
    )


def strip_nans(x):
    # gets rid of nans in a list
    if isinstance(x, list):
        x_strip = ""
        for a in x:
            if a == a:
                # not nan
                x_strip = x_strip + a.strip()
        return x_strip
    else:
        return x.strip()


def split_into_list(word):
    return [char for char in word]
