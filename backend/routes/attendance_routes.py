from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from utils.auth import role_required
from datetime import datetime


def create_attendance_blueprint(mysql):
    attendance_bp = Blueprint("attendance", __name__)

    # ✅ GET all attendance — Admin & HR only
    @attendance_bp.route("/attendance", methods=["GET"])
    @jwt_required()
    @role_required(["Admin", "HR"])
    def get_all_attendance():
        cur = mysql.connection.cursor()
        cur.execute(
            """
            SELECT a.id, e.name, a.date, a.status, a.time_in, a.time_out
            FROM attendance a
            JOIN employees e ON a.employee_id = e.id
        """
        )
        rows = cur.fetchall()

        results = []
        for row in rows:
            results.append(
                {
                    "id": row[0],
                    "name": row[1],
                    "date": row[2].isoformat() if row[2] else None,
                    "status": row[3],
                    "time_in": str(row[4]) if row[4] else None,
                    "time_out": str(row[5]) if row[5] else None,
                }
            )

        return jsonify(results)

    # ✅ Manual mark attendance — Admin & HR
    @attendance_bp.route("/attendance", methods=["POST"])
    @jwt_required()
    @role_required(["Admin", "HR"])
    def mark_attendance_any():
        data = request.get_json()

        required_fields = ["employee_id", "date", "status"]
        if not all(field in data for field in required_fields):
            return jsonify({"msg": "Missing required fields"}), 400

        current_time = datetime.now().strftime("%H:%M:%S")

        cur = mysql.connection.cursor()
        cur.execute(
            """
            INSERT INTO attendance (employee_id, date, status, time_in)
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE status=%s, time_in=%s
        """,
            (
                data["employee_id"],
                data["date"],
                data["status"],
                current_time,
                data["status"],
                current_time,
            ),
        )
        mysql.connection.commit()
        return jsonify({"msg": "Attendance marked"}), 200

    # ✅ Admin: Get all users (ID, name, username, role)
    @attendance_bp.route("/users", methods=["GET"])
    @jwt_required()
    @role_required(["Admin", "HR"])
    def get_all_users():
        cur = mysql.connection.cursor()
        cur.execute(
            """
             SELECT e.id, e.name, u.username, u.role FROM users u JOIN employees e ON u.employee_id = e.id WHERE u.role = 'Employee'
        """
        )
        rows = cur.fetchall()

        users = []
        for row in rows:
            users.append(
                {"employee_id": row[0], "name": row[1], "username": row[2], "role": row[3]}
            )

        return jsonify(users)

    # ✅ Admin: Get attendance by user_id (pass via URL)
    @attendance_bp.route("/attendance/user/<int:user_id>", methods=["GET"])
    @jwt_required()
    @role_required(["Admin", "HR"])
    def get_attendance_by_user(user_id):
        cur = mysql.connection.cursor()

        # Get employee_id from user_id
        cur.execute("SELECT employee_id FROM users WHERE employee_id = %s", (user_id,))
        result = cur.fetchone()
        if not result:
            return jsonify({"msg": "User not found"}), 404

        emp_id = result[0]
        cur.execute(
            """
            SELECT date, status, time_in, time_out
            FROM attendance
            WHERE employee_id = %s
        """,
            (emp_id,),
        )
        rows = cur.fetchall()

        attendance = []
        for row in rows:
            attendance.append(
                {
                    "date": row[0].isoformat() if row[0] else None,
                    "status": row[1],
                    "time_in": str(row[2]) if row[2] else None,
                    "time_out": str(row[3]) if row[3] else None,
                }
            )

        return jsonify(attendance)

    # ✅ Auto-mark attendance — Used by model (only employee_id needed)
    @attendance_bp.route("/attendance/mark/<int:employee_id>", methods=["POST"])
    def mark_attendance_by_model(employee_id):
        data = request.get_json()
        status = data.get("status", "Present")  # Default to "Present" if not provided

        now = datetime.now()
        today = now.date()
        current_time = now.strftime("%H:%M:%S")

        cur = mysql.connection.cursor()
        cur.execute(
            """
            INSERT INTO attendance (employee_id, date, status, time_in)
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE status=%s, time_in=%s
        """,
            (employee_id, today, status, current_time, status, current_time),
        )
        mysql.connection.commit()

        return (
            jsonify(
                {
                    "msg": f"✅ Attendance marked for employee {employee_id} as '{status}'"
                }
            ),
            200,
        )

    return attendance_bp
