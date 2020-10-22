import os
import sys
from lxml import etree
import copy
import pandas as pd
import numpy as np


one_correct = None
two_correct = None
three_correct = None
four_correct = None

#import re
# def remove_control_characters(html):
#    def str_to_int(s, default, base=10):
#        if int(s, base) < 0x10000:
#            return unichr(int(s, base))
#        return default
#    html = re.sub(ur"&#(\d+);?", lambda c: str_to_int(c.group(1), c.group(0)), html)
#    html = re.sub(ur"&#[xX]([0-9a-fA-F]+);?", lambda c: str_to_int(c.group(1), c.group(0), base=16), html)
#    html = re.sub(ur"[\x00-\x08\x0b\x0e-\x1f\x7f]", "", html)
#    return (html)


def create_category(parent, name, course):
    """
    takes the category name and appends following xml structure:
    <question type="category">
        <category>
            <text>$course$/Standard für [SoSe17] BAI/Name</text>
        </category>
    </question>
    """
    question = etree.SubElement(parent, 'question', attrib={'type': 'category'})
    category = etree.SubElement(question, 'category')
    text = etree.SubElement(category, 'text')
    text.text = '$course$/ImportFragen{}/{}'.format(course, name)


def add_question(parent, num_correct, title, text, answers, verbose=False):
    """
    takes parameters and creates the xml structure for questions
    :param parent: the root
    :param num_correct: number of correct answers
    :param title: question title
    :param text: question
    :param answers: list of answers. first the true, then the false answers!
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
            <text>Falsche Aussage1</text>
            <feedback format="html">
                <text/>
            </feedback>
        </answer>
        <answer fraction="-100" format="html">
            <text><![CDATA[<p>Falsche Aussage2<br></p>]]></text>
            <feedback format="html">
                <text/>
            </feedback>
        </answer>
        <answer fraction="-100" format="html">
            <text><![CDATA[<p>Falsche Aussage3<br></p>]]></text>
            <feedback format="html">
                <text/>
            </feedback>
        </answer>
        <answer fraction="100" format="html">
            <text><![CDATA[<p>Richtige Aussage4<br></p>]]></text>
            <feedback format="html">
                <text/>
            </feedback>
        </answer>
    </question>
    """
    global one_correct
    global two_correct
    global three_correct
    global four_correct

    # choose the right template depending on the # of right answers
    if num_correct == 1:
        template = copy.deepcopy(one_correct)
    elif num_correct == 2:
        template = copy.deepcopy(two_correct)
    elif num_correct == 3:
        template = copy.deepcopy(three_correct)
    elif num_correct == 4:
        template = copy.deepcopy(four_correct)
    else:
        raise ValueError("num_correct must be between 1 and 4")

    # modify template with the question data
    template.xpath('/question/name/text')[0].text = title.decode("utf-8")
    if verbose:
        print("Question: ", title)
        print("Text:", text.decode('utf-8'))

    template.xpath('/question/questiontext/text')[0].text = etree.CDATA(text.decode("utf-8"))
    for m in range(len(template.xpath('/question/answer/text'))):
        template.xpath(
            '/question/answer/text')[m].text = etree.CDATA("%s" % answers[m].replace("$", "$$"))

    # add question to root of main file
    parent.append(template.getroot())


