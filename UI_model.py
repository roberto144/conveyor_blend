import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QLabel, QGridLayout
from PyQt5.QtCore import Qt
import matplotlib.pyplot as plt

class SimpleApp(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Aplicação Simples')
        layout = QVBoxLayout()

        grid_layout = QGridLayout()
        self.fields = []
        for i in range(28):
            label = QLabel(f'Campo {i+1}:')
            field = QLineEdit()
            grid_layout.addWidget(label, i % 14, (i // 14) * 2)
            grid_layout.addWidget(field, i % 14, (i // 14) * 2 + 1)
            self.fields.append(field)
        
        layout.addLayout(grid_layout)

        self.calc_button = QPushButton('Calcular')
        self.calc_button.clicked.connect(self.calculate)
        layout.addWidget(self.calc_button)

        self.setLayout(layout)

    def calculate(self):
        values = [float(field.text()) for field in self.fields]
        self.show_graph(values)

    def show_graph(self, values):
        plt.figure(figsize=(10, 5))
        plt.plot(values, marker='o')
        plt.title('Gráfico dos Valores')
        plt.xlabel('Índice')
        plt.ylabel('Valor')
        plt.grid(True)
        plt.show()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = SimpleApp()
    ex.show()
    sys.exit(app.exec_())