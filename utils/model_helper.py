# utils/model_helper.py

import pandas as pd
import numpy as np

def prepare_features(df, sel_mort, sel_del):
    """
    Sadece gerekli kolonları almak icin
    """
    X_mort = df[sel_mort].values
    X_del = df[sel_del].values
    return X_mort, X_del

def predict_risks(model, X_mort, X_del):
    """
    İki hedef için (mortalite ve deliryum) risk skorlarını hesaplar.
    """
    mort_model = model["mortality"]
    del_model = model["delirium"]

    mort_prob = mort_model.predict_proba(X_mort)[0][1]
    del_prob = del_model.predict_proba(X_del)[0][1]

    return mort_prob, del_prob
