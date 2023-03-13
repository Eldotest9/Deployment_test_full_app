
from google.protobuf.symbol_database import Default
import pandas as pd
import plotly.express as px
import streamlit as st
import numpy as np
from streamlit.type_util import data_frame_to_bytes
#import xlrd
#import math
#import re
#import seaborn as sns
#import matplotlib.pyplot as plt
#import matplotlib as plt




st.set_page_config(page_title="Renesas Cross-reference Guide",
                   page_icon= ":dash:",
                   layout = "wide")




#@st.cache(allow_output_mutation=True)
def get_data_from_excel():

    Combined_cleaned = pd.read_excel(r"Cross_referece_guide_Refereal.xlsx",sheet_name= "Combined_cleaned_all_parts")
    Frequency_scaling = pd.read_excel(r"Cross_referece_guide_Refereal.xlsx",sheet_name= "Frequency")
    Package_info_ST = pd.read_excel(r"Cross_referece_guide_Refereal.xlsx",sheet_name= "Packaging_ST",index_col=0)
    Package_info_NXP = pd.read_excel(r"Cross_referece_guide_Refereal.xlsx",sheet_name= "Packaging_NXP",index_col=0)
    Renesas_combined_cores= Combined_cleaned[Combined_cleaned["Company"] == "Renesas"]
    Processor= Frequency_scaling["Processor"].tolist()
    Processor_multiplier = Frequency_scaling["Scaled to M4"].tolist()
    Processor_multiplier = [round(num, 2) for num in Processor_multiplier]
    
    
    for i in range (len(Processor)):    
        index = list(Combined_cleaned[Combined_cleaned["Core"] == Processor[i]].index)
        Combined_cleaned.loc[index,"Frequency Scaled"] = Combined_cleaned.loc[index,"Operating Frequency (MHz)"]*Processor_multiplier[i]


    Renesas_combined_cores= Combined_cleaned[Combined_cleaned["Company"] == "Renesas"]
    return Combined_cleaned,Renesas_combined_cores,Package_info_ST,Package_info_NXP

Combined_cleaned,Renesas_combined_cores,Package_info_ST,Package_info_NXP = get_data_from_excel()


#st.dataframe(Combined_M4_M33_cores)


#------------- Algorithm -------------------#




def similarity_index(competitor_part_number,a=2,b=2,c=2,d=1,e=1):
    competitor_freq =list(Combined_cleaned[Combined_cleaned["Part Number"] == competitor_part_number]["Frequency Scaled"])[0]
    competitor_RAM =list(Combined_cleaned[Combined_cleaned["Part Number"] == competitor_part_number]["RAM Size (kB)"])[0]
    competitor_Flash =list(Combined_cleaned[Combined_cleaned["Part Number"] == competitor_part_number]["Flash Size (kB) (Prog)"])[0]
    competitor_lead =list(Combined_cleaned[Combined_cleaned["Part Number"] == competitor_part_number]["Lead Count (#)"])[0]
    oui= ["Frequency_similarity_index","RAM_similarity_index","Flash_similarity_index","Lead_count_similarity_index","Pkg_similarity_index"]
     
    
    Renesas_combined_cores.loc[:,"Frequency_similarity_index"] =  Renesas_combined_cores.loc[:,"Frequency Scaled"].apply(lambda x: ((np.min([x,competitor_freq]))/(np.max([x,competitor_freq]))))
    Renesas_combined_cores.loc[:,"RAM_similarity_index"] =  Renesas_combined_cores.loc[:,"RAM Size (kB)"].apply(lambda x: ((np.min([x,competitor_RAM]))/(np.max([x,competitor_RAM]))) )
    Renesas_combined_cores.loc[:,"Flash_similarity_index"] =  Renesas_combined_cores.loc[:,"Flash Size (kB) (Prog)"].apply(lambda x: ((np.min([x,competitor_Flash]))/(np.max([x,competitor_Flash]))) )
    Renesas_combined_cores.loc[:,"Lead_count_similarity_index"] =  Renesas_combined_cores.loc[:,"Lead Count (#)"].apply(lambda x: ((np.min([x,competitor_lead]))/(np.max([x,competitor_lead]))) )
    
    
    pkg_names = Combined_cleaned[Combined_cleaned["Part Number"] == competitor_part_number]["Pkg. Type"].unique()
    company_name = Combined_cleaned[Combined_cleaned["Part Number"] == competitor_part_number]["Company"].tolist()[0]
    package_info_index = Package_info_ST.index.values.tolist()
    workable_package = []
    

    if ~Combined_cleaned[Combined_cleaned["Part Number"] == competitor_part_number]["Pkg. Type"].any():
        Renesas_combined_cores.loc[:,"Pkg_similarity_index"] = 0
        
    elif company_name == "STm32":
        for j in package_info_index:
            for i in pkg_names:
                if int(Package_info_ST.loc[[j]][i]) == 1:
                    workable_package.append(j)
    
    else:
        for j in package_info_index:
            for i in pkg_names:
                if int(Package_info_NXP.loc[[j]][i]) == 1:
                    workable_package.append(j)        
    
    for i in Renesas_combined_cores.index: 
        if Renesas_combined_cores.loc[i,"Pkg. Type"] in workable_package:
            Renesas_combined_cores.loc[i,"Pkg_similarity_index"] = 1
        else:
            Renesas_combined_cores.loc[i,"Pkg_similarity_index"] = 0
    
    
    Renesas_combined_cores.loc[: , oui] = Renesas_combined_cores[oui].fillna(0)
    for i in Renesas_combined_cores.index:
        columns = list(Renesas_combined_cores.loc[i,oui])
        Renesas_combined_cores.loc[i,"Similarity_Index"] = np.average(columns,weights= [a,b,c,d,e])
    
    return Renesas_combined_cores.sort_values(by = "Similarity_Index",ascending=False)






