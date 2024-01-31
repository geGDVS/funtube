from flask import Flask
from flask import render_template
from flask import request
from flask import redirect
from replit import db
import secrets, os, shutil, time, requests, json

app = Flask(__name__)

def get_time():
    nowTime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    return nowTime

@app.route('/')
def index(name=""): 
    if request.cookies.get('login') == 'Y':
        name = request.cookies.get('name')
    return render_template('base-test.html', db = db['confirmed'].values(), login = request.cookies.get('login'), name = name)


@app.route('/msg')
def msg(): 
    if request.cookies.get('login') != 'Y':
        return render_template('error.html', msg="登录/注册")
    name = request.cookies.get('name')
    return render_template('msg.html', db=db['account'][name])


@app.route("/face-change", methods=['GET', 'POST'])
def change_face():
    if request.method == 'POST' and request.cookies.get('login') == 'Y':
        face = request.files['face']
        name = request.cookies.get('name')
        face.save(f'/home/runner/funtube/static/face/{name}/face.jpg')
        return redirect('/space')
    else:
        return render_template('page_not_found.html')

@app.route('/face')
def face(): 
    if request.cookies.get('login') != 'Y':
        return render_template('error.html', msg="登录/注册")
    name = request.cookies.get('name')
    return render_template('face.html', name=name)

@app.route('/login', methods=['GET', 'POST'])
def login(): 
    if request.method == 'POST':
        name = request.form['name']
        pswd = request.form['pswd']
        if name in db['account']:
            if db['account'][name]['pswd'] == pswd:
                resp = redirect('/')
                resp.set_cookie('name', name)
                resp.set_cookie('login', 'Y')
                return resp
            else:
                return render_template('error.html', msg='密码错误或用户名已存在！')
        else:
            db['account'][name] = {
                'name': name,
                'pswd': pswd,
                'comment': [f'欢迎{name}入驻Funtube!({get_time()})'],
            }
            os.makedirs(f'/home/runner/funtube/static/face/{name}')
            shutil.copy('/home/runner/funtube/static/face/face.png', f'/home/runner/funtube/static/face/{name}/face.jpg')
            resp = redirect('/')
            resp.set_cookie('name', name)
            resp.set_cookie('login', 'Y')
            return resp
    else:
        return render_template('error.html', msg='登录')

@app.route('/upload', methods=['GET', 'POST'])
def upload(): 
    if request.cookies.get('login') != 'Y':
        return render_template('page_not_found.html')
    if request.method == 'POST':
        title = request.form['title']
        author = request.cookies.get('name')
        music = request.files['music']
        note = request.form['note']
        pic = request.files['pic']
        word = request.files['word']
        id = secrets.token_urlsafe(6)
        os.makedirs(f'/home/runner/funtube/static/unconfirmed/{id}')
        type = music.filename.rsplit(".", 1)[1].lower()
        music.save(f'/home/runner/funtube/static/unconfirmed/{id}/music.{type}')
        db['unconfirmed'][id] = {
            'id': id,
            'title': title,
            'author': author,
            'status': 'unconfirmed',
            'note': note,
            'played': 0,
            'comment': [],
            'type': type
        }
        pic.save(f'/home/runner/funtube/static/unconfirmed/{id}/pic.jpg')
        word.save(f'/home/runner/funtube/static/unconfirmed/{id}/word.txt')
        return render_template('thanks.html')
    return render_template('upload.html')

@app.route("/music/<id>", methods=['GET', 'POST'])
def music(id):
    if request.method == 'POST':
        comment = request.form['comment']
        db['confirmed'][id]['comment'].insert(0, {
            'author': request.cookies.get('name'),
            'content': comment})
    for var in db['confirmed'].values():
        if var['id'] == id:
            var['played'] += 1
            return render_template('music.html', db = db['confirmed'][id], login = request.cookies.get('login'), name = request.cookies.get('name'))
    return render_template('page_not_found.html')

@app.route("/space", methods=['GET', 'POST'])
def space():
    if request.cookies.get('login') != 'Y':
        return render_template('error.html', msg="登录/注册")
    name = request.cookies.get('name')
    return render_template('space.html', db=db['account'][name])

