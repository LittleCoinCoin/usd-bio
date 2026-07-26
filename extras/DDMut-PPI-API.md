API - Documentation  
Here we offer an API (Application Programming Interface) to assist users in  
integrating DDMut-PPI into their research pipelines.  
In  summary,  all  jobs  submitted  to  our  server  are  labelled  with  a  unique  ID  
which is used to query the status (in queue, processing, processed).  
DDMut-PPI allows for six distinct types of submissions:

[Single Prediction  
](cleans.html#1)[List Prediction  
](cleans.html#3)[Alanine Scanning  
](cleans.html#5)[Saturation Mutagenesis  
](cleans.html#6)[Multiple Mutations: Manual Prediction  
](cleans.html#8)[Multiple Mutations: Systematic Evaluation](cleans.html#10)

Single Prediction -  
<http://biosig.lab.uq.edu.au/ddmut_ppi/api/single>

POST - Job Submission  
Arguments

pdb_accession (optional) - 4 character PDB code  
pdb_file (optional) -[ file in PDB format  
](http://www.wwpdb.org/documentation/file-format.php)chain (required) - Chain identifier  
mutation(required) - Point mutation code (aaFrom + residueNumber +  
aaTo)  
Reverse (optional) - Whether to predict reverse mutations (True/False).  
Default is False  
email (optional) - Email for contact when the job is finished

Return

job_id - ID used for uniquely identify each job

Examples

curl  
\$ 

curl

https://biosig.lab.uq.edu.au/ddmut_ppi/api/single 

-X

POST 

-i 

-F 

pdb_file=@/home/ubuntu/1cse.pdb 

-F

mutation=L45G -F chain=I -F reverse=True  
HTTP/1.0 200 OK  
Content-Type: application/json  
Content-Length: 38  
Date: Tue, 21 Nov 2023 04:36:23 GMT  
{  
"job_id": "17005413833647785"  
}

GET - Retrieve Job Results  
Arguments

job_id  -  ID  used  for  uniquely  identify  each  job.  Generated  upon  
submission

Return  
For jobs still being processed or waiting on queue, the message below will be  
returned from querying this endpoint:

[message - RUNNING](https://biosig.lab.uq.edu.au/ddmut_ppi/)

[For jobs suc](https://biosig.lab.uq.edu.au/ddmut_ppi/api#)[cessfully pr](https://biosig.lab.uq.edu.au/ddmut_ppi/datasets)[oc](https://biosig.lab.uq.edu.au/ddmut_ppi/help)[essed b](https://biosig.lab.uq.edu.au/ddmut_ppi/api)[y DDMut-PPI](https://biosig.lab.uq.edu.au/ddmut_ppi/privacy)[, the following da](https://biosig.lab.uq.edu.au/contact)[ta will be  
](https://biosig.lab.uq.edu.au/acknowledgements)[returned](https://biosig.lab.uq.edu.au/ddmut_ppi/api#)[:](https://biosig.lab.uq.edu.au/ddmut_ppi/datasets)

[prediction -](https://biosig.lab.uq.edu.au/tools)

[Examples](https://biosig.lab.uq.edu.au/tools)

curl  
\$ 

curl

https://biosig.lab.uq.edu.au/ddmut_ppi/api/single 

-X

GET -F job_id=17005413833647785  
HTTP/1.0 200 OK  
Content-Type: application/json  
Content-Length: 33  
Date: Wed, 10 Jun 2022 05:10:59 GMT  
{  
"job_id": "17005413833647785",  
"status": "DONE",  
"prediction": -3.323,  
"prediction_reverse": 2.905,  
"chain": "I",

[DDMut-PPI](https://biosig.lab.uq.edu.au/ddmut_ppi/)

[](https://biosig.lab.uq.edu.au/ddmut_ppi/api#)

[](https://biosig.lab.uq.edu.au/ddmut_ppi/api#)

[Run](https://biosig.lab.uq.edu.au/ddmut_ppi/api#)

[Data](https://biosig.lab.uq.edu.au/ddmut_ppi/datasets)

[Help](https://biosig.lab.uq.edu.au/ddmut_ppi/help)

[API](https://biosig.lab.uq.edu.au/ddmut_ppi/api)

[Privacy](https://biosig.lab.uq.edu.au/ddmut_ppi/privacy)

[Contact](https://biosig.lab.uq.edu.au/contact)

[Acknowledgements](https://biosig.lab.uq.edu.au/acknowledgements)

[Related Resources](https://biosig.lab.uq.edu.au/tools)

"position": 45,  
"wild-type": "LEU",  
"mutant": "GLY",  
"distance_to_interface": 2.72,  
"results_page":  
"https://biosig.lab.uq.edu.au/ddmut_ppi/results_prediction/17005413833647785",  
}

List Prediction -  
<http://biosig.lab.uq.edu.au/ddmut_ppi/api/list>

POST - Job Submission  
Arguments

pdb_accession (optional) - 4 character PDB code  
pdb_file (optional) -[ file in PDB format  
](http://www.wwpdb.org/documentation/file-format.php)mutation_list  (required)  -  .txt  or  .csv  file  with  mutation  list.  One  
mutation code per line (aaFrom + residueNumber + aaTo). Limited up to  
500 mutations.  
Reverse (optional) - Whether to predict reverse mutations (True/False).  
Default is False

Return

job_id - ID used for uniquely identify each job

Examples

curl  
\$  curl  https://biosig.lab.uq.edu.au/ddmut_ppi/api/list  
-X  POST  -i  -F  pdb_file=@/home/ubuntu/1cse.pdb  -F  
mutations_list=@/home/ubuntu/mutations.txt  
HTTP/1.0 200 OK  
Content-Type: application/json  
Content-Length: 33  
Date: Tue, 21 Nov 2023 05:15:45 GMT  
{  
"job_id": "17005437412529573"  
}

GET - Retrieve Job Results  
Arguments

job_id  -  ID  used  for  uniquely  identify  each  job.  Generated  upon  
submission

Return  
For jobs still being processed or waiting on queue, the message below will be  
returned from querying this endpoint:

message - RUNNING

For jobs successfully processed by DDMut-PPI, the following data will be  
returned:

Array list of results (in [json f](https://en.wikipedia.org/wiki/JSON)ormat) for each mutation identified with a  
sequencial identifying number

Examples

curl  
\$  curl  https://biosig.lab.uq.edu.au/ddmut_ppi/api/list  
-X GET -F job_id=16649535589333909  
{  
"job_id": "16649535589333909",  
"status": "DONE",  
"results_page":  
"http://10.50.192.76:5000/results_prediction/16649535589333909",  
"I_L45A": {  
"chain": "I",  
"wild-type": "L",  
"mutant": "A",  
"position": "45",  
"prediction": -1.97,  
"outcome": "Decreasing"  
},  
"I_L45K": {  
"chain": "I",  
"wild-type": "L",  
"mutant": "K",  
"position": "45",  
"prediction": -2.787,  
"outcome": "Decreasing"  
},  
...  
}

Alanine Scanning -  
<http://biosig.lab.uq.edu.au/ddmut_ppi/api/interface>

POST - Job Submission  
Arguments

pdb_accession (optional) - 4 character PDB code  
pdb_file (optional) -[ file in PDB format](http://www.wwpdb.org/documentation/file-format.php)

Return

job_id - ID used for uniquely identify each job

Examples

curl  
\$ 

curl

https://biosig.lab.uq.edu.au/ddmut_ppi/api/interface  -  
X  POST  -i  -F  pdb_file=@/home/ubuntu/1cse.pdb  -F  
analysis_type='alascan'  
HTTP/1.0 200 OK  
Content-Type: application/json  
Content-Length: 33  
Date: Tue, 21 Nov 2023 05:10:59 GMT  
{  
"job_id": "16705716575422666"  
}

GET - Retrieve Job Results  
Arguments

job_id  -  ID  used  for  uniquely  identify  each  job.  Generated  upon  
submission

Return  
For jobs still being processed or waiting on queue, the message below will be  
returned from querying this endpoint:

message - RUNNING

For jobs successfully processed by DDMut-PPI, the following data will be  
returned:

Array list of results (in [json f](https://en.wikipedia.org/wiki/JSON)ormat) for each mutation identified with a

sequential identifying number

Examples

curl  
\$ 

curl

https://biosig.lab.uq.edu.au/ddmut_ppi/api/interface  -  
X GET -F job_id=16705716575422666  
{  
"job_id": "16705716575422666",  
"status": "DONE",  
"results_page":  
"http://10.50.192.76:5000/results_prediction/16705716575422666",  
"I_L45A": {  
"chain": "I",  
"wild-type": "L",  
"mutant": "A",  
"position": "45",  
"prediction": -1.97,  
"outcome": "Decreasing"  
},  
"I_L37A": {  
"chain": "I",  
"wild-type": "L",  
"mutant": "K",  
"position": "45",  
"prediction": -2.787,  
"outcome": "Decreasing"  
},  
...  
}

Saturation Mutagenesis -  
<http://biosig.lab.uq.edu.au/ddmut_ppi/api/interface>

POST - Job Submission  
Arguments

pdb_accession (optional) - 4 character PDB code  
pdb_file (optional) -[ file in PDB format](http://www.wwpdb.org/documentation/file-format.php)

Return

job_id - ID used for uniquely identify each job

Examples

curl  
\$ 

curl

https://biosig.lab.uq.edu.au/ddmut_ppi/api/interface  -  
X  POST  -i  -F  pdb_file=@/home/ubuntu/1cse.pdb  -F  
analysis_type='satmut'  
HTTP/1.0 200 OK  
Content-Type: application/json  
Content-Length: 33  
Date: Tue, 21 Nov 2023 05:10:59 GMT  
{  
"job_id": "16705716575422666"  
}

GET - Retrieve Job Results  
Arguments

job_id  -  ID  used  for  uniquely  identify  each  job.  Generated  upon  
submission

Return  
For jobs still being processed or waiting on queue, the message below will be  
returned from querying this endpoint:

message - RUNNING

For jobs successfully processed by DDMut-PPI, the following data will be  
returned:

Array list of results (in [json f](https://en.wikipedia.org/wiki/JSON)ormat) for each mutation identified with a  
sequential identifying number

Examples

curl  
\$ 

curl

https://biosig.lab.uq.edu.au/ddmut_ppi/api/interface  -  
X GET -F job_id=16705716575422666  
{  
"job_id": "16705716575422666",  
"status": "DONE",

"results_page":  
"http://10.50.192.76:5000/results_prediction/16705716575422666",  
"I_L45A": {  
"chain": "I",  
"wild-type": "L",  
"mutant": "A",  
"position": "45",  
"prediction": -1.97,  
"outcome": "Decreasing"  
},  
"I_L37A": {  
"chain": "I",  
"wild-type": "L",  
"mutant": "K",  
"position": "45",  
"prediction": -2.787,  
"outcome": "Decreasing"  
},  
...  
}

Multiple Mutations: Manual Prediction -  
<https://biosig.lab.uq.edu.au/ddmut_ppi/api/manual>

POST - Job Submission  
Arguments

pdb_accession (optional) - 4 character PDB code  
pdb_file (optional) -[ file in PDB format  
](http://www.wwpdb.org/documentation/file-format.php)mutations_list(required)  -  Upload  a  plain  text  file  with  one  multiple  
mutation per line. Limited up t[o 500 mutations. Download sample  
](https://biosig.lab.uq.edu.au/ddmut_ppi/static/mutations.txt)email (optional) - Email for contact when the job is finished

Return

job_id - ID used for uniquely identify each job

Examples

curl  
\$ 

curl

https://biosig.lab.uq.edu.au/ddmut_ppi/api/manual  -X

POST 

-i 

-F 

pdb_accession="1cse" 

-F

mutations_list=@/home/ubuntu/mutations.txt  
HTTP/1.0 200 OK  
Content-Type: application/json  
Content-Length: 33  
Date: Wed, 22 Nov 2023 05:10:59 GMT  
{  
"job_id": "160706007808"  
}

GET - Retrieve Job Results  
Arguments

job_id  -  ID  used  for  uniquely  identify  each  job.  Generated  upon  
submission

Return  
For jobs still being processed or waiting on queue, the message below will  
be returned from querying this endpoint:

message - RUNNING

For jobs successfully processed by DDMut-PPI, the following data will be  
returned:

prediction -

Examples

curl  
\$ 

curl

https://biosig.lab.uq.edu.au/ddmut_ppi/api/manual  -X  
GET -F job_id=160706007808  
HTTP/1.0 200 OK  
Content-Type: application/json  
Content-Length: 33  
Date: Wed, 22 Nov 2023 05:13:29 GMT  
{  
"E Q2M; I R48A; E T33A": {  
"average_distance": 22.14,  
"individual_predictions": {  
" E T33A": -0.71,  
" I R48A": -0.72,

"E Q2M": -0.163  
},  
"prediction": -1.27  
},  
"I D46A; I R48A": {  
"average_distance": 6.48,  
"individual_predictions": {  
" I R48A": -0.72,  
"I D46A": -2.287  
},  
"prediction": -2.29  
},  
"I D46A; I R48A; E T33A": {  
"average_distance": 11.29,  
"individual_predictions": {  
" E T33A": -0.71,  
" I R48A": -0.72,  
"I D46A": -2.287  
},  
"prediction": -2.89  
},  
"I D46A; I R48K": {  
"average_distance": 6.48,  
"individual_predictions": {  
" I R48K": -0.806,  
"I D46A": -2.287  
},  
"prediction": -2.27  
}  
}

Multiple Mutations: Systematic Evaluation -  
<https://biosig.lab.uq.edu.au/ddmut_ppi/api/systematic>

POST - Job Submission  
Arguments

pdb_accession (optional) - 4 character PDB code  
pdb_file (optional) -[ file in PDB format  
](http://www.wwpdb.org/documentation/file-format.php)chain_id  (required)  -  Chain  identifier  for  systematic  evaluation  of  
interface.

email (optional) - Email for contact when the job is finished

Return

job_id - ID used for uniquely identify each job

Examples

curl  
\$ 

curl

https://biosig.lab.uq.edu.au/ddmut_ppi/api/systematic  
-X  POST  -i  -F  pdb_file=@/home/ubuntu/1cse.pdb  -F  
chain="I"  
HTTP/1.0 200 OK  
Content-Type: application/json  
Content-Length: 33  
Date: Wed, 22 Nov 2023 03:11:09 GMT  
{  
"job_id": "160706129233"  
}

GET - Retrieve Job Results  
Arguments

job_id  -  ID  used  for  uniquely  identify  each  job.  Generated  upon  
submission

Return  
For jobs still being processed or waiting on queue, the message below will  
be returned from querying this endpoint:

message - RUNNING

For jobs successfully processed by DDMut-PPI, the following data will be  
returned:

Array list of results (in [json f](https://en.wikipedia.org/wiki/JSON)ormat) for each mutation identified with a  
sequencial identifying number

Examples

curl  
\$ 

curl

https://biosig.lab.uq.edu.au/ddmut_ppi/api/systematic

-X GET -F job_id=160706129233  
HTTP/1.0 200 OK  
Content-Type: application/json  
Content-Length: 33  
Date: Wed, 22 Nov 2023 08:01:12 GMT  
{  
"I T44P;I D46G;I L45G": {  
"avg_distance": 4.39,  
"individual_predictions": {  
"D46G": -2.057,  
"L45G": -2.019,  
"T44P": -3.271  
},  
"prediction": -5.98  
},  
"I T44P;I D46G;I V43P": {  
"avg_distance": 6.2,  
"individual_predictions": {  
"D46G": -2.057,  
"T44P": -3.271,  
"V43P": -1.899  
},  
"prediction": -6.01  
},  
"I T44P;I D46P;I L45D": {  
"avg_distance": 4.39,  
"individual_predictions": {  
"D46P": -2.838,  
"L45D": -2.257,  
"T44P": -3.271  
},  
"prediction": -6.07  
},  
"I T44P;I D46P;I L45E": {  
"avg_distance": 4.39,  
"individual_predictions": {  
"D46P": -2.838,  
"L45E": -1.892,  
"T44P": -3.271  
},  
"prediction": -5.94

},  
"I T44P;I D46P;I L45G": {  
"avg_distance": 4.39,  
"individual_predictions": {  
"D46P": -2.838,  
"L45G": -2.019,  
"T44P": -3.271  
},  
"prediction": -5.93  
},  
"I T44P;I D46P;I V43P": {  
"avg_distance": 6.2,  
"individual_predictions": {  
"D46P": -2.838,  
"T44P": -3.271,  
"V43P": -1.899  
},  
"prediction": -6.09  
},  
"I T44P;I D46V;I L45E": {  
"avg_distance": 4.39,  
"individual_predictions": {  
"D46V": -1.992,  
"L45E": -1.892,  
"T44P": -3.271  
},  
"prediction": -5.94  
},  
"I T44P;I D46V;I V43P": {  
"avg_distance": 6.2,  
"individual_predictions": {  
"D46V": -1.992,  
"T44P": -3.271,  
"V43P": -1.899  
},  
"prediction": -6.06  
},  
"I T44P;I L45D;I D46G": {  
"avg_distance": 4.39,  
"individual_predictions": {  
"D46G": -2.057,

[Biosig Lab   
](https://biosig.lab.uq.edu.au/)Our group is interested in developing and experimentally validating novel  
computational methods to exploit this data, enhancing the impact of genome  
sequencing, structural genomics, and functional genomics on biology and medicine.

Best viewed using [Chrome](http://www.google.com/chrome) on 1280x960 resolution and above

"L45D": -2.257,  
"T44P": -3.271  
},  
"prediction": -6.04  
},  
}
