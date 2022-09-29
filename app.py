
import streamlit as st
import pandas as pd
import numpy as np
import re


@st.cache
def convert_df(df):
    # IMPORTANT: Cache the conversion to prevent computation on every rerun
    return df.to_csv().encode('utf-8')

def not_eod_related( df , checks):
    m = df.merge( checks , on = "Control_ID" , how = "right" )
    m = m[ m["eod_related"] == 0 ] # not eod related
    m = m[ m["Score"] == 0 ] # get failed controls 
    m = m[ ["Control_ID" , "Comment_text" , "SQL" , "T" ] ]
    return m

def merge_files( BEOD , AEOD , PRE_TRIALS, ALL_SQL, CHECKS , OUTPUT):
    
    prev_trial = pd.read_excel( PRE_TRIALS, sheet_name="trials")
    prev_trial = prev_trial[ ["Control_ID" , "Jira" , "MIGS team comment"] ]
    
    sql_q = pd.read_excel( ALL_SQL , sheet_name="SQL")
    all_checks = pd.read_excel( CHECKS , sheet_name="checks")
    sc_output_beod = pd.read_csv( BEOD )
    sc_output_beod["T"] = "BEOD"

    sc_output_aoed = pd.read_csv( AEOD )
    sc_output_aoed["T"] = "AEOD" 
    beod_clean = not_eod_related( sc_output_beod , all_checks) 
    aeod_clean = sc_output_aoed.merge( all_checks , on="Control_ID" , how = "right" )
    aeod_clean = aeod_clean[ aeod_clean["Score"] == 0 ][["Control_ID" , "Comment_text" , "SQL" , "T"]]


    aeod_clean = aeod_clean.merge( sql_q , on = "Control_ID" , how = "left"  )
    beod_clean = beod_clean.merge( sql_q , on = "Control_ID" , how = "left"  )
    
    sc_output = pd.concat( [ beod_clean , aeod_clean ]  )
    
    sc_output = sc_output.sort_values( "Control_ID")
    final = sc_output.merge( prev_trial , on = "Control_ID" , how = "inner" ) 
    final["REPORT"] = "YES"
    final["COMMENT"] = final.apply( lambda x: "YES" if x["MIGS team comment"] != '' else "NO" , axis = 1 ) 
    final = final.drop_duplicates( subset=["Control_ID" , "T"])
    final = final.fillna('')
    final.to_csv(OUTPUT + ".csv")
    
    final[ "BEOD/EOD"] = final[ "T"]
    final["BEOD/EOD"][final.duplicated( subset = ["Control_ID"] ,keep="first")] = "BEOD/AEOD"
    #final.duplicated( subset = ["Control_ID"] ,keep="first").head(10)
    #final = final[final.duplicated( subset = ["Control_ID"] ,keep="first") ]
    
    final = final[ ~final.duplicated( subset = ["Control_ID"] ,keep="last") ]
    #final =final.drop_duplicates( subset=["Control_ID"] , keep = "first")
    final = final.sort_values( "Control_ID")
    final.to_csv("{}_2app.csv".format(OUTPUT))

    return final


BEOD = st.file_uploader("Upload SC BEOD")
AEOD = st.file_uploader("Upload SC AEOD")
PRE_TRIALS = st.file_uploader("Upload Trials")

CHECKS = st.file_uploader("Upload SC checks")
ALL_SQL = st.file_uploader("Upload SQL examples")

sc_output = None
queries = None
trials = None 
if (BEOD  and AEOD ) and (PRE_TRIALS and CHECKS) :
    # To read file as bytes:
    # To convert to a string based IO:
    if ALL_SQL:
        st.write("Download Results")
        RESULTS = merge_files(   BEOD , AEOD , PRE_TRIALS, ALL_SQL, CHECKS , "TEST" ) 

        data = convert_df( RESULTS)
        st.download_button(
        label="Download data as CSV",
        data=data,
        file_name='output.csv',
        mime='text/csv',
            )
    # Can be used wherever a "file-like" object is accepted:
        pass 
