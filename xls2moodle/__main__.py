"""Main module for xls2 moodle conversion."""
# -*- coding: utf-8 -*-
import os
import sys
import copy
#import xls2moodle

try:
    from lxml import etree
    import pandas as pd
    import numpy as np
except ImportError:
    message = 'Dependencies missing!\n' \
              'Install via "pip install -r requirements.txt"'
    import tkinter.messagebox
    try:
        root_window = tkinter.Tk()
        root_window.withdraw()  # hide the root window
        tkinter.messagebox.showerror(message=message)
        root_window.destroy()
    except tkinter.TclError:
        print(message)
    sys.exit(1)


def create_category(parent, name, course):
    """
    Create a category in xml structure.

    Takes the category name and appends following xml structure:
    <question type="category">
        <category>
            <text>$course$/Standard für [SoSe17] BAI/Name</text>
        </category>
    </question>

    :param parent: the root
    :param name: str, name for the questions (?)
    :param course: str, name of the course
    """
    question = etree.SubElement(parent, 'question',
                                attrib={'type': 'category'})
    category = etree.SubElement(question, 'category')
    text = etree.SubElement(category, 'text')
    text.text = '$course$/ImportFragen{}/{}'.format(course, name)


def add_question(parent, template, title, text, answers, verbose=False):
    """
    Take parameters and create the xml structure for questions.

    :param parent: the root
    :param template: template of correct answers
    :param title: question title
    :param text: question
    :param answers: list of answers. first the true, then the false answers!
    :param verbose: print messages if True
    xml structure (for one correct answer):
    <question type="multichoice">
        <name>
            <text>title</text>
        </name>
        <questiontext format="html">
            <text><![CDATA[<p>text</p>]]></text>
        </questiontext>
        <generalfeedback format="html">
            <text/>
        </generalfeedback>
        <defaultgrade>1.0000000</defaultgrade>
        <penalty>0.0000000</penalty>
        <hidden>0</hidden>
        <single>false</single>
        <shuffleanswers>true</shuffleanswers>
        <answernumbering>none</answernumbering>
        <correctfeedback format="html">
            <text/>
        </correctfeedback>
        <partiallycorrectfeedback format="html">
            <text/>
        </partiallycorrectfeedback>
        <incorrectfeedback format="html">
            <text/>
        </incorrectfeedback>
        <answer fraction="-100" format="html">
            <text>FALSEe Answer1</text>
            <feedback format="html">
                <text/>
            </feedback>
        </answer>
        <answer fraction="-100" format="html">
            <text><![CDATA[<p>FALSEe Answer2<br></p>]]></text>
            <feedback format="html">
                <text/>
            </feedback>
        </answer>
        <answer fraction="-100" format="html">
            <text><![CDATA[<p>FALSEe Answer3<br></p>]]></text>
            <feedback format="html">
                <text/>
            </feedback>
        </answer>
        <answer fraction="100" format="html">
            <text><![CDATA[<p>Richtige Answer4<br></p>]]></text>
            <feedback format="html">
                <text/>
            </feedback>
        </answer>
    </question>
    """
    # modify template with the question data
    template.xpath('/question/name/text')[0].text = title.decode("utf-8")
    if verbose:
        print("Question: ", title)
        print("Text:", text.decode('utf-8'))

    template.xpath('/question/questiontext/text')[0].text = etree.CDATA(
        text.decode("utf-8"))
    for m in range(len(template.xpath('/question/answer/text'))):
        try:
            cell_content = answers[m].replace("$", "$$")
        except AttributeError:  # cell contains int
            cell_content = answers[m]
        template.xpath('/question/answer/text')[m].text = etree.CDATA(
            "%s" % cell_content)

    # add question to root of main file
    parent.append(template.getroot())


