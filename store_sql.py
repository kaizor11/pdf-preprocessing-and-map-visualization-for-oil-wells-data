import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv
import os

load_dotenv()

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = ""
DB_PORT = 123
DB_NAME = ""
TABLE_NAME = ""

df = pd.read_csv("output_new.csv")

engine = create_engine(
    f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

df.to_sql(
    name=TABLE_NAME,
    con=engine,
    if_exists="replace",
    index=False
)
