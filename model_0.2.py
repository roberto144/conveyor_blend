### Blast Furnace Conveyor Belt Blending Model ###
### Author: Roberto Abreu Alencar 
### Date: 10-02-2025

#Basic Import
from cProfile import label
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
#import scipy.optimize as opm

#units of the system 
# lenght = m
# mass = kg
# density = kg/m³
# flow = kg/s 
#speed = m/s

#Classes Definition

#material definition
class material:
    def __init__(self, density):
        self.density = density

#silo definition
class silo():
    def __init__(self,capacity,material,flow, position, start, end):
        self.material = material
        self.capacity = capacity
        self.flow = flow
        self.position = position
        self.start = start
        self.end = end
    
    def quantity(self,dt):
        quant = self.flow*dt
        return quant
    

# conveyor definition, use later for overflow check calculation
class conveyor:
    def __init__(self, velocity, lenght):
        self.velocity  = velocity
        self.lenght = lenght


##############################
#### Auxiliary Functions #####
##############################

def shift_matrix_right(matrix, steps):
    # Converte a matriz para um array numpy para facilitar a manipulação
    matrix = np.array(matrix)
    
    # Obtém o número de linhas e colunas da matriz
    rows, cols = matrix.shape
    
    # Cria uma nova matriz para armazenar os elementos deslocados
    shifted_matrix = np.zeros((rows, cols), dtype=matrix.dtype)
    
    # Desloca cada elemento para a direita pelo número especificado de passos
    for i in range(rows):
        for j in range(cols):
            if j+steps < cols:
                shifted_matrix[i, (j + steps)] = matrix[i, j]
    
    return shifted_matrix

def main():
    resp = input("Save Result in csv? (Y/N): ").strip().upper()

    if resp == "Y":
        DF = pd.DataFrame(save_data)
        DF.to_csv("data.csv")
    elif resp == "N":
        print("...")
    else:
        print("Invalid Answer")

def calcular_proporcoes(matriz):
    # Verifica se a matriz tem pelo menos duas colunas
    if matriz.shape[1] < 2:
        raise ValueError("A matriz deve ter pelo menos duas colunas.")
    
    # Última coluna da matriz representa o total
    total = matriz[:, -1]
    
    # Calcula as proporções (porcentagens) de cada coluna em relação ao total
    proporcoes = matriz[:, :-2] / total[:, np.newaxis] * 100
    
    return proporcoes


############################################
#### initial definitions to the problem #### 
############################################

#total time only timestep and number of steps will be defined by speed and spacing definition
t_total = 180
div_lenght = 1 # consider 1 meter to make easily the positioning of each silo 
# conveyor details (lenght and velocity) 
c1 = conveyor(velocity=1.5, lenght=40)
#delta t and n_steps
dt = div_lenght/c1.velocity
n_steps = int(t_total/dt)

# Number of materials
n_mat = 6
# matrix initiation 
mat = np.zeros((n_mat,int(c1.lenght/div_lenght)))

# Definition of materials 
#sinter = material(density=2200)
#nut_coke = material(density=600)
#lump_ore = material(density=2300)
#pellet = material(density=2400)

coal = material(density=900)

#consider the 300t silo variying t/h from 22 to 60 and 150t from 6 to 40

#make this an objective function the flow of 400 t/h to calculate the flows for each conveyor belt

#material organization in the flow matrix
#BST = 0
#APL = 1
#DBI = 2
#PIT = 3
#KNC = 4
#CMS = 5

#consider each silo separated by 3 meters

# Silo assignment - carefull with silo distancing (get from drawings) - need to put numbers based on drawings to make sense
s1  = silo(capacity=300 ,material="BST" , flow = 34, position=(0,3), start=10, end=140)
s2  = silo(capacity=300 ,material="PIT" , flow = 34, position=(3,6), start=12, end=140)
s3  = silo(capacity=150 ,material="DBI" , flow = 15, position=(2,9), start=14, end=140)
s4  = silo(capacity=150 ,material="DBI" , flow = 15, position=(2,12), start=16,end=140)
s5  = silo(capacity=300 ,material="APL" , flow = 38, position=(1,15), start=18,end=140)
s6  = silo(capacity=300 ,material="CMS" , flow = 36, position=(5,18), start=20,end=140)
s7  = silo(capacity=300 ,material="BST" , flow = 34, position=(0,21), start=22,end=140)
s8  = silo(capacity=300 ,material="BST" , flow = 30, position=(0,3), start=10, end=140)
s9  = silo(capacity=300 ,material="KNC" , flow = 30, position=(4,6), start=12, end=140)
s10 = silo(capacity=150 ,material="RES" , flow = 0 , position=(0,9), start=14, end=140) #the spare silo is put in the 1st element of the matrix as convention
s11 = silo(capacity=150 ,material="APL" , flow = 19, position=(1,12), start=16, end=140)
s12 = silo(capacity=300 ,material="PIT" , flow = 23, position=(3,15), start=18, end=140)
s13 = silo(capacity=300 ,material="CMS" , flow = 36, position=(5,18), start=20, end=140)
s14 = silo(capacity=300 ,material="BST" , flow = 34, position=(0,21), start=22, end=140)

