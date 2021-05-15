import matplotlib.pyplot as plt
import numpy as np
import time
from pyfirmata import Arduino, util
from threading import Thread
import csv
import gi
from gi.repository import Gtk

gi.require_version('Gtk', '3.0')


class Main(Thread):
    def __init__(self, pino, temp_exec, temp_graf) -> None:
        self.pino = pino
        self.t_exec = temp_exec
        self.t_graf = temp_graf
        self.dados = builder.get_object('informacoes')
        super().__init__()

    def plot_Grafico(self, X, Y, tittle=None, Ini=None, Term=None):
        titulo2 = f'-> Início {Ini}\n-> Fim {Term}\nGráfico nº {tittle}'
        plt.title(titulo2)
        plt.xlabel('Tempo em segundos')
        plt.ylabel('Temperatura em C°')
        plt.plot(X, Y)
        plt.savefig(f'/home/fernando/Área de Trabalho/{Term}.pdf')
        plt.clf()
        # plt.show()

    def data(self):
        data = time.strftime('%a, %d %b %Y %H:%M:%S', time.localtime())
        return data

    def mediaTemp(self, n_temp):
        soma = 0
        for n in range(200):
            soma += n_temp
        media = soma / (n + 1)
        return media

    def run(self,):
        x = []
        y = []
        t = Temperatura()
        try:
            tempo_exec = int(self.t_exec)
            tempo_graf = int(self.t_graf)
        except TypeError:
            return None
        inicio = self.data()
        cont = 0
        qtd_grafico = 0
        print(f'Início -> {inicio}')
        self.dados.set_text('')
        with open('log.csv', 'a+', newline='', encoding='utf-8') as file:
            w = csv.writer(file)
            while cont < tempo_exec:
                x.append(cont)
                y.append(self.mediaTemp(t.get_temperatura(self.pino)))
                w.writerow([x[cont], y[cont], self.data()])
                cont += 1
                time.sleep(1)
                if cont == tempo_graf:
                    qtd_grafico += 1
                    self.plot_Grafico(x, y, str(qtd_grafico), inicio, self.data())
                    cont = 0
                    tempo_exec -= tempo_graf
                    x = []
                    y = []
                    continue
            file.close()
            qtd_grafico += 1
            self.plot_Grafico(x, y, str(qtd_grafico), inicio, self.data())


class Temperatura:
    def get_temperatura(self, pinoTermo):
        leiturapin = pinoTermo.read() * 1000
        resistencia = 10000 * ((1024 / leiturapin) - 1)
        temp = np.log(resistencia)
        temp = 1 / (0.001129148 + (0.000234125 * temp) +
                    (0.0000000876741 * temp * temp * temp))
        temp = temp - 273.15
        return temp


class CalcTempo:
    def __init__(self, ativa=False) -> None:
        self.hr = builder.get_object('hora_execucao')
        self.min = builder.get_object('minuto_execucao')
        self.seg = builder.get_object('segundo_execucao')
        self.tempo_definido = builder.get_object('tempo_definido_recebe_dados')
        self.ativa = ativa

    def temp_exec(self):
        if self.ativa:
            try:
                hora = self.hr.get_text()
                minuto = self.min.get_text()
                segundo = self.seg.get_text()
                hora = int(hora) * 3600
                if 0 <= int(minuto) <= 59:
                    minuto = int(minuto) * 60
                else:
                    self.tempo_definido.set_text('Minutos e segundos entre 0 e 59.')
                    return None
                if 0 <= int(segundo) <= 59:
                    segundo = int(segundo) * 1
                else:
                    self.tempo_definido.set_text('Minutos e segundos entre 0 e 59.')
                    return None
                def_msg = f'{int(hora/3600)} hora(s), {int(minuto/60)} minuto(s) e {segundo} sgundo(s)'
                self.tempo_definido.set_text(def_msg)
                tempo = int(hora) + int(minuto) + int(segundo)
                return tempo
            except ValueError:
                self.tempo_definido.set_text('Digite somente Números.')
                return None
        else:
            self.tempo_definido.set_text('Tempo Indefinido.')
            return 9999999999999999999999999999999999999999999999999999


