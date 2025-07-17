from cProfile import label
import sys
from PyQt5.QtWidgets import QApplication, QWidget,QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QTextEdit, QFrame, QFormLayout, QTableWidget, QTableWidgetItem, QHeaderView, QFileDialog
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas # type: ignore
import numpy as np
#import pandas as pd
import json

# Classes and auxiliary functions
class material:
    def __init__(self, density):
        self.density = density

class silo:
    def __init__(self, capacity, material, flow, mat_position, silo_position, start):
        self.material = str(material)
        self.capacity = float(capacity)
        self.flow = float(flow) # flow rate in kg/s
        self.mat_position = int(mat_position)
        self.silo_position = int(silo_position)
        self.start = float(start)   
 
    def quantity(self, dt):
        quant = self.flow * dt
        return quant
    
    def end(self):
        return self.start + (self.capacity / self.flow)
    
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


def calcular_proporcoes_seguro(matriz):
    if matriz.shape[1] < 3:
        raise ValueError("A matriz deve ter pelo menos três colunas.")
    
    total = matriz[:, -1]
    numeradores = matriz[:, :-2]

    # Evita divisão por zero substituindo zeros por np.nan temporariamente
    with np.errstate(divide='ignore', invalid='ignore'):
        proporcoes = np.divide(numeradores, total[:, np.newaxis]) * 100
        proporcoes[~np.isfinite(proporcoes)] = 0  # Substitui NaN e inf por 0

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
    ax[0, 0].set_ylabel("material flow [kg/s]")

    ax[1, 0].stackplot(matrix_ton[:, col-2],matrix_pr[:,(range(len(mat_labels)))].T,
                       labels=mat_labels)
    ax[1, 0].set_title("Material Proportion in Conveyor [%]")
    ax[1, 0].set_xlim(0, t_total)
    ax[1, 0].legend()
    ax[1, 0].set_ylabel("% material")

    ax[0, 1].plot(matrix_ton[:, col-2], matrix_ton[:, col-1])
    ax[0, 1].set_title("Flow in the Conveyor Belt [kg/s]")

    for j in range(len(silos)):
        ax[1, 1].broken_barh([(silos[j].start, silos[j].end())], (j + 0.2, 0.3))
    
    #plt.show()

#Aqui comeca a criacao da interface do programa. 

