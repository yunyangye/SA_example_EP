import os
from shutil import copyfile,rmtree
import subprocess
import pandas as pd

def runModel(indx,para_indx,tmpl_file,attribute_file,epw_file):
    f = open(tmpl_file,'r')
    tmpl = f.readlines()
    f.close()
    
    f = open(attribute_file,'r')
    attribute = f.readlines()
    f.close()
    
    for i in range(len(indx)):
        for x in para_indx[i]:
            for j in range(len(attribute)):
                if '$Start:'+x in attribute[j] and indx[i] in attribute[j]:
                    start_indx = j+1
                if '$End:'+x in attribute[j] and indx[i] in attribute[j]:
                    end_indx = j
            data = attribute[start_indx:end_indx]
            for k in range(len(tmpl)):
                if tmpl[k] == '$'+x+'$\n':
                    break
            new_tmpl = []
            for m in range(k):
                new_tmpl.append(tmpl[m])
            for m in data:
                new_tmpl.append(m)
            for m in range(k+1,len(tmpl)):
                new_tmpl.append(tmpl[m])
            tmpl = []
            for m in new_tmpl:
                tmpl.append(m)
    
    # create a new folder
    os.makedirs('temp')
    f = open('./temp/temp.idf','w')
    for x in tmpl:
        f.writelines(x)
    f.close()
    copyfile(epw_file,'./temp/temp.epw')
    
    # run the models
    df = subprocess.Popen(['C:/EnergyPlusV8-6-0/energyplus.exe','-w','./temp/temp.epw','-d','./temp','./temp/temp.idf'],stdout=subprocess.PIPE)
    output,err = df.communicate()
    print(output.decode('utf-8'))
    if not err is None:
        print(err.decode('utf-8'))

def collectInformation(html_file):
    tables = pd.read_html(html_file)
    site_EUI = float(tables[0][2][1])
    elec_EUI = float(tables[3][1][16])/float(tables[2][1][1])*1000
    ng_EUI = float(tables[3][2][16])/float(tables[2][1][1])*1000
    heat_elec_EUI = float(tables[3][1][1])/float(tables[2][1][1])*1000
    cool_elec_EUI = float(tables[3][1][2])/float(tables[2][1][1])*1000
    int_lig_elec_EUI = float(tables[3][1][3])/float(tables[2][1][1])*1000
    ext_lig_elec_EUI = float(tables[3][1][4])/float(tables[2][1][1])*1000
    int_eqp_elec_EUI = float(tables[3][1][5])/float(tables[2][1][1])*1000
    fan_elec_EUI = float(tables[3][1][7])/float(tables[2][1][1])*1000
    water_elec_EUI = float(tables[3][1][12])/float(tables[2][1][1])*1000
    heat_ng_EUI = float(tables[3][2][1])/float(tables[2][1][1])*1000
    data = [site_EUI,elec_EUI,ng_EUI,heat_elec_EUI,cool_elec_EUI,int_lig_elec_EUI,ext_lig_elec_EUI,
            int_eqp_elec_EUI,fan_elec_EUI,water_elec_EUI,heat_ng_EUI]
    
    return data

# parameter index
para_indx = [['Inf_ZN1','Inf_ZN2','Inf_ZN3','Inf_ZN4'],
             ['Ins_Roof'],['Door_R'],['Window'],['OA_Flow_Core',
             'OA_Flow_ZN1','OA_Flow_ZN2','OA_Flow_ZN3','OA_Flow_ZN4'],['Cool_COP'],
             ['Heat_COP'],['Lig_Sch'],['Equip_Sch'],['Lights','EMS'],['Daylighting'],
             ['Ext_Lig'],['Fan'],['OA_Controller'],['SWH'],['DualSetpoint']]

# years
years_lib = ['2004','2007','2010','2013','2016']

# calculate
tmpl_file = './ASHRAE90.1_OfficeSmall_STD_Honolulu.tmpl'
attribute_file = './Attributes_Honolulu.txt'
epw_file = './USA_HI_Honolulu.Intl.AP.911820_TMY3.epw'

len_para = len(para_indx)

# create result table
title = ','
for i in range(len_para):
    title += ','
title += 'site_EUI,elec_EUI,ng_EUI,heat_elec_EUI,cool_elec_EUI,int_lig_elec_EUI,ext_lig_elec_EUI,int_eqp_elec_EUI,fan_elec_EUI,water_elec_EUI,heat_ng_EUI\n'

f = open('./results.csv','w')
f.writelines(title)
f.close()

