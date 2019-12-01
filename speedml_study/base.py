import numpy as np
import pandas as pd
class Base(object):
    def __init__(self, train=None, test=None, target=None, uid=None):
        from . import Speedml
        if test is None and target is None and isinstance(train,Speedml):
            train = train.train
            test  = train.test
            target = train.target
            uid = train.uid if hasattr(train,"uid") else None
        Base=self
        Base.target = target
        if isinstance(train,str):
            # TODO: Add more file formats supported by pandas.read_
            if train.endswith('.csv'):
                Base.train = pd.read_csv(train)
                Base.test = pd.read_csv(test)

            if train.endswith('.json'):
                Base.train = pd.read_json(train)
                Base.test = pd.read_json(test)
        elif isinstance(train,pd.DataFrame):
            Base.target = target
            Base.train=train
            Base.test=test        
    
        if not Base.train is None  and not Base.test is None:
            if uid:
                Base.uid = Base.test.pop(uid)
                Base.train = Base.train.drop([uid], axis=1)

            self.np = np
            self.pd = pd
        else:
            print('ERROR: SpeedML can only process .csv and .json file extensions.')
    #@staticmethod
    def data_n(self):
        """
        Updates train_n and test_n numeric datasets (used for model data creation) based on numeric datatypes from train and test datasets.
        """
        Base=self
        Base.train_n = Base.train.select_dtypes(include=[np.number])
        Base.test_n = Base.test.select_dtypes(include=[np.number])
