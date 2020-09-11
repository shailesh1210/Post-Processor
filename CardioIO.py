# This module handles I/O operations
# 1. Reads and refines user selected input file
# 2. Display and output averages of selected variables

import wx

# from CardioIO import CardioIO
from IO import IO
import pandas as pd


class CardioIO(IO):
    RISK_FACTORS_VARS = ["Age", "SD_Age",
                         "Tchols", "SD_Tchols",
                         "LDL", "SD_LDL",
                         "HDL", "SD_HDL",
                         "SBP", "SD_SBP",
                         "Smoking", "Low_Smoke", "Up_Smoke",
                         "HTN", "Low_HTN", "Up_HTN"]

    # STATINS_VARS = ["Statins_Usage"]
    STATINS_VARS = ["Pop", "TotalStatinsEligiblePre",
                    "OnStatinsPre", "NotOnStatinsPre",
                    "BaselineStatinsUse", "StatinsUsePost",
                    "RemainingUsePost"]

    CHD_VARS = ["Ten_year_CHD"]

    STRATA = ['Intervention', 'Time', 'Race_Gender']
    STRATA_STATINS = ['Intervention', 'RaceGender']

    def __init__(self, interface):

        super().__init__(interface)

        self.risk_factor_data = pd.DataFrame()
        self.total_chd_risk = pd.DataFrame()
        self.fatal_chd_risk = pd.DataFrame()

        self.__risk_filename = "mean_risk.csv"
        self.__total_chd_filename = "total_chd.csv"
        self.__fatal_chd_filename = "fatal_chd.csv"
        self.__statins_filename = "statins_use.csv"

    def read_risk_factors_data(self, file_paths):
        self.setDisplayFlag(True)
        self.risk_factor_data = self.read(file_paths=file_paths,
                                          ref_header=CardioIO.RISK_FACTORS_VARS,
                                          ignore_index=True, index_col="State")

        if self.show():
            wx.MessageBox("Risk factor files successfully imported!")
            self.risk_factor_data = self.__calculate(data=self.risk_factor_data, columns=CardioIO.RISK_FACTORS_VARS)

    def read_total_chd_risk(self, file_paths):
        self.setDisplayFlag(True)
        self.total_chd_risk = self.read(file_paths=file_paths,
                                        ref_header=CardioIO.CHD_VARS,
                                        ignore_index=True, index_col="State")

        if self.show():
            wx.MessageBox("Total CHD risk files are successfully imported!")
            self.total_chd_risk = self.__calculate(data=self.total_chd_risk, columns=CardioIO.CHD_VARS)

    def read_fatal_chd_risk(self, file_paths):
        self.setDisplayFlag(True)
        self.fatal_chd_risk = self.read(file_paths=file_paths,
                                        ref_header=CardioIO.CHD_VARS,
                                        ignore_index=True, index_col="State")

        if self.show():
            wx.MessageBox("Fatal CHD risk files are successfully imported!")
            self.fatal_chd_risk = self.__calculate(data=self.fatal_chd_risk, columns=CardioIO.CHD_VARS)

    def read_statins_use(self, file_paths):
        self.setDisplayFlag(True)
        self.statins_use = self.read(file_paths=file_paths,
                                     ref_header=CardioIO.STATINS_VARS,
                                     ignore_index=True, index_col="State")

        # print(self.statins_use)

        if self.show():
            wx.MessageBox("Statins Usage files are successfully imported!")
            self.statins_use = self.__calculate_statins_use(data=self.statins_use, columns=CardioIO.STATINS_VARS)


    def output(self):

        if not self.risk_factor_data.empty:
            self.write(self.risk_factor_data,  self.__risk_filename)

        if not self.total_chd_risk.empty:
            self.write(self.total_chd_risk, self.__total_chd_filename)

        if not self.fatal_chd_risk.empty:
            self.write(self.fatal_chd_risk, self.__fatal_chd_filename)

        if not self.statins_use.empty:
            self.write(self.statins_use, self.__statins_filename)

    def __calculate(self, data, columns):
        for col in columns:
            data[col] *= data.Pop

        data = data.groupby(CardioIO.STRATA).sum()

        for col in columns:
            data[col] /= data.Pop

        return data

    def __calculate_statins_use(self, data, columns):
        data = data.groupby(CardioIO.STRATA_STATINS).sum()

        # for col in columns:
            # data["Percent"] = 100 * (data[col] / data.Pop)

        return data







