from flask import Flask, render_template, request, redirect, url_for
from flask_mysqldb import MySQL
import MySQLdb.cursors
import config

app = Flask(__name__)

# Configuração do MySQL
app.config['MYSQL_HOST'] = config.MYSQL_HOST
app.config['MYSQL_USER'] = config.MYSQL_USER
app.config['MYSQL_PASSWORD'] = config.MYSQL_PASSWORD
app.config['MYSQL_DB'] = config.MYSQL_DB
app.config['MYSQL_CURSORCLASS'] = config.MYSQL_CURSORCLASS

mysql = MySQL(app)

# Página inicial (listar todas as máquinas)
@app.route('/')
def index():
    search = request.args.get('search', '')
    status_filter = request.args.get('status', '')
    setor_filter = request.args.get('setor', '')

    cur = mysql.connection.cursor()

    query = "SELECT * FROM maquinas WHERE 1=1"
    params = []

    if search:
        query += " AND patrimonio LIKE %s"
        params.append(f"%{search}%")
    if status_filter:
        query += " AND status = %s"
        params.append(status_filter)
    if setor_filter:
        query += " AND setor = %s"
        params.append(setor_filter)

    cur.execute(query, params)
    maquinas = cur.fetchall()

    # Lista de setores para o filtro
    cur.execute("SELECT DISTINCT setor FROM maquinas")
    setores = [row['setor'] for row in cur.fetchall()]

    cur.close()

    return render_template(
        'index.html',
        maquinas=maquinas,
        search=search,
        status_filter=status_filter,
        setor_filter=setor_filter,
        setores=setores
    )

# Página de status
@app.route('/status')
def status():
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT patrimonio, tipo, status, setor FROM maquinas")
    rows = cur.fetchall()

    # ----------- Agrupamento por Categoria (como já tem) -----------
    status_data = {}
    for row in rows:
        tipo = row['tipo']
        status_eq = row['status']
        setor = row['setor']

        if tipo.startswith('maquina_'):
            if tipo not in status_data:
                status_data[tipo] = {
                    'entregues': 0,
                    'pendentes': 0,
                    'setores': set()
                }
            if status_eq == 'entregue':
                status_data[tipo]['entregues'] += 1
            else:
                status_data[tipo]['pendentes'] += 1
            if setor:
                status_data[tipo]['setores'].add(setor)

        elif tipo.startswith('tela_') or tipo.startswith('notebook_'):
            if tipo not in status_data:
                status_data[tipo] = {
                    'entregues': 0,
                    'pendentes': 0,
                    'setores': set()
                }
            if status_eq == 'entregue':
                status_data[tipo]['entregues'] += 1
            else:
                status_data[tipo]['pendentes'] += 1
            if setor:
                status_data[tipo]['setores'].add(setor)

    for tipo in status_data:
        status_data[tipo]['setores'] = sorted(list(status_data[tipo]['setores']))

    # ----------- Agrupamento por Setor (com lista de itens) -----------
    status_setor_data = {}
    for row in rows:
        setor = row['setor'] or "Não informado"
        status_eq = row['status']
        patrimonio = row['patrimonio']
        tipo = row['tipo']

        if setor not in status_setor_data:
            status_setor_data[setor] = {
                'entregues': 0,
                'pendentes': 0,
                'itens_entregues': [],
                'itens_pendentes': []
            }

        if status_eq == 'entregue':
            status_setor_data[setor]['entregues'] += 1
            status_setor_data[setor]['itens_entregues'].append(f"{patrimonio} ({tipo})")
        else:
            status_setor_data[setor]['pendentes'] += 1
            status_setor_data[setor]['itens_pendentes'].append(f"{patrimonio} ({tipo})")

    cur.close()

    # Valores de referência (você pode depois puxar isso de outra tabela)
    valores_por_tipo = {
        'maquina_tipo_1': 5900,
        'maquina_tipo_2': 6600,
        'maquina_tipo_3': 22890,
        'tela_tipo_1': 700,
        'tela_tipo_2': 1480,
        'notebook_tipo_1': 6250,
        'notebook_tipo_2': 7700
    }

    # Total do projeto
    valor_total_projeto = 1500000

    # Calcular valor já entregue
    valor_entregue = 0
    for row in rows:
        tipo = row['tipo']
        status_eq = row['status']
        if status_eq == 'entregue' and tipo in valores_por_tipo:
            valor_entregue += valores_por_tipo[tipo]

    # Porcentagem financeira
    percentual_financeiro = round((valor_entregue / valor_total_projeto) * 100, 2)

    return render_template(
        'status.html',
        status_data=status_data,
        status_setor_data=status_setor_data,
        valor_total_projeto=valor_total_projeto,
        valor_entregue=valor_entregue,
        percentual_financeiro=percentual_financeiro
    )


# Adicionar máquina
@app.route('/add', methods=['GET', 'POST'])
def add():
    if request.method == 'POST':
        patrimonio = request.form['patrimonio']
        tipo = request.form['tipo']
        setor = request.form['setor']
        status = request.form['status']

        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO maquinas (patrimonio, tipo, setor, status) VALUES (%s, %s, %s, %s)",
                    (patrimonio, tipo, setor, status))
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('index'))
    return render_template('add.html')

# Editar máquina
@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit(id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM maquinas WHERE id=%s", (id,))
    maquina = cur.fetchone()
    cur.close()

    if request.method == 'POST':
        patrimonio = request.form['patrimonio']
        tipo = request.form['tipo']
        setor = request.form['setor']
        status = request.form['status']

        cur = mysql.connection.cursor()
        cur.execute("""
            UPDATE maquinas
            SET patrimonio=%s, tipo=%s, setor=%s, status=%s
            WHERE id=%s
        """, (patrimonio, tipo, setor, status, id))
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('index'))

    return render_template('edit.html', maquina=maquina)

# Deletar máquina
@app.route('/delete/<int:id>')
def delete(id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM maquinas WHERE id=%s", (id,))
    mysql.connection.commit()
    cur.close()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
