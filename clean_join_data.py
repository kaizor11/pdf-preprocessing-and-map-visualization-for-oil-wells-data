# clean data 
import pandas as pd
import numpy as np
PDF_IN_PATH = "output.csv"
PDF_OUT_PATH = "output_clean.csv"
SCRAPE_IN_PATH = "scraped_data.csv"
SCRAPE_OUT_PATH = "scraped_data_processed.csv"


PROCESS_PDF = False
PROCESS_SCRAPE = True

if PROCESS_PDF:
    df = pd.read_csv(PDF_IN_PATH)

    # clean the data
    # remove any entries with no API numbers
    df = df.dropna(subset=["api"])

    # clean up debris characters in each string
    def clean_debris(input_str, bad_chars=["{","}", "(", ")", "|"]):
        if pd.isna(input_str):
            return np.nan
        new_str = []
        for i in range(len(input_str)):
            if input_str[i] not in bad_chars:
                new_str.append(input_str[i])
        return ''.join(new_str).strip()

    clean_col_list = ["well_name",
                    "operator",
                    "api",
                    "latitude",
                    "longitude"]

    for col in clean_col_list:
        df[col] = df[col].apply(clean_debris)

    # replace NaN with "Unknown" in certain cols
    def mark_unknown(input_str):
        if not pd.isna(input_str):
            return input_str
        return "Unknown"

    unk_col_list = ["well_name",
                    "operator"]
    for col in unk_col_list:
        df[col] = df[col].apply(mark_unknown)

    #convert long/lats
    long_lat_str = df["latitude"] + " " + df["longitude"]

    def clean_long_lat_str(in_str, accepted = "-1234567890. "):
        if pd.isna(in_str):
            return np.nan
        new_str = []
        for char in in_str:
            if char in accepted:
                new_str.append(char)
        return ''.join(new_str).strip()

    long_lat_str = long_lat_str.apply(clean_long_lat_str)

    def convert_long_lat(in_str):
        if pd.isna(in_str):
            return np.nan
        numbers = in_str.split(" ")
        numbers = [float(x) for x in numbers]
        # convert sexagesimal to decimal
        lat = numbers[0] + numbers[1]/60.0 + numbers[2]/3600.0
        long = numbers[3] + numbers[4]/60.0 + numbers[5]/3600.0

        # round to 6 decimals
        lat = round(lat, 6)
        long = round(long, 6)

        return f"{lat}, {long}"

    # put lat/long back in df
    long_lat_str = long_lat_str.apply(convert_long_lat)
    df["Latitude"] = long_lat_str.apply(lambda x: np.nan if pd.isna(x) else x.split(", ")[0])
    df["Longitude"] = long_lat_str.apply(lambda x: np.nan if pd.isna(x) else x.split(", ")[1])

    # final column selection// remove pdf column
    df = df[["file_num", 
            "well_name", 
            "operator", 
            "api", 
            "latitude", 
            "longitude"]]

    print(df.head())
    df.to_csv(PDF_OUT_PATH)

if PROCESS_SCRAPE:
    #all that is really needed here is to split lat/long and replace NaN with "Unknown"
    df = pd.read_csv(SCRAPE_IN_PATH)
    df["Latitude"] = df["Latitude_Longitude"].apply(lambda x: float(x.split(", ")[0]))
    df["Longitude"] = df["Latitude_Longitude"].apply(lambda x: float(x.split(", ")[1]))
    df["Well_Name"] = df["Well_Name"].fillna("Unknown")
    df["First_Production_Date"] = df["First_Production_Date"].fillna("Unknown")
    df["Most_Recent_Production_Date"] = df["Most_Recent_Production_Date"].fillna("Unknown")

    # final column selection// remove lat_long column
    df = df[["API_Number", 
            "Well_Name", 
            "Status", 
            "Type", 
            "Closest_City", 
            "First_Production_Date",
            "Most_Recent_Production_Date",
            "Latitude",
            "Longitude"
            ]]
    
    df.to_csv(SCRAPE_OUT_PATH)