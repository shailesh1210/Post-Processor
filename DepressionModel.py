from DepressionIO import DepressionIO
import numpy as np
import matplotlib.pyplot as plt
import sys


class DepressionModel:
    COHORTS = ["E", "F", "G", "H", "I"]
    OUTCOMES = ["True Positive", "False Positive", "True Negative", "False Negative"]

    MAX_DEPRESSION_SYM = 27
    AGE_CAT1 = 7
    AGE_CAT2 = 3
    SEX = 2
    EDU_CAT = 2
    POSITIVE = 1
    NEGATIVE = 0

    def __init__(self, interface):
        self.__ui = interface
        self.__io = DepressionIO(interface)

        self.__cut_off_scores = [score for score in range(DepressionModel.MAX_DEPRESSION_SYM + 1)]
        self.__screening_outcomes = {}
        self.__sens_spec = {}

        self.__process_complete = False

    def import_nhanes(self, nhanes_file_path):
        self.__io.read_nhanes_data(nhanes_file_path)

    def import_depression_preval(self, preval_path):
        self.__io.read_depression_prevalence(preval_path)

    def process(self):
        if self.__ui.nhanes_check_box.IsChecked():
            self.__initialize()
            self.__screen_depression()

            self.__io.output_by_cohorts(self.__sens_spec, cohorts=DepressionModel.COHORTS)
            self.__io.output_by_age_gender(self.__sens_spec, num_age=DepressionModel.AGE_CAT2,
                                           num_sex=DepressionModel.SEX)
        elif self.__ui.prevalence_check_box.IsChecked():
            self.__io.output_depression_prevalence()

    def plot_roc(self):

        if self.__ui.cohortE_check_box.IsChecked():
            figE = plt.figure("Cohort E")
            self.__plot(cohort="E", figure=figE)

        if self.__ui.cohortF_check_box.IsChecked():
            figF = plt.figure("Cohort F")
            self.__plot(cohort="F", figure=figF)

        if self.__ui.cohortG_check_box.IsChecked():
            figG = plt.figure("Cohort G")
            self.__plot(cohort="G", figure=figG)

        if self.__ui.cohortH_check_box.IsChecked():
            figH = plt.figure("Cohort H")
            self.__plot(cohort="H", figure=figH)

        if self.__ui.cohortI_check_box.IsChecked():
            figI = plt.figure("Cohort I")
            self.__plot(cohort="I", figure=figI)

        plt.show()

    def import_success(self):
        return self.__io.show()

    def get_sens_spec(self, cohort):
        return self.__sens_spec[cohort]

    def is_complete(self):
        return self.__process_complete

    def __initialize(self):
        for cohort in DepressionModel.COHORTS:
            self.__sens_spec[cohort] = {}
            for score in self.__cut_off_scores:
                self.__sens_spec[cohort][score] = {"Sensitivity": 0, "Specificity": 0}

        for sex in range(DepressionModel.SEX):
            for age_cat in range(DepressionModel.AGE_CAT2):
                sex_age = (sex+1, age_cat+1)
                self.__sens_spec[sex_age] = {}
                for score in self.__cut_off_scores:
                    self.__sens_spec[sex_age][score] = {"Sensitivity": 0, "Specificity": 0}

        for outcome in DepressionModel.OUTCOMES:
            self.__screening_outcomes[outcome] = {"Weight": 0, "Freq": 0}

    def __screen_depression(self):
        nhanes_data = self.__io.get_nhanes_data()

        for score in self.__cut_off_scores:
            col_name = "cut_off_" + str(score)
            nhanes_data.loc[:, col_name] = np.where(nhanes_data["depscalescore"] >= score,
                                                    DepressionModel.POSITIVE, DepressionModel.NEGATIVE)

        self.__io.set_nhanes_data(nhanes_data)

        self.__compute_outcomes_by_cohorts(depression_type="other")
        self.__compute_outcomes_by_age_gender(depression_type="other")

    def __compute_outcomes_by_cohorts(self, depression_type):
        self.__process_complete = False

        cohorts = self.__get_cohorts()
        # cut_off_scores = [score for score in range(DepressionModel.MAX_DEPRESSION_SYM + 1)]

        self.__ui.display_text_box.AppendText("\n")

        for cohort, data_cohort in cohorts.items():
            for score in self.__cut_off_scores:
                self.__ui.display_text_box.AppendText("Processing: Cohort=" + str(cohort)
                                                      + " ,Cut-Off=" + str(score) + "\n")
                col_name = "cut_off_" + str(score)

                self.__screening_outcomes = self.__sum(data_cohort, gold_std=depression_type,
                                                       cut_off_criteria=col_name)

                self.__compute_sensitivity_specificity(cohort_name=cohort, cut_off_score=score)
                self.__reset_outcomes()

        self.__ui.display_text_box.AppendText("\nProcessing Complete!")
        self.__process_complete = True

    def __compute_outcomes_by_age_gender(self, depression_type):
        nhanes_age_gender = self.__get_stratified_nhanes()

        self.__ui.display_text_box.AppendText("\n\n")

        for age_gender, data in nhanes_age_gender.items():
            for score in self.__cut_off_scores:
                self.__ui.display_text_box.AppendText("Processing: Sex= " + str(age_gender[0])
                                                      + " ,Age_Cat= " + str(age_gender[1])
                                                      + " ,Cut-Off-Score=" + str(score) + "\n")
                col_name = "cut_off_" + str(score)
                self.__screening_outcomes = self.__sum(data, gold_std=depression_type,
                                                       cut_off_criteria=col_name)

                self.__compute_sensitivity_specificity(cohort_name=age_gender, cut_off_score=score)
                self.__reset_outcomes()

        self.__ui.display_text_box.AppendText("\nProcessing Complete!")

    def __sum(self, data, gold_std, cut_off_criteria):
        weight = "Weight"
        freq = "Freq"

        screening_outcomes = self.__screening_outcomes.copy()

        for idx, row in data.iterrows():
            outcome = self.__get_screening_outcome(row=row, gold_std=gold_std,
                                                   cut_off_criteria=cut_off_criteria)
            if outcome == "None":
                continue

            self.__screening_outcomes[outcome][weight] += row["wtmec2yr"]
            self.__screening_outcomes[outcome][freq] += 1

        return screening_outcomes

        # self.__compute_sensitivity_specificity(cohort=cohort, cut_off_score=cut_off_score)
        # self.__reset_outcomes()

    def __get_cohorts(self):
        cohorts = {}
        nhanes_data = self.__io.get_nhanes_data().groupby("cmark")
        for c in DepressionModel.COHORTS:
            cohorts[c] = nhanes_data.get_group(c)

        return cohorts

    def __get_stratified_nhanes(self):
        age_gender = {}
        nhanes_data = self.__io.get_nhanes_data().groupby(["gender", "agecat2"])

        for sex in range(DepressionModel.SEX):
            for age_cat in range(DepressionModel.AGE_CAT2):
                sex_age = (sex+1, age_cat+1)
                age_gender[sex_age] = nhanes_data.get_group(sex_age)

        return age_gender

    def __get_screening_outcome(self, row, gold_std, cut_off_criteria):
        if row[gold_std] == DepressionModel.POSITIVE and row[cut_off_criteria] == DepressionModel.POSITIVE:
            return "True Positive"
        elif row[gold_std] == DepressionModel.NEGATIVE and row[cut_off_criteria] == DepressionModel.POSITIVE:
            return "False Positive"
        elif row[gold_std] == DepressionModel.POSITIVE and row[cut_off_criteria] == DepressionModel.NEGATIVE:
            return "False Negative"
        elif row[gold_std] == DepressionModel.NEGATIVE and row[cut_off_criteria] == DepressionModel.NEGATIVE:
            return "True Negative"
        else:
            return "None"

    def __compute_sensitivity_specificity(self, cohort_name, cut_off_score):
        sens = "Sensitivity"
        spec = "Specificity"

        tp = self.__getTruePositive()
        fn = self.__getFalseNegative()

        if (tp + fn) != 0:
            self.__sens_spec[cohort_name][cut_off_score][sens] = tp / (tp + fn)
        else:
            self.__sens_spec[cohort_name][cut_off_score][sens] = 0

        tn = self.__getTrueNegative()
        fp = self.__getFalsePositive()

        if (tn + fp) != 0:
            self.__sens_spec[cohort_name][cut_off_score][spec] = tn / (tn + fp)
        else:
            self.__sens_spec[cohort_name][cut_off_score][spec] = 0

    def __plot(self, cohort, figure):
        sens = []
        spec = []

        for key, data in self.__sens_spec[cohort].items():
            sens.append(data["Sensitivity"])
            spec.append(1-data["Specificity"])

        plt.clf()
        plt.plot(spec, sens, color="orange", marker="o", label="ROC")
        plt.plot([0, 1], [0, 1], color="darkblue", linestyle="--")

        id = 0
        for i, j in zip(spec, sens):
            plt.annotate(id, xy=(i, j))
            id += 1

        plt.xlabel("1-Specificity")
        plt.ylabel("Sensitivity")

        plt.title("ROC curve for cohort " + cohort)
        plt.legend()

    def __getTruePositive(self):
        return self.__screening_outcomes["True Positive"]["Weight"] * self.__screening_outcomes["True Positive"]["Freq"]

    def __getFalsePositive(self):
        return self.__screening_outcomes["False Positive"]["Weight"] * self.__screening_outcomes["False Positive"]["Freq"]

    def __getTrueNegative(self):
        return self.__screening_outcomes["True Negative"]["Weight"] * self.__screening_outcomes["True Negative"]["Freq"]

    def __getFalseNegative(self):
        return self.__screening_outcomes["False Negative"]["Weight"] * self.__screening_outcomes["False Negative"]["Freq"]

    def __reset_outcomes(self):
        for outcome in DepressionModel.OUTCOMES:
            self.__screening_outcomes[outcome]["Weight"] = 0
            self.__screening_outcomes[outcome]["Freq"] = 0










