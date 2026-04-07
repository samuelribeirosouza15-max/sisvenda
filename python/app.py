import sqlite3
import hashlib
from datetime import datetime

# --- CONFIGURAÇÃO E CRIAÇÃO DO BANCO ---
def inicializar_bd():
    conn = sqlite3.connect('sisvenda_total.db')
    cursor = conn.cursor()
    
    # Tabela de Usuários
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            senha TEXT NOT NULL,
            cargo TEXT NOT NULL -- 'admin' ou 'cliente'
        )
    ''')
    
    # Tabela de Produtos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS produtos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            preco REAL NOT NULL,
            estoque INTEGER NOT NULL
        )
    ''')

    # Tabela de Vendas
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS vendas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente TEXT NOT NULL,
            data_venda TEXT NOT NULL,
            valor_total REAL NOT NULL
        )
    ''')

    # Criar Admin Padrão (usuário: admin | senha: 123)
    senha_admin = hashlib.sha256("123".encode()).hexdigest()
    try:
        cursor.execute('INSERT INTO usuarios (username, senha, cargo) VALUES (?, ?, ?)',
                       ('admin', senha_admin, 'admin'))
    except sqlite3.IntegrityError:
        pass 

    conn.commit()
    conn.close()

# --- FUNÇÕES DE USUÁRIO E SEGURANÇA ---
def cadastrar_usuario(username, senha, cargo='cliente'):
    conn = sqlite3.connect('sisvenda_total.db')
    cursor = conn.cursor()
    senha_hash = hashlib.sha256(senha.encode()).hexdigest()
    try:
        cursor.execute('INSERT INTO usuarios (username, senha, cargo) VALUES (?, ?, ?)',
                       (username, senha_hash, cargo))
        conn.commit()
        print(f"\n[OK] Usuário {username} criado!")
    except sqlite3.IntegrityError:
        print("\n[Erro] Usuário já existe.")
    finally:
        conn.close()

def autenticar(username, senha):
    conn = sqlite3.connect('sisvenda_total.db')
    cursor = conn.cursor()
    senha_hash = hashlib.sha256(senha.encode()).hexdigest()
    cursor.execute('SELECT username, cargo FROM usuarios WHERE username = ? AND senha = ?', 
                   (username, senha_hash))
    user = cursor.fetchone()
    conn.close()
    return user

# --- FUNÇÕES DE PRODUTOS E VENDAS ---
def adicionar_produto(nome, preco, estoque):
    conn = sqlite3.connect('sisvenda_total.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO produtos (nome, preco, estoque) VALUES (?, ?, ?)', 
                   (nome, preco, estoque))
    conn.commit()
    conn.close()

def listar_produtos():
    conn = sqlite3.connect('sisvenda_total.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM produtos')
    prods = cursor.fetchall()
    conn.close()
    if not prods:
        print("\nNenhum produto cadastrado.")
    for p in prods:
        print(f"ID: {p[0]} | {p[1]} | Preço: R${p[2]:.2f} | Estoque: {p[3]}")

def realizar_venda(id_produto, quantidade, nome_cliente):
    conn = sqlite3.connect('sisvenda_total.db')
    cursor = conn.cursor()
    cursor.execute('SELECT nome, preco, estoque FROM produtos WHERE id = ?', (id_produto,))
    prod = cursor.fetchone()
    
    if prod and prod[2] >= quantidade:
        total = prod[1] * quantidade
        data = datetime.now().strftime('%d/%m/%Y %H:%M')
        # Atualiza estoque e registra venda
        cursor.execute('UPDATE produtos SET estoque = estoque - ? WHERE id = ?', (quantidade, id_produto))
        cursor.execute('INSERT INTO vendas (cliente, data_venda, valor_total) VALUES (?, ?, ?)', 
                       (nome_cliente, data, total))
        conn.commit()
        print(f"\n[SUCESSO] {quantidade}x {prod[0]} vendido(s) para {nome_cliente}. Total: R${total:.2f}")
    else:
        print("\n[Erro] Estoque insuficiente ou produto inexistente.")
    conn.close()

# --- INTERFACES (MENUS) ---
def menu_admin():
    while True:
        print("\n--- PAINEL ADMINISTRATIVO ---")
        print("1. Cadastrar Produto")
        print("2. Ver Estoque")
        print("3. Criar Novo Usuário")
        print("0. Logout")
        op = input("Escolha: ")
        
        if op == "1":
            n = input("Nome: "); p = float(input("Preço: ")); e = int(input("Qtd Inicial: "))
            adicionar_produto(n, p, e)
        elif op == "2":
            listar_produtos()
        elif op == "3":
            u = input("Username: "); s = input("Senha: "); c = input("Cargo (admin/cliente): ")
            cadastrar_usuario(u, s, c)
        elif op == "0": break

def menu_cliente(nome):
    while True:
        print(f"\n--- ÁREA DO CLIENTE ({nome}) ---")
        print("1. Ver Produtos")
        print("2. Comprar")
        print("0. Logout")
        op = input("Escolha: ")
        
        if op == "1":
            listar_produtos()
        elif op == "2":
            listar_produtos()
            id_p = int(input("ID do produto: "))
            qtd = int(input("Quantidade: "))
            realizar_venda(id_p, qtd, nome)
        elif op == "0": break

# --- LOOP PRINCIPAL ---
def main():
    inicializar_bd()
    while True:
        print("\n=== SISVENDA v1.0 ===")
        print("1. Login")
        print("2. Criar Conta")
        print("0. Fechar")
        escolha = input("Opção: ")
        
        if escolha == "1":
            u = input("User: "); s = input("Senha: ")
            dados = autenticar(u, s)
            if dados:
                if dados[1] == 'admin': menu_admin()
                else: menu_cliente(dados[0])
            else:
                print("\nLogin inválido.")
        elif escolha == "2":
            u = input("Novo User: "); s = input("Nova Senha: ")
            cadastrar_usuario(u, s)
        elif escolha == "0": break

if __name__ == "__main__":
    main()