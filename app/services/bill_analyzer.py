# services/bill_analyzer.py
from typing import Dict, List, Any
import json
from .claude import analyze_with_claude
from .perplexity import search_ucr_rates
from .database import load_cpt_database, load_medicare_database  

# app/services/bill_analyzer.py

async def ucr_validation(bill):
    medicare_rates = await load_medicare_database()
    discrepancies = []

    for procedure in bill["billing_details"]["procedure_codes"]:
        code = procedure["code"]
        description = procedure["description"]
        billed_cost = procedure["cost"]

        if code in medicare_rates:
            medicare_info = medicare_rates[code]
            
            discrepancies.append({
                "code": code,
                "description": medicare_info['description'],
                "billed_cost": billed_cost,
                "medicare_rate": medicare_info.get('payment_rate', 0),
                "apc": medicare_info['apc'],
                "code_found": True
            })
        else:
            discrepancies.append({
                "code": code,
                "description": description,
                "billed_cost": billed_cost,
                "medicare_rate": "Not available in database",
                "code_found": False
            })

    ucr_result = await search_ucr_rates(bill)

    prompt = f"""
    Analyze the following medical bill information:

    Medicare Discrepancies:
    {json.dumps(discrepancies, indent=2)}

    UCR Information:
    {ucr_result}

    Provide your analysis in the following JSON format:
    {{
        "ucr_validation": {{
            "procedure_analysis": [
                {{
                    "code": "...",
                    "description": "...",
                    "billed_cost": 0,
                    "medicare_rate": 0,
                    "ucr_rate": 0,
                    "is_reasonable": true/false,
                    "comments": "..."
                }}
            ],
            "overall_assessment": "...",
            "recommendations": ["..."]
        }}
    }}
    """

    result = await analyze_with_claude(prompt)
    return {"ucr_validation": result}

async def explanation_handler(results):
    report = "Explanation Summary:\n"
    for result in results:
        for key, value in result.items():
            report += f"{key}: {value}\n"

    prompt = f"""
    Please analyze this medical bill report and provide a structured response:

    {report}

    Provide your analysis in the following JSON format:
    {{
        "summary": "Brief overview of findings",
        "code_validation": {{
            "issues_found": true/false,
            "details": ["..."]
        }},
        "ucr_validation": {{
            "concerns": ["..."],
            "recommendations": ["..."]
        }},
        "overall_recommendation": "..."
    }}
    """

    return await analyze_with_claude(prompt)

async def analyze_medical_bill(user_input):
    # We'll use this sample bill for demo purposes
    demo_bill = {
        "patient_info": {
            "name": "John Doe",
            "ssn": "123-45-6789",
            "dob": "1990-01-01",
            "address": "123 Main St, Anytown, USA",
            "insurance_policy": "POLICY123",
        },
        "visit_info": {
            "date_of_visit": "2024-11-01",
            "provider_info": "Hospital ABC",
            "doctor": "Dr. Jane Smith",
            "location": "Outpatient",
        },
        "billing_details": {
            "charges": 1200,
            "procedure_codes": [
                {
                    "code": "86152",
                    "description": "Cell enumeration & id",
                    "quantity": 1,
                    "cost": 300
                },
                {
                    "code": "B002",
                    "description": "X-ray",
                    "quantity": 2,
                    "cost": 450
                }
            ],
            "total_cost": 1200,
            "insurance_coverage": 80,
            "amount_due": 240
        },
        "diagnoses": [
            {
                "code": "J01.90",
                "description": "Acute sinusitis",
                "severity": "Mild"
            },
            {
                "code": "R51",
                "description": "Headache",
                "severity": "Moderate"
            }
        ],
        "notes": "Follow-up recommended in 2 weeks."
    }

    try:
        # Use the demo bill but update it with user's info
        demo_bill["patient_info"].update({
            "name": f"{user_input['patient_info']['first_name']} {user_input['patient_info']['last_name']}",
            "dob": user_input['patient_info']['date_of_birth']
        })

        # Run the analyses using the demo bill
        results = []
        
        # Code validation
        code_result = await code_validation(demo_bill)
        results.append(code_result)
        
        # UCR validation
        ucr_result = await ucr_validation(demo_bill)
        results.append(ucr_result)

        # Final report
        final_report = await explanation_handler(results)
        
        try:
            return json.loads(final_report)
        except json.JSONDecodeError:
            return {"summary": final_report}

    except Exception as e:
        print(f"Error in analyze_medical_bill: {str(e)}")
        raise Exception(f"Analysis failed: {str(e)}")

