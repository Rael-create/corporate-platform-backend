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