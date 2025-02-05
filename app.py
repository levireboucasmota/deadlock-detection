import tkinter as tk
from tkinter import ttk, messagebox

from classes import Processo, SistemaOperacional

class InterfaceGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Simulador de Deadlock")

        self.recursos = []
        self.processos = []
        self.sistema_operacional = None
        self.log_text = tk.Text(root, wrap=tk.WORD, height=15, width=60)
        self.log_text.pack(pady=10)

        self.frame_controles = tk.Frame(root)
        self.frame_controles.pack(pady=10)

        self.label_intervalo = tk.Label(self.frame_controles, text="Intervalo Verificação (s):")
        self.label_intervalo.grid(row=0, column=0, padx=5, pady=5)
        self.entry_intervalo = tk.Entry(self.frame_controles)
        self.entry_intervalo.grid(row=0, column=1, padx=5, pady=5)

        self.btn_iniciar = tk.Button(self.frame_controles, text="Iniciar Simulação", command=self.iniciar_simulacao)
        self.btn_iniciar.grid(row=0, column=2, padx=5, pady=5)

        self.btn_parar = tk.Button(self.frame_controles, text="Parar Simulação", command=self.parar_simulacao)
        self.btn_parar.grid(row=0, column=3, padx=5, pady=5)

        self.frame_adicionar = tk.Frame(root)
        self.frame_adicionar.pack(pady=10)

        self.label_tipo = tk.Label(self.frame_adicionar, text="Tipo:")
        self.label_tipo.grid(row=0, column=0, padx=5, pady=5)
        self.combo_tipo = ttk.Combobox(self.frame_adicionar, values=["Recurso", "Processo"])
        self.combo_tipo.grid(row=0, column=1, padx=5, pady=5)

        self.label_nome = tk.Label(self.frame_adicionar, text="Nome:")
        self.label_nome.grid(row=1, column=0, padx=5, pady=5)
        self.entry_nome = tk.Entry(self.frame_adicionar)
        self.entry_nome.grid(row=1, column=1, padx=5, pady=5)

        self.label_id = tk.Label(self.frame_adicionar, text="ID:")
        self.label_id.grid(row=2, column=0, padx=5, pady=5)
        self.entry_id = tk.Entry(self.frame_adicionar)
        self.entry_id.grid(row=2, column=1, padx=5, pady=5)

        self.label_quantidade = tk.Label(self.frame_adicionar, text="Quantidade:")
        self.label_quantidade.grid(row=3, column=0, padx=5, pady=5)
        self.entry_quantidade = tk.Entry(self.frame_adicionar)
        self.entry_quantidade.grid(row=3, column=1, padx=5, pady=5)

        self.label_intervalo_solicitacao = tk.Label(self.frame_adicionar, text="Intervalo Solicitação (s):")
        self.label_intervalo_solicitacao.grid(row=4, column=0, padx=5, pady=5)
        self.entry_intervalo_solicitacao = tk.Entry(self.frame_adicionar)
        self.entry_intervalo_solicitacao.grid(row=4, column=1, padx=5, pady=5)

        self.label_tempo_utilizacao = tk.Label(self.frame_adicionar, text="Tempo Utilização (s):")
        self.label_tempo_utilizacao.grid(row=5, column=0, padx=5, pady=5)
        self.entry_tempo_utilizacao = tk.Entry(self.frame_adicionar)
        self.entry_tempo_utilizacao.grid(row=5, column=1, padx=5, pady=5)

        self.btn_adicionar = tk.Button(self.frame_adicionar, text="Adicionar", command=self.adicionar_elemento)
        self.btn_adicionar.grid(row=6, column=0, columnspan=2, pady=10)

        self.frame_status = tk.Frame(root)
        self.frame_status.pack(pady=10)

        self.label_status = tk.Label(self.frame_status, text="Status dos Processos:")
        self.label_status.pack(pady=5)

        self.tree_status = ttk.Treeview(self.frame_status, columns=("Status", "Recursos Alocados", "Recursos Esperados"), show='headings')
        self.tree_status.heading("Status", text="Status")
        self.tree_status.heading("Recursos Alocados", text="Recursos Alocados")
        self.tree_status.heading("Recursos Esperados", text="Recursos Esperados")
        self.tree_status.pack(pady=5)

        self.label_recursos = tk.Label(self.frame_status, text="Recursos:")
        self.label_recursos.pack(pady=5)

        self.tree_recursos = ttk.Treeview(self.frame_status, columns=("Disponível", "Total"), show='headings')
        self.tree_recursos.heading("Disponível", text="Disponível")
        self.tree_recursos.heading("Total", text="Total")
        self.tree_recursos.pack(pady=5)

    def adicionar_elemento(self):
        tipo = self.combo_tipo.get()
        nome = self.entry_nome.get()
        id_elemento = self.entry_id.get()
        quantidade = int(self.entry_quantidade.get()) if self.entry_quantidade.get().isdigit() else 0
        intervalo_solicitacao = float(self.entry_intervalo_solicitacao.get()) if self.entry_intervalo_solicitacao.get().replace('.', '', 1).isdigit() else 0
        tempo_utilizacao = float(self.entry_tempo_utilizacao.get()) if self.entry_tempo_utilizacao.get().replace('.', '', 1).isdigit() else 0

        if tipo == "Recurso":
            recurso = recurso(nome, id_elemento, quantidade)
            self.recursos.append(recurso)
            self.atualizar_tree_recursos()
        elif tipo == "Processo":
            processo = Processo(id_elemento, self.recursos, intervalo_solicitacao, tempo_utilizacao, self.atualizar_log)
            self.processos.append(processo)
            self.atualizar_tree_status()

    def iniciar_simulacao(self):
        intervalo_verificacao = float(self.entry_intervalo.get()) if self.entry_intervalo.get().replace('.', '', 1).isdigit() else 1
        if not self.recursos or not self.processos:
            messagebox.showwarning("Aviso", "Adicione pelo menos um recurso e um processo antes de iniciar a simulação.")
            return
        self.sistema_operacional = SistemaOperacional(self.recursos, self.processos, intervalo_verificacao, self.atualizar_log, self.atualizar_matrizes)
        self.sistema_operacional.start()
        for processo in self.processos:
            processo.start()

    def parar_simulacao(self):
        if self.sistema_operacional:
            self.sistema_operacional.parar()
            self.sistema_operacional.join()
            self.sistema_operacional = None
        for processo in self.processos:
            processo.parar()
            processo.join()

    def atualizar_log(self, mensagem):
        self.log_text.insert(tk.END, mensagem + "\n")
        self.log_text.see(tk.END)

    def atualizar_tree_status(self):
        self.tree_status.delete(*self.tree_status.get_children())
        for processo in self.processos:
            recursos_alocados = ", ".join([f"{k}: {v}" for k, v in processo.recursos_alocados.items()])
            recursos_esperados = ", ".join([f"{k}: {v}" for k, v in processo.recursos_requisitados.items()])
            self.tree_status.insert("", tk.END, values=(processo.status, recursos_alocados, recursos_esperados))

    def atualizar_tree_recursos(self):
        self.tree_recursos.delete(*self.tree_recursos.get_children())
        for recurso in self.recursos:
            self.tree_recursos.insert("", tk.END, values=(recurso.disponivel, recurso.quantidade))

    def atualizar_matrizes(self):
        self.atualizar_tree_status()
        self.atualizar_tree_recursos()

if __name__ == "__main__":
    root = tk.Tk()
    app = InterfaceGUI(root)
    root.mainloop()