async def code_validation(bill):
    icd_api = 'https://clinicaltables.nlm.nih.gov/api/icd10cm/v3/search'
    hcpcs_api = 'https://clinicaltables.nlm.nih.gov/api/hcpcs/v3/search'
    
    cpt_codes = await load_cpt_database()
    
    invalid_codes = []
    valid_codes = []

    # Process the codes from the demo bill
    for procedure in bill["billing_details"]["procedure_codes"]:
        code = procedure["code"]
        response = requests.get(icd_api, params={"terms": code, "sf": "code", "df": "code,name"})
        if response.status_code == 200:
            data = response.json()
            if data[1]:  # Valid ICD-10 code
                valid_codes.append({"code": code, "description": data[3][0][1], "type": "ICD-10"})
            else:  # Try HCPCS
                response = requests.get(hcpcs_api, params={"terms": code, "sf": "code", "df": "code,display"})
                if response.status_code == 200:
                    data = response.json()
                    if data[1]:  # Valid HCPCS code
                        valid_codes.append({"code": code, "description": data[3][0][1], "type": "HCPCS"})
                    else:
                        if code in cpt_codes:  # Check CPT
                            valid_codes.append({"code": code, "description": cpt_codes[code], "type": "CPT"})
                        else:
                            invalid_codes.append(code)

    prompt = (
        f"Analyze the following procedure codes and check for any discrepancies:\n\n"
        f"Valid Codes:\n{valid_codes}\n"
        f"Invalid Codes:\n{invalid_codes}\n\n"
        "Provide your analysis in the following JSON format:\n"
        "{\n"
        '  "code_validation": {\n'
        '    "valid_codes": [{"code": "...", "description": "...", "type": "..."}],\n'
        '    "invalid_codes": ["..."],\n'
        '    "discrepancies": ["..."],\n'
        '    "upcoding_risks": ["..."],\n'
        '    "errors": ["..."]\n'
        "  }\n"
        "}\n\n"
    )

    result = await analyze_with_claude(prompt)
    return {"code_validation": result}



# async def code_validation(bill: Dict[str, Any]) -> Dict[str, Any]:
#     try:
#       # sys.stderr.write("i pray to god sometimes")
#       # sys.stderr.flush()
#       icd_api = 'https://clinicaltables.nlm.nih.gov/api/icd10cm/v3/search'
#       hcpcs_api = 'https://clinicaltables.nlm.nih.gov/api/hcpcs/v3/search'
#       cpt_codes = load_cpt_database('cpt.txt')
      
#       invalid_codes = []
#       valid_codes = []

#       # check through RAG codes, mkae
#       for procedure in bill["billing_details"]["procedure_codes"]:
#           code = procedure["code"]
#           response = requests.get(icd_api, params={"terms": code, "sf": "code", "df": "code,name"})
#           if response.status_code == 200:
#               data = response.json()
#               if data[1]:  # Valid ICD-10 code
#                   valid_codes.append({"code": code, "description": data[3][0][1], "type": "ICD-10"})
#               else:  # If invalid as ICD-10, try HCPCS
#                   response = requests.get(hcpcs_api, params={"terms": code, "sf": "code", "df": "code,display"})
#                   if response.status_code == 200:
#                       data = response.json()
#                       if data[1]:  # Valid HCPCS code
#                           valid_codes.append({"code": code, "description": data[3][0][1], "type": "HCPCS"})
#                           check_price = ucr_validation(data[1])
#                       else:
#                           # if not HCPCS check for CPT
#                           if code in cpt_codes:
#                               valid_codes.append({"code": code, "description": cpt_codes[code], "type": "CPT"})
#                           else:
#                               invalid_codes.append(code)  # Invalid for ICD-10, HCPCS, and CPT
#                   else:
#                       print(f"Error querying cpt_.txt HCPCS API for code {code}: {response.status_code}")
#           else:
#               print(f"Error querying ICD-10 API for code {code}: {response.status_code}")
          

#       # prompt = (
#       #     f"Analyze the following procedure codes and check for any discrepancies in {bill['billing_details']['procedure_codes']}.  Make sure that is clear and categorized based on the type of code (ICD-10, HCPCS, CPT). :\n\n"
#       #     f"Valid Codes:\n{valid_codes}"
#       #     f"Invalid Codes:\n{invalid_codes}"
#       #     "Identify any possible discrepancies, upcoding, or errors. Make it clean and concise so the next agent can easily understand"
#       #     "Present it in a numbered list format with headers so it's clear and easy to understand. Ensure the sentences have sufficient information but aren't overloading the next AI Agent"
#       # )
#       #{bill['billing_details']['procedure_codes']} if u wanna refer to the json formatof medical bill
#       prompt = (
#           f"Analyze the following procedure codes and check for any discrepancies:\n\n"
#           f"Valid Codes:\n{valid_codes}\n"
#           f"Invalid Codes:\n{invalid_codes}\n\n"
#           "Provide your analysis in the following JSON format:\n"
#           "{\n"
#           '  "code_validation": {\n'
#           '    "valid_codes": [{"code": "...", "description": "...", "type": "..."}],\n'
#           '    "invalid_codes": ["..."],\n'
#           '    "discrepancies": ["..."],\n'
#           '    "upcoding_risks": ["..."],\n'
#           '    "errors": ["..."]\n'
#           "  }\n"
#           "}\n\n"
#           "Ensure the response is a valid JSON object. If there are no items for a category, use an empty array []."
#       )
#       result = analyze_with_claude(prompt)
#       return {"code_validation": result}
#     except Exception as e:
#         raise Exception(f"Code validation failed: {str(e)}")




