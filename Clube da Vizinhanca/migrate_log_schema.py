import sqlite3
import os

def migrate_log_table(db_path):
    conn = None
    try:
        print(f"Conectando ao banco de dados: {db_path}")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        print("Verificando a estrutura atual da tabela Log...")
        cursor.execute("PRAGMA table_info(Log)")



        print("Iniciando migração da tabela Log...")

        cursor.execute("PRAGMA foreign_keys=OFF;")

        cursor.execute("BEGIN TRANSACTION;")

        print("Renomeando tabela Log para Log_old...")
        cursor.execute("ALTER TABLE Log RENAME TO Log_old;")

        print("Criando nova tabela Log com schema atualizado...")
        cursor.execute(
            """CREATE TABLE Log(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cpf_adm TEXT, -- Can be NULL for system actions/self-registration
                cpf_alvo TEXT, -- Made nullable
                acao TEXT NOT NULL,
                data_hora TEXT,
                FOREIGN KEY (cpf_adm) REFERENCES Adm(cpf) ON DELETE SET NULL,
                FOREIGN KEY (cpf_alvo) REFERENCES Pessoa(cpf) ON DELETE SET NULL -- Key change
            )"""
        )

        print("Copiando dados de Log_old para Log...")
        cursor.execute("INSERT INTO Log (id, cpf_adm, cpf_alvo, acao, data_hora) SELECT id, cpf_adm, cpf_alvo, acao, data_hora FROM Log_old;")

        print("Removendo tabela Log_old...")
        cursor.execute("DROP TABLE Log_old;")

        conn.commit()
        print("Transação concluída.")

        cursor.execute("PRAGMA foreign_keys=ON;")

        print("Migração da tabela Log concluída com sucesso!")

    except sqlite3.Error as e:
        print(f"Erro durante a migração: {e}")
        if conn:
            print("Revertendo alterações...")
            conn.rollback()
    finally:
        if conn:
            conn.close()
            print("Conexão com o banco fechada.")

if __name__ == "__main__":
    db_file = os.path.join(os.path.dirname(__file__), "banco.sqlite")
    if os.path.exists(db_file):
        migrate_log_table(db_file)
    else:
        print(f"Erro: Arquivo do banco de dados não encontrado em {db_file}")

