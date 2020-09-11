import wx
from IO import IO
import os


class DepressionIO(IO):
    # NHANES_COLUMNS = ["wtmec2yr", "cmark", "depdiagfunc", "depscalescore"]
    NHANES_COLUMNS = ["age", "agecat1", "agecat2", "gender", "edu",
                      "wtmec2yr", "cmark", "major", "other", "depscalescore"]
    PREVALENCE_COLUMNS = ["Preval_Before", "Preval_After"]
    STRATA = ["Sex", "Age_Cat", "Depression_Type"]

    def __init__(self, interface):
        super().__init__(interface)
        self.__cohorts = {}

    def get_nhanes_data(self):
        return self.__nhanes_data

    def set_nhanes_data(self, data):
        self.__nhanes_data = data

    def read_nhanes_data(self, file_paths):
        self.setDisplayFlag(True)
        self.__nhanes_data = self.read(file_paths, DepressionIO.NHANES_COLUMNS,
                                       ignore_index=True, index_col="Index")
        if self.show():
            wx.MessageBox("NHANES data successfully imported!")

    def read_depression_prevalence(self, file_path):
        self.setDisplayFlag(True)
        self.__prevalence = self.read(file_path, DepressionIO.PREVALENCE_COLUMNS,
                                      ignore_index=True, index_col="State")

        if self.show():
            wx.MessageBox("Depression Prevalence Successfully Imported!")
            self.__prevalence = self.__calculate(data=self.__prevalence)

    def output_by_cohorts(self, data, cohorts):
        for cohort in cohorts:
            filename = "sens_spec_" + cohort + ".csv"
            self.write_data(data[cohort], filename)

    def output_by_age_gender(self, data, num_age, num_sex):
        for sex in range(num_sex):
            for age in range(num_age):
                sex_age = (sex+1, age+1)
                filename = "sens_spec_" + str(sex+1) + str(age+1) + ".csv"
                self.write_data(data[sex_age], filename)

    def output_depression_prevalence(self):
        self.write(data=self.__prevalence, filename="Prevalence_US.csv")

    def write_data(self, data, filename):
        if not self.show():
            wx.MessageBox("Error: Cannot export file!")
        else:
            out_path = os.path.join(self.getCurDir(), filename)
            if os.path.isfile(out_path):
                open(out_path, "w").close()

            file = open(out_path, "a")
            file.write("Score,Sensitivity,Specificity\n")

            for key, item in data.items():
                cut_off_score = str(key)
                sens = str(item["Sensitivity"])
                spec = str(item["Specificity"])

                file.write(cut_off_score + "," +
                           sens + "," + spec + "\n")

            file.close()
            wx.MessageBox("Success: " + filename + " File exported!")

    def __calculate(self, data):
        data.Preval_Before *= data.Pop_Before
        data.Preval_After *= data.Pop_After

        data = data.groupby(DepressionIO.STRATA).sum()

        data.Preval_Before /= data.Pop_Before
        data.Preval_After /= data.Pop_After

        return data