# async def ucr_validation(bill: Dict[str, Any]) -> Dict[str, Any]:
#     try:
#       medicare_rates = load_medicare_database('./databases/medicare_rates.csv')
#       discrepancies = []
#       # location = bill["visit_info"]["location"]

#       for procedure in bill["billing_details"]["procedure_codes"]:
#           code = procedure["code"]
#           description = procedure.get("description", "Description not available")
#           billed_cost = procedure["cost"]

#           if code in medicare_rates:
#               medicare_info = medicare_rates[code]
#               payment_rate = medicare_info['Payment Rate']
              
#               discrepancies.append({
#                   "code": code,
#                   "description": medicare_info['Description'],
#                   "billed_cost": billed_cost,
#                   "medicare_rate": payment_rate,
#                   "difference": billed_cost - payment_rate,
#                   "percentage_difference": ((billed_cost - payment_rate) / payment_rate) * 100,
#                   "apc": medicare_info['APC'],
#                   "code_found": True
#               })
#           else:
#               discrepancies.append({
#                   "code": code,
#                   "description": description,
#                   "billed_cost": billed_cost,
#                   "medicare_rate": "Not available in database",
#                   "difference": "Unable to calculate",
#                   "percentage_difference": "Unable to calculate",
#                   "apc": "Not available",
#                   "code_found": False
#               })

#       # Search for UCR rates using Perplexity API
#       # sys.stderr.write("i need taco bell fr")
#       # sys.stderr.flush()
#       ucr_result = search_ucr_rates(bill)
#       # print(ucr_result)

#       prompt = f"""
#       Analyze the following medical bill information, including Medicare discrepancies and Usual Customary and Reasonable (UCR) rates:

#       Medicare Discrepancies:
#       {json.dumps(discrepancies, indent=2)}

#       UCR Information:
#       {ucr_result} which sould be saved as ucr_rate in the JSON file

#       Provide your analysis in the following JSON format:
#       {{
#           "ucr_validation": {{
#               "procedure_analysis": [
#                   {{
#                       "code": "...",
#                       "description": "...",
#                       "billed_cost": 0,
#                       "medicare_rate": 0,
#                       "ucr_rate": 0,
#                       "difference": 0,
#                       "percentage_difference": 0,
#                       "is_reasonable": true/false,
#                       "comments": "...",
#                       "sources": ["..."]
#                   }}
#               ],
#               "overall_assessment": "...",
#               "recommendations": [
#                   "..."
#               ],
#               "references": [
#                   "..."
#               ]
#           }}
#       }}

#       For each procedure:
#       1. If Medicare rate is available, use it for comparison.
#       2. Use the UCR rate from the Perplexity API result for comparison.
#       3. Calculate differences and percentage differences using both Medicare (if available) and UCR rates.
#       4. Determine if the billed amount is reasonable compared to Medicare and UCR rates.
#       5. Provide comments on any significant discrepancies.
#       6. Include the sources used for rates.

#       In the "overall_assessment" field, summarize your findings and whether the overall bill appears reasonable.
#       In the "recommendations" array, suggest next steps for the patient based on your analysis.
#       In the "references" array, include any references or sources mentioned in the UCR info.

#       Ensure the response is a valid JSON object. Include all relevant information from your analysis while maintaining the specified structure.
#       """

#       result = analyze_with_claude(prompt)

#       # Ensure the result is valid JSON
#       # json_result = json.loads(result)
#       # return {"ucr_validation": json_result}
#       return {"ucr_validation": result}
#     except Exception as e:
#         raise Exception(f"UCR validation failed: {str(e)}")

# async def fraud_detection(bill: Dict[str, Any]) -> Dict[str, Any]:
#     try:
#         prompt = prompt = f"""
#         Detect any potential fraud indicators in the following provider information:
#         {bill['provider_info']}

#         Provide your analysis in the following JSON format:
#         {{
#         "fraud_detection": {{
#             "potential_indicators": [
#             {{
#                 "type": "...",
#                 "description": "...",
#                 "severity": "..."
#             }}
#             ],
#             "overall_risk_assessment": "...",
#             "recommendations": [
#             "..."
#             ]
#         }}
#         }}

#         Ensure the response is a valid JSON object. If no potential fraud indicators are found, use an empty array for 'potential_indicators'.
#         """
#         result = await analyze_with_claude(prompt)
#         return {"fraud_detection": result}
#     except Exception as e:
#         raise Exception(f"Fraud detection failed: {str(e)}")

# async def analyze_medical_bill(bill: Dict[str, Any]) -> Dict[str, Any]:
#     try:
#         # Run all analyses concurrently
#         import asyncio
#         results = await asyncio.gather(
#             code_validation(bill),
#             ucr_validation(bill),
#             fraud_detection(bill)
#         )
        
#         # Compile results
#         compiled_results = {}
#         for result in results:
#             compiled_results.update(result)
            
#         return compiled_results
#     except Exception as e:
#         raise Exception(f"Analysis failed: {str(e)}")