# noinspection PyPep8Naming
def TableToXML(table, outname, course, verbose=0, xmltemplate_path=""):
    """
    Parse and convert the input table to xml format.

    :param table: df with questions
    :param outname: str, location for storing the final table
    :param course. str, course name
    :param verbose: bool, if prints should be used for progress (default: 0)
    """
    # import questions
    # the question table is exported from google docs as a csv.
    # The column names must be the same as in "BAI_Zwischentestat_Fragen.csv"
    try:
        questions = pd.read_csv(table, sep=",", encoding= 'utf-8')
    except pd.errors.ParserError:
        questions = pd.read_excel(table, 0)

    if xmltemplate_path == "":
        # get path of package data
        xmltemplate_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'xml_templates')

    # filter table
    if "Answer" in questions.columns:
        questions = questions[questions["Answer"] == 1]

    # get categories
    categories = list(set(questions["Theme"].tolist()))

    questions["CORRECT"] = [str(i) for i in questions["CORRECT"]]
    questions["FALSE"] = [str(i) for i in questions["FALSE"]]

    # clean questions dataframe
    if verbose:
        print(questions["CORRECT"].isnull().values.any())
    questions.replace(np.nan, "0", inplace=True)
    questions["CORRECT"].fillna("0", inplace=True)
    if verbose:
        print(questions["CORRECT"].isnull().values.any())
    questions["FALSE"].fillna("0", inplace=True)
    questions["CORRECT"] = questions["CORRECT"].map(
        lambda x: list(map(int, x.replace(".", ",").split(","))))
    questions["FALSE"] = questions["FALSE"].map(
        lambda x: list(map(int, x.replace(".", ",").split(","))))

    # check for errors in data
    questions["datacheck"] = questions["CORRECT"] + questions["FALSE"]
    for i in questions.index:
        # see error codes for cases
        if len(questions.loc[i, "datacheck"]) != len(
                (set(questions.loc[i, "datacheck"]))):
            raise ValueError(
                "duplication in CORRECT/FALSE columns at index {}".format(i))

        if not (set(questions.loc[i, "datacheck"]) == {0, 1, 2, 3, 4}
                or set(questions.loc[i, "datacheck"]) == {1, 2, 3, 4}):
            raise ValueError(
                "Not all answers in CORRECT/FALSE column at index {}".format(i))

        if questions.loc[i, "CORRECT"] == [0]:
            raise ValueError("zero in CORRECT column at index {}".format(i))

        if pd.isnull(questions.loc[i, "Theme"]):
            raise ValueError("Empty category at index {}".format(i))

    # add/rename columns
    questions["num_correct"] = questions["CORRECT"].map(len)
    questions.rename(
        columns={'Question': 'text', 'Theme': 'category'},
        inplace=True)
    questions['answers'] = np.empty((len(questions), 0)).tolist()

    # create answer list with right answers first, then wrong answers
    for i in questions.index:
        remaining = [1, 2, 3, 4]
        for j in questions.loc[i, "CORRECT"]:
            questions.loc[i, "answers"].append(
                questions.loc[
                    i, ["Answer1", "Answer2", "Answer3", "Answer4"]][
                    j - 1])
            remaining.remove(j)
        for k in remaining:
            questions.loc[i, "answers"].append(
                questions.loc[
                    i, ["Answer1", "Answer2", "Answer3", "Answer4"]][
                    k - 1])

    # configure parser: activate cdata and remove blank text at import
    parser = etree.XMLParser(strip_cdata=False, remove_blank_text=True)

    # import template
    tree = etree.parse(os.path.join(xmltemplate_path, 'template.xml'),
                       parser=parser)
    root = tree.getroot()

    # import question template for every possible distribution of points.
    # This is necessary because the points have to add up to 100 in the ISIS
    # System
    correct_templates = list()
    for tf in ('one_correct.xml', 'two_correct.xml', 'three_correct.xml', 'four_correct.xml'):
        correct_templates.append(etree.parse(os.path.join(xmltemplate_path, tf), parser=parser))
    correct_templates = tuple(correct_templates)

    # append questions and categories to xml file
    for i_category in categories:
        print("Processing category: {}".format(i_category.encode("UTF-8")))

        create_category(root, i_category, course)
        for i in questions[questions["category"] == i_category].index:
            if verbose:
                print("Processing Question:")
                print(questions.loc[i, "num_correct"])
                print(questions.loc[i, "text"])
                print(questions.loc[i, "answers"])
                print(correct_templates[
                    questions.loc[i, "num_correct"] - 1].xpath(
                        '/question/answer/@fraction'))
            add_question(
                root,
                # choose the right template depending on the number of right
                # answers
                template=copy.deepcopy(correct_templates[questions.loc[i, "num_correct"] - 1]),
                title=questions.loc[i, "text"].replace("$", "$$").encode("UTF-8")[0:38],
                text=questions.loc[i, "text"].replace("$", "$$").encode("UTF-8"),
                answers=questions.loc[i, "answers"])

    # write the xml file
    tree.write(outname, encoding="UTF-8", xml_declaration=True, pretty_print=True)


def convert_xls2moodle(table, course, verbose=False, template="") -> str:
    """
    Perform xls2 moodle conversion.

    :param table: df with questions
    :param course. str, course name
    :param verbose: bool, if prints should be used for progress
    """
    # save the xml file with the same name as input but with xml extension
    outname = table.split(".")[0]+"_moodle_import.xml"
    print(f"Reading {table}...")
    print(f"XML path {template}...")
    print(f"Generating questions for {course}...")
    TableToXML(table, outname, course, verbose=verbose, xmltemplate_path=template)
    print(f"Done! File saved to {outname}...")
    return outname


