from functools import wraps
from flask import jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt

def role_required(*allowed_roles):
    """
    Decorator to restrict access to specific roles.
    Usage: @role_required("SUPER_ADMIN", "CORPORATE_ADMIN")
    """
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            # 1. Verify the token is valid (already done by @jwt_required, but safe to check)
            verify_jwt_in_request()
            
            # 2. Extract the 'role' from the token payload
            claims = get_jwt()
            user_role = claims.get("role")

            print(f"DEBUG: Token Role is '{user_role}' | Allowed Roles are {allowed_roles}")

            
            # 3. Check if the user's role is allowed
            if user_role in allowed_roles:
                return fn(*args, **kwargs)
            else:
                return jsonify({"message": "Forbidden: You do not have permission to access this resource"}), 403
                
        return decorator
    return wrapper