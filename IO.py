import pandas as pd
import wx
import os


class IO:
    def __init__(self, interface):
        self.display = True
        self.__curDir = os.getcwd()
        self.__ui = interface

    def setDisplayFlag(self, disp):
        self.display = disp

    def getCurDir(self):
        return self.__curDir

    def show(self):
        return self.display

    def read(self, file_paths, ref_header, ignore_index, index_col):
        df = pd.DataFrame()
        for path in file_paths:
            data = pd.read_csv(path, index_col=index_col)
            data.columns = [col.strip() for col in data.columns]

            if not self.__exists(header1=data.columns, header2=ref_header):
                wx.MessageBox("Error: One or more columns are missing in\n" + path)
                self.display = False
                break
            else:
                if df.empty:
                    df = data
                else:
                    df = df.append(data, ignore_index=ignore_index)

                self.enable_export()

        return df

    def read_csv(self, file_paths, columns, ignore_index):
        df = pd.DataFrame()
        for path in file_paths:
            if len(columns) > 0:
                data = pd.read_csv(path, usecols=columns)
            else:
                data = pd.read_csv(path)

            if df.empty:
                df = data
            else:
                df = df.append(data, ignore_index=ignore_index)

            self.enable_export()

        return df

    def write(self, data, filename, append=False):
        if not self.display:
            wx.MessageBox("Error: Cannot export file!")
        else:
            out_path = os.path.join(self.__curDir, filename)
            if os.path.isfile(out_path):
                open(out_path, "w").close()

            if not append:
                data.to_csv(out_path, index=True)
            else:
                data.to_csv(out_path, mode="a", index=True)
            wx.MessageBox("Success: " + filename + " exported!")

    def __exists(self, header1, header2):
        count = 0
        for col1 in header1:
            for col2 in header2:
                if col1 == col2:
                    count += 1

        if count == len(header2):
            return True
        else:
            return False

    def enable_export(self):
        if not self.__ui.export_button.IsEnabled():
            self.__ui.export_button.Enable()