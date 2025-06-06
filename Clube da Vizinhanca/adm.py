import tkinter as tk
from tkinter import messagebox
from bd import BancoDeDados
from cadastro import CadastroAdm, Cadastro
from datetime import datetime
import os
import platform
import subprocess
import sqlite3
from validacao import validar_nome, validar_email, validar_senha, validar_login, validar_cpf, validar_3dig


bd = BancoDeDados()


def mostrar_usuarios(root, cpf_adm_executor):
    """Exibe a lista de usuários e permite ações de ADM."""
    print(f"[ADM DEBUG] Entrando em mostrar_usuarios com ADM CPF: {cpf_adm_executor}")
    if not bd.conn:
        if not bd.conectar():
            messagebox.showerror("Erro Crítico", "Não foi possível conectar ao banco de dados.")
            return
        bd.criar_tabelas()

    if bd.conn:
        try:
            cursor = bd.conn.cursor()
            cursor.execute("SELECT nome, cpf, bloco, numero_ap, email, data_cadastro FROM Pessoa")
            usuarios = cursor.fetchall()


            for widget in root.winfo_children():
                widget.destroy()
                from interface import set_root
                set_root(root)

            janela_usuarios = root
            janela_usuarios.title("Painel do Administrador - Gerenciar Usuários")
            janela_usuarios.geometry("700x580+300+1")
            janela_usuarios.configure(bg="#000F1A")

            tk.Label(janela_usuarios, text="Gerenciar Usuários", font=("Helvetica", 14, "bold"), bg="#000F1A", fg="white").pack(pady=10)


            list_frame = tk.Frame(janela_usuarios, bg="#000F1A")
            list_frame.pack(fill="both", expand=True, padx=10, pady=5)

            canvas = tk.Canvas(list_frame)
            scrollbar = tk.Scrollbar(list_frame, orient="vertical", command=canvas.yview)
            scrollable_frame = tk.Frame(canvas)

            scrollable_frame.bind(
                "<Configure>",
                lambda a: canvas.configure(
                    scrollregion=canvas.bbox("all")
                )
            )

            canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
            canvas.configure(yscrollcommand=scrollbar.set)

            if not usuarios:
                tk.Label(scrollable_frame, text="Nenhum usuário cadastrado.").pack(pady=20)
            else:
                for usuario in usuarios:
                    nome, cpf_usuario, bloco, numero_ap, email, data_cadastro = usuario
                    user_frame = tk.Frame(scrollable_frame, borderwidth=1, relief="solid", bg="#AAAAAA")
                    user_frame.pack(fill="x", padx=5, pady=3)

                    info = f"{nome} | CPF: {cpf_usuario} | Bloco: {bloco} | Ap: {numero_ap} | Email: {email}"
                    tk.Label(user_frame, text=info, anchor="w", bg="#AAAAAA").pack(side="left", padx=5)

                    tk.Button(user_frame, text="Excluir",
                              command=lambda c=cpf_usuario, adm_exec=cpf_adm_executor: excluir_usuario(root, adm_exec,c),
                              fg="dark red", bg="light gray").pack(side="right", padx=2, pady=3)

                    tk.Button(user_frame, text="Editar",
                              command=lambda c=cpf_usuario, adm_exec=cpf_adm_executor: editar_usuario(root, adm_exec,c),
                              fg="dark green", bg="light gray").pack(side="right", padx=2, pady=3)

            canvas.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")


            action_frame = tk.Frame(janela_usuarios, bg="#000F1A")
            action_frame.pack(pady=10)
            tk.Button(action_frame, text="Cadastrar Novo Usuário",
                      command=lambda adm_exec=cpf_adm_executor: abrir_cadastro(root, adm_exec),
                      font=("Arial", 9, "bold"),
                      bg="#001F3F",
                      fg="white",
                      activebackground="#003366",
                      activeforeground="white",
                      relief="raised",
                      height=1,
                      pady=4, padx=4, cursor="hand2"
                      ).pack(side="left", padx=5)

            tk.Button(action_frame, text="Cadastrar Novo ADM",
                      command=lambda adm_exec=cpf_adm_executor: abrir_cadastro_adm(root, adm_exec),
                      font=("Arial", 9, "bold"),
                      bg="#001F3F",
                      fg="white",
                      activebackground="#003366",
                      activeforeground="white",
                      relief="raised",
                      height=1,
                      pady=4, padx=4, cursor="hand2"
                      ).pack(side="left", padx=5)

            tk.Button(action_frame, text="Mostrar Logs", command=exportar_logs_para_txt,
                      font=("Arial", 9, "bold"),
                      bg="#001F3F",
                      fg="white",
                      activebackground="#003366",
                      activeforeground="white",
                      relief="raised",
                      height=1,
                      pady=4, padx=4, cursor="hand2"
                      ).pack(side="left", padx=5)

            tk.Button(action_frame, text="Gerenciar Administradores",
                      command=lambda adm_exec=cpf_adm_executor: mostrar_adms(root, adm_exec),
                      font=("Arial", 9, "bold"),
                      bg="#001F3F",  # Fundo azul escuro
                      fg="white",  # Texto branco
                      activebackground="#003366",  # Fundo ao clicar
                      activeforeground="white",  # Texto ao clicar
                      relief="raised",
                      height=1,
                      pady=4, padx=4, cursor="hand2"
                      ).pack(side="left", padx=5)
            from interface import reiniciar_para_login
            try:

                tk.Button(janela_usuarios, text="Logout", command=reiniciar_para_login,
                          font=("Arial", 9, "bold"),
                          bg="#001F3F",
                          fg="white",
                          activebackground="#003366",
                          activeforeground="white",
                          relief="raised",
                          width=10,
                          height=1,
                          pady=4, padx=4, cursor="hand2"
                          ).pack(pady=10)

            except ImportError:
                tk.Button(janela_usuarios, text="Fechar Painel ADM", command=root.destroy).pack(pady=10)

        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao buscar usuários: {e}")
            print(f"[ADM ERROR] Erro em mostrar_usuarios: {e}")


