from app.models.corporate import Corporate
from app.core.database import db
from sqlalchemy.exc import IntegrityError



def create_corporate(data):
    new_corporate = Corporate(
        corporate_name=data['corporate_name'],
        location=data['location'],
        address=data.get('address'),
        contacts=data.get('contacts'),
        wallet_type=data.get('wallet_type') 

    )

    try:
        db.session.add(new_corporate)
        db.session.commit()
        return new_corporate
    except Exception as e:
        db.session.rollback()
        raise e

def get_all_corporates():
    """Get all corporates."""
    return Corporate.query.all()


def get_corporate(corporate_id):
    """Get a single corporate by ID."""
    corporate = Corporate.query.get(corporate_id)
    if not corporate:
        raise ValueError("Corporate not found")
    return corporate


def delete_corporate(corporate_id):
    corporate = Corporate.query.get(corporate_id)

    if not corporate:
        raise ValueError("Corporate not found")

    db.session.delete(corporate)
    db.session.commit()

    return {
        "message": f"Corporate {corporate_id} deleted successfully"
    }
    
#update corporate details
def update_corporate(corporate_id, data):
    
    corporate = Corporate.query.get(corporate_id)

    if not corporate:
        raise ValueError("Corporate not found")

    corporate.corporate_name = data.get(
        "corporate_name",
        corporate.corporate_name
    )

    corporate.location = data.get(
        "location",
        corporate.location
    )

    corporate.address = data.get(
        "address",
        corporate.address
    )

    corporate.contacts = data.get(
        "contacts",
        corporate.contacts
    )

    corporate.wallet_type = data.get(
        "wallet_type",
        corporate.wallet_type
    )

    db.session.commit()

    return corporate