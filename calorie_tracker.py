import math
import json

import numpy as np
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split

PRIMARY_COLOR = "#007A3D"

# ------------------------------------------------------------
#   CSV SOURCE
#   1. Try local "calories.csv"
#   2. If missing, fall back to GitHub URL
# ------------------------------------------------------------
CSV_URL = "https://raw.githubusercontent.com/philippdmt/Protein_and_Calories/refs/heads/main/calories.csv"


# -----------------------------
# DATA + MODEL LOADING
# -----------------------------
def determine_training_type(heart_rate, age):
    """Bestimme Trainingstyp anhand Herzfrequenz und Alter."""
    if heart_rate >= 0.6 * (220 - age):
        return "Cardio"
    else:
        return "Kraft"


@st.cache_data
def load_and_train_model():
    """
    Läd den Datensatz, trainiert ein Lineares Regressionsmodell
    und gibt (modell, feature_spalten_liste) zurück.

    Versucht zuerst 'calories.csv' lokal, fällt sonst auf CSV_URL zurück.
    """
    try:
        # 1) Versuch: lokale Datei
        calories = pd.read_csv("calories.csv")
    except FileNotFoundError:
        # 2) Fallback: GitHub-URL
        calories = pd.read_csv(CSV_URL)

    # Training_Type ableiten
    calories["Training_Type"] = calories.apply(
        lambda row: determine_training_type(row["Heart_Rate"], row["Age"]), axis=1
    )

    # Zielvariable
    y = calories["Calories"]

    # Features (ohne User_ID, Heart_Rate, Body_Temp, Calories)
    features = calories.drop(columns=["User_ID", "Heart_Rate", "Body_Temp", "Calories"])

    # One-hot Encoding
    X = pd.get_dummies(features, columns=["Gender", "Training_Type"], drop_first=False)

    # Train/Test Split
    X_train, X_test, y_train, y_test = train_test_split(X, y, random_state=42)

    model = LinearRegression()
    model.fit(X_train, y_train)

    return model, X.columns.tolist()


# -----------------------------
# BMR CALCULATION
# -----------------------------
def grundumsatz(age, weight, height, gender):
    """Mifflin–St Jeor BMR equation."""
    if gender.lower() == "male":
        return 10 * weight + 6.25 * height - 5 * age + 5
    else:
        return 10 * weight + 6.25 * height - 5 * age - 161


# -----------------------------
# DONUT CHART
# -----------------------------
def donut_chart(consumed, total, title, unit):
    if total <= 0:
        total = 1

    consumed = max(0, consumed)
    remaining = max(total - consumed, 0)

    # Farbe: grün normal, rot wenn Ziel überschritten
    color = "#007A3D" if consumed <= total else "#FF0000"

    fig, ax = plt.subplots(figsize=(3, 3), facecolor="white")
    ax.pie(
        [consumed, remaining],
        startangle=90,
        counterclock=False,
        colors=[color, "#E0E0E0"],
        wedgeprops={"width": 0.35, "edgecolor": "white"},
    )
    ax.set(aspect="equal")
    ax.set_title(title)

    ax.text(
        0,
        0,
        f"{int(consumed)} / {int(total)} {unit}",
        ha="center",
        va="center",
        fontsize=10,
    )

    st.pyplot(fig)


# -----------------------------
# MAIN (EMBEDDED INTO APP.PY)
# -----------------------------
def main():
    # Kein st.set_page_config hier – das macht app.py schon!

    # In app.py steht bereits:
    # st.header("Calorie tracker"), st.divider(), Container, etc.
    # Hier also "eine Ebene tiefer" bleiben:
    st.subheader("Pumpfessor Joe – Nutrition Planner")
    st.write(
        "Automatic calculation of calories and protein based on training and body data."
    )

    # Load ML model
    try:
        model, feature_columns = load_and_train_model()
    except Exception as e:
        st.error("Error while loading the dataset / model. Check the CSV source.")
        st.exception(e)
        return

    # Initialize session state
    if "meals" not in st.session_state:
        st.session_state.meals = []

    # -----------------------------
    # USER INPUT
    # -----------------------------
    st.markdown("### Personal & workout information")
    col1, col2 = st.columns(2)
    with col1:
        gender = st.selectbox("Gender", ["Male", "Female"])
        age = st.number_input("Age", 0, 100, 25)
        height = st.number_input("Height (cm)", 120, 230, 180)
        weight = st.number_input("Weight (kg)", 35, 200, 75)

    with col2:
        goal = st.selectbox("Goal", ["Cut", "Maintain", "Bulk"])
        training_type = st.selectbox("Training type", ["Cardio", "Kraft"])
        duration = st.number_input("Training duration (min)", 10, 240, 60)

    # -----------------------------
    # CALCULATIONS
    # -----------------------------
    person = {
        "Age": age,
        "Duration": duration,
        "Weight": weight,
        "Height": height,
        "Gender_Female": 1 if gender.lower() == "female" else 0,
        "Gender_Male": 1 if gender.lower() == "male" else 0,
        "Training_Type_Cardio": 1 if training_type.lower() == "cardio" else 0,
        "Training_Type_Kraft": 1 if training_type.lower() == "kraft" else 0,
    }

    person_df = pd.DataFrame([person])
    person_df = person_df.reindex(columns=feature_columns, fill_value=0)

    training_kcal = float(model.predict(person_df)[0])
    bmr = grundumsatz(age, weight, height, gender)

    # Goal adjustments
    if goal.lower() == "bulk":
        target_calories = bmr + training_kcal + 300
        protein_per_kg = 2.0
    elif goal.lower() == "cut":
        target_calories = bmr + training_kcal - 300
        protein_per_kg = 2.2
    else:
        target_calories = bmr + training_kcal
        protein_per_kg = 1.6

    target_calories = max(target_calories, 1200)
    target_protein = protein_per_kg * weight

    # -----------------------------
    # MEAL LOGGING
    # -----------------------------
    st.markdown("### Log meals")
    with st.form("meal_form"):
        m1, m2, m3 = st.columns([2, 1, 1])
        meal_name = m1.text_input("Meal name", "Chicken & rice")
        meal_cal = m2.number_input("Calories", 0, 3000, 500)
        meal_prot = m3.number_input("Protein (g)", 0, 200, 30)
        submitted = st.form_submit_button("Add meal")

    if submitted:
        st.session_state.meals.append(
            {
                "meal": meal_name,
                "calories": float(meal_cal),
                "protein": float(meal_prot),
            }
        )

    # Reset meals
    if st.button("Reset meals"):
        st.session_state.meals = []

    # -----------------------------
    # TOTALS
    # -----------------------------
    total_cal = sum(m["calories"] for m in st.session_state.meals)
    total_prot = sum(m["protein"] for m in st.session_state.meals)

    # -----------------------------
    # DONUT CHARTS
    # -----------------------------
    st.markdown("### Daily targets")
    c1, c2 = st.columns(2)
    with c1:
        donut_chart(total_cal, target_calories, "Calories", "kcal")
    with c2:
        donut_chart(total_prot, target_protein, "Protein", "g")

    # -----------------------------
    # MEAL TABLE
    # -----------------------------
    if st.session_state.meals:
        st.markdown("### Logged meals")
        st.table(pd.DataFrame(st.session_state.meals))


if __name__ == "__main__":
    main()