def editar_usuario(root, cpf_adm_executor, cpf_usuario_alvo):
    """Abre a janela para o ADM editar os dados de um usuário."""
    print(f"[ADM DEBUG] Iniciando edição do Usuário CPF {cpf_usuario_alvo} pelo ADM CPF {cpf_adm_executor}")
    if not bd.conn:
        if not bd.conectar(): messagebox.showerror("Erro", "Sem conexão com banco."); return
    try:
        cursor = bd.conn.cursor()
        cursor.execute("SELECT nome, email, bloco, numero_ap, login FROM Pessoa WHERE cpf = ?",
                       (str(cpf_usuario_alvo),))
        usuario = cursor.fetchone()
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao buscar dados do usuário: {e}")
        return

    if not usuario: messagebox.showerror("Erro", "Usuário não encontrado."); return
    nome_atual, email_atual, bloco_atual, numero_ap_atual, login_atual = usuario

    janela_editar = tk.Toplevel(root)
    janela_editar.title(f"Editar Usuário - CPF: {cpf_usuario_alvo}")
    janela_editar.geometry("400x450+500+100")
    janela_editar.configure(bg="#000F1A")
    janela_editar.transient(root)
    janela_editar.grab_set()

    tk.Label(janela_editar, text="Nome*", bg="#000F1A",
             fg="light gray",
             font=("Helvetica", 9, "bold"),
             width=7,
             height=1,
             pady=4, padx=1).pack()
    entry_nome = tk.Entry(janela_editar,
                          fg="black",
                          relief="flat",
                          highlightbackground="#001427",
                          highlightcolor="#00ADB5",
                          highlightthickness=2,
                          insertbackground="black", justify="center"
                          )
    entry_nome.insert(0, nome_atual)
    entry_nome.pack()

    tk.Label(janela_editar, text="Email*",
             bg="#000F1A",
             fg="light gray",
             font=("Helvetica", 9, "bold"),
             width=7,
             height=1,
             pady=4, padx=1
             ).pack()
    entry_email = tk.Entry(janela_editar,
                           fg="black",
                           relief="flat",
                           highlightbackground="#001427",
                           highlightcolor="#00ADB5",
                           highlightthickness=2,
                           insertbackground="black", justify="center"
                           )
    entry_email.insert(0, email_atual)
    entry_email.pack()

    tk.Label(janela_editar, text="Bloco",
             bg="#000F1A",
             fg="light gray",
             font=("Helvetica", 9, "bold"),
             width=7,
             height=1,
             pady=4, padx=1
             ).pack()
    entry_bloco = tk.Entry(janela_editar,
                           fg="black",
                           relief="flat",
                           highlightbackground="#001427",
                           highlightcolor="#00ADB5",
                           highlightthickness=2,
                           insertbackground="black", justify="center"
                           )
    entry_bloco.insert(0, str(bloco_atual) if bloco_atual is not None else "")
    entry_bloco.pack()

    tk.Label(janela_editar, text="Número do AP",
             bg="#000F1A",
             fg="light gray",
             font=("Helvetica", 9, "bold"),
             width=27,
             height=1,
             pady=4, padx=1
             ).pack()
    entry_numero_ap = tk.Entry(janela_editar,
                               fg="black",
                               relief="flat",
                               highlightbackground="#001427",
                               highlightcolor="#00ADB5",
                               highlightthickness=2,
                               insertbackground="black", justify="center"
                               )
    entry_numero_ap.insert(0, str(numero_ap_atual) if numero_ap_atual is not None else "")
    entry_numero_ap.pack()

    tk.Label(janela_editar, text="Login*",
             bg="#000F1A",
             fg="light gray",
             font=("Helvetica", 9, "bold"),
             width=7,
             height=1,
             pady=4, padx=1
             ).pack()
    entry_login = tk.Entry(janela_editar,
                           fg="black",
                           relief="flat",
                           highlightbackground="#001427",
                           highlightcolor="#00ADB5",
                           highlightthickness=2,
                           insertbackground="black", justify="center"
                           )
    entry_login.insert(0, login_atual)
    entry_login.pack()
    tk.Label(janela_editar, text="Nova Senha (deixe em branco para não alterar)",
             bg="#000F1A",
             fg="light gray",
             font=("Helvetica", 9, "bold"),
             width=37,
             height=1,
             pady=4, padx=1
             ).pack()
    entry_senha = tk.Entry(janela_editar, show=">")
    entry_senha.pack()
    tk.Label(janela_editar, text="* Campos obrigatórios",
             font=("Arial", 6, "bold"),
             bg="#001F3F",
             fg="white",
             relief="raised",
             width=16,
             height=1,
             pady=5, padx=4, cursor="heart"
             ).pack(pady=5)

    def salvar():
        novo_nome = entry_nome.get()
        novo_email = entry_email.get()
        novo_bloco_str = entry_bloco.get()
        novo_numero_ap_str = entry_numero_ap.get()
        novo_login = entry_login.get()
        nova_senha = entry_senha.get()
        if not novo_nome or not novo_email or not novo_login:
            messagebox.showwarning("Campos Obrigatórios", "Nome, Email e Login são obrigatórios.",
                                   parent=janela_editar)
            return
        try:
            novo_bloco = int(novo_bloco_str) if novo_bloco_str else None
            novo_numero_ap = int(novo_numero_ap_str) if novo_numero_ap_str else None
        except ValueError:
            messagebox.showerror("Erro de Formato", "Bloco e AP devem ser números.", parent=janela_editar)
            return

        if messagebox.askyesno("Confirmar Alterações", "Salvar mudanças para este usuário?", parent=janela_editar):
            try:

                bd.atualizar_pessoa(cpf=str(cpf_usuario_alvo), cpf_adm=cpf_adm_executor,
                                    novo_nome=novo_nome, novo_email=novo_email, novo_login=novo_login,
                                    novo_bloco=novo_bloco, novo_numero_ap=novo_numero_ap,
                                    novo_senha=nova_senha if nova_senha else None)

                messagebox.showinfo("Sucesso", "Usuário atualizado!", parent=janela_editar)
                janela_editar.destroy()
                mostrar_usuarios(root, cpf_adm_executor)

            except ValueError as ve:
                messagebox.showerror("Erro de Validação", str(ve), parent=janela_editar)
            except sqlite3.Error as db_err:
                print(f"[ADM ERROR] Erro SQLite em editar_usuario (salvar): {db_err}")
                messagebox.showerror("Erro de Banco", f"Erro ao atualizar usuário: {db_err}", parent=janela_editar)
            except Exception as t:
                messagebox.showerror("Erro Inesperado", f"Erro inesperado ao atualizar usuário: {t}",
                                     parent=janela_editar)

    tk.Button(janela_editar, text="Salvar Alterações", command=salvar,
              font=("Arial", 9, "bold"),
              bg="#001F3F",
              fg="white",
              activebackground="#003366",
              activeforeground="white",
              relief="raised",
              height=1,
              pady=4, padx=4, cursor="hand2"
              ).pack(pady=20)


