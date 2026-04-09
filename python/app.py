import sqlite3
import hashlib
from datetime import datetime

# --- CONFIGURAÇÃO E CRIAÇÃO DO BANCO ---
def inicializar_bd():
    with sqlite3.connect('sisvenda_total.db') as conn:
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

# --- FUNÇÕES DE USUÁRIO E SEGURANÇA ---
def cadastrar_usuario(username, senha, cargo='cliente'):
    senha_hash = hashlib.sha256(senha.encode()).hexdigest()
    try:
        with sqlite3.connect('sisvenda_total.db') as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT INTO usuarios (username, senha, cargo) VALUES (?, ?, ?)',
                           (username, senha_hash, cargo))
            conn.commit()
            print(f"\n[OK] Usuário '{username}' criado com sucesso!")
    except sqlite3.IntegrityError:
        print(f"\n[Erro] O usuário '{username}' já existe. Tente outro nome.")

def autenticar(username, senha):
    senha_hash = hashlib.sha256(senha.encode()).hexdigest()
    with sqlite3.connect('sisvenda_total.db') as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT username, cargo FROM usuarios WHERE username = ? AND senha = ?', 
                       (username, senha_hash))
        user = cursor.fetchone()
    return user

# --- FUNÇÕES DE PRODUTOS E VENDAS ---
def adicionar_produto(nome, preco, estoque):
    with sqlite3.connect('sisvenda_total.db') as conn:
        cursor = conn.cursor()
        cursor.execute('INSERT INTO produtos (nome, preco, estoque) VALUES (?, ?, ?)', 
                       (nome, preco, estoque))
        conn.commit()
        print(f"\n[OK] Produto '{nome}' cadastrado com sucesso!")

def listar_produtos():
    with sqlite3.connect('sisvenda_total.db') as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM produtos')
        prods = cursor.fetchall()
        
    if not prods:
        print("\nNenhum produto cadastrado no momento.")
    else:
        print("\n--- LISTA DE PRODUTOS ---")
        for p in prods:
            print(f"ID: {p[0]:02d} | {p[1]:<15} | Preço: R${p[2]:.2f} | Estoque: {p[3]}")

def realizar_venda(id_produto, quantidade, nome_cliente):
    if quantidade <= 0:
        print("\n[Erro] A quantidade deve ser maior que zero.")
        return

    with sqlite3.connect('sisvenda_total.db') as conn:
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
        elif prod:
            print(f"\n[Erro] Estoque insuficiente. Temos apenas {prod[2]} unidades de {prod[0]}.")
        else:
            print("\n[Erro] Produto inexistente (ID não encontrado).")

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
            n = input("Nome: ")
            p_str = input("Preço: ").replace(",", ".") # Aceita vírgula ou ponto
            e_str = input("Qtd Inicial: ")
            
            try:
                p = float(p_str)
                e = int(e_str)
                if p < 0 or e < 0:
                    print("\n[Erro] Preço e estoque não podem ser negativos.")
                else:
                    adicionar_produto(n, p, e)
            except ValueError:
                print("\n[Erro] Você digitou letras onde deveriam ser números. Tente novamente.")
                
        elif op == "2":
            listar_produtos()
            
        elif op == "3":
            u = input("Username: ")
            s = input("Senha: ")
            c = input("Cargo (admin/cliente): ").lower()
            if c in ['admin', 'cliente']:
                cadastrar_usuario(u, s, c)
            else:
                print("\n[Erro] Cargo inválido. Digite apenas 'admin' ou 'cliente'.")
                
        elif op == "0": 
            print("\nSaindo do painel administrativo...")
            break
        else:
            print("\n[Erro] Opção inválida.")

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
            try:
                id_p = int(input("\nID do produto: "))
                qtd = int(input("Quantidade: "))
                realizar_venda(id_p, qtd, nome)
            except ValueError:
                print("\n[Erro] Digite apenas números inteiros válidos para o ID e Quantidade!")
                
        elif op == "0": 
            print("\nSaindo da área do cliente...")
            break
        else:
            print("\n[Erro] Opção inválida.")

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
            u = input("User: ")
            s = input("Senha: ")
            dados = autenticar(u, s)
            
            if dados:
                if dados[1] == 'admin': 
                    menu_admin()
                else: 
                    menu_cliente(dados[0])
            else:
                print("\n[Erro] Login inválido. Usuário ou senha incorretos.")
                
        elif escolha == "2":
            u = input("Novo User: ")
            s = input("Nova Senha: ")
            cadastrar_usuario(u, s) # Por padrão, cria como 'cliente'
            
        elif escolha == "0": 
            print("\nEncerrando o SISVENDA. Até logo!")
            break
        else:
            print("\n[Erro] Opção inválida.")

if __name__ == "__main__":
    main()
