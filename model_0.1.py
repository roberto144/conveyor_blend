### Blast Furnace Conveyor Belt Blending Model ###
### Author: Roberto Abreu Alencar 
### Date: 10-02-2025

#Basic Import
import matplotlib.pyplot as plt
import numpy as np
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
    def __init__(self):
        pass

# Auxiliary Functions #
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

     
    

# initial definitions to the problem 

#total time only timestep and number of steps will be defined by speed and spacing definition
t_total = 150
# conveyor lenght 
l = 40 # meters
div_lenght = 1 # detailing for each 10 centimeters

# conveyor speed
v = 2 #m/s

#delta t and n_steps
dt = div_lenght/v
n_steps = int(t_total/dt)

# Number of materials
n_mat = 4
# matrix initiation 
mat = np.zeros((n_mat,int(l/div_lenght)))

# Definition of materials 
sinter = material(density=2200)
nut_coke = material(density=600)
lump_ore = material(density=2300)
pellet = material(density=2400)

# Silo assignment - carefull with silo distancing (get from drawings) - need to put numbers based on drawings to make sense
s1 = silo(1000, sinter, flow=300, position=(0,1), start = 20, end = 90)
s2 = silo(1000, nut_coke, flow=150, position=(1,3), start = 50, end = 60)
s3 = silo(1000, lump_ore, flow=300, position=(2,5),start = 20, end = 30)
s4 = silo(1000, pellet, flow=300, position=(3,7),start = 30, end = 60)

# lets try without iteration and loops first to get the feeling in the guts
#save data matrix

save_data = np.zeros((n_steps+1, int(n_mat+1)))

# initialization 
time = 0
counter = 0
# calculate the quantity of each silo in the conveyor for the timestep
while (time <= t_total):
    #now get the size of the step in the matrix
    #calculate the next position of the points - first calculate the delta in distance for each timestep
    ds = v*dt
    step = round(ds/div_lenght)

    #Put the material in conveyor 

    if time>=s1.start and time<=s1.end:
        mat[s1.position] = mat[s1.position] + s1.quantity(dt)
    else:
        mat[s1.position] = mat[s1.position] + 0
    
    if time>=s2.start and time<=s2.end:
        mat[s2.position] = mat[s2.position] + s2.quantity(dt)
    else:
        mat[s2.position] = mat[s2.position] + 0    

    if time>=s3.start and time<=s3.end:
        mat[s3.position] = mat[s3.position] + s3.quantity(dt)
    else:
        mat[s3.position] = mat[s3.position] + 0

    if time>=s4.start and time<=s4.end:
        mat[s4.position] = mat[s4.position] + s4.quantity(dt)
    else:
        mat[s4.position] = mat[s4.position] + 0

 
    #print(list(mat))
    
    point = mat[:,int(l/div_lenght)-1]
    
    #save the data
    save_data[counter,:] = np.append(point, time)
        
    mat = shift_matrix_right(mat, steps=step)

    time = time + dt
    counter = counter + 1
    print("Tempo de simulacao", time)
    print(counter)



print(save_data)
plt.plot(save_data[:,4], save_data[:,0], c = "r", label = "Sinter")
plt.plot(save_data[:,4], save_data[:,1], c = "b", label = "Nut")
plt.plot(save_data[:,4], save_data[:,2], c = "g", label = "Lump")
plt.plot(save_data[:,4], save_data[:,3], c = "y", label = "Pellet")
plt.title("1st result of simulation of conveyot material")
plt.xlabel("Time [s] - timestep of 0.05 s")
plt.ylabel("Tons of each material at point x = 40 m - 1m of conveyor")
plt.legend()
plt.show()
    
    