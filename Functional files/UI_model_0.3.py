from cProfile import label
import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QTextEdit, QFrame, QFormLayout, QTableWidget, QTableWidgetItem, QHeaderView
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import numpy as np
import pandas as pd

# Classes and auxiliary functions
class material:
    def __init__(self, density):
        self.density = density

class silo:
    def __init__(self, capacity, material, flow, position, start, end):
        self.material = str(material)
        self.capacity = float(capacity)
        self.flow = float(flow)
        self.position = position
        self.start = float(start)
        self.end = float(end)

    def quantity(self, dt):
        quant = self.flow * dt
        return quant
    
# conveyor definition, use later for overflow check calculation
class conveyor:
    def __init__(self, velocity, lenght):
        self.velocity = velocity
        self.lenght = lenght

def shift_matrix_right(matrix, steps):
    matrix = np.array(matrix)
    rows, cols = matrix.shape
    shifted_matrix = np.zeros((rows, cols), dtype=matrix.dtype)
    for i in range(rows):
        for j in range(cols):
            if j + steps < cols:
                shifted_matrix[i, (j + steps)] = matrix[i, j]
    return shifted_matrix

def calcular_proporcoes(matriz):
    if matriz.shape[1] < 2:
        raise ValueError("A matriz deve ter pelo menos duas colunas.")
    total = matriz[:, -1]
    proporcoes = matriz[:, :-2] / total[:, np.newaxis] * 100
    return proporcoes

def show_data(ax,matrix_ton, matrix_pr, t_total, silos, mat_labels):
    lin, col = matrix_ton.shape
    ax[0, 0].clear()
    ax[1, 0].clear()
    ax[0, 1].clear()
    ax[1, 1].clear()


    for i in range(col-2):
        ax[0,0].plot(matrix_ton[:,col-2], matrix_ton[:,i], label = mat_labels[i])
    ax[0, 0].legend()
    ax[0, 0].set_xlim(0, t_total)
    ax[0, 0].set_title("Material Positioning")
    ax[0, 0].set_ylabel("material flow [t/h]")

    ax[1, 0].stackplot(matrix_ton[:, col-2],matrix_pr[:,(range(len(mat_labels)))].T,
                       labels=mat_labels)
    ax[1, 0].set_title("Material Proportion in Conveyor")
    ax[1, 0].set_xlim(0, t_total)
    ax[1, 0].legend()
    ax[1, 0].set_ylabel("% material")

    ax[0, 1].plot(matrix_ton[:, col-2], matrix_ton[:, col-1])
    ax[0, 1].set_title("Flow in the Conveyor Belt")
    
    for j in range(len(silos)):
        ax[1, 1].broken_barh([(silos[j].start, silos[j].end)], (j + 0.2, 0.3))
    
    plt.show()