class TempGraf:
    def __init__(self) -> None:
        self.hr_g = builder.get_object('hora_grafic')
        self.min_g = builder.get_object('minuto_grafic')
        self.seg_g = builder.get_object('segundo_grafic')
        self.msg_graf = builder.get_object('display_freq')

    def temp_graf(self):
        try:
            hora = self.hr_g.get_text()
            minuto = self.min_g.get_text()
            segundo = self.seg_g.get_text()
            if 0 <= int(hora) <= 2:
                hora = int(hora) * 3600
            else:
                self.msg_graf.set_text('Tempo máximo de 3 horas.')
                return None
            if 0 <= int(minuto) <= 59:
                minuto = int(minuto) * 60
            else:
                self.msg_graf.set_text('Minutos e segundos entre 0 e 59.')
                return None
            if 0 <= int(segundo) <= 59:
                segundo = int(segundo) * 1
            else:
                self.msg_graf.set_text('Minutos e segundos entre 0 e 59.')
                return None
            self.msg_graf.set_text(f'{int(hora/3600)} hora(s), {int(minuto/60)} minuto(s) e {segundo} sgundo(s)')
            return int(hora) + int(minuto) + int(segundo)
        except ValueError:
            self.msg_graf.set_text('Digite somente Números.')
            return None


class Handler:
    def __init__(self):
        self.Uno = None
        self.pinoTermo = None
        self.porta = None
        self.pinoAnalog = None
        self.entra_p_serial = builder.get_object('entra_p_serial')
        self.entra_pino_analog = builder.get_object('entra_pino_analog')
        self.cx_msg_erros = builder.get_object('display _erros')
        self.bot_modo_temp = builder.get_object('escolhe_modo_t')
        self.init_status = False
        self.def_temp_on = False
        self.temp_off = False

    def on_janela_principal_destroy(self, janela_principal):
        Gtk.main_quit()

    def com_Arduino(self):

        errP = '   Porta Serial não encontrada. Entre com a porta correta.   '
        errPino = '   Entre com o pino onde o sensor está conectado.   '
        self.porta = self.entra_p_serial.get_text()
        self.pinoAnalog = self.entra_pino_analog.get_text()
        try:
            self.Uno = Arduino(self.porta)
            self.cx_msg_erros.set_text('  OK !  ')
            self.init_status = True
        except:
            self.cx_msg_erros.set_text(errP)
            self.init_status = False
            return None
        it = util.Iterator(self.Uno)
        it.start()
        if self.pinoAnalog:
            self.pinoTermo = self.Uno.get_pin(f'a:{self.pinoAnalog}:i')
            self.cx_msg_erros.set_text('  OK !  ')
            self.init_status = True
        else:
            self.cx_msg_erros.set_text(errPino)
            self.init_status = False
            return None
        time.sleep(3)

    def msg(self):
        msg: Gtk.MessageDialog = builder.get_object('msg_status')
        msg.show_all()
        msg.run()
        msg.hide()

    def on_escolhe_modo_t_toggled(self, escolhe_modo):
        if self.bot_modo_temp.get_active():
            return True
        else:
            return False

    def on_botao_iniciar_clicked(self, botao_iniciar):
        if not self.init_status:
            self.com_Arduino()
            graf = TempGraf()
            temp = CalcTempo(self.on_escolhe_modo_t_toggled(self))
            g = graf.temp_graf()
            t = temp.temp_exec()
            main = Main(self.pinoTermo, t, g)
            main.start()
        else:
            self.msg()

    def on_botao_terminar_clicked(self, botao_terminar):
        self.init_status = False


builder = Gtk.Builder()
builder.add_from_file('interface_termistor.glade')
builder.connect_signals(Handler())
janela = builder.get_object('janela_principal')
janela.show_all()
Gtk.main()
