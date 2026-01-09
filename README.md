# **Phishing Email Detection Using Machine Learning**

This project builds a phishing email detection system using machine learning techniques. It uses Natural Language Processing (NLP) for text vectorization and Random Forest classifier (or any other ML model) for classification. The goal is to detect whether an email is a phishing email or legitimate based on its content. <br> Author-Krish Gupta

---

## **Table of Contents**
- [Project Overview](#project-overview)
- [Features](#features)
- [Technologies Used](#technologies-used)
- [Installation](#installation)
- [Setup and Usage](#setup-and-usage)
  - [Step 1: Install Dependencies](#step-1-install-dependencies)
  - [Step 2: Preprocess Data](#step-2-preprocess-data)
  - [Step 3: Train the Model](#step-3-train-the-model)
  - [Step 4: Make Predictions](#step-4-make-predictions)
- [How It Works](#how-it-works)
- [How to Contribute](#how-to-contribute)
- [License](#license)

---

## **Project Overview**

This project detects phishing emails using machine learning. It involves several steps, including preprocessing raw email data, training a model using a labeled dataset, and using that model to predict whether new emails are phishing or legitimate.

---

## **Features**
- **Email Classification**: Classify emails into "Phishing" or "Not Phishing" based on their content.
- **Text Preprocessing**: The raw email text is converted into a feature vector using TF-IDF (Term Frequency - Inverse Document Frequency).
- **Model Training**: Train a machine learning model using various algorithms such as Random Forest, Logistic Regression, etc.
- **Prediction**: Predict whether a new email is phishing based on the trained model.

---

## **Technologies Used**
- **Python**: Programming language.
- **Scikit-learn**: Library for machine learning algorithms.
- **Pandas**: Data manipulation and analysis.
- **NumPy**: Library for numerical computing.
- **Flask** (optional): Can be used to deploy the model as a web service.
- **Pickle**: For saving and loading the trained model.

---

## **Installation**

### **1. Clone the Repository**
```bash
git clone https://github.com/yourusername/phishing-email-detection.git
cd phishing-email-detection


### **2. Set up a Virtual Environment (optional but recommended)**
```bash
python -m venv venv
```
Activate the virtual environment:
- **Windows**: 
  ```bash
  venv\bin
  cd venv\bin
  .\Activate or .\Activate.ps1 # For Windows u need to enter that in powershell 
  ```
- **macOS/Linux**: 
  ```bash
  source venv/bin/activate
  ```

### **3. Install Dependencies**
```bash
pip install -r requirements.txt
```

---

## **Setup and Usage**

### **Step 1: Install Dependencies**
Make sure all required libraries are installed:
```bash
pip install -r requirements.txt
```

### **Step 2: Preprocess Data**
Run the `preprocess.py` script to preprocess the raw data and save it as a pickle file:
```bash
python src/preprocess.py
```
This script:
- Loads the raw email dataset (`phishing_emails.csv`).
- Converts the email text into a numerical format using TF-IDF vectorization.
- Saves the processed data to `preprocessed_data.pkl`.

### **Step 3: Train the Model**
Train the machine learning model by running the `train.py` script:
```bash
python src/train.py
```
This script:
- Loads the preprocessed data.
- Splits it into training and testing sets.
- Trains a Random Forest classifier (or other ML models) using the training data.
- Saves the trained model to `phishing_detector.pkl`.

**Note**: To try a different model, replace the `RandomForestClassifier` in `train.py` with another algorithm, like `LogisticRegression`.

### **Step 4: Make Predictions**
Predict phishing emails using the `predict.py` script:
```bash
python src/predict.py
```
This script:
- Loads the trained model (`phishing_detector.pkl`) and vectorizer.
- Takes an input email and predicts whether it’s phishing or legitimate.

To test with your own email, modify the `email_text` variable in `predict.py`:
```python
email_text = "Your account has been compromised. Click here to reset your password."
```

---

## **How It Works**

### **1. Preprocessing**
- Converts raw email content into numerical feature vectors using TF-IDF vectorization. This calculates the importance of each word in the email relative to other emails.

### **2. Model Training**
- Trains a Random Forest model to classify emails as phishing or not based on text patterns.

### **3. Prediction**
- For a new email, the model predicts whether it is phishing or legitimate using the patterns it learned during training.

---

## **Troubleshooting Virtual Environment**
If the virtual environment becomes "locked" (you cannot install or uninstall packages), it may be due to a corrupted `pip` cache. To fix this:
1. Deactivate the virtual environment:
   ```bash
   deactivate
   ```
2. Remove the `venv` folder:
   ```bash
   rm -rf venv
   ```
3. Recreate and activate the virtual environment:
   ```bash
   python -m venv venv
   cd venv\bin
   \Activate or .\Activate.ps1 # For Windows u need to enter that in powershell 
   source venv/bin/activate  # For macOS/Linux
   ```
4. Reinstall dependencies:
   ```bash
   pip install -r requirements.txt
   ```

---

## **How to Contribute**

1. **Fork the repository** and clone it to your local machine.
2. **Make changes or improvements** and commit them.
3. **Push your changes** to your forked repository.
4. **Create a pull request** with a detailed description of the changes.

---
Execution Policies:
In PowerShell, you may encounter execution policy restrictions that prevent scripts from running. You need to set the execution policy appropriately (e.g., using Set-ExecutionPolicy Unrestricted -Scope Process) to allow the execution of Activate.ps1.

## **License**


📜 Copyright & Usage Disclaimer

© 2026 Krish Gupta. All rights reserved.
This project is the sole property of the developer.

Unauthorized copying, modification, redistribution, or commercial use of this project (in whole or in part) is strictly prohibited without explicit permission from the developer.
If you wish to:
Use this project
Modify it
Redistribute it
Include it in your own work
You must contact the developer first for permission.

📩 Contact Details
Telegram: https://t.me/KT777mia
Email: krishg1234567890@gmail.com





## 💰 Help Developer by Donating
  [![PayPal](https://img.shields.io/badge/PayPal-00457C?style=for-the-badge&logo=paypal&logoColor=white)](https://paypal.me/spookistud) [![Patreon](https://img.shields.io/badge/Patreon-F96854?style=for-the-badge&logo=patreon&logoColor=white)](https://patreon.com/Spookistud) [![Ko-Fi](https://img.shields.io/badge/Ko--fi-F16061?style=for-the-badge&logo=ko-fi&logoColor=white)](https://ko-fi.com/Putin) 
  
```
