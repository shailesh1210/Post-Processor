from RefinerIO import RefinerIO
import wx


class ACSRefiner:
    def __init__(self, interface):
        self.__ui = interface
        self.__io = RefinerIO(interface)

    def import_acs(self, acs_file_path, columns, columns_dict):

        if len(columns) > 0:
            self.__io.read_acs_data(file_paths=acs_file_path,
                                    columns=columns, columns_dict=columns_dict)
        else:
            wx.MessageBox("Error: One or more columns must be selected!")

    def import_pums(self, pums_file_path):
        self.__io.read_pums_data(file_paths=pums_file_path)

    def import_marginals(self, marginal_file_path):
        self.__io.read_marginals(file_paths=marginal_file_path)

    def start_ipf(self):
        self.__io.ipf()

    def output(self):
        self.__io.output_acs_data()
        self.__io.output_income()