from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = "qujiguan_secret"  # 会话密钥，用于登录状态维持

# 初始化数据库（创建表+初始数据）
def init_db():
    conn = sqlite3.connect('qujiguan.db')
    c = conn.cursor()
    # 兴趣分类表
    c.execute('''CREATE TABLE IF NOT EXISTS hobby
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  title TEXT NOT NULL, 
                  desc TEXT NOT NULL)''')
    # 展览表
    c.execute('''CREATE TABLE IF NOT EXISTS exhibition
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  title TEXT NOT NULL, 
                  content TEXT NOT NULL, 
                  list TEXT NOT NULL, 
                  create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    # 管理员表（初始账号：admin 密码：123456）
    c.execute('''CREATE TABLE IF NOT EXISTS admin
                 (username TEXT PRIMARY KEY, 
                  password TEXT NOT NULL)''')
    # 插入初始数据（避免重复插入）
    c.execute("INSERT OR IGNORE INTO admin VALUES ('admin', '123456')")
    c.execute("INSERT OR IGNORE INTO hobby VALUES (1, '手账收藏', '记录生活的精致手账，涵盖复古、治愈等风格')")
    c.execute("INSERT OR IGNORE INTO hobby VALUES (2, '潮玩盲盒', '限量潮玩与盲盒收藏，包含IP联名款')")
    c.execute('''INSERT OR IGNORE INTO exhibition VALUES (1, '春日收藏展', '2025年春季主题收藏展，汇集全国爱好者藏品', '展览时间：2025-04-01至2025-04-15；展览地点：趣集馆线下展厅；参与方式：免费入场；咨询电话：12345678', ?)''', 
              (datetime.now(),))  # 用参数传递Python变量
    conn.commit()
    conn.close()

# 前端页面 - 首页
@app.route('/')
def index():
    conn = sqlite3.connect('qujiguan.db')
    c = conn.cursor()
    c.execute("SELECT * FROM hobby")
    hobbies = c.fetchall()
    c.execute("SELECT * FROM exhibition LIMIT 1")
    exhibition = c.fetchone() or (0, '暂无展览', '暂无展览信息', '暂无关键信息')
    conn.close()
    return render_template('index.html', hobbies=hobbies, exhibition=exhibition)

# 前端页面 - 兴趣分类页
@app.route('/hobby')
def hobby():
    conn = sqlite3.connect('qujiguan.db')
    c = conn.cursor()
    c.execute("SELECT * FROM hobby")
    hobbies = c.fetchall()
    conn.close()
    return render_template('hobby.html', hobbies=hobbies)

# 前端页面 - 展览详情页
@app.route('/exhibition')
def exhibition():
    conn = sqlite3.connect('qujiguan.db')
    c = conn.cursor()
    c.execute("SELECT * FROM exhibition ORDER BY create_time DESC")
    exhibitions = c.fetchall()
    conn.close()
    return render_template('exhibition.html', exhibitions=exhibitions)

# 管理员登录
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = sqlite3.connect('qujiguan.db')
        c = conn.cursor()
        c.execute("SELECT * FROM admin WHERE username=? AND password=?", (username, password))
        if c.fetchone():
            session['admin'] = username  # 登录成功，记录会话
            return redirect(url_for('admin_index'))
        else:
            return "账号或密码错误！<a href=' '>返回登录</a >"
    return render_template('admin/login.html')

# 管理员首页
@app.route('/admin')
def admin_index():
    if 'admin' not in session:
        return redirect(url_for('admin_login'))  # 未登录则跳转登录页
    return '''
        <h2>趣集馆后台管理</h2>
        <a href="/admin/hobby" style="display: block; margin: 10px 0;">兴趣分类管理</a >
        <a href="/admin/exhibition" style="display: block; margin: 10px 0;">展览管理</a >
        <a href="/admin/logout" style="display: block; margin: 10px 0;">退出登录</a >
    '''

# 兴趣分类管理（增删改）
@app.route('/admin/hobby', methods=['GET', 'POST'])
def hobby_manage():
    if 'admin' not in session:
        return redirect(url_for('admin_login'))
    
    conn = sqlite3.connect('qujiguan.db')
    c = conn.cursor()
    edit_id = request.args.get('edit_id')
    hobby = None
    
    # 编辑时获取当前兴趣数据
    if edit_id:
        c.execute("SELECT * FROM hobby WHERE id=?", (edit_id,))
        hobby = c.fetchone()
    
    # 新增/修改提交
    if request.method == 'POST':
        title = request.form['title']
        desc = request.form['desc']
        try:
            if edit_id:  # 修改
                c.execute("UPDATE hobby SET title=?, desc=? WHERE id=?", (title, desc, edit_id))
            else:  # 新增
                c.execute("INSERT INTO hobby (title, desc) VALUES (?, ?)", (title, desc))
            conn.commit()
            return redirect(url_for('hobby_manage'))  # 提交后刷新页面
        except Exception as e:
            return f"操作失败：{str(e)}<br><a href='/admin/hobby'>返回</a >"
    
    # 获取所有兴趣分类
    c.execute("SELECT * FROM hobby")
    hobbies = c.fetchall()
    conn.close()
    return render_template('admin/hobby_manage.html', hobbies=hobbies, hobby=hobby)

# 删除兴趣分类
@app.route('/admin/hobby/delete/<int:id>')
def hobby_delete(id):
    if 'admin' not in session:
        return redirect(url_for('admin_login'))
    
    try:
        conn = sqlite3.connect('qujiguan.db')
        c = conn.cursor()
        c.execute("DELETE FROM hobby WHERE id=?", (id,))
        conn.commit()
        conn.close()
    except Exception as e:
        return f"删除失败：{str(e)}<br><a href='/admin/hobby'>返回</a >"
    return redirect(url_for('hobby_manage'))

# 展览管理（增删改）
@app.route('/admin/exhibition', methods=['GET', 'POST'])
def exhibition_manage():
    if 'admin' not in session:
        return redirect(url_for('admin_login'))
    
    conn = sqlite3.connect('qujiguan.db')
    c = conn.cursor()
    edit_id = request.args.get('edit_id')
    edit_exhibition = None
    
    # 编辑时获取当前展览数据
    if edit_id:
        c.execute("SELECT * FROM exhibition WHERE id=?", (edit_id,))
        edit_exhibition = c.fetchone()
    
    # 新增/修改提交
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        list_str = request.form['list']
        try:
            if edit_id:  # 修改
                c.execute("UPDATE exhibition SET title=?, content=?, list=? WHERE id=?", (title, content, list_str, edit_id))
            else:  # 新增
                c.execute("INSERT INTO exhibition (title, content, list) VALUES (?, ?, ?)", (title, content, list_str))
            conn.commit()
            return redirect(url_for('exhibition_manage'))  # 提交后刷新页面
        except Exception as e:
            return f"操作失败：{str(e)}<br><a href='/admin/exhibition'>返回</a >"
    
    # 获取所有展览
    c.execute("SELECT * FROM exhibition ORDER BY create_time DESC")
    exhibitions = c.fetchall()
    conn.close()
    return render_template('admin/exhibition_manage.html', exhibitions=exhibitions, edit_id=edit_id, edit_exhibition=edit_exhibition)

# 删除展览
@app.route('/admin/exhibition/delete/<int:id>')
def exhibition_delete(id):
    if 'admin' not in session:
        return redirect(url_for('admin_login'))
    
    try:
        conn = sqlite3.connect('qujiguan.db')
        c = conn.cursor()
        c.execute("DELETE FROM exhibition WHERE id=?", (id,))
        conn.commit()
        conn.close()
    except Exception as e:
        return f"删除失败：{str(e)}<br><a href='/admin/exhibition'>返回</a >"
    return redirect(url_for('exhibition_manage'))

# 管理员退出登录
@app.route('/admin/logout')
def admin_logout():
    session.pop('admin', None) 
if __name__ == '__main__':
    init_db()
    app.run(debug=True)