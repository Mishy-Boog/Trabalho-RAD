import sqlite3
import os
from cadastro import Cadastro
from cadastro import CadastroAdm
from datetime import datetime

class BancoDeDados:
    def __init__(self, nome_banco="banco.sqlite"):
        self.nome_banco = os.path.join(os.path.dirname(__file__), nome_banco)
        self.conn = None

    def conectar(self):
        try:
            self.conn = sqlite3.connect(self.nome_banco, timeout=10, check_same_thread=False)
            self.conn.execute("PRAGMA foreign_keys = ON")
            print("Conexão aberta e PRAGMA foreign_keys=ON executado.")
            return True
        except sqlite3.Error as e:
            print(f"Erro ao conectar ao banco de dados: {e}")
            self.conn = None
            return False

    def criar_tabelas(self):
        if not self.conn:
            if not self.conectar():
                print("Não foi possível conectar ao banco para criar tabelas.")
                return False
        try:
            self.cadastrar()
            self.cadastrar_adm()
            self.banco_log()
            return True
        except Exception as e:
            print(f"Erro durante a criação de tabelas: {e}")
            return False


    def cadastrar(self):
        """Cria a tabela Pessoa se não existir."""
        if self.conn:
            try:
                cursor = self.conn.cursor()
                cursor.execute(
                    """CREATE TABLE IF NOT EXISTS Pessoa(
                    cpf TEXT PRIMARY KEY,
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
                print("Tabela Pessoa verificada/criada.")
            except sqlite3.Error as e:
                print(f"Erro ao criar tabela Pessoa: {e}")
                raise

    def inserir_pessoa(self, pessoa: Cadastro, cpf_adm=None):
        """Insere uma nova pessoa e registra o log"""
        if not self.conn:
            print("Erro: Sem conexão com o banco para inserir pessoa.")
            return False
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "INSERT INTO Pessoa (cpf, nome, login, senha, bloco, numero_ap, email, data_cadastro) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (pessoa.cpf, pessoa.nome, pessoa.login, pessoa.get_senha(), pessoa.bloco, pessoa.numero_ap,
                 pessoa.email, pessoa.data_cadastro)
            )
            acao_log = "Cadastro de novo usuário" if cpf_adm else "Auto-cadastro de usuário"
            log_id = self.inserir_log(cpf_adm, pessoa.cpf, acao_log)
            if log_id is None:
                print(f"Erro ao inserir log para {acao_log}. Revertendo inserção de pessoa.")
                self.conn.rollback()
                raise sqlite3.Error(f"Falha ao registrar log para {acao_log}.")
            self.conn.commit()
            print(f"Pessoa inserida com sucesso! Log ID: {log_id}")
            return True
        except sqlite3.Error as e:
            print(f"Erro ao inserir pessoa: {e}")
            self.conn.rollback()
            if "UNIQUE constraint failed" in str(e):
                 raise ValueError(f"Erro: CPF ou Login ou Email já cadastrado ({e})")
            raise

    def atualizar_pessoa(self, cpf, cpf_adm=None, novo_nome=None, novo_email=None, novo_login=None, novo_senha=None,
                         novo_bloco=None, novo_numero_ap=None):
        """Atualiza dados de uma pessoa e registra o log"""
        if not self.conn:
            print("Erro: Sem conexão com o banco para atualizar pessoa.")
            return False
        updates = []
        params = []
        if novo_nome is not None: updates.append("nome = ?"); params.append(novo_nome)
        if novo_email is not None: updates.append("email = ?"); params.append(novo_email)
        if novo_login is not None: updates.append("login = ?"); params.append(novo_login)
        if novo_senha is not None: updates.append("senha = ?"); params.append(novo_senha)
        if novo_bloco is not None: updates.append("bloco = ?"); params.append(novo_bloco)
        if novo_numero_ap is not None: updates.append("numero_ap = ?"); params.append(novo_numero_ap)
        
        if not updates:
            print("Nenhuma atualização solicitada para Pessoa.")
            return False

        params.append(cpf)
        sql = f"UPDATE Pessoa SET {", ".join(updates)} WHERE cpf = ?"
        
        try:
            cursor = self.conn.cursor()
            cursor.execute(sql, tuple(params))
            if cursor.rowcount > 0:
                acao_log = "Usuário atualizado por ADM" if cpf_adm else "Usuário atualizou próprios dados"
                log_id = self.inserir_log(cpf_adm, cpf, acao_log)
                if log_id is None:
                    print(f"Erro ao inserir log para {acao_log}. Revertendo atualização.")
                    self.conn.rollback()
                    raise sqlite3.Error(f"Falha ao registrar log para {acao_log}.")
                self.conn.commit()
                print(f"Pessoa atualizada com sucesso! Log ID: {log_id}")
                return True
            else:
                print(f"Nenhuma pessoa encontrada com o CPF {cpf} para atualizar.")
                return False
        except sqlite3.Error as e:
            print(f"Erro ao atualizar pessoa: {e}")
            self.conn.rollback()
            if "UNIQUE constraint failed" in str(e):
                 raise ValueError(f"Erro: Login ou Email já cadastrado por outro usuário ({e})")
            raise

    def deletar_pessoa(self, cpf, cpf_adm=None):
        """Deleta uma pessoa e registra o log. cpf_adm=None para auto-exclusão."""
        if not self.conn:
            raise ConnectionError("Sem conexão com o banco para deletar pessoa.")
        
        print(f"[BD DEBUG] deletar_pessoa - Tentando excluir CPF: {cpf} por ADM: {cpf_adm}")
        
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT nome FROM Pessoa WHERE cpf = ?", (cpf,))
            pessoa = cursor.fetchone()
            
            if pessoa:
                acao_log = "Usuário excluído por ADM" if cpf_adm else "Usuário excluiu própria conta"
                print(f"[BD DEBUG] deletar_pessoa - Tentando inserir log ANTES da exclusão. ADM: {cpf_adm}, Alvo: {cpf}, Ação: {acao_log}")
                log_id = self.inserir_log(cpf_adm, cpf, acao_log)
                
                if log_id is None:
                    print(f"[BD ERROR] Falha ao inserir log para {acao_log}. Exclusão cancelada.")
                    raise sqlite3.Error(f"Falha ao registrar log de {acao_log}. Exclusão cancelada.")

                print(f"[BD DEBUG] deletar_pessoa - Log ID {log_id} inserido. Prosseguindo com DELETE para CPF {cpf}.")
                cursor.execute("DELETE FROM Pessoa WHERE cpf = ?", (cpf,))
                
                if cursor.rowcount > 0:
                    self.conn.commit()
                    print(f"Pessoa (CPF: {cpf}) deletada com sucesso! Log ID: {log_id}")
                    return True
                else:
                    print(f"[BD ERROR] Erro INESPERADO ao deletar: Usuário com CPF {cpf} não encontrado APÓS inserção do log (rowcount=0).")
                    self.conn.rollback()
                    return False
            else:
                print(f"Usuário com CPF {cpf} não encontrado para exclusão.")
                return False
        except sqlite3.Error as e:

            print(f"[BD ERROR] Erro SQLite ao deletar pessoa (CPF: {cpf}): {e}")
            self.conn.rollback()
            raise

    def listar_pessoas(self):
        """Lista todas as pessoas."""
        if not self.conn:
            if not self.conectar(): return []
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM Pessoa")
            return cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Erro ao listar pessoas: {e}")
            return []

    def cadastrar_adm(self):
        """Cria a tabela Adm se não existir."""
        if self.conn:
            try:
                cursor = self.conn.cursor()
                cursor.execute(
                    """CREATE TABLE IF NOT EXISTS Adm(
                    cpf TEXT PRIMARY KEY,
                    nome TEXT NOT NULL,
                    login TEXT NOT NULL UNIQUE,
                    senha TEXT NOT NULL,
                    data_cadastro TEXT
                    )"""
                )
                self.conn.commit()
                print("Tabela Adm verificada/criada.")
            except sqlite3.Error as e:
                print(f"Erro ao criar tabela Adm: {e}")
                raise

    def inserir_adm(self, adm: CadastroAdm):
        """Insere um novo administrador."""
        if not self.conn:
             print("Erro: Sem conexão com o banco para inserir ADM.")
             return False
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "INSERT INTO Adm (cpf, nome, login, senha, data_cadastro) VALUES (?, ?, ?, ?, ?)",
                (adm.cpf, adm.nome, adm.login, adm.get_senha(), adm.data_cadastro)
            )

            self.conn.commit()
            print("Adm inserido com sucesso!")
            return True
        except sqlite3.Error as e:
            print(f"Erro ao inserir adm: {e}")
            self.conn.rollback()
            if "UNIQUE constraint failed" in str(e):
                 raise ValueError(f"Erro: CPF ou Login de ADM já cadastrado ({e})")
            raise

    def listar_adms(self):
        """Lista todos os administradores."""
        if not self.conn:
            if not self.conectar(): return []
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT cpf, nome, login, data_cadastro FROM Adm")
            return cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Erro ao listar administradores: {e}")
            return []

    def atualizar_adm(self, cpf_adm_executor, cpf_adm_alvo, novo_nome=None, novo_login=None, nova_senha=None):
        """Atualiza dados de um administrador."""
        if not self.conn:
            print("Erro: Sem conexão com o banco para atualizar ADM.")
            return False
        updates = []
        params = []
        if novo_nome is not None: updates.append("nome = ?"); params.append(novo_nome)
        if novo_login is not None: updates.append("login = ?"); params.append(novo_login)
        if nova_senha is not None: updates.append("senha = ?"); params.append(nova_senha)
        
        if not updates:
            print("Nenhuma atualização solicitada para ADM.")
            return False
            
        params.append(cpf_adm_alvo)
        sql = f"UPDATE Adm SET {", ".join(updates)} WHERE cpf = ?"
        
        try:
            cursor = self.conn.cursor()
            cursor.execute(sql, tuple(params))
            if cursor.rowcount > 0:
                self.conn.commit()
                print(f"Administrador: {cpf_adm_executor} atualizou o Adm abaixo")
                print(f"Administrador (CPF: {cpf_adm_alvo}) atualizado com sucesso!")
                return True
            else:
                print(f"Nenhum administrador encontrado com o CPF {cpf_adm_alvo} para atualizar.")
                return False
        except sqlite3.Error as e:
            print(f"Erro ao atualizar administrador: {e}")
            self.conn.rollback()
            if "UNIQUE constraint failed" in str(e):
                 raise ValueError(f"Erro: Login de ADM já cadastrado por outro administrador ({e})")
            raise

    def deletar_adm(self, cpf_adm_executor, cpf_adm_alvo):
        """Deleta um administrador."""
        if not self.conn:
            raise ConnectionError("Sem conexão com o banco para deletar ADM.")
        if cpf_adm_executor == cpf_adm_alvo:
            raise ValueError("Administrador não pode excluir a própria conta.")
            
        print(f"[BD DEBUG] deletar_adm - Tentando excluir ADM CPF: {cpf_adm_alvo} por ADM: {cpf_adm_executor}")
        
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT nome FROM Adm WHERE cpf = ?", (cpf_adm_alvo,))
            adm = cursor.fetchone()
            if adm:

                cursor.execute("DELETE FROM Adm WHERE cpf = ?", (cpf_adm_alvo,))
                if cursor.rowcount > 0:
                    self.conn.commit()
                    print(f"Administrador (CPF: {cpf_adm_alvo}) deletado com sucesso!")
                    return True
                else:
                    print(f"[BD ERROR] Erro INESPERADO ao deletar ADM: ADM com CPF {cpf_adm_alvo} não encontrado APÓS verificação inicial (rowcount=0).")
                    self.conn.rollback()
                    return False
            else:
                print(f"Administrador com CPF {cpf_adm_alvo} não encontrado para exclusão.")
                return False
        except sqlite3.Error as e:
            print(f"[BD ERROR] Erro SQLite ao deletar administrador (CPF: {cpf_adm_alvo}): {e}")
            self.conn.rollback()
            raise


    @staticmethod
    def validar_login(login, senha):

        conn = None
        try:
            db_path = os.path.join(os.path.dirname(__file__), "banco.sqlite")
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            # Verifica ADM primeiro
            cursor.execute("SELECT cpf, nome FROM Adm WHERE login = ? AND senha = ?", (login, senha))
            adm = cursor.fetchone()
            if adm:
                print(f"Login ADM bem-sucedido para {login}")
                return "adm", adm[0], adm[1]
            cursor.execute("SELECT cpf, nome, bloco, numero_ap, email FROM Pessoa WHERE login = ? AND senha = ?", (login, senha))
            pessoa = cursor.fetchone()
            if pessoa:
                print(f"Login Pessoa bem-sucedido para {login}")
                return "pessoa", pessoa[0], pessoa[1], pessoa[2], pessoa[3], pessoa[4]
            print(f"Login ou senha inválidos para {login}.")
            return None
        except sqlite3.Error as e:
            print(f"Erro durante validação de login: {e}")
            return None
        finally:
            if conn:
                conn.close()

    def banco_log(self):
        """Cria ou atualiza a tabela Log, garantindo FKs corretas."""
        if self.conn:
            try:
                cursor = self.conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='Log';")
                table_exists = cursor.fetchone()

                create_table_sql = """
                    CREATE TABLE Log(
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        cpf_adm TEXT, 
                        cpf_alvo TEXT, 
                        acao TEXT NOT NULL,
                        data_hora TEXT,
                        FOREIGN KEY (cpf_adm) REFERENCES Adm(cpf) ON DELETE SET NULL,
                        FOREIGN KEY (cpf_alvo) REFERENCES Pessoa(cpf) ON DELETE SET NULL
                    )
                """
                
                if not table_exists:
                    print("Tabela Log não existe. Criando...")
                    cursor.execute(create_table_sql)
                else:

                    print("Tabela Log já existe. Verificação de estrutura não implementada.")
                    
                self.conn.commit()
                print("Tabela Log verificada/criada.")
            except sqlite3.Error as e:
                print(f"Erro ao criar/verificar tabela Log: {e}")
                raise

    def inserir_log(self, cpf_adm, cpf_alvo, acao):
        """Insere um registro na tabela Log"""
        if not self.conn:
            print("Erro: Sem conexão com o banco para inserir log.")
            raise ConnectionError("Sem conexão com o banco para inserir log.")

        print(f"[BD DEBUG] inserir_log - Tentando inserir: ADM={cpf_adm}, Alvo={cpf_alvo}, Ação='{acao}'")

        try:
            data_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor = self.conn.cursor()

            if cpf_adm is not None:
                cursor.execute("SELECT 1 FROM Adm WHERE cpf = ?", (cpf_adm,))
                if cursor.fetchone() is None:
                    print(
                        f"[BD ERROR] Falha ao inserir log: CPF do ADM executor ({cpf_adm}) não encontrado na tabela Adm.")
                    raise sqlite3.IntegrityError(f"FOREIGN KEY constraint failed: ADM CPF {cpf_adm} não existe.")

            nome_alvo = None
            cpf_real = cpf_alvo

            if cpf_alvo:
                cursor.execute("SELECT nome, cpf FROM Pessoa WHERE cpf = ?", (cpf_alvo,))
                resultado = cursor.fetchone()
                if resultado:
                    nome_alvo, cpf_real = resultado
                else:
                    nome_alvo = None

            if "excluído" in acao or "excluiu" in acao:
                if nome_alvo:
                    acao += f"\n  Alvo: {nome_alvo} | CPF: {cpf_real}"
                else:
                    acao += f"\n  Alvo: CPF: {cpf_real} (usuário já removido)"
            elif "atualizado" in acao:
                if nome_alvo:
                    acao += f"\n  Alvo: {nome_alvo} | CPF: {cpf_real}"
                else:
                    acao += f"\n  Alvo: CPF: {cpf_real} (não encontrado)"
            elif "Cadastro" in acao:
                if nome_alvo:
                    acao += f"\n  Alvo: {nome_alvo} | CPF: {cpf_real}"
                else:
                    acao += f"\n  Alvo: CPF: {cpf_real} (não encontrado)"

            cursor.execute(
                "INSERT INTO Log (cpf_adm, cpf_alvo, acao, data_hora) VALUES (?, ?, ?, ?)",
                (cpf_adm, cpf_alvo, acao, data_hora)
            )
            log_id = cursor.lastrowid
            self.conn.commit()
            print(f"[BD DEBUG] inserir_log - Log ID {log_id} inserido com sucesso.")
            return log_id

        except sqlite3.Error as db_err:
            print(f"[BD ERROR] Erro ao inserir log: {db_err}")
            raise db_err
        except Exception as e:
            print(f"[BD ERROR] Erro inesperado ao inserir log: {e}")
            raise e

    def cursor(self):
        """Retorna um cursor da conexão."""
        if self.conn is None:
            raise Exception("Conexão com o banco de dados não estabelecida.")
        return self.conn.cursor()

    @staticmethod
    def buscar_usuario_por_cpf(conn, cpf):
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT id, nome, cpf FROM Pessoa WHERE cpf=?", (cpf,))
        usuario = cursor.fetchone()

        if usuario:
            return dict(usuario)
        return None

    def fechar_conexao(self):
        if self.conn:
            self.conn.close()
            self.conn = None
            print("Conexão com o banco de dados fechada.")
