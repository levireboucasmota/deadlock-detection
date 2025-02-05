import tkinter as tk
from tkinter import messagebox
from classes import Recurso, SistemaOperacional, Processo

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Simulação de Deadlocks")

        # Listas para recursos e processos
        self.recursos = []
        self.processos = []
        self.so = None

        # Frame de entrada de dados (lado esquerdo)
        self.frame_entrada = tk.Frame(root)
        self.frame_entrada.grid(row=0, column=0, padx=5, pady=5, sticky="n")

        # Recursos
        tk.Label(self.frame_entrada, text="Nome do Recurso:").grid(row=0, column=0, sticky="w")
        self.entry_nome_recurso = tk.Entry(self.frame_entrada, width=20)
        self.entry_nome_recurso.grid(row=0, column=1)

        tk.Label(self.frame_entrada, text="ID do Recurso:").grid(row=1, column=0, sticky="w")
        self.entry_id_recurso = tk.Entry(self.frame_entrada, width=20)
        self.entry_id_recurso.grid(row=1, column=1)

        tk.Label(self.frame_entrada, text="Quantidade:").grid(row=2, column=0, sticky="w")
        self.entry_quantidade_recurso = tk.Entry(self.frame_entrada, width=20)
        self.entry_quantidade_recurso.grid(row=2, column=1)

        # Botão "Adicionar Recurso" com mais espaço acima
        tk.Button(self.frame_entrada, text="Adicionar Recurso", command=self.adicionar_recurso).grid(
            row=3, column=0, columnspan=2, pady=(10, 2)
        )

        # Processos
        tk.Label(self.frame_entrada, text="ID do Processo:").grid(row=4, column=0, sticky="w")
        self.entry_id_processo = tk.Entry(self.frame_entrada, width=20)
        self.entry_id_processo.grid(row=4, column=1)

        tk.Label(self.frame_entrada, text="Intervalo de Solicitação (s):").grid(row=5, column=0, sticky="w")
        self.entry_intervalo_processo = tk.Entry(self.frame_entrada, width=20)
        self.entry_intervalo_processo.grid(row=5, column=1)

        tk.Label(self.frame_entrada, text="Tempo de Utilização (s):").grid(row=6, column=0, sticky="w")
        self.entry_tempo_utilizacao = tk.Entry(self.frame_entrada, width=20)
        self.entry_tempo_utilizacao.grid(row=6, column=1)

        # Botão "Adicionar Processo" com mais espaço acima
        tk.Button(self.frame_entrada, text="Adicionar Processo", command=self.adicionar_processo).grid(
            row=7, column=0, columnspan=2, pady=(10, 2)
        )

        # Remoção de processos
        tk.Label(self.frame_entrada, text="ID do Processo para Remover:").grid(row=8, column=0, sticky="w")
        self.entry_remover_processo = tk.Entry(self.frame_entrada, width=20)
        self.entry_remover_processo.grid(row=8, column=1)

        # Botão "Remover Processo" com mais espaço acima
        tk.Button(self.frame_entrada, text="Remover Processo", command=self.remover_processo).grid(
            row=9, column=0, columnspan=2, pady=(10, 2)
        )

        # Configuração do SO
        tk.Label(self.frame_entrada, text="Intervalo de Verificação (s):").grid(row=10, column=0, sticky="w")
        self.entry_intervalo_verificacao = tk.Entry(self.frame_entrada, width=20)
        self.entry_intervalo_verificacao.grid(row=10, column=1)

        # Botões "Iniciar Simulação" e "Parar Simulação" com mais espaço acima
        tk.Button(self.frame_entrada, text="Iniciar Simulação", command=self.iniciar_simulacao).grid(
            row=11, column=0, columnspan=2, pady=(10, 2)
        )
        tk.Button(self.frame_entrada, text="Parar Simulação", command=self.parar_simulacao).grid(
            row=12, column=0, columnspan=2, pady=(10, 2)
        )

        # Área de log (na parte inferior da esquerda)
        tk.Label(self.frame_entrada, text="Log:").grid(row=13, column=0, sticky="w", pady=(10, 0))
        self.log_text = tk.Text(self.frame_entrada, height=15, width=50)  # Aumentado o tamanho
        self.log_text.grid(row=14, column=0, columnspan=2, pady=2)

        # Frame para exibição das matrizes (lado direito)
        self.frame_matrizes = tk.Frame(root)
        self.frame_matrizes.grid(row=0, column=1, padx=5, pady=5, sticky="n")

        # Matriz de Recursos Existentes
        tk.Label(self.frame_matrizes, text="Recursos Existentes").grid(row=0, column=0, sticky="w")
        self.txt_recursos_existentes = tk.Text(self.frame_matrizes, height=10, width=40)  # Aumentado o tamanho
        self.txt_recursos_existentes.grid(row=1, column=0, pady=2)

        # Matriz de Recursos Disponíveis
        tk.Label(self.frame_matrizes, text="Recursos Disponíveis").grid(row=2, column=0, sticky="w")
        self.txt_recursos_disponiveis = tk.Text(self.frame_matrizes, height=10, width=40)  # Aumentado o tamanho
        self.txt_recursos_disponiveis.grid(row=3, column=0, pady=2)

        # Processos – Recursos Alocados
        tk.Label(self.frame_matrizes, text="Processos - Recursos Alocados").grid(row=4, column=0, sticky="w")
        self.txt_processos_alocados = tk.Text(self.frame_matrizes, height=10, width=40)  # Aumentado o tamanho
        self.txt_processos_alocados.grid(row=5, column=0, pady=2)

        # Processos Bloqueados – Recursos Aguardados
        tk.Label(self.frame_matrizes, text="Processos Bloqueados - Recursos Aguardados").grid(row=6, column=0, sticky="w")
        self.txt_processos_bloqueados = tk.Text(self.frame_matrizes, height=10, width=40)  # Aumentado o tamanho
        self.txt_processos_bloqueados.grid(row=7, column=0, pady=2)

        # Status dos Processos
        tk.Label(self.frame_matrizes, text="Status dos Processos").grid(row=8, column=0, sticky="w")
        self.txt_status_processos = tk.Text(self.frame_matrizes, height=10, width=40)  # Aumentado o tamanho
        self.txt_status_processos.grid(row=9, column=0, pady=2)

        # Inicia a atualização periódica das matrizes
        self.atualizar_matrizes()

    def adicionar_recurso(self):
        nome = self.entry_nome_recurso.get()
        id_recurso = self.entry_id_recurso.get()
        quantidade = self.entry_quantidade_recurso.get()
        if nome and id_recurso.isdigit() and quantidade.isdigit():
            self.recursos.append(Recurso(nome, int(id_recurso), int(quantidade), self.atualizar_log))
            self.atualizar_log(f"Recurso {nome} adicionado.")
        else:
            messagebox.showerror("Erro", "Preencha os campos de recurso corretamente.")

    def adicionar_processo(self):
        id_processo = self.entry_id_processo.get()
        intervalo = self.entry_intervalo_processo.get()
        tempo_utilizacao = self.entry_tempo_utilizacao.get()
        if id_processo.isdigit() and intervalo.isdigit() and tempo_utilizacao.isdigit():
            processo = Processo(
                id=int(id_processo),
                delta_ts=int(intervalo),
                delta_tu=int(tempo_utilizacao),
                recursos=self.recursos,
                atualizar_log=self.atualizar_log
            )
            self.processos.append(processo)
            self.atualizar_log(f"Processo {id_processo} adicionado.")
        else:
            messagebox.showerror("Erro", "Preencha os campos de processo corretamente.")

    def remover_processo(self):
        id_remover = self.entry_remover_processo.get()
        if not id_remover.isdigit():
            messagebox.showerror("Erro", "Digite um ID válido para remoção.")
            return
        id_remover = int(id_remover)
        processo = next((p for p in self.processos if p.id == id_remover), None)
        if processo:
            processo.finalizar()  # Finaliza a thread do processo
            self.processos.remove(processo)
            self.atualizar_log(f"Processo {id_remover} removido.")
        else:
            messagebox.showerror("Erro", "Processo não encontrado.")

    def iniciar_simulacao(self):
        if not self.recursos or not self.processos:
            messagebox.showerror("Erro", "Adicione pelo menos um recurso e um processo.")
            return
        intervalo_verificacao = self.entry_intervalo_verificacao.get()
        if not intervalo_verificacao.isdigit():
            messagebox.showerror("Erro", "Preencha o intervalo de verificação corretamente.")
            return
        self.so = SistemaOperacional(self.recursos, int(intervalo_verificacao), self.atualizar_log)
        self.so.start()
        for processo in self.processos:
            processo.start()
        self.atualizar_log("Simulação iniciada.")

    def parar_simulacao(self):
        if self.so:
            for processo in self.processos:
                processo.finalizar()
            self.so.parar()
            self.atualizar_log("Simulação encerrada.")

    def atualizar_log(self, mensagem):
        self.log_text.insert(tk.END, mensagem + "\n")
        self.log_text.see(tk.END)

    def atualizar_matrizes(self):
        # Recursos Existentes
        self.txt_recursos_existentes.delete("1.0", tk.END)
        for r in self.recursos:
            self.txt_recursos_existentes.insert(tk.END, f"{r.nome}: {r.quantidade_total}\n")

        # Recursos Disponíveis
        self.txt_recursos_disponiveis.delete("1.0", tk.END)
        for r in self.recursos:
            self.txt_recursos_disponiveis.insert(tk.END, f"{r.nome}: {r.quantidade_disponivel}\n")

        # Processos com Recursos Alocados
        self.txt_processos_alocados.delete("1.0", tk.END)
        for p in self.processos:
            recursos_alocados = ", ".join([r.nome for r, _ in p.recursos_alocados])
            self.txt_processos_alocados.insert(tk.END, f"Processo {p.id}: {recursos_alocados or '-'}\n")

        # Processos Bloqueados – Recursos Aguardados
        self.txt_processos_bloqueados.delete("1.0", tk.END)
        for p in self.processos:
            if p.status == "bloqueado":
                self.txt_processos_bloqueados.insert(tk.END, f"Processo {p.id}: aguardando recurso\n")

        # Status dos Processos
        self.txt_status_processos.delete("1.0", tk.END)
        for p in self.processos:
            self.txt_status_processos.insert(tk.END, f"Processo {p.id}: {p.status}\n")

        # Atualiza novamente após 1 segundo
        self.root.after(1000, self.atualizar_matrizes)

if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()