class App(QWidget):
    def __init__(self):
        super().__init__()
        self.title = 'Conveyor Blending Model - v0.5'
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
        self.div_len_input = QLineEdit(self)
        self.div_res_input = QLineEdit(self)
        self.c_vel_input = QLineEdit(self)

        form_layout.addRow("Simulation Time[s]", self.t_total_input)
        form_layout.addRow("Conveyor Length[m]", self.div_len_input)
        form_layout.addRow("Conveyor resolution size[m]", self.div_res_input)
        form_layout.addRow("Conveyor Velocity[m/s]", self.c_vel_input)
        sidebar.addLayout(form_layout)


        # Tabela para entrada de dados dos silos
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(['Material','Capacity [kg]', 'Flow [kg/s]', 'Silo Material No','Silo Position Conveyor', 'Start [s]'])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch) # type: ignore
        sidebar.addWidget(self.table)

        #table with material names
        self.table_mat = QTableWidget()
        self.table_mat.setColumnCount(1)
        self.table_mat.setHorizontalHeaderLabels(["Material Names"])
        self.table_mat.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch) # type: ignore
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
        self.figure = plt.figure(figsize=(12, 8))  # Increase figure size
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setMinimumSize(900, 600)  # Set minimum size for the canvas
        main_area.addWidget(self.canvas)
        
        # Adiciona a área principal ao layout principal
        main_layout.addLayout(main_area)
        
        # Botão para salvar o caso
        self.save_case_button = QPushButton('Save Case', self)
        self.save_case_button.clicked.connect(self.save_case)
        sidebar.addWidget(self.save_case_button)

        # Botão para carregar um caso salvo
        self.load_case_button = QPushButton("Load Case", self)
        self.load_case_button.clicked.connect(self.load_case)
        sidebar.addWidget(self.load_case_button)

        self.setLayout(main_layout)
        self.show()
    
    def save_case(self):

        filename, _ = QFileDialog.getSaveFileName(self, "Save Case", "", "JSON Files (*.json)")
        if filename:
            case_data = {
                "simulation_time": self.t_total_input.text(),
                "conveyor_length": self.div_len_input.text(),
                "conveyor_resolution": self.div_res_input.text(),
                "conveyor_velocity": self.c_vel_input.text(),
                "silos": [],
                "materials": [],
                "results": {
                    "mat": self.mat.tolist() if hasattr(self, 'mat') else [],
                    "save_data": self.save_data.tolist() if hasattr(self, 'save_data') else [],
                    "save_prop": self.save_prop.tolist() if hasattr(self, 'save_prop') else []
                }
            }

            for row in range(self.table.rowCount()):
                silo_data = {}
                for col, key in enumerate(['material','capacity','flow','mat_position','silo_position','start']):
                    item = self.table.item(row, col)
                    silo_data[key] = item.text() if item else ""
                case_data["silos"].append(silo_data)

            for row in range(self.table_mat.rowCount()):
                item = self.table_mat.item(row, 0)
                if item and item.text():
                    case_data["materials"].append(item.text())

            with open(filename, "w", encoding="utf-8") as f:
                json.dump(case_data, f, indent=4)

            self.result_area.append(f"Case saved to {filename}")

    def load_case(self):

        filename, _ = QFileDialog.getOpenFileName(self, "Load Case", "", "JSON Files (*.json)")
        if filename:
            with open(filename, 'r') as f:
                case = json.load(f)

            # Restaurar entradas
            self.t_total_input.setText(str(case["simulation_time"]))
            self.div_len_input.setText(str(case["conveyor_length"]))
            self.div_res_input.setText(str(case["conveyor_resolution"]))
            self.c_vel_input.setText(str(case["conveyor_velocity"]))

            # Restaurar silos
            self.table.setRowCount(0)
            for silo in case["silos"]:
                row = self.table.rowCount()
                self.table.insertRow(row)
                self.table.setItem(row, 0, QTableWidgetItem(str(silo["material"])))
                self.table.setItem(row, 1, QTableWidgetItem(str(silo["capacity"])))
                self.table.setItem(row, 2, QTableWidgetItem(str(silo["flow"])))
                self.table.setItem(row, 3, QTableWidgetItem(str(silo["mat_position"])))
                self.table.setItem(row, 4, QTableWidgetItem(str(silo["silo_position"])))
                self.table.setItem(row, 5, QTableWidgetItem(str(silo["start"])))

            # Restaurar materiais
            self.table_mat.setRowCount(0)
            for mat in case["materials"]:
                row = self.table_mat.rowCount()
                self.table_mat.insertRow(row)
                self.table_mat.setItem(row, 0, QTableWidgetItem(str(mat)))

            # Restaurar resultados
            self.mat = np.array(case["results"]["mat"])
            self.save_data = np.array(case["results"]["save_data"])
            self.save_prop = np.array(case["results"]["save_prop"])

            # Mostrar mensagem
            self.result_area.setText("Case loaded successfully. Ready to plot or analyze.")

            # Atualizar gráficos
            self.figure.clear()
            self.ax = self.figure.subplots(2, 2)
            show_data(self.ax,
                        self.save_data,
                        self.save_prop,
                        t_total=float(case["simulation_time"]),
                        silos=[], mat_labels=case["materials"])
            self.canvas.draw()

    def add_row(self):
        row_position = self.table.rowCount()
        self.table.insertRow(row_position)

    def add_row_mat(self):
        row_position = self.table_mat.rowCount()
        self.table_mat.insertRow(row_position)
    
    def run_model(self):
        #get values of the inputs
        t_total = float(self.t_total_input.text())
        div_lenght = float(self.div_len_input.text()) # Tamanho da correia
        div_res = float(self.div_res_input.text()) # tamanho da divisao da correia
        c_vel = float(self.c_vel_input.text()) # velocidade da correia
        # Obter os valores de entrada da tabela
        silos = []
        for row in range(self.table.rowCount()):
            capacity = self.table.item(row, 1)
            if capacity is not None and capacity.text() != '':
                capacity = float(capacity.text())
            flow = self.table.item(row, 2)
            if flow is not None and flow.text() != '':
                flow = float(flow.text())
            mat_position = self.table.item(row, 3) # posicao do material na matrix 
            if mat_position is not None and mat_position.text() != '': 
                mat_position = int(mat_position.text())
            silo_no = self.table.item(row, 4)
            if silo_no is not None and silo_no.text() != '':
                silo_no = int(silo_no.text())
            start = self.table.item(row, 5)
            if start is not None and start.text() != '':
                start = float(start.text())
            material_instance = self.table.item(row,0)
            if material_instance is not None and material_instance.text() != '':
                material_instance = material_instance.text() 
            silo_instance = silo(capacity=capacity, material=material_instance, flow=flow, mat_position=mat_position,silo_position=silo_no, start=start)
            silos.append(silo_instance)
        
        #obter nomes dos materiais 

        names_mat = []
        for row in range(self.table_mat.rowCount()):
            mat_input = self.table_mat.item(row,0)
            if mat_input is not None and mat_input.text() != '':
                mat_input = str(mat_input.text())
            names_mat.append(mat_input)

        n_mat = len(names_mat)
        # Simulação (Aqui eh a parte da logica da simulacao)

        c1 = conveyor(velocity=c_vel, lenght=div_lenght)
        dt = div_res / c1.velocity
        n_steps = int(t_total / dt)
        mat = np.zeros((n_mat, int(c1.lenght / div_res)))
        save_data = np.zeros((n_steps + 1, int(n_mat + 2)))
        time = 0
        counter = 0
        ds = c1.velocity * dt
        step = round(ds / div_res)
        
        while (time <= t_total):
            
            for i in range(len(silos)):
                if time >= silos[i].start and time <= silos[i].end():
                    mat[silos[i].mat_position, silos[i].silo_position] = mat[silos[i].mat_position, silos[i].silo_position] + silos[i].quantity(dt)
            point = mat[:, -1]
            total = np.sum(point)
            save_data[counter, :] = np.concatenate((point, time, total), axis=None)
            mat = shift_matrix_right(mat, steps=step)
            time += dt
            counter += 1
        
        save_prop = calcular_proporcoes_seguro(save_data)
        
        # Exibir os resultados na área de texto
        self.result_area.setText(f'Silos configurados: {len(silos)}\n'
                                 f'Tempo Total: {t_total}\n'
                                 f'Comprimento da Divisão: {div_lenght}\n'
                                 f'Número de Materiais: {n_mat}')
        # Format and display the final state of the matrix 'mat'
        mat_str = np.array2string(mat, precision=2, separator=', ')
        self.result_area.append("\n\nFinal matrix 'mat':\n" + mat_str)
        
        self.mat = mat
        self.save_data = save_data
        self.save_prop = save_prop

        # Plotar os resultados no canvas
        self.figure.clear()
        self.ax = self.figure.subplots(2, 2) # type: ignore
        show_data(self.ax,save_data, save_prop, t_total=t_total, silos=silos,mat_labels=names_mat)
        self.canvas.draw()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = App()
    sys.exit(app.exec_())