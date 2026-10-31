
import os
import mysql.connector

from dotenv import load_dotenv

# Load environment variables from project root
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]

load_dotenv(ROOT_DIR / ".env")


def get_connection():

    connection = mysql.connector.connect(

        host=os.getenv("MYSQL_HOST", "localhost"),

        user=os.getenv("MYSQL_USER"),

        password=os.getenv("MYSQL_PASSWORD"),

        database=os.getenv("MYSQL_DATABASE"),

        port=int(os.getenv("MYSQL_PORT", "3306")),

        charset="utf8mb4"

    )

    return connection
