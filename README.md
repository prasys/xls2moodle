# xls2moodle
Script to convert multiple choice questions from xls to moodle's xml format. The xml format
can then be used to import the questions into moodle quizes. Please note, that this repository
and the code was intended to be used for german tables / quizes. Adaptions are possible, but
some columns (in the input) are hard-coded at the moment.

To install the package and make use of the tkinter GUI (thanks @euvbonk), you can use the following snippet
(to be used best from an anaconda shell).

>pip install xls2moodle

## Running xls2moodle:
The script requires two inputs:
- course name
- location of tabular excel file with questions
- (optionally: custom templates corresponding to the xml templates with 1,2,3,4 correct answers.)

There are two options to run xls2moodle, all command line calls should be executed in the anaconda
shell:

1) run the GUI by running:
> xls2moodle

![alt text](https://github.com/gieses/xls2moodle/blob/master/docs/gui_xls2moodle.PNG)

2) run the command line version by executing.
> xls2moodle -c COURSE_NAME -t XLS_QUESTIONS

Help message can be displayed via:
>xls2moodle --help

## output
- xml format, ready for import in moodle

## question format

Please refer to the template_advanced.xlsx to get an idea on the file format.
Mandatory columns:
- Aussage1 - possible answer 1
- Aussage2 - possible answer 2
- Aussage3 - possible answer 3
- Aussage4 - possible answer 4
- WAHR - contains index of correct answer(s), 1-based
- FALSCH - contains index of wrong answer(s), 1-based
- Themenblock - contains a topic name (this should be the same for similar questions)
- Hauptfrage - Question text

Optional columns:
- Anwendung - boolean, filter to include (1) or exclude (0) questions

Further columns are ignored.

## templates
The script reads templates (xml_templates-folder) that were previously exported from moodle.
If the format changes in the future, this process needs to be repeated. In the meantime, do
not touch any of the xml templates.

## known issues
- latex equation code supported (?)
- reading of data with special encoding (utf-8) currently not possible with the latest pandas version

# Contributors
- Benjamin Furtwängler
- Sven Giese
- euvbonk