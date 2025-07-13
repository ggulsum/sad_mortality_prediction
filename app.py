import streamlit as st
import pandas as pd
import joblib
import json
import plotly.graph_objects as go
from utils.model_helper import prepare_features, predict_risks

# === SAYFA AYARLARI ===
st.set_page_config(page_title="Sepsis Risk Tahmini", layout="wide")
st.title("Sepsis Hastalarında Risk Tahmini Uygulaması")

# === MODEL YÜKLEME ===
@st.cache_resource
def load_model():
    return joblib.load("prediction/model.pkl")

@st.cache_data
def load_features():
    with open("prediction/selected_features.json", "r") as f:
        return json.load(f)

model = load_model()
feature_dict = load_features()
sel_mort = feature_dict["mortality"]
sel_del = feature_dict["delirium"]

# === CSV YÜKLEME ===
uploaded_file = st.file_uploader("📁 Hasta verilerini yükleyin (CSV)", type="csv")

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    st.success("✅ Dosya yüklendi.")

    subject_ids = df['subject_id'].unique()
    selected_id = st.selectbox("🔍 Bir subject_id seçin:", subject_ids)

    if selected_id:
        patient_data = df[df['subject_id'] == selected_id].copy()

        try:
            # === ÖZELLİK HAZIRLAMA & TAHMİN ===
            X_mort, X_del = prepare_features(patient_data, sel_mort, sel_del)
            mort_risk, del_risk = predict_risks(model, X_mort, X_del)

            # === EN ÜSTE: TAHMİN SONUÇLARI ===
            st.markdown("## 📊 Tahmin Sonuçları")

            col1, col2 = st.columns(2)

            with col1:
                st.markdown("#### 🔴 14 Günlük Mortalite Riski Tahmini")
                fig1 = go.Figure(go.Indicator(
                    mode="gauge+number",
                    value=mort_risk * 100,
                    title={'text': "Mortalite Riski (%)"},
                    gauge={
                        'axis': {'range': [0, 100], 'tickwidth': 1},
                        'bar': {'color': "darkred"},
                        'bgcolor': "white",
                        'steps': [
                            {'range': [0, 50], 'color': "lightgray"},
                            {'range': [50, 100], 'color': "salmon"}
                        ],
                        'threshold': {
                            'line': {'color': "red", 'width': 4},
                            'thickness': 0.75,
                            'value': mort_risk * 100
                        }
                    },
                    domain={'x': [0, 1], 'y': [0, 1]}
                ))
                st.plotly_chart(fig1, use_container_width=True)
                st.markdown(f"**Gerçek Etiket:** {'🟢 Hayatta' if patient_data['mortality'].values[0] == 0 else '🔴 Vefat Etti'}")

            with col2:
                st.markdown("#### 🟣 24 Saatlik Deliryum Riski Tahmini")
                fig2 = go.Figure(go.Indicator(
                    mode="gauge+number",
                    value=del_risk * 100,
                    title={'text': "Deliryum Riski (%)"},
                    gauge={
                        'axis': {'range': [0, 100], 'tickwidth': 1},
                        'bar': {'color': "purple"},
                        'bgcolor': "white",
                        'steps': [
                            {'range': [0, 50], 'color': "lightgray"},
                            {'range': [50, 100], 'color': "#dda0dd"}
                        ],
                        'threshold': {
                            'line': {'color': "purple", 'width': 4},
                            'thickness': 0.75,
                            'value': del_risk * 100
                        }
                    },
                    domain={'x': [0, 1], 'y': [0, 1]}
                ))
                st.plotly_chart(fig2, use_container_width=True)
                st.markdown(f"**Gerçek Etiket:** {'🟢 Deliryum Yok' if patient_data['delirium_positive'].values[0] == 0 else '🟣 Deliryum Var'}")

        except Exception as e:
            st.error(f"🚨 Tahmin sırasında hata oluştu: {str(e)}")

        # === HASTA BİLGİLERİ ve KOMORBİDİTE ===
        st.markdown("## 🩺 Hasta Bilgileri ve Komorbiditeler")

        display_cols = ["age", "icu_los", "sofa_score", "gcs", "sapsii", "charlson_comorbidity_index"]

        comorbid_cols = [
            "diabetes", "hypertension", "renal_failure", "pulmonary", "cardiovascular",
            "liver_failure", "ami", "ckd", "copd", "heart_failure", "malignant_tumor"
        ]

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### 🧾 Temel Bilgiler")
            rounded_data = patient_data[display_cols].round(0).astype(int).T
            rounded_data.columns = ["Değer"]
            st.table(rounded_data)

        with col2:
            st.markdown("### 🦠 Komorbiditeler")
            existing_comorb_cols = [col for col in comorbid_cols if col in patient_data.columns]

            if existing_comorb_cols:
                comorbidity_status = patient_data[existing_comorb_cols].astype(int).T
                comorbidity_status.columns = ["Durum"]
                comorbidity_status["Durum"] = comorbidity_status["Durum"].map({0: "❌", 1: "✅"})
                st.table(comorbidity_status)
            else:
                st.warning("⚠️ Komorbidite bilgileri eksik.")
else:
    st.info("📌 Devam etmek için bir CSV dosyası yükleyin.")
