from __future__ import annotations

import os
from typing import Any
from dotenv import load_dotenv

load_dotenv()


def build_mysql_config(table_name: str, primary_key_fields: list[str]) -> dict[str, Any]:
    return {
        "host": os.getenv("MYSQL_HOST", "127.0.0.1"),
        "port": int(os.getenv("MYSQL_PORT", "3306")),
        "user": os.getenv("MYSQL_USER", "root"),
        "password": os.getenv("MYSQL_PASSWORD", ""),
        "database": os.getenv("MYSQL_DATABASE", "classicmodels"),
        "table_name": table_name,
        "primary_key_fields": primary_key_fields,
    }
