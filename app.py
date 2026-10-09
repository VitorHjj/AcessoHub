import os
import secrets
import sqlite3
from datetime import date, datetime, timedelta
from calendar import monthrange
from functools import wraps
from pathlib import Path
from flask import Flask, render_template, request, redirect, url_for, session, flash, abort
from werkzeug.security import generate_password_hash, check_password_hash
from database import criar_tabela, conectar

BASE = Path(__file__).resolve().parent
os.chdir(BASE)
app = Flask(__name__)
secret_path = BASE / '.session_key'
if not secret_path.exists():
    secret_path.write_text(secrets.token_hex(32))
    secret_path.chmod(0o600)
app.secret_key = os.environ.get('SECRET_KEY') or secret_path.read_text().strip()

# Preços fictícios para demonstração; altere aqui para definir seus pacotes.
PLANOS = {
    'mensal': {'nome': 'Mensal', 'meses': 1, 'centavos': 10000},
    'trimestral': {'nome': 'Trimestral', 'meses': 3, 'centavos': 27000},
    'semestral': {'nome': 'Semestral', 'meses': 6, 'centavos': 51000},
    'anual': {'nome': 'Anual', 'meses': 12, 'centavos': 96000},
}


def somar_meses(data, meses):
    indice = data.year * 12 + data.month - 1 + meses
    ano, mes = divmod(indice, 12)
    mes += 1
    return date(ano, mes, min(data.day, monthrange(ano, mes)[1]))


def escolher_plano(form):
    chave = form.get('plano', '')
    if chave not in PLANOS:
        raise ValueError('Selecione um plano válido.')
    return chave, PLANOS[chave]


def registrar_plano(db, uid, chave, plano, anterior, base):
    validade = somar_meses(base, plano['meses'])
    db.execute('UPDATE usuarios SET expiracao=?, plano=? WHERE id=?', (validade.isoformat(), chave, uid))
    db.execute('INSERT INTO pagamentos (usuario_id,data,valor,dias,validade_anterior,validade_nova,plano,meses) VALUES (?,?,?,?,?,?,?,?)',
               (uid, datetime.now().isoformat(timespec='seconds'), plano['centavos']/100,
                (validade-base).days, anterior.isoformat(), validade.isoformat(), plano['nome'], plano['meses']))
    return validade
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE='Lax')
if os.environ.get('COOKIE_SECURE') == '1':
    app.config['SESSION_COOKIE_SECURE'] = True


def init_db():
    criar_tabela()
    with conectar() as db:
        db.execute('CREATE TABLE IF NOT EXISTS administradores (id INTEGER PRIMARY KEY, usuario TEXT UNIQUE NOT NULL, senha_hash TEXT NOT NULL)')


def rows(sql, args=()):
    with conectar() as db:
        db.row_factory = sqlite3.Row
        return [dict(r) for r in db.execute(sql, args).fetchall()]


def one(sql, args=()):
    result = rows(sql, args)
    return result[0] if result else None


