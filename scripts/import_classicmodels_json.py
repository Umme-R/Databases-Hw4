from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
import mysql.connector


load_dotenv()


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CUSTOMERS_PATH = Path(
    os.getenv("CUSTOMERS_JSON_PATH", r"C:\Users\ummer\Downloads\customers.json")
)
DEFAULT_ORDERS_PATH = Path(
    os.getenv("ORDERS_JSON_PATH", r"C:\Users\ummer\Downloads\orders.json")
)


def load_json(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError(f"{path} must contain a JSON array")
    return data


def connect_server():
    return mysql.connector.connect(
        host=os.getenv("MYSQL_HOST", "127.0.0.1"),
        port=int(os.getenv("MYSQL_PORT", "3306")),
        user=os.getenv("MYSQL_USER", "root"),
        password=os.getenv("MYSQL_PASSWORD", ""),
    )


def connect_database():
    return mysql.connector.connect(
        host=os.getenv("MYSQL_HOST", "127.0.0.1"),
        port=int(os.getenv("MYSQL_PORT", "3306")),
        user=os.getenv("MYSQL_USER", "root"),
        password=os.getenv("MYSQL_PASSWORD", ""),
        database=os.getenv("MYSQL_DATABASE", "classicmodels"),
    )


def ensure_database() -> None:
    database = os.getenv("MYSQL_DATABASE", "classicmodels")
    connection = connect_server()
    try:
        cursor = connection.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{database}`")
        connection.commit()
    finally:
        connection.close()


def ensure_tables() -> None:
    connection = connect_database()
    try:
        cursor = connection.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS customers (
                customerNumber INT PRIMARY KEY,
                customerName VARCHAR(255) NOT NULL,
                contactLastName VARCHAR(255) NOT NULL,
                contactFirstName VARCHAR(255) NOT NULL,
                phone VARCHAR(50) NOT NULL,
                addressLine1 VARCHAR(255) NOT NULL,
                addressLine2 VARCHAR(255) NULL,
                city VARCHAR(100) NOT NULL,
                state VARCHAR(100) NULL,
                postalCode VARCHAR(20) NULL,
                country VARCHAR(100) NOT NULL,
                salesRepEmployeeNumber INT NULL,
                creditLimit DECIMAL(10, 2) NULL
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS orders (
                orderNumber INT PRIMARY KEY,
                orderDate DATE NOT NULL,
                requiredDate DATE NOT NULL,
                shippedDate DATE NULL,
                status VARCHAR(50) NOT NULL,
                comments TEXT NULL,
                customerNumber INT NOT NULL,
                CONSTRAINT fk_orders_customer
                    FOREIGN KEY (customerNumber) REFERENCES customers(customerNumber)
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS orderdetails (
                orderNumber INT NOT NULL,
                productCode VARCHAR(50) NOT NULL,
                quantityOrdered INT NOT NULL,
                priceEach DECIMAL(10, 2) NOT NULL,
                orderLineNumber INT NOT NULL,
                PRIMARY KEY (orderNumber, productCode),
                CONSTRAINT fk_orderdetails_order
                    FOREIGN KEY (orderNumber) REFERENCES orders(orderNumber)
                    ON DELETE CASCADE
            )
            """
        )
        connection.commit()
    finally:
        connection.close()


def normalize_date(value: Any) -> Any:
    if value in (None, "", "None"):
        return None
    return value


def import_customers(customers_path: Path) -> int:
    rows = load_json(customers_path)
    payload: list[tuple[Any, ...]] = []
    for row in rows:
        contact = row.get("contact", {})
        address = row.get("address", {})
        payload.append(
            (
                row["customerNumber"],
                row["customerName"],
                contact.get("lastName", "").strip(),
                contact.get("firstName", "").strip(),
                row["phone"],
                address.get("addressLine1"),
                address.get("addressLine2"),
                address.get("city"),
                address.get("state"),
                address.get("postalCode"),
                (address.get("country") or "").strip(),
                row.get("salesRepNumber"),
                row.get("creditLimit"),
            )
        )

    connection = connect_database()
    try:
        cursor = connection.cursor()
        cursor.executemany(
            """
            INSERT INTO customers (
                customerNumber, customerName, contactLastName, contactFirstName, phone,
                addressLine1, addressLine2, city, state, postalCode, country,
                salesRepEmployeeNumber, creditLimit
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                customerName = VALUES(customerName),
                contactLastName = VALUES(contactLastName),
                contactFirstName = VALUES(contactFirstName),
                phone = VALUES(phone),
                addressLine1 = VALUES(addressLine1),
                addressLine2 = VALUES(addressLine2),
                city = VALUES(city),
                state = VALUES(state),
                postalCode = VALUES(postalCode),
                country = VALUES(country),
                salesRepEmployeeNumber = VALUES(salesRepEmployeeNumber),
                creditLimit = VALUES(creditLimit)
            """,
            payload,
        )
        connection.commit()
        return len(payload)
    finally:
        connection.close()


def import_orders_and_details(orders_path: Path) -> tuple[int, int]:
    rows = load_json(orders_path)
    order_payload: list[tuple[Any, ...]] = []
    detail_payload: list[tuple[Any, ...]] = []

    for row in rows:
        order_payload.append(
            (
                row["orderNumber"],
                row["orderDate"],
                row["requiredDate"],
                normalize_date(row.get("shippedDate")),
                row["status"],
                row.get("comments"),
                row["customerNumber"],
            )
        )
        for detail in row.get("orderDetails", []):
            detail_payload.append(
                (
                    row["orderNumber"],
                    detail["productCode"],
                    detail["quantityOrdered"],
                    detail["priceEach"],
                    detail["orderLineNumber"],
                )
            )

    connection = connect_database()
    try:
        cursor = connection.cursor()
        cursor.executemany(
            """
            INSERT INTO orders (
                orderNumber, orderDate, requiredDate, shippedDate, status, comments, customerNumber
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                orderDate = VALUES(orderDate),
                requiredDate = VALUES(requiredDate),
                shippedDate = VALUES(shippedDate),
                status = VALUES(status),
                comments = VALUES(comments),
                customerNumber = VALUES(customerNumber)
            """,
            order_payload,
        )
        cursor.executemany(
            """
            INSERT INTO orderdetails (
                orderNumber, productCode, quantityOrdered, priceEach, orderLineNumber
            ) VALUES (%s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                quantityOrdered = VALUES(quantityOrdered),
                priceEach = VALUES(priceEach),
                orderLineNumber = VALUES(orderLineNumber)
            """,
            detail_payload,
        )
        connection.commit()
        return len(order_payload), len(detail_payload)
    finally:
        connection.close()


def main() -> None:
    customers_path = DEFAULT_CUSTOMERS_PATH
    orders_path = DEFAULT_ORDERS_PATH
    if not customers_path.exists():
        raise FileNotFoundError(f"customers file not found: {customers_path}")
    if not orders_path.exists():
        raise FileNotFoundError(f"orders file not found: {orders_path}")

    ensure_database()
    ensure_tables()
    customer_count = import_customers(customers_path)
    order_count, detail_count = import_orders_and_details(orders_path)
    print(
        f"Imported {customer_count} customers, {order_count} orders, "
        f"and {detail_count} orderdetails into {os.getenv('MYSQL_DATABASE', 'classicmodels')}."
    )


if __name__ == "__main__":
    main()
