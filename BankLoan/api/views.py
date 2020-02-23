from django.shortcuts import render
from rest_framework import viewsets
from django.core import serializers
from rest_framework.response import Response
from rest_framework import status
from . forms import ApprovalForm
from django.http import HttpResponse
from django.http import JsonResponse
from django.contrib import messages
from . models import approvals
from . serializers import approvalsSerializers
import pickle
from keras import backend as K
import joblib
import numpy as np
from sklearn import preprocessing
import pandas as pd
from collections import defaultdict, Counter

class ApprovalsView(viewsets.ModelViewSet):
	queryset = approvals.objects.all()
	serializer_class = approvalsSerializers

def encode_onehot(df):
	ohe_col=joblib.load("api/allcol.pkl")
	cat_columns=['Gender','Married','Education','Self_Employed','Property_Area']
	df_processed = pd.get_dummies(df, columns=cat_columns)
	newdict={}
	for i in ohe_col:
		if i in df_processed.columns:
			newdict[i]=df_processed[i].values
		else:
			newdict[i]=0
	newdf=pd.DataFrame(newdict)
	return newdf

def approvereject(unit):
	try:
		mdl=joblib.load("api/bank_loan_model.pkl")
		scalers=joblib.load("api/scalers.pkl")
		X=scalers.transform(unit)
		y_pred=mdl.predict(X)
		y_pred=(y_pred>0.58)
		newdf=pd.DataFrame(y_pred, columns=['Status'])
		newdf=newdf.replace({True:'Approved', False:'Rejected'})
		K.clear_session()
		return (newdf.values[0][0],X[0])
	except ValueError as e:
		return (e.args[0])

def load_app(request): 
	if request.method=='POST':
		form=ApprovalForm(request.POST)
		if form.is_valid():
				Firstname = form.cleaned_data['firstname']
				Lastname = form.cleaned_data['lastname']
				Dependents = form.cleaned_data['Dependents']
				ApplicantIncome = form.cleaned_data['ApplicantIncome']
				CoapplicantIncome = form.cleaned_data['CoapplicantIncome']
				LoanAmount = form.cleaned_data['LoanAmount']
				Loan_Amount_Term = form.cleaned_data['Loan_Amount_Term']
				Credit_History = form.cleaned_data['Credit_History']
				Gender = form.cleaned_data['Gender']
				Married = form.cleaned_data['Married']
				Education = form.cleaned_data['Education']
				Self_Employed = form.cleaned_data['Self_Employed']
				Property_Area = form.cleaned_data['Property_Area']
				myDict = (request.POST).dict()
				df=pd.DataFrame(myDict, index=[0])
				answer=approvereject(encode_onehot(df))[0]
				Xscalers=approvereject(encode_onehot(df))[1]
				if int(df['LoanAmount'])<50000:
					if answer == 'Approved':
						messages.success(request,'Application Status: {}'.format(answer))
					else:
						messages.error(request,'Application Status: {}'.format(answer))
				else:
					messages.error(request,'Invalid: Your Loan Request Exceeds $50,000 Limit')
	
	form=ApprovalForm()
				
	return render(request, 'form.html', {'form':form})