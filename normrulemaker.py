#Alma Normalization Rule Generator

import tkinter as tk
from tkinter import messagebox, filedialog
import re
import pandas as pd

class NormRuleMaker:
    def __init__(self, root):
        self.root = root
        self.root.title("Alma Normalization Rule Maker")

        tk.Label(root, text="This program will generate a normalization rule for adding new headings based on the existence of other headings in specific fields.\nInputs must be in .xlsx or .csv format and should have two columns, one for the original heading and one for the heading to be added.\nColumn titles should be the field and indicators, using # for blanks (e.g., 655#7).\nThe column should include the full contents of the field, with subfields separated by $ (e.g., Informational works$2lcgft).\nThe start of the field will be assumed to be in $a.").pack(pady=10)

        #Use checkbox to trigger deletion of existing fields
        tk.Label(root, text="Delete headings in Column A from records?").pack(pady=10)
        self.DeleteHeadings = tk.BooleanVar()
        tk.Checkbutton(root, variable=self.DeleteHeadings).pack()

        tk.Label(root, text="Select a file to process:").pack(pady=10)
        tk.Button(root, text="LOAD", command=self.getfile).pack()

        tk.Label(root, text="Generate Normalization Rule").pack(pady=10)
        tk.Button(root, text="RUN", command=self.generaterule).pack()

        #Create dataframe and check for input
        self.df = None
        self.inputpresent = False

        #Create base rule
        self.baserule = ""

    def getfile(self):
        file = filedialog.askopenfilename()
        #Check filetype and populate dataframe
        if file.endswith("xlsx"):
            try:
                self.df = pd.read_excel(file)
                print("XLSX file recognized and read")
                self.inputpresent = True
                return self.inputpresent
            except Exception as e:
                messagebox.showerror(title="Fileread error - XLSX", message=e)
                self.inputpresent = False
                return self.inputpresent
        elif file.endswith("csv"):
            try:
                self.df = pd.read_csv(file)
                print("CSV file recognized and read")
                self.inputpresent = True
                return self.inputpresent
            except Exception as e:
                messagebox.showerror(title="Fileread error - CSV", message=e)
                self.inputpresent = False
                return self.inputpresent
        else:
            messagebox.showerror(title="Filetype Error", message="Error: Please ensure file is in .xlsx or .csv format and filename includes filetype extension.")
            self.inputpresent = False
            return self.inputpresent
    
    def generaterule(self):
        #Check for input
        if self.inputpresent == False:
            messagebox.showerror(title="Missing Input", message="Error: Please select an input before continuing.")
            return None
        headers = list(self.df.columns.values)
        #Ensure df has two columns
        if len(headers) != 2:
            messagebox.showerror(title="File Error", message="Error: Please ensure file has two columns.")
            return None
        #Parse field and ind data
        columna = headers[0]
        columnb = headers[1]
        fielda = columna[:3]
        ind1a = columna[3]
        ind2a = columna[4]
        fieldb = columnb[:3]
        ind1b = columnb[3]
        ind2b = columnb[4]
        count = 0
        #Get count of rows in df
        for index, row in self.df.iterrows():
            count += 1
        for index, row in self.df.iterrows():
            #parse row data to determine if multiple subfields exist and create when and then clauses
            fielda_contents = row[columna]
            if "$" in fielda_contents:
                fielda_contents = fielda_contents.split("$")
                whenclause = f'exists "{fielda}.{{{ind1a},{ind2a}}}.a.{fielda_contents[0]}"'
                fielda_contents.pop(0)
                for contents in fielda_contents:
                    whenclause += f' and (exists "{fielda}.{{{ind1a},{ind2a}}}.{contents[0]}.{contents[1:]}")'
            else:
                whenclause = f'exists "{fielda}.{{{ind1a},{ind2a}}}.a.{fielda_contents}"'
            fieldb_contents = row[columnb]
            if "$" in fieldb_contents:
                fieldb_contents = fieldb_contents.split("$")
                thenclause = f'addField "{fieldb}.{{{ind1b},{ind2b}}}.a.{fieldb_contents[0]}"'
                baseheading = fieldb_contents[0]
                fieldb_contents.pop(0)
                for contents in fieldb_contents:
                    thenclause += f'\naddSubField "{fieldb}.{{{ind1b},{ind2b}}}.{contents[0]}.{contents[1:]}" if (exists "{fieldb}.{{{ind1b},{ind2b}}}.a.{baseheading}")'
            else:
                thenclause = f'addField "{fieldb}.{{{ind1b},{ind2b}}}.a.{fieldb_contents}"'
            self.baserule += f'rule "Heading Update {count+1}"\nsalience {count+1}\nwhen\n{whenclause}\nthen\n{thenclause}\nend\n\n'
            count -= 1
        self.baserule += f'rule "Heading Update {count+1}"\nsalience {count+1}\nwhen\nTRUE\nthen\ncorrectDuplicateFields "{fieldb}"\nend'
        #Remove headings if checkbox is True
        if self.DeleteHeadings.get():
            self.baserule += f'\n\nrule "Delete Headings"\nsalience {count}\nwhen\nTRUE\nthen\n'
            for index, row in self.df.iterrows():
                if "$" in row[columna]:
                    fielda_contents = str(row[columna]).split("$")
                    self.baserule += f'removeField "{columna[:3]}" if (exists "{columna[:3]}.{{{ind1a},{ind2a}}}.a.{fielda_contents[0]}")\n'
                    # fielda_contents.pop(0)
                    # for contents in fielda_contents:
                    #     self.baserule += f' and (exists "{columna[:3]}.{{{ind1a},{ind2a}}}.{contents}")'
                    # self.baserule += ")\n"
                else:
                    self.baserule += f'removeField "{columna[:3]}" if (exists "{columna[:3]}.a.{{{ind1a},{ind2a}}}.{str(row[columna])}")\n'
            self.baserule += "end"
        outputfile = filedialog.asksaveasfilename()
        with open(f'{outputfile}.txt',"w") as fh:
            fh.write(self.baserule)

def main():
    root = tk.Tk()
    app = NormRuleMaker(root)
    root.mainloop()

if __name__ == "__main__":
    main()