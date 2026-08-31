from apscheduler.schedulers.background import BackgroundScheduler
from app.services.mpesa_service import query_status
from app.models.mpesa_transaction import MpesaTransaction
from app.core.database import db

def start_scheduler(app):
    """
    Start the background scheduler to check pending M-Pesa transactions.
    Runs every 5 minutes.
    """
    
    def check_pending_transactions():
        with app.app_context():
            try:
                pending_txs = MpesaTransaction.query.filter_by(status="PENDING").all()
                
                if not pending_txs:
                    return
                
                print(f"🔍 Checking {len(pending_txs)} pending transaction(s)...")
                
                for tx in pending_txs:
                    try:
                        response = query_status(tx.checkout_request_id)
                        result_code = response.get("ResultCode")
                        
                        # Check if we got a valid response
                        if result_code is not None:
                            if result_code == "0" or result_code == 0:
                                tx.status = "COMPLETED"
                                # Try to extract receipt from response if available
                                if response.get("CallbackMetadata"):
                                    metadata = response.get("CallbackMetadata", {}).get("Item", [])
                                    for item in metadata:
                                        if item.get("Name") == "MpesaReceiptNumber":
                                            tx.receipt_number = item.get("Value")
                                        elif item.get("Name") == "TransactionDate":
                                            tx.transaction_date = item.get("Value")
                                print(f"✅ Transaction {tx.checkout_request_id} updated to COMPLETED")
                            else:
                                tx.status = "FAILED"
                                print(f"❌ Transaction {tx.checkout_request_id} failed: {response.get('ResultDesc')}")
                        else:
                            # If no ResultCode, Safaricom might not have processed it yet
                            # Skip this transaction and try again later
                            print(f"⏳ Transaction {tx.checkout_request_id} still processing...")
                            continue
                        
                        db.session.commit()
                        
                    except Exception as e:
                        print(f"⚠️ Error checking transaction {tx.checkout_request_id}: {e}")
                        # If we get a 500 error, Safaricom might not recognize this transaction anymore
                        # Mark it as FAILED to stop retrying
                        if "500" in str(e) or "Internal Server Error" in str(e):
                            tx.status = "FAILED"
                            tx.result_desc = "Transaction expired or not found on M-Pesa"
                            db.session.commit()
                            print(f"❌ Transaction {tx.checkout_request_id} marked as FAILED due to API error")
                        
            except Exception as e:
                print(f"⚠️ Scheduler error: {e}")

    # Create and start the scheduler
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        func=check_pending_transactions,
        trigger="interval",
        minutes=5,
        id="mpesa_status_checker",
        replace_existing=True
    )
    scheduler.start()
    print("🔄 M-Pesa status checker scheduler started (runs every 5 minutes)")
    
    return scheduler