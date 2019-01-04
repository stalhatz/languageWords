from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
import pandas as pd
import numpy as np
import pdb
import openpyxl as oxl
import pickle
def storeFileFromGoogleDrive(folderName, filename , mimetype ):
  gauth = GoogleAuth()
  # Try to load saved client credentials
  gauth.LoadCredentialsFile("mycreds.txt")
  if gauth.credentials is None:
    # Authenticate if they're not there
    gauth.LocalWebserverAuth()
  elif gauth.access_token_expired:
    # Refresh them if expired
    gauth.Refresh()
  else:
    # Initialize the saved creds
    gauth.Authorize()
  gauth.SaveCredentialsFile("mycreds.txt")
  drive = GoogleDrive(gauth)
  folderName = "'" + folderName + "'"
  fileList = drive.ListFile({'q': folderName + " in parents"}).GetList()
  #Print document titles in folder
  for i,file in enumerate(fileList):
      print(str(i) + " :: " + file.metadata["title"])
  a = fileList[0].GetContentFile(filename, mimetype)

def readData(fn):
  table = pd.read_csv(fn, decimal = ',')
  return table

def readFileFromGoogleDrive(folderName="1Pv9g4vpso0a4nGEP1lbQqCKygHmVnMlX", filename="Travail_Stavros.xlsx", mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'):
  #storeFileFromGoogleDrive(folderName, filename , mimetype)
  #Unnormalized table
  
  wb = oxl.load_workbook(filename)
  #_jobs = readData(filename)
  words = {}
  for col in wb.get_active_sheet().columns:
    for numRow,cell in enumerate(col):
      if numRow==0:
        category = cell.value
      elif cell.value is not None: 
        text = cell.value
        if "HYPERLINK" in text:
          a = text.strip("=HYPERLINK(\"").rstrip("\")").split("\",\"")
          words[a[1]] = [a[0] , category]
  return words

def saveToPickle(a, filename):
  with open(filename, 'wb') as output:
    pickle.dump(a, output, pickle.HIGHEST_PROTOCOL)

words = readFileFromGoogleDrive()
saveToPickle(words, "dictWords.pkl")
