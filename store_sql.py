import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv
import os

load_dotenv()

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = "100.53.132.91"
DB_PORT = 3306
DB_NAME = "oil_wells"
TABLE_NAME = "well_info_df"
CSV_FILE = "output.csv"

df = pd.read_csv()

engine = create_engine(
    f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

df.to_sql(
    name=TABLE_NAME,
    con=engine,
    if_exists="replace",
    index=False
)