class App(QWidget):
    def __init__(self):
        super().__init__()
        self.title = 'Conveyor Blending Model - v0.3'
        self.initUI()
    
    def initUI(self):
        self.setWindowTitle(self.title)
        
        # Layout principal
        main_layout = QHBoxLayout()
        
        # Barra lateral para os campos de entrada
        sidebar = QVBoxLayout()

        #form entry for general inputs
        form_layout = QFormLayout()
        
        self.t_total_input = QLineEdit(self)
        self.div_lenght_input = QLineEdit(self)

        form_layout.addRow("Simulation Time[s]", self.t_total_input)
        form_layout.addRow("Conveyor division[m]", self.div_lenght_input)
        sidebar.addLayout(form_layout)

        # Tabela para entrada de dados dos silos
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(['Material','Capacity', 'Flow', 'Position', 'Start', 'End'])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        sidebar.addWidget(self.table)

        #table with material names
        self.table_mat = QTableWidget()
        self.table_mat.setColumnCount(1)
        self.table_mat.setHorizontalHeaderLabels(["Material Names"])
        self.table_mat.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        sidebar.addWidget(self.table_mat)

        # Botão para adicionar linha na tabela
        self.add_row_button = QPushButton('Add Silo', self)
        self.add_row_button.clicked.connect(self.add_row)
        sidebar.addWidget(self.add_row_button)
        
        #button to add more materials
        self.add_row_button_material = QPushButton("Add Material", self)
        self.add_row_button_material.clicked.connect(self.add_row_mat)
        sidebar.addWidget(self.add_row_button_material)

        # Botão para executar o modelo
        self.run_button = QPushButton('Run Model', self)
        self.run_button.clicked.connect(self.run_model)
        sidebar.addWidget(self.run_button)
        
        # Adiciona a barra lateral ao layout principal
        main_layout.addLayout(sidebar)
        
        # Linha vertical para separar a barra lateral da área principal
        line = QFrame()
        line.setFrameShape(QFrame.VLine)
        line.setFrameShadow(QFrame.Sunken)
        main_layout.addWidget(line)
        
        # Layout para a área principal
        main_area = QVBoxLayout()
        
        # Área de texto para exibir os resultados
        self.result_area = QTextEdit(self)
        main_area.addWidget(self.result_area)
        
        # Canvas para exibir gráficos
        self.figure = plt.figure()
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setSizePolicy(7, 7)
        main_area.addWidget(self.canvas)
        
        # Adiciona a área principal ao layout principal
        main_layout.addLayout(main_area)
        
        self.setLayout(main_layout)
        self.show()
    
    def add_row(self):
        row_position = self.table.rowCount()
        self.table.insertRow(row_position)

    def add_row_mat(self):
        row_position = self.table_mat.rowCount()
        self.table_mat.insertRow(row_position)
    
    def run_model(self):
        #get values of the inouts
        t_total = float(self.t_total_input.text())
        div_lenght = float(self.div_lenght_input.text())
        # Obter os valores de entrada da tabela
        silos = []
        for row in range(self.table.rowCount()):
            capacity = self.table.item(row, 1)
            if capacity is not None and capacity.text() != '':
                capacity = float(capacity.text())
            flow = self.table.item(row, 2)
            if flow is not None and flow.text() != '':
                flow = float(flow.text())
            position = self.table.item(row, 3)
            if position is not None and position.text() != '':
                position = tuple(map(int, position.text().split(',')))
            start = self.table.item(row, 4)
            if start is not None and start.text() != '':
                start = float(start.text())
            end = self.table.item(row, 5)
            if end is not None and end.text() != '':
                end = float(end.text())
            material_instance = self.table.item(row,0)
            if material_instance is not None and material_instance.text() != '':
                material_instance = material_instance.text() 
            silo_instance = silo(capacity=capacity, material=material_instance, flow=flow, position=position, start=start, end=end)
            silos.append(silo_instance)
        
        #obter nomes dos materiais 

        names_mat = []
        for row in range(self.table_mat.rowCount()):
            mat_input = self.table_mat.item(row,0)
            if mat_input is not None and mat_input.text() != '':
                mat_input = str(mat_input.text())
            names_mat.append(mat_input)

        n_mat = len(names_mat)
        # Simulação (adicione aqui a lógica completa da simulação)

        c1 = conveyor(velocity=1.5, lenght=40)
        dt = div_lenght / c1.velocity
        n_steps = int(t_total / dt)
        mat = np.zeros((n_mat, int(c1.lenght / div_lenght)))
        save_data = np.zeros((n_steps + 1, int(n_mat + 2)))
        time = 0
        counter = 0
        
        while (time <= t_total):
            ds = c1.velocity * dt
            step = round(ds / div_lenght)
            for i in range(len(silos)):
                if time >= silos[i].start and time <= silos[i].end:
                    mat[silos[i].position] = mat[silos[i].position] + silos[i].quantity(dt)
            point = mat[:, int(c1.lenght / div_lenght) - 1]
            sum = np.sum(point)
            save_data[counter, :] = np.concatenate((point, time, sum), axis=None)
            mat = shift_matrix_right(mat, steps=step)
            time += dt
            counter += 1
        
        save_prop = calcular_proporcoes(save_data)
        
        # Exibir os resultados na área de texto
        self.result_area.setText(f'Silos configurados: {len(silos)}\n'
                                 f'Tempo Total: {t_total}\n'
                                 f'Comprimento da Divisão: {div_lenght}\n'
                                 f'Número de Materiais: {n_mat}')
        
        # Plotar os resultados no canvas
        self.figure.clear()
        self.ax = self.figure.subplots(2, 2) # type: ignore
        show_data(self.ax,save_data, save_prop, t_total=t_total, silos=silos,mat_labels=names_mat)
        self.canvas.draw()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = App()
    sys.exit(app.exec_())