def excluir_usuario(root, cpf_adm_executor, cpf_usuario_alvo):
    """Exclui um usuário pelo ADM."""
    print(f"[ADM DEBUG] Iniciando exclusão do Usuário CPF {cpf_usuario_alvo} pelo ADM CPF {cpf_adm_executor}")
    if messagebox.askyesno("Confirmar Exclusão", f"Excluir o usuário CPF {cpf_usuario_alvo}?", icon='warning'):
        if not bd.conn:
            if not bd.conectar(): messagebox.showerror("Erro", "Sem conexão com banco."); return
        try:

            bd.deletar_pessoa(cpf=str(cpf_usuario_alvo), cpf_adm=cpf_adm_executor)

            messagebox.showinfo("Sucesso", f"Usuário CPF {cpf_usuario_alvo} excluído.")
            mostrar_usuarios(root, cpf_adm_executor)

        except sqlite3.Error as db_err:
            print(f"[ADM ERROR] Erro SQLite em excluir_usuario: {db_err}")
            messagebox.showerror("Erro de Banco",
                                 f"Erro ao tentar excluir usuário: {db_err}. Verifique se o ADM executor ({cpf_adm_executor}) existe e é válido.")
        except Exception as e:
            print(f"[ADM ERROR] Exceção inesperada em excluir_usuario: {e}")
            messagebox.showerror("Erro Inesperado", f"Erro inesperado na exclusão: {e}")


