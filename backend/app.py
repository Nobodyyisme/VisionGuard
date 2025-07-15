from flask import Flask
from flask_mysqldb import MySQL
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from config import Config
from routes.auth_routes import create_auth_blueprint
from routes.employee_routes import create_employee_blueprint
from routes.attendance_routes import create_attendance_blueprint

app = Flask(__name__)
app.config.from_object(Config)

mysql = MySQL(app)
jwt = JWTManager(app)
CORS(app)

app.register_blueprint(create_auth_blueprint(mysql), url_prefix="/auth")
app.register_blueprint(create_employee_blueprint(mysql), url_prefix="/employee")
app.register_blueprint(create_attendance_blueprint(mysql), url_prefix="/attendance")

if __name__ == '__main__':
    app.run(debug=True)
