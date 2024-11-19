# app/main.py
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List

app = FastAPI()

# Configure CORS to allow requests from your Next.js app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# app/main.py
@app.post("/api/analyze")
async def analyze_bill(
    files: List[UploadFile] = File(...),
    firstName: str = Form(...),
    lastName: str = Form(...),
    dateOfBirth: str = Form(...)
):
    try:
        demo_analysis = {
            "summary": f"Analysis for {firstName} {lastName}",
            "details": {
                "code_validation": {
                    "valid_codes": [
                        {"code": "86152", "description": "Cell enumeration & id", "type": "CPT"},
                        {"code": "B002", "description": "X-ray", "type": "HCPCS"}
                    ],
                    "invalid_codes": [],
                    "discrepancies": ["Minor pricing variance noted"],
                    "upcoding_risks": ["None detected"],
                    "errors": []
                },
                "ucr_validation": {
                    "procedure_analysis": [
                        {
                            "code": "86152",
                            "description": "Cell enumeration & id",
                            "billed_cost": 300,
                            "medicare_rate": 250,
                            "ucr_rate": 275,
                            "is_reasonable": True,
                            "comments": "Within acceptable range"
                        }
                    ],
                    "overall_assessment": "The charges appear to be within reasonable ranges",
                    "recommendations": ["Keep records for your files", "No immediate action needed"],
                    "references": [  # Add this references array
                        "Medicare Fee Schedule 2024",
                        "National UCR Database",
                        "Healthcare Bluebook"
                    ]
                }
            }
        }
        
        return {"analysis": demo_analysis}

    except Exception as e:
        print(f"Error processing request: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

# from fastapi import FastAPI, File, UploadFile, Form, HTTPException
# from fastapi.middleware.cors import CORSMiddleware
# from typing import List
# import uvicorn
# from pydantic import BaseModel
# from datetime import date
# import os
# from dotenv import load_dotenv
# # Update these imports to include 'app'
# from app.services.bill_analyzer import analyze_medical_bill
# from app.services.claude import analyze_with_claude
# from app.services.perplexity import search_ucr_rates
# # Load environment variables
# load_dotenv()

# app = FastAPI(title="Medical Bill Analyzer API")

# # Configure CORS
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["http://localhost:3000"],  # Your Next.js frontend URL
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# class AnalysisRequest(BaseModel):
#     first_name: str
#     last_name: str
#     date_of_birth: date


# @app.post("/api/analyze")
# async def analyze_bill(
#     files: List[UploadFile] = File(...),
#     firstName: str = Form(...),
#     lastName: str = Form(...),
#     dateOfBirth: str = Form(...)
# ):
#     try:
#         # Create basic user input structure
#         user_input = {
#             "patient_info": {
#                 "first_name": firstName,
#                 "last_name": lastName,
#                 "date_of_birth": dateOfBirth
#             }
#         }

#         # Analyze using the demo bill
#         analysis_result = await analyze_medical_bill(user_input)
        
#         return {"analysis": analysis_result}

#     except Exception as e:
#         print(f"Error processing request: {str(e)}")
#         raise HTTPException(status_code=500, detail=str(e))

# # @app.post("/api/analyze")
# # async def analyze_bill(
# #     files: List[UploadFile] = File(...),
# #     firstName: str = Form(...),  # Changed from first_name to match frontend
# #     lastName: str = Form(...),   # Changed from last_name to match frontend
# #     dateOfBirth: str = Form(...) # Changed from date_of_birth to match frontend
# # ):
# #     try:
# #         if not files:
# #             raise HTTPException(status_code=400, detail="No files uploaded")
        
# #         if len(files) > 10:
# #             raise HTTPException(status_code=400, detail="Maximum 10 files allowed")

# #         # Process uploaded files
# #         results = []
# #         for file in files:
# #             content = await file.read()
# #             try:
# #                 text_content = content.decode()
# #                 results.append(text_content)
# #             except UnicodeDecodeError:
# #                 # Handle binary files
# #                 results.append(str(content))

# #         # Create bill data structure
# #         bill_data = {
# #             "patient_info": {
# #                 "firstName": firstName,  # Match the frontend keys
# #                 "lastName": lastName,
# #                 "dateOfBirth": dateOfBirth
# #             },
# #             "file_contents": results
# #         }

# #         analysis_result = await analyze_medical_bill(bill_data)
# #         return {"analysis": analysis_result}

# #     except Exception as e:
# #         print(f"Error processing request: {str(e)}")  # Add logging
# #         raise HTTPException(status_code=500, detail=str(e))

# # if __name__ == "__main__":
# #     uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)