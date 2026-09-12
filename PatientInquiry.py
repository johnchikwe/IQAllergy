import streamlit as st
from PIL import Image
import os # Still need import of the PDF 
import pdfplumber
import json
from openai import OpenAI




# Page Configuration
st.set_page_config(page_title="IgE Allergy Translator", layout="wide")

st.title("🩺 96-Food IgE Lab Panel Translator")
st.write("Upload a lab result or prescription image/PDF to translate into plain English instructions.")

api_key = os.getenv("OPENAI_API_KEY") or st.sidebar.text_input("OpenAI API Key", type="password")

# Create Two Columns for the Layout
col1, col2 = st.columns([1, 1])

extracted_text = ""

with col1:
    st.header("1. Lab Result Input")
    
    # File Uploader Widget
    # uploaded_file = st.file_uploader(
    #     "Choose a Lab Report or Prescription image...", 
    #     type=["png", "jpg", "jpeg", "pdf"]
    # )
    
    uploaded_file = st.file_uploader("Or Upload PDF Report", type=["pdf"])

    if uploaded_file:
        with pdfplumber.open(uploaded_file) as pdf:
            for page in pdf.pages:
                extracted_text += page.extract_text() + "\n"

        with st.expander("Preview Raw Extracted PDF Text"):
            st.text(extracted_text[:1000] + "...")

        analyze_btn = st.button("Translate PDF Panel", type="primary")


with col2:
    st.header("2. Patient Action Plan")

    if uploaded_file and ('analyze_btn' in locals() and analyze_btn):
        if not api_key:
            st.error("Please add your OpenAI API Key to proceed.")
        else:
            client = OpenAI(api_key=api_key)
            with st.spinner("Agent parsing PDF & building diet plan..."):
                system_prompt = """
                You are an expert allergy & clinical nutrition agent. 
                Extract elevated allergens from the raw PDF text and output strict JSON:
                {
                  "total_ige": "e.g. 550 IU/mL (Elevated)",
                  "high_reactive": [
                    {"food": "Hazelnut", "level": "1.07 kU/L", "class": "High", "swap": "Sunflower seeds or Pumpkin seed butter"}
                  ],
                  "mild_reactive": [
                    {"food": "Almond", "level": "0.28 kU/L", "class": "Mild", "advice": "Rotate diet - eat once every 4 days"}
                  ],
                  "safe_foods": ["Rice", "Coconut", "Brazil Nut"],
                  "doctor_questions": ["Should I carry an EpiPen given the Total IgE elevation?"]
                }
                """

                response = client.chat.completions.create(
                    model="gpt-4o",
                    response_format={"type": "json_object"},
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": f"Parse this lab text:\n{extracted_text}"}
                    ]
                )

                data = json.loads(response.choices[0].message.content)
                
                st.subheader(f"📊 Overall IgE Status: {data.get('total_ige', 'N/A')}")
                
                st.error("🔴 **High Reactivity (Strict Avoidance & Swaps)**")
                for item in data.get("high_reactive", []):
                    st.write(f"- **{item['food']}** ({item['level']}): Swap with *{item['swap']}*")
                
                st.warning("🟡 **Mild Reactivity (Rotation Strategy)**")
                for item in data.get("mild_reactive", []):
                    st.write(f"- **{item['food']}** ({item['level']}): {item['advice']}")
                    
                st.success("🟢 **Safe Core Grocery List**")
                st.write(", ".join(data.get("safe_foods", [])))
                
                st.info("📋 **Questions for Your Doctor**")
                for q in data.get("doctor_questions", []):
                    st.write(f"- {q}")

# with col2:
#     st.header("2. Patient Action Plan")
    
#     if uploaded_file is not None and analyze_btn:
#         st.info("Translating your document...")
        
#         # Placeholder output to simulate model response
#         st.subheader("📋 Plain English Summary")
#         st.write("This document shows standard blood test results with elevated glucose levels.")
        
#         st.subheader("⚠️ Flagged Findings")
#         st.warning("Fasting Blood Sugar: 115 mg/dL (Slightly Above Normal: 70-99 mg/dL)")
        
#         st.subheader("🗓️ Daily Action Plan")
#         st.markdown("- **Morning:** Drink 16 oz of water before breakfast.") # this is just a test and is meant to showcase streamlit
#         st.markdown("- **Next Steps:** Schedule follow-up check in 3 months.")
#     else:
#         st.write("Upload a document on the left and click **Analyze & Translate** to view results.")