from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from utils.auth import role_required


def create_employee_blueprint(mysql):
    employee_bp = Blueprint("employee", __name__)

    @employee_bp.route("/attendance/self", methods=["GET"])
    @jwt_required()
    @role_required(["Employee"])
    def get_own_attendance():
        emp_id = get_jwt_identity()
        cur = mysql.connection.cursor()
        cur.execute(
            "SELECT date, status, time_in, time_out FROM attendance WHERE employee_id=%s",
            (emp_id,),
        )
        rows = cur.fetchall()

        # Convert to list of dicts and stringify any time fields
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

    @employee_bp.route("/attendance/self", methods=["POST"])
    @jwt_required()
    @role_required(["Employee"])
    def mark_own_attendance():
        emp_id = get_jwt_identity()
        print(emp_id)
        data = request.json
        cur = mysql.connection.cursor()
        cur.execute(
            """
            INSERT INTO attendance (employee_id, date, status, time_in)
            VALUES (%s, CURDATE(), %s, CURTIME())
            ON DUPLICATE KEY UPDATE status=%s, time_in=CURTIME()
        """,
            (emp_id, data["status"], data["status"]),
        )
        mysql.connection.commit()
        return jsonify({"msg": "Attendance marked"})

    return employee_bp
