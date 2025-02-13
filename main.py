from datetime import timedelta
from os import urandom
from flask_bcrypt import Bcrypt
from flask import Flask, jsonify, request, session,redirect, url_for
from flask_cors import CORS
from flask_session import Session
import mysql.connector

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
                "message": "用户名或密码错误"
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
    register_data = request.json
    print(register_data)
    return jsonify({
        "status": 200,
        "message": "注册成功",
    }), 200

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

