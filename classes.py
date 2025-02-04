import threading
import time
import random

class Recurso:
    def __init__(self, nome, identificador, quantidade):
        self.nome = nome
        self.id = identificador
        self.quantidade = quantidade
        self.disponivel = quantidade
        self.lock = threading.Lock()

class SistemaOperacional(threading.Thread):
    def __init__(self, recursos, processos, intervalo_verificacao, atualizar_log):
        super().__init__()
        self.recursos = recursos
        self.processos = processos
        self.intervalo_verificacao = intervalo_verificacao
        self.atualizar_log = atualizar_log
        self.running = True

    def run(self):
        while self.running:
            time.sleep(self.intervalo_verificacao)
            self.detectar_deadlock()

    def detectar_deadlock(self):
        bloqueados = [p for p in self.processos if p.status == "Bloqueado"]
        mensagem = "\nVerificando por deadlocks...\n"
        if bloqueados:
            detalhes = []
            for p in bloqueados:
                if p.recurso_esperado is not None:
                    detalhes.append(f"Processo {p.id} aguardando {p.recurso_esperado.nome}")
            mensagem += "\n".join(detalhes) if detalhes else "Deadlock detectado, mas sem recurso identificado."
        else:
            mensagem += "Nenhum deadlock detectado."
        self.atualizar_log(mensagem)

    def parar(self):
        self.running = False

class Processo(threading.Thread):
    def __init__(self, id, recursos, intervalo_solicitacao, tempo_utilizacao, atualizar_log):
        super().__init__()
        self.id = id
        self.recursos = recursos
        self.intervalo_solicitacao = intervalo_solicitacao
        self.tempo_utilizacao = tempo_utilizacao
        self.atualizar_log = atualizar_log
        self.running = True
        self.recurso_atual = None       # Recurso que está sendo utilizado
        self.recurso_esperado = None    # Recurso que está aguardando (se bloqueado)
        self.status = "Bloqueado"       # Inicialmente "Bloqueado" até adquirir um recurso

    def run(self):
        while self.running:
            time.sleep(self.intervalo_solicitacao)
            recurso = random.choice(self.recursos)
            adquirido = False

            recurso.lock.acquire()
            try:
                if recurso.disponivel > 0:
                    recurso.disponivel -= 1
                    adquirido = True
            finally:
                recurso.lock.release()

            if adquirido:
                self.recurso_atual = recurso
                self.recurso_esperado = None
                self.status = "Rodando"
                self.atualizar_log(f"Processo {self.id} alocou {recurso.nome}.")
                time.sleep(self.tempo_utilizacao)
                
                recurso.lock.acquire()
                try:
                    recurso.disponivel += 1
                finally:
                    recurso.lock.release()

                self.atualizar_log(f"Processo {self.id} liberou {recurso.nome}.")
                self.recurso_atual = None
                self.status = "Bloqueado"
            else:
                self.recurso_esperado = recurso
                self.status = "Bloqueado"
                self.atualizar_log(f"Processo {self.id} bloqueado aguardando {recurso.nome}.")

    def parar(self):
        self.running = False
