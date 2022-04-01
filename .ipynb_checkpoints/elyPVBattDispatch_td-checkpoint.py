# -*- coding: utf-8 -*-
"""
Created on Fri Mar  4 06:32:32 2022

@author: brend
"""

"""
variables to span: PV size, LiB Power, LiB Duration, FB Power, FB Duration,

elecInbases to load: PV capex/opex tables, Electrolyzer capex/opex tables, LiB capex/opex, FB capex/opex

select PV size

select LiB or FB

run for loop to span power Duration

outputs for each case --> LCOH (capex/opex), capacity factors, PVtoH2 Efficiency

"""

"""
PV elecIn input and analysis 
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

filename = 'model_values.xlsx'

# need to change to this file: "C:\Users\brend\Zen\Zen - Active Customers\Mitsui\MIT007_Solar-Battery Analysis\03 Communications\Aquamarine - 12x24 Production -_MBK Modeled_R2.xlsx"

plantPredict = pd.read_excel(filename, sheet_name='Script') #pd.read_excel(filename, sheet_name='Year 1', skiprows = 3, usecols = [0,1,2,3])
pvGen = plantPredict["pvGen"]


#%%    
def elyBattDispatch(power,duration,maxElyP,pvGen):

    """ initial battery size estimate 
    based on assumption of 4%/yr degradation - conservative
    and 5 yr overbuild which is reasonable overbuild"""
    # power = 5
    # duration = 4
    # maxElyP = 3
    
    bolMWh = power*duration/(1-0.04)**5
    
    battCap = power*duration
    CP = 1/duration
    
    """ Battery Efficiency estimate based on Samsung E3 """
    effBatt = 0.0236 * CP**2 - 0.0752 * CP + 0.9764
    effMVT = 0.99
    effAC = 0.99
    
    RTE = effMVT * effAC * effBatt * effMVT * effAC
    
    soc1 = np.zeros(8760)
    battP = np.zeros(8760)
    elyP = np.zeros(8760)
    elyP_batt = np.zeros(8760)
    chgP = np.zeros(8760)
    
    for i in range(1,8760):
        
        # electrolyzer dispatch
        if (pvGen[i] <= maxElyP) and (pvGen[i] > 0):
            
            elyP[i] = pvGen[i]
            
        elif pvGen[i] > maxElyP:
                
            elyP[i] = maxElyP       
        
        elif pvGen[i] <= 0:
                    
            elyP[i]  = 0
                    
                    
        # battery charging dispatch
        # logic only true if (pvGen[i] <= maxElyP) and (pvGen[i] > 0)

        if (pvGen[i] - elyP[i]) > 0 and soc1[i-1] >= 0 and soc1[i-1] < battCap:
            
            
            if (soc1[i-1] + (pvGen[i] - elyP[i])) >= battCap:
                battP[i] = (battCap - soc1[i-1])*RTE
                chgP[i] = battP[i]
                
            elif (pvGen[i] - elyP[i]) > power:
                battP[i] = power * RTE
                chgP[i] = battP[i]
                
            elif (soc1[i-1] + (pvGen[i] - elyP[i])) < battCap:
                battP[i] = (pvGen[i] - elyP[i]) * RTE
                chgP[i] = battP[i]
                
                       
        # battery discharging dispatch - discharging is negative 
        if (pvGen[i] - elyP[i]) <= 0 and soc1[i-1] > 0 and soc1[i-1] <= battCap:
        
            if (soc1[i-1] - power) < 0 and elyP[i] < maxElyP and soc1[i-1] < maxElyP \
                and (soc1[i-1] + elyP[i]) < maxElyP:
                battP[i] = -soc1[i-1]
                elyP_batt[i] = abs(battP[i])
                    
            elif elyP[i] < maxElyP:
                battP[i] = -(maxElyP - elyP[i])
                elyP_batt[i] = abs(battP[i])
                
        soc1[i] =  soc1[i-1] + battP[i]
            
               
    output = pd.DataFrame()       
    output['PV_gen'] = pd.DataFrame(pvGen)
    output['elyP'] = pd.DataFrame(elyP)
    output['battP'] = pd.DataFrame(battP)
    output['elyP_batt'] = pd.DataFrame(elyP_batt)
    output['Date Time'] = pd.to_datetime(plantPredict.iloc[:,0])
    output['PV excess'] = pvGen - elyP - chgP
    output['SOC'] = pd.DataFrame(soc1)
    
    output['wkday'] = output['Date Time'].dt.weekday
    output['month'] = output['Date Time'].dt.month
    output['qrtr'] = output['Date Time'].dt.quarter
    output['hours'] = output['Date Time'].dt.hour
        
    monthly = output.groupby(['month','hours'])
    monthly = monthly.battP.mean()
    for y in range(1, 13):
        ax = monthly[y].plot()
    ax.legend(['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'],loc='center left')
    ax.set_ylabel('MW')

    y=5
    monthly[y]
    
    return sum(elyP)+sum(elyP_batt), sum(output['PV excess']), output, ax
#%%
results = [[(i,j) for j in range(2)] for i in range(5)]
elyEnergy = np.zeros([5,2])
pvExcess = np.zeros([5,2])
pvGenIn = 1 * pvGen
P_ely = 3
battPower = np.array([0.25,0.5,1,1.5,2]) * max(pvGenIn)
battDuration = [2,4]
for i in range(0,5):
    for j in range(0,2):
        results[i][j] = elyBattDispatch(battPower[i],battDuration[j],P_ely,pvGenIn)
        elyEnergy[i][j] = results[i][j][0]
        pvExcess[i][j] = results[i][j][1]
        

#%%

    output = results[0][1][2]       
    
        
    monthly = output.groupby(['month','hours'])
    monthly = monthly.PV_gen.mean()
    for y in range(1, 13):
        ax = monthly[y].plot()
    ax.legend(['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'],loc='center left')
    ax.set_ylabel('MW')

    y=5
    monthly[y]