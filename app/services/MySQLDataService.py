from __future__ import annotations

from decimal import Decimal
import json
from typing import Any, Union

from .AbstractBaseDataService import AbstractBaseDataService


class MySQLDataService(AbstractBaseDataService):
    def __init__(self, config: dict) -> None:
        super().__init__(config)
        self._table_name = str(config["table_name"])
        primary_key_fields = config["primary_key_fields"]
        if not primary_key_fields:
            raise ValueError("primary_key_fields must not be empty")
        self._primary_key_fields = [str(field) for field in primary_key_fields]
        self._host = str(config["host"])
        self._port = int(config.get("port", 3306))
        self._user = str(config["user"])
        self._password = str(config["password"])
        self._database = str(config["database"])

    def _connect(self):
        try:
            import mysql.connector
        except ImportError as exc:
            raise RuntimeError(
                "mysql-connector-python is required to use MySQLDataService"
            ) from exc

        return mysql.connector.connect(
            host=self._host,
            port=self._port,
            user=self._user,
            password=self._password,
            database=self._database,
        )

    @staticmethod
    def _normalize_value(value: Any) -> Any:
        if isinstance(value, Decimal):
            return float(value)
        return value

    def _normalize_row(self, row: dict[str, Any]) -> dict[str, Any]:
        return {key: self._normalize_value(value) for key, value in row.items()}

    def _parse_primary_key(self, primary_key: Union[str, dict]) -> dict[str, Any]:
        if isinstance(primary_key, dict):
            result = dict(primary_key)
        elif len(self._primary_key_fields) == 1:
            result = {self._primary_key_fields[0]: primary_key}
        else:
            try:
                decoded = json.loads(primary_key)
            except json.JSONDecodeError as exc:
                raise ValueError("Composite primary key must be provided as a dict") from exc
            if not isinstance(decoded, dict):
                raise ValueError("Composite primary key must decode to a dict")
            result = decoded

        missing_fields = [
            field for field in self._primary_key_fields if result.get(field) is None
        ]
        if missing_fields:
            raise ValueError(f"Missing primary key fields: {', '.join(missing_fields)}")
        return {field: result[field] for field in self._primary_key_fields}

    @staticmethod
    def _build_where_clause(template: dict[str, Any]) -> tuple[str, list[Any]]:
        if not template:
            return "", []

        clauses: list[str] = []
        values: list[Any] = []
        for key, value in template.items():
            clauses.append(f"`{key}` = %s")
            values.append(value)
        return " WHERE " + " AND ".join(clauses), values

    def _get_next_integer_primary_key(self) -> int:
        if len(self._primary_key_fields) != 1:
            raise ValueError("Automatic key generation only supports single-column keys")

        field = self._primary_key_fields[0]
        query = f"SELECT COALESCE(MAX(`{field}`), 0) + 1 AS next_id FROM `{self._table_name}`"
        connection = self._connect()
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(query)
            row = cursor.fetchone() or {}
            return int(row.get("next_id", 1))
        finally:
            connection.close()

    def retrieveByPrimaryKey(self, primary_key: Union[str, dict]) -> dict:
        key_template = self._parse_primary_key(primary_key)
        where_clause, values = self._build_where_clause(key_template)
        query = f"SELECT * FROM `{self._table_name}`{where_clause}"

        connection = self._connect()
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(query, values)
            row = cursor.fetchone()
            return self._normalize_row(row) if row else {}
        finally:
            connection.close()

    def retrieveByTemplate(self, template: dict) -> list[dict]:
        where_clause, values = self._build_where_clause(template)
        query = f"SELECT * FROM `{self._table_name}`{where_clause}"

        connection = self._connect()
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(query, values)
            rows = cursor.fetchall()
            return [self._normalize_row(dict(row)) for row in rows]
        finally:
            connection.close()

    def create(self, payload: dict) -> str:
        data = dict(payload)
        if len(self._primary_key_fields) == 1:
            primary_key_field = self._primary_key_fields[0]
            if data.get(primary_key_field) is None:
                data[primary_key_field] = self._get_next_integer_primary_key()

        columns = list(data.keys())
        placeholders = ", ".join(["%s"] * len(columns))
        column_sql = ", ".join(f"`{column}`" for column in columns)
        query = f"INSERT INTO `{self._table_name}` ({column_sql}) VALUES ({placeholders})"
        values = [data[column] for column in columns]

        connection = self._connect()
        try:
            cursor = connection.cursor()
            cursor.execute(query, values)
            connection.commit()
        finally:
            connection.close()

        if len(self._primary_key_fields) == 1:
            return str(data[self._primary_key_fields[0]])

        primary_key = {field: data[field] for field in self._primary_key_fields}
        return json.dumps(primary_key, sort_keys=True)

    def updateByPrimaryKey(self, primary_key: Union[str, dict], payload: dict) -> int:
        key_template = self._parse_primary_key(primary_key)
        data = dict(payload)
        for field, value in key_template.items():
            data[field] = value

        non_key_fields = [field for field in data.keys() if field not in key_template]
        if not non_key_fields:
            return 0

        set_clause = ", ".join(f"`{field}` = %s" for field in non_key_fields)
        set_values = [data[field] for field in non_key_fields]
        where_clause, where_values = self._build_where_clause(key_template)
        query = f"UPDATE `{self._table_name}` SET {set_clause}{where_clause}"

        connection = self._connect()
        try:
            cursor = connection.cursor()
            cursor.execute(query, set_values + where_values)
            connection.commit()
            return int(cursor.rowcount)
        finally:
            connection.close()

    def deleteByPrimaryKey(self, primary_key: Union[str, dict]) -> int:
        key_template = self._parse_primary_key(primary_key)
        where_clause, values = self._build_where_clause(key_template)
        query = f"DELETE FROM `{self._table_name}`{where_clause}"

        connection = self._connect()
        try:
            cursor = connection.cursor()
            cursor.execute(query, values)
            connection.commit()
            return int(cursor.rowcount)
        finally:
            connection.close()