def abrir_cadastro(root, cpf_adm_executor):
    print(f"[ADM DEBUG] Abrindo cadastro de usuário pelo ADM CPF: {cpf_adm_executor}")
    cadastro_window = tk.Toplevel(root)
    cadastro_window.title("Cadastrar Usuário")
    cadastro_window.geometry("350x450+500+100")
    cadastro_window.transient(root)
    cadastro_window.grab_set()
    cadastro_window.configure(bg="#000F1A")

    tk.Label(cadastro_window, text="CPF*",
             bg="#000F1A",
             fg="light gray",
             font=("Helvetica", 9, "bold"),
             width=7,
             height=1,
             pady=4, padx=1
             ).pack()
    entry_cpf = tk.Entry(cadastro_window,
                         fg="black",
                         relief="flat",
                         highlightbackground="#001427",
                         highlightcolor="#00ADB5",
                         highlightthickness=2,
                         insertbackground="black", justify="center"
                         )
    entry_cpf.pack()

    tk.Label(cadastro_window, text="Login*",
             bg="#000F1A",
             fg="light gray",
             font=("Helvetica", 9, "bold"),
             width=7,
             height=1,
             pady=4, padx=1
             ).pack()
    entry_login_cad = tk.Entry(cadastro_window,
                               fg="black",
                               relief="flat",
                               highlightbackground="#001427",
                               highlightcolor="#00ADB5",
                               highlightthickness=2,
                               insertbackground="black", justify="center"
                               )
    entry_login_cad.pack()

    tk.Label(cadastro_window, text="Nome*",
             bg="#000F1A",
             fg="light gray",
             font=("Helvetica", 9, "bold"),
             width=7,
             height=1,
             pady=4, padx=1
             ).pack()
    entry_nome = tk.Entry(cadastro_window,
                          fg="black",
                          relief="flat",
                          highlightbackground="#001427",
                          highlightcolor="#00ADB5",
                          highlightthickness=2,
                          insertbackground="black", justify="center"
                          )
    entry_nome.pack()

    tk.Label(cadastro_window, text="Senha*",
             bg="#000F1A",
             fg="light gray",
             font=("Helvetica", 9, "bold"),
             width=7,
             height=1,
             pady=4, padx=1
             ).pack()
    entry_senha_cad = tk.Entry(cadastro_window, show=">",
                               fg="black",
                               relief="flat",
                               highlightbackground="#001427",
                               highlightcolor="#00ADB5",
                               highlightthickness=2,
                               insertbackground="black", justify="center"
                               )
    entry_senha_cad.pack()

    tk.Label(cadastro_window, text="Bloco",
             bg="#000F1A",
             fg="light gray",
             font=("Helvetica", 9, "bold"),
             width=7,
             height=1,
             pady=4, padx=1
             ).pack()
    entry_bloco = tk.Entry(cadastro_window,
                           fg="black",
                           relief="flat",
                           highlightbackground="#001427",
                           highlightcolor="#00ADB5",
                           highlightthickness=2,
                           insertbackground="black", justify="center"
                           )
    entry_bloco.pack()

    tk.Label(cadastro_window, text="Número do AP",
             bg="#000F1A",
             fg="light gray",
             font=("Helvetica", 9, "bold"),
             width=27,
             height=1,
             pady=4, padx=1
             ).pack()
    entry_numero_ap = tk.Entry(cadastro_window,
                               fg="black",
                               relief="flat",
                               highlightbackground="#001427",
                               highlightcolor="#00ADB5",
                               highlightthickness=2,
                               insertbackground="black", justify="center"
                               )
    entry_numero_ap.pack()

    tk.Label(cadastro_window, text="Email*",
             bg="#000F1A",
             fg="light gray",
             font=("Helvetica", 9, "bold"),
             width=7,
             height=1,
             pady=4, padx=1
             ).pack()
    entry_email = tk.Entry(cadastro_window,
                           fg="black",
                           relief="flat",
                           highlightbackground="#001427",
                           highlightcolor="#00ADB5",
                           highlightthickness=2,
                           insertbackground="black", justify="center"
                           )
    entry_email.pack()
    tk.Label(cadastro_window, text="* Campos obrigatórios",
             font=("Arial", 6, "bold"),
             bg="#001F3F",
             fg="white",
             relief="raised",
             width=16,
             height=1,
             pady=5, padx=4, cursor="heart"
             ).pack(pady=5)

    def cadastrar_pessoa():
        try:
            cpf_str = entry_cpf.get().strip()
            login = entry_login_cad.get().strip()
            nome = entry_nome.get().strip()
            senha = entry_senha_cad.get().strip()
            bloco_str = entry_bloco.get().strip()
            numero_ap_str = entry_numero_ap.get().strip()
            email = entry_email.get().strip()

            if not all([cpf_str, login, nome, senha, email, bloco_str, numero_ap_str]):
                messagebox.showwarning("Campos obrigatórios", "Preencha todos os campos obrigatórios.",
                                       parent=cadastro_window)
                return
            if not validar_cpf(cpf_str):
                messagebox.showerror("Erro", "CPF inválido.", parent=cadastro_window)
                return
            if not validar_nome(nome):
                messagebox.showerror("Erro", "Nome inválido. Use letras e espaços (8-20 caracteres).",
                                     parent=cadastro_window)
                return
            if not validar_login(login):
                messagebox.showerror("Erro", "Login inválido. Use 8-20 caracteres alfanuméricos.",
                                     parent=cadastro_window)
                return
            if not validar_senha(senha):
                messagebox.showerror("Erro", "Senha deve ter entre 8 e 20 caracteres.", parent=cadastro_window)
                return
            if not validar_email(email):
                messagebox.showerror("Erro", "E-mail inválido.", parent=cadastro_window)
                return
            if not validar_3dig(bloco_str):
                messagebox.showerror("Erro", "Bloco deve ser entre 1 e 999.", parent=cadastro_window)
                return
            if not validar_3dig(numero_ap_str):
                messagebox.showerror("Erro", "Número do AP deve ser entre 1 e 999.", parent=cadastro_window)
                return

            cpf = cpf_str
            bloco = int(bloco_str)
            numero_ap = int(numero_ap_str)

            pessoa = Cadastro(
                cpf=cpf, login=login, nome=nome, senha=senha,
                bloco=bloco, numero_ap=numero_ap, email=email,
                data_cadastro=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )
            bd.inserir_pessoa(pessoa, cpf_adm=cpf_adm_executor)
            messagebox.showinfo("Sucesso", "Usuário cadastrado com sucesso!", parent=cadastro_window)
            cadastro_window.destroy()
            mostrar_usuarios(root, cpf_adm_executor)
        except ValueError as ve:
            messagebox.showerror("Erro de Validação", str(ve), parent=cadastro_window)
        except Exception as e:
            messagebox.showerror("Erro Inesperado", f"Erro ao cadastrar: {e}", parent=cadastro_window)

    tk.Button(cadastro_window, text="Cadastrar Usuário", command=cadastrar_pessoa,
              font=("Arial", 9, "bold"),
              bg="#001F3F",
              fg="white",
              activebackground="#003366",
              activeforeground="white",
              relief="raised",

              height=1,
              pady=4, padx=4, cursor="hand2"
              ).pack(pady=10)