#array of silos

silos = [s1,s2,s3,s4,s5,s6,s7,s8,s9,s10,s11,s12,s13,s14]

# lets try without iteration and loops first to get the feeling in the guts
#save data matrix

 

save_data = np.zeros((n_steps+1, int(n_mat+2)))

# initialization 
time = 0
counter = 0
# calculate the quantity of each silo in the conveyor for the timestep
while (time <= t_total):
    #now get the size of the step in the matrix
    #calculate the next position of the points - first calculate the delta in distance for each timestep
    ds = c1.velocity*dt
    step = round(ds/div_lenght)
    aux = len(silos)
    #Put the material in conveyor - need to transform this after in a loop to get any number of materials and silos loading the conveyor 
    #easer configuration maybe is a array of classes objects, so the most problematica part will be only the ajusts to the system.
    
    for i in range(aux):
        if time>=silos[i].start and time<=silos[i].end:
            mat[silos[i].position] = mat[silos[i].position] + silos[i].quantity(dt)
        else:
            mat[silos[i].position] = mat[silos[i].position] + 0
    
    #print(list(mat))
    
    point = mat[:,int(c1.lenght/div_lenght)-1]
    sum = np.sum(point)
    #save the data
    save_data[counter,:] = np.concatenate((point, time,sum),axis=None)
        
    mat = shift_matrix_right(mat, steps=step)

    time = time + dt
    counter = counter + 1
    #print("Tempo de simulacao", time)
    #print(counter)


# Do not work in the Danieli environment - try later in home
#if __name__ == "__main__":
#    main()

#proportion matrix

save_prop = calcular_proporcoes(save_data)


print(pd.DataFrame(save_data).to_markdown())



####### Plot the data #######
# need to transform this in a function so i can make various types of anything

def show_data(matrix_ton, matrix_pr, t_total,silos):

    #details about the enter data
    #matrix_ton = matrix with data per material with t/h 
    #matrix_pr = matrix with proportional data, to get a better blend view
    #t_total = total time to get a proper x axis size
    #silos = array with all silos object in analysis. 
    fig, ax = plt.subplots(2,2, figsize = (12,6))
    #plot 1 - positioning
    ax[0,0].plot(matrix_ton[:,6], matrix_ton[:,0], c = "r", label = "BST")
    ax[0,0].plot(matrix_ton[:,6], matrix_ton[:,1], c = "b", label = "APL")
    ax[0,0].plot(matrix_ton[:,6], matrix_ton[:,2], c = "g", label = "DBI")
    ax[0,0].plot(matrix_ton[:,6], matrix_ton[:,3], c = "#000258", label = "PIT")
    ax[0,0].plot(matrix_ton[:,6], matrix_ton[:,4], c = "#FFF258", label = "KNC")
    ax[0,0].plot(matrix_ton[:,6], matrix_ton[:,5], c = "#AB3258", label = "CMS")
    ax[0,0].legend()
    ax[0,0].set_xlim(0,t_total)
    ax[0,0].set_title("Material Positioning")
    ax[0,0].set_ylabel("material flow [t/h]")


    #plot 2 - proportion plot
    ax[1,0].stackplot(matrix_ton[:,6],
                  matrix_pr[:,0],
                  matrix_pr[:,1],
                  matrix_pr[:,2],
                  matrix_pr[:,3],
                  matrix_pr[:,4],
                  matrix_pr[:,5],
                  labels=["BST", "APL","DBI","PIT","KNC","CMS"])
    ax[1,0].set_title("Material Proportion in Conveyor")
    ax[1,0].set_xlim(0,t_total)
    ax[1,0].legend()
    ax[1,0].set_ylabel("% material")

    #plot 3 - main flow in conveyor
    ax[0,1].plot(matrix_ton[:,6], matrix_ton[:,7])
    ax[0,1].set_title("Flow in the Conveyor Belt")

    #plot 4 - silo functioning during the total time 
    #this one is tricky but lets try
    for j in range(len(silos)):
        ax[1,1].broken_barh([(silos[j].start,silos[j].end)],(j+0.2,0.3))

    plt.show()

show_data(save_data, save_prop, t_total=t_total, silos=silos)
    