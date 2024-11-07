from flask import Flask, render_template, request, redirect, url_for
import psycopg2

app = Flask(__name__)

# URL de conexão com o banco de dados PostgreSQL
DATABASE_URL = "postgres://default:qKhdIMjs9xi3@ep-square-fog-a4qzqbtz.us-east-1.aws.neon.tech:5432/verceldb?sslmode=require"

# Função para obter a conexão com o banco de dados PostgreSQL
def get_db():
    try:
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    except Exception as e:
        print(f"Erro ao conectar ao banco de dados: {e}")
        return None

# Função para inicializar o banco de dados, caso ainda não exista
def init_db():
    conn = get_db()
    if conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS notepads (
                username TEXT PRIMARY KEY,
                content TEXT,
                password TEXT
            )
        """)
        conn.commit()
        cursor.close()
        conn.close()

# Página principal (formulário para criar bloco de notas)
@app.route('/')
def index():
    return render_template("index.html")

# Rota para criar um novo bloco de notas com o nome fornecido
@app.route('/create_note', methods=['GET'])
def create_note():
    notename = request.args.get('notename')
    password = request.args.get('password')

    if notename:
        conn = get_db()
        if conn:
            cursor = conn.cursor()

            # Verificar se o bloco de notas já existe
            cursor.execute('SELECT * FROM notepads WHERE username = %s', (notename,))
            if not cursor.fetchone():
                # Se o bloco de notas não existir, cria com conteúdo vazio e senha opcional
                cursor.execute('INSERT INTO notepads (username, content, password) VALUES (%s, %s, %s)', (notename, '', password))
                conn.commit()
            
            cursor.close()
            conn.close()

            return redirect(f'/note/{notename}')
    return "Erro ao criar o bloco de notas", 400

# Rota para acessar um bloco de notas específico
@app.route('/note/<notename>', methods=['GET', 'POST'])
def note(notename):
    conn = get_db()
    if conn:
        cursor = conn.cursor()
        
        # Verificar se o bloco de notas existe
        cursor.execute('SELECT content, password FROM notepads WHERE username = %s', (notename,))
        row = cursor.fetchone()
        
        if row:
            content = row[0]
            password = row[1]

            if request.method == 'POST':
                entered_password = request.form.get('password')
                if password == entered_password:
                    # Atualiza o conteúdo do bloco de notas
                    content = request.form['content']
                    cursor.execute('UPDATE notepads SET content = %s WHERE username = %s', (content, notename))
                    conn.commit()
                    return redirect(f'/note/{notename}')
                else:
                    return "Senha incorreta", 403

            cursor.close()
            conn.close()
            return render_template("note.html", notename=notename, content=content, password=password)
        else:
            cursor.close()
            conn.close()
            return "Bloco de notas não encontrado", 404
    return "Erro ao conectar ao banco de dados", 500

# Inicializar o banco de dados ao iniciar a aplicação
init_db()

# Iniciar o servidor
if __name__ == '__main__':
    app.run(debug=True)