def mostrar_adms(root, cpf_adm_executor):
    """Exibe a lista de administradores e permite ações de ADM."""
    print(f"[ADM DEBUG] Entrando em mostrar_adms com ADM CPF: {cpf_adm_executor}")
    if not bd.conn:
        if not bd.conectar():
            messagebox.showerror("Erro Crítico", "Não foi possível conectar ao banco de dados.")
            return
        bd.criar_tabelas()

    if bd.conn:
        try:
            adms_list = bd.listar_adms()

            for widget in root.winfo_children():
                widget.destroy()
                from interface import set_root
                set_root(root)

            janela_adms = root
            janela_adms.title("Painel do Administrador - Gerenciar Administradores")
            janela_adms.geometry("700x600+300+1")
            janela_adms.configure(bg="#000F1A")

            tk.Label(janela_adms, text="Gerenciar Administradores", font=("Helvetica", 14, "bold"),
                     bg="#000F1A",
                     fg="white"
                     ).pack(pady=10)

            list_frame = tk.Frame(janela_adms, bg="#000F1A")
            list_frame.pack(fill="both", expand=True, padx=10, pady=5)
            canvas = tk.Canvas(list_frame)
            scrollbar = tk.Scrollbar(list_frame, orient="vertical", command=canvas.yview)
            scrollable_frame = tk.Frame(canvas)
            scrollable_frame.bind("<Configure>", lambda a: canvas.configure(scrollregion=canvas.bbox("all")))
            canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
            canvas.configure(yscrollcommand=scrollbar.set)

            if not adms_list:
                tk.Label(scrollable_frame, text="Nenhum administrador cadastrado.", bg="#AAAAAA").pack(pady=20)
            else:
                for adm_data in adms_list:
                    cpf_adm_alvo, nome_adm, login_adm, data_cadastro_adm = adm_data
                    adm_frame = tk.Frame(scrollable_frame, borderwidth=1, relief="solid", bg="#AAAAAA")
                    adm_frame.pack(fill="x", padx=5, pady=3)

                    info = f"{nome_adm} | CPF: {cpf_adm_alvo} | Login: {login_adm}"
                    tk.Label(adm_frame, text=info, anchor="w", bg="#AAAAAA").pack(side="left", padx=5)
                    if cpf_adm_alvo != cpf_adm_executor:
                        tk.Button(adm_frame, text="Excluir",
                                  command=lambda c=cpf_adm_alvo, execu=cpf_adm_executor: excluir_adm(root, execu, c),
                                  fg="dark red", bg="light gray").pack(side="right", padx=2)

                        tk.Button(adm_frame, text="Editar",
                                  command=lambda c=cpf_adm_alvo, execu=cpf_adm_executor: editar_adm(root, execu, c),
                                  fg="dark green", bg="light gray").pack(side="right", padx=2)
                    else:
                        tk.Label(adm_frame, text="(Você)", bg="#AAAAAA", fg="purple").pack(side="right", padx=5)

            canvas.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")

            action_frame = tk.Frame(janela_adms, bg="#000F1A")
            action_frame.pack(pady=10)
            tk.Button(action_frame, text="Cadastrar Novo ADM",
                      command=lambda adm_exec=cpf_adm_executor: abrir_cadastro_adm(root, adm_exec),
                      font=("Arial", 9, "bold"),
                      bg="#001F3F",
                      fg="white",
                      activebackground="#003366",
                      activeforeground="white",
                      relief="raised",
                      height=1,
                      pady=4, padx=4, cursor="hand2"
                      ).pack(side="left", padx=5)

            tk.Button(action_frame, text="Gerenciar Usuários",
                      command=lambda adm_exec=cpf_adm_executor: mostrar_usuarios(root, adm_exec),
                      font=("Arial", 9, "bold"),
                      bg="#001F3F",
                      fg="white",
                      activebackground="#003366",
                      activeforeground="white",
                      relief="raised",
                      height=1,
                      pady=4, padx=4, cursor="hand2"
                      ).pack(side="left", padx=5)
            from interface import reiniciar_para_login
            try:

                tk.Button(janela_adms, text="Logout", command=reiniciar_para_login,
                          font=("Arial", 9, "bold"),
                          bg="#001F3F",
                          fg="white",
                          activebackground="#003366",
                          activeforeground="white",
                          relief="raised",
                          width=10,
                          height=1,
                          pady=4, padx=4, cursor="hand2"
                          ).pack(pady=10)
            except ImportError:
                tk.Button(janela_adms, text="Fechar Painel ADM", command=root.destroy).pack(pady=10)


        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao buscar administradores: {e}")
            print(f"[ADM ERROR] Erro em mostrar_adms: {e}")


