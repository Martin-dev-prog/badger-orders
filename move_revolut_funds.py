iimport requests
import os
import stripe

# Set your Stripe secret key from environment variable
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

def move_funds_from_stripe():
    try:
        # Retrieve the Stripe balance
        balance = stripe.Balance.retrieve()
        available = balance["available"][0]
        amount = available["amount"] / 100  # Convert from pence to GBP
        currency = available["currency"].upper()

        print(f"✅ Available in Stripe: £{amount:.2f} {currency}")

        # Optional: trigger payout manually (Stripe usually auto-payouts)
        # Uncomment below if you want to control payout manually
        # payout = stripe.Payout.create(
        #     amount=int(amount * 100),
        #     currency=currency.lower(),
        #     method="standard",
        #     statement_descriptor="Badger Order Payout"
        # )
        # print("Payout triggered:", payout)

    except stripe.error.StripeError as e:
        print(f"❌ Stripe error: {e.user_message}")
    except Exception as ex:
        print(f"❌ Unexpected error: {ex}")

if __name__ == "__main__":
    move_funds_from_stripe()
