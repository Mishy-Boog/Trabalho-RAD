import sqlite3
import os
from cadastro import Cadastro
from cadastro import Cadastro_adm


class BancoDeDados:
    def __init__(self, nome_banco="banco.sqlite"):
        self.nome_banco = os.path.join(os.path.dirname(__file__), nome_banco)
        self.conn = None
        self.usuario_logado = None

    def conectar(self):
        try:
            self.conn = sqlite3.connect(self.nome_banco)
        except sqlite3.Error as e:
            print(f"Erro ao conectar ao banco de dados: {e}")

    def criar_tabelas(self):
        self.cadastrar()
        self.cadastrar_adm()
        self.banco_log()

    def cadastrar(self):
        if self.conn:
            try:
                cursor = self.conn.cursor()
                cursor.execute(
                    """CREATE TABLE IF NOT EXISTS Pessoa(
                    cpf INTEGER PRIMARY KEY,
                    nome TEXT NOT NULL,
                    login TEXT NOT NULL UNIQUE,
                    senha TEXT NOT NULL,
                    bloco INTEGER,
                    numero_ap INTEGER,
                    email TEXT NOT NULL UNIQUE,
                    data_cadastro TEXT
                    )"""
                )
                self.conn.commit()
            except sqlite3.Error as e:
                print(f"Erro ao criar tabela Pessoa: {e}")

    def inserir_pessoa(self, pessoa: Cadastro):
        if self.conn:
            try:
                cursor = self.conn.cursor()
                cursor.execute(
                    "INSERT INTO Pessoa (cpf, nome, login, senha, bloco, numero_ap, email, data_cadastro) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (pessoa.cpf, pessoa.nome, pessoa.login, pessoa.get_senha(), pessoa.bloco, pessoa.numero_ap,
                     pessoa.email, pessoa.data_cadastro)
                )

                # Verificando se existe um usuário logado
                responsavel = self.usuario_logado if self.usuario_logado else "Desconhecido"
                self.inserir_log(pessoa.nome, "Cadastro de novo usuário", responsavel)
                self.conn.commit()
                print("Pessoa inserida com sucesso!")
            except sqlite3.Error as e:
                print(f"Erro ao inserir pessoa: {e}")

    def atualizar_pessoa(self, cpf, novo_nome=None, novo_email=None, novo_login=None, novo_senha=None,
                         novo_bloco=None, novo_numero_ap=None, responsavel="Administrador"):
        if self.conn:
            try:
                cursor = self.conn.cursor()
                nome_atualizado = None

                if novo_nome:
                    cursor.execute("UPDATE Pessoa SET nome = ? WHERE cpf = ?", (novo_nome, cpf))
                    nome_atualizado = novo_nome

                if novo_email:
                    cursor.execute("UPDATE Pessoa SET email = ? WHERE cpf = ?", (novo_email, cpf))

                if novo_login:
                    cursor.execute("UPDATE Pessoa SET login = ? WHERE cpf = ?", (novo_login, cpf))

                if novo_senha:
                    cursor.execute("UPDATE Pessoa SET senha = ? WHERE cpf = ?", (novo_senha, cpf))

                if novo_bloco:
                    cursor.execute("UPDATE Pessoa SET bloco = ? WHERE cpf = ?", (novo_bloco, cpf))

                if novo_numero_ap:
                    cursor.execute("UPDATE Pessoa SET numero_ap = ? WHERE cpf = ?", (novo_numero_ap, cpf))

                self.conn.commit()

                if nome_atualizado:
                    self.inserir_log(nome_atualizado, "Usuário atualizado",
                                     responsavel)  # Passando o responsável no log

                print("Pessoa atualizada com sucesso!")

            except sqlite3.Error as e:
                print(f"Erro ao atualizar pessoa: {e}")

    def deletar_pessoa(self, cpf, responsavel="Administrador"):
        if self.conn:
            try:
                cursor = self.conn.cursor()
                cursor.execute("SELECT nome FROM Pessoa WHERE cpf = ?", (cpf,))
                nome = cursor.fetchone()
                if nome:
                    nome = nome[0]
                    cursor.execute("DELETE FROM Pessoa WHERE cpf = ?", (cpf,))
                    self.conn.commit()
                    self.inserir_log(nome, "Usuário excluído", responsavel)  # Passando o responsável no log
                    print("Pessoa deletada com sucesso!")
            except sqlite3.Error as e:
                print(f"Erro ao deletar pessoa: {e}")

    def listar_pessoas(self, cpf):
        if self.conn:
            try:
                cursor = self.conn.cursor()
                cursor.execute("SELECT * FROM Pessoa")
                return cursor.fetchall()
            except sqlite3.Error as e:
                print(f"Erro ao listar pessoas: {e}")
                return []

    def cadastrar_adm(self):
        if self.conn:
            try:
                cursor = self.conn.cursor()
                cursor.execute(
                    """CREATE TABLE IF NOT EXISTS Adm(
                    cpf INTEGER PRIMARY KEY,
                    nome TEXT NOT NULL,
                    login TEXT NOT NULL UNIQUE,
                    senha TEXT NOT NULL,
                    data_cadastro TEXT 
                    )"""
                )
                self.conn.commit()
            except sqlite3.Error as e:
                print(f"Erro ao criar tabela adm: {e}")

    def inserir_adm(self, adm: Cadastro_adm):
        if self.conn:
            try:
                cursor = self.conn.cursor()
                cursor.execute(
                    "INSERT INTO Adm (cpf, nome, login, senha, data_cadastro) VALUES (?, ?, ?, ?, ?)",
                    (adm.cpf, adm.nome, adm.login, adm.get_senha(), adm.data_cadastro)
                )
                self.conn.commit()
                print("Adm inserida com sucesso!")
            except sqlite3.Error as e:
                print(f"Erro ao inserir adm: {e}")

    def validar_login(login, senha):
        global usuario_logado  # Usando a variável global

        conn = sqlite3.connect('banco.sqlite')
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM Pessoa WHERE login = ? AND senha = ?", (login, senha))
        pessoa = cursor.fetchone()

        if pessoa:
            usuario_logado = pessoa[
                1]  # Vamos armazenar o nome da pessoa logada (supondo que o nome esteja na posição 1)
            print(f"Login bem-sucedido! Bem-vindo, {usuario_logado}.")
            return True
        else:
            print("Login ou senha inválidos.")
            return False

    def banco_log(self):
        if self.conn:
            try:
                cursor = self.conn.cursor()
                cursor.execute(
                    """CREATE TABLE IF NOT EXISTS Log(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT NOT NULL,
                    acao TEXT NOT NULL,
                    data_hora TEXT,
                    responsavel TEXT NOT NULL  -- Adicionando o responsável
                    )"""
                )
                self.conn.commit()
            except sqlite3.Error as e:
                print(f"Erro ao criar tabela Log: {e}")

    def inserir_log(self, nome, acao, responsavel):
        if self.conn:
            try:
                from datetime import datetime
                data_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                cursor = self.conn.cursor()
                cursor.execute(
                    "INSERT INTO Log (nome, acao, data_hora, responsavel) VALUES (?, ?, ?, ?)",
                    (nome, acao, data_hora, responsavel)  # Aqui você passa o responsável
                )
                self.conn.commit()
                id = cursor.lastrowid
                print(f"Log inserido com sucesso! ID: {id}")
                return id
            except sqlite3.Error as e:
                print(f"Erro ao inserir log: {e}")
                return None

