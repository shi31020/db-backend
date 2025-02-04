from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
# 配置数据库连接
username = 'root'
password = '123456'
host = 'localhost'
port = '3306'
database = 'school'
app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://{username}:{password}@{host}:{port}/{database}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# 数据库初始化
db = SQLAlchemy(app)


# student类型
class Student(db.Model):
    __table_name__ = 'student'

    student_id = db.Column(db.String(4), primary_key=True)  # 学生ID
    name = db.Column(db.String(3))  # 姓名
    sex = db.Column(db.String(1))  # 性别
    date_of_birth = db.Column(db.Date)  # 出生日期
    native_place = db.Column(db.String(2))  # 籍贯
    mobile_phone = db.Column(db.String(11))  # 手机号码
    dept_id = db.Column(db.String(2), db.ForeignKey('department.dept_id'))  # 外键关联部门

    # 显示学生信息的方式
    def __repr__(self):
        return f'<Student {self.name} ({self.student_id})>'


# 通过/api/students返回
@app.route('/api/students', methods=['GET'])
def get_students():
    students = Student.query.all()
    student_data = [{
        "student_id": student.student_id,
        "name": student.name,
        "sex": student.sex,
        "date_of_birth": student.date_of_birth.strftime('%Y-%m-%d'),
        "native_place": student.native_place,
        "mobile_phone": student.mobile_phone,
        "dept_id": student.dept_id
    } for student in students]
    return jsonify(student_data)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # 在首次启动时创建数据库表
    app.run(debug=True)
