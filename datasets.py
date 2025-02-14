import os
import lale
from sklearn.model_selection import train_test_split
import pandas as pd
import pickle

from lale.lib.aif360 import fetch_creditg_df

def download_task(dataset_name, preprocess=True):
    
    cached_data_path = f"data/{dataset_name}_{preprocess}.pkl"
    print(cached_data_path)
    if not os.path.exists(cached_data_path):
        load_df = getattr(lale.lib.aif360.datasets, 'fetch_'+dataset_name+'_df')
        X, y, fairness_info =  load_df()
        print(fairness_info)
        l = fairness_info['protected_attributes']
        sens_names = [d['feature'] for d in l]

        print("Downloaded")
        X.reset_index(drop=True)
        y.reset_index(drop=True)
        
        print(X.shape)
        print(y.shape)
        print(X.head(10))

        if preprocess:
            # Minimal preprocessing

            if dataset_name=='compas_violent':
                # Identify the date columns
                date_columns = ['compas_screening_date', 'dob', 'in_custody', 'out_custody', 'v_screening_date', 'c_jail_in', 'c_jail_out', 'c_offense_date', 'c_arrest_date', 'vr_offense_date', 'screening_date',]
                for col in date_columns:
                    # Drop the date columns
                    X = X.drop(col, axis=1)

            if dataset_name=='default_credit':
                X['sex'] = w=X['sex'].map({1:'one', 2:'two'})
                
            for col in X:
                if len(X[col].unique())==1:
                    X = X.drop(col, axis=1)
        
            # If any sensitive feature column contains continuous values (e.g. age), bin it.
            if 'age' in sens_names:
                bin_edges = [0, 18, 35, 50, float('inf')]  # Define your desired age bins
                bin_labels = ['0-18', '19-35', '36-50', '51+']  # Labels for the bins
            
                # Create a new column 'age_group' based on the bins
                X['age'] = pd.cut(X['age'], bins=bin_edges, labels=bin_labels, right=False)
               
            fav_label = fairness_info["favorable_labels"][0]
            print("Before")
            print(y.head(20))
            y = pd.Series([1 if y==fav_label else 0 for y in y])
            print("After")
            print(y.head(20))
           
            features = X.columns

            print("All features", features)
            print("Sensitive features", sens_names)

            assert y.index.equals(X.index), "Indices of y and sensitive_columns do not match."
            d = {"X": X, "y": y, "features":features, "sens_features":sens_names}
            if not os.path.exists("data"):
                os.makedirs("data")
            with open(cached_data_path, "wb") as f:
                pickle.dump(d, f)


def download_pmad_task(dataset_name, outcome_name, preprocess=True):
    cached_data_path = f"data/{dataset_name}_{preprocess}.pkl"
    print(cached_data_path)
    if not os.path.exists(cached_data_path):
        all_data = pd.read_excel("De-identified PMAD data.xlsx")

        # Extract relevant variables for model fitting
        outcome = outcome_name
        data = all_data[['MOM_AGE','MOM_RACE','ETHNIC_GROUP','MARITAL_STATUS','FINANCIAL_CLASS',
                        'LBW','PTB',
                        'DELIVERY_METHOD','NICU_ADMIT','MFCU_ADMIT',
                        'PREE','GDM','GHTN',
                        'MOM_BMI','MOM_LOS','CHILD_LOS',
                        'HIST_ANXIETY','HIST_DEPRESS','HIST_BIPOLAR','HIST_PMAD','MENTAL_HEALTH_DX_CUTOFF',
                        'MED_PSYCH','MED_CARDIO',
                        outcome]]

        data = data.dropna() # keep only complete data

        # get dummy variables
        data = pd.get_dummies(data)

        # split into X and y
        X = data.drop([outcome], axis=1)
        Y = data[[outcome]]

        #race = data[['MOM_RACE_Asian or Native Hawaiian or Other Pacific Islander',
        #           'MOM_RACE_Black or African American',
        #            'MOM_RACE_Multiracial',
        #            'MOM_RACE_Other',
        #            'MOM_RACE_Unknown',
        #            'MOM_RACE_White',
        #            'MOM_RACE_Hispanic White']]
        #strat_df = pd.concat([Y,race],axis=1)

        # Split the data into training and test sets
        X_train, X_test, y_train, y_test = train_test_split(X, Y, train_size=0.90, test_size=0.10, shuffle=True, random_state=2024)
        features = X_train.columns

        sens_features = ['MOM_RACE_Asian or Native Hawaiian or Other Pacific Islander',
                'MOM_RACE_Black or African American',
                    'MOM_RACE_Multiracial',
                    'MOM_RACE_Other',
                    'MOM_RACE_Unknown',
                    'MOM_RACE_White',
                    'MOM_RACE_Hispanic White']
        print("All features", features)
        print("Sensitive features", sens_features)


        y_train = y_train.iloc[:,-1].astype('int')
        y_test = y_test.iloc[:,-1].astype('int')

        d = {"X_train": X_train, "y_train": y_train, "X_test": X_test, "y_test": y_test, "features":features, "sens_features":sens_features}
        if not os.path.exists("data"):
            os.makedirs("data")
        with open(cached_data_path, "wb") as f:
            pickle.dump(d, f)



if __name__ == '__main__':
    #not_able_to_download = ['meps19', 'meps21', 'meps20',]
    datasets_binary = ['ricci', 'heart_disease', 'student_math', 'student_por', 'creditg', 'titanic', 'us_crime', 'compas_violent', 'nlsy', 'compas',
            'speeddating',  'law_school', 'default_credit', 'bank', 'adult']
    for ds in datasets_binary:
        download_task(ds)
    download_pmad_task('pmad_phq','PHQ9_risk2')
    download_pmad_task('pmad_epds','EPDS_risk2')