def main():
    """XLS2Moodle main function."""
    if len(sys.argv) <= 1:
        import tkinter
        root_window = tkinter.Tk()
        root_window.geometry("540x100")
        # root_window.resizable(0, 0)
        root_window.title('Convert multiple choice questions from xls to moodle\'s xml format')
        root_window.columnconfigure(0, weight=1)
        root_window.columnconfigure(1, weight=2)
        root_window.columnconfigure(2, weight=1)
        root_window.rowconfigure(0, weight=1)
        root_window.rowconfigure(1, weight=1)
        root_window.rowconfigure(2, weight=1)
        root_window.rowconfigure(3, weight=1)

        # course name (string input)
        course_label = tkinter.Label(root_window, text='Course name:')
        course_label.grid(column=0, row=0, sticky=tkinter.E)
        course_entry = tkinter.Entry(root_window)
        course_entry.grid(column=1, row=0, columnspan=2, sticky=tkinter.EW)

        table_label = tkinter.Label(root_window, text='Table file:')
        table_label.grid(column=0, row=1, sticky=tkinter.E)
        table_entry = tkinter.Entry(root_window, state=tkinter.DISABLED)
        table_entry.grid(column=1, row=1, sticky=tkinter.EW)

        xml_label = tkinter.Label(root_window, text='XML folder: (optional)')
        xml_label.grid(column=0, row=2, sticky=tkinter.E)
        xml_entry = tkinter.Entry(root_window, state=tkinter.DISABLED)
        xml_entry.grid(column=1, row=2, sticky=tkinter.EW)

        def handle_file_selection() -> None:
            import tkinter.filedialog
            filetypes = (('Excel files', '*.xlsx'), ('CSV files', '*.csv'), ('All files', '*.*'))
            dialog = tkinter.filedialog.Open(root_window, title='Select table file',
                                             filetypes=filetypes)
            table_file_name = dialog.show()
            if table_file_name:
                # set to normal before inserting
                table_entry.config(state=tkinter.NORMAL)
                table_entry.delete(0, tkinter.END)
                table_entry.insert(tkinter.END, table_file_name)
                table_entry.config(state=tkinter.DISABLED)

        def handle_path_selection():
            import tkinter.filedialog
            pathname = tkinter.filedialog.askdirectory()
            print(pathname)
            if pathname:
                # set to normal before inserting
                xml_entry.config(state=tkinter.NORMAL)
                xml_entry.delete(0, tkinter.END)
                xml_entry.insert(tkinter.END, pathname)
                xml_entry.config(state=tkinter.DISABLED)

        # xls file
        file_selection_button = tkinter.Button(root_window, text='Select file...',
                                               command=handle_file_selection)
        file_selection_button.grid(column=2, row=1)

        # xlm path
        file_selection_button = tkinter.Button(root_window, text='Select path...',
                                               command=handle_path_selection)
        file_selection_button.grid(column=2, row=2)

        def handle_creation():
            if course_entry.get() and table_entry.get():
                outname = convert_xls2moodle(table_entry.get(), course_entry.get(),
                                             template=xml_entry.get())
                import tkinter.messagebox
                tkinter.messagebox.showinfo(message=f"Done! File saved to {outname}...")
                course_entry.delete(0, tkinter.END)
                # set to normal before inserting
                table_entry.config(state=tkinter.NORMAL)
                table_entry.delete(0, tkinter.END)
                table_entry.config(state=tkinter.DISABLED)

        run_button = tkinter.Button(root_window, text='Create Moodle XML',
                                    command=handle_creation)
        run_button.grid(column=1, row=3, columnspan=1, sticky=tkinter.E)
        root_window.mainloop()
    else:
        import argparse

        args_parser = argparse.ArgumentParser(
            formatter_class=argparse.RawDescriptionHelpFormatter, description='''\
    Convert multiple choice questions from xls to moodle\'s xml format
    Example: {} -c {} -t {}'''.format(sys.argv[0], 'AdvancedBioanalytics',
                                      os.path.join('examples', 'template_advanced.xlsx')))
        args_parser.add_argument('-v', '--verbose', default=False,
                                 action='store_true')
        args_parser.add_argument('-c', '--course', help='course name', required=True)
        args_parser.add_argument('-t', '--table',
                                 help='location of tabular excel file with questions',
                                 required=True)
        args_parser.add_argument('-x', '--templates',
                                 help='location of xml template files to use.', default="",
                                 required=False)
        args = args_parser.parse_args()
        convert_xls2moodle(args.table, args.course, args.verbose, args.templates)


if __name__ == "__main__":
    main()
