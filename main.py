import sys, os, subprocess
import time
from multiprocessing import Process, current_process
import json
import gspread
from datetime import datetime
from oauth2client.service_account import ServiceAccountCredentials
import csv

json_key = 'credentialKey.json'
scope = ['https://spreadsheets.google.com/feeds']

transfercsv = 'tempD.csv'
savingcsv = 'tempsaving.csv'

def monitoringSeq():
    subprocess.call(["sudo", "./measuring"])

def GetSpreadsheet(verbose=False):
    if verbose:
        print('UploadProcess::GoogleCredential::Start')
    credentials = ServiceAccountCredentials.from_json_keyfile_name(json_key, scope)
    #get Credential
    gc = gspread.authorize(credentials)
    #get google autorize
    if verbose:
        print('UploadProcess::GoogleCredential::Google Authorized')
    #open configuration file
    with open('cfg.json','r') as infile:
        fname = json.load(infile)
    #spreadsheetfile open
    kk = gc.open(fname['Filename']).worksheet(fname['Sheetname'])
    if verbose:
        print('UploadProcess::GoogleCredential::Open Spreadsheet')
    return kk

def UploadSeq1(verbose=False): #general uploading (only one data-line)
    kk = GetSpreadsheet()
    #get data from temporary file
    imdata = [None]*5
    with open(transfercsv, 'rb') as f:
        reader = csv.reader(f)
        totalD = list(reader)
        imdata = totalD[len(totalD)-1]
    datenormal = datetime.strptime(imdata[0],'%Y-%M-%d %H:%S')
    imdata[0] = datenormal.strftime('%Y-%M-%d %H:%S')
    kk.append_row(imdata)
    print('data upload completed')

def highdeleter(filename):
    i = 0
    tempfilename = filename
    while os.path.exists(tempfilename):
        tempfilename = filename + '_' + str(i)
        i = i+1
    with open(filename,'r') as originfile:
        a = originfile.readlines()
    del(a[0])
    with open(tempfilename,'w') as tempfile:
        for line in a:
            tempfile.write(line)
    os.rename(tempfilename,filename)

def unifier(originname, offsetname, deleting=False,verbose=False):
    if verbose==True:
        print('UploadProcess::DataUnifier::Tranfer Data Detected')
    offsetlines =  open(offsetname,'rb').readlines()
    with open(originname,'ab') as originalfile:
        if verbose==True:
            print('Data lines: %d' %(len(offsetlines)))
        for line in offsetlines:
            #print(line)
            originalfile.write(line)
    print('UploadProcess::DataUnifier::Data Transferred to save data')
    if deleting:
        os.remove(offsetname)
        if verbose==True:
            print('UploadProcess::DataUnifier::Tranfer file deleted')

def UploadSeq2(verbose=False): #delayed uploading (one by one dataline)
    sheet = GetSpreadsheet(verbose=verbose)
    #get data from temporary file
    imdata = [None]*5
    with open(savingcsv, 'rt', encoding='utf-8') as f:
        reader = csv.reader(f)
        totalD = list(reader)
    if verbose:
        print('UploadProcess::UploadSequence::Found %d lines saved, ' %(len(totalD)),end='')
    if not len(totalD)==0:
        imdata = totalD[0]
        if verbose:
            print('Sending to google...')
        datenormal = datetime.strptime(imdata[0],'%Y-%M-%d %H:%S')
        imdata[0] = datenormal.strftime('%Y-%M-%d %H:%S')
        sheet.append_row(imdata)
        if verbose:
            print('UploadProcess::UploadSequence::Completed Uploading 1 dataline')
    else:
        print('Skip upload sequence')

def CheckLastRow(rowcnt=0):
    sheet = GetSpreadsheet()
    lastrownum = sheet.row_count
    anslist = sheet.row_values(lastrownum-rowcnt)
    ans = not ('' in anslist) or (None in anslist)
    return ans

def SetLastRow(verbose=False):
    if verbose:
        print('UploadProcess::LastRowSetting::Start')
    sheet = GetSpreadsheet()
    while not CheckLastRow():
        sheet.delete_row(sheet.row_count)
        if verbose:
            print('UploadProcess::LastRowSetting::One Blank line deleted')

def monitoringProcess(): #monitoring sequence for multiprocessing
    monitoringSeq()
    time.sleep(60)

def monitoringProcessLoop():
    while True:
        monitoringProcess()

def uploadingProcess(verbose=False): #process of ((Uploading + Data Transfer)) for multiprocessing
    try:
        if os.path.exists(transfercsv):
            unifier(savingcsv,transfercsv,deleting=True,verbose=verbose)
        UploadSeq2(verbose=verbose)
        highdeleter(savingcsv)
        print('UploadProcess::Delete head of saved data')
    except gspread.exceptions.RequestError:
        SetLastRow()
    except:
        raise

def main(verbose=False):
    try:
        monitoringProcessN = 1
        uploadingProcessN = 1
        mproc = Process(target=monitoringProcess)
        mproc.start()
        SetLastRow()
        while True:
            uproc = Process(target=uploadingProcess, args=(True,))
            uproc.start()
            print('UploadProcess::Start::PID %d' %(uproc.pid))
            while uproc.is_alive():
                pass
            del(uproc)
    except KeyboardInterrupt:
        mproc.terminate()
        uproc.join()
        raise
    except:
        pass

if __name__=="__main__":
    main()