def TableToXML(table, outname, course, verbose=0):
    """

    """
    # %%
    global one_correct
    global two_correct
    global three_correct
    global four_correct

    # import questions
    # the question table is exported from google docs as a csv.
    # The column names must be the same as in "BAI_Zwischentestat_Fragen.csv"
    try:
        questions = pd.read_csv(table, sep=",")
    except:
        questions = pd.read_excel(table, 0)

    # filter table
    if "Anwendung" in questions.columns:
        questions = questions[questions["Anwendung"] == 1]

    # get categories
    categories = list(set(questions["Themenblock"].tolist()))

    questions["WAHR"] = [str(i) for i in questions["WAHR"]]
    questions["FALSCH"] = [str(i) for i in questions["FALSCH"]]

    # clean questions dataframe
    if verbose:
        print(questions["WAHR"].isnull().values.any())
    questions.replace("nan", "0", inplace=True)
    questions["WAHR"].fillna("0", inplace=True)
    if verbose:
        print(questions["WAHR"].isnull().values.any())
    questions["FALSCH"].fillna("0", inplace=True)
    questions["WAHR"] = questions["WAHR"].map(
        lambda x: list(map(int, x.replace(".", ",").split(","))))
    questions["FALSCH"] = questions["FALSCH"].map(
        lambda x: list(map(int, x.replace(".", ",").split(","))))

    # check for errors in data
    questions["datacheck"] = questions["WAHR"] + questions["FALSCH"]
    for i in questions.index:
        # see error codes for cases
        if len(questions.loc[i, "datacheck"]) != len((set(questions.loc[i, "datacheck"]))):
            raise ValueError("duplication in WAHR/FALSCH columns at index {}".format(i))

        if not (set(questions.loc[i, "datacheck"]) == set([0, 1, 2, 3, 4])
                or set(questions.loc[i, "datacheck"]) == set([1, 2, 3, 4])):
            raise ValueError("Not all answers in WAHR/FALSCH column at index {}".format(i))

        if questions.loc[i, "WAHR"] == [0]:
            raise ValueError("zero in WAHR column at index {}".format(i))

        if pd.isnull(questions.loc[i, "Themenblock"]):
            raise ValueError("Empty category at index {}".format(i))

    # add/rename columns
    questions["num_correct"] = questions["WAHR"].map(len)
    questions.rename(columns={'Hauptfrage': 'text', 'Themenblock': 'category'}, inplace=True)
    questions['answers'] = np.empty((len(questions), 0)).tolist()

    # create answer list with right answers first, then wrong answers
    for i in questions.index:
        remaining = [1, 2, 3, 4]
        for j in questions.loc[i, "WAHR"]:
            questions.loc[i, "answers"].append(
                questions.loc[i, ["Aussage1", "Aussage2", "Aussage3", "Aussage4"]][j-1])
            remaining.remove(j)
        for k in remaining:
            questions.loc[i, "answers"].append(
                questions.loc[i, ["Aussage1", "Aussage2", "Aussage3", "Aussage4"]][k-1])

    # configure parser: activate cdata and remove blank text at import
    parser = etree.XMLParser(strip_cdata=False, remove_blank_text=True)

    # import template
    tree = etree.parse('template.xml', parser=parser)
    root = tree.getroot()

    # import question template for every possible distribution of points.
    # This is necessary because the points have to add up to 100 in the ISIS System
    one_correct = etree.parse('one_correct.xml', parser=parser)
    two_correct = etree.parse('two_correct.xml', parser=parser)
    three_correct = etree.parse('three_correct.xml', parser=parser)
    four_correct = etree.parse('four_correct.xml', parser=parser)

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
            add_question(root,
                         num_correct=questions.loc[i, "num_correct"],
                         title=questions.loc[i, "text"].replace("$", "$$").encode("UTF-8")[0:38],
                         text=questions.loc[i, "text"].replace("$", "$$").encode("UTF-8"),
                         answers=questions.loc[i, "answers"])

    # write the xml file
    tree.write(outname, encoding="UTF-8", xml_declaration=True, pretty_print=True)
    # %%


# cannot recall the purpose of this snippet, I had some utf8 issues earlier where this snippet
# helped. Might not be necessary with python >= 3.
# reload(sys)
# sys.setdefaultencoding('utf-8')
# sys.exit()
# give the name of the table:

# this is the input data in xlsx format (table format, see readme)
table = "template_advanced.xlsx"
# course name, relevant for the name in moodle where the questions are stored (I believe...)
course = "AdvancedBioanalytics"
# save the xml file with the same name as input but with xml extension
outname = table.split(".")[0]+".xml"

print(f"Reading {table}...")
print(f"Generating questions for {course}...")
TableToXML(table, outname, course, verbose=0)
print(f"Done! File saved to {outname}...")