#------- SIDEBAR    --------#
st.sidebar.header("Please Filter Here:")

# Using object notation
company = st.sidebar.selectbox(
    "Company",
    ("STm32", "NXP")
)
device = st.sidebar.selectbox(
    "Group",
    (Combined_cleaned[Combined_cleaned["Company"] == company]["Group"].unique())
)
part_number = st.sidebar.selectbox(
    "Part Number",
    (Combined_cleaned[(Combined_cleaned["Company"] == company) & (Combined_cleaned["Group"] == device)]["Part Number"].unique())
)
with st.sidebar.expander("Similarity Index Tuning"):
    #st.write('Prioritizing variables')
    freq = st.slider('Frequency', 0, 5, 2)
    RAM = st.slider('RAM Size (kB)', 0, 5, 2)
    Flash = st.slider("Flash Size (kB) (Prog)", 0, 5, 2)
    Lead = st.slider("Lead Count (#)", 0, 5, 1)
    Pkg = st.slider("Pkg. Type", 0, 2, 1)
    st.caption('Vary the slider according to degree of importance to place on the variables in the similarity index algorithm')

new_combined_cores= similarity_index(part_number,freq,RAM,Flash,Lead,Pkg)




#------- MAINPAGE -----------------

col1, col2 = st.columns([4,1])

with col1:
    st.title("Renesas RA family Cross-Reference Guide")
    
with col2:
   st.image("RA_white.png")

cleaned_columns = ["Part Number","Operating Frequency (MHz)","Flash Size (kB) (Prog)","RAM Size (kB)","Core","Lead Count (#)","Pkg. Type","Group","Similarity_Index"]
cleaned_columns_2 = ["Part Number","Operating Frequency (MHz)","Flash Size (kB) (Prog)","RAM Size (kB)","Core","Lead Count (#)","Pkg. Type","Group"]
st.subheader("Selected competitor part")

st.dataframe(Combined_cleaned[Combined_cleaned["Part Number"]== part_number ][cleaned_columns_2])
st.subheader("Arranged Renesas parts in similarity index descending order")

st.dataframe(new_combined_cores[cleaned_columns])
st.text(' Similarity index of 1 represents a perfect match to competitors part and 0 represents no match')

#st.markdown(##)
st.subheader('3D graph representing the RA device of the top 10 parts')


fig = px.scatter_3d(new_combined_cores[:10], x="Operating Frequency (MHz)", y='RAM Size (kB)', z='Flash Size (kB) (Prog)',
              color='Group',width=900, height=900)

st.plotly_chart(fig,use_container_width=True,theme="streamlit")



#---- HIDE STREAMLIT STYLE   -------#

hide_st_style = """
                <style>
                #MainMenu {visibility: hidden;}
                footer {visibility: hidden;}
                header {visibility: hidden;}
                </style>
                """
st.markdown(hide_st_style,unsafe_allow_html=True)