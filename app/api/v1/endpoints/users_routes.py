from flask import Blueprint, request, jsonify

#from app.schemas.staff_schema import StaffCreationSchema
from app.schemas.users_schema import NewUserSchema, UserSchema
from app.services.users_service import create_user
#from app.services.staff_service import create_new_staff

users_bp = Blueprint(
    "users",
    __name__,
    url_prefix="/api/v1/users"
)


new_user_schema = NewUserSchema()
# staff_schema = StaffCreationSchema() 

@users_bp.route("/create", methods=["POST"])
def create_new_user():

    
    data = request.get_json()
    
    
    if not data:
        return jsonify({
            "message": "Request body is required."}), 400
        
    errors = new_user_schema.validate(data)
    
    if errors:
        return jsonify(errors), 400
    
    try:
        # creating new user using the service function
        
        new_user = create_user(data)
        # result = new_user_schema.dump(new_user)
        

        # result = new_user_schema.dump(new_user)
        return jsonify(new_user), 201
    
    except ValueError as e:
        return jsonify({"message": str(e)}), 400
    
    except Exception as e:
        return jsonify({
            "message": "Failed to create new user",
            "error": str(e)
        }), 500