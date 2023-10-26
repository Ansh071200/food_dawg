import mysql.connector

my_connection = mysql.connector.connect(
    host="",
    user="",
    password="",
    database=""
)

# fill your own details here


def insert_order_item(food_item, quantity, order_id):
    try:
        cursor = my_connection.cursor()

        # calling the stored procedure
        cursor.callproc('insert_order_item', (food_item, quantity, order_id))
        my_connection.commit()
        cursor.close()

        print("Order item inserted successfully!")

        return 1

    except mysql.connector.Error as err:
        print(f"Error inserting order item: {err}")
        my_connection.rollback()

        return -1

    except Exception as e:
        print(f"An error occurred: {e}")
        my_connection.rollback()

        return -1


def insert_order_tracking(order_id, status):
    cursor = my_connection.cursor()
    insert_query = "INSERT INTO order_tracking (order_id, status) VALUES (%s, %s)"
    cursor.execute(insert_query, (order_id, status))
    my_connection.commit()
    cursor.close()



def get_total_order_price(order_id):
    cursor = my_connection.cursor()

    # cursor.callproc("get_total_order_price",(order_id)

    query = f"SELECT get_total_order_price({order_id})"
    cursor.execute(query)
    result = cursor.fetchone()[0]

    my_connection.commit()
    cursor.close()
    return result


def get_next_order_id():
    cursor = my_connection.cursor()
    query = "SELECT MAX(order_id) FROM orders"
    cursor.execute(query)
    result = cursor.fetchone()[0]
    cursor.close()
    if result is None:
        return 1
    else:
        return result + 1


def get_order_status(order_id):
    cursor = my_connection.cursor()
    query = f"SELECT status FROM order_tracking WHERE order_id = {order_id}"
    cursor.execute(query)
    result = cursor.fetchone()
    cursor.close()
    if result:
        return result[0]
    else:
        return None


if __name__ == "__main__":
    print(get_next_order_id())
