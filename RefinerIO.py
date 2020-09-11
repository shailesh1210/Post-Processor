import wx
from IO import IO
import pandas as pd
import os
from ipfn import ipfn
import numpy as np


class RefinerIO(IO):
    WHITE_NH = "White alone, not Hispanic or Latino"
    BLACK_NH = "Black or African American alone, not Hispanic or Latino"

    AGE_GROUPS = {"G1": ["POP_18_OVER", "POP_18_M", "POP_18_F"],
                  "G2": ["POP_18_34", "POP_18_34_M", "POP_18_34_F"],
                  "G3": ["POP_35_64", "POP_35_64_M", "POP_35_64_F"],
                  "G4": ["POP_65_OVER", "POP_65_M", "POP_65_F"]}

    SORTING_VARS = ["POP_GROUP", "ID2", "YEAR"]
    PUMS_COLUMNS = ["PWGTP", "AGEP", "SEX", "RAC1P", "HISP", "SCHL", "PINCP"]

    AGE_CAT = {"0-5": "POP_0_5", "5-9": "POP_5_9",
               "10-14": "POP_10_14", "15-19": "POP_15_19",
               "20-24": "POP_20_24", "25-34": "POP_25_34",
               "35-44": "POP_35_44", "45-54": "POP_45_54",
               "55-59": "POP_55_59", "60-64": "POP_60_64",
               "65-74": "POP_65_74", "75-84": "POP_75_84",
               "85+": "POP_85_OVER"}
    SEX_CAT = {"Male": "POP_M", "Female": "POP_F"}
    RACE_ETHNICITY = {"Hispanic": "POP_HISP", "OtherNH": "POP_ONH",
                      "WhiteNH": "POP_WNH", "BlackNH": "POP_BNH"}

    EDU = {"Less than 9th grade": "POP_LESS_9",
           "9th to 12th grade": "POP_9_12",
           "High School": "POP_HS",
           "Some college": "POP_SC",
           "Associates Degree": "POP_AD",
           "Bachelors Degree": "POP_BD",
           "Graduate Degree": "POP_GD"
           }

    STRATA1 = ["RACE_ETH", "SEX_", "AGE_CAT"]
    STRATA2 = STRATA1 + ["EDU"]
    STRATA3 = ["RACE_ETH", "SEX_", "EDU"]
    STRATA4 = STRATA1 + ["PINCP"]
    STRATA5 = ["RACE_ETH", "SEX_"]
    STRATA6 = ["RACE_ETH"]

    YEARS = ["2005", "2006", "2007", "2008",
             "2009", "2010", "2011", "2012",
             "2013", "2014", "2015", "2016"]

    def __init__(self, interface):

        super().__init__(interface)
        self.__ui = interface

        self.acs_data = pd.DataFrame()
        self.ipf_acs_data = pd.DataFrame()
        self.pums_income = pd.DataFrame()

        self.acs_data_whiteNH = pd.DataFrame()
        self.acs_data_blackNH = pd.DataFrame()

        self.marginals = {}
        self.pums_files_path = []

    def read_acs_data(self, file_paths, columns, columns_dict):
        # self.setDisplayFlag(True)
        self.acs_data = self.read_csv(file_paths=file_paths,
                                      columns=columns, ignore_index=True)

        if not self.acs_data.empty:
            self.__rename_columns(columns_dict)
            self.__create_final_dataset()

    def read_pums_data(self, file_paths):
        self.pums_files_path += file_paths

        # print(self.pums_files_path)
        self.enable_export()

    def read_marginals(self, file_paths):
        for path in file_paths:
            year = self.__get_marginal_year(path=path)
            self.__create_marginals(path=path, year=year)

    def __create_marginals(self, path, year):
        marginals_by_year = self.read_csv(file_paths=[path],
                                          columns=[], ignore_index=True)
        marginals_by_year = marginals_by_year.groupby("GEO2")

        marginals_by_state = {}
        for state_name, group in marginals_by_year:
            marginals_by_state[state_name] = group
            self.marginals[year] = marginals_by_state

    def ipf(self):
        if len(self.marginals) > 0:
            for path in self.pums_files_path:
                pums_data_year = self.__get_pums_year(path)
                if pums_data_year in self.marginals:
                    state_name = self.__get_state_name(path=path)

                    self.__read_pums_data(path=path, state=state_name, year=pums_data_year)
                    self.__start(year=pums_data_year, state=state_name)

                    # print(self.seed_matrix)
                else:
                    wx.MessageBox("Error: Marginal and PUMS Years don't match!")
            # print(self.ipf_acs_data)
        else:
            wx.MessageBox("Error: No Marginals Exist!")

    def __read_pums_data(self, path, state, year):
        self.__ui.display_text_box.AppendText("\nImporting PUMS for "
                                              + state + "...\n")

        self.pums_data = self.read_csv(file_paths=[path],
                                       columns=RefinerIO.PUMS_COLUMNS,
                                       ignore_index=True)

        self.pums_data["total"] = 0
        self.pums_data["AGE_CAT"] = self.pums_data.apply(self.__set_age_cat, axis=1)
        self.pums_data["RACE_ETH"] = self.pums_data.apply(self.__set_race_ethnicity, axis=1)
        self.pums_data["SEX_"] = self.pums_data.apply(self.__set_sex, axis=1)

        if int(year) >= 8:
            self.pums_data["EDU"] = self.pums_data.apply(self.__set_education1, axis=1)
        else:
            self.pums_data["EDU"] = self.pums_data.apply(self.__set_education2, axis=1)


    def __start(self, state, year):
        self.__ui.display_text_box.AppendText("Starting IPF for year :"
                                              + year + "...\n")

        stratas = [RefinerIO.STRATA1, RefinerIO.STRATA2, RefinerIO.STRATA4]

        for strata in stratas:
            if strata != RefinerIO.STRATA4:
                self.__create_seed_matrix(strata=strata)
                self.__compute(strata=strata, year=year, state=state)
            else:
                self.__refine_pums_income(year=year, state=state)


    def __create_seed_matrix(self, strata):
        self.seed_matrix = pd.DataFrame()
        self.seed_matrix = self.pums_data.groupby(strata).count().reset_index()

        for col in self.seed_matrix.columns:
            if col == "AGEP" or col == "SEX" or col == "RAC1P" or col == "HISP" or col == "SCHL"\
                    or col == "PINCP" or col == "PWGTP":
                del self.seed_matrix[col]

        if strata == RefinerIO.STRATA1:
            del self.seed_matrix["EDU"]

        if strata == RefinerIO.STRATA2:
            self.seed_matrix = self.__remove_rows(df=self.seed_matrix)
            # self.seed_matrix = self.seed_matrix.reset_index()

    def __compute(self, strata, year, state):
        mar = self.marginals[year][state]
        if strata == RefinerIO.STRATA1:
            self.__ui.display_text_box.AppendText("\nIPF by race, gender and age..\n")

            self.m_sex = self.__sex_marginals(mar)
            self.m_age_cat = self.__age_marginals(mar)
            self.m_race = self.__race_marginals(mar)

            aggregates = [self.m_race, self.m_sex, self.m_age_cat]
            dimension = [["RACE_ETH"], ["SEX_"], ["AGE_CAT"]]

            ipf = ipfn.ipfn(self.seed_matrix, aggregates, dimension)
            df = ipf.iteration(self.__ui)

            df = self.__remove_rows(df)

            self.m_age_cat = df.groupby("AGE_CAT")["total"].sum()
            self.m_sex = df.groupby("SEX_")["total"].sum()
            self.m_race = df.groupby("RACE_ETH")["total"].sum()

        elif strata == RefinerIO.STRATA2:
            self.__ui.display_text_box.AppendText("\nIPF by race, gender, age and education..\n")
            self.m_edu = self.__edu_marginals(mar)

            print()
            print(self.m_race)
            print()

            print(self.m_sex)
            print()

            print(self.m_age_cat)
            print()

            print(self.m_edu)
            print()

            aggregates = [self.m_race, self.m_sex, self.m_age_cat, self.m_edu]
            dimension = [["RACE_ETH"], ["SEX_"], ["AGE_CAT"], ["EDU"]]

            ipf = ipfn.ipfn(self.seed_matrix, aggregates, dimension)
            df = ipf.iteration(self.__ui)

            df_education = self.__merge_education(df=df)

            # df_some_college = self.__remove_education(df=df)

            df_education = self.__add_column(df=df_education, col_name="FIPS", value=int(mar["ID2"]), index=0)
            df_education = self.__add_column(df=df_education, col_name="YEAR", value="20" + year, index=1)

            df_education = self.__fill_dataframe(df=df_education, year=year, fips=int(mar["ID2"]))

            print()
            print(df_education)

            if self.ipf_acs_data.empty:
                self.ipf_acs_data = df_education
            else:
                self.ipf_acs_data = self.ipf_acs_data.append(df_education, ignore_index=True)

    def __refine_pums_income(self, year, state):
        fips = int(self.marginals[year][state]["ID2"])

        for col in self.pums_data.columns:
            if col == "AGEP" or col == "SEX" or col == "RAC1P" or col == "HISP" \
                    or col == "SCHL" or col == "total" or col == "EDU":
                del self.pums_data[col]

        self.pums_data = self.pums_data[self.pums_data["AGE_CAT"] != "25-34"]
        self.pums_data = self.__remove_rows(df=self.pums_data)
        self.pums_data["PINCP"] = pd.to_numeric(self.pums_data["PINCP"], downcast="float")

        # df_income = self.pums_data.groupby(RefinerIO.STRATA5)
        df_income = self.pums_data.groupby(RefinerIO.STRATA6)

        median_income_list = []
        mean_income_list = []
        race_list = []
        # gender_list = []

        for key, df in df_income:
            # race_list.append(key[0])
            # gender_list.append(key[1])

            race_list.append(key)

            df.sort_values("PINCP", inplace=True)
            cum_sum_weights = df.PWGTP.cumsum()
            cut_off_weight = df.PWGTP.sum() / 2.0

            # print(df)

            weighted_median_income = df.PINCP[cum_sum_weights >= cut_off_weight].iloc[0]
            weighted_income = (df["PWGTP"] * df["PINCP"]).sum() / df["PWGTP"].sum()

            median_income_list.append(weighted_median_income)
            mean_income_list.append(weighted_income)

        # df_income = pd.DataFrame(columns=["FIPS", "YEAR", "RACE_ETH", "SEX_", "Median", "Mean"])
        df_income = pd.DataFrame(columns=["FIPS", "YEAR", "RACE_ETH", "Median", "Mean"])

        df_income["RACE_ETH"] = race_list
        # df_income["SEX_"] = gender_list

        df_income["Median"] = median_income_list
        df_income["Mean"] = mean_income_list

        df_income["FIPS"] = int(fips)
        df_income["YEAR"] = "20" + year

        if self.pums_income.empty:
            self.pums_income = df_income
        else:
            self.pums_income = self.pums_income.append(df_income, ignore_index=True)

    def output_acs_data(self):
        if self.__ui.pop_count_cb.IsChecked():
            self.write_data_("acs_pop_count.csv")
        elif self.__ui.ipf_cb.IsChecked():

            self.__create_final_ipf_dataset(strata=RefinerIO.STRATA3)

            file_num = 1
            for strata, df in self.ipf_acs_data.items():
                self.write(data=df, filename="ipf_acs_" + str(file_num) + ".csv")
                file_num += 1

    def output_income(self):
        # df = self.pums_income.groupby(RefinerIO.STRATA5)
        df = self.pums_income.groupby(RefinerIO.STRATA6)
        file = 1
        for strata, data in df:
            self.write(data=data, filename="income_" + str(file) + ".csv")
            file += 1

    def write_data_(self, filename):
        if self.final_acs_data.empty:
            wx.MessageBox("Error:Cannot export file!")
        else:
            out_path = os.path.join(self.getCurDir(), filename)
            if os.path.isfile(out_path):
                open(out_path, "w").close()

            file = open(out_path, "a")

            out_columns = ""
            for cols in self.final_acs_data.columns:
                out_columns += (str(cols) + ",")

            file.write(out_columns + "\n")

            for row, columns in self.final_acs_data.iterrows():
                out_values = ""
                for col in self.final_acs_data.columns:
                    out_values += (str(columns[col]) + ",")
                file.write(out_values + "\n")

            file.close()
            wx.MessageBox("Success: " + filename + " File exported!")

    def __rename_columns(self, columns_dict):
        new_columns = {}
        for col_name, value in columns_dict.items():
            if col_name in self.acs_data.columns:
                new_columns[col_name] = value

        self.acs_data = self.acs_data.rename(columns=new_columns)

        # print(self.acs_data.columns)

    def __create_final_dataset(self):
        self.final_acs_data = pd.DataFrame()

        if self.__column_exists(RefinerIO.SORTING_VARS):
            self.acs_data = self.__calculate_pop_count(self.acs_data)
            if not self.acs_data.empty:
                refined_acs_data = dict(tuple(self.acs_data.groupby("POP_GROUP")))

                if RefinerIO.WHITE_NH in refined_acs_data.keys():
                    self.acs_data_whiteNH = refined_acs_data[RefinerIO.WHITE_NH]
                    self.acs_data_whiteNH["POP_GROUP"] = \
                        self.acs_data_whiteNH["POP_GROUP"].replace(RefinerIO.WHITE_NH, "WhiteNH")

                if RefinerIO.BLACK_NH in refined_acs_data.keys():
                    self.acs_data_blackNH = refined_acs_data[RefinerIO.BLACK_NH]
                    self.acs_data_blackNH["POP_GROUP"] = \
                        self.acs_data_blackNH["POP_GROUP"].replace(RefinerIO.BLACK_NH, "BlackNH")

                self.final_acs_data = pd.merge(self.acs_data_whiteNH,
                                               self.acs_data_blackNH,
                                               on=["YEAR", "ID2"], how='outer',
                                               suffixes=("_W", "_B"))

                for col in self.final_acs_data.columns:
                    self.final_acs_data[col] = self.final_acs_data[col].fillna(0)

        else:
            wx.MessageBox("Error: POP GROUP, YEAR or ID2 is missing!")

    def __create_final_ipf_dataset(self, strata):
        self.ipf_acs_data = dict(tuple(self.ipf_acs_data.groupby(strata)))

        ref_df = pd.DataFrame()
        for key, df in self.ipf_acs_data.items():
            ref_df = df
            break

        # ref_df = self.ipf_acs_data[("WhiteNH", "Male", "35-44")]
        columns = ref_df.columns
        template = pd.DataFrame(columns=columns)

        for col in columns:
            if col == "FIPS" or col == "YEAR":
                template[col] = ref_df[col]
            else:
                del template[col]

        template = template.reset_index(drop=True)

        merge_cols = ["FIPS", "YEAR"]
        strata_list = self.__get_strata_list(strata=strata)

        for strata, df in self.ipf_acs_data.items():
            if strata in strata_list:
                df = df.reset_index(drop=True)
                df = pd.merge(template, df, on=merge_cols, how="left")

                for col in columns:
                    df[col] = df[col].fillna(0)

                self.ipf_acs_data[strata] = df

                strata_list.remove(strata)

        if len(strata_list) > 0:
            df_new = pd.DataFrame(columns=columns)
            for strata in strata_list:
                df_new = pd.merge(template, df_new, on=merge_cols, how="left")
                for col in columns:
                    if col == "FIPS" or col == "YEAR":
                        continue
                    df_new[col] = 0

                self.ipf_acs_data[strata] = df_new

    def __calculate_pop_count(self, data):
        flags = []
        for group, col_names in RefinerIO.AGE_GROUPS.items():
            if self.__column_exists(col_names):
                flags.append(True)
                if group == "G1":
                    data.POP_18_M = round(data.POP_18_OVER * (data.POP_18_M / 100))
                    data.POP_18_F = round(data.POP_18_OVER * (data.POP_18_F / 100))
                elif group == "G2":
                    data.POP_18_34_M = round(data.POP_18_34 * (data.POP_18_34_M / 100))
                    data.POP_18_34_F = round(data.POP_18_34 * (data.POP_18_34_F / 100))
                elif group == "G3":
                    data.POP_35_64_M = round(data.POP_35_64 * (data.POP_35_64_M / 100))
                    data.POP_35_64_F = round(data.POP_35_64 * (data.POP_35_64_F / 100))
                elif group == "G4":
                    data.POP_65_M = round(data.POP_65_OVER * (data.POP_65_M / 100))
                    data.POP_65_F = round(data.POP_65_OVER * (data.POP_65_F / 100))

        if len(flags) > 0:
            wx.MessageBox("ACS data successfully imported!")
            data = data.sort_values(RefinerIO.SORTING_VARS)
            return data

        else:
            wx.MessageBox("Error: One or more column/s missing!")
            return pd.DataFrame()

    def __column_exists(self, columns):
        # columns = ["POP_18_OVER", "POP_18_M", "POP_18_F"]
        count = 0
        for col in columns:
            if col in self.acs_data.columns:
                count += 1

        if count < len(columns):
            return False
        else:
            return True

    def __remove_rows(self, df):
        age_cat_below25 = ["0-5", "5-9", "10-14", "15-19", "20-24"]
        df = df[(df["RACE_ETH"] == "WhiteNH") | (df["RACE_ETH"] == "BlackNH")]
        for age_cat in age_cat_below25:
            df = df[df["AGE_CAT"] != age_cat]

        return df

    def __merge_education(self, df):
        replace_rules = {}
        edu_cat = "HS or Less"
        for edu, var in RefinerIO.EDU.items():
            replace_rules[edu] = edu_cat
            if edu == "High School":
                replace_rules[edu] = edu_cat
                edu_cat = "Some college or more"

        df = df[df["AGE_CAT"] != "25-34"]

        df = df.groupby(RefinerIO.STRATA3).sum().reset_index()
        return self.__merge_rows(df=df, replace_rules=replace_rules,
                                 strata=RefinerIO.STRATA3, col="EDU")

    def __remove_education(self, df):
        return df[df["EDU"] == "Some college or more"]

    def __merge_rows(self, df, replace_rules, strata, col):
        df[col].replace(replace_rules, inplace=True)
        df = df.groupby(strata).sum().reset_index()
        return df

    def __add_column(self, df, col_name, value, index):
        df.insert(index, col_name, value)
        return df

    def __fill_dataframe(self, df, year, fips):
        cols = df.columns
        year = "20" + year

        new_df = pd.DataFrame(columns=cols)

        for col in cols:
            if col == "RACE_ETH":
                new_df["RACE_ETH"] = ["BlackNH",
                                      "BlackNH",
                                      "BlackNH",
                                      "BlackNH",
                                      "WhiteNH",
                                      "WhiteNH",
                                      "WhiteNH",
                                      "WhiteNH"]
            elif col == "SEX_":
                new_df["SEX_"] = ["Male",
                                  "Male",
                                  "Female",
                                  "Female",
                                  "Male",
                                  "Male",
                                  "Female",
                                  "Female"]
            elif col == "EDU":
                new_df["EDU"] = ["HS or Less",
                                 "Some college or more",
                                 "HS or Less",
                                 "Some college or more",
                                 "HS or Less",
                                 "Some college or more",
                                 "HS or Less",
                                 "Some college or more"]
            elif col == "total":
                del new_df["total"]

        new_df["FIPS"] = fips
        new_df["YEAR"] = year

        # print(new_df.columns)

        df = pd.merge(new_df, df, on=list(new_df.columns), how="left")
        df["total"] = df["total"].fillna(0)

        return df

    def __race_marginals(self, mar):
        return self.__get_marginal_by_attribute(marginal=mar,
                                                col_name="RACE_ETH",
                                                col_dict=RefinerIO.RACE_ETHNICITY)

    def __sex_marginals(self, mar):
        return self.__get_marginal_by_attribute(marginal=mar,
                                                col_name="SEX_",
                                                col_dict=RefinerIO.SEX_CAT)

    def __age_marginals(self, mar):
        return self.__get_marginal_by_attribute(marginal=mar,
                                                col_name="AGE_CAT",
                                                col_dict=RefinerIO.AGE_CAT)

    def __edu_marginals(self, mar):
        m_edu = self.__get_marginal_by_attribute(marginal=mar,
                                                 col_name="EDU",
                                                 col_dict=RefinerIO.EDU)
        total_pop = self.__get_pop_25_over()
        total_percent = m_edu.sum()

        for edu, est in m_edu.items():
            m_edu[edu] = float(total_pop * est/total_percent)

        return m_edu

    def __get_marginal_by_attribute(self, marginal, col_name, col_dict):
        mar_by_attr = self.pums_data.groupby(col_name)["total"].sum()
        for attr, row in mar_by_attr.items():
            mar_by_attr.loc[attr] = float(marginal[col_dict[attr]])

        return mar_by_attr

    def __get_marginal_year(self, path):
        filename = self.__get_file_name(path=path, delimiter="\\")
        file_list = filename[0].split("_")
        year = file_list[1]

        return year

    def __get_pums_year(self, path):
        filename = self.__get_file_name(path=path, delimiter="\\")
        filename = list(filename[0])

        year = filename[2] + filename[3]

        return year

    def __get_state_name(self, path):

        filename = self.__get_file_name(path=path, delimiter="\\")
        filename = list(filename[0])

        state_name = filename[len(filename)-2] + filename[len(filename)-1]

        return state_name.upper()

    def __get_file_name(self, path, delimiter):
        path = path.split(delimiter)
        return path[len(path) - 1].split(".")

    def __get_strata_list(self, strata):
        if strata == RefinerIO.STRATA1:
            return self.__get_strata_by_race_gender_age()
        elif strata == RefinerIO.STRATA3:
            return self.__get_strata_by_race_gender_education()
        else:
            return -1

    def __get_strata_by_race_gender_age(self):
        race = ["WhiteNH", "BlackNH"]
        gender = ["Male", "Female"]
        age_cat = ["35-44", "45-54", "55-64", "65-74", "75-84", "85+"]

        strata_list = []
        for r in race:
            for g in gender:
                for a in age_cat:
                    strata_list.append((r, g, a))

        return strata_list

    def __get_strata_by_race_gender_education(self):
        race = ["WhiteNH", "BlackNH"]
        gender = ["Male", "Female"]
        education = ["Some college or more"]

        strata_list = []
        for r in race:
            for g in gender:
                for e in education:
                    strata_list.append((r, g, e))

        return strata_list

    def __get_pop_25_over(self):
        pop = 0
        for age_cat, est in self.m_age_cat.items():
            pop += est

        return pop

    def __set_age_cat(self, row):
        if 0 <= row["AGEP"] <= 4:
            return "0-5"
        elif 5 <= row["AGEP"] <= 9:
            return "5-9"
        elif 10 <= row["AGEP"] <= 14:
            return "10-14"
        elif 15 <= row["AGEP"] <= 19:
            return "15-19"
        elif 20 <= row["AGEP"] <= 24:
            return "20-24"
        elif 25 <= row["AGEP"] <= 34:
            return "25-34"
        elif 35 <= row["AGEP"] <= 44:
            return "35-44"
        elif 45 <= row["AGEP"] <= 54:
            return "45-54"
        elif 55 <= row["AGEP"] <= 59:
            return "55-59"
        elif 60 <= row["AGEP"] <= 64:
            return "60-64"
        elif 65 <= row["AGEP"] <= 74:
            return "65-74"
        elif 75 <= row["AGEP"] <= 84:
            return "75-84"
        else:
            return "85+"

    def __set_race_ethnicity(self, row):
        if row["HISP"] == 1:
            if row["RAC1P"] == 1:
                return "WhiteNH"
            elif row["RAC1P"] == 2:
                return "BlackNH"
            else:
                return "OtherNH"
        else:
            return "Hispanic"

    def __set_sex(self, row):
        if row["SEX"] == 1:
            return "Male"
        elif row["SEX"] == 2:
            return "Female"

    def __set_education1(self, row):
        if row["SCHL"] <= 11:
            return "Less than 9th grade"
        elif row["SCHL"] <= 15:
            return "9th to 12th grade"
        elif row["SCHL"] <= 17:
            return "High School"
        elif row["SCHL"] <= 19:
            return "Some college"
        elif row["SCHL"] <= 20:
            return "Associates Degree"
        elif row["SCHL"] <= 21:
            return "Bachelors Degree"
        elif row["SCHL"] <= 24:
            return "Graduate Degree"

    def __set_education2(self, row):
        if row["SCHL"] <= 4:
            return "Less than 9th grade"
        elif row["SCHL"] <= 8:
            return "9th to 12th grade"
        elif row["SCHL"] <= 9:
            return "High School"
        elif row["SCHL"] <= 11:
            return "Some college"
        elif row["SCHL"] <= 12:
            return "Associates Degree"
        elif row["SCHL"] <= 13:
            return "Bachelors Degree"
        elif row["SCHL"] <= 16:
            return "Graduate Degree"





