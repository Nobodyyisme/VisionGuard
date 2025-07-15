from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, get_jwt
import bcrypt
from utils.auth import role_required

def create_auth_blueprint(mysql):
    auth_bp = Blueprint('auth_bp', __name__)

    @auth_bp.route('/test', methods=['GET'])
    def test():
        return jsonify({"message": "✅ Auth service is working!"}), 200


    @auth_bp.route('/login', methods=['POST'])
    def login():
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')

        cur = mysql.connection.cursor()
        cur.execute("SELECT employee_id, username, password_hash, role FROM users WHERE username=%s", (username,))
        user = cur.fetchone()

        if user and bcrypt.checkpw(password.encode(), user[2].encode()):
            token = create_access_token(
                identity = str(user[0]),  # only user ID
                additional_claims={"role": user[3]}  # role is in claims
            )
            return jsonify({"token": token, "role": user[3]}), 200

        return jsonify({"msg": "Invalid credentials"}), 401

    @auth_bp.route('/register', methods=['POST'])
    @jwt_required()
    @role_required(['Admin', 'HR'])
    def register():
        data = request.get_json()
        if not data:
            return jsonify({"msg": "Missing JSON body"}), 400

        # Extract employee & login fields
        name = data.get('name')
        department = data.get('department')
        designation = data.get('designation')
        email = data.get('email')
        phone = data.get('phone')
        join_date = data.get('join_date')  # expect format: "YYYY-MM-DD"
        status = data.get('status')

        username = data.get('username')
        password = data.get('password')
        role = data.get('role')

        # Validate presence of all required fields
        required_fields = [name, department, designation, email, phone, join_date, status, username, password, role]
        if not all(required_fields):
            return jsonify({"msg": "All fields are required"}), 400

        # Check for duplicate username
        cur = mysql.connection.cursor()
        cur.execute("SELECT id FROM users WHERE username=%s", (username,))
        if cur.fetchone():
            return jsonify({"msg": "Username already exists"}), 409

        # Hash password
        hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

        # Insert into employees table
        cur.execute("""
            INSERT INTO employees (name, department, designation, email, phone, join_date, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (name, department, designation, email, phone, join_date, status))
        employee_id = cur.lastrowid

        # Insert into users table
        cur.execute("""
            INSERT INTO users (employee_id, username, password_hash, role)
            VALUES (%s, %s, %s, %s)
        """, (employee_id, username, hashed_password, role))

        mysql.connection.commit()

        return jsonify({"msg": f"User '{username}' registered successfully with role '{role}'."}), 201

    @auth_bp.route('/me', methods=['GET'])
    @jwt_required()
    def get_my_info():
        user_id = get_jwt_identity()

        cur = mysql.connection.cursor()
        cur.execute("""
            SELECT 
                e.name, e.department, e.designation, e.email, e.phone, e.join_date, e.status,
                u.username, u.role
            FROM users u
            JOIN employees e ON u.employee_id = e.id
            WHERE u.id = %s
        """, (user_id,))
        user = cur.fetchone()

        if not user:
            return jsonify({"msg": "User not found"}), 404

        return jsonify({
            "name": user[0],
            "department": user[1],
            "designation": user[2],
            "email": user[3],
            "phone": user[4],
            "join_date": user[5].isoformat() if user[5] else None,
            "status": user[6],
            "username": user[7],
            "role": user[8]
        }), 200


    return auth_bp
