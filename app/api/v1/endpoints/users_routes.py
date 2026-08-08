# app/api/v1/endpoints/users_routes.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

# ✅ Import models correctly - using your actual model names
from app.models.users import User
from app.models.staff import Staff
from app.models.corporate import Corporate
from app.schemas.users_schema import NewUserSchema
from app.services.users_service import create_user

users_bp = Blueprint(
    "users",
    __name__,
    url_prefix="/api/v1/users"
)

new_user_schema = NewUserSchema()

@users_bp.route("/create", methods=["POST"])
def create_new_user():
    data = request.get_json()
    
    if not data:
        return jsonify({"message": "Request body is required."}), 400
        
    errors = new_user_schema.validate(data)
    
    if errors:
        return jsonify(errors), 400
    
    try:
        new_user = create_user(data)
        return jsonify(new_user), 201
    
    except ValueError as e:
        return jsonify({"message": str(e)}), 400
    
    except Exception as e:
        return jsonify({
            "message": "Failed to create new user",
            "error": str(e)
        }), 500


# ✅ Get current authenticated user
@users_bp.route("/me", methods=["GET"])
@jwt_required()
def get_current_user():
    """
    Get the currently authenticated user with their staff and corporate data.
    """
    try:
        # Get the current user's ID from the JWT token
        current_user_id = get_jwt_identity()
        print(f"🔍 Fetching user with ID: {current_user_id}")
        
        # ✅ Fetch user from database using user_id
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({"message": "User not found"}), 404
        
        print(f"✅ User found: {user.username}")
        
        # ✅ Fetch staff data for this user
        staff = Staff.query.filter_by(user_id=user.user_id).first()
        print(f"👤 Staff found: {staff is not None}")
        
        # ✅ Fetch corporate data if staff exists
        corporate = None
        if staff:
            corporate = Corporate.query.get(staff.corporate_id)
            print(f"🏢 Corporate found: {corporate is not None}")
            if corporate:
                # ✅ FIX: Use corporate_name instead of name
                print(f"🏢 Corporate name: {corporate.corporate_name}")
        
        # Build user data response
        user_data = {
            "user_id": user.user_id,
            "username": user.username,
            "role": user.role,
            "created_at": user.created_at.isoformat() if user.created_at else None,
        }
        
        # Add staff data if it exists
        if staff:
            user_data["first_name"] = staff.first_name or ''
            user_data["last_name"] = staff.last_name or ''
            user_data["full_name"] = f"{staff.first_name or ''} {staff.last_name or ''}".strip()
            user_data["email"] = staff.email or None
            user_data["phone"] = staff.phone_number or None
            user_data["staff_id"] = staff.staff_id
            user_data["location"] = staff.location or None
            user_data["status"] = staff.status
            user_data["rides_used"] = staff.rides_used or 0
            user_data["rides_allowance"] = staff.rides_allocated or 20
            user_data["max_fare_per_ride"] = staff.max_fare_per_ride or 0
        else:
            # Default values if no staff data
            user_data["first_name"] = ''
            user_data["last_name"] = ''
            user_data["full_name"] = user.username
            user_data["email"] = None
            user_data["phone"] = None
            user_data["rides_used"] = 0
            user_data["rides_allowance"] = 20
            user_data["max_fare_per_ride"] = 0
        
        # ✅ Add corporate data - FIXED: use corporate_name
        if corporate:
            user_data["company"] = corporate.corporate_name  # ✅ Use corporate_name
            user_data["corporate_id"] = corporate.corporate_id
        else:
            user_data["company"] = 'Corporate Rides'  # Fallback
        
        print(f"✅ Returning user data with company: {user_data.get('company')}")
        return jsonify(user_data), 200
        
    except Exception as e:
        print(f"❌ Error fetching current user: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "message": "Failed to fetch user data",
            "error": str(e)
        }), 500


# Get user by ID (for admin purposes)
@users_bp.route("/<int:user_id>", methods=["GET"])
@jwt_required()
def get_user(user_id):
    """
    Get a specific user by ID (admin only).
    """
    try:
        # Check if current user is admin/super admin
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        
        if current_user.role not in ['SUPER_ADMIN', 'CORPORATE_ADMIN']:
            return jsonify({"message": "Unauthorized"}), 403
        
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({"message": "User not found"}), 404
        
        staff = Staff.query.filter_by(user_id=user.user_id).first()
        corporate = None
        if staff:
            corporate = Corporate.query.get(staff.corporate_id)
        
        user_data = {
            "user_id": user.user_id,
            "username": user.username,
            "role": user.role,
            "created_at": user.created_at.isoformat() if user.created_at else None,
        }
        
        if staff:
            user_data["first_name"] = staff.first_name
            user_data["last_name"] = staff.last_name
            user_data["full_name"] = f"{staff.first_name} {staff.last_name}".strip()
            user_data["email"] = staff.email
            user_data["phone"] = staff.phone_number
            user_data["rides_used"] = staff.rides_used or 0
            user_data["rides_allowance"] = staff.rides_allocated or 20
            user_data["max_fare_per_ride"] = staff.max_fare_per_ride or 0
        
        if corporate:
            user_data["company"] = corporate.corporate_name  # ✅ Use corporate_name
        
        return jsonify(user_data), 200
        
    except Exception as e:
        return jsonify({
            "message": "Failed to fetch user",
            "error": str(e)
        }), 500