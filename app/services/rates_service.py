from app.core.database import db
from app.models.rates import RateType, Rate
from sqlalchemy.exc import IntegrityError
from app.models.users import User

def check_is_super_admin(user_id):
    user = User.query.get(user_id)
    if not user:
        raise ValueError("User not found.")
    if user.role !="SUPER_ADMIN":
        raise ValueError("Access denied. Only SUPER_ADMIN can create rates")
    return user


def create_rate_type(data):
    
    check_is_super_admin(data['created_by'])
        
    new_type = RateType(name=data['name'].upper())
        
    try:
        db.session.add(new_type)
        db.session.commit()
        return new_type
    except IntegrityError:
        db.session.rollback()
        raise ValueError("This rate type already exists")
    
def get_all_rate_types():
    return RateType.query.all()

def get_rate_type(rate_type_id):
    rate_type = RateType.query.get(rate_type_id)
    if not rate_type:
        raise ValueError("Rate type not found")
    return rate_type

def update_rate_type(rate_type_id, data):
    check_is_super_admin(data['created_by'])
    rate_type = get_rate_type(rate_type_id)
    
    if 'name' in data:
        rate_type.name = data['name'].upper()
    
    try:
        db.session.commit()
        return rate_type
    except IntegrityError:
        db.session.rollback()
        raise ValueError("Rate type name already exists")


def delete_rate_type(rate_type_id, user_id):
    check_is_super_admin(user_id)
    rate_type = get_rate_type(rate_type_id)
    
    # Check if rate type has associated rates
    if rate_type.rates:
        raise ValueError("Cannot delete rate type with existing rates. Delete rates first.")
    
    db.session.delete(rate_type)
    db.session.commit()
    return {"message": f"Rate type {rate_type_id} deleted successfully"}

#RATE
   
def create_rate(data):
    
    check_is_super_admin(data['created_by'])

    new_rate = Rate(
        rate=data['rate'],
        rate_type_id=data['rate_type_id'],
        created_by=data['created_by']
    )

    try:
        db.session.add(new_rate)
        db.session.commit()
        return new_rate
    except IntegrityError:
        db.session.rollback()
        raise ValueError("Failed to create rate. Check if rate_type_id exists.")
    

def get_all_rates():
    return Rate.query.all()   

def get_rate(rate_id):
    rate = Rate.query.get(rate_id)
    if not rate:
        raise ValueError("Rate not found")
    return rate


def update_rate(rate_id, data):
    check_is_super_admin(data['created_by'])
    rate = get_rate(rate_id)
    
    if 'rate' in data:
        rate.rate = data['rate']
    if 'rate_type_id' in data:
        rate.rate_type_id = data['rate_type_id']
    
    try:
        db.session.commit()
        return rate
    except IntegrityError:
        db.session.rollback()
        raise ValueError("Failed to update rate. Check if rate_type_id exists.")


def delete_rate(rate_id, user_id):
    check_is_super_admin(user_id)
    rate = get_rate(rate_id)
    
    db.session.delete(rate)
    db.session.commit()
    return {"message": f"Rate {rate_id} deleted successfully"}   