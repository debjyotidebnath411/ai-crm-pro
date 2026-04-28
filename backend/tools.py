from datetime import datetime, timedelta
import re



def today_date():
    return datetime.today().strftime("%d-%m-%Y")


def tomorrow_date():
    return (datetime.today() + timedelta(days=1)).strftime("%d-%m-%Y")


def yesterday_date():
    return (datetime.today() - timedelta(days=1)).strftime("%d-%m-%Y")


def resolve_relative_date(text):
    t = text.lower()

    if "today" in t:
        return today_date()

    if "tomorrow" in t:
        return tomorrow_date()

    if "yesterday" in t:
        return yesterday_date()

    return ""




def normalize_time(text):
    t = text.lower().strip()

    if "12pm" in t or "12 pm" in t:
        return "12:00"

    if "1pm" in t or "1 pm" in t:
        return "13:00"

    if "2pm" in t or "2 pm" in t:
        return "14:00"

    if "3pm" in t or "3 pm" in t:
        return "15:00"

    if "4pm" in t or "4 pm" in t:
        return "16:00"

    if "5pm" in t or "5 pm" in t:
        return "17:00"

    if "6pm" in t or "6 pm" in t:
        return "18:00"

    if "7pm" in t or "7 pm" in t:
        return "19:00"

    if "8pm" in t or "8 pm" in t:
        return "20:00"

    if "9am" in t or "9 am" in t:
        return "09:00"

    if "10am" in t or "10 am" in t:
        return "10:00"

    if "11am" in t or "11 am" in t:
        return "11:00"

    if "noon" in t:
        return "12:00"

    
    match = re.search(r"\b(\d{1,2}):(\d{2})\b", t)
    if match:
        h = int(match.group(1))
        m = match.group(2)
        return f"{h:02d}:{m}"

    return ""




def clean_value(value):
    if value is None:
        return ""

    return str(value).strip()



def merge_forms(old_data, new_data):
    merged = old_data.copy()

    for k, v in new_data.items():
        if clean_value(v) != "":
            merged[k] = v

    return merged
