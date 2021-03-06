import stripe
import json
import os

from flask import Flask, render_template, jsonify, request, send_from_directory
from dotenv import load_dotenv, find_dotenv

# Setup Stripe python client library
load_dotenv(find_dotenv())
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
stripe.api_version = os.getenv('STRIPE_API_VERSION')

static_dir = str(os.path.abspath(os.path.join(
    __file__, '..', os.getenv('STATIC_DIR'))))
app = Flask(__name__, static_folder=static_dir,
            static_url_path='', template_folder=static_dir)

# For demo purposes we're hardcoding the amount and currency here.
# Replace this with your cart functionality.
cart = {
    'amount': 1099,
    'currency': 'AUD'
}


def create_order(items):
    # Replace this with your order creation logic.
    # Calculate the order total on the server to prevent
    # manipulation of the amount on the client.
    return items


@app.route('/', methods=['GET'])
def get_checkout_page():
    # Display checkout page
    return render_template('index.html')


@app.route('/config', methods=['GET'])
def get_PUBLISHABLE_KEY():
    return jsonify({
        'publishableKey': os.getenv('STRIPE_PUBLISHABLE_KEY'),
        'cart': cart
    })


@app.route('/create-payment-intent', methods=['POST'])
def create_payment():
    data = json.loads(request.data)
    # Create a new customer object so that we can
    # safe the payment method for future usage.
    customer = stripe.Customer.create(
        name=data['name'],
        email=data['email']
    )

    # Create a PaymentIntent
    order = create_order(cart)
    intent = stripe.PaymentIntent.create(
        payment_method_types=['au_becs_debit'],
        setup_future_usage='off_session',
        customer=customer['id'],
        amount=order['amount'],
        currency=order['currency']
    )

    try:
        # Send publishable key and PaymentIntent details to client
        return jsonify({'clientSecret': intent.client_secret})
    except Exception as e:
        return jsonify(error=str(e)), 403


@app.route('/webhook', methods=['POST'])
def webhook_received():
    # You can use webhooks to receive information about asynchronous payment events.
    # For more about our webhook events check out https://stripe.com/docs/webhooks.
    webhook_secret = os.getenv('STRIPE_WEBHOOK_SECRET')
    request_data = json.loads(request.data)

    if webhook_secret:
        # Retrieve the event by verifying the signature using the raw body and secret if webhook signing is configured.
        signature = request.headers.get('stripe-signature')
        try:
            event = stripe.Webhook.construct_event(
                payload=request.data, sig_header=signature, secret=webhook_secret)
            data = event['data']
        except Exception as e:
            return e
        # Get the type of webhook event sent - used to check the status of PaymentIntents.
        event_type = event['type']
    else:
        data = request_data['data']
        event_type = request_data['type']
    data_object = data['object']

    if event_type == 'payment_intent.succeeded':
        print('???? Payment received!')
        # Fulfill any orders, e-mail receipts, etc
        # To cancel the payment you will need to issue a Refund (https://stripe.com/docs/api/refunds)
    elif event_type == 'payment_intent.payment_failed':
        print('??? Payment failed.')
    return jsonify({'status': 'success'})


if __name__ == '__main__':
    app.run()