@app.route("/delete-user", methods=['GET', 'POST'])
def delete_user():
    if request.cookies.get('login') != 'Y':
        return render_template('page_not_found.html')
    name = request.cookies.get('name')
    del db['account'][name]
    shutil.rmtree(f'/home/runner/funtube/static/face/{name}')
    resp = redirect('/')
    resp.set_cookie('login', 'N')
    return resp


@app.route("/logout", methods=['GET', 'POST'])
def logout():
    if request.cookies.get('login') != 'Y':
        return render_template('page_not_found.html')
    resp = redirect('/')
    resp.set_cookie('login', 'N')
    return resp

@app.route("/check-music/<id>")
def check_music(id):
    for var in db['unconfirmed'].values():
        if var['id'] == id:
            return render_template('check-music.html', db = db['unconfirmed'][id])
    for var in db['confirmed'].values():
        if var['id'] == id:
            return render_template('check-music.html', db = db['confirmed'][id])
    return render_template('page_not_found.html')

@app.route("/check", methods=['GET', 'POST'])
def check():
    if request.cookies.get('mod_login') == 'Y':
        return render_template('check.html', db = db['confirmed'].values(), undb = db['unconfirmed'].values())
    else:
        if request.cookies.get('login') == 'Y':
            if request.cookies.get('name') in ['Br·O·Ken']:
                resp = redirect('/check')
                resp.set_cookie('mod_login', 'Y')
                return resp
        if request.method == 'POST':
            if request.form['pswd'] == os.environ['check_pswd']:
                resp = redirect('/check')
                resp.set_cookie('mod_login', 'Y')
                return resp
        return render_template('pswd.html')

@app.route("/pass", methods=['GET', 'POST'])
def check_pass():
    if request.cookies.get('mod_login') == 'Y':
        if request.method == 'GET':
            id = request.args['id']
            for var in db['unconfirmed'].values():
                if var['id'] == id:
                    shutil.copytree(f'/home/runner/funtube/static/unconfirmed/{id}', f'/home/runner/funtube/static/confirmed/{id}')
                    shutil.rmtree(f'/home/runner/funtube/static/unconfirmed/{id}')
                    db['confirmed'][id] = db['unconfirmed'][id]
                    del db['unconfirmed'][id]
                    db['confirmed'][id]['status'] = 'confirmed'
                    if var['author'] in db['account']:
                        text = var['title']
                        db['account'][var['author']]['comment'].append(f'您的视频【{text}】已通过审核({get_time()})')
                    return render_template('operate.html')
            return render_template('page_not_found.html')
    else:
        if request.method == 'POST':
            if request.form['pswd'] == os.environ['check_pswd']:
                resp = redirect('/check')
                resp.set_cookie('mod_login', 'Y')
                return resp
        return render_template('pswd.html')

@app.route("/delete", methods=['GET', 'POST'])
def delete():
    if request.cookies.get('mod_login') == 'Y':
        if request.method == 'POST':
            id = request.form['id']
            reason = request.form['cause']
            for var in db['unconfirmed'].values():
                if var['id'] == id:
                    shutil.rmtree(f'/home/runner/funtube/static/unconfirmed/{id}')
                    if var['author'] in db['account']:
                        text = var['title']
                        db['account'][var['author']]['comment'].append(f'您的视频【{text}】未通过审核，原因：{reason}({get_time()})')
                    del db['unconfirmed'][id]
                    return render_template('operate.html')
            for var in db['confirmed'].values():
                if var['id'] == id:
                    shutil.rmtree(f'/home/runner/funtube/static/confirmed/{id}')
                    if var['author'] in db['account']:
                        text = var['title']
                        db['account'][var['author']]['comment'].append(f'您的视频【{text}】已被删除，原因：{reason}({get_time()})')
                    del db['confirmed'][id]
                    return render_template('operate.html')
            return render_template('page_not_found.html')
    else:
        if request.method == 'POST':
            if request.form['pswd'] == os.environ['check_pswd']:
                resp = redirect('/check')
                resp.set_cookie('mod_login', 'Y')
                return resp
        return render_template('pswd.html')

@app.errorhandler(404)
def page_not_found(error):
    return render_template('page_not_found.html'), 404
    
app.run(host='0.0.0.0', port=82)
