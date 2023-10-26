# {*THESE ARE THE MODULES NEEDED TO RUN THIS PROJECT*}
#
# {----------v----------}
#
# mysql-connector-python
# fastapi[all]



from fastapi import FastAPI
from fastapi import Request
from fastapi.responses import JSONResponse
import db_func
import extractor
app = FastAPI()




# storing content of in_progress orders
# will be in the format of :
# {session_id:{"item","quantity"},...}

inprogress_orders = {}

@app.post("/")
async def handle_request(request: Request):
    # retrieve the data from the request
    payload = await request.json()

    # extracting the necessary information from the payload
    intent = payload['queryResult']['intent']['displayName']
    parameters = payload['queryResult']['parameters']
    output_contexts = payload['queryResult']['outputContexts']

    # extracted session id
    session_id = extractor.extract_session_id(output_contexts[0]["name"])

    # for easier functionality
    intent_handler_dict = {
        'order_add': add_to_order,
        'remove_order': remove_from_order,
        'Complete_order': complete_order,
        'track-order__context_ongoing_order': track_order
    }

    # passing necessary params i.e parameters and session_id
    return intent_handler_dict[intent](parameters, session_id)

def save_to_db(order: dict):
    next_order_id = db_func.get_next_order_id()
    for food_item, quantity in order.items():
        rcode = db_func.insert_order_item(
            food_item,
            quantity,
            next_order_id
        )

        # if return_code is -1 return the error_code as -1
        if rcode == -1:
            return -1

    # by default the order status is in progress
    # further can be changed by the db admins

    db_func.insert_order_tracking(next_order_id, "in progress")


    return next_order_id

def complete_order(session_id: str):

    # if the order hasn't been placed
    if session_id not in inprogress_orders:
        fulfillment_text = "I'm having a trouble finding your order. Sorry! Can you place a new order please?"
    # extract the order dict present currently
    else:
        order = inprogress_orders[session_id]

        # saving to the db and getting the order_id from the db {the function is defined above}
        order_id = save_to_db(order)

        # internal server error
        if order_id == -1:
            fulfillment_text = "Sorry, I couldn't process your order due to a error. " \
                               "Please place a new order again"
        else:
            # gets the order total
            order_total = db_func.get_total_order_price(order_id)
            fulfillment_text = f"Awesome. We have placed your order. " \
                           f"Here is your order id # {order_id}. " \
                           f"Your order total is {order_total} which you can pay at the time of delivery!"

        del inprogress_orders[session_id]

    return JSONResponse(content={
        "fulfillmentText": fulfillment_text
    })


def add_to_order(parameters: dict, session_id: str):
    # extract fooditems and quantity
    food_items = parameters["food-item"]
    quantities = parameters["number"]

    # in case of missing parameters like quantity or foos items
    if len(food_items) != len(quantities):
        fulfillment_text = "Sorry I didn't understand. Can you please specify food items and quantities clearly?"
    else:
        # create a dict out of the two
        new_food_dict = dict(zip(food_items, quantities))

        # checking for session_id in dict
        if session_id in inprogress_orders:
            # updating the current dict with new data
            current_food_dict = inprogress_orders[session_id]
            current_food_dict.update(new_food_dict)
            # correspondingly updating the inprogress dict as well
            inprogress_orders[session_id] = current_food_dict
        else:
            inprogress_orders[session_id] = new_food_dict

        # getting the orders
        order_str = extractor.get_str_from_food_dict(inprogress_orders[session_id])
        fulfillment_text = f"So far you have: {order_str}. Do you need anything else?"

    return JSONResponse(content={
        "fulfillmentText": fulfillment_text
    })


def remove_from_order(parameters: dict, session_id: str):
    if session_id not in inprogress_orders:
        # if inprogress is empty
        return JSONResponse(content={
            "fulfillmentText": "I'm having a trouble finding your order. Sorry! Can you place a new order please?"
        })

    # extracting what the user want to delete
    food_items = parameters["food-item"]

    # check the present items in the dict
    current_order = inprogress_orders[session_id]

    removed_items = []
    no_such_items = []

    for item in food_items:
        # if item in the food_items but not in the orders
        if item not in current_order:
            no_such_items.append(item)
        else:
            # if item in current order
            removed_items.append(item)
            del current_order[item]

    if len(removed_items) > 0:
        fulfillment_text = f'Removed {",".join(removed_items)} from your order!'

    if len(no_such_items) > 0:
        fulfillment_text = f' Your current order does not have {",".join(no_such_items)}'

    # if no orders
    if len(current_order.keys()) == 0:
        fulfillment_text += " Your order is empty!"
    else:
        # current present orders after removal
        order_str = extractor.get_str_from_food_dict(current_order)
        fulfillment_text += f" Here is what is left in your order: {order_str}"

    return JSONResponse(content={
        "fulfillmentText": fulfillment_text
    })


def track_order(parameters: dict):
    # extracting order id
    order_id = int(parameters['order_id'])

    # to get order status
    order_status = db_func.get_order_status(order_id)
    if order_status:
        fulfillment_text = f"The order status for order id: {order_id} is: {order_status}"
    else:
        fulfillment_text = f"No order found with order id: {order_id}"

    return JSONResponse(content={
        "fulfillmentText": fulfillment_text
    })