def editar_adm(root, cpf_adm_executor, cpf_adm_alvo):
    """Abre a janela para editar os dados de um administrador."""
    print(f"[ADM DEBUG] Iniciando edição do ADM CPF {cpf_adm_alvo} pelo ADM CPF {cpf_adm_executor}")
    if not bd.conn:
        if not bd.conectar(): messagebox.showerror("Erro", "Sem conexão com banco."); return

    if bd.conn:
        cursor = bd.conn.cursor()
        try:
            cursor.execute("SELECT nome, login FROM Adm WHERE cpf = ?", (str(cpf_adm_alvo),))
            adm_atual = cursor.fetchone()
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao buscar dados do ADM: {e}")
            return

        if not adm_atual:
            messagebox.showerror("Erro", "Administrador não encontrado.")
            return

        nome_atual, login_atual = adm_atual

        janela_editar = tk.Toplevel(root)
        janela_editar.title(f"Editar Administrador - CPF: {cpf_adm_alvo}")
        janela_editar.geometry("350x300+500+100")
        janela_editar.configure(bg="#000F1A")
        janela_editar.transient(root)
        janela_editar.grab_set()

        tk.Label(janela_editar, text="Nome*",
                 bg="#000F1A",
                 fg="light gray",
                 font=("Helvetica", 9, "bold"),
                 width=7,
                 height=1,
                 pady=4, padx=1
                 ).pack()
        entry_nome = tk.Entry(janela_editar,
                              fg="black",
                              relief="flat",
                              highlightbackground="#001427",
                              highlightcolor="#00ADB5",
                              highlightthickness=2,
                              insertbackground="black", justify="center"
                              )
        entry_nome.insert(0, nome_atual)
        entry_nome.pack()

        tk.Label(janela_editar, text="Login*",
                 bg="#000F1A",
                 fg="light gray",
                 font=("Helvetica", 9, "bold"),
                 width=7,
                 height=1,
                 pady=4, padx=1
                 ).pack()
        entry_login = tk.Entry(janela_editar,
                               fg="black",
                               relief="flat",
                               highlightbackground="#001427",
                               highlightcolor="#00ADB5",
                               highlightthickness=2,
                               insertbackground="black", justify="center"
                               )
        entry_login.insert(0, login_atual)
        entry_login.pack()

        tk.Label(janela_editar, text="Nova Senha (deixe em branco para não alterar)",
                 bg="#000F1A",
                 fg="light gray",
                 font=("Helvetica", 9, "bold"),
                 height=1,
                 pady=4, padx=1
                 ).pack()
        entry_senha = tk.Entry(janela_editar, show=">",
                               fg="black",
                               relief="flat",
                               highlightbackground="#001427",
                               highlightcolor="#00ADB5",
                               highlightthickness=2,
                               insertbackground="black", justify="center"
                               )
        entry_senha.pack()
        tk.Label(janela_editar, text="* Campos obrigatórios",
                 font=("Arial", 6, "bold"),
                 bg="#001F3F",
                 fg="white",
                 relief="raised",
                 width=16,
                 height=1,
                 pady=5, padx=4, cursor="heart"
                 ).pack(pady=5)

        def salvar_adm():
            novo_nome = entry_nome.get()
            novo_login = entry_login.get()
            nova_senha = entry_senha.get()
            if not novo_nome or not novo_login:
                messagebox.showwarning("Campos Obrigatórios", "Nome e Login são obrigatórios.", parent=janela_editar)
                return

            if messagebox.askyesno("Confirmar Alterações", "Salvar mudanças para este administrador?",
                                   parent=janela_editar):
                try:

                    success = bd.atualizar_adm(cpf_adm_executor=cpf_adm_executor,
                                               cpf_adm_alvo=str(cpf_adm_alvo),
                                               novo_nome=novo_nome,
                                               novo_login=novo_login,
                                               nova_senha=nova_senha if nova_senha else None)
                    if success:
                        messagebox.showinfo("Sucesso", "Administrador atualizado!", parent=janela_editar)
                        janela_editar.destroy()
                        mostrar_adms(root, cpf_adm_executor)
                    else:

                        messagebox.showerror("Erro", "Falha ao atualizar administrador (não encontrado?).",
                                             parent=janela_editar)
                except ValueError as ve:
                    messagebox.showerror("Erro de Validação", str(ve), parent=janela_editar)
                except Exception as v:
                    messagebox.showerror("Erro Inesperado", f"Erro ao atualizar ADM: {v}", parent=janela_editar)

        tk.Button(janela_editar, text="Salvar Alterações", command=salvar_adm,
                  font=("Arial", 9, "bold"),
                  bg="#001F3F",
                  fg="white",
                  activebackground="#003366",
                  activeforeground="white",
                  relief="raised",
                  height=1,
                  pady=4, padx=4, cursor="hand2"
                  ).pack(pady=20)


