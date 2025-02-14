import json
from datetime import timedelta
from os import urandom

import mysql.connector
from flask import Flask, jsonify, request, session
from flask_bcrypt import Bcrypt
from flask_cors import CORS
from mysql.connector import Error

from flask_session import Session

app = Flask(__name__)
CORS(app,supports_credentials=True)
# 配置数据库连接
def get_db_connection():
    return mysql.connector.connect(
        host='47.116.161.132',
        user='test',
        password='123456',
        database='school',
        port=3306
    )


# 配置 Session 存储
def session_startup():
    app.config["SESSION_TYPE"] = "filesystem"  # 存储在服务器文件系统
    app.config["SESSION_PERMANENT"] = False  # 关闭浏览器后 Session 失效
    app.config["SESSION_USE_SIGNER"] = True  # 防止篡改
    app.config["SECRET_KEY"] = urandom(24)  # 用于加密 Session
    app.permanent_session_lifetime = timedelta(days=3)  # 设置 cookies 存活3天
    Session(app)
session_startup()
# 启动bcrypt
bcrypt = Bcrypt(app)


@app.route('/api/login/account', methods=['POST'])
def login_data():
    data = request.json
    user_id = data.get('id')
    password = data.get('password')
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        # 查询用户信息
        query = "SELECT * FROM Login WHERE id = %s"
        cursor.execute(query, (user_id,))

        # 获取查询结果
        user = cursor.fetchone()  # 获取单个用户记录

        if not user:
            # 如果用户不存在，返回 404 错误
            return jsonify({
                "success": False,
                "message": "用户不存在"
            }), 404

        # 获取密码和权限
        db_password = user[1]  # 假设密码是第二个字段
        access = user[2]  # 假设权限是第三个字段

        if bcrypt.check_password_hash(db_password, password):
            # 登录成功，设置 session
            session['user_id'] = user_id
            session['access'] = access
            session.permanent = True  # 设置持久会话
            return jsonify({
                "success": True,
                "message": "登录成功",
                "data": {
                    "id": user_id,
                    "access": access
                }
            })
        else:
            # 如果密码错误
            return jsonify({
                "success": False,
                "message": "密码错误"
            }), 401
    finally:
        # 确保关闭数据库连接
        cursor.close()
        connection.close()

@app.route('/api/login/outLogin', methods=['POST'])
def logout():
    session.clear()
    return jsonify({"success": True, "message": "已成功退出登录"}), 200


@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    print(data)

    # 获取身份标记
    role = 'student' if data['identity'] == 'student' else 'teacher'
    department_name = data['department']
    # 连接到数据库
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT DID FROM Department WHERE Dname = %s", (department_name,))
    DID = cursor.fetchone()
    DID = DID['DID']

    access = []
    if data['isAdmin']:
        access.append('admin')
    if role == 'student':
        # 学生注册逻辑
        access.append('student')
        cursor.execute("SELECT * FROM Student WHERE SNO = %s", (data['studentId'],))
        existing_student = cursor.fetchone()
        if existing_student:
            cursor.close()
            conn.close()
            return jsonify({'status': 400, 'message': '该学生ID已被注册'}), 400

        # 插入学生信息
        cursor.execute(
            "INSERT INTO Student (SNO, SName, Gender, Department, GPA, Admission,Major) VALUES (%s, %s, %s, %s, %s, %s,%s)",
            (data['studentId'], data['name'], data['gender'], DID, data['GPA'], data['enrollmentYear'],data['major'])
        )
        # 插入 Login 表
        cursor.execute(
            "INSERT INTO Login (id, password, access) VALUES (%s, %s, %s)",
            (data['studentId'], bcrypt.generate_password_hash(data['password']).decode('utf-8'),
             json.dumps(access))
        )

    elif role == 'teacher':
        # 教师注册逻辑
        access.append('teacher')
        cursor.execute("SELECT * FROM Teacher WHERE TID = %s", (data['teacherId'],))
        existing_teacher = cursor.fetchone()
        if existing_teacher:
            cursor.close()
            conn.close()
            return jsonify({'status': 400, 'message': '该教师ID已被注册'}), 400

        # 插入教师信息
        cursor.execute(
            "INSERT INTO Teacher (TID, TName, Gender, Department, Title) VALUES (%s, %s, %s, %s, %s)",
            (data['teacherId'], data['name'], data['gender'], DID, data['title'])
        )

        # 插入 Login 表
        cursor.execute(
            "INSERT INTO Login (id, password, access) VALUES (%s, %s, %s)",
            (data['teacherId'], bcrypt.generate_password_hash(data['password']).decode('utf-8'),
             json.dumps(access))
        )

    # 提交事务
    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({'status': 200, 'message': '注册成功'}), 200


def query_classes(CID=None, TID=None, TimeSlot=None, Capacity=None):
    query = """
            SELECT CID, TID, TimeSlot, Capacity FROM ClassView 
            WHERE (%s IS NULL OR CID = %s) 
              AND (%s IS NULL OR TID = %s) 
              AND (%s IS NULL OR TimeSlot = %s) 
              AND (%s IS NULL OR Capacity = %s)
        """
    params = [CID, CID, TID, TID, TimeSlot, TimeSlot, Capacity, Capacity]


    try:
        # 连接数据库并执行查询
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute(query, params)
        results = cursor.fetchall()
        cursor.close()
        connection.close()
        return results

    except Error as e:
        # 捕获数据库连接或执行错误
        print(f"Database error: {e}")
        return None
@app.route('/api/query_classes', methods=['POST'])
def query_classes_api():
    try:
        # 获取 JSON 请求体
        data = request.get_json()

        # 获取查询参数
        CID = data.get('CID')
        TID = data.get('TID')
        TimeSlot = data.get('TimeSlot')
        Capacity = data.get('Capacity')

        # 调用查询函数
        results = query_classes(CID, TID, TimeSlot, Capacity)

        # 如果查询失败，返回 500 错误
        if results is None:
            return jsonify({"error": "数据库查询失败"}), 500

        # 返回查询结果
        return jsonify(results)

    except Exception as e:
        # 捕获其他异常
        print(f"Error: {e}")
        return jsonify({"error": "请求处理失败"}), 400

@app.route('/api/departments', methods=['GET'])
def get_departments():
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        # 查询所有院系
        query = "SELECT * FROM Department"
        cursor.execute(query)

        # 获取所有院系名称
        departments = cursor.fetchall()

        if not departments:
            return jsonify({
                "success": False,
                "message": "没有找到院系"
            }), 404

        department_names = [department[1] for department in departments]  # 提取院系名称

        return jsonify({
            'success': True,
            'data': department_names
        })
    except Exception as e:
        print(f"获取院系列表失败: {e}")
        return jsonify({
            'success': False,
            'data': []
        })
    finally:
        cursor.close()
        connection.close()



if __name__ == '__main__':
    app.run(debug=True)

