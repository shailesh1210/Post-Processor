import wx
import os
import threading as td
import time

from collections import OrderedDict
from CardioModel import CardioModel
from DepressionModel import DepressionModel
from ACSRefiner import ACSRefiner


class Interface(wx.Frame):
    HEIGHT = 720
    WIDTH = 1600

    def __init__(self):
        super().__init__(parent=None,
                         title="Post Processor",
                         size=(Interface.WIDTH, Interface.HEIGHT),
                         style=wx.MINIMIZE_BOX | wx.SYSTEM_MENU | wx.CAPTION | wx.CLOSE_BOX)

    def initialize(self):
        self.window = wx.Panel(self)

        self.parent_box = wx.BoxSizer(wx.HORIZONTAL)
        self.left_box = wx.BoxSizer(wx.VERTICAL)
        self.right_box = wx.BoxSizer(wx.VERTICAL)

        self.__create_input_widgets()
        self.__create_output_widgets()

        self.parent_box.Add(self.left_box, proportion=1, flag=wx.EXPAND | wx.ALL, border=5)
        self.parent_box.Add(self.right_box, proportion=1, flag=wx.EXPAND | wx.ALL, border=5)

        self.window.SetSizer(self.parent_box)

        self.Center()
        self.Show()

    def __create_input_widgets(self):
        self.__create_choice_box()
        self.__create_buttons()

    def __create_output_widgets(self):
        display_vbox = wx.BoxSizer(wx.VERTICAL)

        display_label = wx.StaticText(self.window, label="Output Console")
        self.display_text_box = wx.TextCtrl(self.window, style=wx.TE_MULTILINE | wx.TE_READONLY)

        display_vbox.Add(display_label, flag=wx.ALL | wx.ALIGN_CENTER, border=5)
        display_vbox.Add(self.display_text_box, proportion=1, flag=wx.ALIGN_CENTER | wx.EXPAND)

        self.right_box.Add(display_vbox, proportion=1, flag=wx.EXPAND)

    def __create_choice_box(self):
        choice_vbox = wx.BoxSizer(wx.VERTICAL)

        model_label = wx.StaticText(self.window, label="Available models")

        self.models = ["Cardio Model", "Depression Model", "ACS Refiner"]
        self.choice_models = wx.Choice(self.window, choices=self.models,
                                       name=self.models[0],
                                       size=(200, 30))
        self.choice_models.Bind(wx.EVT_CHOICE, self.__model_selection)

        choice_vbox.Add(model_label, flag=wx.ALL | wx.ALIGN_CENTER, border=10)
        choice_vbox.Add(self.choice_models, flag=wx.LEFT | wx.RIGHT | wx.EXPAND, border=10)

        self.left_box.Add(choice_vbox, flag=wx.EXPAND | wx.LEFT | wx.RIGHT, border=10)

        self.__create_cardio_menu()
        self.__create_depression_menu()
        self.__create_acs_refiner_menu()

    def __create_buttons(self):
        button_vbox = wx.BoxSizer(wx.VERTICAL)

        # self.import_button = wx.Button(self.window, label="Import files", size=(200, 40))
        # self.import_button.Bind(wx.EVT_BUTTON, self.__import_files)

        self.export_button = wx.Button(self.window, label="Process", size=(200, 40))
        # self.export_button.Bind(wx.EVT_BUTTON, self.__export_files)
        # self.export_button.Bind(wx.EVT_BUTTON, self.__thread_start, self.__export_files)
        self.Bind(wx.EVT_BUTTON, self.__thread_start, self.export_button)
        self.export_button.Disable()

        self.clear_btn = wx.Button(self.window, label="Clear", size=(200, 40))
        self.clear_btn.Bind(wx.EVT_BUTTON, self.__clear)

        # button_vbox.Add(self.import_button, flag=wx.RIGHT | wx.LEFT | wx.BOTTOM | wx.EXPAND, border=10)
        button_vbox.Add(self.export_button, flag=wx.RIGHT | wx.LEFT | wx.BOTTOM | wx.EXPAND, border=10)
        button_vbox.Add(self.clear_btn, flag=wx.RIGHT | wx.LEFT | wx.EXPAND, border=10)

        self.left_box.Add(button_vbox, flag=wx.EXPAND | wx.ALL, border=10)

    def __create_cardio_menu(self):

        sizer = wx.GridSizer(4, 2, 10, 10)

        self.mean_check_box = wx.CheckBox(self.window, label="Mean of risk factors")
        self.mean_check_box.Bind(wx.EVT_CHECKBOX, self.__enableMeanRiskImport)

        self.total_risk_check_box = wx.CheckBox(self.window, label="Total Risk of CHD")
        self.total_risk_check_box.Bind(wx.EVT_CHECKBOX, self.__enableTotalImport)

        self.fatal_risk_check_box = wx.CheckBox(self.window, label="Fatal Risk of CHD")
        self.fatal_risk_check_box.Bind(wx.EVT_CHECKBOX, self.__enableFatalImport)

        self.statins_check_box = wx.CheckBox(self.window, label="Statins Usage")
        self.statins_check_box.Bind(wx.EVT_CHECKBOX, self.__enableStatinsUseImport)

        self.import_btn1 = wx.Button(self.window, label="Import files", size=(400, 40))
        self.import_btn1.Disable()
        self.import_btn1.Bind(wx.EVT_BUTTON, self.__import_mean_risks)

        self.import_btn2 = wx.Button(self.window, label="Import files", size=(400, 40))
        self.import_btn2.Disable()
        self.import_btn2.Bind(wx.EVT_BUTTON, self.__import_total_chd)

        self.import_btn3 = wx.Button(self.window, label="Import files", size=(400, 40))
        self.import_btn3.Disable()
        self.import_btn3.Bind(wx.EVT_BUTTON, self.__import_fatal_chd)

        self.import_btn4 = wx.Button(self.window, label="Import files", size=(400, 40))
        self.import_btn4.Disable()
        self.import_btn4.Bind(wx.EVT_BUTTON, self.__import_statins_use)

        sizer.AddMany([self.mean_check_box, (self.import_btn1, 1, wx.EXPAND),
                       self.total_risk_check_box, (self.import_btn2, 1, wx.EXPAND),
                       self.fatal_risk_check_box, (self.import_btn3, 1, wx.EXPAND),
                       self.statins_check_box, (self.import_btn4, 1, wx.EXPAND)])

        self.left_box.Add(sizer, flag=wx.EXPAND | wx.ALL, border=15)
        self.__hide_cardio_menu()

    def __create_depression_menu(self):
        sizer1 = wx.GridSizer(2, 2, 10, 10)
        sizer2 = wx.GridSizer(2, 3, 10, 10)

        self.nhanes_check_box = wx.CheckBox(self.window, label="NHANES Cohort")
        self.nhanes_check_box.Bind(wx.EVT_CHECKBOX, self.__enableNHANESImport)

        self.import_nhanes_btn = wx.Button(self.window, label="Import files", size=(400, 40))
        self.import_nhanes_btn.Disable()
        self.import_nhanes_btn.Bind(wx.EVT_BUTTON, self.__import_nhanes_data)

        self.prevalence_check_box = wx.CheckBox(self.window, label="Depression Prevalence")
        self.prevalence_check_box.Bind(wx.EVT_CHECKBOX, self.__enablePrevalenceImport)

        self.import_preval_btn = wx.Button(self.window, label="Import files", size=(400, 40))
        self.import_preval_btn.Disable()
        self.import_preval_btn.Bind(wx.EVT_BUTTON, self.__import_depression_prevalence)

        self.roc_text = wx.StaticText(self.window, label="Select Cohorts")

        self.cohortE_check_box = wx.CheckBox(self.window, label="Cohort E")
        self.cohortE_check_box.Bind(wx.EVT_CHECKBOX, self.__enable_plot_button)
        self.cohortE_check_box.Disable()

        self.cohortF_check_box = wx.CheckBox(self.window, label="Cohort F")
        self.cohortF_check_box.Bind(wx.EVT_CHECKBOX, self.__enable_plot_button)
        self.cohortF_check_box.Disable()

        self.cohortG_check_box = wx.CheckBox(self.window, label="Cohort G")
        self.cohortG_check_box.Bind(wx.EVT_CHECKBOX, self.__enable_plot_button)
        self.cohortG_check_box.Disable()

        self.cohortH_check_box = wx.CheckBox(self.window, label="Cohort H")
        self.cohortH_check_box.Bind(wx.EVT_CHECKBOX, self.__enable_plot_button)
        self.cohortH_check_box.Disable()

        self.cohortI_check_box = wx.CheckBox(self.window, label="Cohort I")
        self.cohortI_check_box.Bind(wx.EVT_CHECKBOX, self.__enable_plot_button)
        self.cohortI_check_box.Disable()

        self.plot_roc_button = wx.Button(self.window, label="Plot", size=(200, 40))
        self.plot_roc_button.Bind(wx.EVT_BUTTON, self.__plot_roc_curve)
        self.plot_roc_button.Disable()

        sizer1.AddMany([self.nhanes_check_box, (self.import_nhanes_btn, 1, wx.EXPAND),
                        self.prevalence_check_box, (self.import_preval_btn, 1, wx.EXPAND)])
        sizer2.AddMany([self.cohortE_check_box, self.cohortF_check_box, self.cohortG_check_box,
                        self.cohortH_check_box, self.cohortI_check_box])

        self.left_box.Add(sizer1, flag=wx.EXPAND | wx.ALL, border=20)
        self.left_box.Add(self.roc_text, flag=wx.LEFT | wx.RIGHT, border=20)
        self.left_box.Add(sizer2, flag=wx.EXPAND | wx.ALL, border=20)
        self.left_box.Add(self.plot_roc_button, flag=wx.EXPAND | wx.LEFT | wx.RIGHT, border=20)

        self.__hide_depression_menu()

    def __create_acs_refiner_menu(self):
        sizer = wx.GridSizer(2, 3, 10, 10)

        self.pop_count_cb = wx.CheckBox(self.window, label="Compute population weights")
        self.pop_count_cb.Bind(wx.EVT_CHECKBOX, self.__enable_acs_import_button)

        self.col_selection_btn = wx.Button(self.window, label="Select Columns", size=(200, 40))
        self.col_selection_btn.Disable()
        self.col_selection_btn.Bind(wx.EVT_BUTTON, self.__select_columns_acs)

        self.import_acs_btn = wx.Button(self.window, label="Import files", size=(200, 40))
        self.import_acs_btn.Disable()
        self.import_acs_btn.Bind(wx.EVT_BUTTON, self.__import_acs_file)

        self.ipf_cb = wx.CheckBox(self.window, label="Raking")
        self.ipf_cb.Bind(wx.EVT_CHECKBOX, self.__enable_pums_import_button)

        self.import_pums_btn = wx.Button(self.window, label="Import PUMS files", size=(200, 40))
        self.import_pums_btn.Disable()
        self.import_pums_btn.Bind(wx.EVT_BUTTON, self.__import_pums_file)

        self.import_marginals_btn = wx.Button(self.window, label="Import Marginals", size=(200, 40))
        self.import_marginals_btn.Disable()
        self.import_marginals_btn.Bind(wx.EVT_BUTTON, self.__import_marginals)

        sizer.AddMany([self.pop_count_cb, (self.col_selection_btn, 1, wx.EXPAND),(self.import_acs_btn, 1, wx.EXPAND),
                       self.ipf_cb, (self.import_pums_btn, 1, wx.EXPAND), (self.import_marginals_btn, 1, wx.EXPAND)])

        self.left_box.Add(sizer, flag=wx.EXPAND | wx.ALL, border=20)

        self.__hide_acs_refiner_menu()

    def __model_selection(self, event):
        self.model_name = self.models[self.choice_models.GetCurrentSelection()]
        if self.model_name == "Cardio Model":
            self.__display_cardio_menu()
            self.__hide_depression_menu()
            self.__hide_acs_refiner_menu()

            self.cardio_model = CardioModel(self)

        elif self.model_name == "Depression Model":
            self.__display_depression_menu()
            self.__hide_cardio_menu()
            self.__hide_acs_refiner_menu()

            self.depression_model = DepressionModel(self)
        else:
            self.__display_acs_refiner_menu()
            self.__hide_cardio_menu()
            self.__hide_depression_menu()

            self.acs_refiner = ACSRefiner(self)

        self.display_text_box.AppendText(self.model_name + " is selected!\n")

        self.choice_models.Disable()
        self.window.Fit()
        self.window.SetSize((Interface.WIDTH-10, Interface.HEIGHT-10))

    def __display_cardio_menu(self):
        self.mean_check_box.Show()
        self.import_btn1.Show()

        self.total_risk_check_box.Show()
        self.import_btn2.Show()

        self.fatal_risk_check_box.Show()
        self.import_btn3.Show()

        self.statins_check_box.Show()
        self.import_btn4.Show()

    def __hide_cardio_menu(self):
        self.mean_check_box.Hide()
        self.import_btn1.Hide()

        self.total_risk_check_box.Hide()
        self.import_btn2.Hide()

        self.fatal_risk_check_box.Hide()
        self.import_btn3.Hide()

        self.statins_check_box.Hide()
        self.import_btn4.Hide()

    def __display_depression_menu(self):
        self.nhanes_check_box.Show()
        self.import_nhanes_btn.Show()

        self.prevalence_check_box.Show()
        self.import_preval_btn.Show()

        self.roc_text.Show()
        self.cohortE_check_box.Show()
        self.cohortF_check_box.Show()
        self.cohortG_check_box.Show()
        self.cohortH_check_box.Show()
        self.cohortI_check_box.Show()
        self.plot_roc_button.Show()

    def __hide_depression_menu(self):
        self.nhanes_check_box.Hide()
        self.import_nhanes_btn.Hide()

        self.prevalence_check_box.Hide()
        self.import_preval_btn.Hide()

        self.roc_text.Hide()
        self.cohortE_check_box.Hide()
        self.cohortF_check_box.Hide()
        self.cohortG_check_box.Hide()
        self.cohortH_check_box.Hide()
        self.cohortI_check_box.Hide()
        self.plot_roc_button.Hide()

    def __display_acs_refiner_menu(self):
        self.pop_count_cb.Show()
        self.col_selection_btn.Show()
        self.import_acs_btn.Show()

        self.ipf_cb.Show()
        self.import_pums_btn.Show()
        self.import_marginals_btn.Show()

    def __hide_acs_refiner_menu(self):
        self.pop_count_cb.Hide()
        self.col_selection_btn.Hide()
        self.import_acs_btn.Hide()

        self.ipf_cb.Hide()
        self.import_pums_btn.Hide()
        self.import_marginals_btn.Hide()

    def __import_mean_risks(self, event):
        mean_risk_path = self.__import_files()

        if len(mean_risk_path) > 0:
            self.cardio_model.import_risk_factor(mean_risk_path)

    def __import_total_chd(self, event):
        total_risk_path = self.__import_files()
        if len(total_risk_path) > 0:
            self.cardio_model.import_total_chd(total_risk_path)

    def __import_fatal_chd(self, event):
        fatal_risk_path = self.__import_files()
        if len(fatal_risk_path) > 0:
            self.cardio_model.import_fatal_chd(fatal_risk_path)

    def __import_statins_use(self, event):
        statins_use_path = self.__import_files()
        if len(statins_use_path) > 0:
            self.cardio_model.import_statins_use(statins_use_path)

    def __import_nhanes_data(self, event):
        nhanes_data_path = self.__import_files()
        if len(nhanes_data_path) > 0:
            self.depression_model.import_nhanes(nhanes_data_path)

    def __import_depression_prevalence(self, event):
        preval_data_path = self.__import_files()
        if len(preval_data_path) > 0:
            self.depression_model.import_depression_preval(preval_data_path)

    def __select_columns_acs(self, event):
        dialog_box = wx.Dialog(self, title="Select one or more columns", size=(900, 350))
        panel_dialog = wx.Panel(dialog_box)

        self.column_dictionary = {"year": "YEAR", "Id": "ID",
                                  "Id2": "ID2", "Geography": "GEO",
                                  "Population Group": "POP_GROUP",
                                  "Estimate; Total population": "TOT_POP",
                                  "Estimate; Total population - SEX AND AGE - 18 years and over": "POP_18_OVER",
                                  "Estimate; Total population - SEX AND AGE - 18 years and over - Male": "POP_18_M",
                                  "Estimate; Total population - SEX AND AGE - 18 years and over - Female": "POP_18_F",
                                  "Estimate; Total population - SEX AND AGE - 18 to 34 years": "POP_18_34",
                                  "Estimate; Total population - SEX AND AGE - 18 to 34 years - Male": "POP_18_34_M",
                                  "Estimate; Total population - SEX AND AGE - 18 to 34 years - Female": "POP_18_34_F",
                                  "Estimate; Total population - SEX AND AGE - 35 to 64 years": "POP_35_64",
                                  "Estimate; Total population - SEX AND AGE - 35 to 64 years - Male": "POP_35_64_M"	,
                                  "Estimate; Total population - SEX AND AGE - 35 to 64 years - Female": "POP_35_64_F",
                                  "Estimate; Total population - SEX AND AGE - 65 years and over": "POP_65_OVER",
                                  "Estimate; Total population - SEX AND AGE - 65 years and over - Male": "POP_65_M",
                                  "Estimate; Total population - SEX AND AGE - 65 years and over - Female": "POP_65_F"
                                  }

        self.selected_columns = []

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.list_box_left = wx.ListBox(panel_dialog, size=(410, 200),
                                        choices=list(self.column_dictionary.keys()),
                                        style=wx.LB_MULTIPLE)

        # self.list_box_left.Bind(wx.EVT_LISTBOX, self.__column_selection_list_box)

        self.list_box_right = wx.ListBox(panel_dialog, size=(410, 200),
                                         style=wx.LB_SINGLE)

        self.add_btn = wx.Button(panel_dialog, label=">>", pos=(240, 230), size=(200, 40))
        self.add_btn.Bind(wx.EVT_BUTTON, self.__add_columns)

        self.remove_btn = wx.Button(panel_dialog, label="<<", pos=(460, 230), size=(200, 40))
        self.remove_btn.Bind(wx.EVT_BUTTON, self.__remove_columns)

        sizer.Add(self.list_box_left, flag=wx.ALL, border=20)
        sizer.Add(self.list_box_right, flag=wx.ALL, border=20)

        panel_dialog.SetSizer(sizer)

        dialog_box.ShowModal()

    def __import_acs_file(self, event):
        acs_path = self.__import_files()
        # print(acs_path)
        if len(acs_path) > 0:
            self.acs_refiner.import_acs(acs_path, self.selected_columns, self.column_dictionary)

    def __import_pums_file(self, event):
        pums_file_paths = self.__import_files()
        if len(pums_file_paths) > 0:
            self.acs_refiner.import_pums(pums_file_paths)

    def __import_marginals(self, event):
        marginal_file_paths = self.__import_files()
        if len(marginal_file_paths) > 0:
            self.import_marginals_btn.Disable()
            self.acs_refiner.import_marginals(marginal_file_paths)

    def __import_files(self):
        wildcards = "CSV files (*.csv) | *.csv|"\
                    "All files (*.*) | *.*"

        file_dialog = wx.FileDialog(self, message="Choose a file",
                                    defaultDir=os.getcwd(),
                                    defaultFile="",
                                    wildcard=wildcards,
                                    style=wx.FD_OPEN | wx.FD_MULTIPLE | wx.FD_CHANGE_DIR)

        paths = []
        if file_dialog.ShowModal() == wx.ID_OK:
            paths = file_dialog.GetPaths()
            self.display_text_box.AppendText("You have selected " + str(len(paths)) + " files!\n")
            for path in paths:
                self.display_text_box.AppendText("File path: " + path + "\n")
        else:
            self.display_text_box.AppendText("File is not imported!\n")
            wx.MessageBox("Error: No files were imported!")

        self.display_text_box.AppendText("\n")

        return paths

    def __export_files(self, event):
        if self.model_name == "Cardio Model":
            self.cardio_model.output()
            time.sleep(3)
        elif self.model_name == "Depression Model":
            self.depression_model.process()
            time.sleep(0.5)

            if self.depression_model.is_complete():
                self.__enable_cohort_check_box()
        elif self.model_name == "ACS Refiner":
            if self.pop_count_cb.IsChecked():
                self.acs_refiner.output()
                time.sleep(3)
            elif self.ipf_cb.IsChecked():
                self.acs_refiner.start_ipf()
                self.acs_refiner.output()
                time.sleep(3)

    def __clear(self, event):
        self.display_text_box.Clear()

    def __enableMeanRiskImport(self, event):
        if self.mean_check_box.IsChecked():
            self.import_btn1.Enable()
        else:
            self.import_btn1.Disable()

    def __enableTotalImport(self, event):
        if self.total_risk_check_box.IsChecked():
            self.import_btn2.Enable()
        else:
            self.import_btn2.Disable()

    def __enableFatalImport(self, event):
        if self.fatal_risk_check_box.IsChecked():
            self.import_btn3.Enable()
        else:
            self.import_btn3.Disable()

    def __enableStatinsUseImport(self, event):
        if self.statins_check_box.IsChecked():
            self.import_btn4.Enable()
        else:
            self.import_btn4.Disable()


    def __enableNHANESImport(self, event):
        if self.nhanes_check_box.IsChecked():
            self.import_nhanes_btn.Enable()
        else:
            self.import_nhanes_btn.Disable()

    def __enablePrevalenceImport(self, event):
        if self.prevalence_check_box.IsChecked():
            self.import_preval_btn.Enable()
        else:
            self.import_preval_btn.Disable()

    def __enable_cohort_check_box(self):
        self.cohortE_check_box.Enable()
        self.cohortF_check_box.Enable()
        self.cohortG_check_box.Enable()
        self.cohortH_check_box.Enable()
        self.cohortI_check_box.Enable()

    def __enable_plot_button(self, event):
        if self.__isCohortChecked():
            self.plot_roc_button.Enable()
        else:
            self.plot_roc_button.Disable()

    def __enable_acs_import_button(self, event):
        if self.pop_count_cb.IsChecked():
            self.import_acs_btn.Enable()
            self.col_selection_btn.Enable()
        else:
            self.import_acs_btn.Disable()
            self.col_selection_btn.Disable()

    def __enable_pums_import_button(self, event):
        if self.ipf_cb.IsChecked():
            self.import_pums_btn.Enable()
            self.import_marginals_btn.Enable()
        else:
            self.import_pums_btn.Disable()
            self.import_marginals_btn.Disable()

    def __plot_roc_curve(self, event):
        self.depression_model.plot_roc()

    def __add_columns(self, event):
        left_indexes = self.__get_column_index(self.list_box_left)
        for index in left_indexes:
            col_name = self.list_box_left.GetString(index)
            self.selected_columns.append(col_name)

            self.selected_columns = list(OrderedDict.fromkeys(self.selected_columns))
            self.list_box_right.Set(self.selected_columns)

        # print(self.selected_columns)

    def __remove_columns(self, event):
        right_indexes = self.__get_column_index(self.list_box_right)
        for index in right_indexes:
            col_name = self.list_box_right.GetString(index)
            self.selected_columns.remove(col_name)
            self.list_box_right.Set(self.selected_columns)

        # print(self.selected_columns)

    def __get_column_index(self, list_box):
        indexes = list_box.GetSelections()
        return indexes

    def __thread_start(self, event):
        thread = td.Thread(target=self.__export_files, args=(event, ))
        thread.start()

    def __isCohortChecked(self):
        if self.cohortE_check_box.IsChecked():
            return True
        elif self.cohortF_check_box.IsChecked():
            return True
        elif self.cohortG_check_box.IsChecked():
            return True
        elif self.cohortH_check_box.IsChecked():
            return True
        elif self.cohortI_check_box.IsChecked():
            return True
        else:
            return False