# forward
for i in range(len(years_lib)-1):
    base_indx = [years_lib[i]]*len_para
    # run baseline model
    runModel(base_indx,para_indx,tmpl_file,attribute_file,epw_file)
    # collect baseline EUI
    data = collectInformation('./temp/eplustbl.htm')
    line = 'base'
    for x in base_indx:
        line += ','
        line += x
    for x in data:
        line += ','
        line += str(x)
    line += '\n'
    f = open('./results.csv','a')
    f.writelines(line)
    f.close()
    rmtree('./temp')
    
    # identify the attributes that are changed 
    indx_lib = [0]*len_para
    f = open(attribute_file,'r')
    attribute = f.readlines()
    f.close()
    for ind,row in enumerate(para_indx):
        k = 0
        for x in row:
            for y in attribute:
                if '$Start:'+x in y and years_lib[i] in y:
                    if years_lib[i+1] not in y:
                        k = 1
        indx_lib[ind] += k

    # count number of '1'
    num_att = 0
    for x in indx_lib:
        if x == 1:
            num_att += 1
    
    baseline = [0]*len_para
    for num in range(num_att):
        # create new indx
        newline = []
        for m in range(len(indx_lib)):
            if baseline[m] == 0 and indx_lib[m] == 1:
                temp = []
                for val in baseline:
                    temp.append(val)
                temp[m] = 1
                newline.append(temp)
        
        new_indx = []
        for row in newline:
            temp = []
            for val in row:
                if val == 0:
                    temp.append(years_lib[i])
                else:
                    temp.append(years_lib[i+1])
            new_indx.append(temp)
        
        site_EUI = []
        for val in new_indx:
            # run baseline model
            runModel(val,para_indx,tmpl_file,attribute_file,epw_file)
            # collect baseline EUI
            data = collectInformation('./temp/eplustbl.htm')
            line = 'new'+str(num)
            for x in val:
                line += ','
                line += x
            for x in data:
                line += ','
                line += str(x)
            line += '\n'
            f = open('./results.csv','a')
            f.writelines(line)
            f.close()
            rmtree('./temp')
            site_EUI.append(data[0])
        
        max_saving_id = site_EUI.index(min(site_EUI))
        baseline = []
        for val in newline[max_saving_id]:
            baseline.append(val)

# backword
for i in range(len(years_lib)-1):
    base_indx = [years_lib[len(years_lib)-1-i]]*len_para
    # run baseline model
    runModel(base_indx,para_indx,tmpl_file,attribute_file,epw_file)
    # collect baseline EUI
    data = collectInformation('./temp/eplustbl.htm')
    line = 'base'
    for x in base_indx:
        line += ','
        line += x
    for x in data:
        line += ','
        line += str(x)
    line += '\n'
    f = open('./results.csv','a')
    f.writelines(line)
    f.close()
    rmtree('./temp')
    
    # identify the attributes that are changed 
    indx_lib = [0]*len_para
    f = open(attribute_file,'r')
    attribute = f.readlines()
    f.close()
    for ind,row in enumerate(para_indx):
        k = 0
        for x in row:
            for y in attribute:
                if '$Start:'+x in y and years_lib[len(years_lib)-1-i] in y:
                    if years_lib[len(years_lib)-2-i] not in y:
                        k = 1
        indx_lib[ind] += k

    # count number of '1'
    num_att = 0
    for x in indx_lib:
        if x == 1:
            num_att += 1
    
    baseline = [0]*len_para
    for num in range(num_att):
        # create new indx
        newline = []
        for m in range(len(indx_lib)):
            if baseline[m] == 0 and indx_lib[m] == 1:
                temp = []
                for val in baseline:
                    temp.append(val)
                temp[m] = 1
                newline.append(temp)
        
        new_indx = []
        for row in newline:
            temp = []
            for val in row:
                if val == 0:
                    temp.append(years_lib[len(years_lib)-1-i])
                else:
                    temp.append(years_lib[len(years_lib)-2-i])
            new_indx.append(temp)
        
        site_EUI = []
        for val in new_indx:
            # run baseline model
            runModel(val,para_indx,tmpl_file,attribute_file,epw_file)
            # collect baseline EUI
            data = collectInformation('./temp/eplustbl.htm')
            line = 'new'+str(num)
            for x in val:
                line += ','
                line += x
            for x in data:
                line += ','
                line += str(x)
            line += '\n'
            f = open('./results.csv','a')
            f.writelines(line)
            f.close()
            rmtree('./temp')
            site_EUI.append(data[0])
        
        max_use_id = site_EUI.index(max(site_EUI))
        baseline = []
        for val in newline[max_use_id]:
            baseline.append(val)

