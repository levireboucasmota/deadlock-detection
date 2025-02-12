import tkinter as tk
from tkinter import messagebox
import threading
from threading import Thread, Semaphore
import time
import random

mutexProcesso = Semaphore(1)

class Recurso:
    def __init__(self, nome, id, instancias):
        self.nome = nome
        self.id = id
        self.instancias_totais = instancias
        self.instancias = Semaphore(instancias)
        self.instancias_disponiveis = instancias

class Processo(threading.Thread):
    global recursos

    def __init__(self, id, delta_s, delta_u, log):
        super().__init__()
        self.id = id
        self.tempo_solicitacao = delta_s
        self.tempo_utilizacao = delta_u
        self.tempo = 0
        self.updates = []
        self.utiliza = [0] * len(recursos)
        self.solicita = [0] * len(recursos)
        self.log = log
        self._stop = threading.Event()  

    def run(self):
        while not self._stop.is_set():  
            for i in range(self.tempo_solicitacao):
                if self._stop.is_set():  
                    break
                self.atualizar_tempo()

            if self._stop.is_set(): 
                break

            recurso = random.choice(recursos)

            if (self.utiliza[recurso.id] + 1) < recurso.instancias_totais:

                self.solicita[recurso.id] += 1

                self.log(f"Processo {self.id} solicitou o recurso {recurso.nome} (Tempo: {self.tempo}s)")

                recurso.instancias.acquire()

                self.solicita[recurso.id] -= 1
                self.updates.append([self.tempo + self.tempo_utilizacao, recurso])

                mutexProcesso.acquire()
                recurso.instancias_disponiveis -= 1
                mutexProcesso.release()

                self.utiliza[recurso.id] += 1
                self.log(f"Processo {self.id} conseguiu o recurso {recurso.nome} (Tempo: {self.tempo}s)")

        self._liberar_recursos()
        self.log(f"Processo {self.id} terminou. (Tempo: {self.tempo})")

    def atualizar_tempo(self):
        time.sleep(1)
        self.tempo += 1

        if (self.updates) and (self.updates[0][0] == self.tempo):
            recurso = self.updates[0][1]
            recurso.instancias.release()
            mutexProcesso.acquire()
            recurso.instancias_disponiveis += 1
            mutexProcesso.release()

            self.utiliza[recurso.id] -= 1
            self.log(f"Processo {self.id} liberou o recurso {recurso.nome} (Tempo: {self.tempo}s)")
            self.updates.pop(0)

    def _liberar_recursos(self):
        for i in range(len(self.utiliza)):
            if self.utiliza[i] > 0:
                recurso = recursos[i]
                self.log(f"{self.utiliza[i]} instâncias do recurso {recurso.nome} foram liberadas. (Tempo: {self.tempo}s)")
                recurso.instancias.release(self.utiliza[i])
                mutexProcesso.acquire()
                recurso.instancias_disponiveis += self.utiliza[i]
                mutexProcesso.release()
                self.utiliza[i] = 0

    def parar(self):
        self._stop.set()  
        self._liberar_recursos()
        

class SistemaOperacional(Thread):
    global recursos, processos

    def __init__(self, processos, delta_v, log, atualizar_matrizes):
        super().__init__()
        self.processos = processos
        self.tempo_verificacao = delta_v
        self.log = log
        self.atualizar_matrizes = atualizar_matrizes
        self.running = False

    def run(self):
        self.running = True
        while self.running:
            time.sleep(self.tempo_verificacao)
            self.verificar_deadlock()
            self.atualizar_matrizes()  # Atualiza as matrizes 

    def verificar_deadlock(self):
        disponiveis = [recurso.instancias_disponiveis for recurso in recursos]
        alocacoes = [processo.utiliza[:] for processo in processos]  # Criando cópias para evitar mutação
        requisicoes = [processo.solicita[:] for processo in processos]
        deadlock = []

        while True:
            progresso = False 

            for requisicao in range(len(requisicoes)):
                if sum(requisicoes[requisicao]) == 0:
                    if sum(alocacoes[requisicao]) == 0:
                        continue

                # Verificar se TODOS os recursos que o processo precisa estão disponíveis
                disponivel = all(disponiveis[recurso] >= requisicoes[requisicao][recurso] for recurso in range(len(requisicoes[requisicao])))

                if disponivel:
                    # Libera os recursos do processo
                    disponiveis = [disponiveis[i] + alocacoes[requisicao][i] for i in range(len(disponiveis))]
                    alocacoes[requisicao] = [0] * len(disponiveis)
                    requisicoes[requisicao] = [0] * len(disponiveis)
                    progresso = True
                    break  # Recomeçar o loop para verificar novamente
            
            if not progresso:
                break  # Nenhum processo conseguiu ser atendido -> possível deadlock

        # Identificar processos que ainda possuem recursos alocados (estão em deadlock)
        for i in range(len(alocacoes)):
            if sum(alocacoes[i]) != 0:
                deadlock.append(processos[i].id)  # Salvar ID do processo

        if deadlock:
            self.log(f"Deadlock detectado! Processos em deadlock: {deadlock}")
        else:
            self.log("Nenhum deadlock foi detectado.")

    def parar(self):
        self.running = False
            
