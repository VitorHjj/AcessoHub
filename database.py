import sqlite3

BANCO = 'acesso.db'


def conectar():
    conexao = sqlite3.connect(BANCO)
    conexao.execute('PRAGMA foreign_keys = ON')
    return conexao


def criar_tabela():
    with conectar() as conexao:
        conexao.execute('''CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            expiracao TEXT NOT NULL,
            email TEXT,
            cpf TEXT,
            telefone TEXT,
            nascimento TEXT
        )''')
        colunas = {linha[1] for linha in conexao.execute('PRAGMA table_info(usuarios)')}
        for coluna in ('email', 'cpf', 'telefone', 'nascimento'):
            if coluna not in colunas:
                conexao.execute(f'ALTER TABLE usuarios ADD COLUMN {coluna} TEXT')
        if 'suspenso' not in colunas:
            conexao.execute('ALTER TABLE usuarios ADD COLUMN suspenso INTEGER NOT NULL DEFAULT 0')
        conexao.execute('''CREATE TABLE IF NOT EXISTS pagamentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            data TEXT NOT NULL,
            valor REAL NOT NULL,
            dias INTEGER NOT NULL,
            validade_anterior TEXT,
            validade_nova TEXT NOT NULL,
            FOREIGN KEY(usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
        )''')
        conexao.execute('''CREATE TABLE IF NOT EXISTS acessos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            data_hora TEXT NOT NULL,
            permitido INTEGER NOT NULL,
            motivo TEXT NOT NULL,
            FOREIGN KEY(usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
        )''')
        if 'plano' not in colunas:
            conexao.execute('ALTER TABLE usuarios ADD COLUMN plano TEXT')
        pagamentos_colunas = {linha[1] for linha in conexao.execute('PRAGMA table_info(pagamentos)')}
        if 'plano' not in pagamentos_colunas:
            conexao.execute('ALTER TABLE pagamentos ADD COLUMN plano TEXT')
        if 'meses' not in pagamentos_colunas:
            conexao.execute('ALTER TABLE pagamentos ADD COLUMN meses INTEGER')
        # Dados antigos podem conter CPFs repetidos; não interrompemos a migração.
        repetidos = conexao.execute('''SELECT 1 FROM usuarios
            WHERE cpf IS NOT NULL AND cpf != ''
            GROUP BY cpf HAVING COUNT(*) > 1 LIMIT 1''').fetchone()
        if not repetidos:
            conexao.execute('''CREATE UNIQUE INDEX IF NOT EXISTS idx_usuarios_cpf
                ON usuarios(cpf) WHERE cpf IS NOT NULL AND cpf != '' ''')