def logged_in(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get('admin_id'):
            return redirect(url_for('login'))
        return fn(*args, **kwargs)
    return wrapper


@app.before_request
def protect():
    if request.method == 'POST':
        if not session.get('csrf') or request.form.get('csrf') != session['csrf']:
            abort(400, 'Token de segurança inválido. Atualize a página.')


@app.context_processor
def context():
    if 'csrf' not in session:
        session['csrf'] = secrets.token_hex(24)
    return {'csrf': session['csrf'], 'hoje': date.today().isoformat(), 'planos': PLANOS}


def digits(value):
    return ''.join(c for c in str(value or '') if c.isdigit())


def cpf_ok(cpf):
    if len(cpf) != 11 or cpf == cpf[0] * 11:
        return False
    for size in (9, 10):
        check = sum(int(cpf[i]) * (size + 1 - i) for i in range(size)) * 10 % 11
        if (0 if check == 10 else check) != int(cpf[size]):
            return False
    return True


def validate(form):
    nome = form.get('nome', '').strip()
    email = form.get('email', '').strip().lower()
    cpf = digits(form.get('cpf'))
    telefone = digits(form.get('telefone'))
    nascimento = form.get('nascimento', '').strip()
    if len(nome) < 2 or len(nome) > 120:
        raise ValueError('Informe um nome válido (2 a 120 caracteres).')
    if '@' not in email or '.' not in email.split('@')[-1] or len(email) > 200:
        raise ValueError('Informe um e-mail válido.')
    if not cpf_ok(cpf):
        raise ValueError('CPF inválido.')
    if len(telefone) not in (10, 11):
        raise ValueError('Telefone deve ter 10 ou 11 dígitos.')
    try:
        nasc = date.fromisoformat(nascimento)
        if nasc > date.today() or nasc.year < 1900:
            raise ValueError()
    except ValueError:
        raise ValueError('Data de nascimento inválida.')
    return nome, email, cpf, telefone, nascimento


def get_user(uid):
    user = one('SELECT * FROM usuarios WHERE id=?', (uid,))
    if not user:
        abort(404)
    return user


def status(user):
    if user['suspenso']:
        return 'Suspenso'
    return 'Ativo' if user['expiracao'] >= date.today().isoformat() else 'Vencido'


app.jinja_env.globals['status_usuario'] = status


@app.route('/configurar', methods=['GET', 'POST'])
def setup():
    if one('SELECT id FROM administradores LIMIT 1'):
        return redirect(url_for('dashboard' if session.get('admin_id') else 'login'))
    if request.method == 'POST':
        username = request.form.get('usuario', '').strip()
        password = request.form.get('senha', '')
        if len(username) < 3 or len(password) < 10:
            flash('Usuário mínimo 3 caracteres e senha mínima 10 caracteres.', 'error')
        else:
            try:
                with conectar() as db:
                    cursor = db.execute('INSERT INTO administradores (usuario, senha_hash) VALUES (?,?)', (username, generate_password_hash(password)))
                    admin_id = cursor.lastrowid
                session.clear()
                session.update(admin_id=admin_id, admin_name=username, csrf=secrets.token_hex(24))
                flash('Administrador criado.', 'success')
                return redirect(url_for('dashboard'))
            except sqlite3.IntegrityError:
                flash('Administrador já configurado.', 'error')
    return render_template('auth.html', setup=True, title='Configuração inicial')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if not one('SELECT id FROM administradores LIMIT 1'):
        return redirect(url_for('setup'))
    if request.method == 'POST':
        admin = one('SELECT * FROM administradores WHERE usuario=?', (request.form.get('usuario', '').strip(),))
        if admin and check_password_hash(admin['senha_hash'], request.form.get('senha', '')):
            session.clear()
            session['admin_id'] = admin['id']
            session['admin_name'] = admin['usuario']
            session['csrf'] = secrets.token_hex(24)
            return redirect(url_for('dashboard'))
        flash('Usuário ou senha incorretos.', 'error')
    return render_template('auth.html', setup=False, title='Entrar')


@app.post('/sair')
@logged_in
def logout():
    session.clear()
    return redirect(url_for('login'))


@app.route('/')
@logged_in
def dashboard():
    users = rows('SELECT * FROM usuarios ORDER BY id DESC')
    active = sum(status(u) == 'Ativo' for u in users)
    expired = sum(status(u) == 'Vencido' for u in users)
    suspended = sum(status(u) == 'Suspenso' for u in users)
    revenue = one('SELECT COALESCE(SUM(valor),0) AS total FROM pagamentos')['total']
    latest = rows('''SELECT p.*, u.nome FROM pagamentos p JOIN usuarios u ON u.id=p.usuario_id ORDER BY p.id DESC LIMIT 6''')
    return render_template('dashboard.html', title='Dashboard', total=len(users), active=active, expired=expired, suspended=suspended, revenue=revenue, latest=latest, recent=users[:6])


@app.route('/usuarios')
@logged_in
def users():
    q = request.args.get('q', '').strip()
    filtro = request.args.get('status', '')
    data = rows('SELECT * FROM usuarios WHERE nome LIKE ? OR cpf LIKE ? OR CAST(id AS TEXT)=? ORDER BY id DESC', (f'%{q}%', f'%{digits(q)}%' if digits(q) else '##no-match##', q)) if q else rows('SELECT * FROM usuarios ORDER BY id DESC')
    if filtro in ('Ativo', 'Vencido', 'Suspenso'):
        data = [u for u in data if status(u) == filtro]
    return render_template('users.html', title='Usuários', users=data, q=q, filtro=filtro)


@app.route('/usuarios/novo', methods=['GET', 'POST'])
@logged_in
def new_user():
    if request.method == 'POST':
        try:
            values = validate(request.form)
            chave, plano = escolher_plano(request.form)
            with conectar() as db:
                cursor = db.execute('INSERT INTO usuarios (nome,email,cpf,telefone,nascimento,expiracao,suspenso) VALUES (?,?,?,?,?,?,0)', (*values, date.today().isoformat()))
                registrar_plano(db, cursor.lastrowid, chave, plano, date.today(), date.today())
            flash('Usuário cadastrado com o plano selecionado.', 'success')
            return redirect(url_for('users'))
        except (ValueError, sqlite3.IntegrityError) as ex:
            flash('CPF já cadastrado.' if isinstance(ex, sqlite3.IntegrityError) else str(ex), 'error')
    return render_template('user_form.html', title='Novo usuário', user=None)


@app.route('/usuarios/<int:uid>/editar', methods=['GET', 'POST'])
@logged_in
def edit_user(uid):
    user = get_user(uid)
    if request.method == 'POST':
        try:
            values = validate(request.form)
            with conectar() as db:
                db.execute('UPDATE usuarios SET nome=?,email=?,cpf=?,telefone=?,nascimento=? WHERE id=?', (*values, uid))
            flash('Cadastro atualizado.', 'success')
            return redirect(url_for('users'))
        except (ValueError, sqlite3.IntegrityError) as ex:
            flash('CPF já cadastrado.' if isinstance(ex, sqlite3.IntegrityError) else str(ex), 'error')
    return render_template('user_form.html', title='Editar usuário', user=user)


@app.post('/usuarios/<int:uid>/excluir')
@logged_in
def delete_user(uid):
    get_user(uid)
    with conectar() as db:
        db.execute('DELETE FROM usuarios WHERE id=?', (uid,))
    flash('Usuário e seus históricos excluídos.', 'success')
    return redirect(url_for('users'))


@app.post('/usuarios/<int:uid>/suspender')
@logged_in
def suspend_user(uid):
    user = get_user(uid)
    with conectar() as db:
        db.execute('UPDATE usuarios SET suspenso=? WHERE id=?', (0 if user['suspenso'] else 1, uid))
    flash('Situação do usuário atualizada.', 'success')
    return redirect(request.referrer if request.referrer and request.referrer.startswith(request.host_url) else url_for('users'))


@app.post('/usuarios/<int:uid>/acesso')
@logged_in
def access_user(uid):
    user = get_user(uid)
    allowed = status(user) == 'Ativo'
    reason = 'Acesso permitido' if allowed else ('Usuário suspenso' if user['suspenso'] else 'Mensalidade vencida')
    with conectar() as db:
        db.execute('INSERT INTO acessos (usuario_id,data_hora,permitido,motivo) VALUES (?,?,?,?)', (uid, datetime.now().isoformat(timespec='seconds'), int(allowed), reason))
    flash(f'{user["nome"]}: {reason}.', 'success' if allowed else 'error')
    return redirect(url_for('users'))


@app.post('/usuarios/<int:uid>/renovar')
@logged_in
def renew(uid):
    user = get_user(uid)
    try:
        chave, plano = escolher_plano(request.form)
    except ValueError as ex:
        flash(str(ex), 'error')
        return redirect(url_for('users'))
    current = date.fromisoformat(user['expiracao'])
    base = max(date.today(), current)
    with conectar() as db:
        new_exp = registrar_plano(db, uid, chave, plano, current, base)
    flash(f'Plano {plano["nome"]} renovado até {new_exp.strftime("%d/%m/%Y")}.', 'success')
    return redirect(url_for('users'))


@app.route('/mensalidades')
@logged_in
def payments():
    data = rows('SELECT p.*,u.nome FROM pagamentos p JOIN usuarios u ON u.id=p.usuario_id ORDER BY p.id DESC')
    return render_template('payments.html', title='Mensalidades', payments=data)


@app.route('/acessos')
@logged_in
def accesses():
    data = rows('SELECT a.*,u.nome FROM acessos a JOIN usuarios u ON u.id=a.usuario_id ORDER BY a.id DESC LIMIT 500')
    return render_template('accesses.html', title='Histórico de acessos', accesses=data)


@app.route('/relatorios')
@logged_in
def reports():
    users_data = rows('SELECT * FROM usuarios ORDER BY nome')
    monthly = rows("SELECT substr(data,1,7) mes, COUNT(*) quantidade, SUM(valor) total FROM pagamentos GROUP BY substr(data,1,7) ORDER BY mes DESC LIMIT 12")
    return render_template('reports.html', title='Relatórios', users=users_data, monthly=monthly, active=sum(status(u) == 'Ativo' for u in users_data), expired=sum(status(u) == 'Vencido' for u in users_data), suspended=sum(status(u) == 'Suspenso' for u in users_data))


init_db()
if __name__ == '__main__':
    app.run(debug=False, host='127.0.0.1', port=5000)