def excluir_adm(root, cpf_adm_executor, cpf_adm_alvo):
    """Exclui um administrador."""
    print(f"[ADM DEBUG] Iniciando exclusão do ADM CPF {cpf_adm_alvo} pelo ADM CPF {cpf_adm_executor}")
    if cpf_adm_executor == cpf_adm_alvo:
        messagebox.showerror("Erro", "Você não pode excluir sua própria conta.")
        return

    if messagebox.askyesno("Confirmar Exclusão", f"Excluir o administrador CPF {cpf_adm_alvo}?", icon='warning'):
        if not bd.conn:
            if not bd.conectar(): messagebox.showerror("Erro", "Sem conexão com banco."); return
        try:

            bd.deletar_adm(cpf_adm_executor=cpf_adm_executor, cpf_adm_alvo=str(cpf_adm_alvo))

            messagebox.showinfo("Sucesso", f"Administrador CPF {cpf_adm_alvo} excluído.")
            mostrar_adms(root, cpf_adm_executor)

        except ValueError as ve:
            messagebox.showerror("Erro de Validação", str(ve))
        except sqlite3.Error as db_err:
            print(f"[ADM ERROR] Erro SQLite em excluir_adm: {db_err}")
            messagebox.showerror("Erro de Banco", f"Erro ao tentar excluir ADM: {db_err}")
        except Exception as e:
            print(f"[ADM ERROR] Exceção inesperada em excluir_adm: {e}")
            messagebox.showerror("Erro Inesperado", f"Erro inesperado na exclusão do ADM: {e}")


def abrir_cadastro_adm(root, cpf_adm_executor):
    """Abre a janela para um ADM cadastrar outro ADM."""
    print(f"[ADM DEBUG] Abrindo cadastro de ADM pelo ADM CPF: {cpf_adm_executor}")
    cadastro_window = tk.Toplevel(root)
    cadastro_window.title("Cadastrar Administrador")
    cadastro_window.geometry("350x300+500+100")
    cadastro_window.transient(root)
    cadastro_window.grab_set()
    cadastro_window.configure(bg="#000F1A")

    tk.Label(cadastro_window, text="CPF*",
             bg="#000F1A",
             fg="light gray",
             font=("Helvetica", 9, "bold"),
             width=7,
             height=1,
             pady=4, padx=1
             ).pack()
    entry_cpf = tk.Entry(cadastro_window,
                         fg="black",
                         relief="flat",
                         highlightbackground="#001427",
                         highlightcolor="#00ADB5",
                         highlightthickness=2,
                         insertbackground="black", justify="center"
                         )
    entry_cpf.pack()

    tk.Label(cadastro_window, text="Login*",
             bg="#000F1A",
             fg="light gray",
             font=("Helvetica", 9, "bold"),
             width=7,
             height=1,
             pady=4, padx=1
             ).pack()
    entry_login_cad = tk.Entry(cadastro_window,
                               fg="black",
                               relief="flat",
                               highlightbackground="#001427",
                               highlightcolor="#00ADB5",
                               highlightthickness=2,
                               insertbackground="black", justify="center"
                               )
    entry_login_cad.pack()

    tk.Label(cadastro_window, text="Nome*",
             bg="#000F1A",
             fg="light gray",
             font=("Helvetica", 9, "bold"),
             width=7,
             height=1,
             pady=4, padx=1
             ).pack()
    entry_nome = tk.Entry(cadastro_window,
                          fg="black",
                          relief="flat",
                          highlightbackground="#001427",
                          highlightcolor="#00ADB5",
                          highlightthickness=2,
                          insertbackground="black", justify="center"
                          )
    entry_nome.pack()

    tk.Label(cadastro_window, text="Senha*",
             bg="#000F1A",
             fg="light gray",
             font=("Helvetica", 9, "bold"),
             width=7,
             height=1,
             pady=4, padx=1
             ).pack()
    entry_senha_cad = tk.Entry(cadastro_window, show=">",
                               fg="black",
                               relief="flat",
                               highlightbackground="#001427",
                               highlightcolor="#00ADB5",
                               highlightthickness=2,
                               insertbackground="black", justify="center"
                               )
    entry_senha_cad.pack()

    tk.Label(cadastro_window, text="* Campos obrigatórios",
             font=("Arial", 6, "bold"),
             bg="#001F3F",
             fg="white",
             relief="raised",
             width=16,
             height=1,
             pady=5, padx=4, cursor="heart"
             ).pack(pady=5)

    def cadastrar():
        try:
            cpf_str = entry_cpf.get().strip()
            login = entry_login_cad.get().strip()
            nome = entry_nome.get().strip()
            senha = entry_senha_cad.get().strip()

            if not all([cpf_str, login, nome, senha]):
                messagebox.showwarning("Campos obrigatórios", "Preencha todos os campos obrigatórios.",
                                       parent=cadastro_window)
                return
            if not validar_cpf(cpf_str):
                messagebox.showerror("Erro", "CPF inválido.", parent=cadastro_window)
                return
            if not validar_nome(nome):
                messagebox.showerror("Erro", "Nome inválido. Use letras e espaços (8-20 caracteres).",
                                     parent=cadastro_window)
                return
            if not validar_login(login):
                messagebox.showerror("Erro", "Login inválido. Use 8-20 caracteres alfanuméricos.",
                                     parent=cadastro_window)
                return
            if not validar_senha(senha):
                messagebox.showerror("Erro", "Senha deve ter entre 8 e 20 caracteres.", parent=cadastro_window)
                return

            cpf = int(cpf_str)
            novo_adm = CadastroAdm(
                cpf=cpf, login=login, nome=nome, senha=senha,
                data_cadastro=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )
            bd.inserir_adm(novo_adm)
            messagebox.showinfo("Sucesso", "Administrador cadastrado com sucesso!", parent=cadastro_window)
            cadastro_window.destroy()
            if root.title().startswith("Painel do Administrador - Gerenciar Administradores"):
                mostrar_adms(root, cpf_adm_executor)

        except ValueError as ve:
            messagebox.showerror("Erro de Validação", str(ve), parent=cadastro_window)
        except Exception as e:
            messagebox.showerror("Erro Inesperado", f"Erro inesperado no cadastro ADM: {e}", parent=cadastro_window)

    tk.Button(cadastro_window, text="Cadastrar ADM", command=cadastrar,
              font=("Arial", 9, "bold"),
              bg="#001F3F",
              fg="white",
              activebackground="#003366",
              activeforeground="white",
              relief="raised",
              height=1,
              pady=4, padx=4, cursor="hand2"
              ).pack(pady=10)