recursos = []
processos = []

class DeadlockApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Simulação de Deadlock")
        self.root.geometry("780x880")

        # Frame para adicionar recursos
        self.recurso_frame = tk.LabelFrame(root, text="Criar Recurso")
        self.recurso_frame.place(x=10, y=10, width=500, height=120)

        self.recurso_nome_label = tk.Label(self.recurso_frame, text="Nome do Recurso:")
        self.recurso_nome_label.grid(row=0, column=0, padx=5, pady=5)
        self.recurso_nome_entry = tk.Entry(self.recurso_frame)
        self.recurso_nome_entry.grid(row=0, column=1, padx=5, pady=5)

        self.recurso_instancias_label = tk.Label(self.recurso_frame, text="Instâncias:")
        self.recurso_instancias_label.grid(row=1, column=0, padx=5, pady=5)
        self.recurso_instancias_entry = tk.Entry(self.recurso_frame)
        self.recurso_instancias_entry.grid(row=1, column=1, padx=5, pady=5)

        self.adicionar_recurso_button = tk.Button(self.recurso_frame, text="Adicionar Recurso", command=self.adicionar_recurso)
        self.adicionar_recurso_button.grid(row=2, column=1, padx=5, pady=5)

        # Frame para adicionar processos
        self.processo_frame = tk.LabelFrame(root, text="Criar Processo")
        self.processo_frame.place(x=10, y=140, width=500, height=120)

        self.processo_tempo_solicitacao_label = tk.Label(self.processo_frame, text="Tempo de Solicitação:")
        self.processo_tempo_solicitacao_label.grid(row=0, column=0, padx=5, pady=5)
        self.processo_tempo_solicitacao_entry = tk.Entry(self.processo_frame)
        self.processo_tempo_solicitacao_entry.grid(row=0, column=1, padx=5, pady=5)

        self.processo_tempo_utilizacao_label = tk.Label(self.processo_frame, text="Tempo de Utilização:")
        self.processo_tempo_utilizacao_label.grid(row=1, column=0, padx=5, pady=5)
        self.processo_tempo_utilizacao_entry = tk.Entry(self.processo_frame)
        self.processo_tempo_utilizacao_entry.grid(row=1, column=1, padx=5, pady=5)

        self.criar_processo_button = tk.Button(self.processo_frame, text="Criar Processo", command=self.criar_processo)
        self.criar_processo_button.grid(row=2, column=1, padx=5, pady=5)

        # Botões centrais
        self.iniciar_simulacao_button = tk.Button(root, text="Iniciar Simulação", command=self.iniciar_simulacao)
        self.iniciar_simulacao_button.place(x=200, y=270, width=120, height=30)

        self.excluir_processo_button = tk.Button(root, text="Excluir Processo", command=self.excluir_processo)
        self.excluir_processo_button.place(x=200, y=310, width=120, height=30)

        # Listas à direita
        self.recursos_frame = tk.LabelFrame(root, text="Recursos")
        self.recursos_frame.place(x=520, y=10, width=250, height=250)
        self.recursos_listbox = tk.Listbox(self.recursos_frame)
        self.recursos_listbox.pack(fill="both", expand=True, padx=5, pady=5)

        self.processos_frame = tk.LabelFrame(root, text="Processos")
        self.processos_frame.place(x=520, y=260, width=250, height=250)
        self.processos_listbox = tk.Listbox(self.processos_frame)
        self.processos_listbox.pack(fill="both", expand=True, padx=5, pady=5)

        # Frames para as matrizes
        self.matrizes_frame = tk.LabelFrame(root, text="Matrizes")
        self.matrizes_frame.place(x=10, y=660, width=760, height=200)

        self.matrizes_disponiveis_frame = tk.LabelFrame(self.matrizes_frame, text="Recursos Disponíveis (A)")
        self.matrizes_disponiveis_frame.place(x=10, y=10, width=240, height=160)
        self.matrizes_disponiveis_text = tk.Text(self.matrizes_disponiveis_frame, height=5)
        self.matrizes_disponiveis_text.pack(fill="both", expand=True, padx=5, pady=5)

        self.matrizes_alocadas_frame = tk.LabelFrame(self.matrizes_frame, text="Recursos Alocados (C)")
        self.matrizes_alocadas_frame.place(x=260, y=10, width=240, height=160)
        self.matrizes_alocadas_text = tk.Text(self.matrizes_alocadas_frame, height=5)
        self.matrizes_alocadas_text.pack(fill="both", expand=True, padx=5, pady=5)

        self.matrizes_solicitacoes_frame = tk.LabelFrame(self.matrizes_frame, text="Solicitações (R)")
        self.matrizes_solicitacoes_frame.place(x=510, y=10, width=240, height=160)
        self.matrizes_solicitacoes_text = tk.Text(self.matrizes_solicitacoes_frame, height=5)
        self.matrizes_solicitacoes_text.pack(fill="both", expand=True, padx=5, pady=5)

        # Log na parte inferior
        self.log_frame = tk.LabelFrame(root, text="Log")
        self.log_frame.place(x=10, y=350, width=500, height=300)
        self.log_text = tk.Text(self.log_frame, height=10)
        self.log_text.pack(fill="both", expand=True, padx=10, pady=5)

        # Inicializa o sistema operacional (mas não inicia a simulação ainda)
        self.so = SistemaOperacional(processos, 5, self.log, self.atualizar_matrizes)
        self.simulacao_iniciada = False

    def adicionar_recurso(self):
        nome = self.recurso_nome_entry.get()
        instancias = self.recurso_instancias_entry.get()

        if nome and instancias:
            try:
                instancias = int(instancias)
                id = len(recursos)
                recursos.append(Recurso(nome, id, instancias))
                self.atualizar_recursos()
                self.log(f"Recurso '{nome}' adicionado com {instancias} instâncias.")
                self.recurso_nome_entry.delete(0, tk.END)
                self.recurso_instancias_entry.delete(0, tk.END)
            except ValueError:
                messagebox.showerror("Erro", "O número de instâncias deve ser um valor inteiro.")
        else:
            messagebox.showerror("Erro", "Por favor, preencha todos os campos.")

    def criar_processo(self):
        tempo_solicitacao = self.processo_tempo_solicitacao_entry.get()
        tempo_utilizacao = self.processo_tempo_utilizacao_entry.get()

        if tempo_solicitacao and tempo_utilizacao:
            try:
                tempo_solicitacao = int(tempo_solicitacao)
                tempo_utilizacao = int(tempo_utilizacao)
                id = len(processos) + 1
                processo = Processo(id, tempo_solicitacao, tempo_utilizacao, self.log)
                processos.append(processo)
                if self.simulacao_iniciada:
                    processo.start()
                self.atualizar_processos()
                self.log(f"Processo {id} criado com Tempo de Solicitação (∆Ts)={tempo_solicitacao} e Tempo de Utilização (∆Tu)={tempo_utilizacao}.")
                self.processo_tempo_solicitacao_entry.delete(0, tk.END)
                self.processo_tempo_utilizacao_entry.delete(0, tk.END)
            except ValueError:
                messagebox.showerror("Erro", "Os intervalos devem ser valores inteiros.")
        else:
            messagebox.showerror("Erro", "Por favor, preencha todos os campos.")

    def excluir_processo(self):
        selected = self.processos_listbox.curselection()
        if selected:
            id = int(self.processos_listbox.get(selected[0]).split()[1])
            for processo in processos:
                if processo.id == id:
                    processo.parar()  # Para o processo
                    processos.remove(processo)  # Remove da lista de processos
                    self.atualizar_processos()
                    self.log(f"Processo {id} excluído.")
                    break
            
            if len(processos) == 0:
                self.so.parar()

    def iniciar_simulacao(self):
        if not self.simulacao_iniciada:
            self.simulacao_iniciada = True
            self.so.start()
            for processo in processos:
                processo.start()
            self.log("Simulação iniciada.")
            self.iniciar_simulacao_button.config(state=tk.DISABLED)  # Desabilita o botão após iniciar a simulação

    def atualizar_matrizes(self):
        # Limpa o conteúdo atual das matrizes
        self.matrizes_disponiveis_text.config(state=tk.NORMAL)
        self.matrizes_disponiveis_text.delete(1.0, tk.END)
        self.matrizes_alocadas_text.config(state=tk.NORMAL)
        self.matrizes_alocadas_text.delete(1.0, tk.END)
        self.matrizes_solicitacoes_text.config(state=tk.NORMAL)
        self.matrizes_solicitacoes_text.delete(1.0, tk.END)

        # Obtém as matrizes de disponíveis, alocações e requisições
        disponiveis = [recurso.instancias_disponiveis for recurso in recursos]
        alocacoes = [processo.utiliza[:] for processo in processos]
        requisicoes = [processo.solicita[:] for processo in processos]

        # Formata as matrizes para exibição
        self.matrizes_disponiveis_text.insert(tk.END, str(disponiveis) + "\n")
        self.matrizes_alocadas_text.insert(tk.END, "\n".join([str(alocacao) for alocacao in alocacoes]) + "\n")
        self.matrizes_solicitacoes_text.insert(tk.END, "\n".join([str(requisicao) for requisicao in requisicoes]) + "\n")

        # Desabilita a edição do texto
        self.matrizes_disponiveis_text.config(state=tk.DISABLED)
        self.matrizes_alocadas_text.config(state=tk.DISABLED)
        self.matrizes_solicitacoes_text.config(state=tk.DISABLED)

    def atualizar_recursos(self):
        self.recursos_listbox.delete(0, tk.END)
        for recurso in recursos:
            self.recursos_listbox.insert(tk.END, f"{recurso.nome} (Instâncias: {recurso.instancias_disponiveis})")

    def atualizar_processos(self):
        self.processos_listbox.delete(0, tk.END)
        for processo in processos:
            self.processos_listbox.insert(tk.END, f"Processo {processo.id}")

    def log(self, message):
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)

if __name__ == "__main__":
    root = tk.Tk()
    app = DeadlockApp(root)
    root.mainloop()