def exportar_logs_para_txt():
    """Exporta os logs do banco para um arquivo de texto e o abre."""
    print("[ADM DEBUG] Iniciando exportação de logs.")
    if not bd.conn:
        if not bd.conectar(): messagebox.showerror("Erro", "Sem conexão com banco.")
        return
    try:
        cursor = bd.conn.cursor()
        adms = {row[0]: row[1] for row in cursor.execute("SELECT cpf, nome FROM Adm").fetchall()}
        current_users = {row[0]: row[1] for row in cursor.execute("SELECT cpf, nome FROM Pessoa").fetchall()}
        cursor.execute("SELECT id, cpf_adm, cpf_alvo, acao, data_hora FROM Log ORDER BY data_hora DESC")
        logs = cursor.fetchall()
        if not logs:
            messagebox.showinfo("Logs", "Nenhum log encontrado.")
            return
        log_dir = os.path.join(os.path.dirname(__file__), "logs")
        os.makedirs(log_dir, exist_ok=True)
        nome_arquivo = os.path.join(log_dir, "event_log.txt")
        with open(nome_arquivo, "w", encoding="utf-8") as f:
            f.write("---- LOGS DE EVENTOS DO SISTEMA ----\n\n")
            for log in logs:
                id_log, cpf_adm_log, cpf_alvo_log, acao, data_hora = log
                adm_display = adms.get(cpf_adm_log, f"ADM CPF {cpf_adm_log}") if cpf_adm_log else "Sistema/Usuário"
                if cpf_alvo_log:
                    user_name = current_users.get(cpf_alvo_log)
                    target_display = f"{user_name} (CPF: {cpf_alvo_log})" if user_name else f"Usuário Excluído (CPF: {cpf_alvo_log})"
                else:

                    if "ADM" in acao:
                        target_display = "N/A (Ação do ADM)"
                    elif cpf_adm_log is None:
                        target_display = "Próprio Usuário"
                    else:
                        target_display = "N/A"

                f.write(f"[{data_hora}] ID:{id_log} | Ação: {acao}\n")
                f.write(f"  Executor: {adm_display} | Alvo: {target_display}\n")
                f.write("-" * 40 + "\n")
        messagebox.showinfo("Logs Exportados", f"Logs salvos em: {nome_arquivo}")
        try:
            sistema = platform.system()
            if sistema == "Windows":
                os.startfile(nome_arquivo)
            elif sistema == "Darwin":
                subprocess.call(["open", nome_arquivo])
            else:
                subprocess.call(["xdg-open", nome_arquivo])
        except Exception as open_e:
            messagebox.showwarning("Abrir Log", f"Não foi possível abrir o log: {open_e}.")
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao exportar logs: {e}")
        print(f"[ADM ERROR] Erro em exportar_logs_para_txt: {e}")
